import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour importer les stratégies
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))
from strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple, calculate_metrics

def test_all_timeframes(symbol="XAUUSD"):
    """Teste la stratégie sur tous les timeframes disponibles"""
    print(f"[bold blue]=== Test Multi-Timeframes {symbol} Sharpe 1 Simple ===[/bold blue]")
    
    # Timeframes disponibles
    timeframes = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1']
    
    results_summary = []
    
    for timeframe in timeframes:
        print(f"\n[bold yellow]--- Test {symbol} {timeframe} ---[/bold yellow]")
        
        # Chemin du fichier CSV
        csv_path = f"data/raw/{symbol}_{timeframe}_mt5.csv"
        
        if not os.path.exists(csv_path):
            print(f"[red]Fichier non trouvé: {csv_path}[/red]")
            continue
        
        try:
            # Chargement des données
            df = pd.read_csv(csv_path)
            df['Date'] = pd.to_datetime(df['Date'])
            
            print(f"[green]Données chargées: {len(df)} bougies[/green]")
            print(f"Période: {df['Date'].min()} à {df['Date'].max()}")
            
            # Application de la stratégie
            trades, df_with_signals = strategie_xauusd_sharpe1_simple(df, symbol, timeframe)
            
            # Calcul des métriques
            metrics = calculate_metrics(trades)
            
            # Affichage des résultats
            print(f"📊 Total trades: {metrics['total_trades']}")
            print(f"✅ Taux de réussite: {metrics['win_rate']:.2f}%")
            print(f"💰 Retour total: {metrics['total_return']:.2f}%")
            print(f"⚖️ Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"📊 Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}")
            
            # Ajout au résumé
            results_summary.append({
                'Symbol': symbol,
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
            
        except Exception as e:
            print(f"[red]Erreur pour {timeframe}: {e}[/red]")
            continue
    
    # Création du résumé
    if results_summary:
        summary_df = pd.DataFrame(results_summary)
        
        # Sauvegarde du résumé
        os.makedirs('results/backtests', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"results/backtests/{symbol}_multi_timeframe_summary_{timestamp}.csv"
        summary_df.to_csv(summary_file, index=False)
        
        # Affichage du tableau récapitulatif
        print(f"\n[bold green]=== RÉSUMÉ MULTI-TIMEFRAMES ===[/bold green]")
        print(summary_df.to_string(index=False, float_format='%.2f'))
        
        # Sauvegarde du rapport
        report_file = f"results/backtests/{symbol}_multi_timeframe_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Rapport Multi-Timeframes {symbol} - Stratégie Sharpe 1 Simple\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Résumé des Performances\n\n")
            f.write(summary_df.to_markdown(index=False, float_format='%.2f'))
            f.write("\n\n")
            
            # Meilleur timeframe par métrique
            f.write("## Meilleurs Timeframes par Métrique\n\n")
            
            if len(summary_df) > 0:
                best_return = summary_df.loc[summary_df['Total_Return'].idxmax()]
                best_sharpe = summary_df.loc[summary_df['Sharpe_Ratio'].idxmax()]
                best_winrate = summary_df.loc[summary_df['Win_Rate'].idxmax()]
                best_profit_factor = summary_df.loc[summary_df['Profit_Factor'].idxmax()]
                
                f.write(f"- **Meilleur retour**: {best_return['Timeframe']} ({best_return['Total_Return']:.2f}%)\n")
                f.write(f"- **Meilleur Sharpe**: {best_sharpe['Timeframe']} ({best_sharpe['Sharpe_Ratio']:.2f})\n")
                f.write(f"- **Meilleur win rate**: {best_winrate['Timeframe']} ({best_winrate['Win_Rate']:.2f}%)\n")
                f.write(f"- **Meilleur profit factor**: {best_profit_factor['Timeframe']} ({best_profit_factor['Profit_Factor']:.2f})\n")
        
        print(f"\n[green]Résumé sauvegardé: {summary_file}[/green]")
        print(f"[green]Rapport sauvegardé: {report_file}[/green]")
    
    return results_summary

def test_all_symbols(timeframe="D1"):
    """Teste la stratégie sur tous les symboles disponibles"""
    print(f"[bold blue]=== Test Multi-Symboles {timeframe} Sharpe 1 Simple ===[/bold blue]")
    
    # Symboles disponibles
    symbols = ['XAUUSD', 'EURUSD', 'US30.cash', 'GER40.cash', 'US500.cash']
    
    results_summary = []
    
    for symbol in symbols:
        print(f"\n[bold yellow]--- Test {symbol} {timeframe} ---[/bold yellow]")
        
        # Chemin du fichier CSV
        csv_path = f"data/raw/{symbol}_{timeframe}_mt5.csv"
        
        if not os.path.exists(csv_path):
            print(f"[red]Fichier non trouvé: {csv_path}[/red]")
            continue
        
        try:
            # Chargement des données
            df = pd.read_csv(csv_path)
            df['Date'] = pd.to_datetime(df['Date'])
            
            print(f"[green]Données chargées: {len(df)} bougies[/green]")
            print(f"Période: {df['Date'].min()} à {df['Date'].max()}")
            
            # Application de la stratégie
            trades, df_with_signals = strategie_xauusd_sharpe1_simple(df, symbol, timeframe)
            
            # Calcul des métriques
            metrics = calculate_metrics(trades)
            
            # Affichage des résultats
            print(f"📊 Total trades: {metrics['total_trades']}")
            print(f"✅ Taux de réussite: {metrics['win_rate']:.2f}%")
            print(f"💰 Retour total: {metrics['total_return']:.2f}%")
            print(f"⚖️ Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"📊 Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}")
            
            # Ajout au résumé
            results_summary.append({
                'Symbol': symbol,
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
            
        except Exception as e:
            print(f"[red]Erreur pour {symbol}: {e}[/red]")
            continue
    
    # Création du résumé
    if results_summary:
        summary_df = pd.DataFrame(results_summary)
        
        # Sauvegarde du résumé
        os.makedirs('results/backtests', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"results/backtests/multi_symbols_{timeframe}_summary_{timestamp}.csv"
        summary_df.to_csv(summary_file, index=False)
        
        # Affichage du tableau récapitulatif
        print(f"\n[bold green]=== RÉSUMÉ MULTI-SYMBOLES ===[/bold green]")
        print(summary_df.to_string(index=False, float_format='%.2f'))
        
        print(f"\n[green]Résumé sauvegardé: {summary_file}[/green]")
    
    return results_summary

def main():
    """Fonction principale"""
    print("[bold blue]🚀 Test Multi-Timeframes et Multi-Symboles[/bold blue]")
    
    # Test multi-timeframes pour XAUUSD
    print("\n" + "="*60)
    test_all_timeframes("XAUUSD")
    
    # Test multi-symboles sur D1
    print("\n" + "="*60)
    test_all_symbols("D1")
    
    print("\n[bold green]✅ Tests terminés![/bold green]")

if __name__ == "__main__":
    main() 