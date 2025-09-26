#!/usr/bin/env python3
"""
Script de vérification simple pour ProofEngine
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def main():
    print("🔍 ProofEngine - Vérification Simple")
    print("=" * 40)
    
    # 1. Vérifier les variables d'environnement
    print("\n1. Variables d'environnement...")
    api_key = os.getenv('OPENROUTER_API_KEY')
    model = os.getenv('OPENROUTER_MODEL')
    
    if api_key and model:
        print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
        print(f"✅ Modèle: {model}")
    else:
        print("❌ Variables manquantes")
        return 1
    
    # 2. Test ping
    print("\n2. Test de connectivité...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'proofengine.runner.cli', 'ping'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Connectivité LLM OK")
        else:
            print(f"❌ Échec: {result.stderr}")
            return 1
    except Exception as e:
        print(f"❌ Exception: {e}")
        return 1
    
    # 3. Test plan
    print("\n3. Test de génération de plan...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'proofengine.runner.cli', 'propose-plan',
            '--goal', 'Test simple',
            '--x-summary', '{}',
            '--obligations', '[]',
            '--history', '[]'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Génération de plan OK")
        else:
            print(f"❌ Échec: {result.stderr}")
            return 1
    except Exception as e:
        print(f"❌ Exception: {e}")
        return 1
    
    # 4. Test actions
    print("\n4. Test de génération d'actions...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'proofengine.runner.cli', 'propose-actions',
            '--task', 'Test simple',
            '--k', '2'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Génération d'actions OK")
        else:
            print(f"❌ Échec: {result.stderr}")
            return 1
    except Exception as e:
        print(f"❌ Exception: {e}")
        return 1
    
    print("\n🎉 Toutes les vérifications sont passées !")
    return 0

if __name__ == "__main__":
    sys.exit(main())
