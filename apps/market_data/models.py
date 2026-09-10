from django.db import models


class ImportDonneesMarche(models.Model):
    """Trace le statut du dernier import Yahoo Finance pour un ticker donné."""

    STATUT_CHOICES = [
        ("ok", "Import réussi"),
        ("echec", "Échec"),
        ("exclu", "Exclu (trop de données manquantes)"),
    ]

    ticker = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100, blank=True)
    date_debut_historique = models.DateField()
    date_fin_historique = models.DateField()
    date_dernier_import = models.DateTimeField(auto_now=True)
    nb_lignes_importees = models.IntegerField(default=0)
    taux_valeurs_manquantes = models.FloatField(default=0.0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="echec")
    message_erreur = models.TextField(blank=True)

    class Meta:
        verbose_name = "Import de données marché"
        verbose_name_plural = "Imports de données marché"
        ordering = ["ticker"]

    def __str__(self):
        return f"{self.ticker} ({self.statut})"
