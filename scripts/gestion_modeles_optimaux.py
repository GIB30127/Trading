#!/usr/bin/env python3
"""
Gestion des Modèles Optimaux
Sauvegarde, charge et compare les meilleurs modèles d'optimisation
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import shutil
import warnings
warnings.filterwarnings('ignore')

class ModelManager:
    def __init__(self):
        self.models_dir = "models_optimaux"
        self.models_file = os.path.join(self.models_dir, "modeles_enregistres.json")
        self.backup_dir = os.path.join(self.models_dir, "backups")
        
        # Création des dossiers
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Chargement des modèles existants
        self.models = self.load_models()
    
    def load_models(self):
        """Charge les modèles enregistrés"""
        if os.path.exists(self.models_file):
            try:
                with open(self.models_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_models(self):
        """Sauvegarde les modèles"""
        with open(self.models_file, 'w', encoding='utf-8') as f:
            json.dump(self.models, f, indent=2, ensure_ascii=False)
    
    def register_model(self, model_name, params, metrics, optimization_type, timeframe, symbol="XAUUSD"):
        """Enregistre un nouveau modèle optimal"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_id = f"{model_name}_{timestamp}"
        
        model_data = {
            'id': model_id,
            'name': model_name,
            'optimization_type': optimization_type,
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': timestamp,
            'date_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'params': params,
            'metrics': metrics,
            'score': self.calculate_model_score(metrics),
            'status': 'active'
        }
        
        # Vérifier si c'est le meilleur modèle pour ce type
        best_key = f"{optimization_type}_{timeframe}"
        if best_key not in self.models or self.models[best_key]['score'] < model_data['score']:
            # Sauvegarder l'ancien modèle comme backup
            if best_key in self.models:
                old_model = self.models[best_key]
                backup_file = os.path.join(self.backup_dir, f"{old_model['id']}.json")
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(old_model, f, indent=2, ensure_ascii=False)
                print(f"📦 Backup créé: {backup_file}")
            
            # Enregistrer le nouveau meilleur modèle
            self.models[best_key] = model_data
            self.save_models()
            
            print(f"🏆 Nouveau meilleur modèle enregistré: {model_name}")
            print(f"   📊 Score: {model_data['score']:.2f}")
            print(f"   💰 Retour: {metrics.get('total_return', 0):.1f}%")
            print(f"   📉 Drawdown: {metrics.get('max_drawdown', 0):.1f}%")
            
            return True
        else:
            print(f"⚠️ Modèle non enregistré - Score insuffisant")
            print(f"   Actuel: {self.models[best_key]['score']:.2f}")
            print(f"   Nouveau: {model_data['score']:.2f}")
            return False
    
    def calculate_model_score(self, metrics):
        """Calcule un score pour le modèle"""
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
        elif return_val > 50:
            score += 20
        
        # Drawdown (0-30 points)
        dd = metrics.get('max_drawdown', 100)
        if dd < 10:
            score += 30
        elif dd < 20:
            score += 25
        elif dd < 30:
            score += 20
        elif dd < 50:
            score += 15
        
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
    
    def get_best_model(self, optimization_type, timeframe):
        """Récupère le meilleur modèle pour un type et timeframe"""
        key = f"{optimization_type}_{timeframe}"
        return self.models.get(key, None)
    
    def get_all_models(self):
        """Récupère tous les modèles"""
        return self.models
    
    def list_models(self):
        """Liste tous les modèles enregistrés"""
        print("📋 MODÈLES OPTIMAUX ENREGISTRÉS")
        print("=" * 60)
        
        if not self.models:
            print("❌ Aucun modèle enregistré")
            return
        
        for key, model in self.models.items():
            print(f"\n🔹 {model['name']}")
            print(f"   📊 Type: {model['optimization_type']}")
            print(f"   📈 Timeframe: {model['timeframe']}")
            print(f"   🏆 Score: {model['score']:.2f}/100")
            print(f"   💰 Retour: {model['metrics'].get('total_return', 0):.1f}%")
            print(f"   📉 Drawdown: {model['metrics'].get('max_drawdown', 0):.1f}%")
            print(f"   🎯 Win Rate: {model['metrics'].get('win_rate', 0):.1f}%")
            print(f"   ⚖️ Profit Factor: {model['metrics'].get('profit_factor', 0):.2f}")
            print(f"   📅 Créé: {model['date_created']}")
    
    def export_model(self, optimization_type, timeframe, export_path=None):
        """Exporte un modèle vers un fichier"""
        model = self.get_best_model(optimization_type, timeframe)
        
        if not model:
            print(f"❌ Modèle non trouvé: {optimization_type} {timeframe}")
            return None
        
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"models_optimaux/export_{optimization_type}_{timeframe}_{timestamp}.json"
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(model, f, indent=2, ensure_ascii=False)
        
        print(f"📤 Modèle exporté: {export_path}")
        return export_path
    
    def import_model(self, import_path):
        """Importe un modèle depuis un fichier"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            # Vérifier la structure
            required_fields = ['name', 'optimization_type', 'timeframe', 'params', 'metrics']
            for field in required_fields:
                if field not in model_data:
                    print(f"❌ Champ manquant: {field}")
                    return False
            
            # Enregistrer le modèle
            success = self.register_model(
                model_data['name'],
                model_data['params'],
                model_data['metrics'],
                model_data['optimization_type'],
                model_data['timeframe'],
                model_data.get('symbol', 'XAUUSD')
            )
            
            return success
            
        except Exception as e:
            print(f"❌ Erreur d'import: {e}")
            return False
    
    def create_strategy_file(self, optimization_type, timeframe):
        """Crée un fichier de stratégie avec les paramètres optimaux"""
        model = self.get_best_model(optimization_type, timeframe)
        
        if not model:
            print(f"❌ Modèle non trouvé: {optimization_type} {timeframe}")
            return None
        
        # Création du fichier de stratégie
        strategy_content = f'''#!/usr/bin/env python3
"""
Stratégie Optimisée - {model['name']}
Paramètres optimaux générés le {model['date_created']}
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Paramètres optimaux
OPTIMAL_PARAMS = {json.dumps(model['params'], indent=4)}

