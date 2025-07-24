import os
import pandas as pd
import numpy as np
import glob
from rich import print
import warnings
warnings.filterwarnings('ignore')

def parse_backtest_file(filepath):
    """Parse un fichier de backtest et extrait les métriques"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraction des métriques clés
        metrics = {}
        
        # Performance (format: "Performance totale : 27.31%")
        if 'Performance totale :' in content:
            perf_line = [line for line in content.split('\n') if 'Performance totale :' in line][0]
            perf_value = perf_line.split('Performance totale :')[1].strip().replace('%', '')
            metrics['Performance'] = float(perf_value)
        
        # Trades (format: "Nombre de trades : 220")
        if 'Nombre de trades :' in content:
            trades_line = [line for line in content.split('\n') if 'Nombre de trades :' in line][0]
            trades_value = trades_line.split('Nombre de trades :')[1].strip()
            metrics['Total_Trades'] = int(trades_value)
        
        # Trades gagnants/perdants pour calculer win rate
        if 'Trades gagnants :' in content and 'Trades perdants :' in content:
            winning_line = [line for line in content.split('\n') if 'Trades gagnants :' in line][0]
            losing_line = [line for line in content.split('\n') if 'Trades perdants :' in line][0]
            winning_trades = int(winning_line.split('Trades gagnants :')[1].strip())
            losing_trades = int(losing_line.split('Trades perdants :')[1].strip())
            total_trades = winning_trades + losing_trades
            if total_trades > 0:
                metrics['Win_Rate'] = (winning_trades / total_trades) * 100
                metrics['Total_Trades'] = total_trades
        
        # Sharpe Ratio (format: "Sharpe Ratio : 0.71")
        if 'Sharpe Ratio :' in content:
            sharpe_line = [line for line in content.split('\n') if 'Sharpe Ratio :' in line][0]
            sharpe_value = sharpe_line.split('Sharpe Ratio :')[1].strip()
            metrics['Sharpe_Ratio'] = float(sharpe_value)
        
        # Max Drawdown (format: "Max Drawdown : 15.2%")
        if 'Max Drawdown :' in content:
            dd_line = [line for line in content.split('\n') if 'Max Drawdown :' in line][0]
            dd_value = dd_line.split('Max Drawdown :')[1].strip().replace('%', '')
            metrics['Max_Drawdown'] = float(dd_value)
        
        # Profit Factor (format: "Profit Factor : 1.25")
        if 'Profit Factor :' in content:
            pf_line = [line for line in content.split('\n') if 'Profit Factor :' in line][0]
            pf_value = pf_line.split('Profit Factor :')[1].strip()
            metrics['Profit_Factor'] = float(pf_value)
        
        # Calmar Ratio (format: "Calmar Ratio : 0.85")
        if 'Calmar Ratio :' in content:
            calmar_line = [line for line in content.split('\n') if 'Calmar Ratio :' in line][0]
            calmar_value = calmar_line.split('Calmar Ratio :')[1].strip()
            metrics['Calmar_Ratio'] = float(calmar_value)
        
        return metrics
    except Exception as e:
        print(f"Erreur parsing {filepath}: {e}")
        return {}

def calculate_annual_returns(performance_pct, initial_capital=10000):
    """Calcule les retours annuels avec capital initial"""
    performance_decimal = performance_pct / 100
    final_capital = initial_capital * (1 + performance_decimal)
    annual_return = final_capital - initial_capital
    return {
        'Initial_Capital': initial_capital,
        'Final_Capital': final_capital,
        'Annual_Return': annual_return,
        'ROI_Percentage': performance_pct
    }

def analyze_all_backtests():
    """Analyse tous les fichiers de backtest disponibles"""
    
    print("💰 Analyse de Rentabilité - Budget 10 000€")
    print("=" * 60)
    
    # Recherche de tous les fichiers de backtest
    backtest_files = []
    
    # Dossiers à scanner
    search_paths = [
        "backtest/*.md",
        "final_results/*.md", 
        "capital_preservation_results/*.md",
        "price_action_results/*.md",
        "simple_backtests/*.md",
        "optimized_backtests/*.md"
    ]
    
    for pattern in search_paths:
        files = glob.glob(pattern)
        backtest_files.extend(files)
    
    print(f"📁 {len(backtest_files)} fichiers de backtest trouvés")
    
    all_results = []
    
    for filepath in backtest_files:
        # Extraction du nom du fichier pour identifier symbol/timeframe
        filename = os.path.basename(filepath)
        
        # Parsing du fichier
        metrics = parse_backtest_file(filepath)
        
        print(f"📄 {filename}: {len(metrics)} métriques trouvées")
        if metrics:
            print(f"   Performance: {metrics.get('Performance', 'N/A')}")
            print(f"   Trades: {metrics.get('Total_Trades', 'N/A')}")
        
        if metrics and 'Performance' in metrics:
            # Calcul des retours avec 10 000€
            returns = calculate_annual_returns(metrics['Performance'])
            
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
                'Metrics': metrics,
                'Returns': returns
            }
            
            all_results.append(result)
    
    return all_results

def generate_comprehensive_report(all_results):
    """Génère un rapport complet"""
    
    if not all_results:
        print("❌ Aucun résultat de backtest trouvé")
        return
    
    print(f"\n📊 ANALYSE COMPLÈTE - {len(all_results)} Stratégies")
    print("=" * 60)
    
    # Tri par performance
    sorted_by_performance = sorted(all_results, key=lambda x: x['Returns']['Annual_Return'], reverse=True)
    
    print(f"\n🥇 TOP 10 PAR RENTABILITÉ (10 000€ initial) :")
    print("-" * 80)
    for i, result in enumerate(sorted_by_performance[:10], 1):
        returns = result['Returns']
        metrics = result['Metrics']
        print(f"{i:2d}. {result['Symbol']} {result['Timeframe']}")
        print(f"     💰 Capital final: {returns['Final_Capital']:,.0f}€ (+{returns['Annual_Return']:,.0f}€)")
        print(f"     📈 Performance: {returns['ROI_Percentage']:.2f}% | Trades: {metrics.get('Total_Trades', 'N/A')}")
        win_rate = metrics.get('Win_Rate', 'N/A')
        sharpe = metrics.get('Sharpe_Ratio', 'N/A')
        if isinstance(win_rate, (int, float)):
            win_rate_str = f"{win_rate:.1f}%"
        else:
            win_rate_str = str(win_rate)
        if isinstance(sharpe, (int, float)):
            sharpe_str = f"{sharpe:.2f}"
        else:
            sharpe_str = str(sharpe)
        print(f"     🎯 Win Rate: {win_rate_str} | Sharpe: {sharpe_str}")
        max_dd = metrics.get('Max_Drawdown', 'N/A')
        if isinstance(max_dd, (int, float)):
            print(f"     📉 Max DD: {max_dd:.1f}%")
        else:
            print(f"     📉 Max DD: {max_dd}")
        print()
    
    # Statistiques globales
    total_return = sum([r['Returns']['Annual_Return'] for r in all_results])
    avg_return = np.mean([r['Returns']['Annual_Return'] for r in all_results])
    avg_performance = np.mean([r['Returns']['ROI_Percentage'] for r in all_results])
    avg_drawdown = np.mean([r['Metrics'].get('Max_Drawdown', 0) for r in all_results])
    
    profitable_strategies = [r for r in all_results if r['Returns']['Annual_Return'] > 0]
    loss_making_strategies = [r for r in all_results if r['Returns']['Annual_Return'] < 0]
    
    print(f"📊 STATISTIQUES GLOBALES :")
    print("-" * 40)
    print(f"   💰 Retour total si on investit 10 000€ dans chaque stratégie: {total_return:,.0f}€")
    print(f"   📈 Retour moyen par stratégie: {avg_return:,.0f}€")
    print(f"   🎯 Performance moyenne: {avg_performance:.2f}%")
    print(f"   📉 Drawdown moyen: {avg_drawdown:.1f}%")
    print(f"   ✅ Stratégies rentables: {len(profitable_strategies)}/{len(all_results)} ({len(profitable_strategies)/len(all_results)*100:.1f}%)")
    print(f"   ❌ Stratégies perdantes: {len(loss_making_strategies)}/{len(all_results)} ({len(loss_making_strategies)/len(all_results)*100:.1f}%)")
    
    # Meilleures stratégies par instrument
    print(f"\n🏆 MEILLEURES STRATÉGIES PAR INSTRUMENT :")
    print("-" * 50)
    
    symbols = list(set([r['Symbol'] for r in all_results]))
    for symbol in symbols:
        symbol_results = [r for r in all_results if r['Symbol'] == symbol]
        if symbol_results:
            best_symbol = max(symbol_results, key=lambda x: x['Returns']['Annual_Return'])
            returns = best_symbol['Returns']
            metrics = best_symbol['Metrics']
            print(f"   {symbol}: {best_symbol['Timeframe']} → {returns['Final_Capital']:,.0f}€ (+{returns['Annual_Return']:,.0f}€)")
    
    # Stratégies avec faible drawdown
    low_dd_strategies = [r for r in all_results if r['Metrics'].get('Max_Drawdown', 999) < 20]
    if low_dd_strategies:
        print(f"\n🛡️ STRATÉGIES AVEC FAIBLE DRAWDOWN (<20%) :")
        print("-" * 50)
        for result in sorted(low_dd_strategies, key=lambda x: x['Returns']['Annual_Return'], reverse=True)[:5]:
            returns = result['Returns']
            metrics = result['Metrics']
            max_dd = metrics.get('Max_Drawdown', 'N/A')
        if isinstance(max_dd, (int, float)):
            dd_str = f"{max_dd:.1f}%"
        else:
            dd_str = str(max_dd)
        print(f"   {result['Symbol']} {result['Timeframe']}: {returns['Final_Capital']:,.0f}€ (DD: {dd_str})")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS :")
    print("-" * 30)
    
    if profitable_strategies:
        best_overall = max(profitable_strategies, key=lambda x: x['Returns']['Annual_Return'])
        best_risk_adjusted = max(profitable_strategies, key=lambda x: x['Metrics'].get('Sharpe_Ratio', 0))
        
        print(f"   🥇 Meilleure performance: {best_overall['Symbol']} {best_overall['Timeframe']}")
        print(f"      → {best_overall['Returns']['Final_Capital']:,.0f}€ (+{best_overall['Returns']['Annual_Return']:,.0f}€)")
        
        print(f"   🎯 Meilleur ratio risque/récompense: {best_risk_adjusted['Symbol']} {best_risk_adjusted['Timeframe']}")
        print(f"      → Sharpe: {best_risk_adjusted['Metrics'].get('Sharpe_Ratio', 'N/A'):.2f}")
    
    # Sauvegarde du rapport
    os.makedirs("rapport_rentabilite", exist_ok=True)
    
    report = f"""# 💰 Rapport de Rentabilité - Budget 10 000€

