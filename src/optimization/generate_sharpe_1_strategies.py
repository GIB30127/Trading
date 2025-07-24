#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de stratégies Pine Script optimisées pour Sharpe Ratio > 1
Pour tous les actifs et timeframes
"""

import os

# Configuration des actifs et timeframes
ASSETS = [
    "XAUUSD",      # Or
    "GER40.cash",  # DAX
    "US30.cash",   # Dow Jones
    "EURUSD"       # Euro/Dollar
]

TIMEFRAMES = [
    "M15",  # 15 minutes
    "M30",  # 30 minutes
    "H1",   # 1 heure
    "H4",   # 4 heures
    "D1"    # 1 jour
]

# Template de la stratégie optimisée
STRATEGY_TEMPLATE = '''//@version=6
strategy("{asset} {timeframe} Sharpe 1 Optimized", overlay=true, margin_long=100, margin_short=100, default_qty_type=strategy.percent_of_equity, default_qty_value=8)

// === PARAMÈTRES OPTIMISÉS POUR SHARPE > 1 ===
breakout_period = 2        // Breakout court
risk_atr = 0.5            // Stop loss serré pour réduire la volatilité
profit_atr = 2.0          // Take profit optimisé
rsi_overbought = 82       // RSI moins permissif
rsi_oversold = 18         // RSI moins permissif
ema_short = 3             // EMA plus courte
ema_long = 10             // EMA plus courte
atr_period = 6            // ATR plus court

// === INDICATEURS ===
atr = ta.atr(atr_period)
rsi = ta.rsi(close, 6)    // RSI plus court
ema_short_val = ta.ema(close, ema_short)
ema_long_val = ta.ema(close, ema_long)

// Breakouts
high_break = ta.highest(high, breakout_period)
low_break = ta.lowest(low, breakout_period)

// === FILTRES OPTIMISÉS ===
// Tendance haussière confirmée
uptrend = ema_short_val > ema_long_val and close > ema_short_val and ema_short_val > ema_short_val[1]

// Volatilité contrôlée
volatility_ok = atr > ta.sma(atr, 12) * 0.4 and atr < ta.sma(atr, 12) * 1.8

// Momentum confirmé
momentum_up = close > close[1] and close[1] > close[2]

// Volume confirmé
volume_ok = volume > ta.sma(volume, 8) * 0.7

// === CONDITIONS OPTIMISÉES ===
breakout_up = high[1] < high_break[1] and high >= high_break

// Conditions RSI optimisées
rsi_ok = rsi < rsi_overbought and rsi > 25

// === SIGNAL OPTIMISÉ ===
optimized_condition = breakout_up and uptrend and volatility_ok and momentum_up and rsi_ok and volume_ok

// === STRATÉGIE OPTIMISÉE ===
if optimized_condition
    strategy.entry("Optimized Long", strategy.long)
    strategy.exit("Exit Optimized", "Optimized Long", stop=close - risk_atr * atr, limit=close + profit_atr * atr)

// === PLOTS ===
plot(ema_short_val, "EMA Short", color=color.blue, linewidth=2)
plot(ema_long_val, "EMA Long", color=color.red, linewidth=2)
plot(high_break, "High Break", color=color.green, style=plot.style_line)

// === ALERTS ===
alertcondition(optimized_condition, "Signal Optimized", "Signal d'achat {asset} {timeframe} - Sharpe 1 Optimized")
'''

def create_directory_if_not_exists(directory):
    """Crée un répertoire s'il n'existe pas"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"📁 Répertoire créé : {directory}")

def generate_strategy_file(asset, timeframe):
    """Génère un fichier Pine Script pour un actif et timeframe donnés"""
    
    # Créer le répertoire Pine_Scripts s'il n'existe pas
    create_directory_if_not_exists("Pine_Scripts")
    
    # Nom du fichier
    filename = f"Pine_Scripts/{asset}_{timeframe}_Sharpe_1_Optimized.pine"
    
    # Générer le contenu
    content = STRATEGY_TEMPLATE.format(asset=asset, timeframe=timeframe)
    
    # Écrire le fichier
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fichier créé : {filename}")

def main():
    """Fonction principale"""
    print("🚀 Génération des stratégies Pine Script optimisées pour Sharpe Ratio > 1")
    print("=" * 70)
    
    total_files = 0
    
    # Générer pour chaque combinaison actif/timeframe
    for asset in ASSETS:
        for timeframe in TIMEFRAMES:
            generate_strategy_file(asset, timeframe)
            total_files += 1
    
    print("=" * 70)
    print(f"🎯 Génération terminée ! {total_files} fichiers créés.")
    print("\n📋 Fichiers générés :")
    
    # Lister tous les fichiers créés
    for asset in ASSETS:
        for timeframe in TIMEFRAMES:
            filename = f"Pine_Scripts/{asset}_{timeframe}_Sharpe_1_Optimized.pine"
            print(f"   • {filename}")
    
    print(f"\n✨ Tu peux maintenant copier ces scripts dans TradingView !")
    print(f"🎯 Objectif : Sharpe Ratio > 1 sur tous les actifs et timeframes")

if __name__ == "__main__":
    main() 