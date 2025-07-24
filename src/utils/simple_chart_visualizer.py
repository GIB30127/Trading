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

def simple_breakout_strategy_with_signals(df, symbol, timeframe):
    """Stratégie avec génération des signaux pour visualisation"""
    
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
    
    # Signaux
    df['EMA_Trend'] = df['Close'] > df['EMA50']
    df['Breakout_Up'] = (df['High'].shift(1) < df['High_Break'].shift(1)) & (df['High'] >= df['High_Break'])
    df['Breakout_Down'] = (df['Low'].shift(1) > df['Low_Break'].shift(1)) & (df['Low'] <= df['Low_Break'])
    
    # Conditions d'entrée
    df['Long_Signal'] = df['Breakout_Up'] & df['EMA_Trend'] & df['Volume_OK']
    df['Short_Signal'] = df['Breakout_Down'] & ~df['EMA_Trend'] & df['Volume_OK']
    
    df = df.dropna().reset_index(drop=True)
    
    # Génération des trades avec signaux visuels
    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target = 0
    trades = []
    entry_index = 0
    
    for i in range(1, len(df)):
        if position == 0:
            if df.loc[i, 'Long_Signal']:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price + profit_atr * df.loc[i, 'ATR']
                entry_index = i
                
            elif df.loc[i, 'Short_Signal']:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + risk_atr * df.loc[i, 'ATR']
                profit_target = entry_price - profit_atr * df.loc[i, 'ATR']
                entry_index = i

        elif position == 1:  # Long
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'EntryIndex': entry_index,
                    'ExitIndex': i,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (profit_target - entry_price) / entry_price,
                    'EntryIndex': entry_index,
                    'ExitIndex': i,
                    'Reason': 'Take Profit'
                })
                position = 0

        elif position == -1:  # Short
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'EntryIndex': entry_index,
                    'ExitIndex': i,
                    'Reason': 'Stop Loss'
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target,
                    'PnL': (entry_price - profit_target) / entry_price,
                    'EntryIndex': entry_index,
                    'ExitIndex': i,
                    'Reason': 'Take Profit'
                })
                position = 0

    return df, trades

def create_simple_chart(df, trades, symbol, timeframe):
    """Crée un graphique simple et efficace"""
    
    # Création du graphique
    fig = go.Figure()
    
    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Prix',
            increasing_line_color='#26A69A',
            decreasing_line_color='#EF5350'
        )
    )
    
    # EMAs
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EMA20'],
            mode='lines',
            name='EMA20',
            line=dict(color='#FF9800', width=1)
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EMA50'],
            mode='lines',
            name='EMA50',
            line=dict(color='#2196F3', width=2)
        )
    )
    
    # Breakout levels
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['High_Break'],
            mode='lines',
            name='Résistance Breakout',
            line=dict(color='#FF5722', width=1, dash='dash'),
            opacity=0.7
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Low_Break'],
            mode='lines',
            name='Support Breakout',
            line=dict(color='#4CAF50', width=1, dash='dash'),
            opacity=0.7
        )
    )
    
    # Signaux d'entrée
    long_signals = df[df['Long_Signal']]
    short_signals = df[df['Short_Signal']]
    
    if not long_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=long_signals.index,
                y=long_signals['Low'] * 0.995,
                mode='markers',
                name='Signal Long',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='#4CAF50',
                    line=dict(color='white', width=1)
                )
            )
        )
    
    if not short_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=short_signals.index,
                y=short_signals['High'] * 1.005,
                mode='markers',
                name='Signal Short',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color='#F44336',
                    line=dict(color='white', width=1)
                )
            )
        )
    
    # Trades
    for trade in trades:
        entry_color = '#4CAF50' if trade['Type'] == 'Long' else '#F44336'
        exit_color = '#FF9800' if trade['Reason'] == 'Take Profit' else '#F44336'
        
        # Ligne d'entrée à sortie
        fig.add_trace(
            go.Scatter(
                x=[trade['EntryIndex'], trade['ExitIndex']],
                y=[trade['Entry'], trade['Exit']],
                mode='lines+markers',
                name=f"{trade['Type']} {trade['Reason']}",
                line=dict(color=entry_color, width=2),
                marker=dict(
                    size=8,
                    color=[entry_color, exit_color],
                    symbol=['circle', 'diamond']
                ),
                showlegend=False
            )
        )
    
    # Mise à jour du layout
    fig.update_layout(
        title=f'Analyse Technique {symbol} {timeframe} - Stratégie Breakout',
        xaxis_title='Temps',
        yaxis_title='Prix',
        template='plotly_dark',
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_performance_chart(trades, symbol, timeframe):
    """Crée un graphique de performance simple"""
    
    if not trades:
        return None
    
    df_trades = pd.DataFrame(trades)
    df_trades['Cumulative_PnL'] = df_trades['PnL'].cumsum()
    df_trades['Trade_Number'] = range(1, len(df_trades) + 1)
    
    fig = go.Figure()
    
    # Performance cumulative
    fig.add_trace(
        go.Scatter(
            x=df_trades['Trade_Number'],
            y=df_trades['Cumulative_PnL'] * 100,
            mode='lines+markers',
            name='PnL Cumulatif (%)',
            line=dict(color='#4CAF50' if df_trades['Cumulative_PnL'].iloc[-1] > 0 else '#F44336', width=2)
        )
    )
    
    fig.update_layout(
        title=f'Performance {symbol} {timeframe}',
        xaxis_title='Numéro de Trade',
        yaxis_title='PnL Cumulatif (%)',
        template='plotly_dark',
        height=400
    )
    
    return fig

def main():
    print("📊 Générateur de Graphiques Simplifié")
    print("=" * 45)
    
    SYMBOLS = ['XAUUSD', 'US30.cash', 'EURUSD', 'GER40.cash']
    TIMEFRAMES = ['D1', 'H4', 'H1']
    
    # Création du dossier pour les graphiques
    os.makedirs("charts", exist_ok=True)
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            filename = f"datas/{symbol}_{timeframe}_mt5.csv"
            if os.path.exists(filename):
                print(f"📈 Création du graphique pour {symbol} {timeframe}...")
                
                # Chargement et traitement des données
                df = pd.read_csv(filename)
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Génération des signaux et trades
                df_signals, trades = simple_breakout_strategy_with_signals(df, symbol, timeframe)
                
                if len(trades) > 0:
                    # Création du graphique principal
                    chart = create_simple_chart(df_signals, trades, symbol, timeframe)
                    chart.write_html(f"charts/{symbol}_{timeframe}_chart.html")
                    
                    # Création du graphique de performance
                    perf_chart = create_performance_chart(trades, symbol, timeframe)
                    if perf_chart:
                        perf_chart.write_html(f"charts/{symbol}_{timeframe}_performance.html")
                    
                    # Calcul des statistiques
                    df_trades = pd.DataFrame(trades)
                    total_pnl = df_trades['PnL'].sum()
                    trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
                    win_rate = trades_gagnants / len(trades) * 100
                    
                    print(f"  ✅ Graphiques créés: {len(trades)} trades, {win_rate:.1f}% win rate, {total_pnl:.2%} PnL")
                else:
                    print(f"  ⚠️ Aucun trade pour {symbol} {timeframe}")
    
    print(f"\n🎉 Graphiques générés dans le dossier 'charts/'")
    print("📁 Fichiers créés:")
    print("   - *_chart.html : Graphiques techniques avec signaux")
    print("   - *_performance.html : Graphiques de performance")
    print("\n💡 Ouvrez les fichiers .html dans votre navigateur pour voir les graphiques !")

if __name__ == "__main__":
    main() 