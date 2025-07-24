#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour générer automatiquement toutes les versions améliorées des stratégies Pine Script
"""

import os

# Configuration des instruments et timeframes
INSTRUMENTS = {
    'XAUUSD': 'XAUUSD',
    'GER40.cash': 'GER40.cash'
}

TIMEFRAMES = ['M15', 'H1', 'H4', 'D1', 'M30']

# Paramètres optimisés pour chaque timeframe
TIMEFRAME_PARAMS = {
    'M15': {
        'breakout_period': 8,
        'risk_atr': 1.0,
        'profit_atr': 2.0,
        'rsi_overbought': 75,
        'rsi_oversold': 25,
        'adx_threshold': 20,
        'ema_short': 15,
        'ema_long': 40
    },
    'H1': {
        'breakout_period': 10,
        'risk_atr': 1.1,
        'profit_atr': 2.2,
        'rsi_overbought': 72,
        'rsi_oversold': 28,
        'adx_threshold': 22,
        'ema_short': 18,
        'ema_long': 45
    },
    'H4': {
        'breakout_period': 12,
        'risk_atr': 1.2,
        'profit_atr': 2.4,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'adx_threshold': 25,
        'ema_short': 21,
        'ema_long': 55
    },
    'D1': {
        'breakout_period': 12,
        'risk_atr': 1.2,
        'profit_atr': 2.4,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'adx_threshold': 25,
        'ema_short': 21,
        'ema_long': 55
    },
    'M30': {
        'breakout_period': 9,
        'risk_atr': 1.05,
        'profit_atr': 2.1,
        'rsi_overbought': 73,
        'rsi_oversold': 27,
        'adx_threshold': 21,
        'ema_short': 17,
        'ema_long': 42
    }
}

def generate_improved_strategy(instrument, timeframe):
    """Génère une version améliorée de la stratégie"""
    params = TIMEFRAME_PARAMS[timeframe]
    
    strategy_name = f"{instrument}_{timeframe}_strategy_improved"
    
    script = f'''//@version=6
strategy("{instrument} {timeframe} Multitimeframe Strategy - Improved", overlay=true, margin_long=100, margin_short=100)

// === PARAMÈTRES OPTIMISÉS POUR MEILLEUR SHARPE RATIO ===
breakout_period = {params['breakout_period']}       // Optimisé pour qualité vs quantité
risk_atr = {params['risk_atr']}            // Stop loss plus serré
profit_atr = {params['profit_atr']}          // Take profit plus réaliste
rsi_overbought = {params['rsi_overbought']}       // Seuils RSI plus stricts
rsi_oversold = {params['rsi_oversold']}         // Seuils RSI plus stricts
adx_threshold = {params['adx_threshold']}        // ADX plus strict pour qualité
ema_short = {params['ema_short']}            // EMA optimisée
ema_long = {params['ema_long']}             // EMA optimisée

// === INDICATEURS ===
atr = ta.atr(14)
rsi = ta.rsi(close, 14)
// Utilisation d'un indicateur de tendance simple
trend_strength_indicator = math.abs(ta.ema(close, 14) - ta.ema(close, 28)) / atr
adx = trend_strength_indicator * 100
ema_short_val = ta.ema(close, ema_short)
ema_long_val = ta.ema(close, ema_long)

// Breakouts
high_break = ta.highest(high, breakout_period)
low_break = ta.lowest(low, breakout_period)

// Filtres améliorés pour qualité
trend_strength = math.abs(ema_short_val - ema_long_val) / atr
volatility_ok = atr > ta.sma(atr, 50) * 0.7  // Volatilité modérée
volume_ok = volume > ta.sma(volume, 20) * 0.8  // Volume plus strict

// === CONDITIONS AMÉLIORÉES ===
ema_trend = close > ema_long_val
adx_strong = adx > adx_threshold
trend_strong = trend_strength > 0.4  // Tendance plus forte

breakout_up = high[1] < high_break[1] and high >= high_break
breakout_down = low[1] > low_break[1] and low <= low_break

// Conditions RSI plus strictes
rsi_ok_long = rsi < rsi_overbought and rsi > 40  // Zone plus restrictive
rsi_ok_short = rsi > rsi_oversold and rsi < 60   // Zone plus restrictive

// Filtres supplémentaires pour Short (éviter les appels de marge)
strong_downtrend = ema_short_val < ema_long_val and close < ema_short_val
strong_uptrend = ema_short_val > ema_long_val and close > ema_short_val

// === SIGNALS AMÉLIORÉS ===
long_condition = breakout_up and ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_long and close > ema_short_val and strong_uptrend
short_condition = breakout_down and not ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_short and close < ema_short_val and strong_downtrend

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
alertcondition(long_condition, "Signal Long", "Signal d'achat {instrument} {timeframe} - Improved")
alertcondition(short_condition, "Signal Short", "Signal de vente {instrument} {timeframe} - Improved")
'''
    
    return script

def generate_long_only_strategy(instrument, timeframe):
    """Génère une version Long-only de la stratégie"""
    params = TIMEFRAME_PARAMS[timeframe]
    
    # Paramètres ajustés pour Long-only
    long_params = {
        'breakout_period': max(8, params['breakout_period'] - 2),
        'risk_atr': params['risk_atr'] - 0.1,
        'profit_atr': params['profit_atr'] - 0.2,
        'rsi_overbought': params['rsi_overbought'] - 5,
        'rsi_oversold': params['rsi_oversold'] + 5,
        'adx_threshold': params['adx_threshold'] - 3,
        'ema_short': params['ema_short'] - 1,
        'ema_long': params['ema_long'] - 5
    }
    
    script = f'''//@version=6
strategy("{instrument} {timeframe} Multitimeframe Strategy - Long Only", overlay=true, margin_long=100, margin_short=100)

// === PARAMÈTRES OPTIMISÉS POUR LONG ONLY ===
breakout_period = {long_params['breakout_period']}       // Optimisé pour Long
risk_atr = {long_params['risk_atr']}            // Stop loss serré
profit_atr = {long_params['profit_atr']}          // Take profit réaliste
rsi_overbought = {long_params['rsi_overbought']}       // Seuil RSI strict pour Long
rsi_oversold = {long_params['rsi_oversold']}         // Seuil RSI pour éviter les zones de survente
adx_threshold = {long_params['adx_threshold']}        // ADX pour qualité
ema_short = {long_params['ema_short']}            // EMA courte réactive
ema_long = {long_params['ema_long']}             // EMA longue

// === INDICATEURS ===
atr = ta.atr(14)
rsi = ta.rsi(close, 14)
// Utilisation d'un indicateur de tendance simple
trend_strength_indicator = math.abs(ta.ema(close, 14) - ta.ema(close, 28)) / atr
adx = trend_strength_indicator * 100
ema_short_val = ta.ema(close, ema_short)
ema_long_val = ta.ema(close, ema_long)

// Breakouts
high_break = ta.highest(high, breakout_period)
low_break = ta.lowest(low, breakout_period)

// Filtres optimisés pour Long
trend_strength = math.abs(ema_short_val - ema_long_val) / atr
volatility_ok = atr > ta.sma(atr, 50) * 0.6  // Volatilité suffisante
volume_ok = volume > ta.sma(volume, 20) * 0.7  // Volume correct

// === CONDITIONS OPTIMISÉES POUR LONG ===
ema_trend = close > ema_long_val
adx_strong = adx > adx_threshold
trend_strong = trend_strength > 0.3

breakout_up = high[1] < high_break[1] and high >= high_break

// Conditions RSI optimisées pour Long
rsi_ok_long = rsi < rsi_overbought and rsi > 35  // Zone optimale pour Long

// Filtres supplémentaires pour qualité Long
strong_uptrend = ema_short_val > ema_long_val and close > ema_short_val
momentum_positive = close > close[1] and close[1] > close[2]  // Momentum haussier

// === SIGNAL LONG SEULEMENT ===
long_condition = breakout_up and ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_long and close > ema_short_val and strong_uptrend and momentum_positive

// === STRATÉGIE LONG ONLY ===
if long_condition
    strategy.entry("Long", strategy.long)
    strategy.exit("Exit Long", "Long", stop=close - risk_atr * atr, limit=close + profit_atr * atr)

// === PLOTS ===
plot(ema_short_val, "EMA Short", color=color.blue)
plot(ema_long_val, "EMA Long", color=color.red)
plot(high_break, "High Break", color=color.green, style=plot.style_line)
plot(low_break, "Low Break", color=color.red, style=plot.style_line)

// === ALERTS ===
alertcondition(long_condition, "Signal Long", "Signal d'achat {instrument} {timeframe} - Long Only")
'''
    
    return script

def main():
    """Fonction principale pour générer tous les scripts"""
    output_dir = "Pine_Scripts_Improved"
    
    # Créer le dossier de sortie
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("🚀 Génération des stratégies améliorées...")
    
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            print(f"📝 Génération {instrument} {timeframe}...")
            
            # Version Improved
            improved_script = generate_improved_strategy(instrument, timeframe)
            improved_filename = f"{output_dir}/{instrument}_{timeframe}_strategy_improved.pine"
            with open(improved_filename, 'w', encoding='utf-8') as f:
                f.write(improved_script)
            
            # Version Long Only
            long_only_script = generate_long_only_strategy(instrument, timeframe)
            long_only_filename = f"{output_dir}/{instrument}_{timeframe}_strategy_long_only.pine"
            with open(long_only_filename, 'w', encoding='utf-8') as f:
                f.write(long_only_script)
    
    print(f"✅ Génération terminée ! {len(INSTRUMENTS) * len(TIMEFRAMES) * 2} fichiers créés dans {output_dir}/")
    print("\n📁 Fichiers générés :")
    
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            print(f"  - {instrument}_{timeframe}_strategy_improved.pine")
            print(f"  - {instrument}_{timeframe}_strategy_long_only.pine")

if __name__ == "__main__":
    main() 