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

def compute_adx(df, window):
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff().abs()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    trur = compute_atr(df, window)
    plus_di = 100 * (plus_dm.rolling(window=window).sum() / trur)
    minus_di = 100 * (minus_dm.rolling(window=window).sum() / trur)
    dx = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=window).mean()
    return adx

def compute_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategie_avancee(df, symbol, timeframe):
    """Stratégie avancée avec tous les indicateurs et gestion du risque optimisée"""
    
    df = df.copy()
    
    # Paramètres adaptés par instrument
    if symbol == 'XAUUSD':
        breakout_period = 15
        risk_atr = 2.0  # Stop plus serré
        profit_atr = 4.0  # Objectif plus réaliste
        adx_threshold = 25
        rsi_overbought = 70
        rsi_oversold = 30
        max_drawdown_limit = 0.15  # 15% max drawdown
    elif symbol == 'US30.cash':
        breakout_period = 12
        risk_atr = 1.8
        profit_atr = 3.5
        adx_threshold = 22
        rsi_overbought = 75
        rsi_oversold = 25
        max_drawdown_limit = 0.12
    elif symbol == 'EURUSD':
        breakout_period = 10
        risk_atr = 1.5
        profit_atr = 3.0
        adx_threshold = 20
        rsi_overbought = 70
        rsi_oversold = 30
        max_drawdown_limit = 0.10
    else:  # GER40.cash
        breakout_period = 10
        risk_atr = 1.6
        profit_atr = 3.2
        adx_threshold = 20
        rsi_overbought = 70
        rsi_oversold = 30
        max_drawdown_limit = 0.12
    
    # Ajustement timeframe
    if timeframe == 'D1':
        breakout_period = int(breakout_period * 1.2)
        risk_atr *= 1.1
        profit_atr *= 1.1
    elif timeframe == 'H1':
        breakout_period = int(breakout_period * 0.9)
        risk_atr *= 0.9
        profit_atr *= 0.9
    
    # Calcul de tous les indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['ADX'] = compute_adx(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    
    # Breakouts
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # Volume
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.8
    
    # Conditions avancées
    df['EMA_Trend'] = df['Close'] > df['EMA50']
    df['EMA200_Trend'] = df['Close'] > df['EMA200']
    df['ADX_Strong'] = df['ADX'] > adx_threshold
    df['RSI_Not_Overbought'] = df['RSI'] < rsi_overbought
    df['RSI_Not_Oversold'] = df['RSI'] > rsi_oversold
    
    # Breakouts
    df['Breakout_Up'] = (df['High'].shift(1) < df['High_Break'].shift(1)) & (df['High'] >= df['High_Break'])
    df['Breakout_Down'] = (df['Low'].shift(1) > df['Low_Break'].shift(1)) & (df['Low'] <= df['Low_Break'])
    
    # Conditions d'entrée renforcées
    df['Long_Signal'] = (
        df['Breakout_Up'] & 
        df['EMA_Trend'] & 
        df['EMA200_Trend'] &  # Tendance principale
        df['ADX_Strong'] &    # Tendance forte
        df['RSI_Not_Overbought'] &  # Pas de surachat
        df['Volume_OK']
    )
    
    df['Short_Signal'] = (
        df['Breakout_Down'] & 
        ~df['EMA_Trend'] & 
        ~df['EMA200_Trend'] &  # Tendance baissière
        df['ADX_Strong'] &     # Tendance forte
        df['RSI_Not_Oversold'] &  # Pas de survente
        df['Volume_OK']
    )
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trailing_stop = 0
    trades = []
    cumulative_pnl = 0
    max_cumulative = 0

    for i in range(1, len(df)):
        # Gestion du drawdown maximum
        current_drawdown = (max_cumulative - cumulative_pnl) / max_cumulative if max_cumulative > 0 else 0
        if current_drawdown > max_drawdown_limit:
            continue  # Skip trades si drawdown trop élevé
        
        if position == 0:
            # Entrée Long avec conditions renforcées
            if df.loc[i, 'Long_Signal']:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                trailing_stop = entry_price - (risk_atr * 0.8) * df.loc[i, 'ATR']  # Trailing plus serré
                
            # Entrée Short avec conditions renforcées
            elif df.loc[i, 'Short_Signal']:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']
                trailing_stop = entry_price + (risk_atr * 0.8) * df.loc[i, 'ATR']

        elif position == 1:  # Position Long
            # Mise à jour du trailing stop
            new_trailing_stop = df.loc[i, 'Close'] - (risk_atr * 0.8) * df.loc[i, 'ATR']
            if new_trailing_stop > trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sorties avec trailing stop
            if df.loc[i, 'Low'] <= stop_loss:
                pnl = (stop_loss - entry_price) / entry_price
                cumulative_pnl += pnl
                max_cumulative = max(max_cumulative, cumulative_pnl)
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': pnl,
                    'Reason': 'Stop Loss',
                    'Drawdown': current_drawdown
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                pnl = (profit_target - entry_price) / entry_price
                cumulative_pnl += pnl
                max_cumulative = max(max_cumulative, cumulative_pnl)
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit',
                    'Drawdown': current_drawdown
                })
                position = 0
            elif df.loc[i, 'Low'] <= trailing_stop:
                pnl = (trailing_stop - entry_price) / entry_price
                cumulative_pnl += pnl
                max_cumulative = max(max_cumulative, cumulative_pnl)
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': pnl,
                    'Reason': 'Trailing Stop',
                    'Drawdown': current_drawdown
                })
                position = 0

        elif position == -1:  # Position Short
            # Mise à jour du trailing stop
            new_trailing_stop = df.loc[i, 'Close'] + (risk_atr * 0.8) * df.loc[i, 'ATR']
            if new_trailing_stop < trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sorties avec trailing stop
            if df.loc[i, 'High'] >= stop_loss:
                pnl = (entry_price - stop_loss) / entry_price
                cumulative_pnl += pnl
                max_cumulative = max(max_cumulative, cumulative_pnl)
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': pnl,
                    'Reason': 'Stop Loss',
                    'Drawdown': current_drawdown
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                pnl = (entry_price - profit_target) / entry_price
                cumulative_pnl += pnl
                max_cumulative = max(max_cumulative, cumulative_pnl)
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit',
                    'Drawdown': current_drawdown
                })
                position = 0
            elif df.loc[i, 'High'] >= trailing_stop:
                pnl = (entry_price - trailing_stop) / entry_price
                cumulative_pnl += pnl
                max_cumulative = max(max_cumulative, cumulative_pnl)
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': pnl,
                    'Reason': 'Trailing Stop',
                    'Drawdown': current_drawdown
                })
                position = 0

    return trades

