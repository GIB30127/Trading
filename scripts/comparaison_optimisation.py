#!/usr/bin/env python3
"""
Comparaison des Méthodes d'Optimisation
Compare les résultats de l'optimisation génétique et du RL
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour importer les modules
sys.path.append('src/strategies')
from strategie_xauusd_sharpe1_simple import calculate_metrics

def analyze_drawdown_problem():
    """Analyse le problème du drawdown"""
    print("🔍 ANALYSE DU PROBLÈME DE DRAWDOWN")
    print("=" * 50)
    
    # Chargement des résultats multi-timeframes
    analysis_dir = "results/analysis"
    summary_dirs = [d for d in os.listdir(analysis_dir) if d.startswith("XAUUSD_multi_timeframe_summary_")]
    
    if not summary_dirs:
        print("❌ Aucun rapport de synthèse trouvé")
        return
    
    latest_dir = max(summary_dirs)
    csv_file = os.path.join(analysis_dir, latest_dir, "resume_tous_timeframes.csv")
    
    if not os.path.exists(csv_file):
        print(f"❌ Fichier CSV non trouvé: {csv_file}")
        return
    
    df = pd.read_csv(csv_file)
    
    print("📊 ANALYSE DES DRAWDOWNS PAR TIMEFRAME:")
    print()
    
    for _, row in df.iterrows():
        if row['Total_Trades'] == 0:
            continue
            
        drawdown = row['Max_Drawdown']
        status = "🟢" if drawdown < 30 else "🟡" if drawdown < 50 else "🔴"
        
        print(f"{status} {row['Timeframe']}: {drawdown:.1f}% drawdown")
        
        if drawdown > 100:
            print(f"   ⚠️  DRAWDOWN CRITIQUE - Optimisation urgente requise")
        elif drawdown > 50:
            print(f"   ⚠️  Drawdown élevé - Optimisation recommandée")
        elif drawdown < 20:
            print(f"   ✅ Drawdown excellent - Stratégie stable")
    
    print()
    print("🎯 CAUSES PROBABLES DU DRAWDOWN ÉLEVÉ:")
    print("1. Stop loss trop large ou inexistant")
    print("2. Position sizing inadapté")
    print("3. Corrélation des trades (tous dans la même direction)")
    print("4. Manque de filtres de volatilité")
    print("5. Trailing stop inefficace")
    print("6. Pas de limite sur le nombre de positions simultanées")

def propose_solutions():
    """Propose des solutions pour réduire le drawdown"""
    print("\n💡 SOLUTIONS PROPOSÉES")
    print("=" * 50)
    
    solutions = {
        "Stop Loss Dynamique": {
            "description": "Stop loss basé sur l'ATR pour s'adapter à la volatilité",
            "parametres": ["stop_loss_atr"],
            "impact": "Réduction immédiate du drawdown"
        },
        "Position Sizing": {
            "description": "Taille de position basée sur le risque par trade",
            "parametres": ["risk_per_trade", "max_positions"],
            "impact": "Contrôle du risque global"
        },
        "Filtres de Volatilité": {
            "description": "Filtres supplémentaires pour éviter les marchés trop volatils",
            "parametres": ["volatility_filter", "atr_threshold"],
            "impact": "Réduction des faux signaux"
        },
        "Trailing Stop Amélioré": {
            "description": "Trailing stop plus réactif et adaptatif",
            "parametres": ["trail_atr", "trail_activation"],
            "impact": "Protection des gains"
        },
        "Corrélation des Positions": {
            "description": "Limitation des positions dans la même direction",
            "parametres": ["max_long_positions", "max_short_positions"],
            "impact": "Diversification du risque"
        },
        "Time-based Exit": {
            "description": "Sortie automatique après un certain temps",
            "parametres": ["max_hold_time"],
            "impact": "Éviter les positions qui traînent"
        }
    }
    
    for i, (solution, details) in enumerate(solutions.items(), 1):
        print(f"{i}. {solution}")
        print(f"   📝 {details['description']}")
        print(f"   ⚙️  Paramètres: {', '.join(details['parametres'])}")
        print(f"   🎯 Impact: {details['impact']}")
        print()

def compare_optimization_methods():
    """Compare les méthodes d'optimisation"""
    print("\n🔄 COMPARAISON DES MÉTHODES D'OPTIMISATION")
    print("=" * 50)
    
    methods = {
        "Optimisation Génétique": {
            "avantages": [
                "Exploration large de l'espace des paramètres",
                "Peut trouver des optima globaux",
                "Robuste aux minima locaux",
                "Parallélisable"
            ],
            "inconvenients": [
                "Temps de calcul élevé",
                "Risque de suroptimisation",
                "Pas de garantie de convergence"
            ],
            "meilleur_pour": "Optimisation multi-objectifs, recherche de paramètres optimaux"
        },
        "Reinforcement Learning": {
            "avantages": [
                "Apprentissage adaptatif",
                "Peut s'adapter aux changements de marché",
                "Optimisation continue",
                "Gestion d'état complexe"
            ],
            "inconvenients": [
                "Courbe d'apprentissage",
                "Difficile à interpréter",
                "Risque d'overfitting",
                "Complexité de mise en œuvre"
            ],
            "meilleur_pour": "Adaptation en temps réel, gestion d'état complexe"
        },
        "Optimisation Manuelle": {
            "avantages": [
                "Contrôle total",
                "Compréhension des paramètres",
                "Rapide à implémenter",
                "Pas de suroptimisation"
            ],
            "inconvenients": [
                "Biais humain",
                "Exploration limitée",
                "Pas de garantie d'optimalité",
                "Temps humain important"
            ],
            "meilleur_pour": "Ajustements fins, compréhension de la stratégie"
        }
    }
    
    for method, details in methods.items():
        print(f"🔹 {method}")
        print(f"   ✅ Avantages:")
        for avantage in details['avantages']:
            print(f"      • {avantage}")
        print(f"   ❌ Inconvénients:")
        for inconvenient in details['inconvenients']:
            print(f"      • {inconvenient}")
        print(f"   🎯 Meilleur pour: {details['meilleur_pour']}")
        print()

