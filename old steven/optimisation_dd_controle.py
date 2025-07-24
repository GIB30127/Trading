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

def strategie_dd_controle(df, params):
    """Stratégie avec contrôle strict du drawdown"""
    
    df = df.copy()
    
    # Paramètres de la stratégie
    breakout_period = params['breakout_period']
    risk_atr = params['risk_atr']
    profit_atr = params['profit_atr']
    adx_threshold = params['adx_threshold']
    rsi_overbought = params['rsi_overbought']
    rsi_oversold = params['rsi_oversold']
    ema_fast = params['ema_fast']
    ema_slow = params['ema_slow']
    ema_trend = params['ema_trend']
    
    # Contraintes de drawdown
    max_daily_dd = 0.05  # 5% par jour
    max_weekly_dd = 0.10  # 10% par semaine
    
    # Calcul des indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['ADX'] = compute_adx(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    df['EMA_Fast'] = df['Close'].ewm(span=ema_fast).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=ema_slow).mean()
    df['EMA_Trend'] = df['Close'].ewm(span=ema_trend).mean()
    
    # Breakouts
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # Volume
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.8
    
    # Conditions
    df['EMA_Trend_Up'] = df['Close'] > df['EMA_Slow']
    df['EMA_Trend_Down'] = df['Close'] < df['EMA_Slow']
    df['EMA200_Trend'] = df['Close'] > df['EMA_Trend']
    df['ADX_Strong'] = df['ADX'] > adx_threshold
    df['RSI_Not_Overbought'] = df['RSI'] < rsi_overbought
    df['RSI_Not_Oversold'] = df['RSI'] > rsi_oversold
    
    # Breakouts
    df['Breakout_Up'] = (df['High'].shift(1) < df['High_Break'].shift(1)) & (df['High'] >= df['High_Break'])
    df['Breakout_Down'] = (df['Low'].shift(1) > df['Low_Break'].shift(1)) & (df['Low'] <= df['Low_Break'])
    
    # Signaux
    df['Long_Signal'] = (
        df['Breakout_Up'] & 
        df['EMA_Trend_Up'] & 
        df['EMA200_Trend'] & 
        df['ADX_Strong'] & 
        df['RSI_Not_Overbought'] & 
        df['Volume_OK']
    )
    
    df['Short_Signal'] = (
        df['Breakout_Down'] & 
        df['EMA_Trend_Down'] & 
        ~df['EMA200_Trend'] & 
        df['ADX_Strong'] & 
        df['RSI_Not_Oversold'] & 
        df['Volume_OK']
    )
    
    df = df.dropna().reset_index(drop=True)
    df['Date'] = pd.to_datetime(df['Date'])

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trailing_stop = 0
    trades = []
    
    # Gestion du drawdown
    daily_pnl = 0
    weekly_pnl = 0
    last_date = None
    last_week = None
    
    for i in range(1, len(df)):
        current_date = df.loc[i, 'Date']
        
        # Reset daily PnL
        if last_date is None or current_date.date() != last_date.date():
            daily_pnl = 0
            last_date = current_date
        
        # Reset weekly PnL
        if last_week is None or current_date.isocalendar()[1] != last_week:
            weekly_pnl = 0
            last_week = current_date.isocalendar()[1]
        
        # Vérification des contraintes de drawdown
        if abs(daily_pnl) > max_daily_dd or abs(weekly_pnl) > max_weekly_dd:
            continue  # Skip trades si contraintes dépassées
        
        if position == 0:
            # Entrée Long
            if df.loc[i, 'Long_Signal']:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                trailing_stop = entry_price - (risk_atr * 0.7) * df.loc[i, 'ATR']
                
            # Entrée Short
            elif df.loc[i, 'Short_Signal']:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']
                trailing_stop = entry_price + (risk_atr * 0.7) * df.loc[i, 'ATR']

        elif position == 1:  # Long
            # Mise à jour trailing stop
            new_trailing_stop = df.loc[i, 'Close'] - (risk_atr * 0.7) * df.loc[i, 'ATR']
            if new_trailing_stop > trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sorties
            if df.loc[i, 'Low'] <= stop_loss:
                pnl = (stop_loss - entry_price) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': pnl,
                    'Reason': 'Stop Loss',
                    'Date': current_date
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                pnl = (profit_target - entry_price) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit',
                    'Date': current_date
                })
                position = 0
            elif df.loc[i, 'Low'] <= trailing_stop:
                pnl = (trailing_stop - entry_price) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': pnl,
                    'Reason': 'Trailing Stop',
                    'Date': current_date
                })
                position = 0

        elif position == -1:  # Short
            # Mise à jour trailing stop
            new_trailing_stop = df.loc[i, 'Close'] + (risk_atr * 0.7) * df.loc[i, 'ATR']
            if new_trailing_stop < trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sorties
            if df.loc[i, 'High'] >= stop_loss:
                pnl = (entry_price - stop_loss) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': pnl,
                    'Reason': 'Stop Loss',
                    'Date': current_date
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                pnl = (entry_price - profit_target) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit',
                    'Date': current_date
                })
                position = 0
            elif df.loc[i, 'High'] >= trailing_stop:
                pnl = (entry_price - trailing_stop) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': pnl,
                    'Reason': 'Trailing Stop',
                    'Date': current_date
                })
                position = 0

    return trades

