import pandas as pd
import numpy as np

# Paramètres de la stratégie
ema_fast_len = 9
ema_slow_len = 21
rsi_len = 14
rsi_ov_buy = 30
rsi_ov_sell = 70
take_profit_perc = 1.5 / 100
stop_loss_perc = 0.7 / 100

# Liste des actifs et timeframes
assets = [
    ("XAUUSD", ["M15", "H1"]),
    ("DJI", ["M15", "H1"]),
    ("EURUSD", ["M15", "H1"])
]

def compute_ema(series, window):
    return series.ewm(span=window, adjust=False).mean()

def compute_rsi(series, window):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def backtest(df):
    df['ema_fast'] = compute_ema(df['Close'], ema_fast_len)
    df['ema_slow'] = compute_ema(df['Close'], ema_slow_len)
    df['rsi'] = compute_rsi(df['Close'], rsi_len)
    df = df.dropna().reset_index(drop=True)

    position = 0  # 1 = long, -1 = short, 0 = flat
    entry_price = 0
    results = []

    for i in range(1, len(df)):
        # Signaux d'entrée
        long_cond = (df.loc[i-1, 'ema_fast'] < df.loc[i-1, 'ema_slow']) and \
                    (df.loc[i, 'ema_fast'] > df.loc[i, 'ema_slow']) and \
                    (df.loc[i, 'rsi'] < rsi_ov_buy)
        short_cond = (df.loc[i-1, 'ema_fast'] > df.loc[i-1, 'ema_slow']) and \
                     (df.loc[i, 'ema_fast'] < df.loc[i, 'ema_slow']) and \
                     (df.loc[i, 'rsi'] > rsi_ov_sell)

        # Entrée en position
        if position == 0:
            if long_cond:
                position = 1
                entry_price = df.loc[i, 'Close']
                sl = entry_price * (1 - stop_loss_perc)
                tp = entry_price * (1 + take_profit_perc)
            elif short_cond:
                position = -1
                entry_price = df.loc[i, 'Close']
                sl = entry_price * (1 + stop_loss_perc)
                tp = entry_price * (1 - take_profit_perc)
        # Gestion de la position
        elif position == 1:
            # Stop Loss ou Take Profit
            if df.loc[i, 'Low'] <= sl:
                results.append((sl - entry_price) / entry_price)
                position = 0
            elif df.loc[i, 'High'] >= tp:
                results.append((tp - entry_price) / entry_price)
                position = 0
        elif position == -1:
            if df.loc[i, 'High'] >= sl:
                results.append((entry_price - sl) / entry_price)
                position = 0
            elif df.loc[i, 'Low'] <= tp:
                results.append((entry_price - tp) / entry_price)
                position = 0

    # Calcul de la performance
    if results:
        perf = (np.prod([1 + r for r in results]) - 1) * 100
    else:
        perf = 0
    return perf, len(results)

# === Test avec données fictives pour valider le code ===
data_test = {
    'Date': pd.date_range(start='2023-01-01', periods=50, freq='H'),
    'Open': np.linspace(1.05, 1.10, 50),
    'High': np.linspace(1.051, 1.101, 50),
    'Low': np.linspace(1.049, 1.099, 50),
    'Close': np.linspace(1.05, 1.10, 50) + np.random.normal(0, 0.001, 50),
    'Volume': np.random.randint(100, 200, 50)
}
df_test = pd.DataFrame(data_test)
perf, n_trades = backtest(df_test)
print(f"[TEST] Performance sur données fictives : {perf:.2f}% sur {n_trades} trades")

# === Utilisation réelle avec un fichier CSV ===
filename = "EURUSD_H1.csv"
try:
    df = pd.read_csv(filename)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    perf, n_trades = backtest(df)
    print(f"EURUSD H1 : {perf:.2f}% de performance sur {n_trades} trades")
except Exception as e:
    print(f"Erreur lors de la lecture ou du traitement du fichier : {e}") 