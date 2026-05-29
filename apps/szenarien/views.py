"""Views für die Szenario-Verwaltung (CRUD).

Ein Szenario wird zusammen mit seinen Faktor-Eingaben (LEF + LM) über ein
Inline-Formset angelegt und bearbeitet.
"""

from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import FaktorFormSet, SzenarioForm
from .models import Szenario


class SzenarioListView(ListView):
    model = Szenario
    template_name = "szenarien/dashboard.html"
    context_object_name = "szenarien"


class SzenarioDetailView(DetailView):
    model = Szenario
    template_name = "szenarien/detail.html"
    context_object_name = "szenario"


class _SzenarioFormMixin:
    """Gemeinsame Formset-Logik für Anlegen und Bearbeiten."""

    model = Szenario
    form_class = SzenarioForm
    template_name = "szenarien/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "faktor_formset" not in context:
            if self.request.method == "POST":
                context["faktor_formset"] = FaktorFormSet(
                    self.request.POST, instance=self.object
                )
            else:
                context["faktor_formset"] = FaktorFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        formset = FaktorFormSet(self.request.POST, instance=self.object)
        if not formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, faktor_formset=formset)
            )
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("szenarien:detail", kwargs={"pk": self.object.pk})


class SzenarioCreateView(_SzenarioFormMixin, CreateView):
    pass


class SzenarioUpdateView(_SzenarioFormMixin, UpdateView):
    pass


class SzenarioDeleteView(DeleteView):
    model = Szenario
    template_name = "szenarien/confirm_delete.html"
    context_object_name = "szenario"
    success_url = reverse_lazy("szenarien:dashboard")
