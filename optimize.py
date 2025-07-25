#!/usr/bin/env python3
"""
Script Principal d'Optimisation
Point d'entrée pour l'optimisation des stratégies
"""

import sys
import os

# Rich pour une belle interface
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Ajout du chemin des scripts
sys.path.append('scripts')

def main():
    console.print(Panel.fit(
        "[bold blue]🚀 SYSTÈME D'OPTIMISATION - MENU PRINCIPAL[/bold blue]\n"
        "[cyan]Point d'entrée pour tous les scripts d'optimisation[/cyan]",
        border_style="blue",
        box=box.DOUBLE
    ))
    
    # Menu avec Rich
    menu_table = Table(title="🎯 Options d'Optimisation", box=box.ROUNDED)
    menu_table.add_column("Option", style="cyan", no_wrap=True)
    menu_table.add_column("Description", style="white")
    menu_table.add_column("Objectif", style="yellow")
    
    menu_table.add_row("1", "Optimisation Génétique", "Réduire le Drawdown")
    menu_table.add_row("2", "Optimisation Agressive", "Maximiser les Gains")
    menu_table.add_row("3", "Reinforcement Learning", "Apprentissage Adaptatif")
    menu_table.add_row("4", "Système Complet", "Toutes les Méthodes")
    menu_table.add_row("5", "Comparaison", "Analyser les Résultats")
    menu_table.add_row("6", "Multi-Timeframes", "Test sur Tous les TF")
    menu_table.add_row("7", "Affichage Résultats", "Visualiser les Données")
    menu_table.add_row("8", "Analyse Automatique", "Rapports Détaillés")
    menu_table.add_row("9", "Gestion Modèles", "Sauvegarder/Charger")
    
    console.print(menu_table)
    
    choice = console.input("\n[bold green]Choisissez une option (1-9): [/bold green]")
    
    if choice == "1":
        console.print(Panel.fit("[bold blue]🧬 Optimisation Génétique[/bold blue]", border_style="blue"))
        os.system("python scripts/optimisation_genetique_drawdown.py")
    elif choice == "2":
        console.print(Panel.fit("[bold red]🔥 Optimisation Agressive[/bold red]", border_style="red"))
        os.system("python scripts/optimisation_agressive_gains.py")
    elif choice == "3":
        console.print(Panel.fit("[bold purple]🤖 Reinforcement Learning[/bold purple]", border_style="purple"))
        os.system("python scripts/reinforcement_learning_optimizer.py")
    elif choice == "4":
        console.print(Panel.fit("[bold green]🔗 Système d'Optimisation Complet[/bold green]", border_style="green"))
        os.system("python scripts/systeme_optimisation_complet.py")
    elif choice == "5":
        console.print(Panel.fit("[bold yellow]📊 Comparaison des Méthodes[/bold yellow]", border_style="yellow"))
        os.system("python scripts/comparaison_optimisation.py")
    elif choice == "6":
        console.print(Panel.fit("[bold cyan]⏰ Test Multi-Timeframes[/bold cyan]", border_style="cyan"))
        os.system("python scripts/test_all_timeframes_xauusd.py")
    elif choice == "7":
        console.print(Panel.fit("[bold magenta]📈 Affichage des Résultats[/bold magenta]", border_style="magenta"))
        os.system("python scripts/afficher_resultats_multitimeframes.py")
    elif choice == "8":
        console.print(Panel.fit("[bold orange]📋 Analyse Automatique[/bold orange]", border_style="orange"))
        os.system("python scripts/analyse_strategie_auto.py")
    elif choice == "9":
        console.print(Panel.fit("[bold violet]💾 Gestion des Modèles[/bold violet]", border_style="violet"))
        os.system("python scripts/gestion_modeles_optimaux.py")
    else:
        console.print("❌ [red]Option invalide[/red]")

if __name__ == "__main__":
    main()
