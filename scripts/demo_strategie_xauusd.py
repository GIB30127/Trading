#!/usr/bin/env python3
"""
Démonstration de la Stratégie XAUUSD D1 Sharpe 1 Simple
Transformée depuis Pine Script vers Python pour backtesting MT5/CSV

Auteur: Assistant IA
Date: 2025-07-24
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from rich import print
from rich.table import Table
from rich.console import Console
import warnings
warnings.filterwarnings('ignore')

# Ajout des chemins pour importer les modules
sys.path.append('src/strategies')
sys.path.append('src/backtesting')

# Import des stratégies
from strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple, calculate_metrics
from strategie_xauusd_sharpe1_mt5_live import XAUUSDSharpe1LiveStrategy

console = Console()

def print_banner():
    """Affiche la bannière de démonstration"""
    console.print("""
[bold blue]
╔══════════════════════════════════════════════════════════════╗
║                    STRATÉGIE XAUUSD D1                       ║
║                   SHARPE 1 SIMPLE                            ║
║                                                              ║
║  Transformée depuis Pine Script vers Python                  ║
║  Compatible MT5 et CSV                                       ║
╚══════════════════════════════════════════════════════════════╝
[/bold blue]
    """)

def show_strategy_parameters():
    """Affiche les paramètres de la stratégie"""
    console.print("\n[bold yellow]📊 PARAMÈTRES DE LA STRATÉGIE[/bold yellow]")
    
    table = Table(title="Configuration")
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur", style="green")
    table.add_column("Description", style="white")
    
    table.add_row("Breakout Period", "2", "Période pour détecter les breakouts")
    table.add_row("Profit ATR", "2.5", "Multiplicateur ATR pour le take profit")
    table.add_row("Trail ATR", "0.5", "Multiplicateur ATR pour le trailing stop")
    table.add_row("RSI Overbought", "85", "Niveau de surachat RSI")
    table.add_row("RSI Oversold", "15", "Niveau de survente RSI")
    table.add_row("EMA Short", "4", "EMA courte")
    table.add_row("EMA Long", "12", "EMA longue")
    table.add_row("ATR Period", "8", "Période pour le calcul ATR")
    
    console.print(table)

def show_strategy_logic():
    """Affiche la logique de la stratégie"""
    console.print("\n[bold yellow]🧠 LOGIQUE DE LA STRATÉGIE[/bold yellow]")
    
    console.print("""
[bold cyan]CONDITIONS D'ENTRÉE LONG:[/bold cyan]
• Breakout au-dessus du plus haut des 2 dernières bougies
• EMA courte > EMA longue (tendance haussière)
• Prix > EMA courte
• RSI < 85 et > 20
• ATR > moyenne ATR * 0.3 (volatilité suffisante)
• Volume > moyenne volume * 0.5
• Momentum haussier (prix > prix précédent)

[bold cyan]CONDITIONS D'ENTRÉE SHORT:[/bold cyan]
• Breakout en-dessous du plus bas des 2 dernières bougies
• EMA courte < EMA longue (tendance baissière)
• Prix < EMA courte
• RSI > 15 et < 80
• ATR > moyenne ATR * 0.3 (volatilité suffisante)
• Volume > moyenne volume * 0.5
• Momentum baissier (prix < prix précédent)

