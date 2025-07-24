import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from rich import print
import warnings
warnings.filterwarnings('ignore')

def compute_atr(df, window):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategie_finale_simple(df, symbol, timeframe):
    """Stratégie simple et efficace basée sur les fondamentaux"""
    
    df = df.copy()
    
    # Paramètres SIMPLES et EFFICACES
    if symbol == 'XAUUSD':
        breakout_period = 10
        risk_atr = 2.0
        profit_atr = 4.0
        rsi_overbought = 75
        rsi_oversold = 25
    elif symbol == 'US30.cash':
        breakout_period = 8
        risk_atr = 1.8
        profit_atr = 3.5
        rsi_overbought = 70
        rsi_oversold = 30
    elif symbol == 'EURUSD':
        breakout_period = 8
        risk_atr = 1.5
        profit_atr = 3.0
        rsi_overbought = 70
        rsi_oversold = 30
    else:  # GER40.cash
        breakout_period = 8
        risk_atr = 1.6
        profit_atr = 3.2
        rsi_overbought = 70
        rsi_oversold = 30
    
    # Ajustement timeframe simple
    if timeframe == 'D1':
        breakout_period = int(breakout_period * 1.5)
        risk_atr *= 1.2
        profit_atr *= 1.2
    elif timeframe == 'H1':
        breakout_period = int(breakout_period * 0.8)
        risk_atr *= 0.8
        profit_atr *= 0.8
    
    # Indicateurs SIMPLES
    df['ATR'] = compute_atr(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    # Breakouts SIMPLES
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # Volume simple
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.5  # Plus permissif
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trades = []

    for i in range(1, len(df)):
        # Conditions SIMPLES
        ema_trend = df.loc[i, 'Close'] > df.loc[i, 'EMA50']
        volume_ok = df.loc[i, 'Volume_OK']
        
        # Breakouts purs
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        
        # RSI simple
        rsi_ok_long = df.loc[i, 'RSI'] < rsi_overbought
        rsi_ok_short = df.loc[i, 'RSI'] > rsi_oversold

        if position == 0:
            # Entrée Long - CONDITIONS SIMPLES
            if (breakout_up and ema_trend and volume_ok and rsi_ok_long):
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                
            # Entrée Short - CONDITIONS SIMPLES
            elif (breakout_down and not ema_trend and volume_ok and rsi_ok_short):
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']

        elif position == 1:  # Position Long
            # Sorties SIMPLES
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (profit_target - entry_price) / entry_price,
                    'Reason': 'Take Profit'
                })
                position = 0

        elif position == -1:  # Position Short
            # Sorties SIMPLES
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (entry_price - profit_target) / entry_price,
                    'Reason': 'Take Profit'
                })
                position = 0

    return trades

