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

def compute_support_resistance(df, window=20):
    """Calcule les niveaux de support et résistance dynamiques"""
    df['Support'] = df['Low'].rolling(window=window).min()
    df['Resistance'] = df['High'].rolling(window=window).max()
    return df

def compute_momentum_oscillator(df, window=14):
    """Oscillateur de momentum personnalisé"""
    df['Momentum'] = (df['Close'] - df['Close'].shift(window)) / df['Close'].shift(window) * 100
    df['Momentum_MA'] = df['Momentum'].rolling(window=window).mean()
    df['Momentum_Signal'] = np.where(df['Momentum'] > df['Momentum_MA'], 1, -1)
    return df

def compute_volatility_filter(df, window=20):
    """Filtre de volatilité pour éviter les marchés trop volatils"""
    df['Volatility'] = df['Close'].rolling(window=window).std() / df['Close'].rolling(window=window).mean()
    df['Volatility_MA'] = df['Volatility'].rolling(window=window).mean()
    df['Volatility_OK'] = df['Volatility'] < df['Volatility_MA'] * 1.5  # Éviter les pics de volatilité
    return df

def compute_trend_strength(df, window=50):
    """Force de la tendance basée sur la cohérence des mouvements"""
    df['Price_Change'] = df['Close'].pct_change()
    df['Trend_Direction'] = np.where(df['Price_Change'] > 0, 1, -1)
    df['Trend_Consistency'] = df['Trend_Direction'].rolling(window=window).sum().abs() / window
    df['Strong_Trend'] = df['Trend_Consistency'] > 0.6  # Au moins 60% de cohérence
    return df

def price_action_strategy(df, symbol, timeframe):
    """Stratégie de Price Action avec gestion stricte du risque"""
    
    df = df.copy()
    
    # Paramètres adaptés par instrument
    if symbol == 'XAUUSD':
        atr_multiplier = 1.2
        profit_multiplier = 2.0
        min_trades_per_day = 0.5
        max_trades_per_day = 2
    elif symbol == 'US30.cash':
        atr_multiplier = 1.0
        profit_multiplier = 1.8
        min_trades_per_day = 0.3
        max_trades_per_day = 1.5
    elif symbol == 'EURUSD':
        atr_multiplier = 0.8
        profit_multiplier = 1.5
        min_trades_per_day = 0.2
        max_trades_per_day = 1
    else:  # GER40.cash
        atr_multiplier = 0.9
        profit_multiplier = 1.6
        min_trades_per_day = 0.2
        max_trades_per_day = 1.2
    
    # Ajustement timeframe
    if timeframe == 'D1':
        atr_multiplier *= 1.3
        profit_multiplier *= 1.2
        min_trades_per_day *= 0.3
        max_trades_per_day *= 0.5
    elif timeframe == 'H1':
        atr_multiplier *= 0.7
        profit_multiplier *= 0.8
        min_trades_per_day *= 2
        max_trades_per_day *= 3
    
    # Calcul des indicateurs Price Action
    df['ATR'] = compute_atr(df, 14)
    df = compute_support_resistance(df, 15)
    df = compute_momentum_oscillator(df, 10)
    df = compute_volatility_filter(df, 20)
    df = compute_trend_strength(df, 30)
    
    # EMAs pour contexte
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    # Volume
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.7
    
    df = df.dropna().reset_index(drop=True)
    df['Date'] = pd.to_datetime(df['Date'])

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trades = []
    
    # Gestion du risque strict
    daily_pnl = 0
    weekly_pnl = 0
    daily_trades = 0
    last_date = None
    last_week = None
    
    # Contraintes
    max_daily_dd = 0.05  # 5%
    max_weekly_dd = 0.10  # 10%
    max_daily_trades = max_trades_per_day
    min_daily_trades = min_trades_per_day

    for i in range(1, len(df)):
        current_date = df.loc[i, 'Date']
        
        # Reset quotidien
        if last_date is None or current_date.date() != last_date.date():
            daily_pnl = 0
            daily_trades = 0
            last_date = current_date
        
        # Reset hebdomadaire
        if last_week is None or current_date.isocalendar()[1] != last_week:
            weekly_pnl = 0
            last_week = current_date.isocalendar()[1]
        
        # Vérification des contraintes
        if (abs(daily_pnl) > max_daily_dd or 
            abs(weekly_pnl) > max_weekly_dd or 
            daily_trades >= max_daily_trades):
            continue
        
        # Conditions Price Action
        
        # 1. Pullback sur support/résistance
        near_support = df.loc[i, 'Close'] <= df.loc[i, 'Support'] * 1.005
        near_resistance = df.loc[i, 'Close'] >= df.loc[i, 'Resistance'] * 0.995
        
        # 2. Momentum favorable
        momentum_bullish = df.loc[i, 'Momentum_Signal'] == 1
        momentum_bearish = df.loc[i, 'Momentum_Signal'] == -1
        
        # 3. Volatilité acceptable
        volatility_ok = df.loc[i, 'Volatility_OK']
        
        # 4. Tendance cohérente
        trend_ok = df.loc[i, 'Strong_Trend']
        
        # 5. Volume confirmé
        volume_ok = df.loc[i, 'Volume_OK']
        
        # 6. Contexte EMA
        ema_bullish = df.loc[i, 'Close'] > df.loc[i, 'EMA20'] > df.loc[i, 'EMA50']
        ema_bearish = df.loc[i, 'Close'] < df.loc[i, 'EMA20'] < df.loc[i, 'EMA50']
        
        # Signaux d'entrée
        long_signal = (
            near_support and 
            momentum_bullish and 
            volatility_ok and 
            trend_ok and 
            volume_ok and 
            ema_bullish
        )
        
        short_signal = (
            near_resistance and 
            momentum_bearish and 
            volatility_ok and 
            trend_ok and 
            volume_ok and 
            ema_bearish
        )
        
        if position == 0:
            # Entrée Long
            if long_signal:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - atr_multiplier * df.loc[i, 'ATR']
                profit_target = entry_price + profit_multiplier * df.loc[i, 'ATR']
                
            # Entrée Short
            elif short_signal:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + atr_multiplier * df.loc[i, 'ATR']
                profit_target = entry_price - profit_multiplier * df.loc[i, 'ATR']

        elif position == 1:  # Long
            # Sorties
            if df.loc[i, 'Low'] <= stop_loss:
                pnl = (stop_loss - entry_price) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                daily_trades += 1
                
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
                daily_trades += 1
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit',
                    'Date': current_date
                })
                position = 0

        elif position == -1:  # Short
            # Sorties
            if df.loc[i, 'High'] >= stop_loss:
                pnl = (entry_price - stop_loss) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                daily_trades += 1
                
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
                daily_trades += 1
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit',
                    'Date': current_date
                })
                position = 0

    return trades

