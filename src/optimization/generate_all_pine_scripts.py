import os

def generate_pine_script(symbol, timeframe):
    """Génère le code Pine Script v6 pour un symbole et timeframe donnés"""
    
    # Paramètres optimisés selon le symbole et timeframe
    if symbol == 'XAUUSD':
        base_params = {
            'M15': {'breakout': 6, 'risk': 1.10, 'profit': 2.40, 'rsi_high': 77, 'rsi_low': 23, 'adx': 16, 'ema_s': 15, 'ema_l': 40},
            'M30': {'breakout': 8, 'risk': 1.21, 'profit': 2.64, 'rsi_high': 76, 'rsi_low': 24, 'adx': 17, 'ema_s': 18, 'ema_l': 45},
            'H1': {'breakout': 10, 'risk': 1.43, 'profit': 3.24, 'rsi_high': 75, 'rsi_low': 25, 'adx': 18, 'ema_s': 20, 'ema_l': 50},
            'H4': {'breakout': 12, 'risk': 1.54, 'profit': 3.36, 'rsi_high': 74, 'rsi_low': 26, 'adx': 20, 'ema_s': 22, 'ema_l': 55},
            'D1': {'breakout': 15, 'risk': 1.76, 'profit': 3.84, 'rsi_high': 72, 'rsi_low': 28, 'adx': 23, 'ema_s': 25, 'ema_l': 60}
        }
    elif symbol == 'GER40.cash':
        base_params = {
            'M15': {'breakout': 6, 'risk': 0.90, 'profit': 1.90, 'rsi_high': 73, 'rsi_low': 27, 'adx': 21, 'ema_s': 15, 'ema_l': 40},
            'M30': {'breakout': 8, 'risk': 0.99, 'profit': 2.09, 'rsi_high': 72, 'rsi_low': 28, 'adx': 22, 'ema_s': 18, 'ema_l': 45},
            'H1': {'breakout': 10, 'risk': 1.17, 'profit': 2.57, 'rsi_high': 71, 'rsi_low': 29, 'adx': 23, 'ema_s': 20, 'ema_l': 50},
            'H4': {'breakout': 12, 'risk': 1.26, 'profit': 2.66, 'rsi_high': 71, 'rsi_low': 29, 'adx': 25, 'ema_s': 22, 'ema_l': 55},
            'D1': {'breakout': 15, 'risk': 1.44, 'profit': 3.04, 'rsi_high': 69, 'rsi_low': 31, 'adx': 28, 'ema_s': 25, 'ema_l': 60}
        }
    
    params = base_params.get(timeframe, base_params['H1'])
    
    pine_script = f"""//@version=6
strategy("{symbol} {timeframe} Multitimeframe Strategy", overlay=true, margin_long=100, margin_short=100)

// === PARAMÈTRES ===
breakout_period = {params['breakout']}
risk_atr = {params['risk']:.2f}
profit_atr = {params['profit']:.2f}
rsi_overbought = {params['rsi_high']}
rsi_oversold = {params['rsi_low']}
adx_threshold = {params['adx']}
ema_short = {params['ema_s']}
ema_long = {params['ema_l']}

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
    """Génère tous les fichiers Pine Script v6"""
    
    print("🎯 GÉNÉRATION DES FICHIERS PINE SCRIPT v6")
    print("=" * 50)
    
    # Créer le dossier Pine Scripts s'il n'existe pas
    if not os.path.exists('Pine_Scripts'):
        os.makedirs('Pine_Scripts')
    
    symbols = ['XAUUSD', 'GER40.cash']
    timeframes = ['M15', 'M30', 'H1', 'H4', 'D1']
    
    files_created = []
    
    for symbol in symbols:
        for timeframe in timeframes:
            filename = f"Pine_Scripts/{symbol}_{timeframe}_strategy.pine"
            
            # Générer le code Pine Script
            pine_code = generate_pine_script(symbol, timeframe)
            
            # Écrire le fichier
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pine_code)
            
            files_created.append(filename)
            print(f"✅ Créé: {filename}")
    
    print(f"\n🎉 {len(files_created)} fichiers Pine Script v6 créés !")
    print("\n📁 Fichiers créés:")
    for file in files_created:
        print(f"   - {file}")
    
    print("\n💡 UTILISATION:")
    print("1. Ouvrez TradingView")
    print("2. Allez dans Pine Editor")
    print("3. Copiez-collez le contenu du fichier .pine")
    print("4. Cliquez sur 'Add to Chart'")
    print("5. Configurez les alertes si nécessaire")
    
    print("\n🎯 PARAMÈTRES OPTIMISÉS:")
    print("XAUUSD: Plus volatil, RSI plus strict, ADX plus bas")
    print("GER40.cash: Moins volatil, RSI moins strict, ADX plus haut")
    
    print("\n✅ Prêt pour le trading en temps réel !")

if __name__ == "__main__":
    main() 