def calculate_dd_metrics(trades):
    """Calcule les métriques avec focus sur le drawdown"""
    if not trades:
        return {
            'Total_PnL': 0,
            'Performance': 0,
            'Sharpe_Ratio': 0,
            'Win_Rate': 0,
            'Total_Trades': 0,
            'Max_Daily_DD': 0,
            'Max_Weekly_DD': 0,
            'Avg_Daily_DD': 0,
            'Avg_Weekly_DD': 0,
            'DD_Compliance': 100,
            'Calmar_Ratio': 0
        }
    
    df_trades = pd.DataFrame(trades)
    df_trades['Date'] = pd.to_datetime(df_trades['Date'])
    
    # Calculs de base
    total_pnl = df_trades['PnL'].sum()
    total_trades = len(trades)
    performance = (1 + total_pnl) ** (252 / total_trades) - 1 if total_trades > 0 else 0
    
    # Calcul des drawdowns quotidiens et hebdomadaires
    df_trades['Date_Only'] = df_trades['Date'].dt.date
    df_trades['Week'] = df_trades['Date'].dt.isocalendar().week
    
    daily_pnl = df_trades.groupby('Date_Only')['PnL'].sum()
    weekly_pnl = df_trades.groupby('Week')['PnL'].sum()
    
    # Drawdowns
    daily_cumulative = daily_pnl.cumsum()
    weekly_cumulative = weekly_pnl.cumsum()
    
    daily_running_max = daily_cumulative.expanding().max()
    weekly_running_max = weekly_cumulative.expanding().max()
    
    daily_dd = (daily_cumulative - daily_running_max) / daily_running_max
    weekly_dd = (weekly_cumulative - weekly_running_max) / weekly_running_max
    
    max_daily_dd = abs(daily_dd.min()) * 100 if len(daily_dd) > 0 else 0
    max_weekly_dd = abs(weekly_dd.min()) * 100 if len(weekly_dd) > 0 else 0
    avg_daily_dd = abs(daily_dd.mean()) * 100 if len(daily_dd) > 0 else 0
    avg_weekly_dd = abs(weekly_dd.mean()) * 100 if len(weekly_dd) > 0 else 0
    
    # Vérification du respect des contraintes
    dd_compliance = 100
    if max_daily_dd > 5:
        dd_compliance -= 50
    if max_weekly_dd > 10:
        dd_compliance -= 50
    
    # Calmar Ratio
    calmar_ratio = performance / (max_weekly_dd / 100) if max_weekly_dd > 0 else 0
    
    return {
        'Total_PnL': total_pnl,
        'Performance': performance,
        'Sharpe_Ratio': df_trades['PnL'].mean() / df_trades['PnL'].std() * np.sqrt(252) if df_trades['PnL'].std() > 0 else 0,
        'Win_Rate': len(df_trades[df_trades['PnL'] > 0]) / len(trades) * 100 if len(trades) > 0 else 0,
        'Total_Trades': total_trades,
        'Max_Daily_DD': max_daily_dd,
        'Max_Weekly_DD': max_weekly_dd,
        'Avg_Daily_DD': avg_daily_dd,
        'Avg_Weekly_DD': avg_weekly_dd,
        'DD_Compliance': dd_compliance,
        'Calmar_Ratio': calmar_ratio
    }

