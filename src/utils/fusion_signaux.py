import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob

# Liste des fichiers CSV à traiter
def get_csv_files():
    return [f for f in os.listdir('.') if f.endswith('.csv')]

# Lecture d'un fichier CSV
def read_csv_file(filename):
    df = pd.read_csv(filename, parse_dates=['Date'])
    return df

# Calcul des indicateurs de base (RSI, MACD, etc.)
def compute_indicators(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']

    # Momentum
    df['Momentum'] = df['Close'].diff(10)

    # CCI
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    ma = tp.rolling(window=10).mean()
    md = tp.rolling(window=10).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    df['CCI'] = (tp - ma) / (0.015 * md)

    # OBV
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'][i] > df['Close'][i-1]:
            obv.append(obv[-1] + df['Volume'][i])
        elif df['Close'][i] < df['Close'][i-1]:
            obv.append(obv[-1] - df['Volume'][i])
        else:
            obv.append(obv[-1])
    df['OBV'] = obv

    # Stochastique
    low_min = df['Low'].rolling(window=14).min()
    high_max = df['High'].rolling(window=14).max()
    df['Stoch'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    df['Stoch_K'] = df['Stoch'].rolling(window=3).mean()

    # ATR
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    # MFI, CMF, VW-MACD, DIOSC, etc. peuvent être ajoutés ici
    # ...
    return df

# Détection de signaux (exemple simplifié)
def detect_signals(df):
    signals = []
    # Exemple : détection d'un croisement MACD
    df['MACD_cross'] = (df['MACD'] > df['MACD_signal']) & (df['MACD'].shift(1) <= df['MACD_signal'].shift(1))
    for idx, row in df.iterrows():
        if row['MACD_cross']:
            signals.append({'Date': row['Date'], 'Signal': 'MACD Bullish Cross'})
    # Ajouter ici la détection des autres signaux fusionnés
    return pd.DataFrame(signals)

# Génération d'un graphique simple
def plot_signals(df, signals, filename):
    plt.figure(figsize=(14,6))
    plt.plot(df['Date'], df['Close'], label='Close')
    for _, sig in signals.iterrows():
        plt.axvline(sig['Date'], color='g', linestyle='--', alpha=0.5)
    plt.title(f'Signaux détectés - {filename}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename.replace('.csv', '_signals.png'))
    plt.close()

# Backtest simple sur les signaux MACD Bullish Cross
def backtest_macd_signals(df, signals):
    trades = []
    in_trade = False
    entry_price = 0
    entry_date = None
    for idx, row in df.iterrows():
        # Si signal d'achat
        if not in_trade and row.get('MACD_cross', False):
            in_trade = True
            entry_price = row['Close']
            entry_date = row['Date']
        # Si déjà en position, on sort au prochain signal (ou à la fin)
        elif in_trade and row.get('MACD_cross', False):
            exit_price = row['Close']
            exit_date = row['Date']
            trades.append({
                'Entry Date': entry_date,
                'Entry Price': entry_price,
                'Exit Date': exit_date,
                'Exit Price': exit_price,
                'PnL': exit_price - entry_price
            })
            in_trade = True  # On peut enchaîner les signaux
            entry_price = row['Close']
            entry_date = row['Date']
    # Si une position reste ouverte à la fin
    if in_trade:
        exit_price = df.iloc[-1]['Close']
        exit_date = df.iloc[-1]['Date']
        trades.append({
            'Entry Date': entry_date,
            'Entry Price': entry_price,
            'Exit Date': exit_date,
            'Exit Price': exit_price,
            'PnL': exit_price - entry_price
        })
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        total_trades = len(trades_df)
        winning_trades = (trades_df['PnL'] > 0).sum()
        losing_trades = (trades_df['PnL'] <= 0).sum()
        win_rate = 100 * winning_trades / total_trades
        total_pnl = trades_df['PnL'].sum()
        report = f"Nombre de trades : {total_trades}\nTrades gagnants : {winning_trades}\nTrades perdants : {losing_trades}\nTaux de réussite : {win_rate:.2f}%\nGain/Perte total : {total_pnl:.2f}\n"
    else:
        report = "Aucun trade détecté.\n"
    return trades_df, report

# Traitement principal
def main():
    csv_files = get_csv_files()
    for csv_file in csv_files:
        print(f'Traitement de {csv_file}...')
        df = read_csv_file(csv_file)
        df = compute_indicators(df)
        signals = detect_signals(df)
        signals.to_csv(csv_file.replace('.csv', '_signals.csv'), index=False)
        plot_signals(df, signals, csv_file)
        # Backtest et rapport de performance
        trades_df, report = backtest_macd_signals(df, signals)
        with open(csv_file.replace('.csv', '_performance.txt'), 'w', encoding='utf-8') as f:
            f.write(report)
        print(report)
    print('Traitement terminé pour tous les fichiers.')

if __name__ == '__main__':
    main() 