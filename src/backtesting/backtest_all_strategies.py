#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de backtest automatisé pour toutes les stratégies Sharpe 1 Optimized
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Configuration des actifs et timeframes
ASSETS = {
    "XAUUSD": "GC=F",      # Or (Gold Futures)
    "GER40.cash": "^GDAXI", # DAX
    "US30.cash": "^DJI",    # Dow Jones
    "EURUSD": "EURUSD=X"    # Euro/Dollar
}

TIMEFRAMES = {
    "M15": "15m",
    "M30": "30m", 
    "H1": "1h",
    "H4": "4h",
    "D1": "1d"
}

class SharpeStrategyBacktest:
    def __init__(self, asset, timeframe, start_date="2020-01-01", end_date="2025-01-01"):
        self.asset = asset
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.trades = []
        self.equity_curve = []
        
    def download_data(self):
        """Télécharge les données pour l'actif et timeframe"""
        try:
            symbol = ASSETS.get(self.asset, self.asset)
            interval = TIMEFRAMES.get(self.timeframe, "1d")
            
            print(f"📥 Téléchargement des données pour {self.asset} {self.timeframe}...")
            
            # Télécharger les données
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=self.start_date, end=self.end_date, interval=interval)
            
            if data.empty:
                print(f"❌ Aucune donnée trouvée pour {self.asset} {self.timeframe}")
                return False
                
            self.data = data
            print(f"✅ {len(data)} bougies téléchargées pour {self.asset} {self.timeframe}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement de {self.asset} {self.timeframe}: {e}")
            return False
    
    def calculate_indicators(self):
        """Calcule les indicateurs de la stratégie"""
        if self.data is None:
            return False
            
        # Paramètres de la stratégie
        breakout_period = 2
        risk_atr = 0.5
        profit_atr = 2.0
        rsi_overbought = 82
        rsi_oversold = 18
        ema_short = 3
        ema_long = 10
        atr_period = 6
        
        # Calcul des indicateurs
        self.data['ATR'] = self.calculate_atr(self.data, atr_period)
        self.data['RSI'] = self.calculate_rsi(self.data['Close'], 6)
        self.data['EMA_short'] = self.data['Close'].ewm(span=ema_short).mean()
        self.data['EMA_long'] = self.data['Close'].ewm(span=ema_long).mean()
        
        # Breakouts
        self.data['High_break'] = self.data['High'].rolling(breakout_period).max()
        self.data['Low_break'] = self.data['Low'].rolling(breakout_period).min()
        
        # Filtres
        self.data['Uptrend'] = (self.data['EMA_short'] > self.data['EMA_long']) & \
                               (self.data['Close'] > self.data['EMA_short']) & \
                               (self.data['EMA_short'] > self.data['EMA_short'].shift(1))
        
        # Volatilité contrôlée
        atr_sma = self.data['ATR'].rolling(12).mean()
        self.data['Volatility_ok'] = (self.data['ATR'] > atr_sma * 0.4) & \
                                    (self.data['ATR'] < atr_sma * 1.8)
        
        # Momentum confirmé
        self.data['Momentum_up'] = (self.data['Close'] > self.data['Close'].shift(1)) & \
                                  (self.data['Close'].shift(1) > self.data['Close'].shift(2))
        
        # Volume confirmé
        volume_sma = self.data['Volume'].rolling(8).mean()
        self.data['Volume_ok'] = self.data['Volume'] > volume_sma * 0.7
        
        # Conditions RSI
        self.data['RSI_ok'] = (self.data['RSI'] < rsi_overbought) & (self.data['RSI'] > 25)
        
        # Breakout signal
        self.data['Breakout_up'] = (self.data['High'].shift(1) < self.data['High_break'].shift(1)) & \
                                  (self.data['High'] >= self.data['High_break'])
        
        # Signal final
        self.data['Signal'] = self.data['Breakout_up'] & self.data['Uptrend'] & \
                             self.data['Volatility_ok'] & self.data['Momentum_up'] & \
                             self.data['RSI_ok'] & self.data['Volume_ok']
        
        return True
    
    def calculate_atr(self, data, period):
        """Calcule l'ATR (Average True Range)"""
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        return atr
    
    def calculate_rsi(self, prices, period):
        """Calcule le RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def run_backtest(self, initial_capital=10000):
        """Exécute le backtest de la stratégie"""
        if self.data is None or 'Signal' not in self.data.columns:
            print("❌ Données ou indicateurs manquants")
            return None
            
        capital = initial_capital
        position = 0
        entry_price = 0
        entry_date = None
        
        self.equity_curve = [initial_capital]
        
        for i in range(1, len(self.data)):
            current_price = self.data['Close'].iloc[i]
            current_date = self.data.index[i]
            
            # Si pas de position et signal d'achat
            if position == 0 and self.data['Signal'].iloc[i]:
                position = 1
                entry_price = current_price
                entry_date = current_date
                
                # Calculer la taille de position (8% du capital)
                position_size = capital * 0.08
                shares = position_size / current_price
                
                # Stop loss et take profit
                atr = self.data['ATR'].iloc[i]
                stop_loss = entry_price - 0.5 * atr
                take_profit = entry_price + 2.0 * atr
                
                self.trades.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'shares': shares,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                })
            
            # Si position ouverte, vérifier sortie
            elif position == 1:
                trade = self.trades[-1]
                
                # Vérifier stop loss ou take profit
                if current_price <= trade['stop_loss'] or current_price >= trade['take_profit']:
                    # Calculer P&L
                    if current_price >= trade['take_profit']:
                        pnl = (trade['take_profit'] - trade['entry_price']) * trade['shares']
                    else:
                        pnl = (trade['stop_loss'] - trade['entry_price']) * trade['shares']
                    
                    capital += pnl
                    trade['exit_date'] = current_date
                    trade['exit_price'] = current_price if current_price >= trade['take_profit'] else trade['stop_loss']
                    trade['pnl'] = pnl
                    trade['pnl_pct'] = (pnl / (trade['entry_price'] * trade['shares'])) * 100
                    
                    position = 0
                    entry_price = 0
                    entry_date = None
            
            self.equity_curve.append(capital)
        
        return self.calculate_metrics(initial_capital)
    
    def calculate_metrics(self, initial_capital):
        """Calcule les métriques de performance"""
        if not self.trades:
            return {
                'asset': self.asset,
                'timeframe': self.timeframe,
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        # Filtrer les trades complets
        completed_trades = [t for t in self.trades if 'exit_date' in t]
        
        if not completed_trades:
            return {
                'asset': self.asset,
                'timeframe': self.timeframe,
                'total_trades': len(self.trades),
                'winning_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        # Calculs de base
        total_trades = len(completed_trades)
        winning_trades = len([t for t in completed_trades if t['pnl'] > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in completed_trades)
        total_return = (total_pnl / initial_capital) * 100
        
        # Calcul du Sharpe Ratio
        returns = [t['pnl_pct'] for t in completed_trades]
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calcul du Max Drawdown
        equity_series = pd.Series(self.equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = abs(drawdown.min())
        
        # Calcul du Profit Factor
        gross_profit = sum(t['pnl'] for t in completed_trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in completed_trades if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'asset': self.asset,
            'timeframe': self.timeframe,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 3)
        }

def main():
    """Fonction principale"""
    print("🚀 Backtest automatisé de toutes les stratégies Sharpe 1 Optimized")
    print("=" * 80)
    
    results = []
    
    # Backtest pour chaque combinaison actif/timeframe
    for asset in ASSETS.keys():
        for timeframe in TIMEFRAMES.keys():
            print(f"\n📊 Backtest de {asset} {timeframe}...")
            
            # Créer et exécuter le backtest
            backtest = SharpeStrategyBacktest(asset, timeframe)
            
            # Télécharger les données
            if not backtest.download_data():
                continue
            
            # Calculer les indicateurs
            if not backtest.calculate_indicators():
                continue
            
            # Exécuter le backtest
            metrics = backtest.run_backtest()
            
            if metrics:
                results.append(metrics)
                print(f"✅ {asset} {timeframe}: Sharpe={metrics['sharpe_ratio']}, Trades={metrics['total_trades']}, WinRate={metrics['win_rate']}%")
            else:
                print(f"❌ Échec du backtest pour {asset} {timeframe}")
    
    # Afficher les résultats
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS DU BACKTEST")
    print("=" * 80)
    
    if results:
        df_results = pd.DataFrame(results)
        
        # Trier par Sharpe Ratio décroissant
        df_results = df_results.sort_values('sharpe_ratio', ascending=False)
        
        print(df_results.to_string(index=False))
        
        # Statistiques globales
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   • Stratégies avec Sharpe > 1: {len(df_results[df_results['sharpe_ratio'] > 1])}")
        print(f"   • Sharpe Ratio moyen: {df_results['sharpe_ratio'].mean():.3f}")
        print(f"   • Sharpe Ratio max: {df_results['sharpe_ratio'].max():.3f}")
        print(f"   • Sharpe Ratio min: {df_results['sharpe_ratio'].min():.3f}")
        
        # Sauvegarder les résultats
        output_file = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_results.to_csv(output_file, index=False)
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")
        
    else:
        print("❌ Aucun résultat de backtest disponible")

if __name__ == "__main__":
    main() 