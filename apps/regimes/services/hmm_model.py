"""Entraînement, étiquetage et décodage du HMM Gaussien de régimes de marché."""

import numpy as np
from django.conf import settings
from hmmlearn.hmm import GaussianHMM

LABELS_PAR_RANG = ["baissier", "neutre", "haussier"]  # tri croissant par moyenne de rendement


class Standardiseur:
    """Standardisation (z-score) ajustée une seule fois sur le train, jamais recalculée."""

    def __init__(self):
        self.moyennes = None
        self.ecarts_types = None

    def ajuster(self, observations: np.ndarray) -> "Standardiseur":
        self.moyennes = observations.mean(axis=0)
        self.ecarts_types = observations.std(axis=0)
        return self

    def transformer(self, observations: np.ndarray) -> np.ndarray:
        return (observations - self.moyennes) / self.ecarts_types


def entrainer_modele(observations_standardisees: np.ndarray, n_etats: int, graine_aleatoire: int = 42) -> GaussianHMM:
    """Entraîne un HMM Gaussien à covariance diagonale (cf. docs/03_modele_hmm.md).

    Un prior de transition "collant" (diagonale renforcée) favorise la persistance
    d'état et limite les oscillations de régime dues au bruit (whipsaw).
    """
    prior_transition = np.ones((n_etats, n_etats))
    np.fill_diagonal(prior_transition, settings.HMM_TRANSMAT_PRIOR_DIAGONAL)

    modele = GaussianHMM(
        n_components=n_etats,
        covariance_type="diag",
        n_iter=200,
        random_state=graine_aleatoire,
        transmat_prior=prior_transition,
    )
    modele.fit(observations_standardisees)
    return modele


def etiqueter_etats(modele: GaussianHMM) -> dict:
    """Associe chaque état caché à un label (baissier/neutre/haussier) selon la moyenne de rendement."""
    moyennes_rendement = modele.means_[:, 0]  # rendement log = 1ère variable d'observation
    ordre_croissant = np.argsort(moyennes_rendement)
    return {etat: LABELS_PAR_RANG[rang] for rang, etat in enumerate(ordre_croissant)}


def decoder_regimes(modele: GaussianHMM, observations_standardisees: np.ndarray, mapping: dict):
    """Décode la séquence de régimes (Viterbi) et les probabilités filtrées par label.

    Retourne (labels, probabilites_par_label, log_vraisemblance) où probabilites_par_label
    est un dict {"haussier": [...], "neutre": [...], "baissier": [...]} aligné sur les dates.
    """
    log_vraisemblance, etats_viterbi = modele.decode(observations_standardisees, algorithm="viterbi")
    labels = [mapping[etat] for etat in etats_viterbi]

    probabilites_brutes = modele.predict_proba(observations_standardisees)
    etat_par_label = {label: etat for etat, label in mapping.items()}
    probabilites_par_label = {
        label: probabilites_brutes[:, etat_par_label[label]] for label in LABELS_PAR_RANG
    }

    return labels, probabilites_par_label, log_vraisemblance


def lisser_persistance(labels: list[str], min_jours: int) -> list[str]:
    """Filtre causal : un changement de régime n'est confirmé que s'il persiste au moins
    `min_jours` jours consécutifs ; sinon le régime précédemment confirmé est maintenu.

    Purement causal (ne regarde jamais en avant) : utilisable en walk-forward sans fuite
    d'information.
    """
    if not labels:
        return labels

    regime_confirme = labels[0]
    candidat = labels[0]
    compteur_candidat = 1
    resultat = [regime_confirme]

    for label in labels[1:]:
        if label == candidat:
            compteur_candidat += 1
        else:
            candidat = label
            compteur_candidat = 1

        if candidat != regime_confirme and compteur_candidat >= min_jours:
            regime_confirme = candidat

        resultat.append(regime_confirme)

    return resultat
