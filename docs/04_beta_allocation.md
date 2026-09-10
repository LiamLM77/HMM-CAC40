# Calcul du bêta et règles d'allocation

## 1. Calcul du bêta

### 1.1 Formule

Pour chaque action $i$, le bêta par rapport au CAC40 est estimé par régression linéaire des rendements :

$$r_{i,t} = \alpha_i + \beta_i \cdot r_{CAC40,t} + \varepsilon_t$$

$$\beta_i = \frac{\text{Cov}(r_i, r_{CAC40})}{\text{Var}(r_{CAC40})}$$

### 1.2 Fenêtre de calcul

- **Fenêtre glissante de 252 jours de bourse** (≈ 1 an), recalculée **chaque semaine** (alignée sur la fréquence de rééquilibrage du portefeuille).
- **Pas de look-ahead bias** : au jour $t$, seules les données des 252 jours précédant (et incluant) $t$ sont utilisées — jamais de données futures.

### 1.3 Pourquoi ce choix (rappel des arbitrages)

| Approche | Avantages | Inconvénients | Retenu ? |
|---|---|---|---|
| Bêta fixe (toute la période) | Stable, peu bruité | Ignore l'évolution du profil de risque, risque de look-ahead bias si mal implémenté | ❌ |
| Glissant 60 jours | Très réactif aux changements récents | Bruité, instable, sensible aux outliers | ❌ |
| **Glissant 252 jours** | Bon compromis stabilité/réactivité, standard académique/pro | Retard de quelques mois pour capter un changement structurel | ✅ |

### 1.4 Ajustement de Blume (optionnel)

$$\beta_{ajusté} = \frac{2}{3} \beta_{brut} + \frac{1}{3} \times 1$$

- Réduit le bruit d'estimation en "tirant" les bêtas extrêmes vers 1 (mean reversion empirique des bêtas dans le temps).
- **Décision (Phase 3, comparaison empirique sur 471 semaines)** : Blume retenu. Turnover total 1681 vs 1940 avec le bêta brut (-13 %), taille moyenne de panier quasi identique (9.11 vs 9.67). `settings.UTILISER_BLUME = True`.

## 2. Seuils de classification

| Régime de marché détecté | Critère de sélection des actions | Label bêta |
|---|---|---|
| Baissier | $\beta_i < 0.8$ | Défensif |
| Neutre | $0.9 \le \beta_i \le 1.1$ | Neutre |
| Haussier | $\beta_i > 1.2$ | Offensif |

- Les actions avec $0.8 \le \beta_i < 0.9$ ou $1.1 < \beta_i \le 1.2$ sont dans une **zone grise**, non éligibles à un panier tant qu'elles n'ont pas franchi clairement un seuil (évite les allers-retours de classification dus au bruit).

## 3. Sélection du panier actif

- À chaque date de rééquilibrage, on identifie le régime courant (sortie du HMM, cf. [03_modele_hmm.md](03_modele_hmm.md)) puis on sélectionne le panier correspondant :
  - **Haussier** → **Top 10 actions** classées par bêta décroissant parmi celles avec $\beta > 1.2$.
  - **Baissier** → **Top 10 actions** classées par bêta croissant (les plus faibles) parmi celles avec $\beta < 0.8$.
  - **Neutre** → **Top 10 actions** dont $|\beta - 1|$ est le plus faible, dans la bande $[0.9, 1.1]$.
- S'il y a moins de 10 actions éligibles dans un panier à une date donnée, le portefeuille est investi sur les actions disponibles uniquement (pas de complément arbitraire par une autre logique).

## 4. Pondération

- **Équipondérée** : chaque action du panier sélectionné reçoit un poids $1/N$ (N = nombre d'actions effectivement retenues, ≤ 10).
- Pas de pondération par capitalisation ni par inverse-volatilité pour la V1 (simplicité, cohérent avec le niveau du projet).

## 5. Limitation du turnover (anti-churn)

Le rééquilibrage est calculé chaque semaine, mais **le portefeuille n'est retouché que si nécessaire**, selon la règle suivante :

1. **Changement de régime** (Haussier ↔ Neutre ↔ Baissier) → rebalancement complet obligatoire vers le nouveau panier.
2. **Régime inchangé** → on applique une **zone tampon (buffer)** pour limiter le nombre de transactions :
   - Une action déjà en portefeuille reste en portefeuille tant qu'elle demeure dans le **top 15** du classement bêta du panier courant (au lieu du top 10 strict).
   - Une action hors portefeuille n'entre que si elle apparaît dans le **top 10** strict.
   - Cette règle évite de vendre/racheter une action qui oscille entre le rang 9 et 11 d'une semaine à l'autre (bruit de classement), ce qui réduirait inutilement la performance nette de frais.
3. Si le nombre d'actions éligibles au panier change fortement (ex: krach soudain réduisant drastiquement le nombre d'actions défensives disponibles), le portefeuille s'ajuste immédiatement en conséquence (priorité au respect des critères de risque sur la limitation de turnover).

## 6. Coûts de transaction

- **0.10 % du montant de chaque transaction** (achat ou vente), appliqué sur le backtest.
- Impact direct sur la performance nette — permet de mesurer si la stratégie reste rentable après frais réalistes.
