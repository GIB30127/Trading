import os
import pandas as pd
import numpy as np
from rich import print

# === Paramètres V3 - Plus équilibrés ===
PERIODE_EMA = 50
PERIODE_ADX = 14
PERIODE_ATR = 14
PERIODE_BREAKOUT = 8  # Plus réactif
SEUIL_ADX = 10  # Plus bas pour plus de signaux
RISK_ATR = 1.8
PROFIT_TARGET = 2.5
TRAILING_STOP = 1.2

# Paramètres simplifiés par instrument
INSTRUMENT_SETTINGS = {
    'XAUUSD': {
        'ADX_THRESHOLD': 8,  # Très bas pour l'or
        'BREAKOUT_PERIOD': 6,
        'RISK_ATR': 2.0,
        'PROFIT_TARGET': 2.0,
        'USE_TREND_FILTER': False  # Pas de filtre tendance pour l'or
    },
    'US30.cash': {
        'ADX_THRESHOLD': 12,
        'BREAKOUT_PERIOD': 8,
        'RISK_ATR': 1.5,
        'PROFIT_TARGET': 3.0,
        'USE_TREND_FILTER': True
    },
    'EURUSD': {
        'ADX_THRESHOLD': 10,
        'BREAKOUT_PERIOD': 8,
        'RISK_ATR': 1.8,
        'PROFIT_TARGET': 2.8,
        'USE_TREND_FILTER': True
    },
    'GER40.cash': {
        'ADX_THRESHOLD': 10,
        'BREAKOUT_PERIOD': 8,
        'RISK_ATR': 1.6,
        'PROFIT_TARGET': 3.2,
        'USE_TREND_FILTER': True
    }
}

SYMBOLS = ['XAUUSD', 'EURUSD', 'US30.cash', 'GER40.cash']
TIMEFRAMES = ['M15', 'M30', 'H1', 'H4', 'D1']

SUP_RES_WINDOW = 20

