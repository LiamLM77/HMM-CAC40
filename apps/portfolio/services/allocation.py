"""Sélection des paniers d'actions par régime et règle anti-churn (cf. docs/04_beta_allocation.md).

Le classement combine le bêta (critère principal) et un score de momentum (qualité/tendance
récente) afin d'éviter de sélectionner des actions au bêta extrême mais en délabrement
récent (cf. diagnostic de sous-performance, Phase 4).
"""

from django.conf import settings


def trier_candidats(candidats, regime: str) -> list[str]:
    """Retourne les tickers éligibles au panier du régime, triés du meilleur au moins bon.

    candidats : pandas.DataFrame indexé par ticker, colonnes 'beta' et 'momentum'.
    """
    if regime == "baissier":
        eligibles = candidats[candidats["beta"] < settings.BETA_SEUIL_DEFENSIF].copy()
        rang_beta = eligibles["beta"].rank(ascending=True, pct=True)  # bêta le plus faible = meilleur
    elif regime == "haussier":
        eligibles = candidats[candidats["beta"] > settings.BETA_SEUIL_OFFENSIF].copy()
        rang_beta = eligibles["beta"].rank(ascending=False, pct=True)  # bêta le plus élevé = meilleur
    else:
        dans_la_bande = candidats["beta"].between(settings.BETA_SEUIL_NEUTRE_BAS, settings.BETA_SEUIL_NEUTRE_HAUT)
        eligibles = candidats[dans_la_bande].copy()
        rang_beta = (eligibles["beta"] - 1).abs().rank(ascending=True, pct=True)  # le plus proche de 1 = meilleur

    if eligibles.empty:
        return []

    rang_momentum = eligibles["momentum"].rank(ascending=False, pct=True)  # momentum le plus élevé = meilleur
    score_composite = settings.POIDS_SCORE_BETA * rang_beta + settings.POIDS_SCORE_MOMENTUM * rang_momentum
    return score_composite.sort_values(ascending=True).index.tolist()


def appliquer_anti_churn(
    candidats_tries: list[str],
    panier_precedent: set[str] | None,
    regime: str,
    regime_precedent: str | None,
) -> set[str]:
    """Applique la règle de zone tampon (buffer) pour limiter le turnover.

    Changement de régime (ou pas de panier précédent) -> panier = top 10 strict.
    Régime inchangé -> une position déjà détenue reste tant qu'elle est dans le top 15 ;
    seules les nouvelles entrées doivent être dans le top 10 strict.
    """
    top_n = settings.PANIER_TAILLE_CIBLE
    top_n_buffer = settings.PANIER_TAILLE_BUFFER

    top10 = set(candidats_tries[:top_n])

    if panier_precedent is None or regime != regime_precedent:
        return top10

    top15 = set(candidats_tries[:top_n_buffer])
    positions_conservees = panier_precedent & top15
    return top10 | positions_conservees
