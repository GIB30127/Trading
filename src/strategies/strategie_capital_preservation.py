import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from rich import print
import warnings
warnings.filterwarnings('ignore')

def compute_atr(df, window):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def strategie_capital_preservation(df, symbol, timeframe):
    """Stratégie qui priorise la préservation du capital"""
    
    df = df.copy()
    
    # Paramètres CONSERVATEURS pour préserver le capital
    if symbol == 'XAUUSD':
        breakout_period = 15
        risk_atr = 1.0  # Stop très serré
        profit_atr = 2.0  # Objectif modeste mais réaliste
        rsi_overbought = 70
        rsi_oversold = 30
        max_consecutive_losses = 3  # Stop après 3 pertes consécutives
    elif symbol == 'US30.cash':
        breakout_period = 12
        risk_atr = 0.8
        profit_atr = 1.8
        rsi_overbought = 70
        rsi_oversold = 30
        max_consecutive_losses = 3
    elif symbol == 'EURUSD':
        breakout_period = 10
        risk_atr = 0.7
        profit_atr = 1.5
        rsi_overbought = 70
        rsi_oversold = 30
        max_consecutive_losses = 2
    else:  # GER40.cash
        breakout_period = 10
        risk_atr = 0.8
        profit_atr = 1.6
        rsi_overbought = 70
        rsi_oversold = 30
        max_consecutive_losses = 3
    
    # Ajustement timeframe conservateur
    if timeframe == 'D1':
        breakout_period = int(breakout_period * 1.2)
        risk_atr *= 1.1
        profit_atr *= 1.1
    elif timeframe == 'H1':
        breakout_period = int(breakout_period * 0.9)
        risk_atr *= 0.9
        profit_atr *= 0.9
    
    # Indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['RSI'] = compute_rsi(df, 14)
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    
    # Breakouts
    df['High_Break'] = df['High'].rolling(window=breakout_period).max()
    df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
    
    # Volume
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_OK'] = df['Volume'] > df['Volume_MA'] * 0.8
    
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trades = []
    
    # Gestion du risque strict
    consecutive_losses = 0
    daily_pnl = 0
    weekly_pnl = 0
    last_date = None
    last_week = None
    
    # Contraintes de drawdown
    max_daily_dd = 0.02  # 2% max par jour
    max_weekly_dd = 0.05  # 5% max par semaine
    max_total_dd = 0.10   # 10% max total

    for i in range(1, len(df)):
        current_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
        
        # Reset quotidien
        if last_date is None or str(current_date)[:10] != str(last_date)[:10]:
            daily_pnl = 0
            last_date = current_date
        
        # Reset hebdomadaire
        if last_week is None or pd.to_datetime(current_date).isocalendar()[1] != last_week:
            weekly_pnl = 0
            last_week = pd.to_datetime(current_date).isocalendar()[1]
        
        # Vérification des contraintes de drawdown
        if (abs(daily_pnl) > max_daily_dd or 
            abs(weekly_pnl) > max_weekly_dd or
            consecutive_losses >= max_consecutive_losses):
            continue  # Skip trades si contraintes dépassées
        
        # Conditions d'entrée RENFORCÉES
        ema_trend = df.loc[i, 'Close'] > df.loc[i, 'EMA50']
        ema200_trend = df.loc[i, 'Close'] > df.loc[i, 'EMA200']
        volume_ok = df.loc[i, 'Volume_OK']
        
        # Breakouts
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        
        # RSI avec zones plus strictes
        rsi_ok_long = 30 < df.loc[i, 'RSI'] < rsi_overbought
        rsi_ok_short = rsi_oversold < df.loc[i, 'RSI'] < 70
        
        # Conditions d'entrée TRÈS STRICTES
        long_signal = (
            breakout_up and 
            ema_trend and 
            ema200_trend and  # Tendance principale
            volume_ok and 
            rsi_ok_long and
            df.loc[i, 'RSI'] > 40  # Pas de surachat
        )
        
        short_signal = (
            breakout_down and 
            not ema_trend and 
            not ema200_trend and  # Tendance baissière
            volume_ok and 
            rsi_ok_short and
            df.loc[i, 'RSI'] < 60  # Pas de survente
        )

        if position == 0:
            # Entrée Long
            if long_signal:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                
            # Entrée Short
            elif short_signal:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']

        elif position == 1:  # Position Long
            # Sorties avec gestion du risque
            if df.loc[i, 'Low'] <= stop_loss:
                pnl = (stop_loss - entry_price) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                consecutive_losses += 1
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': pnl,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                pnl = (profit_target - entry_price) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                consecutive_losses = 0  # Reset des pertes consécutives
                
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit'
                })
                position = 0

        elif position == -1:  # Position Short
            # Sorties avec gestion du risque
            if df.loc[i, 'High'] >= stop_loss:
                pnl = (entry_price - stop_loss) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                consecutive_losses += 1
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': pnl,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                pnl = (entry_price - profit_target) / entry_price
                daily_pnl += pnl
                weekly_pnl += pnl
                consecutive_losses = 0  # Reset des pertes consécutives
                
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': pnl,
                    'Reason': 'Take Profit'
                })
                position = 0

    return trades

