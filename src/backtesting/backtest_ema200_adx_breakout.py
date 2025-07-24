import os
import pandas as pd
import numpy as np
from rich import print


# === Paramètres de la stratégie ===
PERIODE_EMA = 50  # plus court
PERIODE_ADX = 14
PERIODE_ATR = 14
PERIODE_BREAKOUT = 10  # plus court
SEUIL_ADX = 10  # plus bas
RISK_ATR = 1.5  # stop à 1.5 ATR

SYMBOLS = ['XAUUSD', 'EURUSD', 'US30.cash', 'GER40.cash']
TIMEFRAMES = ['M15', 'M30', 'H1', 'H4', 'D1']

SUP_RES_WINDOW = 20  # fenêtre pour support/résistance

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

# === Backtest breakout EMA200/ADX/ATR ===
def backtest_breakout(df):
    df = df.copy()
    df['EMA'] = compute_ema(df['Close'], PERIODE_EMA)
    df['ATR'] = compute_atr(df, PERIODE_ATR)
    df['ADX'] = compute_adx(df, PERIODE_ADX)
    df['High_Break'] = df['High'].rolling(window=PERIODE_BREAKOUT).max()
    df['Low_Break'] = df['Low'].rolling(window=PERIODE_BREAKOUT).min()
    # Support/résistance
    df['Resistance'] = df['High'].shift(1).rolling(window=SUP_RES_WINDOW).max()
    df['Support'] = df['Low'].shift(1).rolling(window=SUP_RES_WINDOW).min()
    df = df.dropna().reset_index(drop=True)

    position = 0  # 1=long, -1=short, 0=flat
    entry_price = 0
    stop_loss = 0
    trades = []
    # Debug : compteurs de conditions
    count_long_cond = 0
    count_short_cond = 0
    count_adx = 0
    count_breakout_long = 0
    count_breakout_short = 0
    count_ema_long = 0
    count_ema_short = 0

    for i in range(1, len(df)):
        ema_long = df.loc[i, 'Close'] > df.loc[i, 'EMA']
        ema_short = df.loc[i, 'Close'] < df.loc[i, 'EMA']
        breakout_long = df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and df.loc[i, 'High'] >= df.loc[i, 'High_Break']
        breakout_short = df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and df.loc[i, 'Low'] <= df.loc[i, 'Low_Break']
        adx_ok = df.loc[i, 'ADX'] > SEUIL_ADX
        if ema_long:
            count_ema_long += 1
        if ema_short:
            count_ema_short += 1
        if breakout_long:
            count_breakout_long += 1
        if breakout_short:
            count_breakout_short += 1
        if adx_ok:
            count_adx += 1
        long_cond = ema_long and breakout_long and adx_ok
        short_cond = ema_short and breakout_short and adx_ok
        if long_cond:
            count_long_cond += 1
        if short_cond:
            count_short_cond += 1
        if position == 0:
            if long_cond:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - RISK_ATR * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                # Extension de Fibonacci sur le dernier swing
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Long')
                # Support/résistance
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                # BOS (Break of Structure)
                bos = df.loc[i, 'High'] > df.loc[i-1, 'High_Break']
            elif short_cond:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + RISK_ATR * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Short')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'Low'] < df.loc[i-1, 'Low_Break']
        elif position == 1:
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
                stop_loss = entry_price + RISK_ATR * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Short')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'Low'] < df.loc[i-1, 'Low_Break']
        elif position == -1:
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
                stop_loss = entry_price - RISK_ATR * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Long')
                resistance = df.loc[i, 'Resistance']
                support = df.loc[i, 'Support']
                bos = df.loc[i, 'High'] > df.loc[i-1, 'High_Break']
    if position != 0:
        trades.append({
            'Type': 'Long' if position == 1 else 'Short',
            'Entry': entry_price,
            'Exit': df.iloc[-1]['Close'],
            'PnL': (df.iloc[-1]['Close'] - entry_price) / entry_price if position == 1 else (entry_price - df.iloc[-1]['Close']) / entry_price,
            'EntryDate': entry_date,
            'ExitDate': df.iloc[-1]['Date'] if 'Date' in df.columns else len(df)-1,
            'Support': support,
            'Resistance': resistance,
            'BOS': bos,
            **fibs
        })
    # Affichage debug
    print(f"\nDEBUG: {len(df)} bougies, EMA long: {count_ema_long}, EMA short: {count_ema_short}, Breakout long: {count_breakout_long}, Breakout short: {count_breakout_short}, ADX>10: {count_adx}, Signaux long: {count_long_cond}, Signaux short: {count_short_cond}")
    return trades