## 📊 Résumé Exécutif

**Capital initial :** 10 000€  
**Nombre de stratégies analysées :** {len(all_results)}  
**Retour total si investissement dans toutes les stratégies :** {total_return:,.0f}€  
**Performance moyenne :** {avg_performance:.2f}%  
**Stratégies rentables :** {len(profitable_strategies)}/{len(all_results)} ({len(profitable_strategies)/len(all_results)*100:.1f}%)

## 🥇 Top 10 Stratégies

"""
    
    for i, result in enumerate(sorted_by_performance[:10], 1):
        returns = result['Returns']
        metrics = result['Metrics']
        report += f"### {i}. {result['Symbol']} {result['Timeframe']}\n"
        report += f"- **Capital final :** {returns['Final_Capital']:,.0f}€ (+{returns['Annual_Return']:,.0f}€)\n"
        report += f"- **Performance :** {returns['ROI_Percentage']:.2f}%\n"
        report += f"- **Trades :** {metrics.get('Total_Trades', 'N/A')}\n"
        report += f"- **Win Rate :** {metrics.get('Win_Rate', 'N/A'):.1f}%\n"
        report += f"- **Sharpe Ratio :** {metrics.get('Sharpe_Ratio', 'N/A'):.2f}\n"
        max_dd = metrics.get('Max_Drawdown', 'N/A')
        if isinstance(max_dd, (int, float)):
            dd_str = f"{max_dd:.1f}%"
        else:
            dd_str = str(max_dd)
        report += f"- **Max Drawdown :** {dd_str}\n\n"
    
    report += f"""## 📈 Statistiques Détaillées

