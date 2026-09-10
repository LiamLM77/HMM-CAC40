# Modèle HMM — Détection des régimes de marché

## 1. Principe général

Un **Hidden Markov Model (HMM) Gaussien** est utilisé pour détecter, de manière **non supervisée**, les régimes cachés du marché à partir de séries d'observations calculées sur le CAC40 (`^FCHI`). Le modèle logit initialement envisagé est **abandonné** : seul le HMM est utilisé.

## 2. Nombre d'états cachés

- **3 régimes** :
  1. **Haussier** (bull) — rendements moyens positifs, volatilité modérée à faible.
  2. **Neutre** (sideways) — rendements proches de zéro, volatilité faible à modérée.
  3. **Baissier** (bear) — rendements moyens négatifs, volatilité élevée.
- L'**identification** (quel état numérique correspond à quel label) se fait **a posteriori**, en triant les états par la moyenne de rendement associée (état à moyenne la plus haute = Haussier, etc.), car le HMM ne connaît pas ces labels a priori.

## 3. Variables d'observation

| Variable | Description | Justification |
|---|---|---|
| **Rendement log** du CAC40 | $r_t = \ln(P_t / P_{t-1})$ | Variable principale, capte la direction du marché |
| **Volatilité réalisée glissante** | Écart-type des rendements sur fenêtre glissante (ex: 20 jours), annualisée | Capte le niveau de stress/incertitude du marché |
| **Spread de taux** | Différentiel de taux souverain (cf. [02_donnees_marche.md](02_donnees_marche.md)) | Variable macro lente, aide à distinguer les régimes structurels (ex: crise de dette) |

- **Volume écarté** : jugé trop bruité au niveau indice, sans signal de régime clair, risque d'ajouter du bruit sans gain d'information.
- **Type de covariance** : **diagonale** (`covariance_type="diag"`) plutôt que pleine, pour limiter le nombre de paramètres à estimer et réduire le risque de surapprentissage (moins de paramètres à estimer par état : variances seules, pas de covariances croisées).
- **Standardisation** : chaque variable est centrée-réduite (z-score) sur la période d'entraînement avant passage au HMM (les paramètres de standardisation du train sont réutilisés tels quels sur le test, pas de recalcul avec des données futures).

## 4. Entraînement et ré-entraînement (walk-forward)

- **Entraînement initial** : sur les 70 % de données les plus anciennes (période "train").
- **Walk-forward pendant le test** : le HMM est **ré-entraîné périodiquement** (fréquence à définir précisément en implémentation, proposition : tous les 3 mois / 63 jours de bourse) en utilisant uniquement les données disponibles jusqu'à la date courante (pas de fuite d'information vers le futur).
- À chaque date de rééquilibrage hebdomadaire du portefeuille, le régime utilisé est celui décodé par le **dernier modèle HMM disponible** à cette date (`predict` sur les nouvelles observations, pas de ré-estimation à chaque semaine — seulement au rythme du ré-entraînement walk-forward).

## 5. Décodage des régimes

- **Algorithme de Viterbi** pour obtenir la séquence d'états la plus probable (régime "officiel" à chaque date, utilisé pour trancher l'allocation).
- **Probabilités filtrées** (`predict_proba` / forward algorithm) également stockées, pour affichage dans le dashboard (ex: "probabilité 72 % Baissier / 20 % Neutre / 8 % Haussier") — utile pour visualiser l'incertitude de détection.

## 6. Risque d'overfitting — points de vigilance

- Nombre de paramètres limité par le choix de covariance diagonale (~3 états × (3 moyennes + 3 variances) + matrice de transition 3×3 ≈ 27 paramètres pour ~1750 observations en train → ratio raisonnable).
- Le **spread de taux**, à variation lente, peut introduire de l'autocorrélation et favoriser des régimes très persistants corrélés à des tendances macro plutôt qu'à des régimes de marché actions à proprement parler. **Point à valider empiriquement** : comparer les régimes obtenus avec/sans cette variable, vérifier la cohérence avec les crises connues (2018 Q4, COVID 2020, 2022 inflation/taux).
- Prévoir une **analyse de sensibilité** : faire tourner le HMM avec 2 puis 3 variables, comparer la stabilité des régimes détectés (nombre de transitions, durée moyenne des régimes) avant de figer la configuration finale.

## 7. Bibliothèque

- `hmmlearn` (`GaussianHMM`) en Python — implémentation standard, compatible avec les besoins (Viterbi, probabilités filtrées, covariance diagonale).

## 8. Validation qualitative

- Superposer visuellement les régimes détectés à la courbe du CAC40 sur la période complète (graphique dans le dashboard) pour une validation qualitative : les régimes baissiers doivent correspondre aux krachs/corrections connus (2020, 2022...).
- Validé : le krach COVID (fév-mars 2020) est détecté en régime baissier avec ~100 % de probabilité.

## 9. Stabilisation des régimes (Phase 4 — correctif)

Le walk-forward initial produisait un **whipsaw** (oscillation haussier/baissier quasi hebdomadaire) sur certaines périodes peu directionnelles, générant un turnover de portefeuille excessif. Deux correctifs ont été appliqués :

1. **Prior de transition "collant"** (`transmat_prior`, diagonale renforcée à `HMM_TRANSMAT_PRIOR_DIAGONAL = 20`) : favorise la persistance d'état lors de l'estimation Baum-Welch.
2. **Filtre de persistance causal** (`HMM_PERSISTANCE_MIN_JOURS = 5`) : un changement de régime n'est confirmé que s'il persiste au moins 5 jours de bourse consécutifs ; sinon le régime précédent est maintenu. Purement causal (aucune fuite d'information future).

Résultat : turnover hebdomadaire total passé de 1697 à 787 sur 471 semaines, répartition des régimes de test plus équilibrée (neutre 313 / haussier 255 / baissier 194 contre 106/444/212 avant correctif).
