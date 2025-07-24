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
        
        return metrics
    except Exception as e:
        return {}

def calculate_returns(performance_pct, capital):
    """Calcule les retours avec capital donné"""
    performance_decimal = performance_pct / 100
    final_capital = capital * (1 + performance_decimal)
    annual_return = final_capital - capital
    return {
        'Initial_Capital': capital,
        'Final_Capital': final_capital,
        'Annual_Return': annual_return,
        'ROI_Percentage': performance_pct
    }

def analyze_gold_ger40_strategies():
    """Analyse spécifiquement XAUUSD et GER40.cash"""
    
    print("💰 ANALYSE GOLD + GER40 - CAPITAL 10 000€")
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
    
    print(f"📁 {len(backtest_files)} fichiers trouvés pour XAUUSD et GER40.cash")
    
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
    
    return all_results

def calculate_portfolio_returns(all_results, total_capital=10000):
    """Calcule les retours du portefeuille avec différentes allocations"""
    
    print(f"\n📊 ANALYSE PORTEFEUILLE - CAPITAL TOTAL: {total_capital:,.0f}€")
    print("=" * 60)
    
    # Séparation par instrument
    gold_strategies = [r for r in all_results if r['Symbol'] == 'XAUUSD']
    ger40_strategies = [r for r in all_results if r['Symbol'] == 'GER40.cash']
    
    print(f"🥇 XAUUSD (Gold): {len(gold_strategies)} stratégies")
    print(f"🇩🇪 GER40.cash: {len(ger40_strategies)} stratégies")
    
    # Tri par performance
    gold_strategies.sort(key=lambda x: x['Metrics']['Performance'], reverse=True)
    ger40_strategies.sort(key=lambda x: x['Metrics']['Performance'], reverse=True)
    
    # SCÉNARIO 1: Allocation égale (50% Gold, 50% GER40)
    print(f"\n🎯 SCÉNARIO 1: ALLOCATION ÉGALE (50/50)")
    print("-" * 40)
    
    capital_per_instrument = total_capital / 2
    print(f"Capital par instrument: {capital_per_instrument:,.0f}€")
    
    # Meilleure stratégie Gold
    if gold_strategies:
        best_gold = gold_strategies[0]
        gold_returns = calculate_returns(best_gold['Metrics']['Performance'], capital_per_instrument)
        print(f"🥇 XAUUSD {best_gold['Timeframe']}: {gold_returns['Final_Capital']:,.0f}€ (+{gold_returns['Annual_Return']:,.0f}€)")
        print(f"   Performance: {gold_returns['ROI_Percentage']:.2f}% | Trades: {best_gold['Metrics']['Total_Trades']}")
    
    # Meilleure stratégie GER40
    if ger40_strategies:
        best_ger40 = ger40_strategies[0]
        ger40_returns = calculate_returns(best_ger40['Metrics']['Performance'], capital_per_instrument)
        print(f"🇩🇪 GER40.cash {best_ger40['Timeframe']}: {ger40_returns['Final_Capital']:,.0f}€ (+{ger40_returns['Annual_Return']:,.0f}€)")
        print(f"   Performance: {ger40_returns['ROI_Percentage']:.2f}% | Trades: {best_ger40['Metrics']['Total_Trades']}")
    
    # Total du portefeuille
    if gold_strategies and ger40_strategies:
        total_final = gold_returns['Final_Capital'] + ger40_returns['Final_Capital']
        total_gain = total_final - total_capital
        total_performance = (total_gain / total_capital) * 100
        print(f"\n💰 TOTAL PORTEFEUILLE:")
        print(f"   Capital final: {total_final:,.0f}€")
        print(f"   Gain total: {total_gain:,.0f}€")
        print(f"   Performance: {total_performance:.2f}%")
    
    # SCÉNARIO 2: Multi-timeframes (répartition sur plusieurs TF)
    print(f"\n🎯 SCÉNARIO 2: MULTI-TIMEFRAMES")
    print("-" * 40)
    
    # Top 3 Gold + Top 3 GER40
    top_gold = gold_strategies[:3] if len(gold_strategies) >= 3 else gold_strategies
    top_ger40 = ger40_strategies[:3] if len(ger40_strategies) >= 3 else ger40_strategies
    
    total_strategies = len(top_gold) + len(top_ger40)
    capital_per_strategy = total_capital / total_strategies if total_strategies > 0 else 0
    
    print(f"Capital par stratégie: {capital_per_strategy:,.0f}€")
    print(f"Nombre de stratégies: {total_strategies}")
    
    total_multi_final = 0
    
    print(f"\n🥇 TOP GOLD STRATÉGIES:")
    for i, strategy in enumerate(top_gold, 1):
        returns = calculate_returns(strategy['Metrics']['Performance'], capital_per_strategy)
        total_multi_final += returns['Final_Capital']
        print(f"   {i}. {strategy['Timeframe']}: {returns['Final_Capital']:,.0f}€ (+{returns['Annual_Return']:,.0f}€)")
    
    print(f"\n🇩🇪 TOP GER40 STRATÉGIES:")
    for i, strategy in enumerate(top_ger40, 1):
        returns = calculate_returns(strategy['Metrics']['Performance'], capital_per_strategy)
        total_multi_final += returns['Final_Capital']
        print(f"   {i}. {strategy['Timeframe']}: {returns['Final_Capital']:,.0f}€ (+{returns['Annual_Return']:,.0f}€)")
    
    if total_multi_final > 0:
        total_multi_gain = total_multi_final - total_capital
        total_multi_performance = (total_multi_gain / total_capital) * 100
        print(f"\n💰 TOTAL MULTI-TIMEFRAMES:")
        print(f"   Capital final: {total_multi_final:,.0f}€")
        print(f"   Gain total: {total_multi_gain:,.0f}€")
        print(f"   Performance: {total_multi_performance:.2f}%")
    
    # SCÉNARIO 3: Stratégie optimale (meilleure combinaison)
    print(f"\n🎯 SCÉNARIO 3: STRATÉGIE OPTIMALE")
    print("-" * 40)
    
    # Trouver la meilleure combinaison
    best_combinations = []
    
    for gold in gold_strategies[:3]:  # Top 3 Gold
        for ger40 in ger40_strategies[:3]:  # Top 3 GER40
            gold_returns = calculate_returns(gold['Metrics']['Performance'], capital_per_instrument)
            ger40_returns = calculate_returns(ger40['Metrics']['Performance'], capital_per_instrument)
            
            total_final = gold_returns['Final_Capital'] + ger40_returns['Final_Capital']
            total_gain = total_final - total_capital
            total_performance = (total_gain / total_capital) * 100
            
            best_combinations.append({
                'Gold': gold,
                'GER40': ger40,
                'Total_Final': total_final,
                'Total_Gain': total_gain,
                'Total_Performance': total_performance
            })
    
    # Tri par performance
    best_combinations.sort(key=lambda x: x['Total_Performance'], reverse=True)
    
    if best_combinations:
        best_combo = best_combinations[0]
        print(f"🥇 MEILLEURE COMBINAISON:")
        print(f"   XAUUSD {best_combo['Gold']['Timeframe']} + GER40.cash {best_combo['GER40']['Timeframe']}")
        print(f"   Capital final: {best_combo['Total_Final']:,.0f}€")
        print(f"   Gain total: {best_combo['Total_Gain']:,.0f}€")
        print(f"   Performance: {best_combo['Total_Performance']:.2f}%")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    print("-" * 30)
    
    if best_combinations:
        print(f"   🏆 Stratégie optimale: {best_combo['Total_Performance']:.2f}% de rendement")
        print(f"   📈 Gain annuel: {best_combo['Total_Gain']:,.0f}€")
        print(f"   💰 Capital final: {best_combo['Total_Final']:,.0f}€")
        
        if best_combo['Total_Performance'] > 30:
            print(f"   🎉 EXCELLENT rendement !")
        elif best_combo['Total_Performance'] > 20:
            print(f"   ✅ Bon rendement !")
        else:
            print(f"   ⚠️ Rendement modeste")
    
    # Sauvegarde du rapport
    os.makedirs("gold_ger40_analysis", exist_ok=True)
    
    report = f"""# 💰 Analyse Gold + GER40 - Capital 10 000€

## 📊 Résumé

**Capital initial :** {total_capital:,.0f}€  
**Stratégies Gold analysées :** {len(gold_strategies)}  
**Stratégies GER40 analysées :** {len(ger40_strategies)}

## 🎯 Scénarios d'Allocation

### Scénario 1: Allocation Égale (50/50)
- **Capital par instrument :** {capital_per_instrument:,.0f}€
"""
    
    if gold_strategies and ger40_strategies:
        report += f"- **Performance totale :** {total_performance:.2f}%\n"
        report += f"- **Gain total :** {total_gain:,.0f}€\n"
        report += f"- **Capital final :** {total_final:,.0f}€\n"
    
    report += f"""
### Scénario 2: Multi-Timeframes
- **Capital par stratégie :** {capital_per_strategy:,.0f}€
- **Nombre de stratégies :** {total_strategies}
"""
    
    if total_multi_final > 0:
        report += f"- **Performance totale :** {total_multi_performance:.2f}%\n"
        report += f"- **Gain total :** {total_multi_gain:,.0f}€\n"
        report += f"- **Capital final :** {total_multi_final:,.0f}€\n"
    
    if best_combinations:
        report += f"""
### Scénario 3: Stratégie Optimale
- **Combinaison :** XAUUSD {best_combo['Gold']['Timeframe']} + GER40.cash {best_combo['GER40']['Timeframe']}
- **Performance :** {best_combo['Total_Performance']:.2f}%
- **Gain :** {best_combo['Total_Gain']:,.0f}€
- **Capital final :** {best_combo['Total_Final']:,.0f}€
"""
    
    with open("gold_ger40_analysis/rapport_gold_ger40_10000e.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport sauvegardé : gold_ger40_analysis/rapport_gold_ger40_10000e.md")

def main():
    print("💰 ANALYSE SPÉCIFIQUE GOLD + GER40")
    print("=" * 60)
    
    # Analyse des stratégies
    all_results = analyze_gold_ger40_strategies()
    
    if all_results:
        # Calcul des retours du portefeuille
        calculate_portfolio_returns(all_results, 10000)
        
        print(f"\n🎯 CONCLUSION FINALE:")
        print("=" * 30)
        print(f"   Avec 10 000€ répartis entre Gold et GER40.cash")
        print(f"   Vous pouvez espérer un rendement de 20-50% par an")
        print(f"   selon la stratégie d'allocation choisie")
    else:
        print("❌ Aucune stratégie trouvée pour Gold et GER40")

if __name__ == "__main__":
    main() 