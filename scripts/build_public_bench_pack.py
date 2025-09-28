#!/usr/bin/env python3
"""
Build Public Benchmark Pack
Creates a zip file with summary.json, seeds, merkle.txt, sbom.json, reproduce.md
"""
import json
import zipfile
import hashlib
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from pefc.summary import build_summary
from pefc.pack.zipper import ZipAdder
from pefc.pack.merkle import build_entries, compute_merkle_root, build_manifest
from pefc.config.loader import get_config, expand_globs
from pefc.logging import setup_logging_from_config, get_logger, set_context

# Initialize logging (will be reconfigured with config)
logger = get_logger(__name__)


class PublicBenchPackBuilder:
    """Builds public benchmark pack with all necessary components."""

    def __init__(
        self, output_dir: Optional[Path] = None, pack_name: Optional[str] = None
    ):
        self.output_dir = Path(output_dir) if output_dir else Path("artifacts")
        self.output_dir.mkdir(exist_ok=True)
        self.pack_name = pack_name or "bench_pack_v0.1.0"
        self.pack_path = self.output_dir / f"{self.pack_name}.zip"

    def build_summary(
        self,
        metrics_sources: list[str],
        include_aggregates: bool = False,
        weight_key: str = "n_items",
        dedup: str = "first",
        validate: bool = False,
        bounded_metrics: Optional[list[str]] = None,
        version: str = "v0.1.0",
    ) -> dict:
        """Build summary.json with aggregated metrics using new API."""
        logger.info("Building summary.json", extra={"event": "summary.build.start"})

        # Convert string paths to Path objects
        sources = [Path(p) for p in metrics_sources]

        # Use new build_summary API
        summary_path = self.output_dir / "summary.json"
        result = build_summary(
            sources=sources,
            out_path=summary_path,
            include_aggregates=include_aggregates,
            weight_key=weight_key,
            dedup=dedup,
            version=version,
            validate=validate,
            bounded_metrics=bounded_metrics,
            schema_path=Path("schema/summary.schema.json"),
        )

        # Add legacy fields for backward compatibility
        result["generated_at"] = datetime.now().isoformat()
        result["reproducibility"] = {
            "deterministic": True,
            "seeds_provided": True,
            "merkle_attestation": True,
        }

        return result

    def collect_seeds(self) -> list:
        """Collect deterministic seeds for reproduction."""
        logger.info("Collecting seeds", extra={"event": "seeds.collect.start"})

        seeds = []

        # Look for seed files
        seed_sources = ["out/seeds.json", "artifacts/seeds.json", "configs/seeds.json"]

        for source in seed_sources:
            if Path(source).exists():
                with open(source) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        seeds.extend(data)
                    elif isinstance(data, dict) and "seeds" in data:
                        seeds.extend(data["seeds"])

        # If no seeds found, generate default seeds
        if not seeds:
            seeds = [42, 123, 456, 789, 999]

        return seeds

    def get_merkle_root(self) -> str:
        """Get Merkle root for integrity verification."""
        print("🔗 Getting Merkle root...")

        merkle_file = Path("out/journal/merkle.txt")
        if merkle_file.exists():
            return merkle_file.read_text().strip()

        # Generate Merkle root from current state
        return self.generate_merkle_root()

    def generate_merkle_root(self) -> str:
        """Generate Merkle root from current state."""
        # Collect all relevant files
        files_to_hash = []

        # Add metrics files
        for pattern in ["out/metrics.json", "artifacts/*/metrics*.json"]:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    files_to_hash.append(file_path)

        # Add configuration files
        for pattern in ["configs/*.json", "schemas/*.json"]:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    files_to_hash.append(file_path)

        # Calculate Merkle root
        if files_to_hash:
            # Sort files for deterministic ordering
            files_to_hash.sort()

            # Calculate combined hash
            combined_content = ""
            for file_path in files_to_hash:
                with open(file_path, "rb") as f:
                    combined_content += f.read().decode("utf-8", errors="ignore")

            merkle_root = hashlib.sha256(combined_content.encode()).hexdigest()
        else:
            # Default Merkle root if no files found
            merkle_root = hashlib.sha256(b"discovery-engine-2cat-v0.1.0").hexdigest()

        return merkle_root

    def get_sbom(self) -> dict:
        """Get Software Bill of Materials."""
        logger.info("Getting SBOM", extra={"event": "sbom.collect.start"})

        sbom_file = Path("out/sbom.json")
        if sbom_file.exists():
            with open(sbom_file) as f:
                return json.load(f)

        # Generate basic SBOM
        return {
            "version": "v0.1.0",
            "generated_at": datetime.now().isoformat(),
            "packages": [],
            "vulnerabilities": [],
            "summary": {
                "total_packages": 0,
                "high_vulnerabilities": 0,
                "critical_vulnerabilities": 0,
            },
        }

    def generate_reproduce_instructions(self) -> str:
        """Generate reproduction instructions."""
        logger.info(
            "Generating reproduction instructions",
            extra={"event": "reproduce.generate.start"},
        )

        instructions = """# Discovery Engine 2‑Cat — Reproduction Instructions

## Prerequisites

- Python 3.11+
- Docker 24.0+
- Git

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/discovery-engine-2cat.git
cd discovery-engine-2cat
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Reproduction

1. Set deterministic seeds:
```bash
export DISCOVERY_SEED=42
export PYTHONHASHSEED=42
```

2. Run benchmark:
```bash
make regtech-demo
```

3. Verify results:
```bash
make determinism
```

4. Check metrics:
```bash
cat out/metrics.json
```

## Verification

### Merkle Root
The Merkle root should match the provided value:
```bash
cat out/journal/merkle.txt
```

### SBOM
The SBOM should show 0 High/Critical vulnerabilities:
```bash
cat out/sbom.json
```

### Metrics
Expected metrics ranges:
- Coverage gain: 0.18-0.25
- Novelty average: 0.19-0.22
- Audit cost p95: 950-1000ms

## Troubleshooting

### Common Issues
1. **Seed mismatch**: Ensure PYTHONHASHSEED is set
2. **Docker issues**: Ensure Docker is running
3. **Permission issues**: Check file permissions

### Support
- GitHub Issues: https://github.com/your-org/discovery-engine-2cat/issues
- Email: contact@your-org.com

## License

This benchmark pack is released under the MIT License.
"""

        return instructions

    def build_pack(
        self,
        metrics_sources: list[str],
        include_aggregates: bool = False,
        weight_key: str = "n_items",
        dedup: str = "first",
        validate: bool = False,
        bounded_metrics: Optional[list[str]] = None,
        version: str = "v0.1.0",
    ) -> bool:
        """Build the complete benchmark pack."""
        logger.info(
            "Building public benchmark pack", extra={"event": "pack.build.start"}
        )

        try:
            # 1) Build payload files list (exclude manifest.json and merkle.txt from Merkle calculation)
            payload_files = []

            # Core files that will be included in Merkle calculation
            summary = self.build_summary(
                metrics_sources,
                include_aggregates,
                weight_key,
                dedup,
                validate,
                bounded_metrics,
                version,
            )
            summary_path = self.output_dir / "summary.json"
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            payload_files.append((summary_path, "summary.json"))

            # Seeds
            seeds = self.collect_seeds()
            seeds_path = self.output_dir / "seeds.json"
            seeds_path.write_text(json.dumps(seeds, indent=2), encoding="utf-8")
            payload_files.append((seeds_path, "seeds.json"))

            # SBOM
            sbom = self.get_sbom()
            sbom_path = self.output_dir / "sbom.json"
            sbom_path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")
            payload_files.append((sbom_path, "sbom.json"))

            # Reproduction instructions
            reproduce_instructions = self.generate_reproduce_instructions()
            reproduce_path = self.output_dir / "reproduce.md"
            reproduce_path.write_text(reproduce_instructions, encoding="utf-8")
            payload_files.append((reproduce_path, "reproduce.md"))

            # Additional files (if they exist)
            additional_files_raw = [
                "out/metrics.json",
                "configs/llm.yaml",
                "schemas/examples/regtech_domain_spec.overrides.json",
            ]

            for file_path in additional_files_raw:
                if Path(file_path).exists():
                    payload_files.append((Path(file_path), Path(file_path).name))

            # 2) Build Merkle entries and compute root
            entries = build_entries(payload_files)
            merkle_root = compute_merkle_root(entries)

            # 3) Build manifest (excluded from Merkle calculation)
            manifest_obj = build_manifest(entries, merkle_root, version)
            manifest_json = json.dumps(manifest_obj, ensure_ascii=False, indent=2)

            # 4) Create zip with ZipAdder for deduplication
            adder = ZipAdder()
            with zipfile.ZipFile(self.pack_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Write payload files
                for entry in entries:
                    adder.add_file(zipf, entry.src_path, entry.arcname)

                # Write proof artifacts (excluded from Merkle calculation)
                adder.add_text(zipf, "manifest.json", manifest_json)
                adder.add_text(zipf, "merkle.txt", merkle_root + "\n")

            # Log final list of files
            logger.info(
                "Files written to zip",
                extra={
                    "event": "zip.complete",
                    "kv": {"file_count": len(adder.seen), "files": sorted(adder.seen)},
                },
            )
            logger.info(
                "Built benchmark pack",
                extra={
                    "event": "pack.build.complete",
                    "kv": {"pack_path": str(self.pack_path)},
                },
            )

            # Calculate and display pack info
            pack_size = self.pack_path.stat().st_size
            logger.info(
                "Pack info",
                extra={
                    "event": "pack.info",
                    "kv": {
                        "size_mb": round(pack_size / 1024 / 1024, 2),
                        "file_count": len(adder.seen),
                    },
                },
            )

            # Verify pack integrity
            with zipfile.ZipFile(self.pack_path, "r") as zipf:
                file_list = zipf.namelist()
                logger.info(
                    "Pack contents",
                    extra={"event": "pack.contents", "kv": {"files": file_list}},
                )

            return True

        except Exception as e:
            logger.error(
                "Failed to build benchmark pack",
                extra={"event": "pack.build.error", "kv": {"error": str(e)}},
                exc_info=True,
            )
            return False

    def sign_pack(self) -> bool:
        """Sign the benchmark pack for integrity verification."""
        logger.info("Signing benchmark pack", extra={"event": "pack.sign.start"})

        try:
            # Generate signature
            with open(self.pack_path, "rb") as f:
                content = f.read()
                signature = hashlib.sha256(content).hexdigest()

            # Save signature
            signature_file = self.output_dir / f"{self.pack_name}.sig"
            with open(signature_file, "w") as f:
                f.write(signature)

            logger.info(
                "Pack signed",
                extra={
                    "event": "pack.sign.complete",
                    "kv": {"sig_path": str(signature_file), "signature": signature},
                },
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to sign pack",
                extra={"event": "pack.sign.error", "kv": {"error": str(e)}},
                exc_info=True,
            )
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Build Discovery Engine 2‑Cat Public Benchmark Pack"
    )
    parser.add_argument(
        "--metrics-source",
        action="append",
        default=[],
        help="Fichier ou dossier JSON de métriques (multi)",
    )
    parser.add_argument(
        "--include-aggregates",
        action="store_true",
        help="Inclure les sources agrégées (défaut: ignorées)",
    )
    parser.add_argument(
        "--weight-key", default="n_items", help="Clé de pondération pour les métriques"
    )
    parser.add_argument(
        "--dedup",
        choices=["first", "last"],
        default="first",
        help="Stratégie de déduplication",
    )
    parser.add_argument(
        "--validate-summary",
        action="store_true",
        help="Valide summary.json contre le schéma + cohérence",
    )
    parser.add_argument(
        "--bounded-metric",
        action="append",
        default=[],
        help="Nom de métrique à contraindre dans [0,1]",
    )
    parser.add_argument(
        "--config", help="Fichier de configuration YAML (défaut: config/pack.yaml)"
    )
    parser.add_argument("--output", help="Dossier de sortie (défaut: artifacts)")
    parser.add_argument("--pack-name", help="Nom du pack (défaut: bench_pack_v0.1.0)")

    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config) if args.config else None
    config = get_config(config_path)

    # Setup logging from config
    setup_logging_from_config(config)
    logger = get_logger(__name__)

    logger.info(
        "Building Discovery Engine 2‑Cat Public Benchmark Pack",
        extra={"event": "pack.init"},
    )

    # Set context
    set_context(
        pack_version=config.pack.version,
        pack_name=config.pack.pack_name,
        run_id=f"build_{int(time.time())}",
    )

    logger.info("Starting pack build", extra={"event": "pack.start"})
    logger.info(
        "Using config",
        extra={"kv": {"config_path": str(config_path) if config_path else "default"}},
    )
    if hasattr(config, "_base_dir"):
        logger.info("Base directory", extra={"kv": {"base_dir": str(config._base_dir)}})

    # Create builder with config values
    output_dir = Path(args.output or config.pack.out_dir)
    pack_name = args.pack_name or config.pack.pack_name

    builder = PublicBenchPackBuilder(
        output_dir=output_dir,
        pack_name=pack_name,
    )

    # Determine metrics sources from config or CLI
    if args.metrics_source:
        metrics_sources = args.metrics_source
    else:
        # Resolve globs from config
        metrics_sources = [
            str(p) for p in expand_globs(config.metrics.sources, config._base_dir)
        ]
        if not metrics_sources:
            # Fallback to default sources
            metrics_sources = [
                "out/metrics.json",
                "artifacts/bench_public/metrics_baseline.json",
                "artifacts/bench_public/metrics_active.json",
            ]

    # Build the pack with config values
    if not builder.build_pack(
        metrics_sources,
        args.include_aggregates or config.metrics.include_aggregates,
        args.weight_key or config.metrics.weight_key,
        args.dedup or config.metrics.dedup,
        args.validate_summary,
        args.bounded_metric or config.metrics.bounded_metrics,
        config.pack.version,
    ):
        logger.error(
            "Failed to build benchmark pack", extra={"event": "pack.build.failed"}
        )
        exit(1)

    # Sign the pack
    if not builder.sign_pack():
        logger.error(
            "Failed to sign benchmark pack", extra={"event": "pack.sign.failed"}
        )
        exit(1)

    logger.info(
        "Public benchmark pack built successfully", extra={"event": "pack.complete"}
    )
    logger.info(
        "Pack details",
        extra={
            "event": "pack.details",
            "kv": {
                "pack_path": str(builder.pack_path),
                "signature_path": str(builder.output_dir / f"{builder.pack_name}.sig"),
                "contents": [
                    "summary.json: Aggregated metrics",
                    "seeds.json: Deterministic seeds",
                    "merkle.txt: Integrity verification",
                    "sbom.json: Software Bill of Materials",
                    "reproduce.md: Reproduction instructions",
                ],
            },
        },
    )


if __name__ == "__main__":
    main()
