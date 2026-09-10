from django.db import models


class ExecutionCalculBeta(models.Model):
    """Trace un calcul complet des bêtas glissants (métadonnées, pas les séries)."""

    date_execution = models.DateTimeField(auto_now_add=True)
    fenetre_jours = models.IntegerField()
    nb_tickers = models.IntegerField()
    nb_dates_hebdomadaires = models.IntegerField()

    class Meta:
        verbose_name = "Exécution calcul bêta"
        verbose_name_plural = "Exécutions calcul bêta"
        ordering = ["-date_execution"]

    def __str__(self):
        return f"Calcul bêta du {self.date_execution:%Y-%m-%d %H:%M}"


class ExecutionAllocation(models.Model):
    """Trace un calcul complet des allocations hebdomadaires (métadonnées)."""

    date_execution = models.DateTimeField(auto_now_add=True)
    utilise_blume = models.BooleanField()
    nb_semaines = models.IntegerField()
    turnover_total = models.IntegerField(help_text="Nombre total d'entrées + sorties de panier sur la période")
    taille_panier_moyenne = models.FloatField()

    class Meta:
        verbose_name = "Exécution allocation"
        verbose_name_plural = "Exécutions allocation"
        ordering = ["-date_execution"]

    def __str__(self):
        return f"Allocation du {self.date_execution:%Y-%m-%d %H:%M} (Blume={self.utilise_blume})"


class ExecutionBacktest(models.Model):
    """Résumé des métriques d'un backtest complet (stratégie vs CAC40 buy & hold)."""

    date_execution = models.DateTimeField(auto_now_add=True)
    date_debut_test = models.DateField()
    date_fin_test = models.DateField()
    capital_initial = models.FloatField()

    capital_final_portefeuille = models.FloatField()
    rendement_annualise_portefeuille = models.FloatField()
    volatilite_portefeuille = models.FloatField()
    sharpe_portefeuille = models.FloatField()
    sortino_portefeuille = models.FloatField()
    calmar_portefeuille = models.FloatField()
    max_drawdown_portefeuille = models.FloatField()
    var_95_portefeuille = models.FloatField()

    capital_final_benchmark = models.FloatField()
    rendement_annualise_benchmark = models.FloatField()
    volatilite_benchmark = models.FloatField()
    sharpe_benchmark = models.FloatField()
    max_drawdown_benchmark = models.FloatField()

    alpha_annualise = models.FloatField()
    beta_portefeuille = models.FloatField()
    taux_sans_risque_moyen = models.FloatField()
    cout_transactions_total = models.FloatField()

    class Meta:
        verbose_name = "Exécution backtest"
        verbose_name_plural = "Exécutions backtest"
        ordering = ["-date_execution"]

    def __str__(self):
        return f"Backtest du {self.date_execution:%Y-%m-%d %H:%M} [{self.date_debut_test} -> {self.date_fin_test}]"

