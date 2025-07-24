import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from rich import print
import warnings
warnings.filterwarnings('ignore')

def compute_atr(df, window):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def simple_breakout_strategy(df, symbol, timeframe):
    """Stratégie de breakout simple"""
    
    df = df.copy()
    
    # Paramètres adaptés par instrument
    if symbol == 'XAUUSD':
        breakout_period = 20
        risk_atr = 3.0
        profit_atr = 6.0
    elif symbol == 'US30.cash':
        breakout_period = 15
        risk_atr = 2.5
        profit_atr = 5.0
    elif symbol == 'EURUSD':
        breakout_period = 12
        risk_atr = 2.0
        profit_atr = 4.0
    else:  # GER40.cash
        breakout_period = 12
        risk_atr = 2.0
        profit_atr = 4.0
    
    # Ajustement timeframe
    if timeframe == 'D1':
        breakout_period = int(breakout_period * 1.5)
        risk_atr *= 1.2
        profit_atr *= 1.2
    elif timeframe == 'H1':
        breakout_period = int(breakout_period * 0.8)
        risk_atr *= 0.8
        profit_atr *= 0.8
    
    # Calcul des indicateurs
    df['ATR'] = compute_atr(df, 14)
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
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

    for i in range(1, len(df)):
        # Conditions de base
        ema_trend = df.loc[i, 'Close'] > df.loc[i, 'EMA50']
        volume_ok = df.loc[i, 'Volume_OK']
        
        # Breakouts purs
        breakout_up = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                      df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_down = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                        df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])

        if position == 0:
            # Entrée Long
            if breakout_up and ema_trend and volume_ok:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                
            # Entrée Short
            elif breakout_down and not ema_trend and volume_ok:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']

        elif position == 1:  # Position Long
            # Sorties
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (profit_target - entry_price) / entry_price,
                    'Reason': 'Take Profit'
                })
                position = 0

        elif position == -1:  # Position Short
            # Sorties
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (entry_price - profit_target) / entry_price,
                    'Reason': 'Take Profit'
                })
                position = 0

    return trades

