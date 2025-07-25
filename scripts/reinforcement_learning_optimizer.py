#!/usr/bin/env python3
"""
Reinforcement Learning pour l'Optimisation de Stratégie
Utilise Q-Learning pour optimiser les paramètres de trading
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import random
import warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour importer les modules
sys.path.append('src/strategies')
from strategie_xauusd_sharpe1_simple import calculate_metrics

class RLOptimizer:
    def __init__(self, symbol="XAUUSD", timeframe="D1", learning_rate=0.1, discount_factor=0.95, epsilon=0.1):
        self.symbol = symbol
        self.timeframe = timeframe
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        
        # Chargement des données
        self.df = self.load_data()
        
        # États et actions
        self.states = self.create_states()
        self.actions = self.create_actions()
        
        # Q-Table
        self.q_table = {}
        self.initialize_q_table()
        
        # Historique
        self.history = []
        self.best_params = None
        self.best_reward = float('-inf')
    
    def load_data(self):
        """Charge les données"""
        csv_path = f"data/raw/{self.symbol}_{self.timeframe}_mt5.csv"
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Fichier non trouvé: {csv_path}")
        
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def create_states(self):
        """Crée les états possibles"""
        # États basés sur les conditions de marché
        states = []
        
        # États de tendance
        trend_states = ['strong_uptrend', 'weak_uptrend', 'sideways', 'weak_downtrend', 'strong_downtrend']
        
        # États de volatilité
        volatility_states = ['low_vol', 'medium_vol', 'high_vol']
        
        # États de momentum
        momentum_states = ['oversold', 'neutral', 'overbought']
        
        # Combinaisons d'états
        for trend in trend_states:
            for vol in volatility_states:
                for mom in momentum_states:
                    states.append(f"{trend}_{vol}_{mom}")
        
        return states
    
    def create_actions(self):
        """Crée les actions possibles (paramètres)"""
        actions = []
        
        # Paramètres discrets
        breakout_periods = [1, 2, 3, 4, 5]
        profit_atrs = [1.5, 2.0, 2.5, 3.0, 3.5]
        rsi_overboughts = [75, 80, 85, 90]
        rsi_oversolds = [10, 15, 20, 25]
        ema_shorts = [3, 4, 5, 6, 7]
        ema_longs = [8, 10, 12, 15, 18]
        atr_periods = [5, 8, 10, 12, 15]
        trail_atrs = [0.5, 0.8, 1.0, 1.5]
        stop_loss_atrs = [1.5, 2.0, 2.5, 3.0]
        max_positions = [1, 2, 3]
        
        # Création des actions
        for bp in breakout_periods:
            for pa in profit_atrs:
                for ro in rsi_overboughts:
                    for ros in rsi_oversolds:
                        for es in ema_shorts:
                            for el in ema_longs:
                                for ap in atr_periods:
                                    for ta in trail_atrs:
                                        for sla in stop_loss_atrs:
                                            for mp in max_positions:
                                                action = {
                                                    'breakout_period': bp,
                                                    'profit_atr': pa,
                                                    'rsi_overbought': ro,
                                                    'rsi_oversold': ros,
                                                    'ema_short': es,
                                                    'ema_long': el,
                                                    'atr_period': ap,
                                                    'trail_atr': ta,
                                                    'stop_loss_atr': sla,
                                                    'max_positions': mp
                                                }
                                                actions.append(action)
        
        return actions
    
    def initialize_q_table(self):
        """Initialise la Q-table"""
        for state in self.states:
            self.q_table[state] = {}
            for action_idx in range(len(self.actions)):
                self.q_table[state][action_idx] = 0.0
    
    def get_current_state(self, df, current_idx):
        """Détermine l'état actuel du marché"""
        if current_idx < 20:  # Pas assez de données
            return 'sideways_medium_vol_neutral'
        
        # Calcul des indicateurs
        close_prices = df['Close'].iloc[current_idx-20:current_idx+1]
        high_prices = df['High'].iloc[current_idx-20:current_idx+1]
        low_prices = df['Low'].iloc[current_idx-20:current_idx+1]
        
        # Tendance
        ema_short = close_prices.ewm(span=5).mean().iloc[-1]
        ema_long = close_prices.ewm(span=15).mean().iloc[-1]
        current_price = close_prices.iloc[-1]
        
        if ema_short > ema_long * 1.02 and current_price > ema_short:
            trend = 'strong_uptrend'
        elif ema_short > ema_long and current_price > ema_short:
            trend = 'weak_uptrend'
        elif ema_short < ema_long * 0.98 and current_price < ema_short:
            trend = 'strong_downtrend'
        elif ema_short < ema_long and current_price < ema_short:
            trend = 'weak_downtrend'
        else:
            trend = 'sideways'
        
        # Volatilité
        atr = self.calculate_atr_simple(high_prices, low_prices, close_prices, 10)
        avg_atr = atr.mean()
        current_atr = atr.iloc[-1]
        
        if current_atr > avg_atr * 1.5:
            volatility = 'high_vol'
        elif current_atr < avg_atr * 0.7:
            volatility = 'low_vol'
        else:
            volatility = 'medium_vol'
        
        # Momentum (RSI simplifié)
        rsi = self.calculate_rsi_simple(close_prices, 14)
        current_rsi = rsi.iloc[-1]
        
        if current_rsi > 70:
            momentum = 'overbought'
        elif current_rsi < 30:
            momentum = 'oversold'
        else:
            momentum = 'neutral'
        
        return f"{trend}_{volatility}_{momentum}"
    
    def calculate_atr_simple(self, high, low, close, period):
        """Calcule l'ATR de manière simplifiée"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_rsi_simple(self, prices, period):
        """Calcule le RSI de manière simplifiée"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def choose_action(self, state):
        """Choisit une action selon la politique epsilon-greedy"""
        if random.random() < self.epsilon:
            # Exploration
            return random.randint(0, len(self.actions) - 1)
        else:
            # Exploitation
            if state in self.q_table:
                q_values = self.q_table[state]
                return max(q_values, key=q_values.get)
            else:
                return random.randint(0, len(self.actions) - 1)
    
    def get_reward(self, trades):
        """Calcule la récompense basée sur les trades"""
        if len(trades) < 5:
            return -100  # Pénalité pour peu de trades
        
        metrics = calculate_metrics(trades)
        
        # Récompense basée sur plusieurs critères
        reward = 0
        
        # Récompense pour le retour
        reward += metrics['total_return'] * 0.1
        
        # Récompense pour le win rate
        if metrics['win_rate'] > 50:
            reward += (metrics['win_rate'] - 50) * 0.5
        
        # Récompense pour le profit factor
        if metrics['profit_factor'] > 1.5:
            reward += (metrics['profit_factor'] - 1.5) * 10
        
        # Pénalité forte pour le drawdown
        if metrics['max_drawdown'] > 30:
            reward -= (metrics['max_drawdown'] - 30) * 5
        elif metrics['max_drawdown'] < 20:
            reward += (20 - metrics['max_drawdown']) * 2
        
        # Récompense pour le Sharpe ratio
        if metrics['sharpe_ratio'] > 1:
            reward += metrics['sharpe_ratio'] * 0.5
        
        return reward
    
    def apply_strategy_with_params(self, params):
        """Applique la stratégie avec les paramètres donnés"""
        # Version simplifiée de la stratégie pour RL
        return self.strategie_rl(self.df, params)
    
    def strategie_rl(self, df, params):
        """Version simplifiée de la stratégie pour RL"""
        df = df.copy()
        
        # Paramètres
        breakout_period = params['breakout_period']
        profit_atr = params['profit_atr']
        rsi_overbought = params['rsi_overbought']
        rsi_oversold = params['rsi_oversold']
        ema_short = params['ema_short']
        ema_long = params['ema_long']
        atr_period = params['atr_period']
        trail_atr = params['trail_atr']
        stop_loss_atr = params['stop_loss_atr']
        max_positions = params['max_positions']
        
        # Calcul des indicateurs
        df['ATR'] = self.calculate_atr_simple(df['High'], df['Low'], df['Close'], atr_period)
        df['RSI'] = self.calculate_rsi_simple(df['Close'], 8)
        df['EMA_Short'] = df['Close'].ewm(span=ema_short).mean()
        df['EMA_Long'] = df['Close'].ewm(span=ema_long).mean()
        df['High_Break'] = df['High'].rolling(window=breakout_period).max()
        df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
        
        # Signaux
        df['Long_Signal'] = (
            (df['High'].shift(1) < df['High_Break'].shift(1)) & 
            (df['High'] >= df['High_Break']) &
            (df['EMA_Short'] > df['EMA_Long']) &
            (df['Close'] > df['EMA_Short']) &
            (df['RSI'] < rsi_overbought) &
            (df['RSI'] > 20)
        )
        
        df['Short_Signal'] = (
            (df['Low'].shift(1) > df['Low_Break'].shift(1)) & 
            (df['Low'] <= df['Low_Break']) &
            (df['EMA_Short'] < df['EMA_Long']) &
            (df['Close'] < df['EMA_Short']) &
            (df['RSI'] > rsi_oversold) &
            (df['RSI'] < 80)
        )
        
        # Simulation des trades
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        positions_count = 0
        
        for i in range(len(df)):
            if i < 50:  # Skip les premières bougies
                continue
                
            current_price = df['Close'].iloc[i]
            current_date = df['Date'].iloc[i]
            current_atr = df['ATR'].iloc[i]
            
            # Gestion des positions existantes
            if position != 0:
                # Stop loss
                if position == 1:
                    stop_loss = entry_price - (stop_loss_atr * current_atr)
                    take_profit = entry_price + (profit_atr * current_atr)
                    
                    if current_price <= stop_loss:
                        pnl = (stop_loss - entry_price) / entry_price * 100
                        trades.append({
                            'Entry_Date': entry_date,
                            'Exit_Date': current_date,
                            'Entry_Price': entry_price,
                            'Exit_Price': stop_loss,
                            'Position': 'Long',
                            'PnL': pnl,
                            'Exit_Reason': 'Stop_Loss'
                        })
                        position = 0
                        positions_count -= 1
                        continue
                    
                    if current_price >= take_profit:
                        pnl = (take_profit - entry_price) / entry_price * 100
                        trades.append({
                            'Entry_Date': entry_date,
                            'Exit_Date': current_date,
                            'Entry_Price': entry_price,
                            'Exit_Price': take_profit,
                            'Position': 'Long',
                            'PnL': pnl,
                            'Exit_Reason': 'Take_Profit'
                        })
                        position = 0
                        positions_count -= 1
                        continue
                
                else:  # Short position
                    stop_loss = entry_price + (stop_loss_atr * current_atr)
                    take_profit = entry_price - (profit_atr * current_atr)
                    
                    if current_price >= stop_loss:
                        pnl = (entry_price - stop_loss) / entry_price * 100
                        trades.append({
                            'Entry_Date': entry_date,
                            'Exit_Date': current_date,
                            'Entry_Price': entry_price,
                            'Exit_Price': stop_loss,
                            'Position': 'Short',
                            'PnL': pnl,
                            'Exit_Reason': 'Stop_Loss'
                        })
                        position = 0
                        positions_count -= 1
                        continue
                    
                    if current_price <= take_profit:
                        pnl = (entry_price - take_profit) / entry_price * 100
                        trades.append({
                            'Entry_Date': entry_date,
                            'Exit_Date': current_date,
                            'Entry_Price': entry_price,
                            'Exit_Price': take_profit,
                            'Position': 'Short',
                            'PnL': pnl,
                            'Exit_Reason': 'Take_Profit'
                        })
                        position = 0
                        positions_count -= 1
                        continue
            
            # Nouvelles entrées
            if position == 0 and positions_count < max_positions:
                if df['Long_Signal'].iloc[i]:
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    positions_count += 1
                
                elif df['Short_Signal'].iloc[i]:
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    positions_count += 1
        
        return trades
    
    def train(self, episodes=1000):
        """Entraîne l'agent RL"""
        print(f"🤖 ENTRAÎNEMENT RL - {self.symbol} {self.timeframe}")
        print(f"Épisodes: {episodes}")
        print("=" * 50)
        
        for episode in range(episodes):
            if episode % 100 == 0:
                print(f"🔄 Épisode {episode}/{episodes}")
            
            # Choisir une action aléatoire pour cet épisode
            action_idx = random.randint(0, len(self.actions) - 1)
            action = self.actions[action_idx]
            
            # Appliquer la stratégie
            trades = self.apply_strategy_with_params(action)
            
            # Calculer la récompense
            reward = self.get_reward(trades)
            
            # Mettre à jour la Q-table pour tous les états
            for state in self.states:
                if state not in self.q_table:
                    self.q_table[state] = {}
                
                if action_idx not in self.q_table[state]:
                    self.q_table[state][action_idx] = 0.0
                
                # Q-Learning update
                current_q = self.q_table[state][action_idx]
                max_future_q = max(self.q_table[state].values()) if self.q_table[state] else 0
                
                new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
                self.q_table[state][action_idx] = new_q
            
            # Stocker l'historique
            if len(trades) > 0:
                metrics = calculate_metrics(trades)
                self.history.append({
                    'episode': episode,
                    'action_idx': action_idx,
                    'reward': reward,
                    'trades_count': len(trades),
                    'total_return': metrics.get('total_return', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'profit_factor': metrics.get('profit_factor', 0)
                })
                
                # Mise à jour du meilleur
                if reward > self.best_reward:
                    self.best_reward = reward
                    self.best_params = action.copy()
        
        # Sauvegarder les résultats
        self.save_results()
        
        return self.best_params
    
    def save_results(self):
        """Sauvegarde les résultats de l'entraînement"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"results/optimization/rl_optimization_{self.symbol}_{self.timeframe}_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # Sauvegarde des paramètres optimaux
        if self.best_params:
            with open(f"{results_dir}/parametres_optimaux_rl.md", 'w', encoding='utf-8') as f:
                f.write(f"# Paramètres Optimaux RL - {self.symbol} {self.timeframe}\n\n")
                f.write(f"**Date d'optimisation**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Paramètres Optimaux\n\n")
                
                for param, value in self.best_params.items():
                    f.write(f"- **{param}**: {value}\n")
                
                f.write(f"\n## Meilleure Récompense\n\n")
                f.write(f"- **Reward**: {self.best_reward:.2f}\n")
            
            # Sauvegarde de l'historique
            history_df = pd.DataFrame(self.history)
            history_df.to_csv(f"{results_dir}/historique_rl.csv", index=False)
            
            print(f"\n✅ Résultats RL sauvegardés: {results_dir}")

def main():
    """Fonction principale"""
    print("🤖 OPTIMISATION PAR REINFORCEMENT LEARNING")
    print("=" * 60)
    
    # Test sur H4 (meilleur drawdown)
    timeframe = 'H4'
    
    try:
        rl_optimizer = RLOptimizer(
            symbol="XAUUSD",
            timeframe=timeframe,
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon=0.2
        )
        
        best_params = rl_optimizer.train(episodes=500)
        
        if best_params:
            print(f"\n✅ Entraînement RL terminé!")
            print(f"📊 Meilleure récompense: {rl_optimizer.best_reward:.2f}")
            print(f"🎯 Paramètres optimaux trouvés")
    
    except Exception as e:
        print(f"❌ Erreur RL: {e}")

if __name__ == "__main__":
    main() 