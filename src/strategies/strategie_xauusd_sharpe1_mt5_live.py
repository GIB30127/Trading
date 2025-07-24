import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

class XAUUSDSharpe1LiveStrategy:
    """
    Stratégie XAUUSD D1 Sharpe 1 Simple adaptée pour le trading en temps réel
    """
    
    def __init__(self, symbol="XAUUSD", timeframe="D1"):
        self.symbol = symbol
        self.timeframe = timeframe
        
        # Paramètres de la stratégie
        self.breakout_period = 2
        self.profit_atr = 2.5
        self.rsi_overbought = 85
        self.rsi_oversold = 15
        self.ema_short = 4
        self.ema_long = 12
        self.atr_period = 8
        self.trail_atr = 0.5
        
        # Ajustement selon le timeframe
        if timeframe == 'D1':
            self.breakout_period = int(self.breakout_period * 1.5)
            self.profit_atr *= 1.2
            self.trail_atr *= 1.2
        elif timeframe == 'H1':
            self.breakout_period = int(self.breakout_period * 0.8)
            self.profit_atr *= 0.8
            self.trail_atr *= 0.8
        elif timeframe == 'H4':
            self.breakout_period = int(self.breakout_period * 1.2)
            self.profit_atr *= 1.1
            self.trail_atr *= 1.1
        
        # État de la stratégie
        self.position = 0  # 0: pas de position, 1: long, -1: short
        self.entry_price = 0
        self.stop_loss = 0
        self.profit_target = 0
        self.trailing_stop = 0
        self.trades_history = []
        
        print(f"[green]Stratégie initialisée pour {symbol} {timeframe}[/green]")
        print(f"Paramètres: Breakout={self.breakout_period}, Profit ATR={self.profit_atr}, Trail ATR={self.trail_atr}")
    
    def calculate_indicators(self, df):
        """Calcule tous les indicateurs nécessaires"""
        df = df.copy()
        
        # Indicateurs de base
        df['ATR'] = compute_atr(df, self.atr_period)
        df['RSI'] = compute_rsi(df, 8)
        df['EMA_Short'] = df['Close'].ewm(span=self.ema_short).mean()
        df['EMA_Long'] = df['Close'].ewm(span=self.ema_long).mean()
        df['High_Break'] = df['High'].rolling(window=self.breakout_period).max()
        df['Low_Break'] = df['Low'].rolling(window=self.breakout_period).min()
        
        # Filtres
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
        
        return df
    
    def check_entry_signals(self, df, current_index):
        """Vérifie les signaux d'entrée"""
        if current_index < 1:
            return None, None
        
        current_price = df.loc[current_index, 'Close']
        current_atr = df.loc[current_index, 'ATR']
        
        # Conditions LONG
        breakout_up = (df.loc[current_index-1, 'High'] < df.loc[current_index-1, 'High_Break'] and 
                      df.loc[current_index, 'High'] >= df.loc[current_index, 'High_Break'])
        rsi_ok_long = (df.loc[current_index, 'RSI'] < self.rsi_overbought and df.loc[current_index, 'RSI'] > 20)
        
        long_condition = (breakout_up and 
                         df.loc[current_index, 'Uptrend'] and 
                         df.loc[current_index, 'Volatility_OK'] and 
                         df.loc[current_index, 'Momentum_Up'] and 
                         rsi_ok_long and 
                         df.loc[current_index, 'Volume_OK'])
        
        # Conditions SHORT
        breakout_down = (df.loc[current_index-1, 'Low'] > df.loc[current_index-1, 'Low_Break'] and 
                        df.loc[current_index, 'Low'] <= df.loc[current_index, 'Low_Break'])
        rsi_ok_short = (df.loc[current_index, 'RSI'] > self.rsi_oversold and df.loc[current_index, 'RSI'] < 80)
        
        short_condition = (breakout_down and 
                          df.loc[current_index, 'Downtrend'] and 
                          df.loc[current_index, 'Volatility_OK'] and 
                          df.loc[current_index, 'Momentum_Down'] and 
                          rsi_ok_short and 
                          df.loc[current_index, 'Volume_OK'])
        
        return long_condition, short_condition
    
    def enter_position(self, position_type, entry_price, atr, entry_date):
        """Entre en position"""
        if position_type == "LONG":
            self.position = 1
            self.entry_price = entry_price
            self.profit_target = entry_price + self.profit_atr * atr
            self.trailing_stop = entry_price - self.trail_atr * atr
            self.stop_loss = self.trailing_stop
            
            trade = {
                'entry_date': entry_date,
                'entry_price': entry_price,
                'position': 'LONG',
                'stop_loss': self.stop_loss,
                'profit_target': self.profit_target,
                'trailing_stop': self.trailing_stop
            }
            
        elif position_type == "SHORT":
            self.position = -1
            self.entry_price = entry_price
            self.profit_target = entry_price - self.profit_atr * atr
            self.trailing_stop = entry_price + self.trail_atr * atr
            self.stop_loss = self.trailing_stop
            
            trade = {
                'entry_date': entry_date,
                'entry_price': entry_price,
                'position': 'SHORT',
                'stop_loss': self.stop_loss,
                'profit_target': self.profit_target,
                'trailing_stop': self.trailing_stop
            }
        
        self.trades_history.append(trade)
        print(f"[green]🎯 Position {position_type} ouverte à {entry_price:.2f}[/green]")
        print(f"   Stop Loss: {self.stop_loss:.2f}")
        print(f"   Profit Target: {self.profit_target:.2f}")
        print(f"   Trailing Stop: {self.trailing_stop:.2f}")
        
        return trade
    
    def update_trailing_stop(self, current_price, current_atr):
        """Met à jour le trailing stop"""
        if self.position == 1:  # LONG
            new_trailing_stop = current_price - self.trail_atr * current_atr
            if new_trailing_stop > self.trailing_stop:
                self.trailing_stop = new_trailing_stop
                self.stop_loss = self.trailing_stop
                print(f"[blue]📈 Trailing stop mis à jour: {self.trailing_stop:.2f}[/blue]")
        
        elif self.position == -1:  # SHORT
            new_trailing_stop = current_price + self.trail_atr * current_atr
            if new_trailing_stop < self.trailing_stop:
                self.trailing_stop = new_trailing_stop
                self.stop_loss = self.trailing_stop
                print(f"[blue]📉 Trailing stop mis à jour: {self.trailing_stop:.2f}[/blue]")
    
    def check_exit_conditions(self, current_price, long_signal, short_signal):
        """Vérifie les conditions de sortie"""
        if self.position == 0:
            return None, None
        
        exit_reason = None
        exit_price = current_price
        
        if self.position == 1:  # LONG
            if current_price <= self.stop_loss:
                exit_price = self.stop_loss
                exit_reason = "Stop Loss"
            elif current_price >= self.profit_target:
                exit_price = self.profit_target
                exit_reason = "Profit Target"
            elif short_signal:
                exit_reason = "Signal Opposé"
        
        elif self.position == -1:  # SHORT
            if current_price >= self.stop_loss:
                exit_price = self.stop_loss
                exit_reason = "Stop Loss"
            elif current_price <= self.profit_target:
                exit_price = self.profit_target
                exit_reason = "Profit Target"
            elif long_signal:
                exit_reason = "Signal Opposé"
        
        return exit_reason, exit_price
    
    def exit_position(self, exit_reason, exit_price, exit_date):
        """Sort de position"""
        if self.position == 0:
            return None
        
        # Calcul du P&L
        if self.position == 1:  # LONG
            pnl = (exit_price - self.entry_price) / self.entry_price * 100
        else:  # SHORT
            pnl = (self.entry_price - exit_price) / self.entry_price * 100
        
        # Mise à jour du trade
        current_trade = self.trades_history[-1]
        current_trade.update({
            'exit_date': exit_date,
            'exit_price': exit_price,
            'pnl': pnl,
            'exit_reason': exit_reason
        })
        
        # Réinitialisation de la position
        old_position = "LONG" if self.position == 1 else "SHORT"
        self.position = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.profit_target = 0
        self.trailing_stop = 0
        
        status = "✅" if pnl > 0 else "❌"
        print(f"[yellow]{status} Position {old_position} fermée à {exit_price:.2f}[/yellow]")
        print(f"   P&L: {pnl:.2f}% - Raison: {exit_reason}")
        
        return current_trade
    
    def process_new_data(self, df, current_index):
        """Traite les nouvelles données et prend les décisions de trading"""
        if current_index < 1:
            return None
        
        # Calcul des indicateurs
        df = self.calculate_indicators(df)
        
        # Vérification des signaux d'entrée
        long_signal, short_signal = self.check_entry_signals(df, current_index)
        
        current_price = df.loc[current_index, 'Close']
        current_atr = df.loc[current_index, 'ATR']
        current_date = df.loc[current_index, 'Date']
        
        # Mise à jour du trailing stop si en position
        if self.position != 0:
            self.update_trailing_stop(current_price, current_atr)
        
        # Vérification des conditions de sortie
        exit_result = self.check_exit_conditions(current_price, long_signal, short_signal)
        if exit_result[0] is not None:  # Si exit_reason n'est pas None
            exit_reason, exit_price = exit_result
            return self.exit_position(exit_reason, exit_price, current_date)
        
        # Entrée en position si pas de position actuelle
        if self.position == 0:
            if long_signal:
                return self.enter_position("LONG", current_price, current_atr, current_date)
            elif short_signal:
                return self.enter_position("SHORT", current_price, current_atr, current_date)
        
        return None
    
    def get_current_status(self):
        """Retourne le statut actuel de la stratégie"""
        return {
            'position': self.position,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'profit_target': self.profit_target,
            'trailing_stop': self.trailing_stop,
            'total_trades': len(self.trades_history)
        }
    
    def get_performance_summary(self):
        """Retourne un résumé des performances"""
        if not self.trades_history:
            return None
        
        completed_trades = [trade for trade in self.trades_history if 'exit_date' in trade]
        
        if not completed_trades:
            return None
        
        total_trades = len(completed_trades)
        winning_trades = len([t for t in completed_trades if t['pnl'] > 0])
        losing_trades = len([t for t in completed_trades if t['pnl'] < 0])
        
        total_return = sum(trade['pnl'] for trade in completed_trades)
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_win': np.mean([t['pnl'] for t in completed_trades if t['pnl'] > 0]) if winning_trades > 0 else 0,
            'avg_loss': np.mean([t['pnl'] for t in completed_trades if t['pnl'] < 0]) if losing_trades > 0 else 0
        }

