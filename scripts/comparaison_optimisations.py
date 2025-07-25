#!/usr/bin/env python3
"""
Comparaison des Résultats d'Optimisation
Compare les résultats des différentes méthodes d'optimisation
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def find_optimization_results():
    """Trouve tous les résultats d'optimisation"""
    results_dir = "results/optimization"
    
    if not os.path.exists(results_dir):
        return {}
    
    optimizations = {}
    
    # Chercher les dossiers d'optimisation
    for folder in os.listdir(results_dir):
        if folder.startswith("genetic_optimization_"):
            optimizations["Génétique (Drawdown)"] = os.path.join(results_dir, folder)
        elif folder.startswith("aggressive_optimization_"):
            optimizations["Agressive (Gains)"] = os.path.join(results_dir, folder)
        elif folder.startswith("rl_optimization_"):
            optimizations["Reinforcement Learning"] = os.path.join(results_dir, folder)
    
    return optimizations

def load_optimization_results(optimizations):
    """Charge les résultats des optimisations"""
    results = {}
    
    for name, folder_path in optimizations.items():
        # Chercher le fichier de paramètres optimaux
        param_file = os.path.join(folder_path, "parametres_optimaux.md")
        if os.path.exists(param_file):
            with open(param_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extraire les métriques
                metrics = {}
                lines = content.split('\n')
                for line in lines:
                    if '**Total Trades**' in line:
                        metrics['total_trades'] = int(line.split(':')[1].strip())
                    elif '**Win Rate**' in line:
                        metrics['win_rate'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Total Return**' in line:
                        metrics['total_return'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Max Drawdown**' in line:
                        metrics['max_drawdown'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Profit Factor**' in line:
                        metrics['profit_factor'] = float(line.split(':')[1].strip())
                    elif '**Sharpe Ratio**' in line:
                        metrics['sharpe_ratio'] = float(line.split(':')[1].strip())
                    elif '**Gain Moyen**' in line:
                        metrics['avg_win'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Perte Moyenne**' in line:
                        metrics['avg_loss'] = float(line.split(':')[1].strip().replace('%', ''))
                
                results[name] = {
                    'folder': folder_path,
                    'metrics': metrics,
                    'params_file': param_file
                }
    
    return results

def display_comparison_table(results):
    """Affiche un tableau de comparaison"""
    print("\n📊 COMPARAISON DES OPTIMISATIONS")
    print("=" * 80)
    
    if not results:
        print("❌ Aucun résultat d'optimisation trouvé")
        return
    
    # Création du tableau
    print(f"{'Méthode':<25} {'Trades':<8} {'Win Rate':<10} {'Retour':<10} {'Drawdown':<10} {'PF':<6} {'Sharpe':<8}")
    print("-" * 80)
    
    for name, data in results.items():
        metrics = data['metrics']
        print(f"{name:<25} {metrics.get('total_trades', 0):<8} {metrics.get('win_rate', 0):<10.1f}% {metrics.get('total_return', 0):<10.1f}% {metrics.get('max_drawdown', 0):<10.1f}% {metrics.get('profit_factor', 0):<6.2f} {metrics.get('sharpe_ratio', 0):<8.1f}")
    
    print()

def analyze_best_methods(results):
    """Analyse les meilleures méthodes par critère"""
    print("🏆 MEILLEURS RÉSULTATS PAR CRITÈRE")
    print("=" * 50)
    
    if not results:
        return
    
    # Meilleur retour
    best_return = max(results.items(), key=lambda x: x[1]['metrics'].get('total_return', 0))
    print(f"💰 Meilleur retour: {best_return[0]} ({best_return[1]['metrics'].get('total_return', 0):.1f}%)")
    
    # Meilleur drawdown
    best_dd = min(results.items(), key=lambda x: x[1]['metrics'].get('max_drawdown', 1000))
    print(f"📉 Meilleur drawdown: {best_dd[0]} ({best_dd[1]['metrics'].get('max_drawdown', 0):.1f}%)")
    
    # Meilleur win rate
    best_wr = max(results.items(), key=lambda x: x[1]['metrics'].get('win_rate', 0))
    print(f"🎯 Meilleur win rate: {best_wr[0]} ({best_wr[1]['metrics'].get('win_rate', 0):.1f}%)")
    
    # Meilleur profit factor
    best_pf = max(results.items(), key=lambda x: x[1]['metrics'].get('profit_factor', 0))
    print(f"⚖️ Meilleur profit factor: {best_pf[0]} ({best_pf[1]['metrics'].get('profit_factor', 0):.2f})")
    
    # Meilleur Sharpe
    best_sharpe = max(results.items(), key=lambda x: x[1]['metrics'].get('sharpe_ratio', 0))
    print(f"📊 Meilleur Sharpe: {best_sharpe[0]} ({best_sharpe[1]['metrics'].get('sharpe_ratio', 0):.1f})")
    
    print()

def calculate_composite_score(metrics):
    """Calcule un score composite"""
    score = 0
    
    # Retour (0-30 points)
    return_val = metrics.get('total_return', 0)
    if return_val > 500:
        score += 30
    elif return_val > 300:
        score += 25
    elif return_val > 200:
        score += 20
    elif return_val > 100:
        score += 15
    elif return_val > 50:
        score += 10
    
    # Drawdown (0-25 points)
    dd = metrics.get('max_drawdown', 100)
    if dd < 10:
        score += 25
    elif dd < 20:
        score += 20
    elif dd < 30:
        score += 15
    elif dd < 50:
        score += 10
    
    # Win Rate (0-20 points)
    wr = metrics.get('win_rate', 0)
    if wr > 60:
        score += 20
    elif wr > 55:
        score += 15
    elif wr > 50:
        score += 10
    
    # Profit Factor (0-15 points)
    pf = metrics.get('profit_factor', 0)
    if pf > 4:
        score += 15
    elif pf > 3:
        score += 12
    elif pf > 2:
        score += 8
    
    # Sharpe Ratio (0-10 points)
    sharpe = metrics.get('sharpe_ratio', 0)
    if sharpe > 3:
        score += 10
    elif sharpe > 2:
        score += 8
    elif sharpe > 1:
        score += 5
    
    return score

def rank_methods(results):
    """Classe les méthodes par score composite"""
    print("🏅 CLASSEMENT PAR SCORE COMPOSITE")
    print("=" * 50)
    
    if not results:
        return
    
    # Calcul des scores
    ranked_methods = []
    for name, data in results.items():
        score = calculate_composite_score(data['metrics'])
        ranked_methods.append((name, score, data['metrics']))
    
    # Tri par score décroissant
    ranked_methods.sort(key=lambda x: x[1], reverse=True)
    
    # Affichage
    for i, (name, score, metrics) in enumerate(ranked_methods, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        print(f"{medal} {i}. {name} - Score: {score}/100")
        print(f"   📊 Retour: {metrics.get('total_return', 0):.1f}% | DD: {metrics.get('max_drawdown', 0):.1f}% | WR: {metrics.get('win_rate', 0):.1f}% | PF: {metrics.get('profit_factor', 0):.2f}")
    
    print()

def recommend_approach(results):
    """Recommandation d'approche basée sur les résultats"""
    print("💡 RECOMMANDATIONS")
    print("=" * 50)
    
    if not results:
        print("❌ Pas assez de données pour faire des recommandations")
        return
    
    # Analyse des patterns
    high_return_methods = [name for name, data in results.items() if data['metrics'].get('total_return', 0) > 300]
    low_dd_methods = [name for name, data in results.items() if data['metrics'].get('max_drawdown', 100) < 20]
    high_wr_methods = [name for name, data in results.items() if data['metrics'].get('win_rate', 0) > 55]
    
    print("📈 Méthodes avec gros gains (>300%):")
    if high_return_methods:
        for method in high_return_methods:
            print(f"   ✅ {method}")
    else:
        print("   ⚠️ Aucune méthode n'atteint 300% de retour")
    
    print("\n📉 Méthodes avec faible drawdown (<20%):")
    if low_dd_methods:
        for method in low_dd_methods:
            print(f"   ✅ {method}")
    else:
        print("   ⚠️ Aucune méthode n'a un drawdown < 20%")
    
    print("\n🎯 Méthodes avec bon win rate (>55%):")
    if high_wr_methods:
        for method in high_wr_methods:
            print(f"   ✅ {method}")
    else:
        print("   ⚠️ Aucune méthode n'a un win rate > 55%")
    
    # Recommandation finale
    print(f"\n🎯 RECOMMANDATION FINALE:")
    
    # Trouver la méthode avec le meilleur équilibre
    best_balanced = None
    best_score = 0
    
    for name, data in results.items():
        metrics = data['metrics']
        return_val = metrics.get('total_return', 0)
        dd = metrics.get('max_drawdown', 100)
        wr = metrics.get('win_rate', 0)
        
        # Score d'équilibre
        balance_score = (return_val / 100) * (1 - dd/100) * (wr / 100)
        
        if balance_score > best_score:
            best_score = balance_score
            best_balanced = name
    
    if best_balanced:
        print(f"   🏆 Méthode recommandée: {best_balanced}")
        metrics = results[best_balanced]['metrics']
        print(f"   📊 Retour: {metrics.get('total_return', 0):.1f}%")
        print(f"   📉 Drawdown: {metrics.get('max_drawdown', 0):.1f}%")
        print(f"   🎯 Win Rate: {metrics.get('win_rate', 0):.1f}%")
    
    print()

def save_comparison_report(results):
    """Sauvegarde un rapport de comparaison"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"results/comparison_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Rapport de Comparaison des Optimisations\n\n")
        f.write(f"**Date de comparaison**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📊 Résultats Comparés\n\n")
        f.write("| Méthode | Trades | Win Rate | Retour | Drawdown | Profit Factor | Sharpe |\n")
        f.write("|---------|--------|----------|--------|----------|---------------|--------|\n")
        
        for name, data in results.items():
            metrics = data['metrics']
            f.write(f"| {name} | {metrics.get('total_trades', 0)} | {metrics.get('win_rate', 0):.1f}% | {metrics.get('total_return', 0):.1f}% | {metrics.get('max_drawdown', 0):.1f}% | {metrics.get('profit_factor', 0):.2f} | {metrics.get('sharpe_ratio', 0):.1f} |\n")
        
        f.write("\n## 🏆 Meilleurs Résultats\n\n")
        
        # Meilleurs par critère
        best_return = max(results.items(), key=lambda x: x[1]['metrics'].get('total_return', 0))
        best_dd = min(results.items(), key=lambda x: x[1]['metrics'].get('max_drawdown', 1000))
        best_wr = max(results.items(), key=lambda x: x[1]['metrics'].get('win_rate', 0))
        
        f.write(f"- **Meilleur retour**: {best_return[0]} ({best_return[1]['metrics'].get('total_return', 0):.1f}%)\n")
        f.write(f"- **Meilleur drawdown**: {best_dd[0]} ({best_dd[1]['metrics'].get('max_drawdown', 0):.1f}%)\n")
        f.write(f"- **Meilleur win rate**: {best_wr[0]} ({best_wr[1]['metrics'].get('win_rate', 0):.1f}%)\n")
        
        f.write("\n## 💡 Recommandations\n\n")
        
        # Recommandations basées sur les objectifs
        f.write("### Pour maximiser les gains:\n")
        high_return_methods = [name for name, data in results.items() if data['metrics'].get('total_return', 0) > 200]
        for method in high_return_methods:
            f.write(f"- {method}\n")
        
        f.write("\n### Pour minimiser le risque:\n")
        low_dd_methods = [name for name, data in results.items() if data['metrics'].get('max_drawdown', 100) < 30]
        for method in low_dd_methods:
            f.write(f"- {method}\n")
        
        f.write("\n### Pour un équilibre optimal:\n")
        # Méthode avec le meilleur équilibre
        best_balanced = None
        best_score = 0
        
        for name, data in results.items():
            metrics = data['metrics']
            return_val = metrics.get('total_return', 0)
            dd = metrics.get('max_drawdown', 100)
            wr = metrics.get('win_rate', 0)
            
            balance_score = (return_val / 100) * (1 - dd/100) * (wr / 100)
            
            if balance_score > best_score:
                best_score = balance_score
                best_balanced = name
        
        if best_balanced:
            f.write(f"- {best_balanced}\n")
    
    print(f"📄 Rapport de comparaison sauvegardé: {report_file}")

def main():
    """Fonction principale"""
    print("📊 COMPARAISON DES RÉSULTATS D'OPTIMISATION")
    print("=" * 60)
    
    # Trouver les résultats
    optimizations = find_optimization_results()
    
    if not optimizations:
        print("❌ Aucun résultat d'optimisation trouvé")
        print("💡 Lancez d'abord quelques optimisations avec optimize.py")
        return
    
    print(f"✅ {len(optimizations)} optimisations trouvées:")
    for name in optimizations.keys():
        print(f"   • {name}")
    
    # Charger les résultats
    results = load_optimization_results(optimizations)
    
    if not results:
        print("❌ Impossible de charger les résultats")
        return
    
    # Affichage des comparaisons
    display_comparison_table(results)
    analyze_best_methods(results)
    rank_methods(results)
    recommend_approach(results)
    
    # Sauvegarde du rapport
    save_comparison_report(results)
    
    print("✅ Comparaison terminée!")

if __name__ == "__main__":
    main() 