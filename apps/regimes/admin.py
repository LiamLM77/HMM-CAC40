from django.contrib import admin

from .models import EntrainementHMM


@admin.register(EntrainementHMM)
class EntrainementHMMAdmin(admin.ModelAdmin):
    list_display = (
        "type_entrainement",
        "date_debut_fenetre",
        "date_fin_fenetre",
        "nb_observations",
        "log_vraisemblance",
        "date_application_debut",
        "date_application_fin",
    )
    list_filter = ("type_entrainement",)
