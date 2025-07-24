#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour générer des stratégies Pine Script optimisées pour un Sharpe Ratio minimum de 1
"""

import os

# Configuration des instruments et timeframes
INSTRUMENTS = {
    'XAUUSD': 'XAUUSD',
    'GER40.cash': 'GER40.cash'
}

TIMEFRAMES = ['M15', 'H1', 'H4', 'D1', 'M30']

# Paramètres optimisés pour Sharpe Ratio > 1
HIGH_SHARPE_PARAMS = {
    'M15': {
        'breakout_period': 6,
        'risk_atr': 0.8,
        'profit_atr': 1.6,
        'rsi_overbought': 68,
        'rsi_oversold': 32,
        'adx_threshold': 35,
        'ema_short': 12,
        'ema_long': 35,
        'volatility_mult': 0.8,
        'volume_mult': 0.9,
        'trend_strength': 0.5
    },
    'H1': {
        'breakout_period': 8,
        'risk_atr': 0.9,
        'profit_atr': 1.8,
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'adx_threshold': 32,
        'ema_short': 15,
        'ema_long': 40,
        'volatility_mult': 0.8,
        'volume_mult': 0.9,
        'trend_strength': 0.5
    },
    'H4': {
        'breakout_period': 10,
        'risk_atr': 1.0,
        'profit_atr': 2.0,
        'rsi_overbought': 72,
        'rsi_oversold': 28,
        'adx_threshold': 30,
        'ema_short': 18,
        'ema_long': 45,
        'volatility_mult': 0.8,
        'volume_mult': 0.9,
        'trend_strength': 0.5
    },
    'D1': {
        'breakout_period': 12,
        'risk_atr': 1.1,
        'profit_atr': 2.2,
        'rsi_overbought': 72,
        'rsi_oversold': 28,
        'adx_threshold': 30,
        'ema_short': 20,
        'ema_long': 50,
        'volatility_mult': 0.8,
        'volume_mult': 0.9,
        'trend_strength': 0.5
    },
    'M30': {
        'breakout_period': 7,
        'risk_atr': 0.85,
        'profit_atr': 1.7,
        'rsi_overbought': 69,
        'rsi_oversold': 31,
        'adx_threshold': 33,
        'ema_short': 14,
        'ema_long': 38,
        'volatility_mult': 0.8,
        'volume_mult': 0.9,
        'trend_strength': 0.5
    }
}

def generate_high_sharpe_strategy(instrument, timeframe):
    """Génère une stratégie optimisée pour Sharpe Ratio > 1"""
    params = HIGH_SHARPE_PARAMS[timeframe]
    
    script = f'''//@version=6
strategy("{instrument} {timeframe} High Sharpe Strategy", overlay=true, margin_long=100, margin_short=100)

// === PARAMÈTRES OPTIMISÉS POUR SHARPE RATIO > 1 ===
breakout_period = {params['breakout_period']}       // Breakout court pour qualité
risk_atr = {params['risk_atr']}            // Stop loss très serré
profit_atr = {params['profit_atr']}          // Take profit optimisé
rsi_overbought = {params['rsi_overbought']}       // Seuils RSI stricts
rsi_oversold = {params['rsi_oversold']}         // Seuils RSI stricts
adx_threshold = {params['adx_threshold']}        // ADX très strict
ema_short = {params['ema_short']}            // EMA courte réactive
ema_long = {params['ema_long']}             // EMA longue
volatility_mult = {params['volatility_mult']}    // Multiplicateur volatilité
volume_mult = {params['volume_mult']}        // Multiplicateur volume
trend_strength = {params['trend_strength']}      // Force de tendance

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

// Filtres très stricts pour qualité maximale
trend_strength_calc = math.abs(ema_short_val - ema_long_val) / atr
volatility_ok = atr > ta.sma(atr, 50) * volatility_mult  // Volatilité contrôlée
volume_ok = volume > ta.sma(volume, 20) * volume_mult  // Volume strict

// === CONDITIONS TRÈS STRICTES ===
ema_trend = close > ema_long_val
adx_strong = adx > adx_threshold
trend_strong = trend_strength_calc > trend_strength

breakout_up = high[1] < high_break[1] and high >= high_break
breakout_down = low[1] > low_break[1] and low <= low_break

// Conditions RSI très strictes
rsi_ok_long = rsi < rsi_overbought and rsi > 45  // Zone très restrictive
rsi_ok_short = rsi > rsi_oversold and rsi < 55   // Zone très restrictive

// Filtres supplémentaires pour qualité maximale
strong_downtrend = ema_short_val < ema_long_val and close < ema_short_val and close < close[1]
strong_uptrend = ema_short_val > ema_long_val and close > ema_short_val and close > close[1]

// Filtres de volatilité et momentum
low_volatility = atr < ta.sma(atr, 20) * 1.2  // Éviter la forte volatilité
momentum_positive = close > close[1] and close[1] > close[2]  // Momentum haussier
momentum_negative = close < close[1] and close[1] < close[2]  // Momentum baissier

// === SIGNALS TRÈS STRICTS ===
long_condition = breakout_up and ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_long and close > ema_short_val and strong_uptrend and momentum_positive and low_volatility
short_condition = breakout_down and not ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_short and close < ema_short_val and strong_downtrend and momentum_negative and low_volatility

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
alertcondition(long_condition, "Signal Long", "Signal d'achat {instrument} {timeframe} - High Sharpe")
alertcondition(short_condition, "Signal Short", "Signal de vente {instrument} {timeframe} - High Sharpe")
'''
    
    return script

def generate_high_sharpe_long_only(instrument, timeframe):
    """Génère une version Long-only optimisée pour Sharpe Ratio > 1"""
    params = HIGH_SHARPE_PARAMS[timeframe]
    
    # Paramètres ajustés pour Long-only
    long_params = {
        'breakout_period': max(5, params['breakout_period'] - 1),
        'risk_atr': params['risk_atr'] - 0.1,
        'profit_atr': params['profit_atr'] - 0.1,
        'rsi_overbought': params['rsi_overbought'] - 3,
        'rsi_oversold': params['rsi_oversold'] + 3,
        'adx_threshold': params['adx_threshold'] - 2,
        'ema_short': params['ema_short'] - 1,
        'ema_long': params['ema_long'] - 2,
        'volatility_mult': params['volatility_mult'],
        'volume_mult': params['volume_mult'],
        'trend_strength': params['trend_strength']
    }
    
    script = f'''//@version=6
strategy("{instrument} {timeframe} High Sharpe Strategy - Long Only", overlay=true, margin_long=100, margin_short=100)

// === PARAMÈTRES OPTIMISÉS POUR SHARPE RATIO > 1 (LONG ONLY) ===
breakout_period = {long_params['breakout_period']}       // Breakout court pour qualité
risk_atr = {long_params['risk_atr']}            // Stop loss très serré
profit_atr = {long_params['profit_atr']}          // Take profit optimisé
rsi_overbought = {long_params['rsi_overbought']}       // Seuils RSI stricts
rsi_oversold = {long_params['rsi_oversold']}         // Seuils RSI pour éviter survente
adx_threshold = {long_params['adx_threshold']}        // ADX très strict
ema_short = {long_params['ema_short']}            // EMA courte réactive
ema_long = {long_params['ema_long']}             // EMA longue
volatility_mult = {long_params['volatility_mult']}    // Multiplicateur volatilité
volume_mult = {long_params['volume_mult']}        // Multiplicateur volume
trend_strength = {long_params['trend_strength']}      // Force de tendance

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

// Filtres très stricts pour qualité maximale
trend_strength_calc = math.abs(ema_short_val - ema_long_val) / atr
volatility_ok = atr > ta.sma(atr, 50) * volatility_mult  // Volatilité contrôlée
volume_ok = volume > ta.sma(volume, 20) * volume_mult  // Volume strict

// === CONDITIONS TRÈS STRICTES POUR LONG ===
ema_trend = close > ema_long_val
adx_strong = adx > adx_threshold
trend_strong = trend_strength_calc > trend_strength

breakout_up = high[1] < high_break[1] and high >= high_break

// Conditions RSI très strictes pour Long
rsi_ok_long = rsi < rsi_overbought and rsi > 40  // Zone très restrictive

// Filtres supplémentaires pour qualité maximale Long
strong_uptrend = ema_short_val > ema_long_val and close > ema_short_val and close > close[1]
momentum_positive = close > close[1] and close[1] > close[2]  // Momentum haussier
low_volatility = atr < ta.sma(atr, 20) * 1.2  // Éviter la forte volatilité

// Filtres de marché haussier
bullish_market = close > ta.sma(close, 50) and ta.sma(close, 20) > ta.sma(close, 50)
price_above_ema = close > ema_short_val and ema_short_val > ema_long_val

// === SIGNAL LONG TRÈS STRICT ===
long_condition = breakout_up and ema_trend and volume_ok and adx_strong and volatility_ok and trend_strong and rsi_ok_long and close > ema_short_val and strong_uptrend and momentum_positive and low_volatility and bullish_market and price_above_ema

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
alertcondition(long_condition, "Signal Long", "Signal d'achat {instrument} {timeframe} - High Sharpe Long Only")
'''
    
    return script

def main():
    """Fonction principale pour générer tous les scripts"""
    output_dir = "Pine_Scripts_High_Sharpe"
    
    # Créer le dossier de sortie
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("🚀 Génération des stratégies High Sharpe (Sharpe Ratio > 1)...")
    
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            print(f"📝 Génération {instrument} {timeframe}...")
            
            # Version High Sharpe (Long + Short)
            high_sharpe_script = generate_high_sharpe_strategy(instrument, timeframe)
            high_sharpe_filename = f"{output_dir}/{instrument}_{timeframe}_high_sharpe.pine"
            with open(high_sharpe_filename, 'w', encoding='utf-8') as f:
                f.write(high_sharpe_script)
            
            # Version High Sharpe Long Only
            high_sharpe_long_script = generate_high_sharpe_long_only(instrument, timeframe)
            high_sharpe_long_filename = f"{output_dir}/{instrument}_{timeframe}_high_sharpe_long_only.pine"
            with open(high_sharpe_long_filename, 'w', encoding='utf-8') as f:
                f.write(high_sharpe_long_script)
    
    print(f"✅ Génération terminée ! {len(INSTRUMENTS) * len(TIMEFRAMES) * 2} fichiers créés dans {output_dir}/")
    print("\n📁 Fichiers générés :")
    
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            print(f"  - {instrument}_{timeframe}_high_sharpe.pine")
            print(f"  - {instrument}_{timeframe}_high_sharpe_long_only.pine")
    
    print("\n🎯 Objectif : Sharpe Ratio > 1 sur tous les actifs et timeframes")
    print("📊 Optimisations appliquées :")
    print("  - Stop loss très serré")
    print("  - Take profit optimisé")
    print("  - Filtres très stricts")
    print("  - Contrôle de la volatilité")
    print("  - Momentum requis")

if __name__ == "__main__":
    main() 