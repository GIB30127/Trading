# 🚀 Projet Trading - Optimisation de Stratégies

## 📁 Structure du Projet

```
Trad_Essay_Sven/
├── 📂 data/                    # Données de trading (CSV, MT5)
├── 📂 src/                     # Code source principal
│   ├── 📂 strategies/          # Stratégies de trading
│   ├── 📂 backtesting/         # Systèmes de backtest
│   ├── 📂 analysis/            # Outils d'analyse
│   └── 📂 utils/               # Utilitaires
├── 📂 scripts/                 # Scripts d'optimisation et utilitaires
├── 📂 docs/                    # Documentation
├── 📂 results/                 # Résultats des tests et analyses
├── 📂 Pine_Scripts/            # Scripts Pine Script originaux
└── 📂 config/                  # Configuration
```

## 🎯 Scripts Principaux

### 🧬 Optimisation
- `optimize.py` - Script principal d'optimisation
- `scripts/optimisation_genetique_drawdown.py` - Optimisation génétique
- `scripts/reinforcement_learning_optimizer.py` - RL pour optimisation
- `scripts/comparaison_optimisation.py` - Comparaison des méthodes

### 📊 Analyse et Tests
- `demo.py` - Script principal de démonstration
- `scripts/test_all_timeframes_xauusd.py` - Tests multi-timeframes
- `scripts/afficher_resultats_multitimeframes.py` - Affichage des résultats
- `scripts/analyse_strategie_auto.py` - Analyse automatique

## 🚀 Utilisation Rapide

### Optimisation
```bash
python optimize.py
```

### Démonstration
```bash
python demo.py
```

### Test Multi-Timeframes
```bash
python scripts/test_all_timeframes_xauusd.py
```

## 📈 Stratégies Disponibles

- **XAUUSD Sharpe 1 Simple** - Stratégie optimisée pour l'or
- **Multi-Timeframes** - Tests sur M5, M15, M30, H1, H4, D1
- **Optimisation Génétique** - Réduction du drawdown
- **Reinforcement Learning** - Adaptation en temps réel

## 📊 Résultats

Les résultats sont sauvegardés dans `results/` avec :
- Rapports d'analyse détaillés
- Graphiques interactifs
- Métriques de performance
- Optimisations par timeframe

## 🔧 Configuration

Vérifiez `config/requirements.txt` pour les dépendances.

## 📚 Documentation

- `docs/README_STRATEGIE_XAUUSD.md` - Documentation de la stratégie
- `docs/README_ANALYSE.md` - Guide d'analyse automatique

---
*Projet créé le: 2025-07-24*
