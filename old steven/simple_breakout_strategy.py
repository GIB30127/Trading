import os
import pandas as pd
import numpy as np
from rich import print
import warnings
warnings.filterwarnings('ignore')

def compute_atr(df, window):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def simple_breakout_strategy(df, symbol, timeframe):
    """Stratégie de breakout simple et efficace"""
    
    df = df.copy()
    
    # Paramètres adaptés par instrument
    if symbol == 'XAUUSD':
        breakout_period = 20  # Plus long pour l'or
        risk_atr = 3.0       # Stop plus large
        profit_atr = 6.0     # Objectif plus ambitieux
        min_adx = 20         # Tendance plus forte
    elif symbol == 'US30.cash':
        breakout_period = 15
        risk_atr = 2.5
        profit_atr = 5.0
        min_adx = 18
    elif symbol == 'EURUSD':
        breakout_period = 12
        risk_atr = 2.0
        profit_atr = 4.0
        min_adx = 15
    else:  # GER40.cash
        breakout_period = 12
        risk_atr = 2.0
        profit_atr = 4.0
        min_adx = 15
    
    # Ajustement timeframe
    if timeframe == 'D1':
        breakout_period = int(breakout_period * 1.5)
        risk_atr *= 1.2
        profit_atr *= 1.2
    elif timeframe == 'H1':
        breakout_period = int(breakout_period * 0.8)
        risk_atr *= 0.8
        profit_atr *= 0.8
    
    # Calcul des indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    # Breakouts
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # Volume (simplifié)
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.8
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trades = []

    for i in range(1, len(df)):
        # Conditions de base
        ema_trend = df.loc[i, 'Close'] > df.loc[i, 'EMA50']
        volume_ok = df.loc[i, 'Volume_OK']
        
        # Breakouts purs
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])

        if position == 0:
            # Entrée Long
            if breakout_up and ema_trend and volume_ok:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                
            # Entrée Short
            elif breakout_down and not ema_trend and volume_ok:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i

        elif position == 1:  # Position Long
            # Sorties
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (profit_target - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Reason': 'Take Profit'
                })
                position = 0

        elif position == -1:  # Position Short
            # Sorties
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (entry_price - profit_target) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Reason': 'Take Profit'
                })
                position = 0

    return trades

def generate_simple_report(trades, symbol, timeframe):
    """Génère un rapport simple et clair"""
    
    if not trades:
        return f"## {symbol}_{timeframe}_mt5.csv\n- Aucun trade généré\n\n"
    
    df_trades = pd.DataFrame(trades)
    total_pnl = df_trades['PnL'].sum()
    performance = (1 + total_pnl) ** (252 / len(trades)) - 1 if len(trades) > 0 else 0
    
    # Calcul du Sharpe Ratio
    returns = df_trades['PnL']
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
    trades_perdants = len(df_trades[df_trades['PnL'] < 0])
    win_rate = trades_gagnants / len(trades) * 100 if len(trades) > 0 else 0
    
    # Ratio risque/récompense
    avg_win = df_trades[df_trades['PnL'] > 0]['PnL'].mean() if trades_gagnants > 0 else 0
    avg_loss = abs(df_trades[df_trades['PnL'] < 0]['PnL'].mean()) if trades_perdants > 0 else 0
    risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
    
    # Rapport
    report = f"""## {symbol}_{timeframe}_mt5.csv

### 📈 Résultats
- Performance totale: {performance:.2%}
- Sharpe Ratio: {sharpe:.2f}
- Nombre de trades: {len(trades)}
- Trades gagnants: {trades_gagnants}
- Trades perdants: {trades_perdants}
- Taux de réussite: {win_rate:.1f}%
- Gain total: {total_pnl:.4f}
- Ratio R/R moyen: {risk_reward:.2f}

### 📋 Détail des trades
| Type | Date entrée | Date sortie | Entrée | Sortie | PnL (%) | Raison |
|------|-------------|-------------|--------|--------|---------|--------|
"""
    
    for trade in trades:
        entry_date = str(trade['EntryDate'])[:10] if len(str(trade['EntryDate'])) > 10 else str(trade['EntryDate'])
        exit_date = str(trade['ExitDate'])[:10] if len(str(trade['ExitDate'])) > 10 else str(trade['ExitDate'])
        
        report += f"| {trade['Type']} | {entry_date} | {exit_date} | {trade['Entry']:.5f} | {trade['Exit']:.5f} | {trade['PnL']*100:.2f} | {trade['Reason']} |\n"
    
    report += "\n"
    return report

def main():
    print("🎯 Stratégie de Breakout Simple")
    print("=" * 40)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    full_report = """# 🎯 Stratégie de Breakout Simple

## 💡 Concept
Breakout pur avec gestion de risque optimisée et paramètres adaptés par instrument.

---

"""
    
    results_summary = []
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📊 Traitement de {symbol} {timeframe}...")
                
                # Chargement des données
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Backtest
                trades = simple_breakout_strategy(df, symbol, timeframe)
                
                # Génération du rapport
                report_section = generate_simple_report(trades, symbol, timeframe)
                full_report += report_section
                
                # Résumé pour comparaison
                if trades:
                    df_trades = pd.DataFrame(trades)
                    total_pnl = df_trades['PnL'].sum()
                    performance = (1 + total_pnl) ** (252 / len(trades)) - 1
                    trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
                    win_rate = trades_gagnants / len(trades) * 100
                    
                    results_summary.append({
                        'Symbol': symbol,
                        'Timeframe': timeframe,
                        'Performance': performance,
                        'WinRate': win_rate,
                        'Trades': len(trades),
                        'TotalPnL': total_pnl
                    })
    
    # Sauvegarde du rapport
    os.makedirs("simple_backtests", exist_ok=True)
    with open("simple_backtests/simple_breakout_backtest.md", 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    print("✅ Rapport généré : simple_backtests/simple_breakout_backtest.md")
    
    # Affichage des résultats clés
    print("\n🏆 Résultats par instrument :")
    for result in results_summary:
        print(f"  {result['Symbol']} {result['Timeframe']}: {result['Performance']:.1%} ({result['WinRate']:.0f}% win rate, {result['Trades']} trades)")
    
    # Meilleurs résultats
    if results_summary:
        best_performance = max(results_summary, key=lambda x: x['Performance'])
        print(f"\n🥇 Meilleur résultat: {best_performance['Symbol']} {best_performance['Timeframe']} ({best_performance['Performance']:.1%})")
        
        positive_results = [r for r in results_summary if r['Performance'] > 0]
        if positive_results:
            print(f"✅ {len(positive_results)} stratégies rentables sur {len(results_summary)}")
        else:
            print("❌ Aucune stratégie rentable - problème fondamental détecté")

if __name__ == "__main__":
    main() 