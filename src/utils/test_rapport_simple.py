import os
import glob

def parse_simple_backtest(filepath):
    """Parse simple d'un fichier de backtest"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metrics = {}
        
        # Performance
        if 'Performance totale :' in content:
            perf_line = [line for line in content.split('\n') if 'Performance totale :' in line][0]
            perf_value = perf_line.split('Performance totale :')[1].strip().replace('%', '')
            metrics['Performance'] = float(perf_value)
            print(f"✅ Performance trouvée: {perf_value}%")
        
        # Trades
        if 'Nombre de trades :' in content:
            trades_line = [line for line in content.split('\n') if 'Nombre de trades :' in line][0]
            trades_value = trades_line.split('Nombre de trades :')[1].strip()
            metrics['Total_Trades'] = int(trades_value)
            print(f"✅ Trades trouvés: {trades_value}")
        
        # Win Rate
        if 'Trades gagnants :' in content and 'Trades perdants :' in content:
            winning_line = [line for line in content.split('\n') if 'Trades gagnants :' in line][0]
            losing_line = [line for line in content.split('\n') if 'Trades perdants :' in line][0]
            winning_trades = int(winning_line.split('Trades gagnants :')[1].strip())
            losing_trades = int(losing_line.split('Trades perdants :')[1].strip())
            total_trades = winning_trades + losing_trades
            if total_trades > 0:
                metrics['Win_Rate'] = (winning_trades / total_trades) * 100
                print(f"✅ Win Rate calculé: {metrics['Win_Rate']:.1f}%")
        
        return metrics
    except Exception as e:
        print(f"❌ Erreur parsing {filepath}: {e}")
        return {}

def main():
    print("🧪 Test Simple de Parsing des Backtests")
    print("=" * 50)
    
    # Test avec un seul fichier
    test_file = "backtest/XAUUSD_D1_backtest.md"
    if os.path.exists(test_file):
        print(f"📄 Test du fichier: {test_file}")
        metrics = parse_simple_backtest(test_file)
        
        if metrics:
            print(f"\n📊 Métriques extraites:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
            
            # Calcul avec 10 000€
            if 'Performance' in metrics:
                performance = metrics['Performance']
                final_capital = 10000 * (1 + performance / 100)
                annual_return = final_capital - 10000
                print(f"\n💰 Avec 10 000€:")
                print(f"   Capital final: {final_capital:,.0f}€")
                print(f"   Gain: {annual_return:,.0f}€")
        else:
            print("❌ Aucune métrique trouvée")
    else:
        print(f"❌ Fichier {test_file} non trouvé")

if __name__ == "__main__":
    main() 