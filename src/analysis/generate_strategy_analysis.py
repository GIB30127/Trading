import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour importer les stratégies
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))
from strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple, calculate_metrics

def create_detailed_analysis(symbol="XAUUSD", timeframe="D1"):
    """Génère une analyse détaillée de la stratégie"""
    
    print(f"[bold blue]🔍 ANALYSE DÉTAILLÉE {symbol} {timeframe}[/bold blue]")
    
    # Chargement des données
    csv_path = f"data/raw/{symbol}_{timeframe}_mt5.csv"
    
    if not os.path.exists(csv_path):
        print(f"[red]❌ Fichier non trouvé: {csv_path}[/red]")
        return None
    
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    print(f"[green]✅ {len(df)} bougies analysées[/green]")
    
    # Application de la stratégie
    trades, df_signals = strategie_xauusd_sharpe1_simple(df, symbol, timeframe)
    metrics = calculate_metrics(trades)
    
    # Création du dossier d'analyse
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_dir = f"results/analysis/{symbol}_{timeframe}_analysis_{timestamp}"
    os.makedirs(analysis_dir, exist_ok=True)
    
    # 1. Rapport textuel détaillé
    generate_text_report(trades, metrics, df_signals, analysis_dir, symbol, timeframe)
    
    # 2. Graphiques d'analyse
    generate_analysis_charts(trades, df_signals, analysis_dir, symbol, timeframe)
    
    # 3. Analyse des trades
    generate_trade_analysis(trades, analysis_dir, symbol, timeframe)
    
    # 4. Métriques avancées
    generate_advanced_metrics(trades, metrics, analysis_dir, symbol, timeframe)
    
    print(f"\n[bold green]✅ Analyse complète générée dans: {analysis_dir}[/bold green]")
    
    return analysis_dir

