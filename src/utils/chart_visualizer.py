import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
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
    df['RSI'] = compute_rsi(df, 14)
    
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

def create_interactive_chart(df, trades, symbol, timeframe):
    """Crée un graphique interactif style TradingView"""
    
    # Création du subplot
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} {timeframe} - Prix & Signaux', 'RSI', 'Volume'),
        row_heights=[0.6, 0.2, 0.2]
    )
    
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
        ),
        row=1, col=1
    )
    
    # EMAs
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EMA20'],
            mode='lines',
            name='EMA20',
            line=dict(color='#FF9800', width=1)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EMA50'],
            mode='lines',
            name='EMA50',
            line=dict(color='#2196F3', width=2)
        ),
        row=1, col=1
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
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Low_Break'],
            mode='lines',
            name='Support Breakout',
            line=dict(color='#4CAF50', width=1, dash='dash'),
            opacity=0.7
        ),
        row=1, col=1
    )
    
    # Signaux d'entrée
    long_signals = df[df['Long_Signal']]
    short_signals = df[df['Short_Signal']]
    
    if not long_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=long_signals.index,
                y=long_signals['Low'] * 0.995,  # Légèrement en dessous
                mode='markers',
                name='Signal Long',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='#4CAF50',
                    line=dict(color='white', width=1)
                )
            ),
            row=1, col=1
        )
    
    if not short_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=short_signals.index,
                y=short_signals['High'] * 1.005,  # Légèrement au-dessus
                mode='markers',
                name='Signal Short',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color='#F44336',
                    line=dict(color='white', width=1)
                )
            ),
            row=1, col=1
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
            ),
            row=1, col=1
        )
    
    # RSI
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['RSI'],
            mode='lines',
            name='RSI',
            line=dict(color='#9C27B0', width=1)
        ),
        row=2, col=1
    )
    
    # Lignes RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
    
    # Volume
    colors = ['#26A69A' if close >= open else '#EF5350' 
              for close, open in zip(df['Close'], df['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        ),
        row=3, col=1
    )
    
    # Volume MA
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Volume_MA'],
            mode='lines',
            name='Volume MA',
            line=dict(color='#FF9800', width=1)
        ),
        row=3, col=1
    )
    
    # Mise à jour du layout
    fig.update_layout(
        title=f'Analyse Technique {symbol} {timeframe} - Stratégie Breakout',
        xaxis_title='Temps',
        yaxis_title='Prix',
        template='plotly_dark',
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Mise à jour des axes
    fig.update_xaxes(title_text="Temps", row=3, col=1)
    fig.update_yaxes(title_text="Prix", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="Volume", row=3, col=1)
    
    return fig

def create_performance_dashboard(trades, symbol, timeframe):
    """Crée un dashboard de performance"""
    
    if not trades:
        return None
    
    df_trades = pd.DataFrame(trades)
    
    # Calculs de performance
    total_pnl = df_trades['PnL'].sum()
    performance = (1 + total_pnl) ** (252 / len(trades)) - 1 if len(trades) > 0 else 0
    trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
    trades_perdants = len(df_trades[df_trades['PnL'] < 0])
    win_rate = trades_gagnants / len(trades) * 100 if len(trades) > 0 else 0
    
    # Graphique de performance cumulative
    df_trades['Cumulative_PnL'] = df_trades['PnL'].cumsum()
    df_trades['Trade_Number'] = range(1, len(df_trades) + 1)
    
    # Création de graphiques séparés pour éviter les conflits
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Performance Cumulative', 'Distribution des PnL', 'Taux de Réussite', 'PnL par Trade'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Performance cumulative
    fig.add_trace(
        go.Scatter(
            x=df_trades['Trade_Number'],
            y=df_trades['Cumulative_PnL'] * 100,
            mode='lines+markers',
            name='PnL Cumulatif (%)',
            line=dict(color='#4CAF50' if total_pnl > 0 else '#F44336', width=2)
        ),
        row=1, col=1
    )
    
    # Distribution des PnL
    fig.add_trace(
        go.Histogram(
            x=df_trades['PnL'] * 100,
            nbinsx=20,
            name='Distribution PnL',
            marker_color='#2196F3',
            opacity=0.7
        ),
        row=1, col=2
    )
    
    # Taux de réussite (bar chart au lieu de pie chart)
    fig.add_trace(
        go.Bar(
            x=['Gagnants', 'Perdants'],
            y=[trades_gagnants, trades_perdants],
            name='Taux de Réussite',
            marker_color=['#4CAF50', '#F44336']
        ),
        row=2, col=1
    )
    
    # PnL par trade
    colors = ['#4CAF50' if pnl > 0 else '#F44336' for pnl in df_trades['PnL']]
    fig.add_trace(
        go.Bar(
            x=df_trades['Trade_Number'],
            y=df_trades['PnL'] * 100,
            name='PnL par Trade (%)',
            marker_color=colors
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title=f'Dashboard Performance {symbol} {timeframe}',
        template='plotly_dark',
        height=600,
        showlegend=False
    )
    
    return fig

def main():
    print("📊 Générateur de Graphiques Interactifs")
    print("=" * 50)
    
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
                    chart = create_interactive_chart(df_signals, trades, symbol, timeframe)
                    chart.write_html(f"charts/{symbol}_{timeframe}_chart.html")
                    
                    # Création du dashboard de performance
                    dashboard = create_performance_dashboard(trades, symbol, timeframe)
                    if dashboard:
                        dashboard.write_html(f"charts/{symbol}_{timeframe}_dashboard.html")
                    
                    print(f"  ✅ Graphiques créés: {len(trades)} trades")
                else:
                    print(f"  ⚠️ Aucun trade pour {symbol} {timeframe}")
    
    print(f"\n🎉 Graphiques générés dans le dossier 'charts/'")
    print("📁 Fichiers créés:")
    print("   - *_chart.html : Graphiques techniques interactifs")
    print("   - *_dashboard.html : Dashboards de performance")
    print("\n💡 Ouvrez les fichiers .html dans votre navigateur pour voir les graphiques !")

if __name__ == "__main__":
    main() 