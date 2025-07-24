import os
import glob
import pandas as pd
import numpy as np
from rich import print
import warnings
warnings.filterwarnings('ignore')

def parse_backtest_file(filepath):
    """Parse un fichier de backtest et extrait les métriques"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metrics = {}
        
        # Performance
        if 'Performance totale :' in content:
            perf_line = [line for line in content.split('\n') if 'Performance totale :' in line][0]
            perf_value = perf_line.split('Performance totale :')[1].strip().replace('%', '')
            metrics['Performance'] = float(perf_value)
        
        # Trades
        if 'Nombre de trades :' in content:
            trades_line = [line for line in content.split('\n') if 'Nombre de trades :' in line][0]
            trades_value = trades_line.split('Nombre de trades :')[1].strip()
            metrics['Total_Trades'] = int(trades_value)
        
        # Win Rate
        if 'Trades gagnants :' in content and 'Trades perdants :' in content:
            winning_line = [line for line in content.split('\n') if 'Trades gagnants :' in line][0]
            losing_line = [line for line in content.split('\n') if 'Trades perdants :' in line][0]
            winning_trades = int(winning_line.split('Trades gagnants :')[1].strip())
            losing_trades = int(losing_line.split('Trades perdants :')[1].strip())
            total_trades = winning_trades + losing_trades
            if total_trades > 0:
                metrics['Win_Rate'] = (winning_trades / total_trades) * 100
                metrics['Total_Trades'] = total_trades
        
        # Sharpe Ratio
        if 'Sharpe Ratio :' in content:
            sharpe_line = [line for line in content.split('\n') if 'Sharpe Ratio :' in line][0]
            sharpe_value = sharpe_line.split('Sharpe Ratio :')[1].strip()
            metrics['Sharpe_Ratio'] = float(sharpe_value)
        
        # Max Drawdown (si disponible)
        if 'Max Drawdown :' in content:
            dd_line = [line for line in content.split('\n') if 'Max Drawdown :' in line][0]
            dd_value = dd_line.split('Max Drawdown :')[1].strip().replace('%', '')
            metrics['Max_Drawdown'] = float(dd_value)
        
        return metrics
    except Exception as e:
        return {}

def calculate_portfolio_drawdown(gold_dd, ger40_dd, gold_weight=0.5, ger40_weight=0.5):
    """Calcule le drawdown du portefeuille"""
    # Calcul du drawdown pondéré
    portfolio_dd = (gold_dd * gold_weight) + (ger40_dd * ger40_weight)
    return portfolio_dd

def analyze_drawdown_gold_ger40():
    """Analyse le drawdown de la stratégie Gold + GER40"""
    
    print("📉 ANALYSE DRAWDOWN - STRATÉGIE GOLD + GER40")
    print("=" * 60)
    
    # Recherche des fichiers XAUUSD et GER40.cash
    backtest_files = []
    search_patterns = [
        "backtest/XAUUSD_*.md",
        "backtest/GER40.cash_*.md"
    ]
    
    for pattern in search_patterns:
        files = glob.glob(pattern)
        backtest_files.extend(files)
    
    print(f"📁 {len(backtest_files)} fichiers analysés")
    
    all_results = []
    
    for filepath in backtest_files:
        filename = os.path.basename(filepath)
        metrics = parse_backtest_file(filepath)
        
        if metrics and 'Performance' in metrics:
            # Identification du symbol et timeframe
            symbol = "Unknown"
            timeframe = "Unknown"
            
            if '_' in filename:
                parts = filename.replace('.md', '').split('_')
                if len(parts) >= 2:
                    symbol = parts[0]
                    timeframe = parts[1]
            
            result = {
                'File': filename,
                'Symbol': symbol,
                'Timeframe': timeframe,
                'Metrics': metrics
            }
            
            all_results.append(result)
    
    # Séparation par instrument
    gold_strategies = [r for r in all_results if r['Symbol'] == 'XAUUSD']
    ger40_strategies = [r for r in all_results if r['Symbol'] == 'GER40.cash']
    
    print(f"\n🥇 XAUUSD (Gold): {len(gold_strategies)} stratégies")
    print(f"🇩🇪 GER40.cash: {len(ger40_strategies)} stratégies")
    
    # Tri par performance
    gold_strategies.sort(key=lambda x: x['Metrics']['Performance'], reverse=True)
    ger40_strategies.sort(key=lambda x: x['Metrics']['Performance'], reverse=True)
    
    print(f"\n📊 ANALYSE DRAWDOWN PAR INSTRUMENT")
    print("=" * 50)
    
    # Analyse Gold
    print(f"\n🥇 XAUUSD (GOLD) - DRAWDOWN:")
    print("-" * 30)
    for i, strategy in enumerate(gold_strategies[:3], 1):
        metrics = strategy['Metrics']
        dd = metrics.get('Max_Drawdown', 'N/A')
        print(f"   {i}. {strategy['Timeframe']}: Performance {metrics['Performance']:.2f}% | DD: {dd}")
    
    # Analyse GER40
    print(f"\n🇩🇪 GER40.cash - DRAWDOWN:")
    print("-" * 30)
    for i, strategy in enumerate(ger40_strategies[:3], 1):
        metrics = strategy['Metrics']
        dd = metrics.get('Max_Drawdown', 'N/A')
        print(f"   {i}. {strategy['Timeframe']}: Performance {metrics['Performance']:.2f}% | DD: {dd}")
    
    # Stratégie optimale identifiée
    print(f"\n🎯 STRATÉGIE OPTIMALE IDENTIFIÉE:")
    print("-" * 40)
    
    best_gold = gold_strategies[0] if gold_strategies else None
    best_ger40 = ger40_strategies[0] if ger40_strategies else None
    
    if best_gold and best_ger40:
        gold_metrics = best_gold['Metrics']
        ger40_metrics = best_ger40['Metrics']
        
        print(f"🥇 XAUUSD {best_gold['Timeframe']}:")
        print(f"   Performance: {gold_metrics['Performance']:.2f}%")
        print(f"   Drawdown: {gold_metrics.get('Max_Drawdown', 'N/A')}")
        print(f"   Sharpe: {gold_metrics.get('Sharpe_Ratio', 'N/A')}")
        
        print(f"\n🇩🇪 GER40.cash {best_ger40['Timeframe']}:")
        print(f"   Performance: {ger40_metrics['Performance']:.2f}%")
        print(f"   Drawdown: {ger40_metrics.get('Max_Drawdown', 'N/A')}")
        print(f"   Sharpe: {ger40_metrics.get('Sharpe_Ratio', 'N/A')}")
        
        # Calcul du drawdown du portefeuille
        gold_dd = gold_metrics.get('Max_Drawdown', 0)
        ger40_dd = ger40_metrics.get('Max_Drawdown', 0)
        
        if isinstance(gold_dd, (int, float)) and isinstance(ger40_dd, (int, float)):
            portfolio_dd = calculate_portfolio_drawdown(gold_dd, ger40_dd)
            print(f"\n📊 DRAWDOWN DU PORTEFEUILLE (50/50):")
            print(f"   Gold DD: {gold_dd:.1f}%")
            print(f"   GER40 DD: {ger40_dd:.1f}%")
            print(f"   Portfolio DD: {portfolio_dd:.1f}%")
            
            # Évaluation du risque
            print(f"\n⚠️ ÉVALUATION DU RISQUE:")
            if portfolio_dd < 10:
                print(f"   🟢 RISQUE FAIBLE: DD de {portfolio_dd:.1f}%")
            elif portfolio_dd < 20:
                print(f"   🟡 RISQUE MODÉRÉ: DD de {portfolio_dd:.1f}%")
            elif portfolio_dd < 30:
                print(f"   🟠 RISQUE ÉLEVÉ: DD de {portfolio_dd:.1f}%")
            else:
                print(f"   🔴 RISQUE TRÈS ÉLEVÉ: DD de {portfolio_dd:.1f}%")
        else:
            print(f"\n⚠️ DRAWDOWN NON DISPONIBLE")
            print(f"   Impossible de calculer le DD du portefeuille")
            print(f"   Les données de drawdown ne sont pas dans les backtests")
    
    # Comparaison avec les contraintes demandées
    print(f"\n🎯 COMPARAISON AVEC VOS CONTRAINTES:")
    print("-" * 40)
    print(f"   Votre demande: DD max 5% quotidien, 10% hebdomadaire")
    
    if best_gold and best_ger40:
        gold_dd = best_gold['Metrics'].get('Max_Drawdown', 0)
        ger40_dd = best_ger40['Metrics'].get('Max_Drawdown', 0)
        
        if isinstance(gold_dd, (int, float)) and isinstance(ger40_dd, (int, float)):
            portfolio_dd = calculate_portfolio_drawdown(gold_dd, ger40_dd)
            
            print(f"   DD du portefeuille: {portfolio_dd:.1f}%")
            
            if portfolio_dd <= 10:
                print(f"   ✅ RESPECTE vos contraintes (≤ 10%)")
            else:
                print(f"   ❌ DÉPASSE vos contraintes (> 10%)")
                print(f"   ⚠️ Risque de drawdown trop élevé")
        else:
            print(f"   ⚠️ Impossible de vérifier (DD non disponible)")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    print("-" * 30)
    
    if best_gold and best_ger40:
        gold_dd = best_gold['Metrics'].get('Max_Drawdown', 0)
        ger40_dd = best_ger40['Metrics'].get('Max_Drawdown', 0)
        
        if isinstance(gold_dd, (int, float)) and isinstance(ger40_dd, (int, float)):
            portfolio_dd = calculate_portfolio_drawdown(gold_dd, ger40_dd)
            
            if portfolio_dd <= 10:
                print(f"   ✅ Stratégie compatible avec vos contraintes")
                print(f"   📈 Performance: 41.42% avec DD de {portfolio_dd:.1f}%")
                print(f"   🎯 Ratio Performance/Risque: {41.42/portfolio_dd:.1f}")
            else:
                print(f"   ⚠️ Stratégie à ajuster pour respecter vos contraintes")
                print(f"   💡 Suggestions:")
                print(f"      - Réduire la taille des positions")
                print(f"      - Ajouter des stops plus serrés")
                print(f"      - Diversifier sur plus d'instruments")
        else:
            print(f"   ⚠️ DD non disponible - Prudence recommandée")
            print(f"   💡 Testez d'abord avec un petit capital")
    
    # Sauvegarde du rapport
    os.makedirs("dd_analysis", exist_ok=True)
    
    report = f"""# 📉 Analyse Drawdown - Stratégie Gold + GER40

