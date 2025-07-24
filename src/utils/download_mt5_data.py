import MetaTrader5 as mt5
import pandas as pd

# === Paramètres ===
SYMBOLS = ['XAUUSD', 'EURUSD', 'US30.cash',"GER40.cash"]
TIMEFRAMES = {
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1
}
N_BARS = 10000  # nombre de bougies à télécharger

# === Connexion à MT5 ===
if not mt5.initialize():
    print('Erreur de connexion à MetaTrader 5')
    quit()

for symbol in SYMBOLS:
    for tf_name, tf_code in TIMEFRAMES.items():
        print(f'Téléchargement de {symbol} en {tf_name}...')
        rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, N_BARS)
        if rates is None or len(rates) == 0:
            print(f'Erreur : aucune donnée récupérée pour {symbol} {tf_name}')
            continue
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.rename(columns={'time': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'}, inplace=True)
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        output = f'datas/{symbol}_{tf_name}_mt5.csv'
        df.to_csv(output, index=False)
        print(f'Données sauvegardées dans {output} ({len(df)} lignes)')

mt5.shutdown() 