"""Moteur de simulation du backtest : valorisation quotidienne du portefeuille (cf. docs/05).

Rééquilibrage complet vers les poids cibles à chaque date de rééquilibrage (mensuelle par
défaut, cf. settings.FREQUENCE_REEQUILIBRAGE) : les poids étant désormais issus d'un blend
probabiliste (cf. allocation_probabiliste.py) qui évolue en douceur d'une période à l'autre,
ce rééquilibrage complet reste peu coûteux (peu de dates, variations de poids progressives).
Coûts de transaction appliqués sur chaque montant échangé (achat ou vente).
"""

import pandas as pd
from django.conf import settings


def charger_allocations_test(con) -> pd.DataFrame:
    """Ne conserve que les dates de la période de test (walk-forward, hors in-sample)."""
    return con.execute(
        """
        SELECT a.date, a.ticker, a.poids, a.regime
        FROM allocations_hebdomadaires a
        JOIN regimes_marche r ON a.date = r.date
        WHERE r.ensemble = 'test'
        ORDER BY a.date, a.ticker
        """
    ).fetchdf()


def charger_prix_quotidiens(con, tickers: list[str], date_debut) -> pd.DataFrame:
    """Charge l'Adjusted Close journalier de tous les tickers utiles, en colonnes (pivot)."""
    marqueurs = ",".join(["?"] * len(tickers))
    donnees = con.execute(
        f"SELECT date, ticker, adj_close FROM prix_ohlcv WHERE ticker IN ({marqueurs}) AND date >= ? ORDER BY date",
        [*tickers, date_debut],
    ).fetchdf()
    return donnees.pivot(index="date", columns="ticker", values="adj_close").sort_index()


def _valeur_positions(positions: dict, prix_du_jour: pd.Series) -> float:
    return sum(quantite * prix_du_jour[ticker] for ticker, quantite in positions.items())


def simuler_backtest(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rejoue le backtest complet. Retourne (valeurs_journalieres, transactions)."""
    allocations = charger_allocations_test(con)
    if allocations.empty:
        raise ValueError("Aucune allocation de test disponible : lancez calculer_allocations au préalable.")

    dates_rebalancement = sorted(allocations["date"].unique())
    date_debut = dates_rebalancement[0]

    tickers_actions = sorted(allocations["ticker"].unique().tolist())
    prix = charger_prix_quotidiens(con, tickers_actions + [settings.TICKER_BENCHMARK], date_debut)

    positions: dict[str, float] = {}
    cash = settings.CAPITAL_INITIAL
    historique_valeur = []
    historique_transactions = []
    taux_cout = settings.COUT_TRANSACTION_POURCENT

    for date in prix.index:
        prix_du_jour = prix.loc[date]

        if date in dates_rebalancement:
            poids_cibles = allocations.loc[allocations["date"] == date].set_index("ticker")["poids"]
            valeur_avant = _valeur_positions(positions, prix_du_jour) + cash

            tickers_concernes = set(positions.keys()) | set(poids_cibles.index)
            for ticker in tickers_concernes:
                valeur_precedente = positions.get(ticker, 0.0) * prix_du_jour[ticker]
                valeur_cible = poids_cibles.get(ticker, 0.0) * valeur_avant
                delta = valeur_cible - valeur_precedente
                if abs(delta) < 1e-9:
                    continue

                cout = abs(delta) * taux_cout
                cash -= delta + cout
                historique_transactions.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "sens": "achat" if delta > 0 else "vente",
                        "montant": abs(delta),
                        "cout": cout,
                    }
                )

                if valeur_cible <= 0:
                    positions.pop(ticker, None)
                else:
                    positions[ticker] = valeur_cible / prix_du_jour[ticker]

        valeur_du_jour = _valeur_positions(positions, prix_du_jour) + cash
        historique_valeur.append({"date": date, "valeur_portefeuille": valeur_du_jour})

    valeurs = pd.DataFrame(historique_valeur).set_index("date")

    # Benchmark CAC40 en achat unique (buy & hold), sans frais
    prix_benchmark = prix[settings.TICKER_BENCHMARK]
    nb_actions_benchmark = settings.CAPITAL_INITIAL / prix_benchmark.iloc[0]
    valeurs["valeur_benchmark"] = prix_benchmark * nb_actions_benchmark

    transactions = pd.DataFrame(historique_transactions)
    return valeurs, transactions

