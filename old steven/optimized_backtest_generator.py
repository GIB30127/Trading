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

def determine_optimal_parameters(symbol, timeframe):
    """Détermine les paramètres optimaux basés sur l'analyse des signaux"""
    
    # Paramètres de base par instrument
    base_params = {
        'XAUUSD': {
            'ADX_THRESHOLD': 15,  # Or plus volatil, ADX plus bas
            'BREAKOUT_PERIOD': 8,
            'EMA_FAST': 20,
            'EMA_SLOW': 50,
            'EMA_TREND': 200,
            'RISK_ATR': 2.0,  # Stop plus large pour l'or
            'PROFIT_TARGET': 3.0,
            'TRAILING_STOP': 1.5,
            'RSI_OVERBOUGHT': 75,
            'RSI_OVERSOLD': 25,
            'USE_TREND_FILTER': False,  # Or fonctionne bien en range
            'USE_VOLUME_FILTER': True,
            'MIN_VOLUME_ATR': 0.8
        },
        'US30.cash': {
            'ADX_THRESHOLD': 20,  # Indices plus directionnels
            'BREAKOUT_PERIOD': 10,
            'EMA_FAST': 20,
            'EMA_SLOW': 50,
            'EMA_TREND': 200,
            'RISK_ATR': 1.5,
            'PROFIT_TARGET': 4.0,
            'TRAILING_STOP': 1.2,
            'RSI_OVERBOUGHT': 70,
            'RSI_OVERSOLD': 30,
            'USE_TREND_FILTER': True,
            'USE_VOLUME_FILTER': True,
            'MIN_VOLUME_ATR': 1.0
        },
        'EURUSD': {
            'ADX_THRESHOLD': 18,
            'BREAKOUT_PERIOD': 8,
            'EMA_FAST': 20,
            'EMA_SLOW': 50,
            'EMA_TREND': 200,
            'RISK_ATR': 1.8,
            'PROFIT_TARGET': 3.5,
            'TRAILING_STOP': 1.3,
            'RSI_OVERBOUGHT': 70,
            'RSI_OVERSOLD': 30,
            'USE_TREND_FILTER': True,
            'USE_VOLUME_FILTER': True,
            'MIN_VOLUME_ATR': 0.9
        },
        'GER40.cash': {
            'ADX_THRESHOLD': 18,
            'BREAKOUT_PERIOD': 8,
            'EMA_FAST': 20,
            'EMA_SLOW': 50,
            'EMA_TREND': 200,
            'RISK_ATR': 1.6,
            'PROFIT_TARGET': 3.8,
            'TRAILING_STOP': 1.2,
            'RSI_OVERBOUGHT': 70,
            'RSI_OVERSOLD': 30,
            'USE_TREND_FILTER': True,
            'USE_VOLUME_FILTER': True,
            'MIN_VOLUME_ATR': 1.0
        }
    }
    
    # Ajustements selon le timeframe
    timeframe_adjustments = {
        'M15': {'BREAKOUT_PERIOD': -2, 'RISK_ATR': -0.3, 'PROFIT_TARGET': -0.5},
        'M30': {'BREAKOUT_PERIOD': -1, 'RISK_ATR': -0.2, 'PROFIT_TARGET': -0.3},
        'H1': {'BREAKOUT_PERIOD': 0, 'RISK_ATR': 0, 'PROFIT_TARGET': 0},
        'H4': {'BREAKOUT_PERIOD': 1, 'RISK_ATR': 0.2, 'PROFIT_TARGET': 0.3},
        'D1': {'BREAKOUT_PERIOD': 2, 'RISK_ATR': 0.5, 'PROFIT_TARGET': 0.8}
    }
    
    # Récupération des paramètres de base
    params = base_params.get(symbol, base_params['EURUSD']).copy()
    
    # Application des ajustements timeframe
    if timeframe in timeframe_adjustments:
        adjustments = timeframe_adjustments[timeframe]
        for param, adjustment in adjustments.items():
            if param in params:
                params[param] += adjustment
                # S'assurer que les valeurs restent dans des limites raisonnables
                if param == 'BREAKOUT_PERIOD':
                    params[param] = max(5, min(20, params[param]))
                elif param == 'RISK_ATR':
                    params[param] = max(1.0, min(3.0, params[param]))
                elif param == 'PROFIT_TARGET':
                    params[param] = max(2.0, min(6.0, params[param]))
    
    return params

