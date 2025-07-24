import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

def compute_atr(df, window=14):
    """Calcule l'ATR (Average True Range)"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_rsi(df, window=14):
    """Calcule le RSI (Relative Strength Index)"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_adx(df, window=14):
    """Calcule l'ADX (Average Directional Index)"""
    # True Range
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # Directional Movement
    up_move = df['High'] - df['High'].shift(1)
    down_move = df['Low'].shift(1) - df['Low']
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smoothed values
    tr_smooth = tr.rolling(window=window).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(window=window).mean() / tr_smooth
    minus_di = 100 * pd.Series(minus_dm).rolling(window=window).mean() / tr_smooth
    
    # ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=window).mean()
    
    return adx

def get_timeframe_params(timeframe):
    """Retourne les paramètres optimisés selon le timeframe"""
    params = {
        'M15': {
            'breakout_period': 6,
            'risk_atr': 1.0,
            'profit_atr': 2.0,
            'rsi_overbought': 75,
            'rsi_oversold': 25,
            'adx_threshold': 18,
            'ema_short': 15,
            'ema_long': 40
        },
        'M30': {
            'breakout_period': 8,
            'risk_atr': 1.1,
            'profit_atr': 2.2,
            'rsi_overbought': 74,
            'rsi_oversold': 26,
            'adx_threshold': 19,
            'ema_short': 18,
            'ema_long': 45
        },
        'H1': {
            'breakout_period': 10,
            'risk_atr': 1.3,
            'profit_atr': 2.7,
            'rsi_overbought': 73,
            'rsi_oversold': 27,
            'adx_threshold': 20,
            'ema_short': 20,
            'ema_long': 50
        },
        'H4': {
            'breakout_period': 12,
            'risk_atr': 1.4,
            'profit_atr': 2.8,
            'rsi_overbought': 72,
            'rsi_oversold': 28,
            'adx_threshold': 22,
            'ema_short': 22,
            'ema_long': 55
        },
        'D1': {
            'breakout_period': 15,
            'risk_atr': 1.6,
            'profit_atr': 3.2,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'adx_threshold': 25,
            'ema_short': 25,
            'ema_long': 60
        }
    }
    return params.get(timeframe, params['H1'])

def get_symbol_adjustments(symbol):
    """Ajustements spécifiques par symbole"""
    if symbol == 'XAUUSD':
        return {
            'risk_multiplier': 1.1,  # Gold plus volatil
            'profit_multiplier': 1.2,
            'rsi_adjustment': 2,  # RSI plus strict pour Gold
            'adx_adjustment': -2
        }
    elif symbol == 'GER40.cash':
        return {
            'risk_multiplier': 0.9,  # Indice moins volatil
            'profit_multiplier': 0.95,
            'rsi_adjustment': -1,
            'adx_adjustment': 3
        }
    else:
        return {
            'risk_multiplier': 1.0,
            'profit_multiplier': 1.0,
            'rsi_adjustment': 0,
            'adx_adjustment': 0
        }