def rapport_detaille(trades, nom_fichier):
    if not trades:
        return f"## {nom_fichier}\nAucun trade détecté.\n"
    df_trades = pd.DataFrame(trades)
    perf = (np.prod([1 + pnl for pnl in df_trades['PnL']]) - 1) * 100
    n_trades = len(df_trades)
    n_gagnants = (df_trades['PnL'] > 0).sum()
    n_perdants = (df_trades['PnL'] <= 0).sum()
    gain_total = df_trades['PnL'].sum()
    pnl_moyen = df_trades['PnL'].mean()
    pnl_std = df_trades['PnL'].std()
    sharpe = (pnl_moyen / pnl_std) * np.sqrt(252) if pnl_std > 0 else 0
    rapport = f"## {nom_fichier}\n"
    rapport += f"- Performance totale : {perf:.2f}%\n"
    rapport += f"- Sharpe Ratio : {sharpe:.2f}\n"
    rapport += f"- Nombre de trades : {n_trades}\n"
    rapport += f"- Trades gagnants : {n_gagnants}\n"
    rapport += f"- Trades perdants : {n_perdants}\n"
    rapport += f"- Gain total (somme des PnL) : {gain_total:.4f}\n"
    # Colonnes dynamiques pour extensions de fibo, support/résistance, BOS
    fib_cols = [col for col in df_trades.columns if col.startswith('Fib_')]
    extra_cols = ['Support', 'Resistance', 'BOS']
    header = '| Type | Date entrée | Date sortie | Entrée | Sortie | PnL (%) |' + ''.join([f' {col} |' for col in extra_cols + fib_cols]) + '\n'
    rapport += f"\n{header}|------|-------------|-------------|--------|--------|---------|" + ''.join(['---------|' for _ in extra_cols + fib_cols]) + '\n'
    for _, row in df_trades.iterrows():
        extra_vals = ''.join([f' {row[col] if col != "BOS" else str(row[col])} |' for col in extra_cols])
        fib_vals = ''.join([f' {row[col]:.5f} |' for col in fib_cols])
        rapport += f"| {row['Type']} | {row['EntryDate']} | {row['ExitDate']} | {row['Entry']:.5f} | {row['Exit']:.5f} | {row['PnL']*100:.2f} |{extra_vals}{fib_vals}\n"
    rapport += "\n"
    return rapport

# === Traitement de tous les CSV du dossier datas/ ===
def main():
    folder = 'datas'
    out_folder = 'backtest'
    os.makedirs(out_folder, exist_ok=True)
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            rapport_global = f"# Rapport de backtest EMA/ADX/ATR/Breakout pour {symbol} {tf}\n\n"
            # Cherche tous les fichiers CSV du symbole et timeframe
            files = [f for f in os.listdir(folder) if f.startswith(symbol) and f'_{tf}_' in f and f.endswith('.csv')]
            if not files:
                print(f'[yellow]Aucun fichier trouvé pour {symbol} {tf} dans {folder}/[/yellow]')
                continue
            for file in files:
                print(f'\nTraitement de {file}...')
                df = pd.read_csv(os.path.join(folder, file))
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                trades = backtest_breakout(df)
                rapport_global += rapport_detaille(trades, file)
            out_path = os.path.join(out_folder, f'{symbol}_{tf}_backtest.md')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(rapport_global)
            print(f'[green]Rapport détaillé enregistré dans {out_path}[/green]')

if __name__ == '__main__':
    main() 