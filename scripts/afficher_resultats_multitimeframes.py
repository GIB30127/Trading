#!/usr/bin/env python3
"""
Affichage des résultats multi-timeframes XAUUSD
Affiche un résumé visuel et interactif des performances
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
import warnings
warnings.filterwarnings('ignore')

console = Console()

def find_latest_summary():
    """Trouve le dernier rapport de synthèse"""
    analysis_dir = "results/analysis"
    
    if not os.path.exists(analysis_dir):
        return None
    
    # Chercher les dossiers de synthèse
    summary_dirs = [d for d in os.listdir(analysis_dir) if d.startswith("XAUUSD_multi_timeframe_summary_")]
    
    if not summary_dirs:
        return None
    
    # Prendre le plus récent
    latest_dir = max(summary_dirs)
    return os.path.join(analysis_dir, latest_dir)

def load_results():
    """Charge les résultats du dernier test"""
    summary_dir = find_latest_summary()
    
    if not summary_dir:
        print("[red]❌ Aucun rapport de synthèse trouvé[/red]")
        return None
    
    csv_file = os.path.join(summary_dir, "resume_tous_timeframes.csv")
    
    if not os.path.exists(csv_file):
        print(f"[red]❌ Fichier CSV non trouvé: {csv_file}[/red]")
        return None
    
    df = pd.read_csv(csv_file)
    return df, summary_dir

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

def display_summary_table(df):
    """Affiche le tableau de synthèse"""
    console.print("\n[bold blue]📊 RÉSULTATS MULTI-TIMEFRAMES XAUUSD[/bold blue]")
    
    table = Table(title="Synthèse des Performances")
    table.add_column("Timeframe", style="cyan", justify="center")
    table.add_column("Trades", style="green", justify="center")
    table.add_column("Win Rate", style="yellow", justify="center")
    table.add_column("Retour", style="magenta", justify="center")
    table.add_column("Profit Factor", style="blue", justify="center")
    table.add_column("Sharpe", style="red", justify="center")
    table.add_column("Drawdown", style="orange", justify="center")
    table.add_column("Score", style="bold", justify="center")
    
    for _, row in df.iterrows():
        if row['Total_Trades'] == 0:  # Skip les timeframes sans trades
            continue
            
        score = calculate_score(row)
        score_emoji = "🟢" if score >= 6 else "🟡" if score >= 4 else "🔴"
        
        table.add_row(
            row['Timeframe'],
            str(int(row['Total_Trades'])),
            f"{row['Win_Rate']:.1f}%",
            f"{row['Total_Return']:.1f}%",
            f"{row['Profit_Factor']:.2f}",
            f"{row['Sharpe_Ratio']:.1f}",
            f"{row['Max_Drawdown']:.1f}%",
            f"{score_emoji} {score}/7"
        )
    
    console.print(table)

def display_best_timeframes(df):
    """Affiche les meilleurs timeframes par métrique"""
    console.print("\n[bold yellow]🏆 MEILLEURS TIMEFRAMES PAR MÉTRIQUE[/bold yellow]")
    
    # Filtrer les timeframes avec des trades
    df_valid = df[df['Total_Trades'] > 0]
    
    if len(df_valid) == 0:
        console.print("[red]❌ Aucun timeframe valide trouvé[/red]")
        return
    
    best_return = df_valid.loc[df_valid['Total_Return'].idxmax()]
    best_sharpe = df_valid.loc[df_valid['Sharpe_Ratio'].idxmax()]
    best_winrate = df_valid.loc[df_valid['Win_Rate'].idxmax()]
    best_pf = df_valid.loc[df_valid['Profit_Factor'].idxmax()]
    best_dd = df_valid.loc[df_valid['Max_Drawdown'].idxmin()]
    
    console.print(f"💰 **Meilleur retour**: {best_return['Timeframe']} ({best_return['Total_Return']:.2f}%)")
    console.print(f"📊 **Meilleur Sharpe**: {best_sharpe['Timeframe']} ({best_sharpe['Sharpe_Ratio']:.2f})")
    console.print(f"🎯 **Meilleur win rate**: {best_winrate['Timeframe']} ({best_winrate['Win_Rate']:.2f}%)")
    console.print(f"⚖️ **Meilleur profit factor**: {best_pf['Timeframe']} ({best_pf['Profit_Factor']:.2f})")
    console.print(f"📉 **Meilleur drawdown**: {best_dd['Timeframe']} ({best_dd['Max_Drawdown']:.2f}%)")

def display_recommendations(df):
    """Affiche les recommandations"""
    console.print("\n[bold green]💡 RECOMMANDATIONS[/bold green]")
    
    # Filtrer les timeframes avec des trades
    df_valid = df[df['Total_Trades'] > 0]
    
    if len(df_valid) == 0:
        return
    
    # Calcul du score pour chaque timeframe
    df_valid['Score'] = df_valid.apply(calculate_score, axis=1)
    best_overall = df_valid.loc[df_valid['Score'].idxmax()]
    
    console.print(f"🎯 **TIMEFRAME RECOMMANDÉ**: {best_overall['Timeframe']}")
    console.print(f"   • Score: {best_overall['Score']}/7")
    console.print(f"   • Retour: {best_overall['Total_Return']:.2f}%")
    console.print(f"   • Win Rate: {best_overall['Win_Rate']:.2f}%")
    console.print(f"   • Profit Factor: {best_overall['Profit_Factor']:.2f}")
    
    console.print("\n[bold]Recommandations par catégorie:[/bold]")
    
    # Timeframes avec bon win rate
    high_winrate = df_valid[df_valid['Win_Rate'] > 55]
    if len(high_winrate) > 0:
        tf_list = ', '.join(high_winrate['Timeframe'].tolist())
        console.print(f"✅ **Win rate élevé** (>55%): {tf_list}")
    
    # Timeframes avec excellent profit factor
    high_pf = df_valid[df_valid['Profit_Factor'] > 2]
    if len(high_pf) > 0:
        tf_list = ', '.join(high_pf['Timeframe'].tolist())
        console.print(f"✅ **Profit factor excellent** (>2): {tf_list}")
    
    # Timeframes avec faible drawdown
    low_dd = df_valid[df_valid['Max_Drawdown'] < 30]
    if len(low_dd) > 0:
        tf_list = ', '.join(low_dd['Timeframe'].tolist())
        console.print(f"✅ **Drawdown faible** (<30%): {tf_list}")

def display_global_analysis(df):
    """Affiche l'analyse globale"""
    console.print("\n[bold magenta]🌍 ANALYSE GLOBALE[/bold magenta]")
    
    # Filtrer les timeframes avec des trades
    df_valid = df[df['Total_Trades'] > 0]
    
    if len(df_valid) == 0:
        return
    
    total_trades = df_valid['Total_Trades'].sum()
    avg_return = df_valid['Total_Return'].mean()
    avg_winrate = df_valid['Win_Rate'].mean()
    avg_pf = df_valid['Profit_Factor'].mean()
    
    console.print(f"📊 **Statistiques globales**:")
    console.print(f"   • Total trades: {int(total_trades)}")
    console.print(f"   • Retour moyen: {avg_return:.2f}%")
    console.print(f"   • Win rate moyen: {avg_winrate:.2f}%")
    console.print(f"   • Profit factor moyen: {avg_pf:.2f}")
    console.print(f"   • Timeframes testés: {len(df_valid)}")
    
    # Évaluation globale
    console.print(f"\n🎯 **ÉVALUATION GLOBALE**:")
    if avg_winrate > 50 and avg_return > 100:
        console.print("🟢 **STRATÉGIE EXCELLENTE** - Performances solides sur tous les timeframes")
    elif avg_winrate > 45 and avg_return > 50:
        console.print("🟡 **STRATÉGIE BONNE** - Performances acceptables avec quelques ajustements")
    else:
        console.print("🔴 **STRATÉGIE À AMÉLIORER** - Optimisation requise")

