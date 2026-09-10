"""Compare le turnover du panier avec bêta brut vs bêta ajusté Blume (cf. docs/04_beta_allocation.md).

Ne persiste rien : affiche uniquement un rapport chiffré pour trancher settings.UTILISER_BLUME.
Usage : python manage.py comparer_ajustement_beta
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.market_data.services import duckdb_store
from apps.portfolio.services import allocation_probabiliste, beta_store
from apps.regimes.services import regimes_store


class Command(BaseCommand):
    help = "Compare le turnover engendré par le bêta brut et le bêta ajusté Blume."

    def handle(self, *args, **options):
        con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)

        betas = beta_store.lire_betas(con)
        regimes = regimes_store.lire_regimes(con)
        con.close()

        if betas.empty or regimes.empty:
            self.stderr.write("Données manquantes : lancez calculer_betas et entrainer_hmm avant cette commande.")
            return

        for colonne, label in [("beta_brut", "Bêta brut"), ("beta_ajuste", "Bêta ajusté Blume")]:
            allocations = allocation_probabiliste.construire_allocations(betas, regimes, colonne_beta=colonne)
            turnover_total = allocation_probabiliste.calculer_turnover(allocations)
            tailles_panier = allocations.groupby("date").size()

            self.stdout.write(self.style.SUCCESS(f"\n=== {label} ==="))
            self.stdout.write(f"  Nombre de dates simulées   : {len(tailles_panier)}")
            self.stdout.write(f"  Taille moyenne du panier   : {tailles_panier.mean():.2f}")
            self.stdout.write(f"  Turnover total (variation de poids cumulée) : {turnover_total:.2f}")
