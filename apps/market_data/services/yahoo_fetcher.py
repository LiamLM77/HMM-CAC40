"""Téléchargement des données de marché depuis Yahoo Finance."""

import pandas as pd
import yfinance as yf


def telecharger_historique(ticker: str, date_debut: str, date_fin: str) -> pd.DataFrame:
    """Télécharge l'historique OHLCV ajusté d'un ticker sur la période demandée.

    Retourne un DataFrame indexé par date avec les colonnes :
    open, high, low, close, adj_close, volume.
    Le DataFrame est vide si le ticker est introuvable ou sans données sur la période.
    """
    donnees = yf.download(
        ticker,
        start=date_debut,
        end=date_fin,
        auto_adjust=False,
        progress=False,
        multi_level_index=False,
    )

    if donnees.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "adj_close", "volume"])

    donnees = donnees.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    donnees.index.name = "date"
    return donnees[["open", "high", "low", "close", "adj_close", "volume"]]
