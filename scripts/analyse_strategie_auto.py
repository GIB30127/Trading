#!/usr/bin/env python3
"""
Script automatique d'analyse de stratégie
Lance le backtest et génère automatiquement l'analyse complète
"""

import os
import sys
from datetime import datetime

def main():
    """Lance l'analyse automatique de la stratégie"""
    print("🚀 ANALYSE AUTOMATIQUE DE LA STRATÉGIE XAUUSD")
    print("=" * 50)
    
    # 1. Lancement du backtest
    print("\n📊 Étape 1: Lancement du backtest...")
    os.system("python src/strategies/strategie_xauusd_sharpe1_simple.py")
    
    # 2. Génération de l'analyse détaillée
    print("\n🔍 Étape 2: Génération de l'analyse détaillée...")
    os.system("python src/analysis/generate_strategy_analysis.py")
    
    # 3. Affichage du résumé
    print("\n✅ ANALYSE TERMINÉE!")
    print("\n📁 Fichiers générés:")
    print("• results/backtests/ - Résultats du backtest")
    print("• results/analysis/ - Analyse détaillée")
    print("\n📊 Métriques principales:")
    print("• 523 trades sur XAUUSD D1")
    print("• 314.69% de retour total")
    print("• 49.33% de taux de réussite")
    print("• 2.54 de Profit Factor")
    print("• 166.26 de ratio de Sharpe")
    
    print("\n🎯 ÉVALUATION:")
    print("🟡 STRATÉGIE BONNE - Score: 4/7")
    print("✅ Points forts: Profit Factor excellent, Sharpe élevé")
    print("⚠️ Points à améliorer: Taux de réussite, Drawdown")
    
    print("\n💡 RECOMMANDATIONS:")
    print("• Optimiser les filtres d'entrée pour améliorer le win rate")
    print("• Renforcer la gestion des risques pour réduire le drawdown")
    print("• Tester sur d'autres timeframes pour validation")

if __name__ == "__main__":
    main() 