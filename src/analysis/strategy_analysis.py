import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rich import print
import warnings
warnings.filterwarnings('ignore')

def analyze_market_conditions(df, symbol, timeframe):
    """Analyse les conditions de marché pour comprendre pourquoi la stratégie échoue"""
    
    print(f"\n🔍 Analyse des conditions de marché pour {symbol} {timeframe}")
    print("=" * 60)
    
    # Calcul des indicateurs
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    df['ATR'] = compute_atr(df, 14)
    df['ADX'] = compute_adx(df, 14)
    
    # Analyse de la volatilité
    df['Volatility'] = df['ATR'] / df['Close'] * 100
    avg_volatility = df['Volatility'].mean()
    
    # Analyse des tendances
    df['Trend'] = np.where(df['EMA50'] > df['EMA200'], 1, -1)  # 1 pour bullish, -1 pour bearish
    trend_changes = df['Trend'].diff().abs().sum()
    
    # Analyse des breakouts
    df['High_10'] = df['High'].rolling(10).max()
    df['Low_10'] = df['Low'].rolling(10).min()
    df['Breakout_Up'] = (df['High'] >= df['High_10'].shift(1)) & (df['High'].shift(1) < df['High_10'].shift(2))
    df['Breakout_Down'] = (df['Low'] <= df['Low_10'].shift(1)) & (df['Low'].shift(1) > df['Low_10'].shift(2))
    
    breakout_up_count = df['Breakout_Up'].sum()
    breakout_down_count = df['Breakout_Down'].sum()
    
    # Analyse de la réussite des breakouts
    df['Breakout_Success_Up'] = False
    df['Breakout_Success_Down'] = False
    
    for i in range(1, len(df)-5):
        if df.loc[i, 'Breakout_Up']:
            # Vérifier si le prix monte de 1 ATR dans les 5 prochaines bougies
            future_high = df.loc[i:i+5, 'High'].max()
            if future_high >= df.loc[i, 'Close'] + df.loc[i, 'ATR']:
                df.loc[i, 'Breakout_Success_Up'] = True
                
        if df.loc[i, 'Breakout_Down']:
            # Vérifier si le prix descend de 1 ATR dans les 5 prochaines bougies
            future_low = df.loc[i:i+5, 'Low'].min()
            if future_low <= df.loc[i, 'Close'] - df.loc[i, 'ATR']:
                df.loc[i, 'Breakout_Success_Down'] = True
    
    success_up_rate = df['Breakout_Success_Up'].sum() / breakout_up_count * 100 if breakout_up_count > 0 else 0
    success_down_rate = df['Breakout_Success_Down'].sum() / breakout_down_count * 100 if breakout_down_count > 0 else 0
    
    # Analyse ADX
    strong_trend_periods = (df['ADX'] > 25).sum()
    weak_trend_periods = (df['ADX'] < 20).sum()
    
    print(f"📊 Statistiques générales:")
    print(f"  - Volatilité moyenne: {avg_volatility:.2f}%")
    print(f"  - Changements de tendance: {trend_changes}")
    print(f"  - Périodes de tendance forte (ADX>25): {strong_trend_periods} ({strong_trend_periods/len(df)*100:.1f}%)")
    print(f"  - Périodes de tendance faible (ADX<20): {weak_trend_periods} ({weak_trend_periods/len(df)*100:.1f}%)")
    
    print(f"\n🎯 Analyse des breakouts:")
    print(f"  - Breakouts haussiers: {breakout_up_count}")
    print(f"  - Breakouts baissiers: {breakout_down_count}")
    print(f"  - Taux de réussite haussier: {success_up_rate:.1f}%")
    print(f"  - Taux de réussite baissier: {success_down_rate:.1f}%")
    
    return {
        'avg_volatility': avg_volatility,
        'trend_changes': trend_changes,
        'breakout_up_success': success_up_rate,
        'breakout_down_success': success_down_rate,
        'strong_trend_periods': strong_trend_periods,
        'weak_trend_periods': weak_trend_periods
    }