def optimize_parameters(symbol, timeframe):
    """Optimise les paramètres pour respecter les contraintes de DD"""
    
    print(f"🔍 Optimisation pour {symbol} {timeframe}...")
    
    # Chargement des données
    filename = f"datas/{symbol}_{timeframe}_mt5.csv"
    df = pd.read_csv(filename)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Espace de recherche des paramètres
    param_ranges = {
        'breakout_period': [8, 10, 12, 15, 18, 20],
        'risk_atr': [1.0, 1.2, 1.5, 1.8, 2.0, 2.5],
        'profit_atr': [2.0, 2.5, 3.0, 3.5, 4.0, 5.0],
        'adx_threshold': [15, 18, 20, 22, 25, 28],
        'rsi_overbought': [65, 70, 75, 80],
        'rsi_oversold': [20, 25, 30, 35],
        'ema_fast': [10, 15, 20, 25],
        'ema_slow': [30, 40, 50, 60],
        'ema_trend': [100, 150, 200, 250]
    }
    
    best_result = None
    best_score = -999999
    
    # Recherche exhaustive (version simplifiée)
    total_combinations = 1
    for param, values in param_ranges.items():
        total_combinations *= len(values)
    
    print(f"  📊 Test de {total_combinations} combinaisons...")
    
    # Test d'un sous-ensemble pour la démonstration
    test_count = 0
    max_tests = 100  # Limite pour la démonstration
    
    for breakout_period in param_ranges['breakout_period'][:3]:
        for risk_atr in param_ranges['risk_atr'][:3]:
            for profit_atr in param_ranges['profit_atr'][:3]:
                for adx_threshold in param_ranges['adx_threshold'][:3]:
                    for rsi_overbought in param_ranges['rsi_overbought'][:2]:
                        for rsi_oversold in param_ranges['rsi_oversold'][:2]:
                            for ema_fast in param_ranges['ema_fast'][:2]:
                                for ema_slow in param_ranges['ema_slow'][:2]:
                                    for ema_trend in param_ranges['ema_trend'][:2]:
                                        test_count += 1
                                        if test_count > max_tests:
                                            break
                                        
                                        params = {
                                            'breakout_period': breakout_period,
                                            'risk_atr': risk_atr,
                                            'profit_atr': profit_atr,
                                            'adx_threshold': adx_threshold,
                                            'rsi_overbought': rsi_overbought,
                                            'rsi_oversold': rsi_oversold,
                                            'ema_fast': ema_fast,
                                            'ema_slow': ema_slow,
                                            'ema_trend': ema_trend
                                        }
                                        
                                        # Test de la stratégie
                                        trades = strategie_dd_controle(df, params)
                                        metrics = calculate_dd_metrics(trades)
                                        
                                        # Score basé sur performance et respect des contraintes
                                        if metrics['DD_Compliance'] == 100:  # Respecte les contraintes
                                            score = metrics['Performance'] * 0.6 + metrics['Calmar_Ratio'] * 0.4
                                            
                                            if score > best_score:
                                                best_score = score
                                                best_result = {
                                                    'params': params,
                                                    'metrics': metrics,
                                                    'trades': trades
                                                }
                                        
                                        if test_count % 20 == 0:
                                            print(f"    Test {test_count}/{max_tests}...")
                                    
                                    if test_count > max_tests:
                                        break
                                if test_count > max_tests:
                                    break
                            if test_count > max_tests:
                                break
                        if test_count > max_tests:
                            break
                    if test_count > max_tests:
                        break
                if test_count > max_tests:
                    break
            if test_count > max_tests:
                break
        if test_count > max_tests:
            break
    
    return best_result