def calculate_metrics(trades):
    """Calcule toutes les métriques de performance"""
    if not trades:
        return {
            'Total_PnL': 0,
            'Performance': 0,
            'Sharpe_Ratio': 0,
            'Win_Rate': 0,
            'Total_Trades': 0,
            'Winning_Trades': 0,
            'Losing_Trades': 0,
            'Avg_Win': 0,
            'Avg_Loss': 0,
            'Risk_Reward': 0,
            'Max_Drawdown': 0
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
    
    # Ratio risque/récompense
    avg_win = df_trades[df_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = abs(df_trades[df_trades['PnL'] < 0]['PnL'].mean()) if losing_trades > 0 else 0
    risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
    
    # Drawdown maximum
    cumulative = df_trades['PnL'].cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
    
    return {
        'Total_PnL': total_pnl,
        'Performance': performance,
        'Sharpe_Ratio': sharpe,
        'Win_Rate': win_rate,
        'Total_Trades': total_trades,
        'Winning_Trades': winning_trades,
        'Losing_Trades': losing_trades,
        'Avg_Win': avg_win,
        'Avg_Loss': avg_loss,
        'Risk_Reward': risk_reward,
        'Max_Drawdown': max_drawdown
    }

def create_comparison_table(all_results):
    """Crée un tableau de comparaison HTML"""
    
    # Création du DataFrame pour le tableau
    table_data = []
    for result in all_results:
        metrics = result['metrics']
        table_data.append({
            'Instrument': result['symbol'],
            'Timeframe': result['timeframe'],
            'Performance (%)': f"{metrics['Performance']:.2%}",
            'PnL Total': f"{metrics['Total_PnL']:.4f}",
            'Sharpe Ratio': f"{metrics['Sharpe_Ratio']:.2f}",
            'Win Rate (%)': f"{metrics['Win_Rate']:.1f}",
            'Trades': metrics['Total_Trades'],
            'Gagnants': metrics['Winning_Trades'],
            'Perdants': metrics['Losing_Trades'],
            'R/R Ratio': f"{metrics['Risk_Reward']:.2f}",
            'Max DD (%)': f"{metrics['Max_Drawdown']:.1f}"
        })
    
    df_table = pd.DataFrame(table_data)
    
    # Tri par performance
    df_table_sorted = df_table.sort_values('Performance (%)', ascending=False)
    
    # Création du HTML
    html_table = df_table_sorted.to_html(
        index=False,
        classes=['table', 'table-striped', 'table-hover'],
        float_format=lambda x: f"{x:.2f}" if isinstance(x, float) else str(x)
    )
    
    return html_table

def create_performance_chart(all_results):
    """Crée un graphique de comparaison des performances"""
    
    # Préparation des données
    symbols = [r['symbol'] for r in all_results]
    timeframes = [r['timeframe'] for r in all_results]
    performances = [r['metrics']['Performance'] * 100 for r in all_results]
    win_rates = [r['metrics']['Win_Rate'] for r in all_results]
    
    # Graphique de performance
    fig = go.Figure()
    
    # Barres de performance
    colors = ['#4CAF50' if p > 0 else '#F44336' for p in performances]
    
    fig.add_trace(
        go.Bar(
            x=[f"{s} {tf}" for s, tf in zip(symbols, timeframes)],
            y=performances,
            name='Performance (%)',
            marker_color=colors,
            text=[f"{p:.1f}%" for p in performances],
            textposition='auto'
        )
    )
    
    fig.update_layout(
        title='Comparaison des Performances par Instrument',
        xaxis_title='Instrument & Timeframe',
        yaxis_title='Performance (%)',
        template='plotly_dark',
        height=500
    )
    
    return fig

def create_win_rate_chart(all_results):
    """Crée un graphique des taux de réussite"""
    
    symbols = [r['symbol'] for r in all_results]
    timeframes = [r['timeframe'] for r in all_results]
    win_rates = [r['metrics']['Win_Rate'] for r in all_results]
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=[f"{s} {tf}" for s, tf in zip(symbols, timeframes)],
            y=win_rates,
            name='Taux de Réussite (%)',
            marker_color='#2196F3',
            text=[f"{w:.1f}%" for w in win_rates],
            textposition='auto'
        )
    )
    
    fig.update_layout(
        title='Taux de Réussite par Instrument',
        xaxis_title='Instrument & Timeframe',
        yaxis_title='Taux de Réussite (%)',
        template='plotly_dark',
        height=400
    )
    
    return fig

