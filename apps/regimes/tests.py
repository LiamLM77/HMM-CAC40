"""Tests unitaires du filtre de persistance causal (cf. docs/03_modele_hmm.md)."""

from apps.regimes.services.hmm_model import lisser_persistance


def test_lisser_persistance_ignore_un_flip_isole():
    labels = ["haussier"] * 5 + ["baissier"] + ["haussier"] * 5
    resultat = lisser_persistance(labels, min_jours=3)
    assert resultat == ["haussier"] * 11


def test_lisser_persistance_confirme_un_changement_durable():
    labels = ["haussier"] * 5 + ["baissier"] * 4
    resultat = lisser_persistance(labels, min_jours=3)
    assert resultat[:5] == ["haussier"] * 5
    assert resultat[-1] == "baissier"