def strategie_multitimeframe(df, symbol, timeframe):
    """
    Stratégie multitimeframe optimisée pour Pine Script v6
    Compatible avec XAUUSD et GER40.cash sur tous timeframes
    """
    
    df = df.copy()
    
    # Paramètres de base selon timeframe
    base_params = get_timeframe_params(timeframe)
    symbol_adjustments = get_symbol_adjustments(symbol)
    
    # Application des ajustements
    params = {
        'breakout_period': base_params['breakout_period'],
        'risk_atr': base_params['risk_atr'] * symbol_adjustments['risk_multiplier'],
        'profit_atr': base_params['profit_atr'] * symbol_adjustments['profit_multiplier'],
        'rsi_overbought': base_params['rsi_overbought'] + symbol_adjustments['rsi_adjustment'],
        'rsi_oversold': base_params['rsi_oversold'] - symbol_adjustments['rsi_adjustment'],
        'adx_threshold': base_params['adx_threshold'] + symbol_adjustments['adx_adjustment'],
        'ema_short': base_params['ema_short'],
        'ema_long': base_params['ema_long']
    }
    
    # Calcul des indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    df['ADX'] = compute_adx(df, 14)
    df['EMA_Short'] = df['Close'].ewm(span=params['ema_short']).mean()
    df['EMA_Long'] = df['Close'].ewm(span=params['ema_long']).mean()
    
    # Breakouts dynamiques
    df['High_Break'] = df['High'].rolling(window=params['breakout_period']).max()
    df['Low_Break'] = df['Low'].rolling(window=params['breakout_period']).min()
    
    # Volume (si disponible)
    if 'Volume' in df.columns:
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.7
    else:
        df['Volume_OK'] = True
    
    # Filtres supplémentaires pour Pine Script v6
    df['Trend_Strength'] = abs(df['EMA_Short'] - df['EMA_Long']) / df['ATR']
    df['Volatility_OK'] = df['ATR'] > df['ATR'].rolling(window=50).mean() * 0.8
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trades = []
    
    # Compteurs pour debug
    signals_long = 0
    signals_short = 0
    trades_executed = 0

    for i in range(1, len(df)):
        # Conditions de base
        ema_trend = df.loc[i, 'Close'] > df.loc[i, 'EMA_Long']
        volume_ok = df.loc[i, 'Volume_OK']
        adx_strong = df.loc[i, 'ADX'] > params['adx_threshold']
        volatility_ok = df.loc[i, 'Volatility_OK']
        trend_strong = df.loc[i, 'Trend_Strength'] > 0.5
        
        # Breakouts
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        
        # RSI conditions
        rsi_ok_long = df.loc[i, 'RSI'] < params['rsi_overbought']
        rsi_ok_short = df.loc[i, 'RSI'] > params['rsi_oversold']
        
        # Conditions d'entrée LONG (optimisées pour Pine Script)
        long_conditions = (
            breakout_up and 
            ema_trend and 
            volume_ok and 
            adx_strong and
            volatility_ok and
            trend_strong and
            rsi_ok_long and
            df.loc[i, 'RSI'] > 35 and  # Pas en survente extrême
            df.loc[i, 'Close'] > df.loc[i, 'EMA_Short']  # Confirmation court terme
        )
        
        # Conditions d'entrée SHORT (optimisées pour Pine Script)
        short_conditions = (
            breakout_down and 
            not ema_trend and 
            volume_ok and 
            adx_strong and
            volatility_ok and
            trend_strong and
            rsi_ok_short and
            df.loc[i, 'RSI'] < 65 and  # Pas en surachat extrême
            df.loc[i, 'Close'] < df.loc[i, 'EMA_Short']  # Confirmation court terme
        )

        if position == 0:
            # Entrée LONG
            if long_conditions:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - params['risk_atr'] * df.loc[i, 'ATR']
                profit_target = entry_price + params['profit_atr'] * df.loc[i, 'ATR']
                signals_long += 1
                
            # Entrée SHORT
            elif short_conditions:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + params['risk_atr'] * df.loc[i, 'ATR']
                profit_target = entry_price - params['profit_atr'] * df.loc[i, 'ATR']
                signals_short += 1

        elif position == 1:  # Position LONG
            # Sortie par Stop Loss
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'Reason': 'Stop Loss',
                    'Date_Entry': df.index[i-1] if i > 0 else i,
                    'Date_Exit': df.index[i],
                    'Timeframe': timeframe,
                    'Symbol': symbol
                })
                position = 0
                trades_executed += 1
                
            # Sortie par Take Profit
            elif df.loc[i, 'High'] >= profit_target:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (profit_target - entry_price) / entry_price,
                    'Reason': 'Take Profit',
                    'Date_Entry': df.index[i-1] if i > 0 else i,
                    'Date_Exit': df.index[i],
                    'Timeframe': timeframe,
                    'Symbol': symbol
                })
                position = 0
                trades_executed += 1

        elif position == -1:  # Position SHORT
            # Sortie par Stop Loss
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'Reason': 'Stop Loss',
                    'Date_Entry': df.index[i-1] if i > 0 else i,
                    'Date_Exit': df.index[i],
                    'Timeframe': timeframe,
                    'Symbol': symbol
                })
                position = 0
                trades_executed += 1
                
            # Sortie par Take Profit
            elif df.loc[i, 'Low'] <= profit_target:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (entry_price - profit_target) / entry_price,
                    'Reason': 'Take Profit',
                    'Date_Entry': df.index[i-1] if i > 0 else i,
                    'Date_Exit': df.index[i],
                    'Timeframe': timeframe,
                    'Symbol': symbol
                })
                position = 0
                trades_executed += 1

    # Statistiques de debug
    print(f"📊 {symbol} {timeframe} - Statistiques:")
    print(f"   Signaux Long: {signals_long}")
    print(f"   Signaux Short: {signals_short}")
    print(f"   Trades exécutés: {trades_executed}")
    print(f"   Trades enregistrés: {len(trades)}")
    print(f"   Paramètres: Breakout={params['breakout_period']}, Risk={params['risk_atr']:.2f}, Profit={params['profit_atr']:.2f}")

    return trades