def compute_atr(df, window):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_adx(df, window):
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff().abs()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    trur = compute_atr(df, window)
    plus_di = 100 * (plus_dm.rolling(window=window).sum() / trur)
    minus_di = 100 * (minus_dm.rolling(window=window).sum() / trur)
    dx = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=window).mean()
    return adx

def suggest_improvements(analysis_results):
    """Suggère des améliorations basées sur l'analyse"""
    
    print(f"\n💡 Suggestions d'amélioration:")
    print("=" * 40)
    
    if analysis_results['breakout_up_success'] < 40 or analysis_results['breakout_down_success'] < 40:
        print("❌ Les breakouts ont un faible taux de réussite")
        print("   → Considérer d'autres signaux d'entrée")
        print("   → Ajouter des filtres de confirmation")
        print("   → Utiliser des pullbacks plutôt que des breakouts")
    
    if analysis_results['weak_trend_periods'] > analysis_results['strong_trend_periods']:
        print("❌ Beaucoup de périodes sans tendance claire")
        print("   → Éviter de trader en range")
        print("   → Attendre des conditions de tendance forte")
        print("   → Utiliser des indicateurs de range")
    
    if analysis_results['avg_volatility'] < 0.5:
        print("❌ Volatilité trop faible")
        print("   → Augmenter les timeframes")
        print("   → Chercher des instruments plus volatils")
    
    print(f"\n✅ Recommandations générales:")
    print("   1. Utiliser des pullbacks sur EMA plutôt que des breakouts")
    print("   2. Trader uniquement quand ADX > 25")
    print("   3. Utiliser des stops plus larges (2-3 ATR)")
    print("   4. Chercher des divergences RSI/prix")
    print("   5. Éviter de trader en range (ADX < 20)")

def create_improved_strategy():
    """Crée une stratégie améliorée basée sur l'analyse"""
    
    print(f"\n🚀 Stratégie améliorée proposée:")
    print("=" * 40)
    
    strategy = """
    # === STRATÉGIE AMÉLIORÉE ===
    
    ## Conditions d'entrée LONG:
    1. Prix > EMA50 > EMA200 (tendance haussière)
    2. ADX > 25 (tendance forte)
    3. RSI < 70 (pas de sur-achat)
    4. Pullback vers EMA50 (pas de breakout)
    5. Volume > moyenne mobile volume
    
    ## Conditions d'entrée SHORT:
    1. Prix < EMA50 < EMA200 (tendance baissière)
    2. ADX > 25 (tendance forte)
    3. RSI > 30 (pas de sur-vente)
    4. Pullback vers EMA50 (pas de breakout)
    5. Volume > moyenne mobile volume
    
    ## Gestion du risque:
    - Stop Loss: 2.5 ATR
    - Take Profit: 4 ATR
    - Trailing Stop: 1.5 ATR
    - Position Size: 2% du capital max
    
    ## Filtres:
    - Pas de trade si ADX < 20 (range)
    - Pas de trade en fin de semaine
    - Pas de trade pendant les news importantes
    """
    
    print(strategy)

def main():
    print("🔍 Analyse approfondie de la stratégie")
    print("=" * 50)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD']
    TIMEFRAMES = ['D1', 'H4']
    
    all_results = {}
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"\n📊 Analyse de {symbol} {timeframe}...")
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                
                results = analyze_market_conditions(df, symbol, timeframe)
                all_results[f"{symbol}_{timeframe}"] = results
                
                suggest_improvements(results)
    
    # Analyse globale
    print(f"\n🌍 Analyse globale:")
    print("=" * 30)
    
    avg_breakout_success = np.mean([
        results['breakout_up_success'] + results['breakout_down_success']
        for results in all_results.values()
    ]) / 2
    
    print(f"Taux de réussite moyen des breakouts: {avg_breakout_success:.1f}%")
    
    if avg_breakout_success < 45:
        print("❌ Les breakouts ne sont pas une stratégie viable")
        print("   → Nécessité de changer d'approche")
    
    create_improved_strategy()

if __name__ == "__main__":
    main() 