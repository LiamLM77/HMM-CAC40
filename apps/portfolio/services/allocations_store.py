"""Stockage des allocations hebdomadaires dans DuckDB (table allocations_hebdomadaires)."""

import duckdb
import pandas as pd


def initialiser_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS allocations_hebdomadaires (
            date DATE,
            ticker VARCHAR,
            poids DOUBLE,
            regime VARCHAR,
            PRIMARY KEY (date, ticker)
        )
        """
    )


def enregistrer_allocations(con: duckdb.DuckDBPyConnection, allocations: pd.DataFrame) -> int:
    initialiser_schema(con)
    con.execute("DELETE FROM allocations_hebdomadaires")
    if allocations.empty:
        return 0
    con.execute("INSERT INTO allocations_hebdomadaires SELECT date, ticker, poids, regime FROM allocations")
    return len(allocations)


def lire_allocations(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM allocations_hebdomadaires ORDER BY date, ticker").fetchdf()