def backtest_hybrid_strategy(df, params):
    """Backtest de la stratégie hybride Breakout + Pullback"""
    
    df = df.copy()
    
    # Calcul des indicateurs
    df['EMA_Fast'] = df['Close'].ewm(span=params['EMA_FAST']).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=params['EMA_SLOW']).mean()
    df['EMA_Trend'] = df['Close'].ewm(span=params['EMA_TREND']).mean()
    df['ATR'] = compute_atr(df, 14)
    df['ADX'] = compute_adx(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    
    # Breakouts
    df['High_Break'] = df['High'].rolling(window=params['BREAKOUT_PERIOD']).max()
    df['Low_Break'] = df['Low'].rolling(window=params['BREAKOUT_PERIOD']).min()
    
    # Volume filter
    if params['USE_VOLUME_FILTER']:
        df['Volume_ATR'] = (df['High'] - df['Low']) / df['ATR']
        df['Volume_OK'] = df['Volume_ATR'] > params['MIN_VOLUME_ATR']
    else:
        df['Volume_OK'] = True
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trailing_stop = 0
    trades = []
    breakout_direction = 0  # 1 pour haussier, -1 pour baissier

    for i in range(1, len(df)):
        # Conditions de base
        ema_long = df.loc[i, 'Close'] > df.loc[i, 'EMA_Slow']
        ema_short = df.loc[i, 'Close'] < df.loc[i, 'EMA_Slow']
        
        # Filtre de tendance
        if params['USE_TREND_FILTER']:
            trend_long = df.loc[i, 'Close'] > df.loc[i, 'EMA_Trend']
            trend_short = df.loc[i, 'Close'] < df.loc[i, 'EMA_Trend']
        else:
            trend_long = True
            trend_short = True
        
        # Breakouts
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        
        # Pullbacks
        pullback_up = (df.loc[i, 'Close'] < df.loc[i, 'EMA_Fast'] and 
                      df.loc[i, 'EMA_Fast'] > df.loc[i, 'EMA_Slow'] and
                      df.loc[i, 'RSI'] < 50)
        pullback_down = (df.loc[i, 'Close'] > df.loc[i, 'EMA_Fast'] and 
                        df.loc[i, 'EMA_Fast'] < df.loc[i, 'EMA_Slow'] and
                        df.loc[i, 'RSI'] > 50)
        
        # Conditions ADX et RSI
        adx_ok = df.loc[i, 'ADX'] > params['ADX_THRESHOLD']
        rsi_ok_long = df.loc[i, 'RSI'] < params['RSI_OVERBOUGHT']
        rsi_ok_short = df.loc[i, 'RSI'] > params['RSI_OVERSOLD']
        volume_ok = df.loc[i, 'Volume_OK']
        
        # Détection des breakouts pour direction
        if breakout_up and not breakout_direction:
            breakout_direction = 1
        elif breakout_down and not breakout_direction:
            breakout_direction = -1
        
        # Conditions d'entrée hybride
        long_cond = (breakout_direction == 1 and pullback_up and 
                    ema_long and trend_long and adx_ok and rsi_ok_long and volume_ok)
        short_cond = (breakout_direction == -1 and pullback_down and 
                     ema_short and trend_short and adx_ok and rsi_ok_short and volume_ok)

        if position == 0:
            if long_cond:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - params['RISK_ATR'] * df.loc[i, 'ATR']
                profit_target = entry_price + params['PROFIT_TARGET'] * df.loc[i, 'ATR']
                trailing_stop = entry_price - params['TRAILING_STOP'] * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                
            elif short_cond:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + params['RISK_ATR'] * df.loc[i, 'ATR']
                profit_target = entry_price - params['PROFIT_TARGET'] * df.loc[i, 'ATR']
                trailing_stop = entry_price + params['TRAILING_STOP'] * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i

        elif position == 1:  # Position Long
            # Mise à jour du trailing stop
            new_trailing_stop = df.loc[i, 'Close'] - params['TRAILING_STOP'] * df.loc[i, 'ATR']
            if new_trailing_stop > trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sorties
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i
                })
                position = 0
                breakout_direction = 0
            elif df.loc[i, 'High'] >= profit_target:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (profit_target - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i
                })
                position = 0
                breakout_direction = 0
            elif df.loc[i, 'Low'] <= trailing_stop:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': (trailing_stop - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i
                })
                position = 0
                breakout_direction = 0

        elif position == -1:  # Position Short
            # Mise à jour du trailing stop
            new_trailing_stop = df.loc[i, 'Close'] + params['TRAILING_STOP'] * df.loc[i, 'ATR']
            if new_trailing_stop < trailing_stop:
                trailing_stop = new_trailing_stop
            
            # Sorties
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i
                })
                position = 0
                breakout_direction = 0
            elif df.loc[i, 'Low'] <= profit_target:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (entry_price - profit_target) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i
                })
                position = 0
                breakout_direction = 0
            elif df.loc[i, 'High'] >= trailing_stop:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': (entry_price - trailing_stop) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i
                })
                position = 0
                breakout_direction = 0

    return trades

