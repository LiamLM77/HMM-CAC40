"""Déclaration des routes de l'app dashboard."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("performance/", views.performance, name="performance"),
    path("regimes/", views.regimes, name="regimes"),
    path("betas/", views.betas, name="betas"),
    path("allocations/", views.allocations, name="allocations"),
    path("relancer-backtest/", views.relancer_backtest, name="relancer_backtest"),
]