def calculate_advanced_metrics(trades):
    """Calcule toutes les métriques avancées"""
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
            'Max_Drawdown': 0,
            'Avg_Drawdown': 0,
            'Profit_Factor': 0,
            'Calmar_Ratio': 0
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
    
    # Drawdown
    cumulative = df_trades['PnL'].cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
    avg_drawdown = abs(df_trades['Drawdown'].mean()) * 100 if 'Drawdown' in df_trades.columns else 0
    
    # Profit Factor
    gross_profit = df_trades[df_trades['PnL'] > 0]['PnL'].sum() if winning_trades > 0 else 0
    gross_loss = abs(df_trades[df_trades['PnL'] < 0]['PnL'].sum()) if losing_trades > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Calmar Ratio (Performance / Max Drawdown)
    calmar_ratio = performance / (max_drawdown / 100) if max_drawdown > 0 else 0
    
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
        'Max_Drawdown': max_drawdown,
        'Avg_Drawdown': avg_drawdown,
        'Profit_Factor': profit_factor,
        'Calmar_Ratio': calmar_ratio
    }

def main():
    print("🚀 Stratégie Avancée avec Gestion du Risque")
    print("=" * 50)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_results = []
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📊 Analyse avancée de {symbol} {timeframe}...")
                
                # Chargement et backtest
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = strategie_avancee(df, symbol, timeframe)
                
                # Calcul des métriques avancées
                metrics = calculate_advanced_metrics(trades)
                
                all_results.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'trades': trades,
                    'metrics': metrics
                })
                
                print(f"  ✅ {len(trades)} trades, {metrics['Performance']:.2%} performance, {metrics['Max_Drawdown']:.1f}% max DD")
    
    # Affichage des résultats
    print(f"\n🏆 Résultats de la Stratégie Avancée :")
    print("=" * 50)
    
    # Tri par Calmar Ratio (meilleur indicateur de qualité)
    best_results = sorted(all_results, key=lambda x: x['metrics']['Calmar_Ratio'], reverse=True)
    
    print(f"\n🥇 Top 5 par Calmar Ratio (Performance/Drawdown) :")
    for i, result in enumerate(best_results[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Performance']:.2%} perf, {metrics['Max_Drawdown']:.1f}% DD, Calmar: {metrics['Calmar_Ratio']:.2f}")
    
    # Tri par performance
    perf_results = sorted(all_results, key=lambda x: x['metrics']['Performance'], reverse=True)
    
    print(f"\n📈 Top 5 par Performance :")
    for i, result in enumerate(perf_results[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Performance']:.2%} perf, {metrics['Max_Drawdown']:.1f}% DD")
    
    # Tri par drawdown minimum
    dd_results = sorted(all_results, key=lambda x: x['metrics']['Max_Drawdown'])
    
    print(f"\n🛡️ Top 5 par Drawdown Minimum :")
    for i, result in enumerate(dd_results[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Max_Drawdown']:.1f}% DD, {metrics['Performance']:.2%} perf")
    
    # Statistiques globales
    positive_results = [r for r in all_results if r['metrics']['Performance'] > 0]
    avg_drawdown = np.mean([r['metrics']['Max_Drawdown'] for r in all_results])
    avg_calmar = np.mean([r['metrics']['Calmar_Ratio'] for r in all_results])
    
    print(f"\n📊 Statistiques Globales :")
    print(f"   - Stratégies rentables: {len(positive_results)}/{len(all_results)} ({len(positive_results)/len(all_results)*100:.1f}%)")
    print(f"   - Drawdown moyen: {avg_drawdown:.1f}%")
    print(f"   - Calmar Ratio moyen: {avg_calmar:.2f}")
    
    # Sauvegarde des résultats
    os.makedirs("advanced_results", exist_ok=True)
    
    # Création du rapport détaillé
    report = "## 🚀 Stratégie Avancée - Résultats Détaillés\n\n"
    report += "### 📊 Comparaison des Métriques\n\n"
    report += "| Instrument | Timeframe | Performance | Max DD | Calmar | Sharpe | Win Rate | Profit Factor |\n"
    report += "|------------|-----------|-------------|--------|--------|--------|----------|---------------|\n"
    
    for result in best_results:
        metrics = result['metrics']
        report += f"| {result['symbol']} | {result['timeframe']} | {metrics['Performance']:.2%} | {metrics['Max_Drawdown']:.1f}% | {metrics['Calmar_Ratio']:.2f} | {metrics['Sharpe_Ratio']:.2f} | {metrics['Win_Rate']:.1f}% | {metrics['Profit_Factor']:.2f} |\n"
    
    with open("advanced_results/advanced_strategy_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport détaillé sauvegardé : advanced_results/advanced_strategy_report.md")

if __name__ == "__main__":
    main() 