def calculate_simple_metrics(trades):
    """Calcule les métriques simples et claires"""
    if not trades:
        return {
            'Total_PnL': 0,
            'Performance': 0,
            'Sharpe_Ratio': 0,
            'Win_Rate': 0,
            'Total_Trades': 0,
            'Winning_Trades': 0,
            'Losing_Trades': 0,
            'Avg_Win': 0,
            'Avg_Loss': 0,
            'Risk_Reward': 0,
            'Max_Drawdown': 0
        }
    
    df_trades = pd.DataFrame(trades)
    total_pnl = df_trades['PnL'].sum()
    returns = df_trades['PnL']
    
    # Métriques de base
    total_trades = len(trades)
    winning_trades = len(df_trades[df_trades['PnL'] > 0])
    losing_trades = len(df_trades[df_trades['PnL'] < 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    # Performance annualisée
    performance = (1 + total_pnl) ** (252 / total_trades) - 1 if total_trades > 0 else 0
    
    # Sharpe Ratio
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    # Ratio risque/récompense
    avg_win = df_trades[df_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = abs(df_trades[df_trades['PnL'] < 0]['PnL'].mean()) if losing_trades > 0 else 0
    risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
    
    # Drawdown maximum
    cumulative = df_trades['PnL'].cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
    
    return {
        'Total_PnL': total_pnl,
        'Performance': performance,
        'Sharpe_Ratio': sharpe,
        'Win_Rate': win_rate,
        'Total_Trades': total_trades,
        'Winning_Trades': winning_trades,
        'Losing_Trades': losing_trades,
        'Avg_Win': avg_win,
        'Avg_Loss': avg_loss,
        'Risk_Reward': risk_reward,
        'Max_Drawdown': max_drawdown
    }

def main():
    print("🎯 Stratégie Finale - Simple et Efficace")
    print("=" * 50)
    print("💡 Retour aux fondamentaux qui marchent")
    print("=" * 50)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_results = []
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📊 Test de {symbol} {timeframe}...")
                
                # Chargement et backtest
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = strategie_finale_simple(df, symbol, timeframe)
                
                # Calcul des métriques
                metrics = calculate_simple_metrics(trades)
                
                all_results.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'trades': trades,
                    'metrics': metrics
                })
                
                print(f"  ✅ {len(trades)} trades, {metrics['Performance']:.2%} performance, {metrics['Win_Rate']:.1f}% win rate")
    
    # Affichage des résultats
    print(f"\n🏆 Résultats de la Stratégie Finale :")
    print("=" * 50)
    
    # Tri par performance
    best_results = sorted(all_results, key=lambda x: x['metrics']['Performance'], reverse=True)
    
    print(f"\n🥇 Top 5 par Performance :")
    for i, result in enumerate(best_results[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Performance']:.2%} perf, {metrics['Win_Rate']:.1f}% win rate, {metrics['Total_Trades']} trades")
    
    # Tri par nombre de trades
    most_trades = sorted(all_results, key=lambda x: x['metrics']['Total_Trades'], reverse=True)
    
    print(f"\n📊 Top 5 par Nombre de Trades :")
    for i, result in enumerate(most_trades[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Total_Trades']} trades, {metrics['Performance']:.2%} perf")
    
    # Tri par win rate
    best_winrate = sorted(all_results, key=lambda x: x['metrics']['Win_Rate'], reverse=True)
    
    print(f"\n🎯 Top 5 par Win Rate :")
    for i, result in enumerate(best_winrate[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Win_Rate']:.1f}% win rate, {metrics['Performance']:.2%} perf")
    
    # Statistiques globales
    positive_results = [r for r in all_results if r['metrics']['Performance'] > 0]
    total_trades_all = sum([r['metrics']['Total_Trades'] for r in all_results])
    avg_performance = np.mean([r['metrics']['Performance'] for r in all_results])
    avg_winrate = np.mean([r['metrics']['Win_Rate'] for r in all_results])
    
    print(f"\n📊 Statistiques Globales :")
    print(f"   - Stratégies rentables: {len(positive_results)}/{len(all_results)} ({len(positive_results)/len(all_results)*100:.1f}%)")
    print(f"   - Total trades: {total_trades_all}")
    print(f"   - Performance moyenne: {avg_performance:.2%}")
    print(f"   - Win rate moyen: {avg_winrate:.1f}%")
    
    # Comparaison avec la stratégie de départ
    print(f"\n🔄 Comparaison avec la stratégie de départ :")
    print(f"   - Notre stratégie simple génère {total_trades_all} trades")
    print(f"   - Performance moyenne: {avg_performance:.2%}")
    print(f"   - {len(positive_results)} stratégies rentables sur {len(all_results)}")
    
    # Sauvegarde des résultats
    os.makedirs("final_results", exist_ok=True)
    
    report = "## 🎯 Stratégie Finale - Simple et Efficace\n\n"
    report += "### 💡 Philosophie\n"
    report += "- Retour aux fondamentaux\n"
    report += "- Conditions simples et claires\n"
    report += "- Pas de sur-optimisation\n\n"
    report += "### 📊 Résultats par Instrument\n\n"
    
    for result in best_results:
        metrics = result['metrics']
        report += f"#### {result['symbol']} {result['timeframe']}\n"
        report += f"- **Performance :** {metrics['Performance']:.2%}\n"
        report += f"- **Trades :** {metrics['Total_Trades']}\n"
        report += f"- **Win Rate :** {metrics['Win_Rate']:.1f}%\n"
        report += f"- **Sharpe Ratio :** {metrics['Sharpe_Ratio']:.2f}\n"
        report += f"- **Max Drawdown :** {metrics['Max_Drawdown']:.1f}%\n"
        report += f"- **Risk/Reward :** {metrics['Risk_Reward']:.2f}\n\n"
    
    with open("final_results/final_strategy_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport sauvegardé : final_results/final_strategy_report.md")
    
    # Recommandations
    if total_trades_all > 0:
        print(f"\n💡 Recommandations :")
        print(f"   - La stratégie simple génère des trades !")
        print(f"   - Focus sur les instruments avec le plus de trades")
        print(f"   - Ajuster les paramètres selon les résultats")
    else:
        print(f"\n⚠️ Problème détecté : Aucun trade généré")
        print(f"   - Vérifier les conditions d'entrée")
        print(f"   - Assouplir les filtres")

if __name__ == "__main__":
    main() 