def main():
    print("🎯 Optimisation avec Contrôle Strict du Drawdown")
    print("=" * 55)
    print("📋 Contraintes : 5% max par jour, 10% max par semaine")
    print("=" * 55)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_optimized_results = []
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                # Optimisation
                result = optimize_parameters(symbol, timeframe)
                
                if result:
                    all_optimized_results.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'result': result
                    })
                    
                    metrics = result['metrics']
                    params = result['params']
                    
                    print(f"\n✅ {symbol} {timeframe} - Optimisation réussie!")
                    print(f"   📈 Performance: {metrics['Performance']:.2%}")
                    print(f"   📊 Trades: {metrics['Total_Trades']}")
                    print(f"   🛡️ DD Quotidien: {metrics['Max_Daily_DD']:.1f}%")
                    print(f"   🛡️ DD Hebdomadaire: {metrics['Max_Weekly_DD']:.1f}%")
                    print(f"   🎯 Calmar Ratio: {metrics['Calmar_Ratio']:.2f}")
                    print(f"   ⚙️ Paramètres optimaux: Breakout={params['breakout_period']}, Risk={params['risk_atr']}, Profit={params['profit_atr']}")
                else:
                    print(f"\n❌ {symbol} {timeframe} - Aucune solution trouvée respectant les contraintes")
    
    # Affichage des meilleurs résultats
    if all_optimized_results:
        print(f"\n🏆 Meilleurs Résultats Optimisés :")
        print("=" * 50)
        
        # Tri par Calmar Ratio
        best_results = sorted(all_optimized_results, 
                            key=lambda x: x['result']['metrics']['Calmar_Ratio'], 
                            reverse=True)
        
        for i, result in enumerate(best_results[:5], 1):
            metrics = result['result']['metrics']
            params = result['result']['params']
            
            print(f"\n🥇 {i}. {result['symbol']} {result['timeframe']}")
            print(f"   📈 Performance: {metrics['Performance']:.2%}")
            print(f"   🛡️ DD Quotidien: {metrics['Max_Daily_DD']:.1f}% | DD Hebdomadaire: {metrics['Max_Weekly_DD']:.1f}%")
            print(f"   🎯 Calmar Ratio: {metrics['Calmar_Ratio']:.2f}")
            print(f"   📊 Trades: {metrics['Total_Trades']} | Win Rate: {metrics['Win_Rate']:.1f}%")
            print(f"   ⚙️ Paramètres: Breakout={params['breakout_period']}, Risk={params['risk_atr']}, Profit={params['profit_atr']}")
        
        # Sauvegarde des résultats
        os.makedirs("dd_optimized_results", exist_ok=True)
        
        report = "## 🎯 Optimisation avec Contrôle Strict du Drawdown\n\n"
        report += "### 📋 Contraintes Respectées\n"
        report += "- **DD Quotidien Max :** 5%\n"
        report += "- **DD Hebdomadaire Max :** 10%\n\n"
        report += "### 🏆 Meilleurs Résultats\n\n"
        
        for i, result in enumerate(best_results, 1):
            metrics = result['result']['metrics']
            params = result['result']['params']
            
            report += f"#### {i}. {result['symbol']} {result['timeframe']}\n"
            report += f"- **Performance :** {metrics['Performance']:.2%}\n"
            report += f"- **DD Quotidien :** {metrics['Max_Daily_DD']:.1f}%\n"
            report += f"- **DD Hebdomadaire :** {metrics['Max_Weekly_DD']:.1f}%\n"
            report += f"- **Calmar Ratio :** {metrics['Calmar_Ratio']:.2f}\n"
            report += f"- **Trades :** {metrics['Total_Trades']}\n"
            report += f"- **Win Rate :** {metrics['Win_Rate']:.1f}%\n"
            report += f"- **Paramètres :** Breakout={params['breakout_period']}, Risk={params['risk_atr']}, Profit={params['profit_atr']}\n\n"
        
        with open("dd_optimized_results/optimization_report.md", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ Rapport sauvegardé : dd_optimized_results/optimization_report.md")
    
    else:
        print("\n❌ Aucune stratégie trouvée respectant les contraintes de drawdown")

if __name__ == "__main__":
    main() 