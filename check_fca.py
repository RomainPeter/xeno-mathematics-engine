#!/usr/bin/env python3
"""
Vérification simple des imports FCA.
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.getcwd())

print("🔍 Vérification des imports FCA...")

try:
    print("Import context...")
    from proofengine.fca.context import Object, Attribute, Intent

    print("✅ Context importé")

    print("Import next_closure...")
    from proofengine.fca.next_closure import NextClosure  # noqa: F401

    print("✅ Next-Closure importé")

    print("Import ae_engine...")
    from proofengine.fca.ae_engine import NextClosureAEEngine  # noqa: F401

    print("✅ AE Engine importé")

    print("\n🎉 Tous les imports FCA sont réussis !")

    # Test simple
    print("\n🧪 Test simple...")
    obj = Object("test")
    attr = Attribute("test")
    intent = Intent({attr})
    print(f"Objet: {obj}")
    print(f"Attribut: {attr}")
    print(f"Intent: {intent}")

    print("\n✅ Test FCA simple réussi !")

except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)
