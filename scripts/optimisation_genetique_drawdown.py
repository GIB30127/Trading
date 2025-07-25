#!/usr/bin/env python3
"""
Optimisation Génétique pour Réduire le Drawdown
Utilise un algorithme génétique pour optimiser les paramètres de la stratégie
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
from strategie_xauusd_sharpe1_simple import strategie_xauusd_sharpe1_simple, calculate_metrics

class GeneticOptimizer:
    def __init__(self, symbol="XAUUSD", timeframe="D1", population_size=50, generations=30):
        self.symbol = symbol
        self.timeframe = timeframe
        self.population_size = population_size
        self.generations = generations
        
        # Chargement des données
        self.df = self.load_data()
        
        # Paramètres à optimiser avec leurs plages
        self.param_ranges = {
            'breakout_period': (1, 5),
            'profit_atr': (1.0, 5.0),
            'rsi_overbought': (70, 95),
            'rsi_oversold': (5, 30),
            'ema_short': (3, 10),
            'ema_long': (8, 20),
            'atr_period': (5, 15),
            'trail_atr': (0.3, 2.0),
            'stop_loss_atr': (1.0, 4.0),  # Nouveau paramètre
            'max_positions': (1, 3),       # Nouveau paramètre
            'risk_per_trade': (0.5, 3.0)   # Nouveau paramètre
        }
        
        self.best_individual = None
        self.best_fitness = float('-inf')
        self.history = []
    
    def load_data(self):
        """Charge les données pour le timeframe spécifié"""
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
        """Évalue la fitness d'un individu (objectif: réduire le drawdown)"""
        try:
            # Application de la stratégie avec les paramètres de l'individu
            trades, df_signals = self.apply_strategy_with_params(individual)
            
            if len(trades) < 10:  # Pas assez de trades
                return float('-inf')
            
            metrics = calculate_metrics(trades)
            
            # Critères de fitness (priorité au drawdown)
            drawdown_penalty = max(0, metrics['max_drawdown'] - 30) * 10  # Pénalité forte si > 30%
            win_rate_bonus = max(0, metrics['win_rate'] - 45) * 0.5       # Bonus pour win rate > 45%
            profit_factor_bonus = max(0, metrics['profit_factor'] - 1.5) * 2  # Bonus pour PF > 1.5
            return_bonus = max(0, metrics['total_return'] - 50) * 0.1      # Bonus pour retour > 50%
            
            # Fitness = bonus - pénalités
            fitness = (win_rate_bonus + profit_factor_bonus + return_bonus) - drawdown_penalty
            
            # Stockage des métriques pour analyse
            individual['metrics'] = metrics
            individual['fitness'] = fitness
            
            return fitness
            
        except Exception as e:
            print(f"Erreur évaluation: {e}")
            return float('-inf')
    
    def apply_strategy_with_params(self, params):
        """Applique la stratégie avec des paramètres personnalisés"""
        # Création d'une version modifiée de la stratégie avec les nouveaux paramètres
        return self.strategie_optimisee(self.df, self.symbol, self.timeframe, params)
    
    def strategie_optimisee(self, df, symbol, timeframe, params):
        """Version optimisée de la stratégie avec gestion du risque améliorée"""
        
        # Paramètres de la stratégie
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
        
        # Calcul des indicateurs
        df = df.copy()
        
        # ATR
        df['ATR'] = self.calculate_atr(df, atr_period)
        
        # RSI
        df['RSI'] = self.calculate_rsi(df['Close'], 8)
        
        # EMAs
        df['EMA_Short'] = df['Close'].ewm(span=ema_short).mean()
        df['EMA_Long'] = df['Close'].ewm(span=ema_long).mean()
        
        # Breakout levels
        df['High_Break'] = df['High'].rolling(window=breakout_period).max()
        df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
        
        # Filtres
        df['Uptrend'] = (df['EMA_Short'] > df['EMA_Long']) & (df['Close'] > df['EMA_Short'])
        df['Downtrend'] = (df['EMA_Short'] < df['EMA_Long']) & (df['Close'] < df['EMA_Short'])
        df['Volatility_OK'] = df['ATR'] > df['ATR'].rolling(window=15).mean() * 0.3
        df['Momentum_Up'] = df['Close'] > df['Close'].shift(1)
        df['Momentum_Down'] = df['Close'] < df['Close'].shift(1)
        
        # Conditions d'entrée
        df['Breakout_Up'] = (df['High'].shift(1) < df['High_Break'].shift(1)) & (df['High'] >= df['High_Break'])
        df['Breakout_Down'] = (df['Low'].shift(1) > df['Low_Break'].shift(1)) & (df['Low'] <= df['Low_Break'])
        
        df['RSI_OK_Long'] = (df['RSI'] < rsi_overbought) & (df['RSI'] > 20)
        df['RSI_OK_Short'] = (df['RSI'] > rsi_oversold) & (df['RSI'] < 80)
        
        # Signaux
        df['Long_Signal'] = (df['Breakout_Up'] & df['Uptrend'] & df['Volatility_OK'] & 
                            df['Momentum_Up'] & df['RSI_OK_Long'])
        df['Short_Signal'] = (df['Breakout_Down'] & df['Downtrend'] & df['Volatility_OK'] & 
                             df['Momentum_Down'] & df['RSI_OK_Short'])
        
        # Gestion des positions avec limite
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        stop_loss = 0
        take_profit = 0
        trailing_stop = 0
        positions_count = 0
        
        for i in range(len(df)):
            current_price = df['Close'].iloc[i]
            current_date = df['Date'].iloc[i]
            current_atr = df['ATR'].iloc[i]
            
            # Vérification du stop loss et take profit
            if position != 0:
                # Stop loss fixe
                if (position == 1 and current_price <= stop_loss) or (position == -1 and current_price >= stop_loss):
                    # Sortie par stop loss
                    exit_price = stop_loss
                    pnl = (exit_price - entry_price) / entry_price * 100 if position == 1 else (entry_price - exit_price) / entry_price * 100
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': 'Long' if position == 1 else 'Short',
                        'pnl': pnl,
                        'exit_reason': 'Stop_Loss'
                    })
                    position = 0
                    positions_count -= 1
                    continue
                
                # Take profit
                if (position == 1 and current_price >= take_profit) or (position == -1 and current_price <= take_profit):
                    # Sortie par take profit
                    exit_price = take_profit
                    pnl = (exit_price - entry_price) / entry_price * 100 if position == 1 else (entry_price - exit_price) / entry_price * 100
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': 'Long' if position == 1 else 'Short',
                        'pnl': pnl,
                        'exit_reason': 'Take_Profit'
                    })
                    position = 0
                    positions_count -= 1
                    continue
                
                # Trailing stop
                if trailing_stop > 0:
                    if position == 1:
                        new_trailing_stop = current_price - (trail_atr * current_atr)
                        if new_trailing_stop > trailing_stop:
                            trailing_stop = new_trailing_stop
                        elif current_price <= trailing_stop:
                            # Sortie par trailing stop
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
                            continue
                    else:  # Short position
                        new_trailing_stop = current_price + (trail_atr * current_atr)
                        if new_trailing_stop < trailing_stop or trailing_stop == 0:
                            trailing_stop = new_trailing_stop
                        elif current_price >= trailing_stop:
                            # Sortie par trailing stop
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
                            continue
            
            # Nouvelles entrées seulement si on n'a pas atteint le maximum de positions
            if position == 0 and positions_count < max_positions:
                if df['Long_Signal'].iloc[i]:
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    stop_loss = entry_price - (stop_loss_atr * current_atr)
                    take_profit = entry_price + (profit_atr * current_atr)
                    trailing_stop = entry_price - (trail_atr * current_atr)
                    positions_count += 1
                
                elif df['Short_Signal'].iloc[i]:
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    stop_loss = entry_price + (stop_loss_atr * current_atr)
                    take_profit = entry_price - (profit_atr * current_atr)
                    trailing_stop = entry_price + (trail_atr * current_atr)
                    positions_count += 1
        
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
        tournament_size = 3
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
    
    def mutate(self, individual, mutation_rate=0.1):
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
        """Lance l'optimisation génétique"""
        print(f"🚀 OPTIMISATION GÉNÉTIQUE - {self.symbol} {self.timeframe}")
        print(f"Population: {self.population_size}, Générations: {self.generations}")
        print("=" * 60)
        
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
        results_dir = f"results/optimization/genetic_optimization_{self.symbol}_{self.timeframe}_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # Sauvegarde des paramètres optimaux
        if self.best_individual:
            optimal_params = {k: v for k, v in self.best_individual.items() if k not in ['metrics', 'fitness']}
            
            with open(f"{results_dir}/parametres_optimaux.md", 'w', encoding='utf-8') as f:
                f.write(f"# Paramètres Optimaux - {self.symbol} {self.timeframe}\n\n")
                f.write(f"**Date d'optimisation**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
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
            
            # Sauvegarde de l'historique
            history_df = pd.DataFrame(self.history)
            history_df.to_csv(f"{results_dir}/historique_optimisation.csv", index=False)
            
            print(f"\n✅ Résultats sauvegardés: {results_dir}")
    
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
                f"Génétique {self.timeframe}",
                params,
                metrics,
                "genetique",
                self.timeframe,
                self.symbol
            )
            
            if success:
                print(f"🏆 Modèle optimal enregistré dans le gestionnaire")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'enregistrement du modèle: {e}")

def main():
    """Fonction principale"""
    print("🧬 OPTIMISATION GÉNÉTIQUE POUR RÉDUIRE LE DRAWDOWN")
    print("=" * 60)
    
    # Test sur différents timeframes
    timeframes = ['H4', 'D1']  # Commençons par les meilleurs
    
    for timeframe in timeframes:
        print(f"\n🎯 Optimisation {timeframe}...")
        
        try:
            optimizer = GeneticOptimizer(
                symbol="XAUUSD",
                timeframe=timeframe,
                population_size=30,
                generations=20
            )
            
            best_params = optimizer.optimize()
            
            if best_params:
                print(f"\n✅ Optimisation {timeframe} terminée!")
                print(f"📊 Meilleur fitness: {optimizer.best_fitness:.2f}")
                
                if 'metrics' in best_params:
                    metrics = best_params['metrics']
                    print(f"🎯 Drawdown optimisé: {metrics.get('max_drawdown', 0):.2f}%")
        
        except Exception as e:
            print(f"❌ Erreur pour {timeframe}: {e}")
            continue
    
    print(f"\n🎉 Optimisation terminée!")

if __name__ == "__main__":
    main() 