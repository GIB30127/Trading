import pandas as pd
import numpy as np
import warnings
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

def strategie_xau_ger40(df, symbol, timeframe):
    """
    Stratégie optimisée pour XAUUSD et GER40.cash
    Basée sur les meilleurs résultats : XAUUSD H1 + GER40.cash H4
    """
    
    df = df.copy()
    
    # Paramètres optimisés selon l'instrument
    if symbol == 'XAUUSD':
        # Paramètres pour XAUUSD (Gold)
        breakout_period = 10
        risk_atr = 1.5
        profit_atr = 3.0
        rsi_overbought = 75
        rsi_oversold = 25
        adx_threshold = 20
        ema_short = 20
        ema_long = 50
    elif symbol == 'GER40.cash':
        # Paramètres pour GER40.cash (Indice allemand)
        breakout_period = 12
        risk_atr = 1.2
        profit_atr = 2.5
        rsi_overbought = 70
        rsi_oversold = 30
        adx_threshold = 25
        ema_short = 20
        ema_long = 50
    else:
        # Paramètres par défaut
        breakout_period = 10
        risk_atr = 1.3
        profit_atr = 2.7
        rsi_overbought = 72
        rsi_oversold = 28
        adx_threshold = 22
        ema_short = 20
        ema_long = 50
    
    # Ajustement timeframe
    if timeframe == 'H1':
        breakout_period = int(breakout_period * 0.8)
        risk_atr *= 0.9
        profit_atr *= 0.9
    elif timeframe == 'H4':
        breakout_period = int(breakout_period * 1.2)
        risk_atr *= 1.1
        profit_atr *= 1.1
    elif timeframe == 'D1':
        breakout_period = int(breakout_period * 1.5)
        risk_atr *= 1.3
        profit_atr *= 1.3
    
    # Calcul des indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    df['ADX'] = compute_adx(df, 14)
    df['EMA_Short'] = df['Close'].ewm(span=ema_short).mean()
    df['EMA_Long'] = df['Close'].ewm(span=ema_long).mean()
    
    # Breakouts
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # Volume (si disponible)
    if 'Volume' in df.columns:
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.8
    else:
        df['Volume_OK'] = True  # Si pas de volume, on accepte tous les trades
    
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
        adx_strong = df.loc[i, 'ADX'] > adx_threshold
        
        # Breakouts
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        
        # RSI conditions
        rsi_ok_long = df.loc[i, 'RSI'] < rsi_overbought
        rsi_ok_short = df.loc[i, 'RSI'] > rsi_oversold
        
        # Conditions d'entrée LONG
        long_conditions = (
            breakout_up and 
            ema_trend and 
            volume_ok and 
            adx_strong and
            rsi_ok_long and
            df.loc[i, 'RSI'] > 30  # Pas en survente extrême
        )
        
        # Conditions d'entrée SHORT
        short_conditions = (
            breakout_down and 
            not ema_trend and 
            volume_ok and 
            adx_strong and
            rsi_ok_short and
            df.loc[i, 'RSI'] < 70  # Pas en surachat extrême
        )

        if position == 0:
            # Entrée LONG
            if long_conditions:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                signals_long += 1
                
            # Entrée SHORT
            elif short_conditions:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']
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
                    'Date_Exit': df.index[i]
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
                    'Date_Exit': df.index[i]
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
                    'Date_Exit': df.index[i]
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
                    'Date_Exit': df.index[i]
                })
                position = 0
                trades_executed += 1

    # Statistiques de debug
    print(f"📊 {symbol} {timeframe} - Statistiques:")
    print(f"   Signaux Long: {signals_long}")
    print(f"   Signaux Short: {signals_short}")
    print(f"   Trades exécutés: {trades_executed}")
    print(f"   Trades enregistrés: {len(trades)}")

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

def main():
    """Fonction principale pour tester la stratégie"""
    print("🎯 STRATÉGIE XAUUSD + GER40.cash")
    print("=" * 50)
    print("📈 Logique de trading optimisée")
    print("=" * 50)
    
    # Exemple d'utilisation
    print("\n💡 UTILISATION:")
    print("1. Chargez vos données dans un DataFrame pandas")
    print("2. Appelez strategie_xau_ger40(df, 'XAUUSD', 'H1')")
    print("3. Appelez strategie_xau_ger40(df, 'GER40.cash', 'H4')")
    print("4. Analysez les résultats avec calculate_metrics(trades)")
    
    print("\n📊 EXEMPLE DE CODE:")
    print("""
# Chargement des données
df_xau = pd.read_csv('XAUUSD_H1_data.csv')
df_ger40 = pd.read_csv('GER40_H4_data.csv')

# Application de la stratégie
trades_xau = strategie_xau_ger40(df_xau, 'XAUUSD', 'H1')
trades_ger40 = strategie_xau_ger40(df_ger40, 'GER40.cash', 'H4')

# Calcul des métriques
metrics_xau = calculate_metrics(trades_xau)
metrics_ger40 = calculate_metrics(trades_ger40)

print(f"XAUUSD H1: {metrics_xau['Win_Rate']:.1f}% win rate, {metrics_xau['Total_PnL']:.2%} PnL")
print(f"GER40 H4: {metrics_ger40['Win_Rate']:.1f}% win rate, {metrics_ger40['Total_PnL']:.2%} PnL")
""")
    
    print("\n🎯 PARAMÈTRES OPTIMISÉS:")
    print("XAUUSD H1:")
    print("   - Breakout: 8 périodes")
    print("   - Risk ATR: 1.35")
    print("   - Profit ATR: 2.7")
    print("   - RSI: 25-75")
    print("   - ADX: >20")
    
    print("\nGER40.cash H4:")
    print("   - Breakout: 14 périodes")
    print("   - Risk ATR: 1.32")
    print("   - Profit ATR: 2.75")
    print("   - RSI: 30-70")
    print("   - ADX: >25")
    
    print("\n✅ Stratégie prête à utiliser !")

if __name__ == "__main__":
    main() 