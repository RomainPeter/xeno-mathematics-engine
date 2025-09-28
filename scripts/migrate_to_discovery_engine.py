#!/usr/bin/env python3
"""
Script de migration vers discovery-engine-2cat.
Prépare les composants à migrer depuis proof-engine-for-code.
"""

import shutil
from pathlib import Path


def create_discovery_engine_structure():
    """Créer la structure du nouveau repository discovery-engine-2cat."""

    base_dir = Path("discovery-engine-2cat")

    # Structure des dossiers
    directories = [
        "external/proof-engine-core",  # Submodule
        "orchestrator",
        "methods/ae",
        "methods/cegis",
        "methods/egraph",
        "domain/regtech_code",
        "schemas",
        "bench",
        "ci",
        "prompts",
        "tests",
        "docs",
        "scripts",
    ]

    # Créer les dossiers
    for directory in directories:
        (base_dir / directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return base_dir


def migrate_schemas():
    """Migrer les schémas JSON v0.1."""

    source_schemas = Path("specs/v0.1")
    target_schemas = Path("discovery-engine-2cat/schemas")

    if not source_schemas.exists():
        print("❌ Source schemas directory not found")
        return False

    # Créer le dossier target
    target_schemas.mkdir(parents=True, exist_ok=True)

    # Fichiers à migrer
    schema_files = [
        "dca.schema.json",
        "composite-op.schema.json",
        "domain-spec.schema.json",
        "failreason-extended.schema.json",
        "domain-spec-regtech-code.json",
    ]

    for schema_file in schema_files:
        source_file = source_schemas / schema_file
        target_file = target_schemas / schema_file

        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"✅ Migrated schema: {schema_file}")
        else:
            print(f"⚠️  Schema not found: {schema_file}")

    return True


def migrate_orchestrator_components():
    """Migrer les composants de l'orchestrateur."""

    # Composants à migrer
    components = {
        "orchestrator/unified_orchestrator.py": "proofengine/orchestrator/unified_orchestrator.py",
        "orchestrator/ae_loop.py": "proofengine/orchestrator/ae_loop.py",
        "orchestrator/cegis_loop.py": "proofengine/orchestrator/cegis_loop.py",
        "orchestrator/selection.py": "proofengine/planner/selection.py",
        "methods/egraph/egraph.py": "proofengine/core/egraph.py",
    }

    base_dir = Path("discovery-engine-2cat")

    for target_path, source_path in components.items():
        source_file = Path(source_path)
        target_file = base_dir / target_path

        if source_file.exists():
            # Créer le dossier parent si nécessaire
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Copier le fichier
            shutil.copy2(source_file, target_file)
            print(f"✅ Migrated component: {target_path}")
        else:
            print(f"⚠️  Component not found: {source_path}")

    return True


def migrate_prompts():
    """Migrer les micro-prompts LLM."""

    source_prompts = Path("prompts")
    target_prompts = Path("discovery-engine-2cat/prompts")

    if not source_prompts.exists():
        print("❌ Source prompts directory not found")
        return False

    # Créer le dossier target
    target_prompts.mkdir(parents=True, exist_ok=True)

    # Fichiers à migrer
    prompt_files = [
        "ae_implications.tpl",
        "ae_counterexamples.tpl",
        "cegis_choreography.tpl",
    ]

    for prompt_file in prompt_files:
        source_file = source_prompts / prompt_file
        target_file = target_prompts / prompt_file

        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"✅ Migrated prompt: {prompt_file}")
        else:
            print(f"⚠️  Prompt not found: {prompt_file}")

    return True


def migrate_configs():
    """Migrer les configurations."""

    source_config = Path("configs/unified_architecture.yaml")
    target_config = Path("discovery-engine-2cat/configs/unified_architecture.yaml")

    if source_config.exists():
        target_config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_config, target_config)
        print("✅ Migrated config: unified_architecture.yaml")
    else:
        print(f"⚠️  Config not found: {source_config}")

    return True


