"""Commande de calcul des bêtas glissants (brut + ajusté Blume) pour tout l'univers.

Usage : python manage.py calculer_betas
"""

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.market_data.services import duckdb_store
from apps.portfolio.models import ExecutionCalculBeta
from apps.portfolio.services import beta_calculator, beta_store


class Command(BaseCommand):
    help = "Calcule le bêta glissant 252 jours (brut et ajusté Blume) de chaque action, aux dates hebdomadaires."

    def handle(self, *args, **options):
        con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)

        univers = pd.read_csv(settings.UNIVERS_CAC40_CSV)
        tickers = univers["ticker"].tolist()

        self.stdout.write(f"Calcul des bêtas glissants ({settings.BETA_FENETRE_JOURS} jours) pour {len(tickers)} actions...")
        betas = beta_calculator.calculer_betas_glissants(con, tickers, settings.TICKER_BENCHMARK, settings.BETA_FENETRE_JOURS)

        nb_lignes = beta_store.enregistrer_betas(con, betas)
        con.close()

        ExecutionCalculBeta.objects.create(
            fenetre_jours=settings.BETA_FENETRE_JOURS,
            nb_tickers=len(tickers),
            nb_dates_hebdomadaires=betas["date"].nunique(),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{nb_lignes} lignes bêta enregistrées ({betas['date'].nunique()} semaines, {len(tickers)} actions)."
            )
        )
