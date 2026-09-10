"""Stockage et lecture des données de marché dans DuckDB.

DuckDB sert de moteur analytique pour les données de marché (gros volumes,
calculs vectorisés), séparé de la base SQLite utilisée par les modèles Django.
"""

import duckdb
import pandas as pd


def obtenir_connexion(chemin_duckdb) -> duckdb.DuckDBPyConnection:
    """Ouvre (ou crée) la base DuckDB au chemin donné et initialise le schéma."""
    con = duckdb.connect(str(chemin_duckdb))
    initialiser_schema(con)
    return con


def initialiser_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Crée les tables nécessaires si elles n'existent pas déjà."""
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS prix_ohlcv (
            ticker VARCHAR,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            adj_close DOUBLE,
            volume BIGINT,
            PRIMARY KEY (ticker, date)
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS rendements (
            ticker VARCHAR,
            date DATE,
            rendement_log DOUBLE,
            PRIMARY KEY (ticker, date)
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS spread_taux (
            date DATE PRIMARY KEY,
            spread_taux DOUBLE
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS taux_sans_risque (
            date DATE PRIMARY KEY,
            taux DOUBLE
        )
        """
    )


def enregistrer_prix(con: duckdb.DuckDBPyConnection, ticker: str, donnees: pd.DataFrame) -> int:
    """Enregistre l'historique OHLCV d'un ticker (remplace les données existantes pour ce ticker)."""
    if donnees.empty:
        return 0

    a_inserer = donnees.reset_index().assign(ticker=ticker)
    a_inserer = a_inserer[["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]]

    con.execute("DELETE FROM prix_ohlcv WHERE ticker = ?", [ticker])
    con.execute("INSERT INTO prix_ohlcv SELECT * FROM a_inserer")
    return len(a_inserer)


def calculer_et_enregistrer_rendements(con: duckdb.DuckDBPyConnection, ticker: str) -> None:
    """Calcule les rendements log à partir de l'adj_close stocké et les enregistre."""
    con.execute("DELETE FROM rendements WHERE ticker = ?", [ticker])
    con.execute(
        """
        INSERT INTO rendements
        SELECT
            ticker,
            date,
            LN(adj_close / LAG(adj_close) OVER (ORDER BY date)) AS rendement_log
        FROM prix_ohlcv
        WHERE ticker = ?
        QUALIFY rendement_log IS NOT NULL
        """,
        [ticker],
    )


def enregistrer_spread_taux(con: duckdb.DuckDBPyConnection, donnees: pd.DataFrame) -> int:
    """Enregistre le spread de taux (remplace les données existantes)."""
    if donnees.empty:
        return 0

    a_inserer = donnees.reset_index()[["date", "spread_taux"]]
    con.execute("DELETE FROM spread_taux")
    con.execute("INSERT INTO spread_taux SELECT * FROM a_inserer")
    return len(a_inserer)


def enregistrer_taux_sans_risque(con: duckdb.DuckDBPyConnection, donnees: pd.DataFrame) -> int:
    """Enregistre le taux sans risque journalier (remplace les données existantes)."""
    if donnees.empty:
        return 0

    a_inserer = donnees.reset_index()[["date", "taux"]]
    con.execute("DELETE FROM taux_sans_risque")
    con.execute("INSERT INTO taux_sans_risque SELECT * FROM a_inserer")
    return len(a_inserer)


def lire_prix(con: duckdb.DuckDBPyConnection, ticker: str) -> pd.DataFrame:
    """Relit l'historique OHLCV d'un ticker depuis DuckDB, trié par date."""
    return con.execute(
        "SELECT * FROM prix_ohlcv WHERE ticker = ? ORDER BY date", [ticker]
    ).fetchdf()
