#!/usr/bin/env python3
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
