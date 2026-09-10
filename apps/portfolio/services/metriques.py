"""Calcul des métriques de performance du backtest (cf. docs/05_backtest_metriques.md)."""

import numpy as np
import pandas as pd
from django.conf import settings


def rendements_quotidiens(valeurs: pd.Series) -> pd.Series:
    return valeurs.pct_change().dropna()


def rendement_annualise(valeurs: pd.Series) -> float:
    nb_jours = len(valeurs) - 1
    return (valeurs.iloc[-1] / valeurs.iloc[0]) ** (252 / nb_jours) - 1


def volatilite_annualisee(rendements: pd.Series) -> float:
    return rendements.std() * np.sqrt(252)


def ratio_sharpe(rendement_ann: float, volatilite_ann: float, taux_sans_risque: float) -> float:
    return (rendement_ann - taux_sans_risque) / volatilite_ann


def ratio_sortino(rendement_ann: float, rendements: pd.Series, taux_sans_risque: float) -> float:
    rendements_negatifs = rendements[rendements < 0]
    if rendements_negatifs.empty:
        return np.nan
    volatilite_negative = rendements_negatifs.std() * np.sqrt(252)
    return (rendement_ann - taux_sans_risque) / volatilite_negative


def max_drawdown(valeurs: pd.Series) -> float:
    plus_haut_cumule = valeurs.cummax()
    drawdown = valeurs / plus_haut_cumule - 1
    return drawdown.min()


def ratio_calmar(rendement_ann: float, mdd: float) -> float:
    return rendement_ann / abs(mdd) if mdd != 0 else np.nan


def var_historique(rendements: pd.Series, niveau_confiance: float) -> float:
    return rendements.quantile(1 - niveau_confiance)


def alpha_beta_vs_benchmark(rendements_portefeuille: pd.Series, rendements_benchmark: pd.Series) -> tuple[float, float]:
    """Régression rendements portefeuille ~ rendements benchmark. Retourne (alpha_annualisé, bêta)."""
    beta, alpha_quotidien = np.polyfit(rendements_benchmark, rendements_portefeuille, 1)
    alpha_annualise = alpha_quotidien * 252
    return alpha_annualise, beta


def calculer_toutes_les_metriques(valeurs: pd.Series, taux_sans_risque: float) -> dict:
    """Calcule l'ensemble des métriques pour une série de valeurs (portefeuille ou benchmark)."""
    rendements = rendements_quotidiens(valeurs)
    rendement_ann = rendement_annualise(valeurs)
    volatilite_ann = volatilite_annualisee(rendements)
    mdd = max_drawdown(valeurs)

    return {
        "rendement_annualise": rendement_ann,
        "volatilite_annualisee": volatilite_ann,
        "sharpe": ratio_sharpe(rendement_ann, volatilite_ann, taux_sans_risque),
        "sortino": ratio_sortino(rendement_ann, rendements, taux_sans_risque),
        "max_drawdown": mdd,
        "calmar": ratio_calmar(rendement_ann, mdd),
        "var_95": var_historique(rendements, settings.VAR_NIVEAU_CONFIANCE),
    }
