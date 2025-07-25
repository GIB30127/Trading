#!/usr/bin/env python3
"""
Organisation et Nettoyage du Projet
Déplace les fichiers dans les bons dossiers et nettoie la racine
"""

import os
import shutil
from datetime import datetime

def create_directory_structure():
    """Crée la structure de dossiers organisée"""
    
    directories = {
        'scripts': {
            'description': 'Scripts principaux et utilitaires',
            'files': [
                'optimisation_genetique_drawdown.py',
                'reinforcement_learning_optimizer.py',
                'comparaison_optimisation.py',
                'afficher_resultats_multitimeframes.py',
                'test_all_timeframes_xauusd.py',
                'analyse_strategie_auto.py',
                'demo_strategie_xauusd.py'
            ]
        },
        'docs': {
            'description': 'Documentation et README',
            'files': [
                'README_STRATEGIE_XAUUSD.md',
                'README_ANALYSE.md'
            ]
        },
        'src/strategies': {
            'description': 'Stratégies de trading',
            'files': [
                'pine_script_to_python.py'
            ]
        }
    }
    
    # Création des dossiers
    for dir_path in directories.keys():
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Dossier créé/vérifié: {dir_path}")
    
    return directories

def move_files(directories):
    """Déplace les fichiers dans les bons dossiers"""
    
    moved_files = []
    errors = []
    
    for dir_path, info in directories.items():
        for filename in info['files']:
            source_path = filename
            dest_path = os.path.join(dir_path, filename)
            
            if os.path.exists(source_path):
                try:
                    # Vérifier si le fichier de destination existe déjà
                    if os.path.exists(dest_path):
                        # Créer un backup avec timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_path = f"{dest_path}.backup_{timestamp}"
                        shutil.move(dest_path, backup_path)
                        print(f"📦 Backup créé: {backup_path}")
                    
                    # Déplacer le fichier
                    shutil.move(source_path, dest_path)
                    moved_files.append(f"{source_path} → {dest_path}")
                    print(f"📁 Déplacé: {source_path} → {dest_path}")
                    
                except Exception as e:
                    errors.append(f"❌ Erreur avec {source_path}: {e}")
            else:
                print(f"⚠️  Fichier non trouvé: {source_path}")
    
    return moved_files, errors

def create_main_scripts():
    """Crée des scripts principaux dans la racine pour faciliter l'utilisation"""
    
    # Script principal d'optimisation
    main_optimization = '''#!/usr/bin/env python3
"""
Script Principal d'Optimisation
Point d'entrée pour l'optimisation des stratégies
"""

import sys
import os

# Ajout du chemin des scripts
sys.path.append('scripts')

def main():
    print("🚀 OPTIMISATION DES STRATÉGIES")
    print("=" * 40)
    print()
    print("1. Optimisation Génétique")
    print("2. Reinforcement Learning")
    print("3. Comparaison des Méthodes")
    print("4. Test Multi-Timeframes")
    print("5. Affichage des Résultats")
    print("6. Analyse Automatique")
    print()
    
    choice = input("Choisissez une option (1-6): ")
    
    if choice == "1":
        os.system("python scripts/optimisation_genetique_drawdown.py")
    elif choice == "2":
        os.system("python scripts/reinforcement_learning_optimizer.py")
    elif choice == "3":
        os.system("python scripts/comparaison_optimisation.py")
    elif choice == "4":
        os.system("python scripts/test_all_timeframes_xauusd.py")
    elif choice == "5":
        os.system("python scripts/afficher_resultats_multitimeframes.py")
    elif choice == "6":
        os.system("python scripts/analyse_strategie_auto.py")
    else:
        print("❌ Option invalide")

if __name__ == "__main__":
    main()
'''
    
    with open('optimize.py', 'w', encoding='utf-8') as f:
        f.write(main_optimization)
    
    # Script de démonstration
    main_demo = '''#!/usr/bin/env python3
"""
Script Principal de Démonstration
Point d'entrée pour les démonstrations
"""

import sys
import os

# Ajout du chemin des scripts
sys.path.append('scripts')

def main():
    print("🎯 DÉMONSTRATION DES STRATÉGIES")
    print("=" * 40)
    print()
    print("1. Démonstration Stratégie XAUUSD")
    print("2. Test Multi-Timeframes")
    print("3. Affichage des Résultats")
    print()
    
    choice = input("Choisissez une option (1-3): ")
    
    if choice == "1":
        os.system("python scripts/demo_strategie_xauusd.py")
    elif choice == "2":
        os.system("python scripts/test_all_timeframes_xauusd.py")
    elif choice == "3":
        os.system("python scripts/afficher_resultats_multitimeframes.py")
    else:
        print("❌ Option invalide")

if __name__ == "__main__":
    main()
'''
    
    with open('demo.py', 'w', encoding='utf-8') as f:
        f.write(main_demo)

