"""Stockage du journal des transactions du backtest (table transactions)."""

import duckdb
import pandas as pd


def initialiser_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            date DATE,
            ticker VARCHAR,
            sens VARCHAR,
            montant DOUBLE,
            cout DOUBLE
        )
        """
    )


def enregistrer_transactions(con: duckdb.DuckDBPyConnection, transactions: pd.DataFrame) -> int:
    initialiser_schema(con)
    con.execute("DELETE FROM transactions")
    if transactions.empty:
        return 0
    a_inserer = transactions[["date", "ticker", "sens", "montant", "cout"]]
    con.execute("INSERT INTO transactions SELECT * FROM a_inserer")
    return len(transactions)


def lire_transactions(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM transactions ORDER BY date, ticker").fetchdf()
