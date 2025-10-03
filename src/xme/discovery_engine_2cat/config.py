"""
Configuration pour le discovery-engine-2cat v0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml  # type: ignore[import-untyped]


@dataclass
class AEConfig:
    """Configuration pour Attribute Exploration."""

    context: str  # Chemin vers le contexte FCA
    timeout_ms: int = 5000  # Timeout en millisecondes
    max_concepts: int = 100  # Nombre maximum de concepts à générer


@dataclass
class CEGISConfig:
    """Configuration pour CEGIS."""

    secret: str  # Secret à découvrir
    max_iters: int = 16  # Nombre maximum d'itérations
    timeout_ms: int = 5000  # Timeout en millisecondes
    domain: str = "bitvector"  # Domaine de synthèse


@dataclass
class BudgetsConfig:
    """Configuration des budgets."""

    ae_ms: int = 1500  # Budget AE en millisecondes
    cegis_ms: int = 1500  # Budget CEGIS en millisecondes
    total_ms: int = 10000  # Budget total en millisecondes


@dataclass
class OutputsConfig:
    """Configuration des sorties."""

    psp: str = "artifacts/psp/2cat.json"  # Fichier PSP de sortie
    run_dir: str = "artifacts/pcap"  # Répertoire des runs PCAP
    metrics: str = "artifacts/metrics/2cat.json"  # Fichier métriques
    report: str = "artifacts/reports/2cat.json"  # Fichier rapport


@dataclass
class PackConfig:
    """Configuration du pack hermétique."""

    out: str = "dist/"  # Répertoire de sortie
    include: List[str] = field(
        default_factory=lambda: [
            "artifacts/psp/*.json",
            "artifacts/pcap/run-*.jsonl",
            "docs/psp.schema.json",
        ]
    )  # Patterns de fichiers à inclure
    exclude: List[str] = field(
        default_factory=lambda: ["**/__pycache__/**", "**/.git/**", "**/node_modules/**"]
    )  # Patterns de fichiers à exclure
    name: str = "2cat-pack"  # Nom de base du pack


@dataclass
class DiscoveryEngine2CatConfig:
    """Configuration complète du discovery-engine-2cat."""

    ae: AEConfig
    cegis: CEGISConfig
    budgets: BudgetsConfig
    outputs: OutputsConfig
    pack: PackConfig

    # Métadonnées
    version: str = "v0"
    description: str = "Discovery Engine 2Cat v0 - Pipeline unifié AE+CEGIS"

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "DiscoveryEngine2CatConfig":
        """
        Charge la configuration depuis un fichier YAML.

        Args:
            yaml_path: Chemin vers le fichier YAML

        Returns:
            Configuration chargée
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Extraire les sections
        ae_data = data.get("ae", {})
        cegis_data = data.get("cegis", {})
        budgets_data = data.get("budgets", {})
        outputs_data = data.get("outputs", {})
        pack_data = data.get("pack", {})

        # Créer les objets de configuration
        ae_config = AEConfig(**ae_data)
        cegis_config = CEGISConfig(**cegis_data)
        budgets_config = BudgetsConfig(**budgets_data)
        outputs_config = OutputsConfig(**outputs_data)
        pack_config = PackConfig(**pack_data)

        return cls(
            ae=ae_config,
            cegis=cegis_config,
            budgets=budgets_config,
            outputs=outputs_config,
            pack=pack_config,
            version=data.get("version", "v0"),
            description=data.get("description", "Discovery Engine 2Cat v0"),
        )

    def to_yaml(self, yaml_path: Path) -> None:
        """
        Sauvegarde la configuration dans un fichier YAML.

        Args:
            yaml_path: Chemin vers le fichier YAML de sortie
        """
        data = {
            "version": self.version,
            "description": self.description,
            "ae": {
                "context": self.ae.context,
                "timeout_ms": self.ae.timeout_ms,
                "max_concepts": self.ae.max_concepts,
            },
            "cegis": {
                "secret": self.cegis.secret,
                "max_iters": self.cegis.max_iters,
                "timeout_ms": self.cegis.timeout_ms,
                "domain": self.cegis.domain,
            },
            "budgets": {
                "ae_ms": self.budgets.ae_ms,
                "cegis_ms": self.budgets.cegis_ms,
                "total_ms": self.budgets.total_ms,
            },
            "outputs": {
                "psp": self.outputs.psp,
                "run_dir": self.outputs.run_dir,
                "metrics": self.outputs.metrics,
                "report": self.outputs.report,
            },
            "pack": {
                "out": self.pack.out,
                "include": self.pack.include,
                "exclude": self.pack.exclude,
                "name": self.pack.name,
            },
        }

        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)

    def validate(self) -> List[str]:
        """
        Valide la configuration et retourne les erreurs.

        Returns:
            Liste des erreurs de validation
        """
        errors = []

        # Vérifier les chemins
        if not Path(self.ae.context).exists():
            errors.append(f"AE context file not found: {self.ae.context}")

        # Vérifier les budgets
        if self.budgets.ae_ms <= 0:
            errors.append("AE budget must be positive")

        if self.budgets.cegis_ms <= 0:
            errors.append("CEGIS budget must be positive")

        if self.budgets.total_ms <= 0:
            errors.append("Total budget must be positive")

        if self.budgets.ae_ms + self.budgets.cegis_ms > self.budgets.total_ms:
            errors.append("AE + CEGIS budgets exceed total budget")

        # Vérifier les sorties
        if not self.outputs.psp.endswith(".json"):
            errors.append("PSP output must be a JSON file")

        if not self.outputs.run_dir:
            errors.append("Run directory must be specified")

        # Vérifier le pack
        if not self.pack.out:
            errors.append("Pack output directory must be specified")

        if not self.pack.include:
            errors.append("Pack must include at least one pattern")

        return errors

    def get_run_id(self) -> str:
        """
        Génère un ID unique pour le run.

        Returns:
            ID du run
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        return f"2cat-{timestamp}"

    def get_pack_filename(self) -> str:
        """
        Génère le nom de fichier du pack.

        Returns:
            Nom du fichier pack
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        return f"{self.pack.name}-{timestamp}.zip"