def generate_text_report(trades, metrics, df_signals, output_dir, symbol, timeframe):
    """Génère un rapport textuel détaillé"""
    
    report_file = f"{output_dir}/rapport_analyse_complet.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Analyse Complète - Stratégie {symbol} {timeframe}\n\n")
        f.write(f"**Date d'analyse**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Résumé exécutif
        f.write("## 📊 RÉSUMÉ EXÉCUTIF\n\n")
        f.write(f"- **Symbole**: {symbol}\n")
        f.write(f"- **Timeframe**: {timeframe}\n")
        f.write(f"- **Période analysée**: {df_signals['Date'].min()} à {df_signals['Date'].max()}\n")
        f.write(f"- **Total trades**: {metrics['total_trades']}\n")
        f.write(f"- **Retour total**: {metrics['total_return']:.2f}%\n")
        f.write(f"- **Ratio de Sharpe**: {metrics['sharpe_ratio']:.2f}\n")
        f.write(f"- **Profit Factor**: {metrics['profit_factor']:.2f}\n")
        f.write(f"- **Drawdown max**: {metrics['max_drawdown']:.2f}%\n\n")
        
        # Métriques de performance
        f.write("## 📈 MÉTRIQUES DE PERFORMANCE\n\n")
        f.write("| Métrique | Valeur | Évaluation |\n")
        f.write("|----------|--------|------------|\n")
        
        # Évaluation du win rate
        win_rate_eval = "🟢 Excellent" if metrics['win_rate'] > 60 else "🟡 Bon" if metrics['win_rate'] > 50 else "🔴 Faible"
        f.write(f"| Taux de réussite | {metrics['win_rate']:.2f}% | {win_rate_eval} |\n")
        
        # Évaluation du profit factor
        pf_eval = "🟢 Excellent" if metrics['profit_factor'] > 2 else "🟡 Bon" if metrics['profit_factor'] > 1.5 else "🔴 Faible"
        f.write(f"| Profit Factor | {metrics['profit_factor']:.2f} | {pf_eval} |\n")
        
        # Évaluation du Sharpe
        sharpe_eval = "🟢 Excellent" if metrics['sharpe_ratio'] > 2 else "🟡 Bon" if metrics['sharpe_ratio'] > 1 else "🔴 Faible"
        f.write(f"| Ratio de Sharpe | {metrics['sharpe_ratio']:.2f} | {sharpe_eval} |\n")
        
        # Évaluation du drawdown
        dd_eval = "🟢 Faible" if metrics['max_drawdown'] < 20 else "🟡 Modéré" if metrics['max_drawdown'] < 40 else "🔴 Élevé"
        f.write(f"| Drawdown max | {metrics['max_drawdown']:.2f}% | {dd_eval} |\n")
        
        f.write("\n")
        
        # Analyse des trades
        f.write("## 📋 ANALYSE DÉTAILLÉE DES TRADES\n\n")
        f.write(f"- **Trades gagnants**: {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)\n")
        f.write(f"- **Trades perdants**: {metrics['losing_trades']} ({100-metrics['win_rate']:.1f}%)\n")
        f.write(f"- **Gain moyen**: {metrics['avg_win']:.2f}%\n")
        f.write(f"- **Perte moyenne**: {metrics['avg_loss']:.2f}%\n")
        f.write(f"- **Ratio gain/perte**: {abs(metrics['avg_win']/metrics['avg_loss']):.2f}\n\n")
        
        # Analyse temporelle
        f.write("## 📅 ANALYSE TEMPORELLE\n\n")
        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades['entry_date'] = pd.to_datetime(df_trades['entry_date'])
            df_trades['year'] = df_trades['entry_date'].dt.year
            df_trades['month'] = df_trades['entry_date'].dt.month
            
            # Performance par année
            yearly_perf = df_trades.groupby('year')['pnl'].agg(['count', 'sum', 'mean']).round(2)
            f.write("### Performance par année:\n")
            f.write("| Année | Nombre de trades | P&L total | P&L moyen |\n")
            f.write("|-------|------------------|-----------|-----------|\n")
            for year, row in yearly_perf.iterrows():
                f.write(f"| {year} | {row['count']} | {row['sum']:.2f}% | {row['mean']:.2f}% |\n")
            f.write("\n\n")
            
            # Performance par mois
            monthly_perf = df_trades.groupby('month')['pnl'].agg(['count', 'sum', 'mean']).round(2)
            f.write("### Performance par mois:\n")
            f.write("| Mois | Nombre de trades | P&L total | P&L moyen |\n")
            f.write("|------|------------------|-----------|-----------|\n")
            for month, row in monthly_perf.iterrows():
                month_name = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'][month-1]
                f.write(f"| {month_name} | {row['count']} | {row['sum']:.2f}% | {row['mean']:.2f}% |\n")
            f.write("\n\n")
        
        # Recommandations
        f.write("## 💡 RECOMMANDATIONS\n\n")
        
        if metrics['win_rate'] < 50:
            f.write("- ⚠️ **Taux de réussite faible**: Considérer l'ajustement des filtres d'entrée\n")
        
        if metrics['profit_factor'] < 1.5:
            f.write("- ⚠️ **Profit Factor faible**: Optimiser la gestion des sorties\n")
        
        if metrics['max_drawdown'] > 40:
            f.write("- ⚠️ **Drawdown élevé**: Renforcer la gestion des risques\n")
        
        if metrics['sharpe_ratio'] < 1:
            f.write("- ⚠️ **Ratio de Sharpe faible**: Améliorer le ratio risque/récompense\n")
        
        if metrics['win_rate'] > 55 and metrics['profit_factor'] > 2:
            f.write("- ✅ **Performance excellente**: Stratégie prête pour le trading réel\n")
        
        f.write("\n## 🎯 CONCLUSION\n\n")
        
        # Score global
        score = 0
        if metrics['win_rate'] > 55: score += 2
        elif metrics['win_rate'] > 50: score += 1
        
        if metrics['profit_factor'] > 2: score += 2
        elif metrics['profit_factor'] > 1.5: score += 1
        
        if metrics['sharpe_ratio'] > 2: score += 2
        elif metrics['sharpe_ratio'] > 1: score += 1
        
        if metrics['max_drawdown'] < 30: score += 1
        
        f.write(f"**Score global**: {score}/7\n\n")
        
        if score >= 6:
            f.write("🟢 **STRATÉGIE EXCELLENTE** - Prête pour le trading réel\n")
        elif score >= 4:
            f.write("🟡 **STRATÉGIE BONNE** - Nécessite quelques ajustements\n")
        else:
            f.write("🔴 **STRATÉGIE À AMÉLIORER** - Optimisation requise\n")

def generate_analysis_charts(trades, df_signals, output_dir, symbol, timeframe):
    """Génère des graphiques d'analyse"""
    
    if not trades:
        return
    
    df_trades = pd.DataFrame(trades)
    df_trades['entry_date'] = pd.to_datetime(df_trades['entry_date'])
    
    # 1. Évolution du capital
    fig_capital = go.Figure()
    
    # Calcul de l'évolution du capital
    df_trades['cumulative_pnl'] = df_trades['pnl'].cumsum()
    df_trades['capital'] = 100 + df_trades['cumulative_pnl']
    
    fig_capital.add_trace(go.Scatter(
        x=df_trades['entry_date'],
        y=df_trades['capital'],
        mode='lines',
        name='Capital',
        line=dict(color='blue', width=2)
    ))
    
    fig_capital.update_layout(
        title=f'Évolution du Capital - {symbol} {timeframe}',
        xaxis_title='Date',
        yaxis_title='Capital (%)',
        template='plotly_white'
    )
    
    fig_capital.write_html(f"{output_dir}/evolution_capital.html")
    
    # 2. Distribution des P&L
    fig_dist = go.Figure()
    
    fig_dist.add_trace(go.Histogram(
        x=df_trades['pnl'],
        nbinsx=30,
        name='Distribution P&L',
        marker_color='lightblue'
    ))
    
    fig_dist.update_layout(
        title=f'Distribution des P&L - {symbol} {timeframe}',
        xaxis_title='P&L (%)',
        yaxis_title='Fréquence',
        template='plotly_white'
    )
    
    fig_dist.write_html(f"{output_dir}/distribution_pnl.html")
    
    # 3. Graphique des prix avec signaux
    fig_signals = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Prix et Signaux', 'RSI', 'ATR'),
        row_heights=[0.6, 0.2, 0.2]
    )
    
    # Prix
    fig_signals.add_trace(go.Candlestick(
        x=df_signals['Date'],
        open=df_signals['Open'],
        high=df_signals['High'],
        low=df_signals['Low'],
        close=df_signals['Close'],
        name='Prix'
    ), row=1, col=1)
    
    # EMAs
    fig_signals.add_trace(go.Scatter(
        x=df_signals['Date'],
        y=df_signals['EMA_Short'],
        name='EMA Short',
        line=dict(color='orange')
    ), row=1, col=1)
    
    fig_signals.add_trace(go.Scatter(
        x=df_signals['Date'],
        y=df_signals['EMA_Long'],
        name='EMA Long',
        line=dict(color='red')
    ), row=1, col=1)
    
    # RSI
    fig_signals.add_trace(go.Scatter(
        x=df_signals['Date'],
        y=df_signals['RSI'],
        name='RSI',
        line=dict(color='purple')
    ), row=2, col=1)
    
    # Lignes RSI
    fig_signals.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig_signals.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # ATR
    fig_signals.add_trace(go.Scatter(
        x=df_signals['Date'],
        y=df_signals['ATR'],
        name='ATR',
        line=dict(color='brown')
    ), row=3, col=1)
    
    fig_signals.update_layout(
        title=f'Analyse Technique - {symbol} {timeframe}',
        xaxis_rangeslider_visible=False,
        height=800
    )
    
    fig_signals.write_html(f"{output_dir}/analyse_technique.html")