def migrate_scripts():
    """Migrer les scripts de test et démo."""

    scripts_to_migrate = {
        "scripts/test_unified_architecture.py": "scripts/test_discovery_engine.py",
        "scripts/demo_unified_architecture.py": "scripts/demo_discovery_engine.py",
    }

    base_dir = Path("discovery-engine-2cat")

    for source_path, target_path in scripts_to_migrate.items():
        source_file = Path(source_path)
        target_file = base_dir / target_path

        if source_file.exists():
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            print(f"✅ Migrated script: {target_path}")
        else:
            print(f"⚠️  Script not found: {source_path}")

    return True


def create_readme():
    """Créer le README pour discovery-engine-2cat."""

    readme_content = """# Discovery Engine 2-Cat

Orchestrateur 2-cat, AE/CEGIS, e-graphs, bandit/MCTS, domain adapters, benchmarks.

## Architecture

Ce repository contient l'agent de découverte basé sur l'Architecture Unifiée v0.1, utilisant le Proof Engine comme dépendance versionnée.

### Structure

```
discovery-engine-2cat/
├── external/
│   └── proof-engine-core/          # Submodule @ tag v0.1.0
├── orchestrator/                   # Orchestrateur principal
├── methods/                        # Méthodes AE/CEGIS/e-graph
├── domain/                         # Domain adapters
├── schemas/                        # JSON Schemas v0.1
├── bench/                          # Benchmarks + baselines
├── ci/                            # CI/CD + attestations
└── prompts/                       # Micro-prompts LLM
```

### Composants

- **AE (Attribute Exploration)**: Next-closure algorithm avec oracle Verifier
- **CEGIS**: Counter-Example Guided Inductive Synthesis
- **E-graphs**: Canonicalisation et anti-redondance structurelle
- **Sélection**: Bandit contextuel, MCTS, Pareto
- **Domain Adapters**: RegTech/Code, etc.

### Utilisation

```bash
# Tests
python scripts/test_discovery_engine.py

# Démo
python scripts/demo_discovery_engine.py

# Benchmarks
python scripts/bench_discovery_engine.py
```

### Dépendances

- **proof-engine-core**: Noyau stable (PCAP, runner hermétique, attestations)
- **Python 3.9+**: Runtime
- **OPA**: Oracle pour vérification
- **Static Analysis**: Outils d'analyse statique

### Versioning

- **discovery-engine**: v0.x (exploration et orchestration)
- **proof-engine-core**: v0.x (noyau stable)
- Compatibilité: `proof-engine-core>=0.1.0,<0.2.0`

## Développement

### Migration depuis proof-engine-for-code

Ce repository a été créé en migrant les composants d'exploration depuis le Proof Engine principal pour permettre un développement indépendant et accéléré.

### Garde-fous

- Aucune modification directe de `proof-engine-core`
- Toute évolution du core → PR sur proof-engine-core → nouveau tag → bump submodule
- Attestations distinctes par repository
- Versionnage coordonné avec contraintes de compatibilité

## License

Voir LICENSE pour les détails.
"""

    readme_file = Path("discovery-engine-2cat/README.md")
    readme_file.parent.mkdir(parents=True, exist_ok=True)

    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("✅ Created README.md")
    return True


def create_gitignore():
    """Créer le .gitignore pour discovery-engine-2cat."""

    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Discovery Engine specific
out/
logs/
artifacts/
cache/
temp/

# Benchmarks
bench/results/
bench/cache/

# CI/CD
ci/artifacts/
ci/logs/

# External dependencies
external/proof-engine-core/
"""

    gitignore_file = Path("discovery-engine-2cat/.gitignore")
    gitignore_file.parent.mkdir(parents=True, exist_ok=True)

    with open(gitignore_file, "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    print("✅ Created .gitignore")
    return True


def create_requirements():
    """Créer requirements.txt pour discovery-engine-2cat."""

    requirements_content = """# Discovery Engine 2-Cat Requirements

# Core dependencies
numpy>=1.21.0
asyncio
dataclasses
typing-extensions

# ML/RL dependencies
scikit-learn>=1.0.0
scipy>=1.7.0

# JSON Schema validation
jsonschema>=4.0.0

# Async HTTP (for OPA client)
aiohttp>=3.8.0

# Development dependencies
pytest>=6.0.0
pytest-asyncio>=0.18.0
black>=22.0.0
ruff>=0.1.0

