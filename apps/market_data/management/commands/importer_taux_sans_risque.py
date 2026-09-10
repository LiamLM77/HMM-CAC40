"""Import du taux sans risque (taux interbancaire 3 mois France, FRED) dans DuckDB.

Usage : python manage.py importer_taux_sans_risque
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.market_data.services import duckdb_store, fred_fetcher


class Command(BaseCommand):
    help = "Importe le taux sans risque (FRED) et le propage sur le calendrier boursier."

    def handle(self, *args, **options):
        con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)

        calendrier_bourse = con.execute(
            "SELECT DISTINCT date FROM prix_ohlcv WHERE ticker = ? ORDER BY date",
            [settings.TICKER_BENCHMARK],
        ).fetchdf()["date"]

        if calendrier_bourse.empty:
            self.stderr.write("Aucun calendrier boursier trouvé : lancez d'abord import_donnees_marche.")
            return

        serie = fred_fetcher.telecharger_serie_fred(
            settings.FRED_SERIE_TAUX_SANS_RISQUE,
            settings.DATE_DEBUT_HISTORIQUE,
            settings.DATE_FIN_HISTORIQUE,
        )
        # Taux annuel en % (ex: 2.03) -> décimal (0.0203), propagé en fréquence journalière
        taux_journalier = (serie / 100).reindex(calendrier_bourse, method="ffill").to_frame(name="taux")
        taux_journalier.index.name = "date"

        nb_lignes = duckdb_store.enregistrer_taux_sans_risque(con, taux_journalier)
        con.close()

        self.stdout.write(self.style.SUCCESS(f"{nb_lignes} jours de taux sans risque enregistrés."))