def display_file_locations(summary_dir):
    """Affiche les emplacements des fichiers"""
    console.print("\n[bold cyan]📁 FICHIERS GÉNÉRÉS[/bold cyan]")
    console.print(f"📄 Rapport de synthèse: {summary_dir}/rapport_synthese_multitimeframes.md")
    console.print(f"📊 Données CSV: {summary_dir}/resume_tous_timeframes.csv")
    
    # Lister les analyses individuelles
    analysis_dir = "results/analysis"
    if os.path.exists(analysis_dir):
        analysis_dirs = [d for d in os.listdir(analysis_dir) if d.startswith("XAUUSD_") and d.endswith("_analysis_")]
        console.print(f"🔍 Analyses individuelles: {len(analysis_dirs)} dossiers")
        for d in analysis_dirs[:3]:  # Afficher les 3 premiers
            console.print(f"   • {d}")

def main():
    """Fonction principale"""
    console.print("[bold blue]📊 AFFICHAGE DES RÉSULTATS MULTI-TIMEFRAMES XAUUSD[/bold blue]")
    console.print("=" * 70)
    
    # Chargement des résultats
    results = load_results()
    
    if results is None:
        return
    
    df, summary_dir = results
    
    # Affichage des résultats
    display_summary_table(df)
    display_best_timeframes(df)
    display_recommendations(df)
    display_global_analysis(df)
    display_file_locations(summary_dir)
    
    console.print("\n[bold green]✅ Affichage terminé![/bold green]")

if __name__ == "__main__":
    main() 