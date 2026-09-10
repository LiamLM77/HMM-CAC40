from django.contrib import admin

from .models import ImportDonneesMarche


@admin.register(ImportDonneesMarche)
class ImportDonneesMarcheAdmin(admin.ModelAdmin):
    list_display = ("ticker", "nom", "statut", "nb_lignes_importees", "taux_valeurs_manquantes", "date_dernier_import")
    list_filter = ("statut",)
    search_fields = ("ticker", "nom")
