"""Vues du dashboard : lecture des résultats (DuckDB + SQLite) et rendu des templates."""

import json

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.core.management import call_command
from django.shortcuts import redirect, render

from apps.market_data.services import duckdb_store
from apps.portfolio.models import ExecutionAllocation, ExecutionBacktest, ExecutionCalculBeta
from apps.portfolio.services import allocations_store, beta_store, valeur_store
from apps.regimes.models import EntrainementHMM
from apps.regimes.services import regimes_store


def _classer_beta(beta: float) -> str:
    """Reproduit les seuils de docs/04_beta_allocation.md pour l'affichage."""
    if beta < settings.BETA_SEUIL_DEFENSIF:
        return "défensif"
    if settings.BETA_SEUIL_NEUTRE_BAS <= beta <= settings.BETA_SEUIL_NEUTRE_HAUT:
        return "neutre"
    if beta > settings.BETA_SEUIL_OFFENSIF:
        return "offensif"
    return "zone grise"


def accueil(request):
    dernier_backtest = ExecutionBacktest.objects.first()
    dernier_calcul_beta = ExecutionCalculBeta.objects.first()
    derniere_allocation = ExecutionAllocation.objects.first()
    dernier_entrainement_hmm = EntrainementHMM.objects.order_by("-date_execution").first()
    contexte = {
        "backtest": dernier_backtest,
        "calcul_beta": dernier_calcul_beta,
        "allocation": derniere_allocation,
        "entrainement_hmm": dernier_entrainement_hmm,
    }
    return render(request, "dashboard/accueil.html", contexte)


def performance(request):
    con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)
    valeurs = valeur_store.lire_valeurs(con)
    con.close()

    contexte = {
        "backtest": ExecutionBacktest.objects.first(),
        "a_des_donnees": not valeurs.empty,
    }
    if not valeurs.empty:
        contexte.update(
            {
                "labels_json": json.dumps(valeurs["date"].astype(str).tolist()),
                "portefeuille_json": json.dumps(valeurs["valeur_portefeuille"].round(2).tolist()),
                "benchmark_json": json.dumps(valeurs["valeur_benchmark"].round(2).tolist()),
            }
        )
    return render(request, "dashboard/performance.html", contexte)


def regimes(request):
    con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)
    regimes_df = regimes_store.lire_regimes(con)
    prix_benchmark = con.execute(
        "SELECT date, adj_close FROM prix_ohlcv WHERE ticker = ? ORDER BY date", [settings.TICKER_BENCHMARK]
    ).fetchdf()
    con.close()

    contexte = {"a_des_donnees": not regimes_df.empty}
    if regimes_df.empty:
        return render(request, "dashboard/regimes.html", contexte)

    fusion = prix_benchmark.merge(regimes_df[["date", "regime", "ensemble"]], on="date", how="inner")

    series_par_regime = {}
    for label in ["haussier", "neutre", "baissier"]:
        serie = fusion["adj_close"].where(fusion["regime"] == label)
        series_par_regime[label] = json.dumps([None if pd.isna(v) else round(v, 2) for v in serie])

    repartition = (
        regimes_df.groupby(["ensemble", "regime"]).size().reset_index(name="nb_jours").to_dict("records")
    )

    contexte.update(
        {
            "labels_json": json.dumps(fusion["date"].astype(str).tolist()),
            "serie_haussier_json": series_par_regime["haussier"],
            "serie_neutre_json": series_par_regime["neutre"],
            "serie_baissier_json": series_par_regime["baissier"],
            "repartition": repartition,
        }
    )
    return render(request, "dashboard/regimes.html", contexte)


def betas(request):
    con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)
    betas_df = beta_store.lire_betas(con)
    con.close()

    contexte = {"a_des_donnees": not betas_df.empty}
    if betas_df.empty:
        return render(request, "dashboard/betas.html", contexte)

    derniere_date = betas_df["date"].max()
    derniers = betas_df[betas_df["date"] == derniere_date].sort_values("beta_ajuste", ascending=False)

    univers = pd.read_csv(settings.UNIVERS_CAC40_CSV).set_index("ticker")
    lignes = []
    for _, ligne in derniers.iterrows():
        info = univers.loc[ligne["ticker"]] if ligne["ticker"] in univers.index else None
        lignes.append(
            {
                "ticker": ligne["ticker"],
                "nom": info["nom"] if info is not None else ligne["ticker"],
                "secteur": info["secteur"] if info is not None else "",
                "beta_brut": round(ligne["beta_brut"], 3),
                "beta_ajuste": round(ligne["beta_ajuste"], 3),
                "momentum_63j": round(ligne["momentum_63j"], 4),
                "classe": _classer_beta(ligne["beta_ajuste"]),
            }
        )

    contexte.update({"date_reference": derniere_date, "lignes": lignes})
    return render(request, "dashboard/betas.html", contexte)


def allocations(request):
    con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)
    allocations_df = allocations_store.lire_allocations(con)
    con.close()

    contexte = {"a_des_donnees": not allocations_df.empty}
    if allocations_df.empty:
        return render(request, "dashboard/allocations.html", contexte)

    dates_disponibles = sorted(allocations_df["date"].unique(), reverse=True)
    date_choisie = request.GET.get("date")
    date_reference = pd.Timestamp(date_choisie) if date_choisie else dates_disponibles[0]

    lignes = (
        allocations_df[allocations_df["date"] == date_reference]
        .sort_values("poids", ascending=False)
        .to_dict("records")
    )

    contexte.update(
        {
            "date_reference": date_reference,
            "dates_disponibles": dates_disponibles,
            "lignes": lignes,
        }
    )
    return render(request, "dashboard/allocations.html", contexte)


def relancer_backtest(request):
    if request.method == "POST":
        try:
            call_command("lancer_backtest")
            messages.success(request, "Backtest relancé avec succès.")
        except Exception as erreur:
            messages.error(request, f"Échec du backtest : {erreur}")
    return redirect("dashboard:accueil")
