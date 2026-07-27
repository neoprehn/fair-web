"""Views für die CAM-Szenario-Verwaltung (CRUD).

Ein CAM-Szenario wird zusammen mit seinem Control (1) und seinen Stufen (6)
und Verlustklassen (5) über ein festes Set von Kind-Formularen mit festem
Prefix angelegt und bearbeitet – analog zu ``apps.szenarien._SzenarioFormMixin``,
nur ohne variablen "Schnitt": die Anzahl der Kind-Objekte steht fest, daher
Update-in-place statt Löschen+Neuanlegen.
"""

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .beispiele import RANSOMWARE_BEISPIEL
from .forms import CamControlForm, CamSzenarioForm, CamStageForm, CamVerlustklasseForm
from .models import CamControl, CamStage, CamSzenario, CamVerlustklasse

_BEISPIEL_STAGES = {s["reihenfolge"]: s for s in RANSOMWARE_BEISPIEL["stages"]}
_BEISPIEL_KLASSEN = {v["klasse"]: v for v in RANSOMWARE_BEISPIEL["verlustklassen"]}


class CamSzenarioListView(ListView):
    model = CamSzenario
    template_name = "cam/dashboard.html"
    context_object_name = "cam_szenarien"


class CamSzenarioDetailView(DetailView):
    model = CamSzenario
    template_name = "cam/detail.html"
    context_object_name = "cam_szenario"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["control"] = getattr(self.object, "control", None)
        context["stages"] = self.object.stages.all()
        context["verlustklassen"] = self.object.verlustklassen.all()
        return context


class _CamSzenarioFormMixin:
    """Anlegen/Bearbeiten eines CAM-Szenarios mit Control + 6 Stufen + 5 Verlustklassen.

    Bei Neuanlage sind alle Kind-Formulare mit dem Ransomware-Beispiel
    vorbelegt (siehe ``beispiele.RANSOMWARE_BEISPIEL``); beim Bearbeiten mit
    den bestehenden Werten.
    """

    model = CamSzenario
    form_class = CamSzenarioForm
    template_name = "cam/form.html"
    context_object_name = "cam_szenario"

    def get_initial(self):
        initial = super().get_initial()
        if not self.object:
            initial.update(RANSOMWARE_BEISPIEL["szenario"])
        return initial

    def _control_form(self, data=None):
        instance = (getattr(self.object, "control", None) if self.object else None) or CamControl()
        initial = None if instance.pk else RANSOMWARE_BEISPIEL["control"]
        return CamControlForm(data, instance=instance, prefix="control", initial=initial)

    def _stage_forms(self, data=None):
        bestehend = {s.reihenfolge: s for s in self.object.stages.all()} if self.object else {}
        forms = {}
        for n in range(1, 7):
            instance = bestehend.get(n) or CamStage(reihenfolge=n)
            initial = None if instance.pk else _BEISPIEL_STAGES[n]
            forms[n] = CamStageForm(data, instance=instance, prefix=f"stage{n}", initial=initial)
        return forms

    def _verlustklasse_forms(self, data=None):
        bestehend = {v.klasse: v for v in self.object.verlustklassen.all()} if self.object else {}
        forms = {}
        for klasse, _label in CamVerlustklasse.Klasse.choices:
            instance = bestehend.get(klasse) or CamVerlustklasse(klasse=klasse)
            initial = None if instance.pk else _BEISPIEL_KLASSEN[klasse]
            forms[klasse] = CamVerlustklasseForm(data, instance=instance, prefix=klasse, initial=initial)
        return forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "control_form" not in context:
            data = self.request.POST if self.request.method == "POST" else None
            context["control_form"] = self._control_form(data)
            context["stage_forms"] = self._stage_forms(data)
            context["verlustklasse_forms"] = self._verlustklasse_forms(data)
        return context

    def form_valid(self, form):
        control_form = self._control_form(self.request.POST)
        stage_forms = self._stage_forms(self.request.POST)
        verlustklasse_forms = self._verlustklasse_forms(self.request.POST)

        alle_ok = (
            control_form.is_valid()
            and all(f.is_valid() for f in stage_forms.values())
            and all(f.is_valid() for f in verlustklasse_forms.values())
        )
        if not alle_ok:
            context = self.get_context_data(
                form=form,
                control_form=control_form,
                stage_forms=stage_forms,
                verlustklasse_forms=verlustklasse_forms,
            )
            return self.render_to_response(context)

        with transaction.atomic():
            self.object = form.save()
            control = control_form.save(commit=False)
            control.szenario = self.object
            control.save()
            for n, stage_form in stage_forms.items():
                stage = stage_form.save(commit=False)
                stage.szenario = self.object
                stage.reihenfolge = n
                stage.save()
            for klasse, klasse_form in verlustklasse_forms.items():
                eintrag = klasse_form.save(commit=False)
                eintrag.szenario = self.object
                eintrag.klasse = klasse
                eintrag.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("cam:detail", kwargs={"pk": self.object.pk})


class CamSzenarioCreateView(PermissionRequiredMixin, _CamSzenarioFormMixin, CreateView):
    permission_required = "cam.add_camszenario"
    raise_exception = True


class CamSzenarioUpdateView(PermissionRequiredMixin, _CamSzenarioFormMixin, UpdateView):
    permission_required = "cam.change_camszenario"
    raise_exception = True


class CamSzenarioDeleteView(PermissionRequiredMixin, DeleteView):
    model = CamSzenario
    template_name = "cam/confirm_delete.html"
    success_url = reverse_lazy("cam:dashboard")
    permission_required = "cam.delete_camszenario"
    raise_exception = True
