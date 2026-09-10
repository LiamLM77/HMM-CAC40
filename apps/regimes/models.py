from django.db import models


class EntrainementHMM(models.Model):
    """Trace chaque (ré)entraînement du HMM (initial ou walk-forward)."""

    TYPE_CHOICES = [
        ("initial", "Entraînement initial (train)"),
        ("walk_forward", "Ré-entraînement walk-forward (test)"),
    ]

    type_entrainement = models.CharField(max_length=15, choices=TYPE_CHOICES)
    date_debut_fenetre = models.DateField()
    date_fin_fenetre = models.DateField()
    nb_observations = models.IntegerField()
    log_vraisemblance = models.FloatField()
    date_application_debut = models.DateField()
    date_application_fin = models.DateField()
    date_execution = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entraînement HMM"
        verbose_name_plural = "Entraînements HMM"
        ordering = ["date_debut_fenetre"]

    def __str__(self):
        return f"{self.type_entrainement} [{self.date_debut_fenetre} -> {self.date_fin_fenetre}]"