### Par Instrument
"""
    
    for symbol in symbols:
        symbol_results = [r for r in all_results if r['Symbol'] == symbol]
        if symbol_results:
            best_symbol = max(symbol_results, key=lambda x: x['Returns']['Annual_Return'])
            returns = best_symbol['Returns']
            report += f"- **{symbol}** : {best_symbol['Timeframe']} → {returns['Final_Capital']:,.0f}€ (+{returns['Annual_Return']:,.0f}€)\n"
    
    report += f"""
### Stratégies Conservatrices (DD < 20%)
"""
    
    for result in sorted(low_dd_strategies, key=lambda x: x['Returns']['Annual_Return'], reverse=True)[:5]:
        returns = result['Returns']
        metrics = result['Metrics']
        max_dd = metrics.get('Max_Drawdown', 'N/A')
        if isinstance(max_dd, (int, float)):
            dd_str = f"{max_dd:.1f}%"
        else:
            dd_str = str(max_dd)
        report += f"- **{result['Symbol']} {result['Timeframe']}** : {returns['Final_Capital']:,.0f}€ (DD: {dd_str})\n"
    
    with open("rapport_rentabilite/rapport_complet_10000e.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport sauvegardé : rapport_rentabilite/rapport_complet_10000e.md")

def main():
    print("💰 ANALYSE DE RENTABILITÉ - BUDGET 10 000€")
    print("=" * 60)
    
    # Analyse de tous les backtests
    all_results = analyze_all_backtests()
    
    # Génération du rapport
    generate_comprehensive_report(all_results)
    
    print(f"\n🎯 CONCLUSION :")
    print("=" * 30)
    if all_results:
        profitable_count = len([r for r in all_results if r['Returns']['Annual_Return'] > 0])
        print(f"   Avec 10 000€ par stratégie, vous avez {profitable_count} stratégies rentables")
        print(f"   sur {len(all_results)} stratégies testées")
        
        if profitable_count > 0:
            best_strategy = max(all_results, key=lambda x: x['Returns']['Annual_Return'])
            print(f"   La meilleure stratégie rapporte {best_strategy['Returns']['Annual_Return']:,.0f}€")
            print(f"   sur un an avec {best_strategy['Symbol']} {best_strategy['Timeframe']}")
    else:
        print("   Aucun backtest disponible pour l'analyse")

if __name__ == "__main__":
    main() 