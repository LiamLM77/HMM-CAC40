"""Stockage du bêta glissant dans DuckDB (table beta_glissant)."""

import duckdb
import pandas as pd


def initialiser_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS beta_glissant (
            ticker VARCHAR,
            date DATE,
            beta_brut DOUBLE,
            beta_ajuste DOUBLE,
            momentum_63j DOUBLE,
            PRIMARY KEY (ticker, date)
        )
        """
    )


def enregistrer_betas(con: duckdb.DuckDBPyConnection, betas: pd.DataFrame) -> int:
    con.execute("DROP TABLE IF EXISTS beta_glissant")
    initialiser_schema(con)
    con.execute(
        "INSERT INTO beta_glissant SELECT ticker, date, beta_brut, beta_ajuste, momentum_63j FROM betas"
    )
    return len(betas)


def lire_betas(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM beta_glissant ORDER BY date, ticker").fetchdf()