# Proof Engine Core (submodule)
# Note: proof-engine-core is included as a git submodule
# Version constraints: >=0.1.0,<0.2.0
"""

    requirements_file = Path("discovery-engine-2cat/requirements.txt")
    requirements_file.parent.mkdir(parents=True, exist_ok=True)

    with open(requirements_file, "w", encoding="utf-8") as f:
        f.write(requirements_content)

    print("✅ Created requirements.txt")
    return True


def create_makefile():
    """Créer Makefile pour discovery-engine-2cat."""

    makefile_content = """# Discovery Engine 2-Cat Makefile

PY=python3

.PHONY: setup test demo bench clean install submodule-update

# Setup
setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
	@echo "Discovery Engine 2-Cat setup complete"

# Submodule management
submodule-init:
	git submodule init
	git submodule update

submodule-update:
	git submodule update --remote --merge

# Testing
test:
	. .venv/bin/activate && $(PY) scripts/test_discovery_engine.py

test-ae:
	. .venv/bin/activate && $(PY) -m pytest tests/methods/ae/ -v

test-cegis:
	. .venv/bin/activate && $(PY) -m pytest tests/methods/cegis/ -v

test-egraph:
	. .venv/bin/activate && $(PY) -m pytest tests/methods/egraph/ -v

# Demo
demo:
	. .venv/bin/activate && $(PY) scripts/demo_discovery_engine.py

demo-ae:
	. .venv/bin/activate && $(PY) scripts/demo_ae_loop.py

demo-cegis:
	. .venv/bin/activate && $(PY) scripts/demo_cegis_loop.py

# Benchmarks
bench:
	. .venv/bin/activate && $(PY) scripts/bench_discovery_engine.py

bench-baseline:
	. .venv/bin/activate && $(PY) scripts/bench_baseline.py

bench-comparison:
	. .venv/bin/activate && $(PY) scripts/bench_comparison.py

# Domain-specific
demo-regtech:
	. .venv/bin/activate && $(PY) scripts/demo_regtech_code.py

# Development
fmt:
	black . && ruff check --fix .

lint:
	ruff check .

type-check:
	mypy .

# Cleanup
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf out/
	rm -rf logs/
	rm -rf artifacts/
	rm -rf cache/

# Installation
install:
	pip install -e .

# Full CI
ci: setup test demo bench
	@echo "✅ Full CI pipeline completed"
"""

    makefile_file = Path("discovery-engine-2cat/Makefile")
    makefile_file.parent.mkdir(parents=True, exist_ok=True)

    with open(makefile_file, "w", encoding="utf-8") as f:
        f.write(makefile_content)

    print("✅ Created Makefile")
    return True


def main():
    """Fonction principale de migration."""

    print("🚀 Migration vers discovery-engine-2cat")
    print("=" * 50)

    # 1. Créer la structure
    print("\n📁 Creating repository structure...")
    create_discovery_engine_structure()

    # 2. Migrer les schémas
    print("\n📋 Migrating schemas...")
    migrate_schemas()

    # 3. Migrer les composants orchestrateur
    print("\n🎭 Migrating orchestrator components...")
    migrate_orchestrator_components()

    # 4. Migrer les prompts
    print("\n🤖 Migrating prompts...")
    migrate_prompts()

    # 5. Migrer les configurations
    print("\n⚙️ Migrating configurations...")
    migrate_configs()

    # 6. Migrer les scripts
    print("\n📜 Migrating scripts...")
    migrate_scripts()

    # 7. Créer les fichiers de base
    print("\n📄 Creating base files...")
    create_readme()
    create_gitignore()
    create_requirements()
    create_makefile()

    print("\n🎉 Migration completed successfully!")
    print("\n📋 Next steps:")
    print("1. cd discovery-engine-2cat")
    print("2. git init")
    print("3. git submodule add <proof-engine-core-url> external/proof-engine-core")
    print("4. git add .")
    print("5. git commit -m 'Initial commit: Discovery Engine 2-Cat'")
    print("6. git remote add origin <discovery-engine-2cat-url>")
    print("7. git push -u origin main")


if __name__ == "__main__":
    main()
