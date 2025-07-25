#!/usr/bin/env python3
"""
Système d'Optimisation Complet avec Fusion de Modèles
Optimisation génétique + RL + Fusion + Apprentissage continu
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import random
import warnings
warnings.filterwarnings('ignore')

# Rich pour une belle interface
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich import box

console = Console()

# Ajout du chemin pour importer les modules
sys.path.append('src/strategies')
from strategie_xauusd_sharpe1_simple import calculate_metrics

class CompleteOptimizationSystem:
    def __init__(self, symbol="XAUUSD", timeframe="D1"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.df = self.load_data()
        
        # Paramètres étendus pour fusion
        self.param_ranges = {
            # Paramètres de base
            'breakout_period': (1, 10),
            'profit_atr': (1.0, 8.0),
            'rsi_overbought': (65, 95),
            'rsi_oversold': (5, 35),
            'ema_short': (2, 15),
            'ema_long': (5, 30),
            'atr_period': (3, 20),
            'trail_atr': (0.2, 3.0),
            'stop_loss_atr': (0.8, 5.0),
            'max_positions': (1, 5),
            'risk_per_trade': (0.3, 5.0),
            
            # Paramètres avancés
            'min_pips_filter': (3, 15),
            'volatility_filter': (0.5, 3.0),
            'momentum_strength': (0.5, 3.0),
            'volume_filter': (0.3, 2.0),
            'trend_strength': (0.5, 3.0),
            'max_hold_time': (1, 50),
            'profit_lock': (0.5, 3.0),
            'breakout_confirmation': (1, 5),
            'rsi_filter': (10, 40),
            'atr_threshold': (0.5, 3.0),
            
            # Paramètres de fusion
            'genetic_weight': (0.0, 1.0),  # Poids du modèle génétique
            'aggressive_weight': (0.0, 1.0),  # Poids du modèle agressif
            'rl_weight': (0.0, 1.0),  # Poids du modèle RL
            'fusion_method': (0, 3),  # 0=avg, 1=weighted, 2=best, 3=hybrid
            'adaptation_rate': (0.1, 0.9),  # Taux d'adaptation
            'exploration_rate': (0.1, 0.5),  # Taux d'exploration
        }
        
        self.models = {}
        self.best_hybrid = None
        self.history = []
        
    def load_data(self):
        """Charge les données"""
        csv_path = f"data/raw/{self.symbol}_{self.timeframe}_mt5.csv"
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Fichier non trouvé: {csv_path}")
        
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def load_existing_models(self):
        """Charge les modèles existants depuis le gestionnaire"""
        try:
            sys.path.append('scripts')
            from gestion_modeles_optimaux import ModelManager
            
            manager = ModelManager()
            existing_models = manager.get_all_models()
            
            for key, model in existing_models.items():
                if model['timeframe'] == self.timeframe:
                    self.models[model['optimization_type']] = {
                        'params': model['params'],
                        'metrics': model['metrics'],
                        'score': model['score']
                    }
            
            console.print(f"📦 [green]{len(self.models)} modèles chargés[/green]")
            
        except Exception as e:
            console.print(f"⚠️ [yellow]Erreur chargement modèles: {e}[/yellow]")
    
    def genetic_optimization(self, population_size=100, generations=200):
        """Optimisation génétique classique"""
        console.print(Panel.fit(
            "[bold blue]🧬 OPTIMISATION GÉNÉTIQUE[/bold blue]",
            border_style="blue"
        ))
        
        population = self.create_population(population_size)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Générations", total=generations)
            
            for gen in range(generations):
                progress.update(task, description=f"Génération {gen + 1}/{generations}")
                
                # Évaluation
                fitness_scores = []
                for individual in population:
                    fitness = self.evaluate_fitness(individual)
                    fitness_scores.append(fitness)
                
                # Sélection et reproduction
                new_population = self.evolutionary_step(population, fitness_scores)
                population = new_population
                
                # Affichage du meilleur
                best_idx = fitness_scores.index(max(fitness_scores))
                best_individual = population[best_idx]
                if 'metrics' in best_individual:
                    metrics = best_individual['metrics']
                    progress.console.print(f"   📊 Retour: [green]{metrics.get('total_return', 0):.1f}%[/green] | DD: [red]{metrics.get('max_drawdown', 0):.1f}%[/red]")
                
                progress.advance(task)
        
        # Sauvegarder le meilleur
        best_idx = fitness_scores.index(max(fitness_scores))
        self.models['genetic'] = {
            'params': {k: v for k, v in population[best_idx].items() if k not in ['metrics', 'fitness']},
            'metrics': population[best_idx].get('metrics', {}),
            'score': max(fitness_scores)
        }
        
        return self.models['genetic']
    
    def aggressive_optimization(self, population_size=100, generations=200):
        """Optimisation agressive pour gains"""
        console.print(Panel.fit(
            "[bold red]🔥 OPTIMISATION AGRESSIVE[/bold red]",
            border_style="red"
        ))
        
        population = self.create_population(population_size)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Générations", total=generations)
            
            for gen in range(generations):
                progress.update(task, description=f"Génération {gen + 1}/{generations}")
                
                # Évaluation avec objectifs agressifs
                fitness_scores = []
                for individual in population:
                    fitness = self.evaluate_aggressive_fitness(individual)
                    fitness_scores.append(fitness)
                
                # Sélection et reproduction
                new_population = self.evolutionary_step(population, fitness_scores)
                population = new_population
                
                # Affichage du meilleur
                best_idx = fitness_scores.index(max(fitness_scores))
                best_individual = population[best_idx]
                if 'metrics' in best_individual:
                    metrics = best_individual['metrics']
                    progress.console.print(f"   💰 Retour: [green]{metrics.get('total_return', 0):.1f}%[/green] | PF: [blue]{metrics.get('profit_factor', 0):.2f}[/blue]")
                
                progress.advance(task)
        
        # Sauvegarder le meilleur
        best_idx = fitness_scores.index(max(fitness_scores))
        self.models['aggressive'] = {
            'params': {k: v for k, v in population[best_idx].items() if k not in ['metrics', 'fitness']},
            'metrics': population[best_idx].get('metrics', {}),
            'score': max(fitness_scores)
        }
        
        return self.models['aggressive']
    
    def reinforcement_learning_optimization(self, episodes=1000):
        """Optimisation par Reinforcement Learning"""
        console.print(Panel.fit(
            "[bold purple]🤖 OPTIMISATION REINFORCEMENT LEARNING[/bold purple]",
            border_style="purple"
        ))
        
        # Q-Learning simplifié
        q_table = {}
        best_reward = float('-inf')
        best_params = None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Épisodes", total=episodes)
            
            for episode in range(episodes):
                progress.update(task, description=f"Épisode {episode + 1}/{episodes}")
                
                # Action aléatoire
                params = self.create_random_params()
                
                # Évaluation
                trades = self.apply_strategy(params)
                if len(trades) > 10:
                    metrics = calculate_metrics(trades)
                    reward = self.calculate_rl_reward(metrics)
                    
                    # Mise à jour Q-table
                    state_key = self.get_state_key(params)
                    if state_key not in q_table:
                        q_table[state_key] = 0
                    
                    q_table[state_key] = max(q_table[state_key], reward)
                    
                    # Mise à jour du meilleur
                    if reward > best_reward:
                        best_reward = reward
                        best_params = params.copy()
                        best_metrics = metrics
                        
                        progress.console.print(f"   🎯 Nouveau meilleur: [green]{reward:.2f}[/green]")
                
                progress.advance(task)
        
        # Sauvegarder le meilleur
        if best_params:
            self.models['rl'] = {
                'params': best_params,
                'metrics': best_metrics,
                'score': best_reward
            }
        
        return self.models.get('rl')
    
    def fusion_models(self):
        """Fuse les modèles existants"""
        console.print(Panel.fit(
            "[bold green]🔗 FUSION DES MODÈLES[/bold green]",
            border_style="green"
        ))
        
        if len(self.models) < 2:
            console.print("❌ [red]Pas assez de modèles pour la fusion[/red]")
            return None
        
        # Créer un tableau des modèles
        table = Table(title="📦 Modèles Disponibles")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Score", style="green")
        table.add_column("Retour", style="blue")
        table.add_column("Drawdown", style="red")
        
        for model_type, model in self.models.items():
            metrics = model['metrics']
            table.add_row(
                model_type.upper(),
                f"{model['score']:.2f}",
                f"{metrics.get('total_return', 0):.1f}%",
                f"{metrics.get('max_drawdown', 0):.1f}%"
            )
        
        console.print(table)
        
        # Méthodes de fusion
        fusion_methods = {
            'average': self.fusion_average,
            'weighted': self.fusion_weighted,
            'best_components': self.fusion_best_components,
            'hybrid': self.fusion_hybrid
        }
        
        best_fusion = None
        best_score = float('-inf')
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Test des méthodes de fusion", total=len(fusion_methods))
            
            for method_name, fusion_func in fusion_methods.items():
                progress.update(task, description=f"Test: {method_name}")
                
                fused_params = fusion_func()
                if fused_params:
                    trades = self.apply_strategy(fused_params)
                    if len(trades) > 10:
                        metrics = calculate_metrics(trades)
                        score = self.calculate_fusion_score(metrics)
                        
                        progress.console.print(f"   📊 {method_name}: Score [green]{score:.2f}[/green] | Retour: [blue]{metrics.get('total_return', 0):.1f}%[/blue]")
                        
                        if score > best_score:
                            best_score = score
                            best_fusion = {
                                'method': method_name,
                                'params': fused_params,
                                'metrics': metrics,
                                'score': score
                            }
                
                progress.advance(task)
        
        if best_fusion:
            self.models['fusion'] = best_fusion
            
            # Afficher le résultat
            result_table = Table(title="🏆 Meilleure Fusion")
            result_table.add_column("Méthode", style="cyan")
            result_table.add_column("Score", style="green")
            result_table.add_column("Retour", style="blue")
            result_table.add_column("Drawdown", style="red")
            result_table.add_column("Win Rate", style="yellow")
            
            metrics = best_fusion['metrics']
            result_table.add_row(
                best_fusion['method'].upper(),
                f"{best_fusion['score']:.2f}",
                f"{metrics.get('total_return', 0):.1f}%",
                f"{metrics.get('max_drawdown', 0):.1f}%",
                f"{metrics.get('win_rate', 0):.1f}%"
            )
            
            console.print(result_table)
        
        return best_fusion
    
    def fusion_average(self):
        """Fusion par moyenne simple"""
        if len(self.models) == 0:
            return None
        
        fused_params = {}
        param_counts = {}
        
        for model_type, model in self.models.items():
            for param, value in model['params'].items():
                if param not in fused_params:
                    fused_params[param] = 0
                    param_counts[param] = 0
                
                fused_params[param] += value
                param_counts[param] += 1
        
        # Moyenne
        for param in fused_params:
            fused_params[param] /= param_counts[param]
            if isinstance(self.param_ranges[param][0], int):
                fused_params[param] = int(round(fused_params[param]))
            else:
                fused_params[param] = round(fused_params[param], 2)
        
        return fused_params
    
    def fusion_weighted(self):
        """Fusion pondérée par score"""
        if len(self.models) == 0:
            return None
        
        fused_params = {}
        total_weight = 0
        
        # Calcul des poids
        weights = {}
        for model_type, model in self.models.items():
            weights[model_type] = model['score']
            total_weight += model['score']
        
        if total_weight == 0:
            return self.fusion_average()
        
        # Normalisation des poids
        for model_type in weights:
            weights[model_type] /= total_weight
        
        # Fusion pondérée
        for param in self.param_ranges.keys():
            weighted_sum = 0
            for model_type, model in self.models.items():
                if param in model['params']:
                    weighted_sum += model['params'][param] * weights[model_type]
            
            fused_params[param] = weighted_sum
            if isinstance(self.param_ranges[param][0], int):
                fused_params[param] = int(round(fused_params[param]))
            else:
                fused_params[param] = round(fused_params[param], 2)
        
        return fused_params
    
    def fusion_best_components(self):
        """Fusion en prenant les meilleurs composants"""
        if len(self.models) == 0:
            return None
        
        fused_params = {}
        
        # Pour chaque paramètre, choisir la valeur du meilleur modèle
        for param in self.param_ranges.keys():
            best_value = None
            best_score = float('-inf')
            
            for model_type, model in self.models.items():
                if param in model['params']:
                    if model['score'] > best_score:
                        best_score = model['score']
                        best_value = model['params'][param]
            
            if best_value is not None:
                fused_params[param] = best_value
        
        return fused_params
    
    def fusion_hybrid(self):
        """Fusion hybride intelligente"""
        if len(self.models) == 0:
            return None
        
        # Combiner les meilleures approches
        fused_params = {}
        
        # Paramètres de gestion du risque depuis le modèle génétique
        if 'genetic' in self.models:
            risk_params = ['stop_loss_atr', 'max_positions', 'risk_per_trade', 'trail_atr']
            for param in risk_params:
                if param in self.models['genetic']['params']:
                    fused_params[param] = self.models['genetic']['params'][param]
        
        # Paramètres de gains depuis le modèle agressif
        if 'aggressive' in self.models:
            gain_params = ['profit_atr', 'min_pips_filter', 'profit_lock']
            for param in gain_params:
                if param in self.models['aggressive']['params']:
                    fused_params[param] = self.models['aggressive']['params'][param]
        
        # Paramètres d'adaptation depuis le RL
        if 'rl' in self.models:
            adapt_params = ['adaptation_rate', 'exploration_rate']
            for param in adapt_params:
                if param in self.models['rl']['params']:
                    fused_params[param] = self.models['rl']['params'][param]
        
        # Compléter avec les valeurs par défaut ou moyennes
        for param, (min_val, max_val) in self.param_ranges.items():
            if param not in fused_params:
                # Valeur par défaut (milieu de la plage)
                default_val = (min_val + max_val) / 2
                if isinstance(min_val, int):
                    fused_params[param] = int(round(default_val))
                else:
                    fused_params[param] = round(default_val, 2)
        
        return fused_params
    
    def continuous_learning(self, iterations=50):
        """Apprentissage continu et amélioration"""
        console.print(Panel.fit(
            "[bold yellow]🔄 APPRENTISSAGE CONTINU[/bold yellow]",
            border_style="yellow"
        ))
        
        if not self.models:
            console.print("❌ [red]Aucun modèle à améliorer[/red]")
            return
        
        best_model = max(self.models.values(), key=lambda x: x['score'])
        current_params = best_model['params'].copy()
        current_score = best_model['score']
        
        console.print(f"🎯 [cyan]Modèle de base:[/cyan] Score [green]{current_score:.2f}[/green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Itérations d'amélioration", total=iterations)
            
            for iteration in range(iterations):
                progress.update(task, description=f"Itération {iteration + 1}/{iterations}")
                
                # Créer des variations du meilleur modèle
                improved_params = self.improve_params(current_params)
                
                # Tester les améliorations
                trades = self.apply_strategy(improved_params)
                if len(trades) > 10:
                    metrics = calculate_metrics(trades)
                    new_score = self.calculate_fusion_score(metrics)
                    
                    progress.console.print(f"   📊 Nouveau score: [green]{new_score:.2f}[/green] | Retour: [blue]{metrics.get('total_return', 0):.1f}%[/blue]")
                    
                    # Accepter si meilleur
                    if new_score > current_score:
                        current_params = improved_params
                        current_score = new_score
                        progress.console.print(f"   ✅ [green]Amélioration acceptée![/green]")
                    else:
                        progress.console.print(f"   ❌ [red]Amélioration rejetée[/red]")
                
                progress.advance(task)
        
        # Sauvegarder le modèle amélioré
        self.models['continuous'] = {
            'params': current_params,
            'metrics': calculate_metrics(self.apply_strategy(current_params)),
            'score': current_score
        }
        
        console.print(f"🏆 [bold green]Modèle final:[/bold green] Score [green]{current_score:.2f}[/green]")
        return self.models['continuous']
    
    def improve_params(self, params):
        """Améliore les paramètres existants"""
        improved = params.copy()
        
        # Mutation intelligente
        for param, (min_val, max_val) in self.param_ranges.items():
            if random.random() < 0.3:  # 30% de chance de mutation
                if isinstance(min_val, int):
                    # Mutation pour paramètres entiers
                    current = improved.get(param, (min_val + max_val) // 2)
                    mutation = random.randint(-1, 1)
                    improved[param] = max(min_val, min(max_val, current + mutation))
                else:
                    # Mutation pour paramètres flottants
                    current = improved.get(param, (min_val + max_val) / 2)
                    mutation = random.uniform(-0.1, 0.1) * (max_val - min_val)
                    improved[param] = max(min_val, min(max_val, current + mutation))
                    improved[param] = round(improved[param], 2)
        
        return improved
    
    def create_population(self, size):
        """Crée une population initiale"""
        return [self.create_random_params() for _ in range(size)]
    
    def create_random_params(self):
        """Crée des paramètres aléatoires"""
        params = {}
        for param, (min_val, max_val) in self.param_ranges.items():
            if isinstance(min_val, int):
                params[param] = random.randint(min_val, max_val)
            else:
                params[param] = round(random.uniform(min_val, max_val), 2)
        return params
    
    def evaluate_fitness(self, individual):
        """Évalue la fitness d'un individu"""
        try:
            trades = self.apply_strategy(individual)
            
            if len(trades) < 10:
                return float('-inf')
            
            metrics = calculate_metrics(trades)
            
            # Critères de fitness équilibrés
            drawdown_penalty = max(0, metrics['max_drawdown'] - 30) * 10
            win_rate_bonus = max(0, metrics['win_rate'] - 45) * 0.5
            profit_factor_bonus = max(0, metrics['profit_factor'] - 1.5) * 2
            return_bonus = max(0, metrics['total_return'] - 50) * 0.1
            
            fitness = (win_rate_bonus + profit_factor_bonus + return_bonus) - drawdown_penalty
            
            individual['metrics'] = metrics
            individual['fitness'] = fitness
            
            return fitness
            
        except Exception as e:
            return float('-inf')
    
    def evaluate_aggressive_fitness(self, individual):
        """Évalue la fitness pour optimisation agressive"""
        try:
            trades = self.apply_strategy(individual)
            
            if len(trades) < 10:
                return float('-inf')
            
            metrics = calculate_metrics(trades)
            
            # Critères agressifs
            total_gain = metrics['total_return']
            drawdown_penalty = max(0, metrics['max_drawdown'] - 20) * 15
            win_rate_bonus = max(0, metrics['win_rate'] - 55) * 2
            profit_factor_bonus = max(0, metrics['profit_factor'] - 3) * 10
            avg_win_bonus = max(0, metrics.get('avg_win', 0) - 2) * 5
            
            fitness = (total_gain * 0.3) - drawdown_penalty + win_rate_bonus + profit_factor_bonus + avg_win_bonus
            
            individual['metrics'] = metrics
            individual['fitness'] = fitness
            
            return fitness
            
        except Exception as e:
            return float('-inf')
    
    def calculate_rl_reward(self, metrics):
        """Calcule la récompense pour le RL"""
        reward = 0
        
        # Récompense pour le retour
        reward += metrics['total_return'] * 0.1
        
        # Récompense pour le win rate
        if metrics['win_rate'] > 50:
            reward += (metrics['win_rate'] - 50) * 0.5
        
        # Récompense pour le profit factor
        if metrics['profit_factor'] > 1.5:
            reward += (metrics['profit_factor'] - 1.5) * 10
        
        # Pénalité pour le drawdown
        if metrics['max_drawdown'] > 30:
            reward -= (metrics['max_drawdown'] - 30) * 5
        elif metrics['max_drawdown'] < 20:
            reward += (20 - metrics['max_drawdown']) * 2
        
        return reward
    
    def calculate_fusion_score(self, metrics):
        """Calcule le score pour la fusion"""
        score = 0
        
        # Retour (0-40 points)
        return_val = metrics.get('total_return', 0)
        if return_val > 500:
            score += 40
        elif return_val > 300:
            score += 35
        elif return_val > 200:
            score += 30
        elif return_val > 100:
            score += 25
        
        # Drawdown (0-30 points)
        dd = metrics.get('max_drawdown', 100)
        if dd < 10:
            score += 30
        elif dd < 20:
            score += 25
        elif dd < 30:
            score += 20
        
        # Win Rate (0-20 points)
        wr = metrics.get('win_rate', 0)
        if wr > 60:
            score += 20
        elif wr > 55:
            score += 15
        elif wr > 50:
            score += 10
        
        # Profit Factor (0-10 points)
        pf = metrics.get('profit_factor', 0)
        if pf > 4:
            score += 10
        elif pf > 3:
            score += 8
        elif pf > 2:
            score += 5
        
        return score
    
    def evolutionary_step(self, population, fitness_scores):
        """Étape d'évolution"""
        new_population = []
        
        # Élitisme
        best_idx = fitness_scores.index(max(fitness_scores))
        new_population.append(population[best_idx])
        
        # Croisement et mutation
        while len(new_population) < len(population):
            # Sélection par tournoi
            parent1 = self.tournament_selection(population, fitness_scores)
            parent2 = self.tournament_selection(population, fitness_scores)
            
            # Croisement
            child = self.crossover(parent1, parent2)
            
            # Mutation
            child = self.mutate(child)
            
            new_population.append(child)
        
        return new_population
    
    def tournament_selection(self, population, fitness_scores, tournament_size=3):
        """Sélection par tournoi"""
        tournament = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament]
        winner = tournament[tournament_fitness.index(max(tournament_fitness))]
        return population[winner]
    
    def crossover(self, parent1, parent2):
        """Croisement de deux parents"""
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
    
    def apply_strategy(self, params):
        """Applique la stratégie avec les paramètres donnés"""
        # Version simplifiée de la stratégie
        return self.strategie_complete(self.df, params)
    
    def strategie_complete(self, df, params):
        """Stratégie complète avec tous les paramètres"""
        df = df.copy()
        
        # Paramètres de base
        breakout_period = int(params.get('breakout_period', 2))
        profit_atr = params.get('profit_atr', 2.5)
        rsi_overbought = params.get('rsi_overbought', 85)
        rsi_oversold = params.get('rsi_oversold', 15)
        ema_short = int(params.get('ema_short', 4))
        ema_long = int(params.get('ema_long', 12))
        atr_period = int(params.get('atr_period', 8))
        trail_atr = params.get('trail_atr', 0.5)
        stop_loss_atr = params.get('stop_loss_atr', 2.0)
        max_positions = int(params.get('max_positions', 1))
        
        # Calcul des indicateurs
        df['ATR'] = self.calculate_atr(df, atr_period)
        df['RSI'] = self.calculate_rsi(df['Close'], 8)
        df['EMA_Short'] = df['Close'].ewm(span=ema_short).mean()
        df['EMA_Long'] = df['Close'].ewm(span=ema_long).mean()
        df['High_Break'] = df['High'].rolling(window=breakout_period).max()
        df['Low_Break'] = df['Low'].rolling(window=breakout_period).min()
        
        # Signaux
        df['Long_Signal'] = (
            (df['High'].shift(1) < df['High_Break'].shift(1)) & 
            (df['High'] >= df['High_Break']) &
            (df['EMA_Short'] > df['EMA_Long']) &
            (df['Close'] > df['EMA_Short']) &
            (df['RSI'] < rsi_overbought) &
            (df['RSI'] > 20)
        )
        
        df['Short_Signal'] = (
            (df['Low'].shift(1) > df['Low_Break'].shift(1)) & 
            (df['Low'] <= df['Low_Break']) &
            (df['EMA_Short'] < df['EMA_Long']) &
            (df['Close'] < df['EMA_Short']) &
            (df['RSI'] > rsi_oversold) &
            (df['RSI'] < 80)
        )
        
        # Simulation des trades
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        positions_count = 0
        
        for i in range(len(df)):
            if i < 50:
                continue
                
            current_price = df['Close'].iloc[i]
            current_date = df['Date'].iloc[i]
            current_atr = df['ATR'].iloc[i]
            
            # Gestion des positions
            if position != 0:
                # Stop loss et take profit
                if position == 1:  # Long
                    stop_loss = entry_price - (stop_loss_atr * current_atr)
                    take_profit = entry_price + (profit_atr * current_atr)
                    
                    if current_price <= stop_loss:
                        pnl = (stop_loss - entry_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'position': 'Long',
                            'pnl': pnl,
                            'exit_reason': 'Stop_Loss'
                        })
                        position = 0
                        positions_count -= 1
                        continue
                    
                    if current_price >= take_profit:
                        pnl = (take_profit - entry_price) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'position': 'Long',
                            'pnl': pnl,
                            'exit_reason': 'Take_Profit'
                        })
                        position = 0
                        positions_count -= 1
                        continue
                
                else:  # Short
                    stop_loss = entry_price + (stop_loss_atr * current_atr)
                    take_profit = entry_price - (profit_atr * current_atr)
                    
                    if current_price >= stop_loss:
                        pnl = (entry_price - stop_loss) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': stop_loss,
                            'position': 'Short',
                            'pnl': pnl,
                            'exit_reason': 'Stop_Loss'
                        })
                        position = 0
                        positions_count -= 1
                        continue
                    
                    if current_price <= take_profit:
                        pnl = (entry_price - take_profit) / entry_price * 100
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': take_profit,
                            'position': 'Short',
                            'pnl': pnl,
                            'exit_reason': 'Take_Profit'
                        })
                        position = 0
                        positions_count -= 1
                        continue
            
            # Nouvelles entrées
            if position == 0 and positions_count < max_positions:
                if df['Long_Signal'].iloc[i]:
                    position = 1
                    entry_price = current_price
                    entry_date = current_date
                    positions_count += 1
                
                elif df['Short_Signal'].iloc[i]:
                    position = -1
                    entry_price = current_price
                    entry_date = current_date
                    positions_count += 1
        
        return trades
    
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
    
    def get_state_key(self, params):
        """Génère une clé d'état pour le RL"""
        return str(sorted(params.items()))
    
    def save_final_model(self):
        """Sauvegarde le modèle final"""
        if not self.models:
            console.print("❌ [red]Aucun modèle à sauvegarder[/red]")
            return
        
        # Trouver le meilleur modèle
        best_model = max(self.models.values(), key=lambda x: x['score'])
        
        # Sauvegarder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"results/optimization/complete_system_{self.symbol}_{self.timeframe}_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # Sauvegarde des résultats
        with open(f"{results_dir}/modele_final.md", 'w', encoding='utf-8') as f:
            f.write(f"# Modèle Final - Système Complet {self.symbol} {self.timeframe}\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Modèles Utilisés\n\n")
            for model_type, model in self.models.items():
                f.write(f"- **{model_type}**: Score {model['score']:.2f}\n")
            
            f.write(f"\n## Meilleur Modèle\n\n")
            f.write(f"- **Type**: {list(self.models.keys())[list(self.models.values()).index(best_model)]}\n")
            f.write(f"- **Score**: {best_model['score']:.2f}\n")
            f.write(f"- **Retour**: {best_model['metrics'].get('total_return', 0):.1f}%\n")
            f.write(f"- **Drawdown**: {best_model['metrics'].get('max_drawdown', 0):.1f}%\n")
            f.write(f"- **Win Rate**: {best_model['metrics'].get('win_rate', 0):.1f}%\n")
            f.write(f"- **Profit Factor**: {best_model['metrics'].get('profit_factor', 0):.2f}\n")
            
            f.write(f"\n## Paramètres Optimaux\n\n")
            for param, value in best_model['params'].items():
                f.write(f"- **{param}**: {value}\n")
        
        console.print(f"✅ [green]Modèle final sauvegardé:[/green] {results_dir}")
        return results_dir

