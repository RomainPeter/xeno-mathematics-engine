#!/usr/bin/env python3
"""
Script pour générer les golden files des intents FCA.
"""

import sys
from pathlib import Path

import orjson

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xme.engines.ae.context import load_context
from xme.engines.ae.next_closure import enumerate_concepts


def intents_sorted(concepts):
    """Extrait et trie les intents des concepts."""
    return [sorted(list(intent)) for (_, intent) in concepts]


def generate_golden(context_path: str, output_path: str):
    """Génère un golden file pour un contexte donné."""
    ctx = load_context(context_path)
    concepts = enumerate_concepts(ctx)
    intents = intents_sorted(concepts)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(orjson.dumps(intents))
    print(f"Generated {output_path} with {len(intents)} intents")


def main():
    """Génère tous les golden files."""
    base = Path(__file__).parent.parent

    # Contexte 4x4
    generate_golden(
        str(base / "tests/fixtures/fca/context_4x4.json"),
        str(base / "tests/golden/ae/context_4x4.intents.json"),
    )

    # Contexte 5x3
    generate_golden(
        str(base / "tests/fixtures/fca/context_5x3.json"),
        str(base / "tests/golden/ae/context_5x3.intents.json"),
    )


if __name__ == "__main__":
    main()
