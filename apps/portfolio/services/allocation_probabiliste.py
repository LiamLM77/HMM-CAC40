"""Construction des allocations par pondération probabiliste des régimes (cf. docs/04).

Plutôt que de basculer intégralement vers un seul panier "dur" selon le régime détecté,
le portefeuille est réparti entre les 3 sous-paniers (défensif/neutre/offensif) au prorata
des probabilités de régime (proba_haussier/neutre/baissier). Cela lisse l'impact d'un
mauvais classement de régime (cf. diagnostic de sous-performance, Phase 4) au lieu d'un
"tout ou rien" hebdomadaire/mensuel.

Chaque sous-panier a sa propre continuité (anti-churn) indépendamment des autres.
"""

import pandas as pd
from django.conf import settings

from .allocation import appliquer_anti_churn, trier_candidats

REGIMES = ["haussier", "neutre", "baissier"]


def construire_allocations(betas: pd.DataFrame, regimes_journaliers: pd.DataFrame, colonne_beta: str | None = None) -> pd.DataFrame:
    """Construit l'historique des allocations (date, ticker, poids, regime dominant).

    betas : colonnes ticker, date, beta_brut, beta_ajuste, momentum_63j (dates de rééquilibrage).
    regimes_journaliers : colonnes date, regime, proba_haussier, proba_neutre, proba_baissier (quotidien).
    colonne_beta : 'beta_brut' ou 'beta_ajuste' ; par défaut settings.UTILISER_BLUME décide.
    """
    if colonne_beta is None:
        colonne_beta = "beta_ajuste" if settings.UTILISER_BLUME else "beta_brut"
    regimes_tries = regimes_journaliers.sort_values("date")

    paniers_precedents = {regime: None for regime in REGIMES}
    lignes = []

    for date, groupe in betas.groupby("date"):
        candidats = groupe.set_index("ticker")[[colonne_beta, "momentum_63j"]].rename(
            columns={colonne_beta: "beta", "momentum_63j": "momentum"}
        )

        regimes_disponibles = regimes_tries[regimes_tries["date"] <= date]
        if regimes_disponibles.empty:
            continue
        derniere_ligne = regimes_disponibles.iloc[-1]
        probabilites = {
            "haussier": derniere_ligne["proba_haussier"],
            "neutre": derniere_ligne["proba_neutre"],
            "baissier": derniere_ligne["proba_baissier"],
        }
        regime_dominant = max(probabilites, key=probabilites.get)

        # Atténuation du biais défensif : une partie de la probabilité "baissier" est
        # réallouée au panier neutre (cf. settings.ATTENUATION_BAISSIER et diagnostic Phase 4 :
        # les creux de marché sont souvent suivis d'un rebond à court terme).
        probabilites_effectives = dict(probabilites)
        probabilite_baissier_reallouee = probabilites["baissier"] * (1 - settings.ATTENUATION_BAISSIER)
        probabilites_effectives["baissier"] = probabilites["baissier"] * settings.ATTENUATION_BAISSIER
        probabilites_effectives["neutre"] = probabilites["neutre"] + probabilite_baissier_reallouee

        poids_par_ticker: dict[str, float] = {}
        for regime in REGIMES:
            candidats_tries = trier_candidats(candidats, regime)
            # Le sous-panier ne bascule jamais "en dur" : on ne compare qu'à sa propre
            # composition passée (buffer top15 toujours actif, jamais de reset top10 strict).
            panier = appliquer_anti_churn(candidats_tries, paniers_precedents[regime], "membre", "membre")
            paniers_precedents[regime] = panier

            if not panier:
                continue
            poids_intra_panier = probabilites_effectives[regime] / len(panier)
            for ticker in panier:
                poids_par_ticker[ticker] = poids_par_ticker.get(ticker, 0.0) + poids_intra_panier

        for ticker, poids in poids_par_ticker.items():
            lignes.append({"date": date, "ticker": ticker, "poids": poids, "regime": regime_dominant})

    return pd.DataFrame(lignes)


def calculer_turnover(allocations: pd.DataFrame) -> float:
    """Turnover total = somme des variations absolues de poids d'une période à l'autre."""
    if allocations.empty:
        return 0.0
    pivot = allocations.pivot(index="date", columns="ticker", values="poids").fillna(0.0).sort_index()
    return pivot.diff().abs().sum().sum()
