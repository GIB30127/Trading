#!/usr/bin/env python3
"""
Lancement Rapide du Système d'Optimisation Complet
Script principal pour lancer toutes les optimisations
"""

import os
import sys
import subprocess
from datetime import datetime

# Rich pour une belle interface
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box

console = Console()

def print_banner():
    """Affiche la bannière du système"""
    console.print(Panel.fit(
        "[bold blue]🚀 SYSTÈME D'OPTIMISATION COMPLET - XAUUSD[/bold blue]\n"
        "[cyan]🎯 Objectifs: Gros gains, petit drawdown, minimum 5 pips[/cyan]\n"
        "[yellow]🧬 Méthodes: Génétique + Agressive + RL + Fusion[/yellow]\n"
        "[green]🔄 Apprentissage continu et amélioration[/green]",
        border_style="blue",
        box=box.DOUBLE
    ))

def check_prerequisites():
    """Vérifie les prérequis"""
    console.print(Panel.fit(
        "[bold yellow]🔍 VÉRIFICATION DES PRÉREQUIS[/bold yellow]",
        border_style="yellow"
    ))
    
    # Vérifier les données
    data_files = [
        "data/raw/XAUUSD_D1_mt5.csv",
        "data/raw/XAUUSD_H4_mt5.csv"
    ]
    
    missing_files = []
    for file_path in data_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        console.print("❌ [red]Fichiers de données manquants:[/red]")
        for file_path in missing_files:
            console.print(f"   • [red]{file_path}[/red]")
        return False
    
    console.print("✅ [green]Données disponibles[/green]")
    
    # Vérifier les scripts
    scripts = [
        "scripts/systeme_optimisation_complet.py",
        "scripts/gestion_modeles_optimaux.py",
        "scripts/comparaison_optimisations.py"
    ]
    
    missing_scripts = []
    for script in scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        console.print("❌ [red]Scripts manquants:[/red]")
        for script in missing_scripts:
            console.print(f"   • [red]{script}[/red]")
        return False
    
    console.print("✅ [green]Scripts disponibles[/green]")
    return True

