"""Construction des variables d'observation du HMM à partir de DuckDB.

Variables (cf. docs/03_modele_hmm.md) : rendement log du CAC40, volatilité
réalisée glissante annualisée, spread de taux France - Allemagne.
"""

import numpy as np
import pandas as pd
from django.conf import settings


def construire_observations(con) -> pd.DataFrame:
    """Retourne un DataFrame indexé par date avec les 3 variables d'observation du HMM."""
    rendements = con.execute(
        "SELECT date, rendement_log FROM rendements WHERE ticker = ? ORDER BY date",
        [settings.TICKER_BENCHMARK],
    ).fetchdf()
    spread = con.execute("SELECT date, spread_taux FROM spread_taux ORDER BY date").fetchdf()

    observations = rendements.merge(spread, on="date", how="left").set_index("date")

    # Volatilité réalisée glissante, annualisée (racine de 252 jours de bourse)
    observations["volatilite_realisee"] = (
        observations["rendement_log"]
        .rolling(settings.HMM_FENETRE_VOLATILITE_JOURS)
        .std()
        * np.sqrt(252)
    )

    # Les premiers jours n'ont pas de fenêtre de volatilité complète ni de spread : on les retire
    observations = observations.dropna(subset=["volatilite_realisee", "spread_taux"])

    return observations[["rendement_log", "volatilite_realisee", "spread_taux"]]