def main():
    """Test de la stratégie en temps réel"""
    print("[bold blue]🤖 Test Stratégie XAUUSD Sharpe 1 Live[/bold blue]")
    
    # Initialisation de la stratégie
    strategy = XAUUSDSharpe1LiveStrategy("XAUUSD", "D1")
    
    # Chargement des données de test
    csv_path = "data/raw/XAUUSD_D1_mt5.csv"
    
    if not os.path.exists(csv_path):
        print(f"[red]Fichier non trouvé: {csv_path}[/red]")
        return
    
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    print(f"[green]Données chargées: {len(df)} bougies[/green]")
    
    # Simulation du trading en temps réel
    for i in range(20, len(df)):  # Commence après les premières bougies pour avoir assez d'historique
        result = strategy.process_new_data(df, i)
        
        if result:
            print(f"📊 Trade exécuté: {result}")
        
        # Affichage du statut tous les 50 bougies
        if i % 50 == 0:
            status = strategy.get_current_status()
            print(f"\n[blue]Statut à la bougie {i}:[/blue]")
            print(f"Position: {status['position']}")
            print(f"Prix d'entrée: {status['entry_price']:.2f}")
            print(f"Stop Loss: {status['stop_loss']:.2f}")
            print(f"Profit Target: {status['profit_target']:.2f}")
    
    # Résumé final
    performance = strategy.get_performance_summary()
    if performance:
        print(f"\n[bold green]=== RÉSUMÉ FINAL ===[/bold green]")
        print(f"Total trades: {performance['total_trades']}")
        print(f"Taux de réussite: {performance['win_rate']:.2f}%")
        print(f"Retour total: {performance['total_return']:.2f}%")
        print(f"Gain moyen: {performance['avg_win']:.2f}%")
        print(f"Perte moyenne: {performance['avg_loss']:.2f}%")

if __name__ == "__main__":
    main() 