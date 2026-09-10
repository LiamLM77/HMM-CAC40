"""Détermination des dates de rééquilibrage (dernier jour de bourse de la période)."""

import pandas as pd


def dates_hebdomadaires(dates_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Retourne, pour chaque semaine ISO couverte, le dernier jour de bourse disponible."""
    semaines = dates_index.isocalendar()
    dernier_jour_par_semaine = (
        pd.Series(dates_index, index=dates_index)
        .groupby([semaines["year"], semaines["week"]])
        .max()
    )
    return pd.DatetimeIndex(sorted(dernier_jour_par_semaine.values))


def dates_mensuelles(dates_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Retourne, pour chaque mois couvert, le dernier jour de bourse disponible."""
    dernier_jour_par_mois = (
        pd.Series(dates_index, index=dates_index)
        .groupby(dates_index.to_period("M"))
        .max()
    )
    return pd.DatetimeIndex(sorted(dernier_jour_par_mois.values))


def dates_rebalancement(dates_index: pd.DatetimeIndex, frequence: str) -> pd.DatetimeIndex:
    """Sélectionne les dates de rééquilibrage selon la fréquence configurée (cf. settings.FREQUENCE_REEQUILIBRAGE)."""
    if frequence == "mensuel":
        return dates_mensuelles(dates_index)
    return dates_hebdomadaires(dates_index)
