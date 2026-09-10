"""Tests unitaires des fonctions critiques : métriques et règles d'allocation."""

import pandas as pd
import pytest

from apps.portfolio.services import allocation, metriques


def test_rendement_annualise_double_en_un_an():
    valeurs_252 = pd.Series([100.0] + [100.0] * 251 + [200.0])
    resultat = metriques.rendement_annualise(valeurs_252)
    assert resultat == pytest.approx(1.0, rel=1e-6)


def test_max_drawdown_detecte_la_pire_baisse():
    valeurs = pd.Series([100, 120, 90, 110])
    assert metriques.max_drawdown(valeurs) == pytest.approx(90 / 120 - 1)


def test_var_historique_est_negative_pour_serie_avec_pertes():
    rendements = pd.Series([0.01, -0.02, 0.015, -0.03, 0.005, -0.01, 0.02])
    assert metriques.var_historique(rendements, 0.95) < 0


def test_trier_candidats_haussier_favorise_beta_eleve_et_momentum_positif():
    candidats = pd.DataFrame(
        {"beta": [1.5, 1.3, 1.8], "momentum": [0.10, -0.05, 0.02]},
        index=["A", "B", "C"],
    )
    resultat = allocation.trier_candidats(candidats, "haussier")
    assert set(resultat) == {"A", "B", "C"}
    assert resultat[0] in {"A", "C"}


def test_trier_candidats_exclut_les_beta_hors_seuil():
    candidats = pd.DataFrame({"beta": [1.0, 0.5], "momentum": [0.0, 0.0]}, index=["A", "B"])
    assert allocation.trier_candidats(candidats, "haussier") == []


def test_anti_churn_reset_top10_si_changement_de_regime():
    candidats = [f"T{i}" for i in range(20)]
    panier_precedent = {"T0", "T1", "T18", "T19"}
    resultat = allocation.appliquer_anti_churn(candidats, panier_precedent, "haussier", "baissier")
    assert resultat == set(candidats[:10])


def test_anti_churn_conserve_les_positions_dans_le_buffer():
    candidats = [f"T{i}" for i in range(20)]
    panier_precedent = {"T0", "T12"}
    resultat = allocation.appliquer_anti_churn(candidats, panier_precedent, "haussier", "haussier")
    assert "T12" in resultat
    assert set(candidats[:10]).issubset(resultat)