def generate_complete_dashboard():
    """Génère le dashboard complet"""
    
    print("📊 Génération du Dashboard Complet")
    print("=" * 40)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    all_results = []
    
    # Collecte de tous les résultats
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📈 Analyse de {symbol} {timeframe}...")
                
                # Chargement et backtest
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                trades = simple_breakout_strategy(df, symbol, timeframe)
                
                # Calcul des métriques
                metrics = calculate_metrics(trades)
                
                all_results.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'trades': trades,
                    'metrics': metrics
                })
                
                print(f"  ✅ {len(trades)} trades, {metrics['Performance']:.2%} performance")
    
    # Création des graphiques
    perf_chart = create_performance_chart(all_results)
    win_rate_chart = create_win_rate_chart(all_results)
    
    # Création du tableau de comparaison
    comparison_table = create_comparison_table(all_results)
    
    # Génération du HTML complet
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Trading - Analyse Complète</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            background-color: #1a1a1a;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: #2d2d2d;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #4CAF50;
        }}
        .metric-card.negative {{
            border-left-color: #F44336;
        }}
        .table {{
            background-color: #2d2d2d;
            color: #ffffff;
        }}
        .table th {{
            background-color: #3d3d3d;
            border-color: #4d4d4d;
        }}
        .table td {{
            border-color: #4d4d4d;
        }}
        .chart-container {{
            background: #2d2d2d;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 2rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1 class="text-center mb-0">📊 Dashboard Trading - Analyse Complète</h1>
            <p class="text-center mb-0 mt-2">Comparaison des stratégies par instrument et timeframe</p>
        </div>
    </div>

    <div class="container">
        <!-- Résumé des meilleurs résultats -->
        <div class="row mb-4">
            <div class="col-12">
                <h2>🏆 Résumé des Performances</h2>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="metric-card">
                    <h4>🥇 Meilleur</h4>
                    <h3>{max(all_results, key=lambda x: x['metrics']['Performance'])['symbol']} {max(all_results, key=lambda x: x['metrics']['Performance'])['timeframe']}</h3>
                    <p>{max(all_results, key=lambda x: x['metrics']['Performance'])['metrics']['Performance']:.2%}</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card negative">
                    <h4>🥉 Pire</h4>
                    <h3>{min(all_results, key=lambda x: x['metrics']['Performance'])['symbol']} {min(all_results, key=lambda x: x['metrics']['Performance'])['timeframe']}</h3>
                    <p>{min(all_results, key=lambda x: x['metrics']['Performance'])['metrics']['Performance']:.2%}</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h4>📈 Moyenne</h4>
                    <h3>{np.mean([r['metrics']['Performance'] for r in all_results]):.2%}</h3>
                    <p>Performance moyenne</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <h4>✅ Rentables</h4>
                    <h3>{len([r for r in all_results if r['metrics']['Performance'] > 0])}/{len(all_results)}</h3>
                    <p>Stratégies rentables</p>
                </div>
            </div>
        </div>

        <!-- Graphiques -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="chart-container">
                    {perf_chart.to_html(full_html=False, include_plotlyjs=False)}
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-12">
                <div class="chart-container">
                    {win_rate_chart.to_html(full_html=False, include_plotlyjs=False)}
                </div>
            </div>
        </div>

        <!-- Tableau de comparaison -->
        <div class="row mb-4">
            <div class="col-12">
                <h2>📋 Tableau Comparatif Détaillé</h2>
                <div class="table-responsive">
                    {comparison_table}
                </div>
            </div>
        </div>

        <!-- Détails par instrument -->
        <div class="row">
            <div class="col-12">
                <h2>🔍 Détails par Instrument</h2>
            </div>
        </div>
"""

    # Ajout des détails par instrument
    for result in all_results:
        metrics = result['metrics']
        trades = result['trades']
        
        html_content += f"""
        <div class="row mb-4">
            <div class="col-12">
                <div class="metric-card">
                    <h3>{result['symbol']} {result['timeframe']}</h3>
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Performance:</strong> {metrics['Performance']:.2%}<br>
                            <strong>PnL Total:</strong> {metrics['Total_PnL']:.4f}
                        </div>
                        <div class="col-md-3">
                            <strong>Sharpe Ratio:</strong> {metrics['Sharpe_Ratio']:.2f}<br>
                            <strong>Win Rate:</strong> {metrics['Win_Rate']:.1f}%
                        </div>
                        <div class="col-md-3">
                            <strong>Trades:</strong> {metrics['Total_Trades']}<br>
                            <strong>R/R Ratio:</strong> {metrics['Risk_Reward']:.2f}
                        </div>
                        <div class="col-md-3">
                            <strong>Max Drawdown:</strong> {metrics['Max_Drawdown']:.1f}%<br>
                            <strong>Gagnants/Perdants:</strong> {metrics['Winning_Trades']}/{metrics['Losing_Trades']}
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""

    html_content += """
    </div>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

    # Sauvegarde du dashboard
    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/complete_dashboard.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n🎉 Dashboard complet généré : dashboard/complete_dashboard.html")
    print("📊 Statistiques générées :")
    print(f"   - {len(all_results)} stratégies analysées")
    print(f"   - {len([r for r in all_results if r['metrics']['Performance'] > 0])} stratégies rentables")
    print(f"   - Performance moyenne : {np.mean([r['metrics']['Performance'] for r in all_results]):.2%}")
    
    # Affichage des meilleurs résultats
    best_results = sorted(all_results, key=lambda x: x['metrics']['Performance'], reverse=True)
    print(f"\n🏆 Top 3 des meilleures stratégies :")
    for i, result in enumerate(best_results[:3], 1):
        print(f"   {i}. {result['symbol']} {result['timeframe']}: {result['metrics']['Performance']:.2%}")

if __name__ == "__main__":
    generate_complete_dashboard() 