def generate_trade_analysis(trades, output_dir, symbol, timeframe):
    """Génère une analyse détaillée des trades"""
    
    if not trades:
        return
    
    df_trades = pd.DataFrame(trades)
    
    # Sauvegarde des trades
    trades_file = f"{output_dir}/trades_detailles.csv"
    df_trades.to_csv(trades_file, index=False)
    
    # Analyse des raisons de sortie
    exit_reasons = df_trades['exit_reason'].value_counts()
    
    analysis_file = f"{output_dir}/analyse_trades.md"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        f.write(f"# Analyse Détaillée des Trades - {symbol} {timeframe}\n\n")
        
        f.write("## 📊 Statistiques des Sorties\n\n")
        f.write("| Raison de sortie | Nombre | Pourcentage |\n")
        f.write("|------------------|--------|-------------|\n")
        
        for reason, count in exit_reasons.items():
            percentage = (count / len(df_trades)) * 100
            f.write(f"| {reason} | {count} | {percentage:.1f}% |\n")
        
        f.write("\n## 📈 Performance par Type de Sortie\n\n")
        
        for reason in exit_reasons.index:
            reason_trades = df_trades[df_trades['exit_reason'] == reason]
            avg_pnl = reason_trades['pnl'].mean()
            win_rate = (reason_trades['pnl'] > 0).mean() * 100
            
            f.write(f"### {reason}\n")
            f.write(f"- Nombre de trades: {len(reason_trades)}\n")
            f.write(f"- P&L moyen: {avg_pnl:.2f}%\n")
            f.write(f"- Taux de réussite: {win_rate:.1f}%\n\n")