def generate_backtest_report(trades, symbol, timeframe, params):
    """Génère un rapport de backtest détaillé"""
    
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
    
    # Rapport
    report = f"""## {symbol}_{timeframe}_mt5.csv

### 📊 Paramètres utilisés
- ADX Threshold: {params['ADX_THRESHOLD']}
- Breakout Period: {params['BREAKOUT_PERIOD']}
- EMA Fast: {params['EMA_FAST']}
- EMA Slow: {params['EMA_SLOW']}
- EMA Trend: {params['EMA_TREND']}
- Risk ATR: {params['RISK_ATR']}
- Profit Target: {params['PROFIT_TARGET']}
- Trailing Stop: {params['TRAILING_STOP']}
- RSI Overbought: {params['RSI_OVERBOUGHT']}
- RSI Oversold: {params['RSI_OVERSOLD']}
- Use Trend Filter: {params['USE_TREND_FILTER']}
- Use Volume Filter: {params['USE_VOLUME_FILTER']}

### 📈 Résultats
- Performance totale: {performance:.2%}
- Sharpe Ratio: {sharpe:.2f}
- Nombre de trades: {len(trades)}
- Trades gagnants: {trades_gagnants}
- Trades perdants: {trades_perdants}
- Taux de réussite: {win_rate:.1f}%
- Gain total: {total_pnl:.4f}

### 📋 Détail des trades
| Type | Date entrée | Date sortie | Entrée | Sortie | PnL (%) |
|------|-------------|-------------|--------|--------|---------|
"""
    
    for trade in trades:
        entry_date = str(trade['EntryDate'])[:10] if len(str(trade['EntryDate'])) > 10 else str(trade['EntryDate'])
        exit_date = str(trade['ExitDate'])[:10] if len(str(trade['ExitDate'])) > 10 else str(trade['ExitDate'])
        
        report += f"| {trade['Type']} | {entry_date} | {exit_date} | {trade['Entry']:.5f} | {trade['Exit']:.5f} | {trade['PnL']*100:.2f} |\n"
    
    report += "\n"
    return report

def main():
    print("🚀 Générateur de backtest optimisé par symbole")
    print("=" * 50)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    full_report = """# 📊 Backtest Stratégie Hybride Breakout + Pullback

## 🎯 Concept
Cette stratégie combine les breakouts pour identifier la direction et les pullbacks pour l'entrée optimale.

---

"""
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📊 Traitement de {symbol} {timeframe}...")
                
                # Détermination des paramètres optimaux
                params = determine_optimal_parameters(symbol, timeframe)
                
                # Chargement des données
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Backtest
                trades = backtest_hybrid_strategy(df, params)
                
                # Génération du rapport
                report_section = generate_backtest_report(trades, symbol, timeframe, params)
                full_report += report_section
    
    # Sauvegarde du rapport complet
    os.makedirs("optimized_backtests", exist_ok=True)
    with open("optimized_backtests/hybrid_strategy_backtest.md", 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    print("✅ Rapport généré : optimized_backtests/hybrid_strategy_backtest.md")
    
    # Affichage des résultats clés
    print("\n🏆 Résultats clés par instrument :")
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                params = determine_optimal_parameters(symbol, timeframe)
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = backtest_hybrid_strategy(df, params)
                
                if trades:
                    df_trades = pd.DataFrame(trades)
                    total_pnl = df_trades['PnL'].sum()
                    performance = (1 + total_pnl) ** (252 / len(trades)) - 1
                    trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
                    win_rate = trades_gagnants / len(trades) * 100
                    
                    print(f"  {symbol} {timeframe}: {performance:.1%} ({win_rate:.0f}% win rate, {len(trades)} trades)")

if __name__ == "__main__":
    main() 