[bold cyan]GESTION DES SORTIES:[/bold cyan]
• Take Profit: Prix d'entrée ± (2.5 × ATR)
• Stop Loss: Trailing stop basé sur 0.5 × ATR
• Sortie sur signal opposé
    """)

def run_backtest_demo():
    """Exécute une démonstration de backtest"""
    console.print("\n[bold yellow]🚀 DÉMONSTRATION BACKTEST[/bold yellow]")
    
    # Vérification des données
    csv_path = "data/raw/XAUUSD_D1_mt5.csv"
    
    if not os.path.exists(csv_path):
        console.print(f"[red]❌ Fichier de données non trouvé: {csv_path}[/red]")
        console.print("Veuillez placer un fichier CSV dans le dossier data/raw/")
        return None
    
    try:
        # Chargement des données
        console.print(f"[green]📁 Chargement des données depuis: {csv_path}[/green]")
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        
        console.print(f"[green]✅ {len(df)} bougies chargées[/green]")
        console.print(f"[green]📅 Période: {df['Date'].min()} à {df['Date'].max()}[/green]")
        
        # Application de la stratégie
        console.print("\n[bold]⚙️ Application de la stratégie...[/bold]")
        trades, df_with_signals = strategie_xauusd_sharpe1_simple(df, 'XAUUSD', 'D1')
        
        # Calcul des métriques
        metrics = calculate_metrics(trades)
        
        # Affichage des résultats
        console.print("\n[bold green]📈 RÉSULTATS DU BACKTEST[/bold green]")
        
        results_table = Table(title="Performance de la Stratégie")
        results_table.add_column("Métrique", style="cyan")
        results_table.add_column("Valeur", style="green")
        
        results_table.add_row("Total Trades", str(metrics['total_trades']))
        results_table.add_row("Trades Gagnants", str(metrics['winning_trades']))
        results_table.add_row("Trades Perdants", str(metrics['losing_trades']))
        results_table.add_row("Taux de Réussite", f"{metrics['win_rate']:.2f}%")
        results_table.add_row("Retour Total", f"{metrics['total_return']:.2f}%")
        results_table.add_row("Gain Moyen", f"{metrics['avg_win']:.2f}%")
        results_table.add_row("Perte Moyenne", f"{metrics['avg_loss']:.2f}%")
        results_table.add_row("Profit Factor", f"{metrics['profit_factor']:.2f}")
        results_table.add_row("Drawdown Max", f"{metrics['max_drawdown']:.2f}%")
        results_table.add_row("Ratio de Sharpe", f"{metrics['sharpe_ratio']:.2f}")
        
        console.print(results_table)
        
        # Affichage des derniers trades
        if trades:
            console.print("\n[bold]📋 DERNIERS 5 TRADES[/bold]")
            trades_table = Table(title="Historique des Trades")
            trades_table.add_column("N°", style="cyan")
            trades_table.add_column("Position", style="yellow")
            trades_table.add_column("Entrée", style="green")
            trades_table.add_column("Sortie", style="red")
            trades_table.add_column("P&L", style="magenta")
            trades_table.add_column("Raison", style="blue")
            
            for i, trade in enumerate(trades[-5:], 1):
                status = "✅" if trade.get('pnl', 0) > 0 else "❌" if trade.get('pnl', 0) < 0 else "⏳"
                pnl_str = f"{trade.get('pnl', 0):.2f}%" if 'pnl' in trade else "En cours"
                exit_price = f"{trade.get('exit_price', 0):.2f}" if 'exit_price' in trade else "En cours"
                
                trades_table.add_row(
                    str(i),
                    f"{status} {trade['position']}",
                    f"{trade['entry_price']:.2f}",
                    exit_price,
                    pnl_str,
                    trade.get('exit_reason', 'En cours')
                )
            
            console.print(trades_table)
        
        return {
            'trades': trades,
            'metrics': metrics,
            'data': df_with_signals
        }
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors du backtest: {e}[/red]")
        return None

def show_live_strategy_demo():
    """Démonstration de la stratégie en temps réel"""
    console.print("\n[bold yellow]🔄 DÉMONSTRATION STRATÉGIE TEMPS RÉEL[/bold yellow]")
    
    # Initialisation de la stratégie
    strategy = XAUUSDSharpe1LiveStrategy("XAUUSD", "D1")
    
    # Chargement des données
    csv_path = "data/raw/XAUUSD_D1_mt5.csv"
    
    if not os.path.exists(csv_path):
        console.print(f"[red]❌ Fichier de données non trouvé[/red]")
        return
    
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    console.print(f"[green]✅ Simulation temps réel avec {len(df)} bougies[/green]")
    
    # Simulation du trading en temps réel
    console.print("\n[bold]🎯 SIMULATION TRADING TEMPS RÉEL[/bold]")
    
    for i in range(20, min(50, len(df))):  # Simule les 30 premières bougies
        result = strategy.process_new_data(df, i)
        
        if result:
            console.print(f"[yellow]📊 Trade exécuté: {result}[/yellow]")
    
    # Statut final
    status = strategy.get_current_status()
    console.print(f"\n[bold]📊 STATUT FINAL[/bold]")
    console.print(f"Position actuelle: {status['position']}")
    console.print(f"Prix d'entrée: {status['entry_price']:.2f}")
    console.print(f"Stop Loss: {status['stop_loss']:.2f}")
    console.print(f"Profit Target: {status['profit_target']:.2f}")
    console.print(f"Total trades: {status['total_trades']}")

def show_usage_examples():
    """Affiche des exemples d'utilisation"""
    console.print("\n[bold yellow]💡 EXEMPLES D'UTILISATION[/bold yellow]")
    
    console.print("""
[bold cyan]1. Backtest simple avec CSV:[/bold cyan]
```python
from src.strategies.strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple

# Chargement des données
df = pd.read_csv("data/raw/XAUUSD_D1_mt5.csv")
df['Date'] = pd.to_datetime(df['Date'])

# Application de la stratégie
trades, df_signals = strategie_xauusd_sharpe1_simple(df, 'XAUUSD', 'D1')
```

[bold cyan]2. Trading en temps réel avec MT5:[/bold cyan]
```python
from src.strategies.strategie_xauusd_sharpe1_mt5_live import XAUUSDSharpe1LiveStrategy

# Initialisation
strategy = XAUUSDSharpe1LiveStrategy("XAUUSD", "D1")

# Pour chaque nouvelle bougie
result = strategy.process_new_data(df, current_index)
if result:
    print(f"Nouveau trade: {result}")
```

[bold cyan]3. Test multi-timeframes:[/bold cyan]
```python
python src/backtesting/backtest_all_xauusd_sharpe1.py
```

[bold cyan]4. Connexion MT5 directe:[/bold cyan]
```python
import MetaTrader5 as mt5

# Initialisation
mt5.initialize()

# Récupération des données
rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_D1, 0, 1000)
df = pd.DataFrame(rates)
```
    """)

def main():
    """Fonction principale de démonstration"""
    print_banner()
    
    # Affichage des paramètres
    show_strategy_parameters()
    
    # Affichage de la logique
    show_strategy_logic()
    
    # Démonstration backtest
    results = run_backtest_demo()
    
    # Démonstration temps réel
    show_live_strategy_demo()
    
    # Exemples d'utilisation
    show_usage_examples()
    
    console.print("\n[bold green]✅ Démonstration terminée![/bold green]")
    console.print("\n[bold]📚 Pour plus d'informations, consultez les fichiers:[/bold]")
    console.print("• src/strategies/strategie_xauusd_sharpe1_simple.py")
    console.print("• src/strategies/strategie_xauusd_sharpe1_mt5_live.py")
    console.print("• src/backtesting/backtest_xauusd_sharpe1_simple.py")

if __name__ == "__main__":
    main() 