def recommend_approach():
    """Recommandation d'approche"""
    print("\n🎯 RECOMMANDATION D'APPROCHE")
    print("=" * 50)
    
    print("📋 PLAN D'ACTION RECOMMANDÉ:")
    print()
    print("1️⃣ PHASE 1: Optimisation Génétique (Priorité)")
    print("   • Objectif: Réduire le drawdown < 30%")
    print("   • Focus: Stop loss, position sizing, trailing stop")
    print("   • Durée: 2-3 heures d'optimisation")
    print("   • Résultat attendu: Paramètres de base optimisés")
    print()
    
    print("2️⃣ PHASE 2: Ajustements Manuels")
    print("   • Objectif: Affiner les paramètres")
    print("   • Focus: Filtres de volatilité, corrélation des positions")
    print("   • Durée: 1-2 heures de tests")
    print("   • Résultat attendu: Stratégie stable")
    print()
    
    print("3️⃣ PHASE 3: Reinforcement Learning (Optionnel)")
    print("   • Objectif: Adaptation en temps réel")
    print("   • Focus: Gestion d'état, adaptation aux changements")
    print("   • Durée: Plusieurs jours d'entraînement")
    print("   • Résultat attendu: Stratégie adaptative")
    print()
    
    print("⚡ PARAMÈTRES PRIORITAIRES À OPTIMISER:")
    print("   • stop_loss_atr: 1.0 - 4.0")
    print("   • max_positions: 1 - 3")
    print("   • trail_atr: 0.3 - 2.0")
    print("   • risk_per_trade: 0.5 - 3.0")
    print("   • volatility_filter: Nouveau paramètre")
    print("   • max_hold_time: Nouveau paramètre")

def create_optimization_plan():
    """Crée un plan d'optimisation détaillé"""
    print("\n📋 PLAN D'OPTIMISATION DÉTAILLÉ")
    print("=" * 50)
    
    plan = {
        "Étape 1": {
            "action": "Lancer l'optimisation génétique",
            "commande": "python optimisation_genetique_drawdown.py",
            "objectif": "Réduire drawdown < 30%",
            "duree": "2-3 heures"
        },
        "Étape 2": {
            "action": "Analyser les résultats",
            "commande": "python afficher_resultats_multitimeframes.py",
            "objectif": "Vérifier l'amélioration",
            "duree": "30 minutes"
        },
        "Étape 3": {
            "action": "Ajustements manuels si nécessaire",
            "commande": "Modification des paramètres",
            "objectif": "Affiner les performances",
            "duree": "1-2 heures"
        },
        "Étape 4": {
            "action": "Test multi-timeframes",
            "commande": "python test_all_timeframes_xauusd.py",
            "objectif": "Validation complète",
            "duree": "1 heure"
        }
    }
    
    for etape, details in plan.items():
        print(f"🔹 {etape}")
        print(f"   📝 Action: {details['action']}")
        print(f"   💻 Commande: {details['commande']}")
        print(f"   🎯 Objectif: {details['objectif']}")
        print(f"   ⏱️  Durée: {details['duree']}")
        print()

def main():
    """Fonction principale"""
    print("🔍 ANALYSE COMPLÈTE DU PROBLÈME DE DRAWDOWN")
    print("=" * 70)
    
    # Analyse du problème
    analyze_drawdown_problem()
    
    # Solutions proposées
    propose_solutions()
    
    # Comparaison des méthodes
    compare_optimization_methods()
    
    # Recommandation
    recommend_approach()
    
    # Plan d'optimisation
    create_optimization_plan()
    
    print("\n🚀 PROCHAINES ÉTAPES:")
    print("1. Lancer l'optimisation génétique")
    print("2. Analyser les résultats")
    print("3. Ajuster si nécessaire")
    print("4. Valider sur tous les timeframes")
    
    print("\n💡 CONSEIL: Commencez par l'optimisation génétique sur H4 (meilleur drawdown actuel)")

if __name__ == "__main__":
    main() 