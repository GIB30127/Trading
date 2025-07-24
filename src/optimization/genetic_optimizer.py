import os
import pandas as pd
import numpy as np
import random
from deap import base, creator, tools, algorithms
from rich import print
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# === Configuration de l'algorithme génétique ===
POPULATION_SIZE = 50
GENERATIONS = 30
CROSSOVER_PROB = 0.7
MUTATION_PROB = 0.3

# === Paramètres à optimiser ===
PARAM_RANGES = {
    'PERIODE_EMA': (20, 100),
    'PERIODE_ADX': (10, 20),
    'PERIODE_BREAKOUT': (5, 20),
    'SEUIL_ADX': (8, 25),
    'RISK_ATR': (1.0, 3.0),
    'PROFIT_TARGET': (1.5, 5.0),
    'TRAILING_STOP': (0.8, 2.0)
}

# === Fonctions indicateurs (copiées de la stratégie) ===
def compute_ema(series, window):
    return series.ewm(span=window, adjust=False).mean()

def compute_atr(df, window):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_adx(df, window):
    plus_dm = df['High'].diff()
    minus_dm = df['Low'].diff().abs()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    trur = compute_atr(df, window)
    plus_di = 100 * (plus_dm.rolling(window=window).sum() / trur)
    minus_di = 100 * (minus_dm.rolling(window=window).sum() / trur)
    dx = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=window).mean()
    return adx

def calc_fib_extensions(entry, swing_high, swing_low, direction):
    fibs = {}
    if direction == 'Long':
        range_ = swing_high - swing_low
        fibs['Fib_1.618'] = swing_high + 1.618 * range_
        fibs['Fib_2.618'] = swing_high + 2.618 * range_
    else:
        range_ = swing_high - swing_low
        fibs['Fib_1.618'] = swing_low - 1.618 * range_
        fibs['Fib_2.618'] = swing_low - 2.618 * range_
    return fibs