def calculate_price_action_metrics(trades):
    """Calcule les métriques pour la stratégie Price Action"""
    if not trades:
        return {
            'Total_PnL': 0,
            'Performance': 0,
            'Sharpe_Ratio': 0,
            'Win_Rate': 0,
            'Total_Trades': 0,
            'Max_Daily_DD': 0,
            'Max_Weekly_DD': 0,
            'Avg_Daily_Trades': 0,
            'DD_Compliance': 100,
            'Calmar_Ratio': 0,
            'Profit_Factor': 0
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
    
    # Trades par jour
    daily_trades_count = df_trades.groupby('Date_Only').size()
    avg_daily_trades = daily_trades_count.mean() if len(daily_trades_count) > 0 else 0
    
    # Vérification du respect des contraintes
    dd_compliance = 100
    if max_daily_dd > 5:
        dd_compliance -= 50
    if max_weekly_dd > 10:
        dd_compliance -= 50
    
    # Autres métriques
    winning_trades = len(df_trades[df_trades['PnL'] > 0])
    losing_trades = len(df_trades[df_trades['PnL'] < 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    # Profit Factor
    gross_profit = df_trades[df_trades['PnL'] > 0]['PnL'].sum() if winning_trades > 0 else 0
    gross_loss = abs(df_trades[df_trades['PnL'] < 0]['PnL'].sum()) if losing_trades > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Calmar Ratio
    calmar_ratio = performance / (max_weekly_dd / 100) if max_weekly_dd > 0 else 0
    
    return {
        'Total_PnL': total_pnl,
        'Performance': performance,
        'Sharpe_Ratio': df_trades['PnL'].mean() / df_trades['PnL'].std() * np.sqrt(252) if df_trades['PnL'].std() > 0 else 0,
        'Win_Rate': win_rate,
        'Total_Trades': total_trades,
        'Max_Daily_DD': max_daily_dd,
        'Max_Weekly_DD': max_weekly_dd,
        'Avg_Daily_Trades': avg_daily_trades,
        'DD_Compliance': dd_compliance,
        'Calmar_Ratio': calmar_ratio,
        'Profit_Factor': profit_factor
    }

def main():
    print("🎯 Stratégie Price Action avec Contrôle Strict du Risque")
    print("=" * 60)
    print("📋 Contraintes : 5% max par jour, 10% max par semaine")
    print("🎨 Approche : Price Action pure avec indicateurs personnalisés")
    print("=" * 60)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_results = []
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📊 Analyse Price Action de {symbol} {timeframe}...")
                
                # Chargement et backtest
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = price_action_strategy(df, symbol, timeframe)
                
                # Calcul des métriques
                metrics = calculate_price_action_metrics(trades)
                
                all_results.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'trades': trades,
                    'metrics': metrics
                })
                
                print(f"  ✅ {len(trades)} trades, {metrics['Performance']:.2%} performance")
                print(f"     🛡️ DD Quotidien: {metrics['Max_Daily_DD']:.1f}% | DD Hebdomadaire: {metrics['Max_Weekly_DD']:.1f}%")
                print(f"     📊 Trades/jour: {metrics['Avg_Daily_Trades']:.1f} | Win Rate: {metrics['Win_Rate']:.1f}%")
    
    # Affichage des résultats
    print(f"\n🏆 Résultats de la Stratégie Price Action :")
    print("=" * 60)
    
    # Tri par Calmar Ratio
    best_results = sorted(all_results, key=lambda x: x['metrics']['Calmar_Ratio'], reverse=True)
    
    print(f"\n🥇 Top 5 par Calmar Ratio (Performance/Drawdown) :")
    for i, result in enumerate(best_results[:5], 1):
        metrics = result['metrics']
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Performance']:.2%} perf, {metrics['Max_Weekly_DD']:.1f}% DD, Calmar: {metrics['Calmar_Ratio']:.2f}")
    
    # Tri par respect des contraintes
    compliant_results = [r for r in all_results if r['metrics']['DD_Compliance'] == 100]
    
    if compliant_results:
        print(f"\n✅ Stratégies respectant les contraintes ({len(compliant_results)}/{len(all_results)}) :")
        for result in compliant_results:
            metrics = result['metrics']
            print(f"   - {result['symbol']} {result['timeframe']}: {metrics['Performance']:.2%} perf, DD: {metrics['Max_Daily_DD']:.1f}%/jour, {metrics['Max_Weekly_DD']:.1f}%/semaine")
    else:
        print(f"\n⚠️ Aucune stratégie ne respecte complètement les contraintes")
        print("   Les meilleures approximations :")
        best_dd_results = sorted(all_results, key=lambda x: x['metrics']['Max_Weekly_DD'])
        for result in best_dd_results[:3]:
            metrics = result['metrics']
            print(f"   - {result['symbol']} {result['timeframe']}: DD {metrics['Max_Weekly_DD']:.1f}% (objectif: 10%)")
    
    # Statistiques globales
    positive_results = [r for r in all_results if r['metrics']['Performance'] > 0]
    avg_daily_dd = np.mean([r['metrics']['Max_Daily_DD'] for r in all_results])
    avg_weekly_dd = np.mean([r['metrics']['Max_Weekly_DD'] for r in all_results])
    
    print(f"\n📊 Statistiques Globales :")
    print(f"   - Stratégies rentables: {len(positive_results)}/{len(all_results)} ({len(positive_results)/len(all_results)*100:.1f}%)")
    print(f"   - DD Quotidien moyen: {avg_daily_dd:.1f}% (objectif: 5%)")
    print(f"   - DD Hebdomadaire moyen: {avg_weekly_dd:.1f}% (objectif: 10%)")
    
    # Sauvegarde des résultats
    os.makedirs("price_action_results", exist_ok=True)
    
    report = "## 🎯 Stratégie Price Action - Résultats\n\n"
    report += "### 📋 Contraintes Cibles\n"
    report += "- **DD Quotidien Max :** 5%\n"
    report += "- **DD Hebdomadaire Max :** 10%\n\n"
    report += "### 📊 Résultats par Instrument\n\n"
    
    for result in best_results:
        metrics = result['metrics']
        report += f"#### {result['symbol']} {result['timeframe']}\n"
        report += f"- **Performance :** {metrics['Performance']:.2%}\n"
        report += f"- **DD Quotidien :** {metrics['Max_Daily_DD']:.1f}%\n"
        report += f"- **DD Hebdomadaire :** {metrics['Max_Weekly_DD']:.1f}%\n"
        report += f"- **Calmar Ratio :** {metrics['Calmar_Ratio']:.2f}\n"
        report += f"- **Trades :** {metrics['Total_Trades']}\n"
        report += f"- **Trades/jour :** {metrics['Avg_Daily_Trades']:.1f}\n"
        report += f"- **Win Rate :** {metrics['Win_Rate']:.1f}%\n"
        report += f"- **Profit Factor :** {metrics['Profit_Factor']:.2f}\n\n"
    
    with open("price_action_results/price_action_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport sauvegardé : price_action_results/price_action_report.md")

if __name__ == "__main__":
    main() 