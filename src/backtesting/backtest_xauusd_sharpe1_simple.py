import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour importer les stratégies
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))
from strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple, calculate_metrics

def load_data_from_csv(symbol, timeframe):
    """Charge les données depuis un fichier CSV"""
    csv_path = f"data/raw/{symbol}_{timeframe}_mt5.csv"
    
    if not os.path.exists(csv_path):
        print(f"[red]Fichier non trouvé: {csv_path}[/red]")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Vérification des colonnes requises
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"[red]Colonnes manquantes: {missing_columns}[/red]")
            return None
        
        print(f"[green]Données chargées: {len(df)} bougies pour {symbol} {timeframe}[/green]")
        print(f"Période: {df['Date'].min()} à {df['Date'].max()}")
        
        return df
    
    except Exception as e:
        print(f"[red]Erreur lors du chargement: {e}[/red]")
        return None

def load_data_from_mt5(symbol, timeframe, start_date=None, end_date=None):
    """Charge les données depuis MT5 (nécessite MetaTrader5)"""
    try:
        import MetaTrader5 as mt5
        
        # Initialisation de MT5
        if not mt5.initialize():
            print("[red]Échec de l'initialisation de MT5[/red]")
            return None
        
        # Conversion des timeframes
        timeframe_map = {
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        if timeframe not in timeframe_map:
            print(f"[red]Timeframe non supporté: {timeframe}[/red]")
            return None
        
        # Dates par défaut
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        # Récupération des données
        rates = mt5.copy_rates_range(symbol, timeframe_map[timeframe], start_date, end_date)
        
        if rates is None or len(rates) == 0:
            print(f"[red]Aucune donnée trouvée pour {symbol} {timeframe}[/red]")
            return None
        
        # Conversion en DataFrame
        df = pd.DataFrame(rates)
        df['Date'] = pd.to_datetime(df['time'], unit='s')
        df = df.drop('time', axis=1)
        
        # Renommage des colonnes
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Spread', 'Real_Volume', 'Date']
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        print(f"[green]Données MT5 chargées: {len(df)} bougies pour {symbol} {timeframe}[/green]")
        print(f"Période: {df['Date'].min()} à {df['Date'].max()}")
        
        return df
    
    except ImportError:
        print("[red]MetaTrader5 non installé. Utilisez les données CSV.[/red]")
        return None
    except Exception as e:
        print(f"[red]Erreur MT5: {e}[/red]")
        return None

def run_backtest(symbol, timeframe, data_source='csv', start_date=None, end_date=None):
    """Exécute le backtest de la stratégie"""
    print(f"[bold blue]=== Backtest XAUUSD Sharpe 1 Simple ===[/bold blue]")
    print(f"Symbole: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Source de données: {data_source.upper()}")
    
    # Chargement des données
    if data_source.lower() == 'mt5':
        df = load_data_from_mt5(symbol, timeframe, start_date, end_date)
    else:
        df = load_data_from_csv(symbol, timeframe)
    
    if df is None:
        print("[red]Impossible de charger les données[/red]")
        return None
    
    # Application de la stratégie
    print("\n[bold]Application de la stratégie...[/bold]")
    trades, df_with_signals = strategie_xauusd_sharpe1_simple(df, symbol, timeframe)
    
    # Calcul des métriques
    metrics = calculate_metrics(trades)
    
    # Affichage des résultats
    print(f"\n[bold green]=== RÉSULTATS DU BACKTEST ===[/bold green]")
    print(f"📊 Total trades: {metrics['total_trades']}")
    print(f"✅ Trades gagnants: {metrics['winning_trades']}")
    print(f"❌ Trades perdants: {metrics['losing_trades']}")
    print(f"🎯 Taux de réussite: {metrics['win_rate']:.2f}%")
    print(f"💰 Retour total: {metrics['total_return']:.2f}%")
    print(f"📈 Gain moyen: {metrics['avg_win']:.2f}%")
    print(f"📉 Perte moyenne: {metrics['avg_loss']:.2f}%")
    print(f"⚖️ Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"📊 Drawdown max: {metrics['max_drawdown']:.2f}%")
    print(f"📊 Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}")
    
    # Affichage des derniers trades
    if trades:
        print(f"\n[bold]📋 Derniers 5 trades:[/bold]")
        for i, trade in enumerate(trades[-5:], 1):
            status = "✅" if trade.get('pnl', 0) > 0 else "❌" if trade.get('pnl', 0) < 0 else "⏳"
            pnl_str = f"{trade.get('pnl', 0):.2f}%" if 'pnl' in trade else "En cours"
            print(f"Trade {i}: {status} {trade['position']} - Entrée: {trade['entry_price']:.2f} - Sortie: {trade.get('exit_price', 'En cours'):.2f} - P&L: {pnl_str}")
    
    return {
        'trades': trades,
        'metrics': metrics,
        'data': df_with_signals
    }

def save_results(results, symbol, timeframe):
    """Sauvegarde les résultats du backtest"""
    if results is None:
        return
    
    # Création du dossier results s'il n'existe pas
    os.makedirs('results/backtests', exist_ok=True)
    
    # Sauvegarde des trades
    if results['trades']:
        trades_df = pd.DataFrame(results['trades'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trades_file = f"results/backtests/{symbol}_{timeframe}_trades_{timestamp}.csv"
        trades_df.to_csv(trades_file, index=False)
        print(f"\n[green]Trades sauvegardés: {trades_file}[/green]")
    
    # Sauvegarde du rapport
    report_file = f"results/backtests/{symbol}_{timeframe}_backtest_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Backtest {symbol} {timeframe} - Stratégie XAUUSD Sharpe 1 Simple\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Métriques de Performance\n\n")
        metrics = results['metrics']
        f.write(f"- **Total trades**: {metrics['total_trades']}\n")
        f.write(f"- **Trades gagnants**: {metrics['winning_trades']}\n")
        f.write(f"- **Trades perdants**: {metrics['losing_trades']}\n")
        f.write(f"- **Taux de réussite**: {metrics['win_rate']:.2f}%\n")
        f.write(f"- **Retour total**: {metrics['total_return']:.2f}%\n")
        f.write(f"- **Gain moyen**: {metrics['avg_win']:.2f}%\n")
        f.write(f"- **Perte moyenne**: {metrics['avg_loss']:.2f}%\n")
        f.write(f"- **Profit Factor**: {metrics['profit_factor']:.2f}\n")
        f.write(f"- **Drawdown max**: {metrics['max_drawdown']:.2f}%\n")
        f.write(f"- **Ratio de Sharpe**: {metrics['sharpe_ratio']:.2f}\n\n")
        
        if results['trades']:
            f.write("## Derniers Trades\n\n")
            for i, trade in enumerate(results['trades'][-10:], 1):
                f.write(f"### Trade {i}\n")
                f.write(f"- **Position**: {trade['position']}\n")
                f.write(f"- **Date d'entrée**: {trade['entry_date']}\n")
                f.write(f"- **Prix d'entrée**: {trade['entry_price']:.2f}\n")
                if 'exit_date' in trade:
                    f.write(f"- **Date de sortie**: {trade['exit_date']}\n")
                    f.write(f"- **Prix de sortie**: {trade['exit_price']:.2f}\n")
                    f.write(f"- **P&L**: {trade['pnl']:.2f}%\n")
                    f.write(f"- **Raison de sortie**: {trade['exit_reason']}\n")
                f.write("\n")
    
    print(f"[green]Rapport sauvegardé: {report_file}[/green]")

def main():
    """Fonction principale"""
    print("[bold blue]🤖 Backtesting XAUUSD Sharpe 1 Simple[/bold blue]")
    
    # Configuration
    symbol = "XAUUSD"
    timeframe = "D1"
    data_source = "csv"  # ou "mt5"
    
    # Exécution du backtest
    results = run_backtest(symbol, timeframe, data_source)
    
    # Sauvegarde des résultats
    if results:
        save_results(results, symbol, timeframe)
    
    print("\n[bold green]✅ Backtest terminé![/bold green]")

if __name__ == "__main__":
    main() 