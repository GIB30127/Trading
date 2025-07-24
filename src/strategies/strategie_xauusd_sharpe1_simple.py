import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from rich import print
import warnings
warnings.filterwarnings('ignore')

def compute_atr(df, window):
    """Calcule l'Average True Range (ATR)"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_rsi(df, window=14):
    """Calcule le Relative Strength Index (RSI)"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategie_xauusd_sharpe1_simple(df, symbol, timeframe):
    """
    Stratégie XAUUSD D1 Sharpe 1 Simple avec Trailing Stop
    Basée sur le script Pine Script fourni
    """
    
    df = df.copy()
    
    # === PARAMÈTRES === (adaptés du Pine Script)
    breakout_period = 2
    profit_atr = 2.5
    rsi_overbought = 85
    rsi_oversold = 15
    ema_short = 4
    ema_long = 12
    atr_period = 8
    trail_atr = 0.5  # trailing stop en ATR
    
    # Ajustement selon le timeframe
    if timeframe == 'D1':
        breakout_period = int(breakout_period * 1.5)
        profit_atr *= 1.2
        trail_atr *= 1.2
    elif timeframe == 'H1':
        breakout_period = int(breakout_period * 0.8)
        profit_atr *= 0.8
        trail_atr *= 0.8
    elif timeframe == 'H4':
        breakout_period = int(breakout_period * 1.2)
        profit_atr *= 1.1
        trail_atr *= 1.1
    
    # === INDICATEURS ===
    df['ATR'] = compute_atr(df, atr_period)
    df['RSI'] = compute_rsi(df, 8)
    df['EMA_Short'] = df['Close'].ewm(span=ema_short).mean()
    df['EMA_Long'] = df['Close'].ewm(span=ema_long).mean()
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # === FILTRES ===
    df['Uptrend'] = (df['EMA_Short'] > df['EMA_Long']) & (df['Close'] > df['EMA_Short'])
    df['Downtrend'] = (df['EMA_Short'] < df['EMA_Long']) & (df['Close'] < df['EMA_Short'])
    
    # Volatilité
    df['ATR_MA'] = df['ATR'].rolling(window=15).mean()
    df['Volatility_OK'] = df['ATR'] > df['ATR_MA'] * 0.3
    
    # Momentum
    df['Momentum_Up'] = df['Close'] > df['Close'].shift(1)
    df['Momentum_Down'] = df['Close'] < df['Close'].shift(1)
    
    # Volume
    df['Volume_MA'] = df['Volume'].rolling(window=10).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.5
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trailing_stop = 0
    trades = []

    for i in range(1, len(df)):
        current_price = df.loc[i, 'Close']
        current_atr = df.loc[i, 'ATR']
        
        # === CONDITIONS LONG ===
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        rsi_ok_long = (df.loc[i, 'RSI'] < rsi_overbought and df.loc[i, 'RSI'] > 20)
        
        simple_long_condition = (breakout_up and 
                               df.loc[i, 'Uptrend'] and 
                               df.loc[i, 'Volatility_OK'] and 
                               df.loc[i, 'Momentum_Up'] and 
                               rsi_ok_long and 
                               df.loc[i, 'Volume_OK'])
        
        # === CONDITIONS SHORT ===
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        rsi_ok_short = (df.loc[i, 'RSI'] > rsi_oversold and df.loc[i, 'RSI'] < 80)
        
        simple_short_condition = (breakout_down and 
                                df.loc[i, 'Downtrend'] and 
                                df.loc[i, 'Volatility_OK'] and 
                                df.loc[i, 'Momentum_Down'] and 
                                rsi_ok_short and 
                                df.loc[i, 'Volume_OK'])
        
        # === GESTION DES POSITIONS ===
        
        # Entrée en position LONG
        if position == 0 and simple_long_condition:
            position = 1
            entry_price = current_price
            profit_target = entry_price + profit_atr * current_atr
            trailing_stop = entry_price - trail_atr * current_atr
            stop_loss = trailing_stop
            
            trades.append({
                'entry_date': df.loc[i, 'Date'],
                'entry_price': entry_price,
                'position': 'LONG',
                'stop_loss': stop_loss,
                'profit_target': profit_target,
                'trailing_stop': trailing_stop
            })
        
        # Entrée en position SHORT
        elif position == 0 and simple_short_condition:
            position = -1
            entry_price = current_price
            profit_target = entry_price - profit_atr * current_atr
            trailing_stop = entry_price + trail_atr * current_atr
            stop_loss = trailing_stop
            
            trades.append({
                'entry_date': df.loc[i, 'Date'],
                'entry_price': entry_price,
                'position': 'SHORT',
                'stop_loss': stop_loss,
                'profit_target': profit_target,
                'trailing_stop': trailing_stop
            })
        
        # Gestion des positions ouvertes
        elif position != 0:
            # Mise à jour du trailing stop
            if position == 1:  # LONG
                new_trailing_stop = current_price - trail_atr * current_atr
                if new_trailing_stop > trailing_stop:
                    trailing_stop = new_trailing_stop
                    stop_loss = trailing_stop
                
                # Vérification des conditions de sortie
                if (current_price <= stop_loss or 
                    current_price >= profit_target or
                    simple_short_condition):  # Signal opposé
                    
                    exit_price = current_price
                    if current_price <= stop_loss:
                        exit_price = stop_loss
                    elif current_price >= profit_target:
                        exit_price = profit_target
                    
                    # Calcul du P&L
                    pnl = (exit_price - entry_price) / entry_price * 100
                    if position == -1:  # SHORT
                        pnl = -pnl
                    
                    trades[-1].update({
                        'exit_date': df.loc[i, 'Date'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'exit_reason': 'Stop Loss' if current_price <= stop_loss else 
                                      'Profit Target' if current_price >= profit_target else 'Signal Opposé'
                    })
                    
                    position = 0
                    entry_price = 0
                    stop_loss = 0
                    profit_target = 0
                    trailing_stop = 0
            
            elif position == -1:  # SHORT
                new_trailing_stop = current_price + trail_atr * current_atr
                if new_trailing_stop < trailing_stop:
                    trailing_stop = new_trailing_stop
                    stop_loss = trailing_stop
                
                # Vérification des conditions de sortie
                if (current_price >= stop_loss or 
                    current_price <= profit_target or
                    simple_long_condition):  # Signal opposé
                    
                    exit_price = current_price
                    if current_price >= stop_loss:
                        exit_price = stop_loss
                    elif current_price <= profit_target:
                        exit_price = profit_target
                    
                    # Calcul du P&L
                    pnl = (entry_price - exit_price) / entry_price * 100
                    
                    trades[-1].update({
                        'exit_date': df.loc[i, 'Date'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'exit_reason': 'Stop Loss' if current_price >= stop_loss else 
                                      'Profit Target' if current_price <= profit_target else 'Signal Opposé'
                    })
                    
                    position = 0
                    entry_price = 0
                    stop_loss = 0
                    profit_target = 0
                    trailing_stop = 0
    
    # Fermeture de la dernière position si elle est encore ouverte
    if position != 0 and len(trades) > 0:
        last_trade = trades[-1]
        if 'exit_date' not in last_trade:
            exit_price = df.iloc[-1]['Close']
            pnl = (exit_price - last_trade['entry_price']) / last_trade['entry_price'] * 100
            if position == -1:  # SHORT
                pnl = -pnl
            
            last_trade.update({
                'exit_date': df.iloc[-1]['Date'],
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': 'Fin de période'
            })
    
    return trades, df

def calculate_metrics(trades):
    """Calcule les métriques de performance de la stratégie"""
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_return': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }
    
    df_trades = pd.DataFrame(trades)
    
    # Filtrage des trades complets
    complete_trades = df_trades[df_trades['exit_date'].notna()].copy()
    
    if len(complete_trades) == 0:
        return {
            'total_trades': len(trades),
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_return': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0
        }
    
    # Calculs de base
    total_trades = len(complete_trades)
    winning_trades = len(complete_trades[complete_trades['pnl'] > 0])
    losing_trades = len(complete_trades[complete_trades['pnl'] < 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    # Retours
    total_return = complete_trades['pnl'].sum()
    avg_win = complete_trades[complete_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
    avg_loss = complete_trades[complete_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
    
    # Profit Factor
    gross_profit = complete_trades[complete_trades['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(complete_trades[complete_trades['pnl'] < 0]['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Drawdown
    cumulative_returns = complete_trades['pnl'].cumsum()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max * 100
    max_drawdown = abs(drawdown.min())
    
    # Sharpe Ratio (simplifié)
    returns_std = complete_trades['pnl'].std()
    sharpe_ratio = total_return / returns_std if returns_std > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'total_return': total_return,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio
    }

def main():
    """Fonction principale pour tester la stratégie"""
    print("[bold blue]=== Stratégie XAUUSD D1 Sharpe 1 Simple ===[/bold blue]")
    
    # Test avec un fichier CSV existant
    csv_path = "data/raw/XAUUSD_D1_mt5.csv"
    
    if os.path.exists(csv_path):
        print(f"[green]Chargement des données depuis: {csv_path}[/green]")
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Application de la stratégie
        trades, df_with_signals = strategie_xauusd_sharpe1_simple(df, 'XAUUSD', 'D1')
        
        # Calcul des métriques
        metrics = calculate_metrics(trades)
        
        print(f"\n[bold]Résultats de la stratégie:[/bold]")
        print(f"Total trades: {metrics['total_trades']}")
        print(f"Trades gagnants: {metrics['winning_trades']}")
        print(f"Trades perdants: {metrics['losing_trades']}")
        print(f"Taux de réussite: {metrics['win_rate']:.2f}%")
        print(f"Retour total: {metrics['total_return']:.2f}%")
        print(f"Gain moyen: {metrics['avg_win']:.2f}%")
        print(f"Perte moyenne: {metrics['avg_loss']:.2f}%")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"Drawdown max: {metrics['max_drawdown']:.2f}%")
        print(f"Ratio de Sharpe: {metrics['sharpe_ratio']:.2f}")
        
        # Affichage des derniers trades
        if trades:
            print(f"\n[bold]Derniers trades:[/bold]")
            for i, trade in enumerate(trades[-5:], 1):
                print(f"Trade {i}: {trade['position']} - Entrée: {trade['entry_price']:.2f} - Sortie: {trade.get('exit_price', 'En cours'):.2f} - P&L: {trade.get('pnl', 0):.2f}%")
    
    else:
        print(f"[red]Fichier non trouvé: {csv_path}[/red]")
        print("Veuillez placer un fichier CSV dans le dossier data/raw/")

if __name__ == "__main__":
    main() 