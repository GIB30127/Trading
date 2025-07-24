import os
import pandas as pd
import numpy as np
from rich import print
import warnings
warnings.filterwarnings('ignore')

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

def compute_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_all_signals(df, symbol, timeframe):
    """Analyse complète de tous les signaux possibles"""
    
    # Calcul des indicateurs
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    df['ATR'] = compute_atr(df, 14)
    df['ADX'] = compute_adx(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    
    # Volatilité
    df['Volatility'] = df['ATR'] / df['Close'] * 100
    
    # Tendances
    df['Trend'] = np.where(df['EMA50'] > df['EMA200'], 1, -1)
    df['Trend_Strength'] = np.where(df['ADX'] > 25, 'Strong', 
                                   np.where(df['ADX'] > 20, 'Medium', 'Weak'))
    
    # Breakouts
    df['High_10'] = df['High'].rolling(10).max()
    df['Low_10'] = df['Low'].rolling(10).min()
    df['Breakout_Up'] = (df['High'] >= df['High_10'].shift(1)) & (df['High'].shift(1) < df['High_10'].shift(2))
    df['Breakout_Down'] = (df['Low'] <= df['Low_10'].shift(1)) & (df['Low'].shift(1) > df['Low_10'].shift(2))
    
    # Pullbacks
    df['Pullback_Up'] = (df['Close'] < df['EMA50']) & (df['EMA50'] > df['EMA200']) & (df['RSI'] < 50)
    df['Pullback_Down'] = (df['Close'] > df['EMA50']) & (df['EMA50'] < df['EMA200']) & (df['RSI'] > 50)
    
    # Divergences RSI
    df['RSI_Higher_High'] = (df['RSI'] > df['RSI'].shift(1)) & (df['Close'] < df['Close'].shift(1))
    df['RSI_Lower_Low'] = (df['RSI'] < df['RSI'].shift(1)) & (df['Close'] > df['Close'].shift(1))
    
    # Support/Résistance
    df['Resistance'] = df['High'].rolling(20).max()
    df['Support'] = df['Low'].rolling(20).min()
    df['Near_Resistance'] = (df['Close'] > df['Resistance'] * 0.98) & (df['Close'] < df['Resistance'])
    df['Near_Support'] = (df['Close'] < df['Support'] * 1.02) & (df['Close'] > df['Support'])
    
    # Analyse de la réussite des signaux
    signals_analysis = {}
    
    # 1. Breakouts
    signals_analysis['breakouts'] = analyze_signal_success(df, 'Breakout_Up', 'Breakout_Down', 'breakout')
    
    # 2. Pullbacks
    signals_analysis['pullbacks'] = analyze_signal_success(df, 'Pullback_Up', 'Pullback_Down', 'pullback')
    
    # 3. Divergences
    signals_analysis['divergences'] = analyze_signal_success(df, 'RSI_Higher_High', 'RSI_Lower_Low', 'divergence')
    
    # 4. Support/Résistance
    signals_analysis['support_resistance'] = analyze_support_resistance(df)
    
    # Statistiques générales
    stats = {
        'avg_volatility': df['Volatility'].mean(),
        'trend_changes': df['Trend'].diff().abs().sum(),
        'strong_trend_periods': (df['ADX'] > 25).sum(),
        'medium_trend_periods': ((df['ADX'] > 20) & (df['ADX'] <= 25)).sum(),
        'weak_trend_periods': (df['ADX'] < 20).sum(),
        'total_periods': len(df)
    }
    
    return signals_analysis, stats

def analyze_signal_success(df, up_signal_col, down_signal_col, signal_type):
    """Analyse la réussite d'un type de signal"""
    
    up_signals = df[up_signal_col].sum()
    down_signals = df[down_signal_col].sum()
    
    # Analyse de la réussite
    up_success = 0
    down_success = 0
    
    for i in range(1, len(df)-10):
        if df.loc[i, up_signal_col]:
            # Vérifier si le prix monte de 1 ATR dans les 10 prochaines bougies
            future_high = df.loc[i:i+10, 'High'].max()
            if future_high >= df.loc[i, 'Close'] + df.loc[i, 'ATR']:
                up_success += 1
                
        if df.loc[i, down_signal_col]:
            # Vérifier si le prix descend de 1 ATR dans les 10 prochaines bougies
            future_low = df.loc[i:i+10, 'Low'].min()
            if future_low <= df.loc[i, 'Close'] - df.loc[i, 'ATR']:
                down_success += 1
    
    up_success_rate = up_success / up_signals * 100 if up_signals > 0 else 0
    down_success_rate = down_success / down_signals * 100 if down_signals > 0 else 0
    
    return {
        'up_signals': up_signals,
        'down_signals': down_signals,
        'up_success_rate': up_success_rate,
        'down_success_rate': down_success_rate,
        'avg_success_rate': (up_success_rate + down_success_rate) / 2
    }

def analyze_support_resistance(df):
    """Analyse des niveaux support/résistance"""
    
    resistance_touches = df['Near_Resistance'].sum()
    support_touches = df['Near_Support'].sum()
    
    # Analyse de la réussite (rebond depuis support/résistance)
    resistance_success = 0
    support_success = 0
    
    for i in range(1, len(df)-5):
        if df.loc[i, 'Near_Resistance']:
            # Vérifier si le prix redescend après avoir touché la résistance
            future_low = df.loc[i:i+5, 'Low'].min()
            if future_low < df.loc[i, 'Close'] - df.loc[i, 'ATR'] * 0.5:
                resistance_success += 1
                
        if df.loc[i, 'Near_Support']:
            # Vérifier si le prix remonte après avoir touché le support
            future_high = df.loc[i:i+5, 'High'].max()
            if future_high > df.loc[i, 'Close'] + df.loc[i, 'ATR'] * 0.5:
                support_success += 1
    
    resistance_success_rate = resistance_success / resistance_touches * 100 if resistance_touches > 0 else 0
    support_success_rate = support_success / support_touches * 100 if support_touches > 0 else 0
    
    return {
        'resistance_touches': resistance_touches,
        'support_touches': support_touches,
        'resistance_success_rate': resistance_success_rate,
        'support_success_rate': support_success_rate,
        'avg_success_rate': (resistance_success_rate + support_success_rate) / 2
    }

def generate_markdown_report(all_results):
    """Génère un rapport markdown complet"""
    
    report = """# 📊 Analyse Complète des Signaux de Trading

## 🎯 Objectif
Cette analyse examine l'efficacité de différents types de signaux de trading pour optimiser la stratégie.

---

"""
    
    # Résumé global
    report += "## 📈 Résumé Global\n\n"
    
    all_signals = []
    for symbol_timeframe, (signals, stats) in all_results.items():
        for signal_type, data in signals.items():
            all_signals.append({
                'symbol_timeframe': symbol_timeframe,
                'signal_type': signal_type,
                'success_rate': data['avg_success_rate']
            })
    
    # Trier par taux de réussite
    all_signals.sort(key=lambda x: x['success_rate'], reverse=True)
    
    report += "### 🏆 Meilleurs Signaux (par taux de réussite)\n\n"
    report += "| Instrument | Signal | Taux de Réussite |\n"
    report += "|------------|--------|------------------|\n"
    
    for signal in all_signals[:10]:
        report += f"| {signal['symbol_timeframe']} | {signal['signal_type']} | {signal['success_rate']:.1f}% |\n"
    
    report += "\n### 📊 Statistiques par Instrument\n\n"
    
    for symbol_timeframe, (signals, stats) in all_results.items():
        report += f"#### {symbol_timeframe}\n\n"
        
        # Statistiques générales
        report += f"- **Volatilité moyenne**: {stats['avg_volatility']:.2f}%\n"
        report += f"- **Changements de tendance**: {stats['trend_changes']}\n"
        report += f"- **Périodes de tendance forte (ADX>25)**: {stats['strong_trend_periods']} ({stats['strong_trend_periods']/stats['total_periods']*100:.1f}%)\n"
        report += f"- **Périodes de tendance moyenne (ADX 20-25)**: {stats['medium_trend_periods']} ({stats['medium_trend_periods']/stats['total_periods']*100:.1f}%)\n"
        report += f"- **Périodes de tendance faible (ADX<20)**: {stats['weak_trend_periods']} ({stats['weak_trend_periods']/stats['total_periods']*100:.1f}%)\n\n"
        
        # Détail des signaux
        report += "**Analyse des signaux :**\n\n"
        
        for signal_type, data in signals.items():
            if signal_type == 'breakouts':
                report += f"- **Breakouts** : {data['up_signals']} haussiers, {data['down_signals']} baissiers\n"
                report += f"  - Taux de réussite haussier : {data['up_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite baissier : {data['down_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite moyen : {data['avg_success_rate']:.1f}%\n\n"
                
            elif signal_type == 'pullbacks':
                report += f"- **Pullbacks** : {data['up_signals']} haussiers, {data['down_signals']} baissiers\n"
                report += f"  - Taux de réussite haussier : {data['up_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite baissier : {data['down_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite moyen : {data['avg_success_rate']:.1f}%\n\n"
                
            elif signal_type == 'divergences':
                report += f"- **Divergences RSI** : {data['up_signals']} haussières, {data['down_signals']} baissières\n"
                report += f"  - Taux de réussite haussier : {data['up_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite baissier : {data['down_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite moyen : {data['avg_success_rate']:.1f}%\n\n"
                
            elif signal_type == 'support_resistance':
                report += f"- **Support/Résistance** : {data['resistance_touches']} touches résistance, {data['support_touches']} touches support\n"
                report += f"  - Taux de réussite résistance : {data['resistance_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite support : {data['support_success_rate']:.1f}%\n"
                report += f"  - Taux de réussite moyen : {data['avg_success_rate']:.1f}%\n\n"
    
    # Recommandations
    report += "## 💡 Recommandations\n\n"
    
    # Analyser les meilleurs signaux
    best_signals = [s for s in all_signals if s['success_rate'] > 50]
    worst_signals = [s for s in all_signals if s['success_rate'] < 30]
    
    if best_signals:
        report += "### ✅ Signaux Prometteurs (>50% de réussite)\n\n"
        for signal in best_signals:
            report += f"- **{signal['signal_type']}** sur {signal['symbol_timeframe']} : {signal['success_rate']:.1f}%\n"
        report += "\n"
    
    if worst_signals:
        report += "### ❌ Signaux à Éviter (<30% de réussite)\n\n"
        for signal in worst_signals:
            report += f"- **{signal['signal_type']}** sur {signal['symbol_timeframe']} : {signal['success_rate']:.1f}%\n"
        report += "\n"
    
    # Stratégie hybride
    report += "## 🚀 Stratégie Hybride Proposée\n\n"
    
    report += """### Combinaison Breakout + Pullback

**Concept :** Utiliser les breakouts pour identifier la direction, puis attendre un pullback pour l'entrée.

**Conditions d'entrée LONG :**
1. Breakout haussier confirmé (prix > résistance + 1 ATR)
2. Pullback vers EMA50 ou niveau de support
3. ADX > 25 (tendance forte)
4. RSI > 30 et < 70 (pas d'extrêmes)
5. Volume > moyenne mobile volume

**Conditions d'entrée SHORT :**
1. Breakout baissier confirmé (prix < support - 1 ATR)
2. Pullback vers EMA50 ou niveau de résistance
3. ADX > 25 (tendance forte)
4. RSI > 30 et < 70 (pas d'extrêmes)
5. Volume > moyenne mobile volume

**Gestion du risque :**
- Stop Loss : 2 ATR
- Take Profit : 4 ATR
- Trailing Stop : 1.5 ATR
- Position Size : 2% du capital max

**Filtres :**
- Pas de trade si ADX < 20 (range)
- Pas de trade en fin de semaine
- Pas de trade pendant les news importantes
"""
    
    return report

def main():
    print("🔍 Analyse complète des signaux de trading")
    print("=" * 50)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_results = {}
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📊 Analyse de {symbol} {timeframe}...")
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                
                signals_analysis, stats = analyze_all_signals(df, symbol, timeframe)
                all_results[f"{symbol}_{timeframe}"] = (signals_analysis, stats)
    
    # Génération du rapport
    print("📝 Génération du rapport markdown...")
    report = generate_markdown_report(all_results)
    
    # Sauvegarde
    os.makedirs("analysis_reports", exist_ok=True)
    with open("analysis_reports/comprehensive_analysis.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Rapport généré : analysis_reports/comprehensive_analysis.md")
    
    # Affichage des meilleurs signaux
    print("\n🏆 Meilleurs signaux identifiés :")
    all_signals = []
    for symbol_timeframe, (signals, stats) in all_results.items():
        for signal_type, data in signals.items():
            all_signals.append({
                'symbol_timeframe': symbol_timeframe,
                'signal_type': signal_type,
                'success_rate': data['avg_success_rate']
            })
    
    all_signals.sort(key=lambda x: x['success_rate'], reverse=True)
    
    for i, signal in enumerate(all_signals[:5]):
        print(f"{i+1}. {signal['signal_type']} sur {signal['symbol_timeframe']} : {signal['success_rate']:.1f}%")

if __name__ == "__main__":
    main() 