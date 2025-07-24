# Stratégie XAUUSD D1 Sharpe 1 Simple

## 📋 Description

Cette stratégie de trading a été transformée depuis un script Pine Script vers Python pour permettre le backtesting avec MetaTrader 5 (MT5) et les fichiers CSV. Elle est conçue pour trader l'or (XAUUSD) sur le timeframe journalier (D1) avec un ratio de Sharpe optimisé.

## 🎯 Caractéristiques

- **Symbole**: XAUUSD (Or)
- **Timeframe**: D1 (Journalier)
- **Type**: Breakout avec filtres multiples
- **Gestion des risques**: Trailing stop basé sur ATR
- **Compatible**: MT5 et CSV

## 📊 Paramètres de la Stratégie

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Breakout Period | 2 | Période pour détecter les breakouts |
| Profit ATR | 2.5 | Multiplicateur ATR pour le take profit |
| Trail ATR | 0.5 | Multiplicateur ATR pour le trailing stop |
| RSI Overbought | 85 | Niveau de surachat RSI |
| RSI Oversold | 15 | Niveau de survente RSI |
| EMA Short | 4 | EMA courte |
| EMA Long | 12 | EMA longue |
| ATR Period | 8 | Période pour le calcul ATR |

## 🧠 Logique de la Stratégie

### Conditions d'Entrée LONG
- Breakout au-dessus du plus haut des 2 dernières bougies
- EMA courte > EMA longue (tendance haussière)
- Prix > EMA courte
- RSI < 85 et > 20
- ATR > moyenne ATR × 0.3 (volatilité suffisante)
- Volume > moyenne volume × 0.5
- Momentum haussier (prix > prix précédent)

### Conditions d'Entrée SHORT
- Breakout en-dessous du plus bas des 2 dernières bougies
- EMA courte < EMA longue (tendance baissière)
- Prix < EMA courte
- RSI > 15 et < 80
- ATR > moyenne ATR × 0.3 (volatilité suffisante)
- Volume > moyenne volume × 0.5
- Momentum baissier (prix < prix précédent)

### Gestion des Sorties
- **Take Profit**: Prix d'entrée ± (2.5 × ATR)
- **Stop Loss**: Trailing stop basé sur 0.5 × ATR
- **Sortie sur signal opposé**

## 📁 Structure des Fichiers

```
Trad_Essay_Sven/
├── src/
│   ├── strategies/
│   │   ├── strategie_xauusd_sharpe1_simple.py      # Stratégie principale
│   │   └── strategie_xauusd_sharpe1_mt5_live.py    # Version temps réel
│   └── backtesting/
│       ├── backtest_xauusd_sharpe1_simple.py       # Backtest simple
│       └── backtest_all_xauusd_sharpe1.py          # Test multi-timeframes
├── data/
│   └── raw/
│       └── XAUUSD_D1_mt5.csv                       # Données historiques
├── results/
│   └── backtests/                                   # Résultats des backtests
├── demo_strategie_xauusd.py                        # Script de démonstration
└── README_STRATEGIE_XAUUSD.md                      # Ce fichier
```

## 🚀 Utilisation

### 1. Installation des Dépendances

```bash
pip install pandas numpy plotly rich MetaTrader5
```

### 2. Backtest Simple avec CSV

```python
import pandas as pd
from src.strategies.strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple

# Chargement des données
df = pd.read_csv("data/raw/XAUUSD_D1_mt5.csv")
df['Date'] = pd.to_datetime(df['Date'])

# Application de la stratégie
trades, df_signals = strategie_xauusd_sharpe1_simple(df, 'XAUUSD', 'D1')

# Affichage des résultats
print(f"Total trades: {len(trades)}")
```

### 3. Trading en Temps Réel avec MT5

```python
from src.strategies.strategie_xauusd_sharpe1_mt5_live import XAUUSDSharpe1LiveStrategy
import MetaTrader5 as mt5

# Initialisation MT5
mt5.initialize()

# Initialisation de la stratégie
strategy = XAUUSDSharpe1LiveStrategy("XAUUSD", "D1")

# Récupération des données
rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_D1, 0, 1000)
df = pd.DataFrame(rates)
df['Date'] = pd.to_datetime(df['time'], unit='s')

# Traitement des nouvelles données
for i in range(len(df)):
    result = strategy.process_new_data(df, i)
    if result:
        print(f"Nouveau trade: {result}")
```

