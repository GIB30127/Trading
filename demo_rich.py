#!/usr/bin/env python3
"""
Démonstration du Système d'Optimisation avec Rich
Affiche toutes les fonctionnalités avec une interface moderne
"""

import os
import sys
import time
from datetime import datetime

# Rich pour une belle interface
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich import box
from rich.columns import Columns
from rich.rule import Rule

console = Console()

def print_welcome():
    """Affiche l'écran de bienvenue"""
    console.print(Panel.fit(
        "[bold blue]🚀 SYSTÈME D'OPTIMISATION COMPLET - XAUUSD[/bold blue]\n"
        "[cyan]Démonstration des Fonctionnalités[/cyan]\n"
        "[yellow]Interface Moderne avec Rich[/yellow]",
        border_style="blue",
        box=box.DOUBLE
    ))

def show_system_overview():
    """Affiche un aperçu du système"""
    console.print(Panel.fit(
        "[bold green]📋 APERÇU DU SYSTÈME[/bold green]\n"
        "[white]• Optimisation Génétique pour réduire le drawdown[/white]\n"
        "[white]• Optimisation Agressive pour maximiser les gains[/white]\n"
        "[white]• Reinforcement Learning pour l'apprentissage adaptatif[/white]\n"
        "[white]• Fusion de modèles pour combiner les meilleures approches[/white]\n"
        "[white]• Apprentissage continu pour amélioration automatique[/white]\n"
        "[white]• Gestion des modèles optimaux avec sauvegarde[/white]",
        border_style="green"
    ))

def show_optimization_methods():
    """Affiche les méthodes d'optimisation"""
    methods_table = Table(title="🧬 Méthodes d'Optimisation", box=box.ROUNDED)
    methods_table.add_column("Méthode", style="cyan", no_wrap=True)
    methods_table.add_column("Objectif", style="white")
    methods_table.add_column("Avantages", style="green")
    methods_table.add_column("Durée", style="yellow")
    
    methods_table.add_row(
        "Génétique",
        "Réduire Drawdown",
        "Stabilité, Équilibre",
        "5-15 min"
    )
    methods_table.add_row(
        "Agressive",
        "Maximiser Gains",
        "Performance, Rendement",
        "5-15 min"
    )
    methods_table.add_row(
        "Reinforcement Learning",
        "Apprentissage Adaptatif",
        "Intelligence, Adaptation",
        "10-20 min"
    )
    methods_table.add_row(
        "Fusion",
        "Combiner Modèles",
        "Synergie, Robustesse",
        "2-5 min"
    )
    methods_table.add_row(
        "Apprentissage Continu",
        "Amélioration Continue",
        "Évolution, Optimisation",
        "3-8 min"
    )
    
    console.print(methods_table)

def show_performance_metrics():
    """Affiche les métriques de performance"""
    metrics_table = Table(title="📊 Métriques de Performance", box=box.ROUNDED)
    metrics_table.add_column("Métrique", style="cyan", no_wrap=True)
    metrics_table.add_column("Description", style="white")
    metrics_table.add_column("Objectif", style="green")
    
    metrics_table.add_row(
        "Total Return",
        "Rendement total en %",
        "> 200%"
    )
    metrics_table.add_row(
        "Max Drawdown",
        "Perte maximale en %",
        "< 20%"
    )
    metrics_table.add_row(
        "Win Rate",
        "Pourcentage de trades gagnants",
        "> 55%"
    )
    metrics_table.add_row(
        "Profit Factor",
        "Ratio gains/pertes",
        "> 2.0"
    )
    metrics_table.add_row(
        "Sharpe Ratio",
        "Rendement ajusté au risque",
        "> 1.5"
    )
    metrics_table.add_row(
        "Min Pips",
        "Mouvement minimum requis",
        "> 5 pips"
    )
    
    console.print(metrics_table)

def show_file_structure():
    """Affiche la structure des fichiers"""
    structure_table = Table(title="📁 Structure du Projet", box=box.ROUNDED)
    structure_table.add_column("Dossier", style="cyan", no_wrap=True)
    structure_table.add_column("Contenu", style="white")
    structure_table.add_column("Fonction", style="green")
    
    structure_table.add_row(
        "scripts/",
        "Scripts d'optimisation",
        "Logique principale"
    )
    structure_table.add_row(
        "data/raw/",
        "Données MT5 CSV",
        "Données historiques"
    )
    structure_table.add_row(
        "results/",
        "Résultats et analyses",
        "Rapports générés"
    )
    structure_table.add_row(
        "models_optimaux/",
        "Modèles sauvegardés",
        "Paramètres optimaux"
    )
    structure_table.add_row(
        "src/strategies/",
        "Stratégies de base",
        "Logique trading"
    )
    
    console.print(structure_table)

def show_quick_start():
    """Affiche le guide de démarrage rapide"""
    console.print(Panel.fit(
        "[bold yellow]⚡ DÉMARRAGE RAPIDE[/bold yellow]\n"
        "[white]1. [bold]python launch_optimization.py[/bold] - Lancement rapide[/white]\n"
        "[white]2. [bold]python optimize.py[/bold] - Menu principal[/white]\n"
        "[white]3. [bold]python scripts/systeme_optimisation_complet.py[/bold] - Système complet[/white]\n"
        "[white]4. [bold]python scripts/gestion_modeles_optimaux.py[/bold] - Gestion modèles[/white]",
        border_style="yellow"
    ))