# === Fonctions indicateurs ===
def compute_ema(series, window):
    return series.ewm(span=window, adjust=False).mean()

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
    """RSI simplifié"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

FIB_EXTENSIONS = [1.618, 2.618]

def calc_fib_extensions(entry, swing_high, swing_low, direction):
    fibs = {}
    if direction == 'Long':
        range_ = swing_high - swing_low
        for ext in FIB_EXTENSIONS:
            fibs[f'Fib_{ext}'] = swing_high + ext * range_
    else:
        range_ = swing_high - swing_low
        for ext in FIB_EXTENSIONS:
            fibs[f'Fib_{ext}'] = swing_low - ext * range_
    return fibs

# === Backtest V3 - Conditions simplifiées ===
def backtest_breakout_v3(df, symbol):
    df = df.copy()
    
    # Récupération des paramètres spécifiques à l'instrument
    settings = INSTRUMENT_SETTINGS.get(symbol, INSTRUMENT_SETTINGS['EURUSD'])
    
    df['EMA'] = compute_ema(df['Close'], PERIODE_EMA)
    df['EMA200'] = compute_ema(df['Close'], 200)
    df['ATR'] = compute_atr(df, PERIODE_ATR)
    df['ADX'] = compute_adx(df, PERIODE_ADX)
    df['RSI'] = compute_rsi(df, 14)
    
    # Paramètres adaptatifs
    breakout_period = settings['BREAKOUT_PERIOD']
    adx_threshold = settings['ADX_THRESHOLD']
    risk_atr = settings['RISK_ATR']
    profit_target = settings['PROFIT_TARGET']
    use_trend_filter = settings['USE_TREND_FILTER']
    
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    df['Resistance'] = df['High'].shift(1).rolling(window=SUP_RES_WINDOW).max()
    df['Support'] = df['Low'].shift(1).rolling(window=SUP_RES_WINDOW).min()
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target_price = 0
    trailing_stop = 0
    trades = []

    # Compteurs de debug
    count_ema_long = 0
    count_ema_short = 0
    count_breakout_long = 0
    count_breakout_short = 0
    count_adx = 0
    count_trend_long = 0
    count_trend_short = 0
    count_rsi_long = 0
    count_rsi_short = 0

    for i in range(1, len(df)):
        # Conditions de base
        ema_long = df.loc[i, 'Close'] > df.loc[i, 'EMA']
        ema_short = df.loc[i, 'Close'] < df.loc[i, 'EMA']
        
        if ema_long:
            count_ema_long += 1
        if ema_short:
            count_ema_short += 1
        
        # Filtre de tendance conditionnel
        if use_trend_filter:
            trend_long = df.loc[i, 'Close'] > df.loc[i, 'EMA200']
            trend_short = df.loc[i, 'Close'] < df.loc[i, 'EMA200']
            if trend_long:
                count_trend_long += 1
            if trend_short:
                count_trend_short += 1
        else:
            trend_long = True
            trend_short = True
        
        breakout_long = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                        df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_short = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                         df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        
        if breakout_long:
            count_breakout_long += 1
        if breakout_short:
            count_breakout_short += 1
        
        adx_ok = df.loc[i, 'ADX'] > adx_threshold
        if adx_ok:
            count_adx += 1
        
        # Filtres RSI plus permissifs
        rsi_ok_long = df.loc[i, 'RSI'] < 75  # Plus permissif (70 -> 75)
        rsi_ok_short = df.loc[i, 'RSI'] > 25  # Plus permissif (30 -> 25)
        
        if rsi_ok_long:
            count_rsi_long += 1
        if rsi_ok_short:
            count_rsi_short += 1
        
        # Conditions V3 - Plus simples
        long_cond = (ema_long and trend_long and breakout_long and 
                    adx_ok and rsi_ok_long)
        short_cond = (ema_short and trend_short and breakout_short and 
                     adx_ok and rsi_ok_short)

        if position == 0:
            if long_cond:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target_price = entry_price + profit_target * df.loc[i, 'ATR']
                trailing_stop = entry_price - TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Long')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'High'] > df.loc[i-1, 'High_Break']
                
            elif short_cond:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target_price = entry_price - profit_target * df.loc[i, 'ATR']
                trailing_stop = entry_price + TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Short')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'Low'] < df.loc[i-1, 'Low_Break']

        elif position == 1:  # Position Long
            # Mise à jour du trailing stop
            new_trailing_stop = df.loc[i, 'Close'] - TRAILING_STOP * df.loc[i, 'ATR']
            if new_trailing_stop > trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sortie par stop loss
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 0
            # Sortie par profit target
            elif df.loc[i, 'High'] >= profit_target_price:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target_price,
                    'PnL': (profit_target_price - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 0
            # Sortie par trailing stop
            elif df.loc[i, 'Low'] <= trailing_stop:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': (trailing_stop - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 0
            # Inversion de position
            elif short_cond:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': df.loc[i, 'Close'],
                    'PnL': (df.loc[i, 'Close'] - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target_price = entry_price - profit_target * df.loc[i, 'ATR']
                trailing_stop = entry_price + TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Short')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'Low'] < df.loc[i-1, 'Low_Break']

        elif position == -1:  # Position Short
            # Mise à jour du trailing stop
            new_trailing_stop = df.loc[i, 'Close'] + TRAILING_STOP * df.loc[i, 'ATR']
            if new_trailing_stop < trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sortie par stop loss
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 0
            # Sortie par profit target
            elif df.loc[i, 'Low'] <= profit_target_price:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target_price,
                    'PnL': (entry_price - profit_target_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 0
            # Sortie par trailing stop
            elif df.loc[i, 'High'] >= trailing_stop:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': (entry_price - trailing_stop) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 0
            # Inversion de position
            elif long_cond:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': df.loc[i, 'Close'],
                    'PnL': (entry_price - df.loc[i, 'Close']) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    'Support': support,
                    'Resistance': resistance,
                    'BOS': bos,
                    **fibs
                })
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target_price = entry_price + profit_target * df.loc[i, 'ATR']
                trailing_stop = entry_price - TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Long')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'High'] > df.loc[i-1, 'High_Break']

    # Debug info
    print(f"\n🔍 Debug {symbol}:")
    print(f"  EMA Long: {count_ema_long}, EMA Short: {count_ema_short}")
    print(f"  Breakout Long: {count_breakout_long}, Breakout Short: {count_breakout_short}")
    print(f"  ADX OK: {count_adx}")
    print(f"  Trend Long: {count_trend_long}, Trend Short: {count_trend_short}")
    print(f"  RSI Long: {count_rsi_long}, RSI Short: {count_rsi_short}")

    return trades

def rapport_detaille(trades, nom_fichier):
    if not trades:
        print(f"Aucun trade pour {nom_fichier}")
        return

    df_trades = pd.DataFrame(trades)
    total_pnl = df_trades['PnL'].sum()
    performance = (1 + total_pnl) ** (252 / len(trades)) - 1 if len(trades) > 0 else 0
    
    # Calcul du Sharpe Ratio
    returns = df_trades['PnL']
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
    trades_perdants = len(df_trades[df_trades['PnL'] < 0])
    
    print(f"\n# Rapport de backtest V3 pour {nom_fichier}")
    print(f"\n## {nom_fichier}")
    print(f"- Performance totale : {performance:.2%}")
    print(f"- Sharpe Ratio : {sharpe:.2f}")
    print(f"- Nombre de trades : {len(trades)}")
    print(f"- Trades gagnants : {trades_gagnants}")
    print(f"- Trades perdants : {trades_perdants}")
    print(f"- Taux de réussite : {trades_gagnants/len(trades)*100:.1f}%")
    print(f"- Gain total (somme des PnL) : {total_pnl:.4f}")
    
    # Affichage des trades
    print("\n| Type | Date entrée | Date sortie | Entrée | Sortie | PnL (%) | Fib_1.618 | Fib_2.618 |")
    print("|------|-------------|-------------|--------|--------|---------|---------|---------|")
    
    for trade in trades:
        entry_date = str(trade['EntryDate'])[:10] if len(str(trade['EntryDate'])) > 10 else str(trade['EntryDate'])
        exit_date = str(trade['ExitDate'])[:10] if len(str(trade['ExitDate'])) > 10 else str(trade['ExitDate'])
        
        print(f"| {trade['Type']} | {entry_date} | {exit_date} | {trade['Entry']:.5f} | {trade['Exit']:.5f} | {trade['PnL']*100:.2f} | {trade.get('Fib_1.618', 0):.5f} | {trade.get('Fib_2.618', 0):.5f} |")

def main():
    print("🚀 Backtest V3 - Conditions simplifiées pour plus de trades")
    print("=" * 60)
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"\n📊 Traitement de {symbol} {timeframe}...")
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = backtest_breakout_v3(df, symbol)
                
                rapport_detaille(trades, f"{symbol}_{timeframe}_mt5.csv")
                
                # Sauvegarde du rapport
                output_file = f"backtest_v3/{symbol}_{timeframe}_backtest_v3.md"
                os.makedirs("backtest_v3", exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Rapport de backtest V3 pour {symbol} {timeframe}\n\n")
                    f.write(f"## {symbol}_{timeframe}_mt5.csv\n")
                    
                    if trades:
                        df_trades = pd.DataFrame(trades)
                        total_pnl = df_trades['PnL'].sum()
                        performance = (1 + total_pnl) ** (252 / len(trades)) - 1
                        returns = df_trades['PnL']
                        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                        trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
                        trades_perdants = len(df_trades[df_trades['PnL'] < 0])
                        
                        f.write(f"- Performance totale : {performance:.2%}\n")
                        f.write(f"- Sharpe Ratio : {sharpe:.2f}\n")
                        f.write(f"- Nombre de trades : {len(trades)}\n")
                        f.write(f"- Trades gagnants : {trades_gagnants}\n")
                        f.write(f"- Trades perdants : {trades_perdants}\n")
                        f.write(f"- Taux de réussite : {trades_gagnants/len(trades)*100:.1f}%\n")
                        f.write(f"- Gain total (somme des PnL) : {total_pnl:.4f}\n\n")
                        
                        f.write("| Type | Date entrée | Date sortie | Entrée | Sortie | PnL (%) | Fib_1.618 | Fib_2.618 |\n")
                        f.write("|------|-------------|-------------|--------|--------|---------|---------|---------|\n")
                        
                        for trade in trades:
                            entry_date = str(trade['EntryDate'])[:10] if len(str(trade['EntryDate'])) > 10 else str(trade['EntryDate'])
                            exit_date = str(trade['ExitDate'])[:10] if len(str(trade['ExitDate'])) > 10 else str(trade['ExitDate'])
                            
                            f.write(f"| {trade['Type']} | {entry_date} | {exit_date} | {trade['Entry']:.5f} | {trade['Exit']:.5f} | {trade['PnL']*100:.2f} | {trade.get('Fib_1.618', 0):.5f} | {trade.get('Fib_2.618', 0):.5f} |\n")
                    else:
                        f.write("- Aucun trade généré\n")

if __name__ == "__main__":
    main() 