def calculate_capital_metrics(trades):
    """Calcule les métriques avec focus sur la préservation du capital"""
    if not trades:
        return {
            'Total_PnL': 0,
            'Performance': 0,
            'Sharpe_Ratio': 0,
            'Win_Rate': 0,
            'Total_Trades': 0,
            'Max_Drawdown': 0,
            'Max_Daily_DD': 0,
            'Max_Weekly_DD': 0,
            'Capital_Preservation_Score': 0,
            'Risk_Adjusted_Return': 0
        }
    
    df_trades = pd.DataFrame(trades)
    total_pnl = df_trades['PnL'].sum()
    returns = df_trades['PnL']
    
    # Métriques de base
    total_trades = len(trades)
    winning_trades = len(df_trades[df_trades['PnL'] > 0])
    losing_trades = len(df_trades[df_trades['PnL'] < 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    # Performance annualisée
    performance = (1 + total_pnl) ** (252 / total_trades) - 1 if total_trades > 0 else 0
    
    # Sharpe Ratio
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    # Drawdown maximum
    cumulative = df_trades['PnL'].cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
    
    # Calcul des drawdowns quotidiens et hebdomadaires (simulation)
    daily_pnl_sim = []
    weekly_pnl_sim = []
    
    # Simulation de répartition temporelle
    for i, pnl in enumerate(df_trades['PnL']):
        daily_pnl_sim.append(pnl)
        if i % 5 == 4:  # 5 trades par semaine
            weekly_pnl_sim.append(sum(daily_pnl_sim[-5:]))
    
    max_daily_dd = max([abs(min(daily_pnl_sim[i:i+5])) for i in range(0, len(daily_pnl_sim), 5)]) * 100 if daily_pnl_sim else 0
    max_weekly_dd = max([abs(min(weekly_pnl_sim[i:i+4])) for i in range(0, len(weekly_pnl_sim), 4)]) * 100 if weekly_pnl_sim else 0
    
    # Score de préservation du capital (0-100)
    capital_preservation_score = 100
    if max_drawdown > 10:
        capital_preservation_score -= 50
    if max_daily_dd > 2:
        capital_preservation_score -= 25
    if max_weekly_dd > 5:
        capital_preservation_score -= 25
    
    # Retour ajusté au risque
    risk_adjusted_return = performance / (max_drawdown / 100) if max_drawdown > 0 else 0
    
    return {
        'Total_PnL': total_pnl,
        'Performance': performance,
        'Sharpe_Ratio': sharpe,
        'Win_Rate': win_rate,
        'Total_Trades': total_trades,
        'Max_Drawdown': max_drawdown,
        'Max_Daily_DD': max_daily_dd,
        'Max_Weekly_DD': max_weekly_dd,
        'Capital_Preservation_Score': capital_preservation_score,
        'Risk_Adjusted_Return': risk_adjusted_return
    }

def main():
    print("🛡️ Stratégie de Préservation du Capital")
    print("=" * 50)
    print("💡 Priorité : Protéger le capital avant tout")
    print("=" * 50)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_results = []
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            # Essayer plusieurs emplacements de fichiers
            possible_paths = [
                f"datas/{symbol}_{timeframe}_mt5.csv",
                f"old steven/datas/{symbol}_{timeframe}_mt5.csv",
                f"{symbol}_{timeframe}.csv"
            ]
            
            filename = None
            for path in possible_paths:
                if os.path.exists(path):
                    filename = path
                    break
            
            if filename:
                print(f"📊 Test de {symbol} {timeframe}...")
                
                # Chargement et backtest
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = strategie_capital_preservation(df, symbol, timeframe)
                
                # Calcul des métriques
                metrics = calculate_capital_metrics(trades)
                
                all_results.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'trades': trades,
                    'metrics': metrics
                })
                
                print(f"  ✅ {len(trades)} trades, {metrics['Performance']:.2%} performance")
                print(f"     🛡️ DD: {metrics['Max_Drawdown']:.1f}% | Score Capital: {metrics['Capital_Preservation_Score']:.0f}/100")
    
    # Affichage des résultats
    print(f"\n🏆 Résultats de la Stratégie de Préservation du Capital :")
    print("=" * 60)
    
    # Tri par score de préservation du capital
    if all_results:
        best_capital_results = sorted(all_results, key=lambda x: x['metrics']['Capital_Preservation_Score'], reverse=True)
        
        print(f"\n🛡️ Top 5 par Score de Préservation du Capital :")
        for i, result in enumerate(best_capital_results[:5], 1):
            metrics = result['metrics']
            print(f"   {i}. {result['symbol']} {result['timeframe']}: Score {metrics['Capital_Preservation_Score']:.0f}/100")
            print(f"      📈 Performance: {metrics['Performance']:.2%} | DD: {metrics['Max_Drawdown']:.1f}% | Trades: {metrics['Total_Trades']}")
        
        # Tri par retour ajusté au risque
        best_risk_adjusted = sorted(all_results, key=lambda x: x['metrics']['Risk_Adjusted_Return'], reverse=True)
        
        print(f"\n📊 Top 5 par Retour Ajusté au Risque :")
        for i, result in enumerate(best_risk_adjusted[:5], 1):
            metrics = result['metrics']
            print(f"   {i}. {result['symbol']} {result['timeframe']}: {metrics['Risk_Adjusted_Return']:.2f}")
            print(f"      📈 Performance: {metrics['Performance']:.2%} | DD: {metrics['Max_Drawdown']:.1f}% | Sharpe: {metrics['Sharpe_Ratio']:.2f}")
        
        # Stratégies respectant les contraintes
        compliant_results = [r for r in all_results if r['metrics']['Capital_Preservation_Score'] >= 75]
        
        print(f"\n✅ Stratégies avec Bonne Préservation du Capital ({len(compliant_results)}/{len(all_results)}) :")
        for result in compliant_results:
            metrics = result['metrics']
            print(f"   - {result['symbol']} {result['timeframe']}: Score {metrics['Capital_Preservation_Score']:.0f}/100")
            print(f"     Performance: {metrics['Performance']:.2%} | DD: {metrics['Max_Drawdown']:.1f}% | Trades: {metrics['Total_Trades']}")
    else:
        print(f"\n❌ Aucun résultat à afficher")
    
    # Statistiques globales
    if all_results:
        positive_results = [r for r in all_results if r['metrics']['Performance'] > 0]
        avg_dd = np.mean([r['metrics']['Max_Drawdown'] for r in all_results])
        avg_capital_score = np.mean([r['metrics']['Capital_Preservation_Score'] for r in all_results])
        
        print(f"\n📊 Statistiques Globales :")
        print(f"   - Stratégies rentables: {len(positive_results)}/{len(all_results)} ({len(positive_results)/len(all_results)*100:.1f}%)")
        print(f"   - Drawdown moyen: {avg_dd:.1f}% (vs 1754% avant !)")
        print(f"   - Score capital moyen: {avg_capital_score:.0f}/100")
    else:
        print(f"\n⚠️ Aucun résultat trouvé - Vérifiez les fichiers de données dans le dossier 'datas/'")
        print(f"   Fichiers attendus : XAUUSD_D1_mt5.csv, US30.cash_H4_mt5.csv, etc.")
    
    # Sauvegarde des résultats
    os.makedirs("capital_preservation_results", exist_ok=True)
    
    report = "## 🛡️ Stratégie de Préservation du Capital\n\n"
    report += "### 💡 Objectifs\n"
    report += "- **DD Max :** 10% (vs 1754% avant)\n"
    report += "- **DD Quotidien :** 2%\n"
    report += "- **DD Hebdomadaire :** 5%\n\n"
    report += "### 📊 Résultats par Instrument\n\n"
    
    if all_results:
        for result in best_capital_results:
            metrics = result['metrics']
            report += f"#### {result['symbol']} {result['timeframe']}\n"
            report += f"- **Score Capital :** {metrics['Capital_Preservation_Score']:.0f}/100\n"
            report += f"- **Performance :** {metrics['Performance']:.2%}\n"
            report += f"- **Max Drawdown :** {metrics['Max_Drawdown']:.1f}%\n"
            report += f"- **Trades :** {metrics['Total_Trades']}\n"
            report += f"- **Win Rate :** {metrics['Win_Rate']:.1f}%\n"
            report += f"- **Sharpe Ratio :** {metrics['Sharpe_Ratio']:.2f}\n\n"
    else:
        report += "Aucun résultat disponible - Vérifiez les fichiers de données\n\n"
    
    with open("capital_preservation_results/capital_preservation_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Rapport sauvegardé : capital_preservation_results/capital_preservation_report.md")
    
    # Recommandations finales
    if all_results:
        if compliant_results:
            best_strategy = max(compliant_results, key=lambda x: x['metrics']['Performance'])
            print(f"\n🏆 RECOMMANDATION FINALE :")
            print(f"   - {best_strategy['symbol']} {best_strategy['timeframe']}")
            print(f"   - Performance: {best_strategy['metrics']['Performance']:.2%}")
            print(f"   - DD: {best_strategy['metrics']['Max_Drawdown']:.1f}%")
            print(f"   - Score Capital: {best_strategy['metrics']['Capital_Preservation_Score']:.0f}/100")
        else:
            print(f"\n⚠️ Aucune stratégie ne respecte complètement les contraintes")
            print(f"   Meilleure approximation : {best_capital_results[0]['symbol']} {best_capital_results[0]['timeframe']}")
    else:
        print(f"\n❌ Impossible de faire des recommandations sans données")

if __name__ == "__main__":
    main() 