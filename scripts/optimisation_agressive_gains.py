#!/usr/bin/env python3
"""
Optimisation Agressive pour Maximiser les Gains
Objectifs: Gros gains, petit drawdown, minimum 5 pips par trade
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import random
import warnings
warnings.filterwarnings('ignore')

# Ajout du chemin pour importer les modules
sys.path.append('src/strategies')
from strategie_xauusd_sharpe1_simple import calculate_metrics

class AggressiveOptimizer:
    def __init__(self, symbol="XAUUSD", timeframe="D1", population_size=100, generations=50):
        self.symbol = symbol
        self.timeframe = timeframe
        self.population_size = population_size
        self.generations = generations
        
        # Chargement des données
        self.df = self.load_data()
        
        # Paramètres étendus à optimiser
        self.param_ranges = {
            # Paramètres de base
            'breakout_period': (1, 10),
            'profit_atr': (2.0, 8.0),  # Augmenté pour plus de gains
            'rsi_overbought': (65, 95),
            'rsi_oversold': (5, 35),
            'ema_short': (2, 15),
            'ema_long': (5, 30),
            'atr_period': (3, 20),
            'trail_atr': (0.2, 3.0),
            'stop_loss_atr': (0.8, 5.0),
            'max_positions': (1, 5),
            'risk_per_trade': (0.3, 5.0),
            
            # Nouveaux paramètres pour gains agressifs
            'min_pips_filter': (3, 15),  # Filtre minimum de pips
            'volatility_filter': (0.5, 3.0),  # Filtre de volatilité
            'momentum_strength': (0.5, 3.0),  # Force du momentum
            'volume_filter': (0.3, 2.0),  # Filtre de volume
            'trend_strength': (0.5, 3.0),  # Force de la tendance
            'max_hold_time': (1, 50),  # Temps max de détention (bougies)
            'profit_lock': (0.5, 3.0),  # Verrouillage des profits
            'breakout_confirmation': (1, 5),  # Confirmation du breakout
            'rsi_filter': (10, 40),  # Filtre RSI supplémentaire
            'atr_threshold': (0.5, 3.0),  # Seuil ATR minimum
            'correlation_filter': (0.3, 2.0),  # Filtre de corrélation
            'time_filter_start': (0, 23),  # Filtre horaire début
            'time_filter_end': (0, 23),  # Filtre horaire fin
            'news_filter': (0, 1),  # Filtre news (0=off, 1=on)
            'weekend_filter': (0, 1),  # Filtre weekend
        }
        
        self.best_individual = None
        self.best_fitness = float('-inf')
        self.history = []
    
    def load_data(self):
        """Charge les données"""
        csv_path = f"data/raw/{self.symbol}_{self.timeframe}_mt5.csv"
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Fichier non trouvé: {csv_path}")
        
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def create_individual(self):
        """Crée un individu avec des paramètres aléatoires"""
        individual = {}
        for param, (min_val, max_val) in self.param_ranges.items():
            if isinstance(min_val, int):
                individual[param] = random.randint(min_val, max_val)
            else:
                individual[param] = round(random.uniform(min_val, max_val), 2)
        return individual
    
    def create_population(self):
        """Crée une population initiale"""
        return [self.create_individual() for _ in range(self.population_size)]
    
    def evaluate_fitness(self, individual):
        """Évalue la fitness avec objectifs agressifs"""
        try:
            trades, df_signals = self.apply_strategy_with_params(individual)
            
            if len(trades) < 20:  # Minimum de trades
                return float('-inf')
            
            metrics = calculate_metrics(trades)
            
            # Critères de fitness agressifs
            # 1. Gain total (priorité maximale)
            total_gain = metrics['total_return']
            
            # 2. Drawdown (doit rester faible)
            drawdown_penalty = max(0, metrics['max_drawdown'] - 20) * 15  # Pénalité forte si > 20%
            
            # 3. Win rate (bonus pour > 55%)
            win_rate_bonus = max(0, metrics['win_rate'] - 55) * 2
            
            # 4. Profit factor (bonus pour > 3)
            profit_factor_bonus = max(0, metrics['profit_factor'] - 3) * 10
            
            # 5. Taille moyenne des gains
            avg_win = metrics.get('avg_win', 0)
            avg_win_bonus = max(0, avg_win - 2) * 5  # Bonus pour gains > 2%
            
            # 6. Nombre de trades (bonus pour plus de trades)
            trades_bonus = min(metrics['total_trades'] / 100, 5)  # Max 5 points
            
            # 7. Sharpe ratio
            sharpe_bonus = max(0, metrics['sharpe_ratio'] - 2) * 2
            
            # 8. Pénalité pour trades trop petits
            small_trades_penalty = 0
            if len(trades) > 0:
                small_trades = sum(1 for trade in trades if abs(trade.get('pnl', 0)) < 0.5)
                small_trades_penalty = (small_trades / len(trades)) * 10
            
            # Fitness = gains - pénalités + bonus
            fitness = (total_gain * 0.3) - drawdown_penalty + win_rate_bonus + profit_factor_bonus + avg_win_bonus + trades_bonus + sharpe_bonus - small_trades_penalty
            
            # Stockage des métriques
            individual['metrics'] = metrics
            individual['fitness'] = fitness
            
            return fitness
            
        except Exception as e:
            print(f"Erreur évaluation: {e}")
            return float('-inf')
    
    def apply_strategy_with_params(self, params):
        """Applique la stratégie avec paramètres optimisés"""
        return self.strategie_agressive(self.df, self.symbol, self.timeframe, params)
    
    def strategie_agressive(self, df, symbol, timeframe, params):
        """Stratégie agressive avec tous les paramètres optimisés"""
        
        df = df.copy()
        
        # Paramètres de base
        breakout_period = int(params['breakout_period'])
        profit_atr = params['profit_atr']
        rsi_overbought = params['rsi_overbought']
        rsi_oversold = params['rsi_oversold']
        ema_short = int(params['ema_short'])
        ema_long = int(params['ema_long'])
        atr_period = int(params['atr_period'])
        trail_atr = params['trail_atr']
        stop_loss_atr = params['stop_loss_atr']
        max_positions = int(params['max_positions'])
        risk_per_trade = params['risk_per_trade']
        
        # Nouveaux paramètres
        min_pips_filter = params['min_pips_filter']
        volatility_filter = params['volatility_filter']
        momentum_strength = params['momentum_strength']
        volume_filter = params['volume_filter']
        trend_strength = params['trend_strength']
        max_hold_time = int(params['max_hold_time'])
        profit_lock = params['profit_lock']
        breakout_confirmation = int(params['breakout_confirmation'])
        rsi_filter = params['rsi_filter']
        atr_threshold = params['atr_threshold']
        correlation_filter = params['correlation_filter']
        time_filter_start = int(params['time_filter_start'])
        time_filter_end = int(params['time_filter_end'])
        news_filter = bool(params['news_filter'])
        weekend_filter = bool(params['weekend_filter'])
        
        # Calcul des indicateurs avancés
        df['ATR'] = self.calculate_atr(df, atr_period)
        df['RSI'] = self.calculate_rsi(df['Close'], 8)
        df['EMA_Short'] = df['Close'].ewm(span=ema_short).mean()
        df['EMA_Long'] = df['Close'].ewm(span=ema_long).mean()
        df['High_Break'] = df['High'].rolling(window=breakout_period).max()
        df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
        
        # Indicateurs supplémentaires
        df['Volatility'] = df['ATR'] / df['Close'] * 100
        df['Momentum'] = df['Close'].pct_change(periods=3)
        df['Trend_Strength'] = abs(df['EMA_Short'] - df['EMA_Long']) / df['EMA_Long'] * 100
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['RSI_MA'] = df['RSI'].rolling(window=10).mean()
        
        # Filtres avancés
        df['Min_Pips_OK'] = df['ATR'] >= min_pips_filter * 0.0001  # Conversion en pips
        df['Volatility_OK'] = df['Volatility'] >= atr_threshold
        df['Momentum_OK'] = abs(df['Momentum']) >= momentum_strength * 0.001
        df['Volume_OK'] = df['Volume'] >= df['Volume_MA'] * volume_filter
        df['Trend_OK'] = df['Trend_Strength'] >= trend_strength
        df['RSI_Filter_OK'] = (df['RSI'] > rsi_filter) & (df['RSI'] < (100 - rsi_filter))
        
        # Filtres temporels
        df['Hour'] = df['Date'].dt.hour
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Time_OK'] = (df['Hour'] >= time_filter_start) & (df['Hour'] <= time_filter_end)
        df['Weekend_OK'] = ~weekend_filter | (df['DayOfWeek'] < 5)  # Lundi-Vendredi
        
        # Conditions d'entrée améliorées
        df['Breakout_Up'] = (
            (df['High'].shift(1) < df['High_Break'].shift(1)) & 
            (df['High'] >= df['High_Break']) &
            (df['High'] - df['High_Break'].shift(1)) >= min_pips_filter * 0.0001  # Minimum pips
        )
        
        df['Breakout_Down'] = (
            (df['Low'].shift(1) > df['Low_Break'].shift(1)) & 
            (df['Low'] <= df['Low_Break']) &
            (df['Low_Break'].shift(1) - df['Low']) >= min_pips_filter * 0.0001  # Minimum pips
        )
        
        # Confirmation du breakout
        for i in range(1, breakout_confirmation + 1):
            df[f'Breakout_Up_Conf_{i}'] = df['High'].shift(-i) > df['High_Break']
            df[f'Breakout_Down_Conf_{i}'] = df['Low'].shift(-i) < df['Low_Break']
        
        # Signaux finaux avec tous les filtres
        df['Long_Signal'] = (
            df['Breakout_Up'] &
            df['EMA_Short'] > df['EMA_Long'] * (1 + trend_strength * 0.001) &
            df['Close'] > df['EMA_Short'] &
            df['RSI'] < rsi_overbought &
            df['RSI'] > rsi_filter &
            df['Min_Pips_OK'] &
            df['Volatility_OK'] &
            df['Momentum_OK'] &
            df['Volume_OK'] &
            df['Trend_OK'] &
            df['RSI_Filter_OK'] &
            df['Time_OK'] &
            df['Weekend_OK']
        )
        
        df['Short_Signal'] = (
            df['Breakout_Down'] &
            df['EMA_Short'] < df['EMA_Long'] * (1 - trend_strength * 0.001) &
            df['Close'] < df['EMA_Short'] &
            df['RSI'] > rsi_oversold &
            df['RSI'] < (100 - rsi_filter) &
            df['Min_Pips_OK'] &
            df['Volatility_OK'] &
            df['Momentum_OK'] &
            df['Volume_OK'] &
            df['Trend_OK'] &
            df['RSI_Filter_OK'] &
            df['Time_OK'] &
            df['Weekend_OK']
        )
        
        # Simulation des trades avec gestion avancée
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        entry_index = 0
        stop_loss = 0
        take_profit = 0
        trailing_stop = 0
        positions_count = 0
        profit_locked = False
        
        for i in range(len(df)):
            if i < 50:  # Skip les premières bougies
                continue
                
            current_price = df['Close'].iloc[i]
            current_date = df['Date'].iloc[i]
            current_atr = df['ATR'].iloc[i]
            
            # Gestion des positions existantes
            if position != 0:
                # Vérification du temps de détention
                if i - entry_index >= max_hold_time:
                    # Sortie par temps
                    exit_price = current_price
                    pnl = (exit_price - entry_price) / entry_price * 100 if position == 1 else (entry_price - exit_price) / entry_price * 100
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': 'Long' if position == 1 else 'Short',
                        'pnl': pnl,
                        'exit_reason': 'Time_Exit'
                    })
                    position = 0
                    positions_count -= 1
                    profit_locked = False
                    continue
                
                # Stop loss et take profit
                if position == 1:  # Long
                    if current_price <= stop_loss:
                        exit_price = stop_loss
                        pnl = (exit_price - entry_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position': 'Long',
                            'pnl': pnl,
                            'exit_reason': 'Stop_Loss'
                        })
                        position = 0
                        positions_count -= 1
                        profit_locked = False
                        continue
                    
                    if current_price >= take_profit:
                        exit_price = take_profit
                        pnl = (exit_price - entry_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position': 'Long',
                            'pnl': pnl,
                            'exit_reason': 'Take_Profit'
                        })
                        position = 0
                        positions_count -= 1
                        profit_locked = False
                        continue
                    
                    # Verrouillage des profits
                    if not profit_locked and pnl >= profit_lock:
                        profit_locked = True
                        trailing_stop = entry_price + (trail_atr * current_atr)
                    
                    # Trailing stop
                    if profit_locked:
                        new_trailing_stop = current_price - (trail_atr * current_atr)
                        if new_trailing_stop > trailing_stop:
                            trailing_stop = new_trailing_stop
                        elif current_price <= trailing_stop:
                            exit_price = trailing_stop
                            pnl = (exit_price - entry_price) / entry_price * 100
                            trades.append({
                                'entry_date': entry_date,
                                'exit_date': current_date,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'position': 'Long',
                                'pnl': pnl,
                                'exit_reason': 'Trailing_Stop'
                            })
                            position = 0
                            positions_count -= 1
                            profit_locked = False
                            continue
                
                else:  # Short position
                    if current_price >= stop_loss:
                        exit_price = stop_loss
                        pnl = (entry_price - exit_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position': 'Short',
                            'pnl': pnl,
                            'exit_reason': 'Stop_Loss'
                        })
                        position = 0
                        positions_count -= 1
                        profit_locked = False
                        continue
                    
                    if current_price <= take_profit:
                        exit_price = take_profit
                        pnl = (entry_price - exit_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position': 'Short',
                            'pnl': pnl,
                            'exit_reason': 'Take_Profit'
                        })
                        position = 0
                        positions_count -= 1
                        profit_locked = False
                        continue
                    
                    # Verrouillage des profits
                    if not profit_locked and pnl >= profit_lock:
                        profit_locked = True
                        trailing_stop = entry_price - (trail_atr * current_atr)
                    
                    # Trailing stop
                    if profit_locked:
                        new_trailing_stop = current_price + (trail_atr * current_atr)
                        if new_trailing_stop < trailing_stop or trailing_stop == 0:
                            trailing_stop = new_trailing_stop
                        elif current_price >= trailing_stop:
                            exit_price = trailing_stop
                            pnl = (entry_price - exit_price) / entry_price * 100
                            trades.append({
                                'entry_date': entry_date,
                                'exit_date': current_date,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'position': 'Short',
                                'pnl': pnl,
                                'exit_reason': 'Trailing_Stop'
                            })
                            position = 0
                            positions_count -= 1
                            profit_locked = False
                            continue
            
            # Nouvelles entrées
            if position == 0 and positions_count < max_positions:
                if df['Long_Signal'].iloc[i]:
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    entry_index = i
                    stop_loss = entry_price - (stop_loss_atr * current_atr)
                    take_profit = entry_price + (profit_atr * current_atr)
                    trailing_stop = entry_price - (trail_atr * current_atr)
                    positions_count += 1
                    profit_locked = False
                
                elif df['Short_Signal'].iloc[i]:
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    entry_index = i
                    stop_loss = entry_price + (stop_loss_atr * current_atr)
                    take_profit = entry_price - (profit_atr * current_atr)
                    trailing_stop = entry_price + (trail_atr * current_atr)
                    positions_count += 1
                    profit_locked = False
        
        return trades, df
    
    def calculate_atr(self, df, period):
        """Calcule l'ATR"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_rsi(self, prices, period):
        """Calcule le RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def select_parents(self, population, fitness_scores):
        """Sélectionne les parents par tournoi"""
        tournament_size = 5
        parents = []
        
        for _ in range(2):
            tournament = random.sample(range(len(population)), tournament_size)
            tournament_fitness = [fitness_scores[i] for i in tournament]
            winner = tournament[tournament_fitness.index(max(tournament_fitness))]
            parents.append(population[winner])
        
        return parents
    
    def crossover(self, parent1, parent2):
        """Croisement des parents"""
        child = {}
        for param in self.param_ranges.keys():
            if random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child
    
    def mutate(self, individual, mutation_rate=0.15):
        """Mutation d'un individu"""
        mutated = individual.copy()
        
        for param, (min_val, max_val) in self.param_ranges.items():
            if random.random() < mutation_rate:
                if isinstance(min_val, int):
                    mutated[param] = random.randint(min_val, max_val)
                else:
                    mutated[param] = round(random.uniform(min_val, max_val), 2)
        
        return mutated
    
    def optimize(self):
        """Lance l'optimisation agressive"""
        print(f"🔥 OPTIMISATION AGRESSIVE - {self.symbol} {self.timeframe}")
        print(f"Population: {self.population_size}, Générations: {self.generations}")
        print("Objectifs: Gros gains, DD < 20%, minimum 5 pips")
        print("=" * 70)
        
        # Population initiale
        population = self.create_population()
        
        for generation in range(self.generations):
            print(f"\n🔄 Génération {generation + 1}/{self.generations}")
            
            # Évaluation de la population
            fitness_scores = []
            for individual in population:
                fitness = self.evaluate_fitness(individual)
                fitness_scores.append(fitness)
                
                # Mise à jour du meilleur
                if fitness > self.best_fitness:
                    self.best_fitness = fitness
                    self.best_individual = individual.copy()
            
            # Affichage des meilleurs résultats
            best_idx = fitness_scores.index(max(fitness_scores))
            best_individual = population[best_idx]
            best_metrics = best_individual.get('metrics', {})
            
            print(f"📊 Meilleur fitness: {max(fitness_scores):.2f}")
            if best_metrics:
                print(f"   • Trades: {best_metrics.get('total_trades', 0)}")
                print(f"   • Win Rate: {best_metrics.get('win_rate', 0):.2f}%")
                print(f"   • Retour: {best_metrics.get('total_return', 0):.2f}%")
                print(f"   • Drawdown: {best_metrics.get('max_drawdown', 0):.2f}%")
                print(f"   • Profit Factor: {best_metrics.get('profit_factor', 0):.2f}")
                print(f"   • Gain Moyen: {best_metrics.get('avg_win', 0):.2f}%")
            
            # Stockage de l'historique
            self.history.append({
                'generation': generation + 1,
                'best_fitness': max(fitness_scores),
                'avg_fitness': np.mean(fitness_scores),
                'best_metrics': best_metrics
            })
            
            # Création de la nouvelle population
            new_population = []
            
            # Élitisme: garder le meilleur
            new_population.append(self.best_individual)
            
            # Génération des enfants
            while len(new_population) < self.population_size:
                parents = self.select_parents(population, fitness_scores)
                child = self.crossover(parents[0], parents[1])
                child = self.mutate(child)
                new_population.append(child)
            
            population = new_population
        
        # Résultats finaux
        self.save_results()
        
        # Enregistrement du modèle optimal
        if self.best_individual and 'metrics' in self.best_individual:
            self.register_optimal_model()
        
        return self.best_individual
    
    def save_results(self):
        """Sauvegarde les résultats de l'optimisation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"results/optimization/aggressive_optimization_{self.symbol}_{self.timeframe}_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # Sauvegarde des paramètres optimaux
        if self.best_individual:
            optimal_params = {k: v for k, v in self.best_individual.items() if k not in ['metrics', 'fitness']}
            
            with open(f"{results_dir}/parametres_optimaux_agressifs.md", 'w', encoding='utf-8') as f:
                f.write(f"# Paramètres Optimaux Agressifs - {self.symbol} {self.timeframe}\n\n")
                f.write(f"**Date d'optimisation**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Objectifs\n\n")
                f.write("- Gros gains\n")
                f.write("- Drawdown < 20%\n")
                f.write("- Minimum 5 pips par trade\n")
                f.write("- Win rate > 55%\n")
                f.write("- Profit factor > 3\n\n")
                
                f.write("## Paramètres Optimisés\n\n")
                
                for param, value in optimal_params.items():
                    f.write(f"- **{param}**: {value}\n")
                
                if 'metrics' in self.best_individual:
                    metrics = self.best_individual['metrics']
                    f.write(f"\n## Résultats Optimaux\n\n")
                    f.write(f"- **Fitness**: {self.best_fitness:.2f}\n")
                    f.write(f"- **Total Trades**: {metrics.get('total_trades', 0)}\n")
                    f.write(f"- **Win Rate**: {metrics.get('win_rate', 0):.2f}%\n")
                    f.write(f"- **Total Return**: {metrics.get('total_return', 0):.2f}%\n")
                    f.write(f"- **Max Drawdown**: {metrics.get('max_drawdown', 0):.2f}%\n")
                    f.write(f"- **Profit Factor**: {metrics.get('profit_factor', 0):.2f}\n")
                    f.write(f"- **Sharpe Ratio**: {metrics.get('sharpe_ratio', 0):.2f}\n")
                    f.write(f"- **Gain Moyen**: {metrics.get('avg_win', 0):.2f}%\n")
                    f.write(f"- **Perte Moyenne**: {metrics.get('avg_loss', 0):.2f}%\n")
            
            # Sauvegarde de l'historique
            history_df = pd.DataFrame(self.history)
            history_df.to_csv(f"{results_dir}/historique_optimisation_agressive.csv", index=False)
            
            print(f"\n✅ Résultats agressifs sauvegardés: {results_dir}")
    
    def register_optimal_model(self):
        """Enregistre le modèle optimal dans le gestionnaire de modèles"""
        try:
            # Import du gestionnaire de modèles
            sys.path.append('scripts')
            from gestion_modeles_optimaux import ModelManager
            
            manager = ModelManager()
            
            # Préparation des données
            params = {k: v for k, v in self.best_individual.items() if k not in ['metrics', 'fitness']}
            metrics = self.best_individual['metrics']
            
            # Enregistrement
            success = manager.register_model(
                f"Agressif {self.timeframe}",
                params,
                metrics,
                "agressive",
                self.timeframe,
                self.symbol
            )
            
            if success:
                print(f"🏆 Modèle optimal agressif enregistré dans le gestionnaire")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'enregistrement du modèle: {e}")

def main():
    """Fonction principale"""
    print("🔥 OPTIMISATION AGRESSIVE POUR MAXIMISER LES GAINS")
    print("=" * 70)
    
    # Test sur différents timeframes
    timeframes = ['H4', 'D1']  # Timeframes avec meilleur potentiel
    
    for timeframe in timeframes:
        print(f"\n🎯 Optimisation Agressive {timeframe}...")
        
        try:
            optimizer = AggressiveOptimizer(
                symbol="XAUUSD",
                timeframe=timeframe,
                population_size=80,
                generations=30
            )
            
            best_params = optimizer.optimize()
            
            if best_params:
                print(f"\n✅ Optimisation Agressive {timeframe} terminée!")
                print(f"📊 Meilleur fitness: {optimizer.best_fitness:.2f}")
                
                if 'metrics' in best_params:
                    metrics = best_params['metrics']
                    print(f"💰 Gain total: {metrics.get('total_return', 0):.2f}%")
                    print(f"🎯 Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
                    print(f"📈 Profit Factor: {metrics.get('profit_factor', 0):.2f}")
                    print(f"🎯 Win Rate: {metrics.get('win_rate', 0):.2f}%")
        
        except Exception as e:
            print(f"❌ Erreur pour {timeframe}: {e}")
            continue
    
    print(f"\n🎉 Optimisation Agressive terminée!")

if __name__ == "__main__":
    main() 