# === Fonction de backtest avec paramètres variables ===
def backtest_with_params(df, params):
    df = df.copy()
    
    # Extraction des paramètres
    PERIODE_EMA = int(params['PERIODE_EMA'])
    PERIODE_ADX = int(params['PERIODE_ADX'])
    PERIODE_ATR = 14  # Fixe
    PERIODE_BREAKOUT = int(params['PERIODE_BREAKOUT'])
    SEUIL_ADX = params['SEUIL_ADX']
    RISK_ATR = params['RISK_ATR']
    PROFIT_TARGET = params['PROFIT_TARGET']
    TRAILING_STOP = params['TRAILING_STOP']
    
    # Calcul des indicateurs
    df['EMA'] = compute_ema(df['Close'], PERIODE_EMA)
    df['ATR'] = compute_atr(df, PERIODE_ATR)
    df['ADX'] = compute_adx(df, PERIODE_ADX)
    df['High_Break'] = df['High'].rolling(window=PERIODE_BREAKOUT).max()
    df['Low_Break'] = df['Low'].rolling(window=PERIODE_BREAKOUT).min()
    df = df.dropna().reset_index(drop=True)

    position = 0
    entry_price = 0
    stop_loss = 0
    profit_target_price = 0
    trailing_stop = 0
    trades = []

    for i in range(1, len(df)):
        ema_long = df.loc[i, 'Close'] > df.loc[i, 'EMA']
        ema_short = df.loc[i, 'Close'] < df.loc[i, 'EMA']
        breakout_long = (df.loc[i-1, 'High'] < df.loc[i-1, 'High_Break'] and 
                        df.loc[i, 'High'] >= df.loc[i, 'High_Break'])
        breakout_short = (df.loc[i-1, 'Low'] > df.loc[i-1, 'Low_Break'] and 
                         df.loc[i, 'Low'] <= df.loc[i, 'Low_Break'])
        adx_ok = df.loc[i, 'ADX'] > SEUIL_ADX
        
        long_cond = ema_long and breakout_long and adx_ok
        short_cond = ema_short and breakout_short and adx_ok

        if position == 0:
            if long_cond:
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - RISK_ATR * df.loc[i, 'ATR']
                profit_target_price = entry_price + PROFIT_TARGET * df.loc[i, 'ATR']
                trailing_stop = entry_price - TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Long')
                
            elif short_cond:
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + RISK_ATR * df.loc[i, 'ATR']
                profit_target_price = entry_price - PROFIT_TARGET * df.loc[i, 'ATR']
                trailing_stop = entry_price + TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Short')

        elif position == 1:  # Position Long
            new_trailing_stop = df.loc[i, 'Close'] - TRAILING_STOP * df.loc[i, 'ATR']
            if new_trailing_stop > trailing_stop:
                trailing_stop = new_trailing_stop
            
            if df.loc[i, 'Low'] <= stop_loss:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (stop_loss - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 0
            elif df.loc[i, 'High'] >= profit_target_price:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': profit_target_price,
                    'PnL': (profit_target_price - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 0
            elif df.loc[i, 'Low'] <= trailing_stop:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': (trailing_stop - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 0
            elif short_cond:
                trades.append({
                    'Type': 'Long',
                    'Entry': entry_price,
                    'Exit': df.loc[i, 'Close'],
                    'PnL': (df.loc[i, 'Close'] - entry_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = -1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price + RISK_ATR * df.loc[i, 'ATR']
                profit_target_price = entry_price - PROFIT_TARGET * df.loc[i, 'ATR']
                trailing_stop = entry_price + TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Short')

        elif position == -1:  # Position Short
            new_trailing_stop = df.loc[i, 'Close'] + TRAILING_STOP * df.loc[i, 'ATR']
            if new_trailing_stop < trailing_stop:
                trailing_stop = new_trailing_stop
            
            if df.loc[i, 'High'] >= stop_loss:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': stop_loss,
                    'PnL': (entry_price - stop_loss) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 0
            elif df.loc[i, 'Low'] <= profit_target_price:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': profit_target_price,
                    'PnL': (entry_price - profit_target_price) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 0
            elif df.loc[i, 'High'] >= trailing_stop:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': trailing_stop,
                    'PnL': (entry_price - trailing_stop) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 0
            elif long_cond:
                trades.append({
                    'Type': 'Short',
                    'Entry': entry_price,
                    'Exit': df.loc[i, 'Close'],
                    'PnL': (entry_price - df.loc[i, 'Close']) / entry_price,
                    'EntryDate': entry_date,
                    'ExitDate': df.loc[i, 'Date'] if 'Date' in df.columns else i,
                    **fibs
                })
                position = 1
                entry_price = df.loc[i, 'Close']
                stop_loss = entry_price - RISK_ATR * df.loc[i, 'ATR']
                profit_target_price = entry_price + PROFIT_TARGET * df.loc[i, 'ATR']
                trailing_stop = entry_price - TRAILING_STOP * df.loc[i, 'ATR']
                entry_date = df.loc[i, 'Date'] if 'Date' in df.columns else i
                swing_high = df.loc[i-1, 'High_Break']
                swing_low = df.loc[i-1, 'Low_Break']
                fibs = calc_fib_extensions(entry_price, swing_high, swing_low, 'Long')

    return trades

# === Fonction de fitness ===
def evaluate_fitness(individual, symbol, timeframe):
    """Évalue la fitness d'un individu (ensemble de paramètres)"""
    try:
        # Conversion de l'individu en paramètres
        params = {}
        for i, (param_name, (min_val, max_val)) in enumerate(PARAM_RANGES.items()):
            if param_name in ['PERIODE_EMA', 'PERIODE_ADX', 'PERIODE_BREAKOUT']:
                params[param_name] = int(min_val + individual[i] * (max_val - min_val))
            else:
                params[param_name] = min_val + individual[i] * (max_val - min_val)
        
        # Chargement des données
        filename = f"datas/{symbol}_{timeframe}_mt5.csv"
        if not os.path.exists(filename):
            return -1000,  # Pénalité si fichier inexistant
        
        df = pd.read_csv(filename)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Backtest
        trades = backtest_with_params(df, params)
        
        if not trades:
            return -1000  # Pénalité si aucun trade
        
        # Calcul des métriques
        df_trades = pd.DataFrame(trades)
        total_pnl = df_trades['PnL'].sum()
        
        if total_pnl <= 0:
            return total_pnl * 100  # Pénalité forte pour pertes
        
        # Calcul du Sharpe Ratio
        returns = df_trades['PnL']
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Taux de réussite
        trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
        win_rate = trades_gagnants / len(trades) if len(trades) > 0 else 0
        
        # Score composite
        performance = (1 + total_pnl) ** (252 / len(trades)) - 1 if len(trades) > 0 else 0
        
        # Fitness = Performance + Sharpe + Win Rate + Pénalité pour trop de trades
        fitness = (performance * 100 + sharpe * 10 + win_rate * 50 - 
                  max(0, len(trades) - 200) * 0.1)  # Pénalité pour sur-trading
        
        return fitness
        
    except Exception as e:
        return -1000  # Pénalité en cas d'erreur

# === Configuration DEAP ===
def setup_genetic_algorithm():
    # Création des types
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    
    toolbox = base.Toolbox()
    
    # Attributs
    toolbox.register("attr_float", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, 
                     toolbox.attr_float, n=len(PARAM_RANGES))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Opérateurs génétiques
    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.2)
    toolbox.register("select", tools.selTournament, tournsize=3)
    
    return toolbox

# === Fonction d'optimisation principale ===
def optimize_strategy(symbol, timeframe):
    print(f"🧬 Optimisation génétique pour {symbol} {timeframe}")
    print("=" * 50)
    
    toolbox = setup_genetic_algorithm()
    
    # Population initiale
    pop = toolbox.population(n=POPULATION_SIZE)
    
    # Statistiques
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)
    
    # Hall of fame pour garder le meilleur
    hof = tools.HallOfFame(1)
    
    # Algorithme génétique
    pop, logbook = algorithms.eaSimple(pop, toolbox, 
                                      cxpb=CROSSOVER_PROB, 
                                      mutpb=MUTATION_PROB, 
                                      ngen=GENERATIONS, 
                                      stats=stats, 
                                      halloffame=hof, 
                                      verbose=True)
    
    # Meilleur individu
    best_individual = hof[0]
    best_fitness = best_individual.fitness.values[0]
    
    # Conversion en paramètres
    best_params = {}
    for i, (param_name, (min_val, max_val)) in enumerate(PARAM_RANGES.items()):
        if param_name in ['PERIODE_EMA', 'PERIODE_ADX', 'PERIODE_BREAKOUT']:
            best_params[param_name] = int(min_val + best_individual[i] * (max_val - min_val))
        else:
            best_params[param_name] = min_val + best_individual[i] * (max_val - min_val)
    
    print(f"\n🏆 Meilleurs paramètres trouvés pour {symbol} {timeframe}:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    print(f"  Fitness: {best_fitness:.2f}")
    
    return best_params, best_fitness

def main():
    print("🧬 Optimisation génétique de la stratégie EMA/ADX/ATR/Breakout")
    print("=" * 60)
    
    SYMBOLS = ['XAUUSD', 'US30.cash']  # Focus sur les instruments problématiques
    TIMEFRAMES = ['D1', 'H1']  # Focus sur les timeframes principaux
    
    results = {}
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            print(f"\n🎯 Optimisation de {symbol} {timeframe}...")
            best_params, fitness = optimize_strategy(symbol, timeframe)
            results[f"{symbol}_{timeframe}"] = {
                'params': best_params,
                'fitness': fitness
            }
    
    # Sauvegarde des résultats
    os.makedirs("genetic_results", exist_ok=True)
    
    with open("genetic_results/optimized_parameters.md", 'w', encoding='utf-8') as f:
        f.write("# Paramètres optimisés par algorithme génétique\n\n")
        
        for key, result in results.items():
            f.write(f"## {key}\n")
            f.write(f"- Fitness: {result['fitness']:.2f}\n")
            f.write("- Paramètres:\n")
            for param, value in result['params'].items():
                f.write(f"  - {param}: {value}\n")
            f.write("\n")
    
    print(f"\n✅ Optimisation terminée ! Résultats sauvegardés dans genetic_results/")
    
    # Test des paramètres optimisés
    print(f"\n🧪 Test des paramètres optimisés...")
    test_optimized_strategy(results)

def test_optimized_strategy(results):
    """Teste la stratégie avec les paramètres optimisés"""
    for key, result in results.items():
        symbol, timeframe = key.split('_')
        params = result['params']
        
        filename = f"datas/{symbol}_{timeframe}_mt5.csv"
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            df['Date'] = pd.to_datetime(df['Date'])
            trades = backtest_with_params(df, params)
            
            if trades:
                df_trades = pd.DataFrame(trades)
                total_pnl = df_trades['PnL'].sum()
                performance = (1 + total_pnl) ** (252 / len(trades)) - 1
                returns = df_trades['PnL']
                sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                trades_gagnants = len(df_trades[df_trades['PnL'] > 0])
                win_rate = trades_gagnants / len(trades)
                
                print(f"\n📊 Résultats optimisés pour {symbol} {timeframe}:")
                print(f"  Performance: {performance:.2%}")
                print(f"  Sharpe: {sharpe:.2f}")
                print(f"  Win Rate: {win_rate:.1%}")
                print(f"  Trades: {len(trades)}")

if __name__ == "__main__":
    main() 