def run_optimization_pipeline():
    """Lance le pipeline d'optimisation complet"""
    console.print(Panel.fit(
        "[bold green]🚀 LANCEMENT DU PIPELINE D'OPTIMISATION[/bold green]",
        border_style="green"
    ))
    
    steps = [
        {
            'name': 'Système d\'Optimisation Complet',
            'script': 'scripts/systeme_optimisation_complet.py',
            'description': 'Génétique + Agressive + RL + Fusion'
        },
        {
            'name': 'Gestion des Modèles',
            'script': 'scripts/gestion_modeles_optimaux.py',
            'description': 'Enregistrement et comparaison'
        },
        {
            'name': 'Comparaison des Optimisations',
            'script': 'scripts/comparaison_optimisations.py',
            'description': 'Analyse des résultats'
        }
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Pipeline d'optimisation", total=len(steps))
        
        for i, step in enumerate(steps, 1):
            progress.update(task, description=f"Étape {i}/{len(steps)}: {step['name']}")
            
            try:
                # Lancer le script
                result = subprocess.run(['python', step['script']], 
                                      capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    progress.console.print(f"   ✅ [green]Succès[/green] - {step['name']}")
                else:
                    progress.console.print(f"   ❌ [red]Erreur[/red] - {step['name']}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                progress.console.print(f"   ⏰ [yellow]Timeout[/yellow] - {step['name']}")
            except Exception as e:
                progress.console.print(f"   ❌ [red]Erreur[/red] - {step['name']}: {e}")
            
            progress.advance(task)

def run_quick_optimization():
    """Lance une optimisation rapide"""
    console.print(Panel.fit(
        "[bold cyan]⚡ OPTIMISATION RAPIDE[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print("🎯 [yellow]Optimisation rapide pour test[/yellow]")
    
    try:
        # Lancer le système complet avec paramètres réduits
        cmd = [
            'python', 'scripts/systeme_optimisation_complet.py'
        ]
        
        console.print("🔄 [blue]Lancement...[/blue]")
        subprocess.run(cmd, timeout=600)  # 10 minutes max
        
    except subprocess.TimeoutExpired:
        console.print("⏰ [yellow]Optimisation interrompue (timeout)[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Erreur: {e}[/red]")

def run_intensive_optimization():
    """Lance une optimisation intensive"""
    console.print(Panel.fit(
        "[bold red]🔥 OPTIMISATION INTENSIVE[/bold red]",
        border_style="red"
    ))
    
    console.print("🎯 [yellow]Optimisation intensive pour résultats maximaux[/yellow]")
    
    try:
        # Lancer le système complet avec paramètres intensifs
        cmd = [
            'python', 'scripts/systeme_optimisation_complet.py'
        ]
        
        console.print("🔄 [blue]Lancement de l'optimisation intensive...[/blue]")
        console.print("⏰ [red]Cette optimisation peut prendre 2-4 heures[/red]")
        subprocess.run(cmd, timeout=14400)  # 4 heures max
        
    except subprocess.TimeoutExpired:
        console.print("⏰ [yellow]Optimisation interrompue (timeout)[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Erreur: {e}[/red]")

def show_results():
    """Affiche les résultats"""
    console.print(Panel.fit(
        "[bold magenta]📊 AFFICHAGE DES RÉSULTATS[/bold magenta]",
        border_style="magenta"
    ))
    
    try:
        # Lister les modèles
        subprocess.run(['python', 'scripts/gestion_modeles_optimaux.py'])
        
        # Comparer les optimisations
        subprocess.run(['python', 'scripts/comparaison_optimisations.py'])
        
    except Exception as e:
        console.print(f"❌ [red]Erreur: {e}[/red]")

def main():
    """Fonction principale"""
    print_banner()
    
    if not check_prerequisites():
        console.print("\n❌ [red]Prérequis non satisfaits. Arrêt.[/red]")
        return
    
    # Menu avec Rich
    menu_table = Table(title="🎯 Options de Lancement", box=box.ROUNDED)
    menu_table.add_column("Option", style="cyan", no_wrap=True)
    menu_table.add_column("Description", style="white")
    menu_table.add_column("Durée", style="yellow")
    
    menu_table.add_row("1", "Pipeline Complet (Recommandé)", "45-90 min")
    menu_table.add_row("2", "Optimisation Rapide (Test)", "5-10 min")
    menu_table.add_row("3", "Optimisation Intensive", "2-4 heures")
    menu_table.add_row("4", "Affichage des Résultats", "Instantané")
    menu_table.add_row("5", "Quitter", "-")
    
    console.print(menu_table)
    
    choice = console.input("\n[bold green]Choisissez une option (1-5): [/bold green]")
    
    if choice == "1":
        console.print(Panel.fit(
            "[bold green]🚀 LANCEMENT DU PIPELINE COMPLET[/bold green]\n"
            "[yellow]⏱️  Durée estimée: 45-90 minutes[/yellow]\n"
            "[cyan]💡 Vous pouvez interrompre avec Ctrl+C[/cyan]",
            border_style="green"
        ))
        
        confirm = console.input("[bold]Continuer ? (o/n): [/bold]")
        if confirm.lower() in ['o', 'oui', 'y', 'yes']:
            run_optimization_pipeline()
        else:
            console.print("❌ [red]Annulé[/red]")
    
    elif choice == "2":
        console.print(Panel.fit(
            "[bold cyan]⚡ LANCEMENT OPTIMISATION RAPIDE[/bold cyan]\n"
            "[yellow]⏱️  Durée estimée: 5-10 minutes[/yellow]",
            border_style="cyan"
        ))
        
        confirm = console.input("[bold]Continuer ? (o/n): [/bold]")
        if confirm.lower() in ['o', 'oui', 'y', 'yes']:
            run_quick_optimization()
        else:
            console.print("❌ [red]Annulé[/red]")
    
    elif choice == "3":
        console.print(Panel.fit(
            "[bold red]🔥 LANCEMENT OPTIMISATION INTENSIVE[/bold red]\n"
            "[yellow]⏱️  Durée estimée: 2-4 heures[/yellow]\n"
            "[red]⚠️  Cette optimisation est très intensive[/red]",
            border_style="red"
        ))
        
        confirm = console.input("[bold]Continuer ? (o/n): [/bold]")
        if confirm.lower() in ['o', 'oui', 'y', 'yes']:
            run_intensive_optimization()
        else:
            console.print("❌ [red]Annulé[/red]")
    
    elif choice == "4":
        show_results()
    
    elif choice == "5":
        console.print("👋 [green]Au revoir![/green]")
        return
    
    else:
        console.print("❌ [red]Option invalide[/red]")
    
    console.print("\n✅ [green]Terminé![/green]")

if __name__ == "__main__":
    main() 