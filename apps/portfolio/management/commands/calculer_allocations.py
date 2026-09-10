"""Calcule et persiste l'historique des allocations (panier + poids par date de rééquilibrage).

Allocation probabiliste : le portefeuille est réparti entre les sous-paniers
défensif/neutre/offensif au prorata des probabilités de régime (cf. docs/04_beta_allocation.md).
Usage : python manage.py calculer_allocations
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.market_data.services import duckdb_store
from apps.portfolio.models import ExecutionAllocation
from apps.portfolio.services import allocation_probabiliste, allocations_store, beta_store
from apps.regimes.services import regimes_store


class Command(BaseCommand):
    help = "Calcule l'historique des allocations probabilistes (régime + bêta/momentum) et le persiste."

    def handle(self, *args, **options):
        con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)

        betas = beta_store.lire_betas(con)
        regimes = regimes_store.lire_regimes(con)

        if betas.empty or regimes.empty:
            self.stderr.write("Données manquantes : lancez calculer_betas et entrainer_hmm avant cette commande.")
            return

        self.stdout.write(
            f"Simulation des allocations probabilistes ({settings.FREQUENCE_REEQUILIBRAGE})..."
        )
        allocations = allocation_probabiliste.construire_allocations(betas, regimes)
        nb_lignes = allocations_store.enregistrer_allocations(con, allocations)
        con.close()

        turnover_total = allocation_probabiliste.calculer_turnover(allocations)
        tailles_panier = allocations.groupby("date").size()

        ExecutionAllocation.objects.create(
            utilise_blume=settings.UTILISER_BLUME,
            nb_semaines=len(tailles_panier),
            turnover_total=int(round(turnover_total)),
            taille_panier_moyenne=float(tailles_panier.mean()) if len(tailles_panier) else 0.0,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{nb_lignes} lignes d'allocation enregistrées sur {len(tailles_panier)} dates "
                f"(turnover total : {turnover_total:.1f})."
            )
        )
        self.stdout.write("Répartition des régimes dominants sur la période d'allocation :")
        self.stdout.write(str(allocations.drop_duplicates("date")["regime"].value_counts()))