def simulate_optimization():
    """Simule une optimisation en temps réel"""
    console.print(Panel.fit(
        "[bold purple]🔄 SIMULATION D'OPTIMISATION[/bold purple]",
        border_style="purple"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        # Simulation génétique
        task1 = progress.add_task("🧬 Optimisation Génétique", total=20)
        for i in range(20):
            time.sleep(0.1)
            progress.update(task1, description=f"Génération {i+1}/20")
            if i % 5 == 0:
                progress.console.print(f"   📊 Retour: [green]{150 + i*10:.1f}%[/green] | DD: [red]{25 - i*0.5:.1f}%[/red]")
            progress.advance(task1)
        
        # Simulation agressive
        task2 = progress.add_task("🔥 Optimisation Agressive", total=15)
        for i in range(15):
            time.sleep(0.1)
            progress.update(task2, description=f"Génération {i+1}/15")
            if i % 3 == 0:
                progress.console.print(f"   💰 Retour: [green]{200 + i*15:.1f}%[/green] | PF: [blue]{2.5 + i*0.1:.2f}[/blue]")
            progress.advance(task2)
        
        # Simulation RL
        task3 = progress.add_task("🤖 Reinforcement Learning", total=10)
        for i in range(10):
            time.sleep(0.1)
            progress.update(task3, description=f"Épisode {i+1}/10")
            if i % 2 == 0:
                progress.console.print(f"   🎯 Récompense: [green]{80 + i*5:.1f}[/green]")
            progress.advance(task3)
        
        # Simulation fusion
        task4 = progress.add_task("🔗 Fusion des Modèles", total=5)
        for i in range(5):
            time.sleep(0.2)
            progress.update(task4, description=f"Test méthode {i+1}/5")
            progress.console.print(f"   📊 Score: [green]{85 + i*3:.1f}[/green]")
            progress.advance(task4)

def show_results_summary():
    """Affiche un résumé des résultats simulés"""
    results_table = Table(title="🏆 Résultats Simulés", box=box.ROUNDED)
    results_table.add_column("Méthode", style="cyan", no_wrap=True)
    results_table.add_column("Score", style="green")
    results_table.add_column("Retour", style="blue")
    results_table.add_column("Drawdown", style="red")
    results_table.add_column("Win Rate", style="yellow")
    
    results_table.add_row("Génétique", "78.5", "340.0%", "15.5%", "58.2%")
    results_table.add_row("Agressive", "82.3", "425.0%", "18.7%", "62.1%")
    results_table.add_row("RL", "79.8", "380.0%", "16.2%", "59.8%")
    results_table.add_row("Fusion", "85.2", "395.0%", "14.8%", "61.5%")
    results_table.add_row("Continu", "87.1", "410.0%", "13.9%", "63.2%")
    
    console.print(results_table)

def show_next_steps():
    """Affiche les prochaines étapes"""
    console.print(Panel.fit(
        "[bold green]🎯 PROCHAINES ÉTAPES[/bold green]\n"
        "[white]1. [bold]Lancer une optimisation réelle[/bold] - Testez sur vos données[/white]\n"
        "[white]2. [bold]Analyser les résultats[/bold] - Comparez les méthodes[/white]\n"
        "[white]3. [bold]Sauvegarder les meilleurs modèles[/bold] - Conservez les paramètres optimaux[/white]\n"
        "[white]4. [bold]Tester en temps réel[/bold] - Validez sur MT5[/white]\n"
        "[white]5. [bold]Optimiser continuellement[/bold] - Améliorez avec le temps[/white]",
        border_style="green"
    ))

def main():
    """Fonction principale de démonstration"""
    print_welcome()
    
    # Aperçu du système
    show_system_overview()
    
    # Méthodes d'optimisation
    show_optimization_methods()
    
    # Métriques de performance
    show_performance_metrics()
    
    # Structure des fichiers
    show_file_structure()
    
    # Démarrage rapide
    show_quick_start()
    
    # Simulation d'optimisation
    simulate_optimization()
    
    # Résultats simulés
    show_results_summary()
    
    # Prochaines étapes
    show_next_steps()
    
    # Menu interactif
    console.print(Rule("[bold blue]Menu Interactif[/bold blue]"))
    
    menu_table = Table(title="🎮 Actions Disponibles", box=box.ROUNDED)
    menu_table.add_column("Option", style="cyan", no_wrap=True)
    menu_table.add_column("Action", style="white")
    
    menu_table.add_row("1", "Lancer l'optimisation complète")
    menu_table.add_row("2", "Voir le menu principal")
    menu_table.add_row("3", "Gérer les modèles")
    menu_table.add_row("4", "Quitter la démo")
    
    console.print(menu_table)
    
    choice = console.input("\n[bold green]Choisissez une action (1-4): [/bold green]")
    
    if choice == "1":
        console.print(Panel.fit("[bold green]🚀 Lancement de l'optimisation...[/bold green]", border_style="green"))
        os.system("python launch_optimization.py")
    elif choice == "2":
        console.print(Panel.fit("[bold blue]📋 Ouverture du menu principal...[/bold blue]", border_style="blue"))
        os.system("python optimize.py")
    elif choice == "3":
        console.print(Panel.fit("[bold violet]💾 Ouverture de la gestion des modèles...[/bold violet]", border_style="violet"))
        os.system("python scripts/gestion_modeles_optimaux.py")
    elif choice == "4":
        console.print("👋 [green]Merci d'avoir testé la démonstration![/green]")
    else:
        console.print("❌ [red]Option invalide[/red]")

if __name__ == "__main__":
    main() 