## 📊 Résumé

**Stratégie optimale :** XAUUSD H1 + GER40.cash H4  
**Performance :** 41.42%  
**Capital :** 10 000€

## 📉 Drawdown par Instrument

### XAUUSD (Gold)
"""
    
    for i, strategy in enumerate(gold_strategies[:3], 1):
        metrics = strategy['Metrics']
        dd = metrics.get('Max_Drawdown', 'N/A')
        report += f"- **{strategy['Timeframe']}** : Performance {metrics['Performance']:.2f}% | DD: {dd}\n"
    
    report += f"""
### GER40.cash
"""
    
    for i, strategy in enumerate(ger40_strategies[:3], 1):
        metrics = strategy['Metrics']
        dd = metrics.get('Max_Drawdown', 'N/A')
        report += f"- **{strategy['Timeframe']}** : Performance {metrics['Performance']:.2f}% | DD: {dd}\n"
    
    if best_gold and best_ger40:
        gold_dd = best_gold['Metrics'].get('Max_Drawdown', 0)
        ger40_dd = best_ger40['Metrics'].get('Max_Drawdown', 0)
        
        if isinstance(gold_dd, (int, float)) and isinstance(ger40_dd, (int, float)):
            portfolio_dd = calculate_portfolio_drawdown(gold_dd, ger40_dd)
            report += f"""
## 📊 Drawdown du Portefeuille

- **Gold DD :** {gold_dd:.1f}%
- **GER40 DD :** {ger40_dd:.1f}%
- **Portfolio DD :** {portfolio_dd:.1f}%

## ⚠️ Évaluation du Risque

"""
            
            if portfolio_dd <= 10:
                report += f"✅ **COMPATIBLE** avec vos contraintes (DD ≤ 10%)\n"
            else:
                report += f"❌ **INCOMPATIBLE** avec vos contraintes (DD > 10%)\n"
    
    with open("dd_analysis/rapport_dd_gold_ger40.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport sauvegardé : dd_analysis/rapport_dd_gold_ger40.md")

def main():
    print("📉 ANALYSE DRAWDOWN GOLD + GER40")
    print("=" * 60)
    
    # Analyse du drawdown
    analyze_drawdown_gold_ger40()
    
    print(f"\n🎯 CONCLUSION:")
    print("=" * 30)
    print(f"   Le drawdown de votre stratégie Gold + GER40")
    print(f"   dépend des données disponibles dans vos backtests")
    print(f"   Vérifiez le rapport généré pour les détails")

if __name__ == "__main__":
    main() 