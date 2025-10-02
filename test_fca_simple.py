#!/usr/bin/env python3
"""
Test simple pour FCA Next-Closure algorithm.
"""

import os
import sys

# Ajouter le répertoire courant au path
sys.path.insert(0, os.getcwd())

try:
    from proofengine.fca.ae_engine import NextClosureAEEngine
    from proofengine.fca.context import Attribute, FormalContext, Object
    from proofengine.fca.next_closure import NextClosure

    print("✅ Imports FCA réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)


def test_simple_context():
    """Test avec un contexte simple."""
    print("\n🧪 Test contexte simple...")

    # Créer un contexte 2×2
    objects = [Object("obj1"), Object("obj2")]
    attributes = [Attribute("attr1"), Attribute("attr2")]

    incidence = {
        (objects[0], attributes[0]): True,  # obj1 a attr1
        (objects[0], attributes[1]): False,  # obj1 n'a pas attr2
        (objects[1], attributes[0]): False,  # obj2 n'a pas attr1
        (objects[1], attributes[1]): True,  # obj2 a attr2
    }

    context = FormalContext(objects, attributes, incidence)
    print(f"Contexte créé: {context}")

    # Test Next-Closure
    next_closure = NextClosure(context)
    concepts = list(next_closure.generate_concepts())

    print(f"Concepts générés: {len(concepts)}")
    for i, concept in enumerate(concepts):
        extent_names = [obj.name for obj in concept.extent.objects]
        intent_names = [attr.name for attr in concept.intent.attributes]
        print(
            f"  {i + 1}. Extent: {{{', '.join(extent_names)}}}, Intent: {{{', '.join(intent_names)}}}"
        )

    return len(concepts) > 0


def test_ae_engine():
    """Test AE Engine."""
    print("\n🔧 Test AE Engine...")

    # Créer un contexte simple
    objects = [Object("obj1"), Object("obj2")]
    attributes = [Attribute("attr1"), Attribute("attr2")]

    incidence = {
        (objects[0], attributes[0]): True,
        (objects[0], attributes[1]): False,
        (objects[1], attributes[0]): False,
        (objects[1], attributes[1]): True,
    }

    context = FormalContext(objects, attributes, incidence)

    # Créer AE Engine
    engine = NextClosureAEEngine()
    ctx = engine.initialize(context)

    print(f"AE Engine initialisé: {ctx}")

    # Exécuter quelques étapes
    for step in range(3):
        result = engine.next_step(ctx)
        if result.success and result.concept:
            extent_names = [obj.name for obj in result.concept.extent.objects]
            intent_names = [attr.name for attr in result.concept.intent.attributes]
            print(
                f"  Étape {step + 1}: Extent: {{{', '.join(extent_names)}}}, Intent: {{{', '.join(intent_names)}}}"
            )
        else:
            print(f"  Étape {step + 1}: {result.error if result.error else 'Pas de concept'}")
            break

    return True


def main():
    """Fonction principale."""
    print("🚀 Test FCA Next-Closure Simple")
    print("=" * 40)

    try:
        # Test contexte simple
        if test_simple_context():
            print("✅ Test contexte simple réussi")
        else:
            print("❌ Test contexte simple échoué")
            return False

        # Test AE Engine
        if test_ae_engine():
            print("✅ Test AE Engine réussi")
        else:
            print("❌ Test AE Engine échoué")
            return False

        print("\n🎉 Tous les tests sont passés !")
        return True

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
