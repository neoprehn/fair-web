"""Tests für die Angreifertyp-Profile (TC-Vorlagen)."""

import pytest
from django.urls import reverse

from apps.szenarien.models import Angreifertyp


@pytest.mark.django_db
def test_angreifertypen_sind_geseedet():
    assert Angreifertyp.objects.count() >= 7
    ns = Angreifertyp.objects.get(name="Nation State (Top Tier)")
    assert (ns.low, ns.mode, ns.high) == (0.80, 0.95, 0.99)
    # Reihenfolge: Script Kiddie zuerst.
    assert Angreifertyp.objects.first().name == "Script Kiddie"


@pytest.mark.django_db
def test_formular_zeigt_tc_picker(client):
    resp = client.get(reverse("szenarien:create"))
    assert resp.status_code == 200
    assert b"angreifertyp-select" in resp.content
    assert "Script Kiddie".encode() in resp.content
    assert "Nation State (Top Tier)".encode() in resp.content