def generate_advanced_metrics(trades, metrics, output_dir, symbol, timeframe):
    """Génère des métriques avancées"""
    
    if not trades:
        return
    
    df_trades = pd.DataFrame(trades)
    
    # Calculs avancés
    advanced_metrics = {}
    
    # Calmar Ratio
    if metrics['max_drawdown'] > 0:
        advanced_metrics['calmar_ratio'] = metrics['total_return'] / metrics['max_drawdown']
    else:
        advanced_metrics['calmar_ratio'] = float('inf')
    
    # Sortino Ratio (simplifié)
    negative_returns = df_trades[df_trades['pnl'] < 0]['pnl']
    if len(negative_returns) > 0:
        downside_deviation = negative_returns.std()
        advanced_metrics['sortino_ratio'] = metrics['total_return'] / downside_deviation if downside_deviation > 0 else 0
    else:
        advanced_metrics['sortino_ratio'] = float('inf')
    
    # Consecutive wins/losses
    df_trades['win'] = df_trades['pnl'] > 0
    consecutive_wins = 0
    consecutive_losses = 0
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    
    current_wins = 0
    current_losses = 0
    
    for win in df_trades['win']:
        if win:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
    
    advanced_metrics['max_consecutive_wins'] = max_consecutive_wins
    advanced_metrics['max_consecutive_losses'] = max_consecutive_losses
    
    # Sauvegarde des métriques avancées
    advanced_file = f"{output_dir}/metriques_avancees.md"
    with open(advanced_file, 'w', encoding='utf-8') as f:
        f.write(f"# Métriques Avancées - {symbol} {timeframe}\n\n")
        
        f.write("| Métrique | Valeur | Description |\n")
        f.write("|----------|--------|-------------|\n")
        f.write(f"| Calmar Ratio | {advanced_metrics['calmar_ratio']:.2f} | Retour/Drawdown |\n")
        f.write(f"| Sortino Ratio | {advanced_metrics['sortino_ratio']:.2f} | Retour/Volatilité baissière |\n")
        f.write(f"| Max Wins Consécutifs | {advanced_metrics['max_consecutive_wins']} | Série de gains max |\n")
        f.write(f"| Max Losses Consécutifs | {advanced_metrics['max_consecutive_losses']} | Série de pertes max |\n")

def main():
    """Fonction principale"""
    print("[bold blue]🔍 GÉNÉRATEUR D'ANALYSE STRATÉGIQUE[/bold blue]")
    
    # Analyse pour XAUUSD D1
    analysis_dir = create_detailed_analysis("XAUUSD", "D1")
    
    if analysis_dir:
        print(f"\n[bold green]📁 Fichiers générés dans: {analysis_dir}[/bold green]")
        print("📄 rapport_analyse_complet.md - Rapport détaillé")
        print("📊 evolution_capital.html - Graphique d'évolution du capital")
        print("📈 distribution_pnl.html - Distribution des P&L")
        print("🔧 analyse_technique.html - Graphiques techniques")
        print("📋 trades_detailles.csv - Données des trades")
        print("📊 analyse_trades.md - Analyse des trades")
        print("📈 metriques_avancees.md - Métriques avancées")

if __name__ == "__main__":
    main() 