def create_project_readme():
    """Crée un README principal pour le projet"""
    
    readme_content = '''# 🚀 Projet Trading - Optimisation de Stratégies

## 📁 Structure du Projet

```
Trad_Essay_Sven/
├── 📂 data/                    # Données de trading (CSV, MT5)
├── 📂 src/                     # Code source principal
│   ├── 📂 strategies/          # Stratégies de trading
│   ├── 📂 backtesting/         # Systèmes de backtest
│   ├── 📂 analysis/            # Outils d'analyse
│   └── 📂 utils/               # Utilitaires
├── 📂 scripts/                 # Scripts d'optimisation et utilitaires
├── 📂 docs/                    # Documentation
├── 📂 results/                 # Résultats des tests et analyses
├── 📂 Pine_Scripts/            # Scripts Pine Script originaux
└── 📂 config/                  # Configuration
```

## 🎯 Scripts Principaux

### 🧬 Optimisation
- `optimize.py` - Script principal d'optimisation
- `scripts/optimisation_genetique_drawdown.py` - Optimisation génétique
- `scripts/reinforcement_learning_optimizer.py` - RL pour optimisation
- `scripts/comparaison_optimisation.py` - Comparaison des méthodes

### 📊 Analyse et Tests
- `demo.py` - Script principal de démonstration
- `scripts/test_all_timeframes_xauusd.py` - Tests multi-timeframes
- `scripts/afficher_resultats_multitimeframes.py` - Affichage des résultats
- `scripts/analyse_strategie_auto.py` - Analyse automatique

## 🚀 Utilisation Rapide

### Optimisation
```bash
python optimize.py
```

### Démonstration
```bash
python demo.py
```

### Test Multi-Timeframes
```bash
python scripts/test_all_timeframes_xauusd.py
```

## 📈 Stratégies Disponibles

- **XAUUSD Sharpe 1 Simple** - Stratégie optimisée pour l'or
- **Multi-Timeframes** - Tests sur M5, M15, M30, H1, H4, D1
- **Optimisation Génétique** - Réduction du drawdown
- **Reinforcement Learning** - Adaptation en temps réel

## 📊 Résultats

Les résultats sont sauvegardés dans `results/` avec :
- Rapports d'analyse détaillés
- Graphiques interactifs
- Métriques de performance
- Optimisations par timeframe

## 🔧 Configuration

Vérifiez `config/requirements.txt` pour les dépendances.

## 📚 Documentation

- `docs/README_STRATEGIE_XAUUSD.md` - Documentation de la stratégie
- `docs/README_ANALYSE.md` - Guide d'analyse automatique

---
*Projet créé le: {date}*
'''.format(date=datetime.now().strftime('%Y-%m-%d'))
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

def main():
    """Fonction principale d'organisation"""
    print("🗂️  ORGANISATION DU PROJET")
    print("=" * 50)
    
    # Création de la structure
    print("\n📁 Création de la structure de dossiers...")
    directories = create_directory_structure()
    
    # Déplacement des fichiers
    print("\n📦 Déplacement des fichiers...")
    moved_files, errors = move_files(directories)
    
    # Création des scripts principaux
    print("\n🎯 Création des scripts principaux...")
    create_main_scripts()
    
    # Création du README principal
    print("\n📚 Création du README principal...")
    create_project_readme()
    
    # Résumé
    print("\n✅ ORGANISATION TERMINÉE!")
    print("=" * 50)
    
    print(f"\n📁 Fichiers déplacés: {len(moved_files)}")
    for file_move in moved_files:
        print(f"   • {file_move}")
    
    if errors:
        print(f"\n❌ Erreurs: {len(errors)}")
        for error in errors:
            print(f"   • {error}")
    
    print(f"\n🎯 Scripts principaux créés:")
    print(f"   • optimize.py - Optimisation des stratégies")
    print(f"   • demo.py - Démonstrations")
    print(f"   • README.md - Documentation principale")
    
    print(f"\n📂 Structure organisée:")
    print(f"   • scripts/ - Scripts d'optimisation")
    print(f"   • docs/ - Documentation")
    print(f"   • src/strategies/ - Stratégies de trading")
    
    print(f"\n🚀 Utilisation:")
    print(f"   • python optimize.py - Pour l'optimisation")
    print(f"   • python demo.py - Pour les démonstrations")

if __name__ == "__main__":
    main() 