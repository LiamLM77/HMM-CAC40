# Cahier des charges — Projet HMM Régimes de Marché CAC40

## 1. Objectif

Construire une stratégie de gestion de portefeuille actions du CAC40 qui **bat l'indice CAC40** en :

1. Détectant le **régime de marché** courant (Haussier / Neutre / Baissier) via un **Hidden Markov Model (HMM)** entraîné sur les rendements et indicateurs de risque du CAC40.
2. Calculant le **bêta** de chaque action du CAC40 par rapport à l'indice.
3. **Allouant les fonds** dynamiquement :
   - Régime **Baissier** → actions défensives, bêta < 0.8 (ex: utilities, santé, conso de base).
   - Régime **Haussier** → actions offensives, bêta > 1.2 (ex: bancaires, techs, cycliques).
   - Régime **Neutre** → allocation mixte / neutre (à définir en phase de calibrage, cf. [04_beta_allocation.md](04_beta_allocation.md)).
4. Présentant les résultats dans une **interface web Django** (Tailwind CSS + Chart.js).

## 2. Décisions validées

| Sujet | Décision |
|---|---|
| Nombre de régimes | 3 (Haussier / Neutre / Baissier) |
| Modèle de régime | HMM seul (pas de régression logit — abandonné) |
| Ré-entraînement HMM | Walk-forward (ré-entraîné périodiquement pendant le test) |
| Univers d'actions | CAC40 actuel (40 valeurs), pas de gestion du survivorship bias |
| Source de données | Yahoo Finance (`yfinance`), prix **Adjusted Close** (dividendes réinvestis) |
| Historique | 10 ans, fréquence journalière |
| Split train/test | 70 % / 30 % chronologique (pas de shuffle) |
| Fenêtre bêta | Glissante 252 jours, recalcul hebdomadaire, ajustement de Blume optionnel |
| Seuils bêta | Défensif < 0.8, Neutre 0.9–1.1, Offensif > 1.2 |
| Panier Régime Haussier | Top 10 actions par bêta le plus élevé (> 1.2) |
| Panier Régime Baissier | Top 10 actions par bêta le plus faible (< 0.8) |
| Panier Régime Neutre | Top 10 actions au bêta le plus proche de 1 (bande 0.9–1.1) |
| Anti-churn (limitation turnover) | Rééquilibrage hebdomadaire, mais on ne retrade que si le régime change OU si une action sort d'une zone tampon (buffer, cf. [04_beta_allocation.md](04_beta_allocation.md)) |
| Pondération portefeuille | Équipondérée au sein du panier sélectionné |
| Capital initial | 1 000 000 € |
| Coûts de transaction | Oui, 0.10 % par transaction (aller ou retour) |
| Interface | Django (apps `market_data`, `regimes`, `portfolio`, `dashboard`) + Tailwind CSS + Chart.js |
| Base de données | DuckDB (analytique / données de marché) + SQLite (modèles Django : config, résultats, historique de backtests) |
| Métriques | Rendement annualisé, volatilité, Sharpe, Sortino, Calmar, Max Drawdown, VaR, alpha/bêta vs CAC40 |

## 3. Hors périmètre (pour l'instant)

- Prise en compte des dividendes détachés dans le calcul du bêta (à trancher en phase données, cf. [02_donnees_marche.md](02_donnees_marche.md)).
- Composition historique réelle du CAC40 (survivorship bias assumé et documenté).
- Modèle logit (abandonné au profit du HMM seul).
- Optimisation de portefeuille (Markowitz, risk parity...) — allocation équipondérée simple pour la V1.

## 4. Documents associés

- [02_donnees_marche.md](02_donnees_marche.md) — Sources de données, univers, période
- [03_modele_hmm.md](03_modele_hmm.md) — Spécification du HMM (variables, nombre d'états, entraînement)
- [04_beta_allocation.md](04_beta_allocation.md) — Calcul du bêta et règles d'allocation
- [05_backtest_metriques.md](05_backtest_metriques.md) — Méthodologie de backtest et métriques
- [06_architecture_technique.md](06_architecture_technique.md) — Architecture logicielle Django
- [07_roadmap.md](07_roadmap.md) — Feuille de route / plan de développement
