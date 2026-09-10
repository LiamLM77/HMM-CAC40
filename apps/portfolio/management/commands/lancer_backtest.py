"""Lance le backtest complet sur la période de test et calcule les métriques de performance.

Usage : python manage.py lancer_backtest
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.market_data.services import duckdb_store
from apps.portfolio.models import ExecutionBacktest
from apps.portfolio.services import backtest_engine, metriques, transactions_store, valeur_store


class Command(BaseCommand):
    help = "Simule le portefeuille jour par jour sur la période de test et calcule les métriques."

    def handle(self, *args, **options):
        con = duckdb_store.obtenir_connexion(settings.DUCKDB_PATH)

        self.stdout.write("Simulation du backtest (rééquilibrage hebdomadaire, coûts de transaction)...")
        valeurs, transactions = backtest_engine.simuler_backtest(con)

        taux_sans_risque = con.execute(
            "SELECT AVG(taux) FROM taux_sans_risque WHERE date BETWEEN ? AND ?",
            [str(valeurs.index.min()), str(valeurs.index.max())],
        ).fetchone()[0]

        nb_lignes_valeurs = valeur_store.enregistrer_valeurs(con, valeurs)
        nb_lignes_transactions = transactions_store.enregistrer_transactions(con, transactions)
        con.close()

        metriques_portefeuille = metriques.calculer_toutes_les_metriques(
            valeurs["valeur_portefeuille"], taux_sans_risque
        )
        metriques_benchmark = metriques.calculer_toutes_les_metriques(
            valeurs["valeur_benchmark"], taux_sans_risque
        )
        alpha_annualise, beta_portefeuille = metriques.alpha_beta_vs_benchmark(
            metriques.rendements_quotidiens(valeurs["valeur_portefeuille"]),
            metriques.rendements_quotidiens(valeurs["valeur_benchmark"]),
        )
        cout_transactions_total = transactions["cout"].sum() if not transactions.empty else 0.0

        ExecutionBacktest.objects.create(
            date_debut_test=valeurs.index.min(),
            date_fin_test=valeurs.index.max(),
            capital_initial=settings.CAPITAL_INITIAL,
            capital_final_portefeuille=valeurs["valeur_portefeuille"].iloc[-1],
            rendement_annualise_portefeuille=metriques_portefeuille["rendement_annualise"],
            volatilite_portefeuille=metriques_portefeuille["volatilite_annualisee"],
            sharpe_portefeuille=metriques_portefeuille["sharpe"],
            sortino_portefeuille=metriques_portefeuille["sortino"],
            calmar_portefeuille=metriques_portefeuille["calmar"],
            max_drawdown_portefeuille=metriques_portefeuille["max_drawdown"],
            var_95_portefeuille=metriques_portefeuille["var_95"],
            capital_final_benchmark=valeurs["valeur_benchmark"].iloc[-1],
            rendement_annualise_benchmark=metriques_benchmark["rendement_annualise"],
            volatilite_benchmark=metriques_benchmark["volatilite_annualisee"],
            sharpe_benchmark=metriques_benchmark["sharpe"],
            max_drawdown_benchmark=metriques_benchmark["max_drawdown"],
            alpha_annualise=alpha_annualise,
            beta_portefeuille=beta_portefeuille,
            taux_sans_risque_moyen=taux_sans_risque,
            cout_transactions_total=cout_transactions_total,
        )

        self.stdout.write(self.style.SUCCESS(f"{nb_lignes_valeurs} jours simulés, {nb_lignes_transactions} transactions."))
        self._afficher_rapport(metriques_portefeuille, metriques_benchmark, valeurs, alpha_annualise, beta_portefeuille, cout_transactions_total)

    def _afficher_rapport(self, m_portefeuille, m_benchmark, valeurs, alpha, beta, cout_total):
        self.stdout.write(self.style.SUCCESS("\n=== Stratégie HMM ==="))
        self.stdout.write(f"  Capital final          : {valeurs['valeur_portefeuille'].iloc[-1]:,.0f} €")
        self.stdout.write(f"  Rendement annualisé     : {m_portefeuille['rendement_annualise']:.2%}")
        self.stdout.write(f"  Volatilité annualisée   : {m_portefeuille['volatilite_annualisee']:.2%}")
        self.stdout.write(f"  Sharpe / Sortino / Calmar : {m_portefeuille['sharpe']:.2f} / {m_portefeuille['sortino']:.2f} / {m_portefeuille['calmar']:.2f}")
        self.stdout.write(f"  Max Drawdown            : {m_portefeuille['max_drawdown']:.2%}")
        self.stdout.write(f"  VaR 95%                 : {m_portefeuille['var_95']:.2%}")
        self.stdout.write(f"  Coûts de transaction totaux : {cout_total:,.0f} €")

        self.stdout.write(self.style.SUCCESS("\n=== CAC40 (buy & hold) ==="))
        self.stdout.write(f"  Capital final          : {valeurs['valeur_benchmark'].iloc[-1]:,.0f} €")
        self.stdout.write(f"  Rendement annualisé     : {m_benchmark['rendement_annualise']:.2%}")
        self.stdout.write(f"  Volatilité annualisée   : {m_benchmark['volatilite_annualisee']:.2%}")
        self.stdout.write(f"  Sharpe                  : {m_benchmark['sharpe']:.2f}")
        self.stdout.write(f"  Max Drawdown            : {m_benchmark['max_drawdown']:.2%}")

        self.stdout.write(self.style.SUCCESS("\n=== Comparaison ==="))
        self.stdout.write(f"  Alpha annualisé vs CAC40 : {alpha:.2%}")
        self.stdout.write(f"  Bêta du portefeuille     : {beta:.2f}")