### 4. Test Multi-Timeframes

```bash
python src/backtesting/backtest_all_xauusd_sharpe1.py
```

### 5. Démonstration Complète

```bash
python demo_strategie_xauusd.py
```

## 📈 Résultats du Backtest

### Performance sur XAUUSD D1
- **Total trades**: 523
- **Taux de réussite**: 49.33%
- **Retour total**: 314.69%
- **Profit Factor**: 2.54
- **Ratio de Sharpe**: 166.26
- **Drawdown max**: 68.71%

### Métriques Détaillées
- **Trades gagnants**: 258
- **Trades perdants**: 265
- **Gain moyen**: 2.01%
- **Perte moyenne**: -0.77%

## 🔧 Personnalisation

### Modification des Paramètres

Vous pouvez ajuster les paramètres dans le fichier `strategie_xauusd_sharpe1_simple.py` :

```python
# Paramètres de la stratégie
breakout_period = 2          # Période de breakout
profit_atr = 2.5            # Multiplicateur ATR pour take profit
trail_atr = 0.5             # Multiplicateur ATR pour trailing stop
rsi_overbought = 85         # Niveau RSI surachat
rsi_oversold = 15           # Niveau RSI survente
ema_short = 4               # EMA courte
ema_long = 12               # EMA longue
atr_period = 8              # Période ATR
```

### Adaptation à d'Autres Symboles

La stratégie peut être adaptée à d'autres symboles en modifiant les paramètres selon les caractéristiques de volatilité :

```python
# Exemple pour EURUSD
if symbol == 'EURUSD':
    breakout_period = 3
    profit_atr = 2.0
    trail_atr = 0.4
    rsi_overbought = 80
    rsi_oversold = 20
```

## 📊 Visualisation

### Génération de Graphiques

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Création du graphique
fig = make_subplots(rows=3, cols=1, shared_xaxes=True)

# Prix et signaux
fig.add_trace(go.Candlestick(
    x=df['Date'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Prix'
), row=1, col=1)

# Indicateurs
fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_Short'], name='EMA Short'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_Long'], name='EMA Long'), row=1, col=1)

# RSI
fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI'), row=2, col=1)

# ATR
fig.add_trace(go.Scatter(x=df['Date'], y=df['ATR'], name='ATR'), row=3, col=1)

fig.show()
```

## ⚠️ Avertissements

1. **Risque de Trading**: Le trading comporte des risques de perte. Cette stratégie est fournie à des fins éducatives uniquement.

2. **Backtesting vs Trading Réel**: Les résultats de backtest peuvent différer du trading réel en raison des spreads, slippage et autres coûts.

3. **Optimisation**: Les paramètres ont été optimisés sur des données historiques et peuvent nécessiter des ajustements pour les conditions de marché actuelles.

4. **Test en Compte Démo**: Testez toujours la stratégie sur un compte démo avant de l'utiliser en réel.

## 🤝 Contribution

Pour contribuer à l'amélioration de cette stratégie :

1. Testez sur différents timeframes et symboles
2. Proposez des optimisations de paramètres
3. Ajoutez de nouveaux filtres ou indicateurs
4. Améliorez la gestion des risques

## 📞 Support

Pour toute question ou problème :

1. Vérifiez que toutes les dépendances sont installées
2. Assurez-vous que les fichiers de données sont présents
3. Consultez les logs d'erreur pour le débogage
4. Testez avec des données de démonstration

## 📚 Ressources Additionnelles

- [Documentation MetaTrader5](https://www.mql5.com/en/docs)
- [Guide Pine Script](https://www.tradingview.com/pine-script-docs/en/v5/index.html)
- [TradingView](https://www.tradingview.com/) pour l'analyse technique

---

**Date de création**: 2025-07-24  
**Version**: 1.0  
**Auteur**: Assistant IA  
**Licence**: Éducative 