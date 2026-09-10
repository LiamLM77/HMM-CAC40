from django.contrib import admin

from .models import ExecutionAllocation, ExecutionBacktest, ExecutionCalculBeta


@admin.register(ExecutionCalculBeta)
class ExecutionCalculBetaAdmin(admin.ModelAdmin):
    list_display = ("date_execution", "fenetre_jours", "nb_tickers", "nb_dates_hebdomadaires")


@admin.register(ExecutionAllocation)
class ExecutionAllocationAdmin(admin.ModelAdmin):
    list_display = ("date_execution", "utilise_blume", "nb_semaines", "turnover_total", "taille_panier_moyenne")


@admin.register(ExecutionBacktest)
class ExecutionBacktestAdmin(admin.ModelAdmin):
    list_display = (
        "date_execution",
        "date_debut_test",
        "date_fin_test",
        "capital_final_portefeuille",
        "capital_final_benchmark",
        "sharpe_portefeuille",
        "alpha_annualise",
        "beta_portefeuille",
    )

