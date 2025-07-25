#!/usr/bin/env python3
"""
Test de la stratégie XAUUSD Sharpe 1 Simple sur tous les timeframes
Génère des rapports d'analyse complets pour chaque timeframe
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
sys.path.append('src/analysis')

from strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple, calculate_metrics
from generate_strategy_analysis import create_detailed_analysis

def test_all_timeframes_xauusd():
    """Teste la stratégie sur tous les timeframes XAUUSD disponibles"""
    
    print("🚀 TEST MULTI-TIMEFRAMES XAUUSD")
    print("=" * 50)
    
    # Timeframes disponibles
    timeframes = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1']
    
    # Stockage des résultats
    all_results = {}
    summary_results = []
    
    for timeframe in timeframes:
        print(f"\n📊 Test {timeframe}...")
        
        # Vérification du fichier de données
        csv_path = f"data/raw/XAUUSD_{timeframe}_mt5.csv"
        
        if not os.path.exists(csv_path):
            print(f"❌ Fichier non trouvé: {csv_path}")
            continue
        
        try:
            # Chargement des données
            df = pd.read_csv(csv_path)
            df['Date'] = pd.to_datetime(df['Date'])
            
            print(f"✅ {len(df)} bougies chargées")
            print(f"📅 Période: {df['Date'].min()} à {df['Date'].max()}")
            
            # Application de la stratégie
            trades, df_signals = strategie_xauusd_sharpe1_simple(df, 'XAUUSD', timeframe)
            metrics = calculate_metrics(trades)
            
            # Stockage des résultats
            all_results[timeframe] = {
                'trades': trades,
                'metrics': metrics,
                'data': df_signals
            }
            
            # Ajout au résumé
            summary_results.append({
                'Timeframe': timeframe,
                'Total_Trades': metrics['total_trades'],
                'Win_Rate': metrics['win_rate'],
                'Total_Return': metrics['total_return'],
                'Avg_Win': metrics['avg_win'],
                'Avg_Loss': metrics['avg_loss'],
                'Profit_Factor': metrics['profit_factor'],
                'Max_Drawdown': metrics['max_drawdown'],
                'Sharpe_Ratio': metrics['sharpe_ratio']
            })
            
            # Affichage des résultats
            print(f"📈 Résultats {timeframe}:")
            print(f"   • Trades: {metrics['total_trades']}")
            print(f"   • Win Rate: {metrics['win_rate']:.2f}%")
            print(f"   • Retour: {metrics['total_return']:.2f}%")
            print(f"   • Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"   • Sharpe: {metrics['sharpe_ratio']:.2f}")
            print(f"   • Drawdown: {metrics['max_drawdown']:.2f}%")
            
            # Génération de l'analyse détaillée
            print(f"🔍 Génération de l'analyse {timeframe}...")
            analysis_dir = create_detailed_analysis('XAUUSD', timeframe)
            
            if analysis_dir:
                print(f"✅ Analyse {timeframe} générée: {analysis_dir}")
            
        except Exception as e:
            print(f"❌ Erreur pour {timeframe}: {e}")
            continue
    
    # Création du rapport de synthèse
    if summary_results:
        create_summary_report(summary_results, all_results)
    
    return summary_results, all_results

def create_summary_report(summary_results, all_results):
    """Crée un rapport de synthèse pour tous les timeframes"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_dir = f"results/analysis/XAUUSD_multi_timeframe_summary_{timestamp}"
    os.makedirs(summary_dir, exist_ok=True)
    
    # Conversion en DataFrame
    df_summary = pd.DataFrame(summary_results)
    
    # Sauvegarde du résumé CSV
    summary_csv = f"{summary_dir}/resume_tous_timeframes.csv"
    df_summary.to_csv(summary_csv, index=False)
    
    # Création du rapport Markdown
    report_file = f"{summary_dir}/rapport_synthese_multitimeframes.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Rapport de Synthèse - XAUUSD Multi-Timeframes\n\n")
        f.write(f"**Date d'analyse**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Résumé exécutif
        f.write("## 📊 RÉSUMÉ EXÉCUTIF\n\n")
        f.write(f"- **Symbole**: XAUUSD\n")
        f.write(f"- **Timeframes testés**: {', '.join(df_summary['Timeframe'].tolist())}\n")
        f.write(f"- **Total analyses**: {len(df_summary)}\n\n")
        
        # Tableau de synthèse
        f.write("## 📈 SYNTHÈSE PAR TIMEFRAME\n\n")
        f.write("| Timeframe | Trades | Win Rate | Retour | Profit Factor | Sharpe | Drawdown | Score |\n")
        f.write("|-----------|--------|----------|--------|---------------|--------|----------|-------|\n")
        
        for _, row in df_summary.iterrows():
            # Calcul du score
            score = calculate_score(row)
            score_emoji = "🟢" if score >= 6 else "🟡" if score >= 4 else "🔴"
            
            f.write(f"| {row['Timeframe']} | {row['Total_Trades']} | {row['Win_Rate']:.1f}% | {row['Total_Return']:.1f}% | {row['Profit_Factor']:.2f} | {row['Sharpe_Ratio']:.1f} | {row['Max_Drawdown']:.1f}% | {score_emoji} {score}/7 |\n")
        
        f.write("\n")
        
        # Meilleurs timeframes par métrique
        f.write("## 🏆 MEILLEURS TIMEFRAMES PAR MÉTRIQUE\n\n")
        
        if len(df_summary) > 0:
            # Meilleur retour
            best_return = df_summary.loc[df_summary['Total_Return'].idxmax()]
            f.write(f"**💰 Meilleur retour**: {best_return['Timeframe']} ({best_return['Total_Return']:.2f}%)\n")
            
            # Meilleur Sharpe
            best_sharpe = df_summary.loc[df_summary['Sharpe_Ratio'].idxmax()]
            f.write(f"**📊 Meilleur Sharpe**: {best_sharpe['Timeframe']} ({best_sharpe['Sharpe_Ratio']:.2f})\n")
            
            # Meilleur win rate
            best_winrate = df_summary.loc[df_summary['Win_Rate'].idxmax()]
            f.write(f"**🎯 Meilleur win rate**: {best_winrate['Timeframe']} ({best_winrate['Win_Rate']:.2f}%)\n")
            
            # Meilleur profit factor
            best_pf = df_summary.loc[df_summary['Profit_Factor'].idxmax()]
            f.write(f"**⚖️ Meilleur profit factor**: {best_pf['Timeframe']} ({best_pf['Profit_Factor']:.2f})\n")
            
            # Meilleur drawdown
            best_dd = df_summary.loc[df_summary['Max_Drawdown'].idxmin()]
            f.write(f"**📉 Meilleur drawdown**: {best_dd['Timeframe']} ({best_dd['Max_Drawdown']:.2f}%)\n")
        
        f.write("\n")
        
        # Recommandations
        f.write("## 💡 RECOMMANDATIONS\n\n")
        
        # Timeframe recommandé
        if len(df_summary) > 0:
            # Calcul du score global pour chaque timeframe
            df_summary['Score'] = df_summary.apply(calculate_score, axis=1)
            best_overall = df_summary.loc[df_summary['Score'].idxmax()]
            
            f.write(f"**🎯 TIMEFRAME RECOMMANDÉ**: {best_overall['Timeframe']}\n")
            f.write(f"- Score: {best_overall['Score']}/7\n")
            f.write(f"- Retour: {best_overall['Total_Return']:.2f}%\n")
            f.write(f"- Win Rate: {best_overall['Win_Rate']:.2f}%\n")
            f.write(f"- Profit Factor: {best_overall['Profit_Factor']:.2f}\n\n")
        
        # Recommandations générales
        f.write("### Recommandations Générales:\n\n")
        
        # Vérification des patterns
        high_winrate = df_summary[df_summary['Win_Rate'] > 55]
        if len(high_winrate) > 0:
            f.write(f"✅ **Timeframes avec bon win rate** (>55%): {', '.join(high_winrate['Timeframe'].tolist())}\n")
        
        high_profit_factor = df_summary[df_summary['Profit_Factor'] > 2]
        if len(high_profit_factor) > 0:
            f.write(f"✅ **Timeframes avec excellent profit factor** (>2): {', '.join(high_profit_factor['Timeframe'].tolist())}\n")
        
        low_drawdown = df_summary[df_summary['Max_Drawdown'] < 30]
        if len(low_drawdown) > 0:
            f.write(f"✅ **Timeframes avec faible drawdown** (<30%): {', '.join(low_drawdown['Timeframe'].tolist())}\n")
        
        # Conclusion
        f.write("\n## 🎯 CONCLUSION\n\n")
        
        total_trades = df_summary['Total_Trades'].sum()
        avg_return = df_summary['Total_Return'].mean()
        avg_winrate = df_summary['Win_Rate'].mean()
        
        f.write(f"**Résumé global**:\n")
        f.write(f"- Total trades analysés: {total_trades}\n")
        f.write(f"- Retour moyen: {avg_return:.2f}%\n")
        f.write(f"- Win rate moyen: {avg_winrate:.2f}%\n")
        f.write(f"- Timeframes testés: {len(df_summary)}\n\n")
        
        if avg_winrate > 50 and avg_return > 100:
            f.write("🟢 **STRATÉGIE GLOBALE EXCELLENTE** - Performances solides sur tous les timeframes\n")
        elif avg_winrate > 45 and avg_return > 50:
            f.write("🟡 **STRATÉGIE GLOBALE BONNE** - Performances acceptables avec quelques ajustements\n")
        else:
            f.write("🔴 **STRATÉGIE GLOBALE À AMÉLIORER** - Optimisation requise\n")
    
    print(f"\n✅ Rapport de synthèse généré: {report_file}")
    print(f"📊 Résumé CSV: {summary_csv}")
    
    return summary_dir

def calculate_score(row):
    """Calcule le score de 0 à 7 pour un timeframe"""
    score = 0
    
    # Win rate (0-2 points)
    if row['Win_Rate'] > 55:
        score += 2
    elif row['Win_Rate'] > 50:
        score += 1
    
    # Profit Factor (0-2 points)
    if row['Profit_Factor'] > 2:
        score += 2
    elif row['Profit_Factor'] > 1.5:
        score += 1
    
    # Sharpe Ratio (0-2 points)
    if row['Sharpe_Ratio'] > 2:
        score += 2
    elif row['Sharpe_Ratio'] > 1:
        score += 1
    
    # Drawdown (0-1 point)
    if row['Max_Drawdown'] < 30:
        score += 1
    
    return score

def main():
    """Fonction principale"""
    print("🚀 TEST MULTI-TIMEFRAMES XAUUSD COMPLET")
    print("=" * 60)
    
    # Test de tous les timeframes
    summary_results, all_results = test_all_timeframes_xauusd()
    
    if summary_results:
        print(f"\n✅ ANALYSE TERMINÉE!")
        print(f"📊 {len(summary_results)} timeframes analysés")
        
        # Affichage du résumé final
        print(f"\n📈 RÉSUMÉ FINAL:")
        for result in summary_results:
            score = calculate_score(result)
            status = "🟢" if score >= 6 else "🟡" if score >= 4 else "🔴"
            print(f"{status} {result['Timeframe']}: {result['Total_Trades']} trades, {result['Win_Rate']:.1f}% win, {result['Total_Return']:.1f}% retour, Score: {score}/7")
    
    print(f"\n📁 Tous les rapports sont disponibles dans results/analysis/")

if __name__ == "__main__":
    main() 