def calculate_metrics(trades):
    """Calcule les métriques de performance"""
    if not trades:
        return {
            'Total_Trades': 0,
            'Winning_Trades': 0,
            'Losing_Trades': 0,
            'Win_Rate': 0,
            'Total_PnL': 0,
            'Avg_Win': 0,
            'Avg_Loss': 0,
            'Profit_Factor': 0,
            'Sharpe_Ratio': 0
        }
    
    df_trades = pd.DataFrame(trades)
    total_trades = len(trades)
    winning_trades = len(df_trades[df_trades['PnL'] > 0])
    losing_trades = len(df_trades[df_trades['PnL'] < 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    total_pnl = df_trades['PnL'].sum()
    avg_win = df_trades[df_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = abs(df_trades[df_trades['PnL'] < 0]['PnL'].mean()) if losing_trades > 0 else 0
    profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
    
    # Sharpe Ratio simplifié
    returns = df_trades['PnL']
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    return {
        'Total_Trades': total_trades,
        'Winning_Trades': winning_trades,
        'Losing_Trades': losing_trades,
        'Win_Rate': win_rate,
        'Total_PnL': total_pnl,
        'Avg_Win': avg_win,
        'Avg_Loss': avg_loss,
        'Profit_Factor': profit_factor,
        'Sharpe_Ratio': sharpe
    }

def generate_pine_script_template(symbol, timeframe):
    """Génère un template Pine Script v6 pour la stratégie"""
    
    base_params = get_timeframe_params(timeframe)
    symbol_adjustments = get_symbol_adjustments(symbol)
    
    params = {
        'breakout_period': base_params['breakout_period'],
        'risk_atr': base_params['risk_atr'] * symbol_adjustments['risk_multiplier'],
        'profit_atr': base_params['profit_atr'] * symbol_adjustments['profit_multiplier'],
        'rsi_overbought': base_params['rsi_overbought'] + symbol_adjustments['rsi_adjustment'],
        'rsi_oversold': base_params['rsi_oversold'] - symbol_adjustments['rsi_adjustment'],
        'adx_threshold': base_params['adx_threshold'] + symbol_adjustments['adx_adjustment'],
        'ema_short': base_params['ema_short'],
        'ema_long': base_params['ema_long']
    }
    
    pine_script = f"""
//@version=6
strategy("{symbol} {timeframe} Multitimeframe Strategy", overlay=true, margin_long=100, margin_short=100)

// === PARAMÈTRES ===
breakout_period = {params['breakout_period']}
risk_atr = {params['risk_atr']:.2f}
profit_atr = {params['profit_atr']:.2f}
rsi_overbought = {params['rsi_overbought']}
rsi_oversold = {params['rsi_oversold']}
adx_threshold = {params['adx_threshold']}
ema_short = {params['ema_short']}
ema_long = {params['ema_long']}

// === INDICATEURS ===
atr = ta.atr(14)
rsi = ta.rsi(close, 14)
[diplus, diminus, adx] = ta.dmi(14, 14)
ema_short_val = ta.ema(close, ema_short)
ema_long_val = ta.ema(close, ema_long)

// Breakouts
high_break = ta.highest(high, breakout_period)
low_break = ta.lowest(low, breakout_period)

// Filtres
trend_strength = math.abs(ema_short_val - ema_long_val) / atr
volatility_ok = atr > ta.sma(atr, 50) * 0.8
volume_ok = volume > ta.sma(volume, 20) * 0.7

// === CONDITIONS ===
ema_trend = close > ema_long_val
adx_strong = adx > adx_threshold
trend_strong = trend_strength > 0.5

breakout_up = high[1] < high_break[1] and high >= high_break
breakout_down = low[1] > low_break[1] and low <= low_break

rsi_ok_long = rsi < rsi_overbought and rsi > 35
rsi_ok_short = rsi > rsi_oversold and rsi < 65

// === SIGNALS ===
long_condition = breakout_up and ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_long and close > ema_short_val
short_condition = breakout_down and not ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_short and close < ema_short_val

// === STRATÉGIE ===
if long_condition
    strategy.entry("Long", strategy.long)
    strategy.exit("Exit Long", "Long", stop=close - risk_atr * atr, limit=close + profit_atr * atr)

if short_condition
    strategy.entry("Short", strategy.short)
    strategy.exit("Exit Short", "Short", stop=close + risk_atr * atr, limit=close - profit_atr * atr)

// === PLOTS ===
plot(ema_short_val, "EMA Short", color=color.blue)
plot(ema_long_val, "EMA Long", color=color.red)
plot(high_break, "High Break", color=color.green, style=plot.style_line)
plot(low_break, "Low Break", color=color.red, style=plot.style_line)

// === ALERTS ===
alertcondition(long_condition, "Signal Long", "Signal d'achat {symbol} {timeframe}")
alertcondition(short_condition, "Signal Short", "Signal de vente {symbol} {timeframe}")
"""
    
    return pine_script

def main():
    """Fonction principale pour tester la stratégie multitimeframe"""
    print("🎯 STRATÉGIE MULTITIMEFRAME XAUUSD + GER40.cash")
    print("=" * 60)
    print("📈 Optimisée pour Pine Script v6")
    print("=" * 60)
    
    # Timeframes disponibles
    timeframes = ['M15', 'M30', 'H1', 'H4', 'D1']
    symbols = ['XAUUSD', 'GER40.cash']
    
    print(f"\n📊 TIMEFRAMES SUPPORTÉS: {', '.join(timeframes)}")
    print(f"🎯 SYMBOLES SUPPORTÉS: {', '.join(symbols)}")
    
    print("\n💡 UTILISATION:")
    print("1. Chargez vos données dans un DataFrame pandas")
    print("2. Appelez strategie_multitimeframe(df, 'XAUUSD', 'H1')")
    print("3. Appelez strategie_multitimeframe(df, 'GER40.cash', 'H4')")
    print("4. Analysez les résultats avec calculate_metrics(trades)")
    print("5. Générez le Pine Script avec generate_pine_script_template()")
    
    print("\n📊 EXEMPLE DE CODE:")
    print("""
# Test sur tous les timeframes
timeframes = ['M15', 'M30', 'H1', 'H4', 'D1']
symbols = ['XAUUSD', 'GER40.cash']

all_results = {}
for symbol in symbols:
    for tf in timeframes:
        # Chargez vos données
        df = pd.read_csv(f'{symbol}_{tf}_data.csv')
        
        # Appliquez la stratégie
        trades = strategie_multitimeframe(df, symbol, tf)
        metrics = calculate_metrics(trades)
        
        all_results[f'{symbol}_{tf}'] = {
            'trades': trades,
            'metrics': metrics
        }
        
        print(f"{symbol} {tf}: {metrics['Win_Rate']:.1f}% win rate, {metrics['Total_PnL']:.2%} PnL")

# Générer Pine Script
pine_script = generate_pine_script_template('XAUUSD', 'H1')
with open('XAUUSD_H1_strategy.pine', 'w') as f:
    f.write(pine_script)
""")
    
    print("\n🎯 PARAMÈTRES OPTIMISÉS PAR TIMEFRAME:")
    for tf in timeframes:
        params = get_timeframe_params(tf)
        print(f"\n{tf}:")
        print(f"   - Breakout: {params['breakout_period']} périodes")
        print(f"   - Risk ATR: {params['risk_atr']:.2f}")
        print(f"   - Profit ATR: {params['profit_atr']:.2f}")
        print(f"   - RSI: {params['rsi_oversold']}-{params['rsi_overbought']}")
        print(f"   - ADX: >{params['adx_threshold']}")
    
    print("\n✅ Stratégie multitimeframe prête pour Pine Script v6 !")

if __name__ == "__main__":
    main() 