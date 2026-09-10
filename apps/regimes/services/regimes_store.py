"""Stockage des régimes de marché détectés dans DuckDB (table regimes_marche)."""

import duckdb
import pandas as pd


def initialiser_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS regimes_marche (
            date DATE PRIMARY KEY,
            regime VARCHAR,
            proba_haussier DOUBLE,
            proba_neutre DOUBLE,
            proba_baissier DOUBLE,
            ensemble VARCHAR,
            date_fin_entrainement DATE
        )
        """
    )


def enregistrer_regimes(con: duckdb.DuckDBPyConnection, regimes: pd.DataFrame) -> int:
    """Remplace intégralement la table regimes_marche par le contenu fourni."""
    initialiser_schema(con)
    con.execute("DELETE FROM regimes_marche")
    a_inserer = regimes.reset_index().rename(columns={"index": "date"})
    con.execute("INSERT INTO regimes_marche SELECT * FROM a_inserer")
    return len(a_inserer)


def lire_regimes(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM regimes_marche ORDER BY date").fetchdf()
