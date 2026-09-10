"""Récupération de séries de taux via FRED (spread souverain, taux sans risque)."""

import pandas as pd
import pandas_datareader.data as web


def telecharger_serie_fred(nom_serie: str, date_debut: str, date_fin: str) -> pd.Series:
    """Télécharge une série FRED brute (fréquence native, généralement mensuelle)."""
    donnees = web.DataReader(nom_serie, "fred", date_debut, date_fin)
    serie = donnees.iloc[:, 0]
    serie.index.name = "date"
    return serie


def telecharger_spread_taux(date_debut: str, date_fin: str, serie_france: str, serie_allemagne: str) -> pd.DataFrame:
    """Télécharge les taux long terme France/Allemagne (mensuels) et calcule le spread.

    Le spread mensuel est ensuite propagé en fréquence journalière (forward-fill)
    par l'appelant, pour être aligné avec les autres observations du HMM.
    Retourne un DataFrame indexé par date avec la colonne 'spread_taux'.
    """
    taux_france = web.DataReader(serie_france, "fred", date_debut, date_fin)
    taux_allemagne = web.DataReader(serie_allemagne, "fred", date_debut, date_fin)

    spread = taux_france.iloc[:, 0] - taux_allemagne.iloc[:, 0]
    resultat = spread.to_frame(name="spread_taux")
    resultat.index.name = "date"
    return resultat