def main():
    """Fonction principale"""
    console.print(Panel.fit(
        "[bold blue]🚀 SYSTÈME D'OPTIMISATION COMPLET[/bold blue]\n"
        "[cyan]Optimisation génétique + RL + Fusion + Apprentissage continu[/cyan]",
        border_style="blue",
        box=box.DOUBLE
    ))
    
    # Configuration
    symbol = "XAUUSD"
    timeframe = "D1"
    
    console.print(f"🎯 [yellow]Configuration:[/yellow] {symbol} {timeframe}")
    console.print()
    
    # Création du système
    system = CompleteOptimizationSystem(symbol, timeframe)
    
    # Chargement des modèles existants
    system.load_existing_models()
    
    # Menu avec Rich
    menu_table = Table(title="🎯 Options d'Optimisation", box=box.ROUNDED)
    menu_table.add_column("Option", style="cyan", no_wrap=True)
    menu_table.add_column("Description", style="white")
    menu_table.add_column("Durée", style="yellow")
    
    menu_table.add_row("1", "Optimisation Génétique", "10-20 min")
    menu_table.add_row("2", "Optimisation Agressive", "10-20 min")
    menu_table.add_row("3", "Reinforcement Learning", "15-30 min")
    menu_table.add_row("4", "Fusion des Modèles", "2-5 min")
    menu_table.add_row("5", "Apprentissage Continu", "5-10 min")
    menu_table.add_row("6", "Optimisation Complète (Tout)", "45-90 min")
    menu_table.add_row("7", "Optimisation Rapide (Test)", "5-10 min")
    menu_table.add_row("8", "Optimisation Intensive", "2-4 heures")
    
    console.print(menu_table)
    
    choice = console.input("\n[bold green]Choisissez une option (1-8): [/bold green]")
    
    if choice == "1":
        system.genetic_optimization()
    elif choice == "2":
        system.aggressive_optimization()
    elif choice == "3":
        system.reinforcement_learning_optimization()
    elif choice == "4":
        system.fusion_models()
    elif choice == "5":
        system.continuous_learning()
    elif choice == "6":
        console.print(Panel.fit(
            "[bold green]🔄 OPTIMISATION COMPLÈTE[/bold green]",
            border_style="green"
        ))
        
        # Optimisation génétique
        system.genetic_optimization(population_size=50, generations=100)
        
        # Optimisation agressive
        system.aggressive_optimization(population_size=50, generations=100)
        
        # Reinforcement Learning
        system.reinforcement_learning_optimization(episodes=500)
        
        # Fusion des modèles
        system.fusion_models()
        
        # Apprentissage continu
        system.continuous_learning(iterations=20)
        
        # Sauvegarde finale
        system.save_final_model()
        
        console.print(Panel.fit(
            "[bold green]🎉 OPTIMISATION COMPLÈTE TERMINÉE![/bold green]",
            border_style="green"
        ))
    elif choice == "7":
        console.print(Panel.fit(
            "[bold cyan]⚡ OPTIMISATION RAPIDE (TEST)[/bold cyan]",
            border_style="cyan"
        ))
        
        # Optimisation rapide pour test
        system.genetic_optimization(population_size=20, generations=10)
        system.aggressive_optimization(population_size=20, generations=10)
        system.reinforcement_learning_optimization(episodes=50)
        system.fusion_models()
        system.continuous_learning(iterations=5)
        
        console.print(Panel.fit(
            "[bold cyan]✅ OPTIMISATION RAPIDE TERMINÉE![/bold cyan]",
            border_style="cyan"
        ))
    elif choice == "8":
        console.print(Panel.fit(
            "[bold red]🔥 OPTIMISATION INTENSIVE[/bold red]",
            border_style="red"
        ))
        
        # Optimisation intensive
        system.genetic_optimization(population_size=200, generations=500)
        system.aggressive_optimization(population_size=200, generations=500)
        system.reinforcement_learning_optimization(episodes=2000)
        system.fusion_models()
        system.continuous_learning(iterations=100)
        
        console.print(Panel.fit(
            "[bold red]🏆 OPTIMISATION INTENSIVE TERMINÉE![/bold red]",
            border_style="red"
        ))
    else:
        console.print("❌ [red]Option invalide[/red]")

if __name__ == "__main__":
    main() 