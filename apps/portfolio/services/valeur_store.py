"""Stockage de la valeur journalière du portefeuille et du benchmark (table valeur_portefeuille)."""

import duckdb
import pandas as pd


def initialiser_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS valeur_portefeuille (
            date DATE PRIMARY KEY,
            valeur_portefeuille DOUBLE,
            valeur_benchmark DOUBLE
        )
        """
    )


def enregistrer_valeurs(con: duckdb.DuckDBPyConnection, valeurs: pd.DataFrame) -> int:
    initialiser_schema(con)
    con.execute("DELETE FROM valeur_portefeuille")
    a_inserer = valeurs.reset_index()[["date", "valeur_portefeuille", "valeur_benchmark"]]
    con.execute("INSERT INTO valeur_portefeuille SELECT * FROM a_inserer")
    return len(a_inserer)


def lire_valeurs(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM valeur_portefeuille ORDER BY date").fetchdf()