# Métriques de performance
PERFORMANCE_METRICS = {json.dumps(model['metrics'], indent=4)}

def strategie_optimale(df, symbol="{model['symbol']}", timeframe="{model['timeframe']}"):
    """
    Stratégie optimisée avec les meilleurs paramètres
    """
    # Application des paramètres optimaux
    params = OPTIMAL_PARAMS
    
    # Votre logique de stratégie ici avec les paramètres optimaux
    # ...
    
    return trades, df_signals

def get_optimal_params():
    """Retourne les paramètres optimaux"""
    return OPTIMAL_PARAMS

def get_performance_metrics():
    """Retourne les métriques de performance"""
    return PERFORMANCE_METRICS

if __name__ == "__main__":
    print("🎯 Stratégie Optimisée")
    print(f"📊 Score: {model['score']:.2f}/100")
    print(f"💰 Retour: {model['metrics'].get('total_return', 0):.1f}%")
    print(f"📉 Drawdown: {model['metrics'].get('max_drawdown', 0):.1f}%")
'''
        
        # Sauvegarde du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_file = f"src/strategies/strategie_optimale_{optimization_type}_{timeframe}_{timestamp}.py"
        
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write(strategy_content)
        
        print(f"📄 Fichier de stratégie créé: {strategy_file}")
        return strategy_file
    
    def compare_models(self, optimization_types=None, timeframes=None):
        """Compare les modèles"""
        print("📊 COMPARAISON DES MODÈLES")
        print("=" * 60)
        
        if not self.models:
            print("❌ Aucun modèle à comparer")
            return
        
        # Filtrage
        models_to_compare = {}
        for key, model in self.models.items():
            opt_type = model['optimization_type']
            tf = model['timeframe']
            
            if optimization_types and opt_type not in optimization_types:
                continue
            if timeframes and tf not in timeframes:
                continue
            
            models_to_compare[key] = model
        
        if not models_to_compare:
            print("❌ Aucun modèle correspondant aux critères")
            return
        
        # Affichage du tableau de comparaison
        print(f"{'Modèle':<25} {'Type':<15} {'TF':<5} {'Score':<8} {'Retour':<10} {'DD':<8} {'WR':<8}")
        print("-" * 80)
        
        for key, model in models_to_compare.items():
            print(f"{model['name']:<25} {model['optimization_type']:<15} {model['timeframe']:<5} {model['score']:<8.1f} {model['metrics'].get('total_return', 0):<10.1f}% {model['metrics'].get('max_drawdown', 0):<8.1f}% {model['metrics'].get('win_rate', 0):<8.1f}%")
        
        print()
        
        # Meilleur modèle global
        best_model = max(models_to_compare.values(), key=lambda x: x['score'])
        print(f"🏆 Meilleur modèle global: {best_model['name']}")
        print(f"   📊 Score: {best_model['score']:.2f}/100")
        print(f"   💰 Retour: {best_model['metrics'].get('total_return', 0):.1f}%")
        print(f"   📉 Drawdown: {best_model['metrics'].get('max_drawdown', 0):.1f}%")

def auto_register_from_optimization_results():
    """Enregistre automatiquement les modèles depuis les résultats d'optimisation"""
    print("🔍 RECHERCHE AUTOMATIQUE DE MODÈLES")
    print("=" * 50)
    
    manager = ModelManager()
    results_dir = "results/optimization"
    
    if not os.path.exists(results_dir):
        print("❌ Dossier results/optimization non trouvé")
        return
    
    registered_count = 0
    
    # Parcourir les dossiers d'optimisation
    for folder in os.listdir(results_dir):
        folder_path = os.path.join(results_dir, folder)
        
        if not os.path.isdir(folder_path):
            continue
        
        # Déterminer le type d'optimisation
        optimization_type = None
        if folder.startswith("genetic_optimization_"):
            optimization_type = "genetique"
        elif folder.startswith("aggressive_optimization_"):
            optimization_type = "agressive"
        elif folder.startswith("rl_optimization_"):
            optimization_type = "rl"
        
        if not optimization_type:
            continue
        
        # Extraire le timeframe et le symbole
        parts = folder.split('_')
        if len(parts) >= 4:
            symbol = parts[2]
            timeframe = parts[3]
        else:
            continue
        
        # Chercher le fichier de paramètres optimaux
        param_file = os.path.join(folder_path, "parametres_optimaux.md")
        if not os.path.exists(param_file):
            param_file = os.path.join(folder_path, "parametres_optimaux_agressifs.md")
        
        if not os.path.exists(param_file):
            continue
        
        # Lire les paramètres et métriques
        try:
            with open(param_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extraire les métriques
                metrics = {}
                lines = content.split('\n')
                for line in lines:
                    if '**Total Trades**' in line:
                        metrics['total_trades'] = int(line.split(':')[1].strip())
                    elif '**Win Rate**' in line:
                        metrics['win_rate'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Total Return**' in line:
                        metrics['total_return'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Max Drawdown**' in line:
                        metrics['max_drawdown'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Profit Factor**' in line:
                        metrics['profit_factor'] = float(line.split(':')[1].strip())
                    elif '**Sharpe Ratio**' in line:
                        metrics['sharpe_ratio'] = float(line.split(':')[1].strip())
                    elif '**Gain Moyen**' in line:
                        metrics['avg_win'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif '**Perte Moyenne**' in line:
                        metrics['avg_loss'] = float(line.split(':')[1].strip().replace('%', ''))
                
                # Extraire les paramètres (simplifié)
                params = {}
                in_params_section = False
                for line in lines:
                    if '## Paramètres Optimisés' in line:
                        in_params_section = True
                        continue
                    elif in_params_section and line.startswith('##'):
                        break
                    elif in_params_section and line.strip().startswith('- **'):
                        param_line = line.strip()
                        if ':' in param_line:
                            param_name = param_line.split('**')[1].split('**')[0]
                            param_value = param_line.split(':')[1].strip()
                            try:
                                if '.' in param_value:
                                    params[param_name] = float(param_value)
                                else:
                                    params[param_name] = int(param_value)
                            except:
                                params[param_name] = param_value
                
                # Enregistrer le modèle
                model_name = f"{optimization_type.capitalize()} {timeframe}"
                success = manager.register_model(
                    model_name, params, metrics, optimization_type, timeframe, symbol
                )
                
                if success:
                    registered_count += 1
                
        except Exception as e:
            print(f"❌ Erreur avec {folder}: {e}")
            continue
    
    print(f"\n✅ {registered_count} modèles enregistrés automatiquement")

def main():
    """Fonction principale"""
    print("🎯 GESTION DES MODÈLES OPTIMAUX")
    print("=" * 50)
    
    manager = ModelManager()
    
    print("1. Enregistrer automatiquement les modèles existants")
    print("2. Lister les modèles enregistrés")
    print("3. Comparer les modèles")
    print("4. Exporter un modèle")
    print("5. Créer un fichier de stratégie")
    print()
    
    choice = input("Choisissez une option (1-5): ")
    
    if choice == "1":
        auto_register_from_optimization_results()
    elif choice == "2":
        manager.list_models()
    elif choice == "3":
        manager.compare_models()
    elif choice == "4":
        opt_type = input("Type d'optimisation (genetique/agressive/rl): ")
        timeframe = input("Timeframe (H4/D1): ")
        manager.export_model(opt_type, timeframe)
    elif choice == "5":
        opt_type = input("Type d'optimisation (genetique/agressive/rl): ")
        timeframe = input("Timeframe (H4/D1): ")
        manager.create_strategy_file(opt_type, timeframe)
    else:
        print("❌ Option invalide")

if __name__ == "__main__":
    main() 