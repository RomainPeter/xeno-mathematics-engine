"""
Interface en ligne de commande pour le Proof Engine for Code v0.
Gère les commandes: plan-run, verify, audit-pack, metrics.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from metrics.collect import MetricsCollector
from planner.meta import MetacognitivePlanner
from proofengine.core.schemas import PCAP, XState
from proofengine.core.state import create_initial_state
from runner.verifier import Verifier
from scripts.audit_pack import AuditPackGenerator


class ProofEngineCLI:
    """Interface en ligne de commande pour le Proof Engine."""

    def __init__(self):
        """Initialise le CLI."""
        self.parser = self._create_parser()
        self.planner = MetacognitivePlanner()
        self.verifier = Verifier()
        self.metrics_collector = MetricsCollector()
        self.audit_pack_generator = AuditPackGenerator()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Crée le parser d'arguments."""
        parser = argparse.ArgumentParser(
            description="Proof Engine for Code v0 - CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples d'utilisation:
  python -m runner.cli plan-run --goal "sanitize input" --case sanitize_input
  python -m runner.cli verify --pcap out/pcap/action_001.json
  python -m runner.cli audit-pack --output out/audit/
  python -m runner.cli metrics --input out/pcap/ --output out/metrics/
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

        # Commande plan-run
        plan_parser = subparsers.add_parser("plan-run", help="Exécuter un plan")
        plan_parser.add_argument("--goal", required=True, help="Objectif à atteindre")
        plan_parser.add_argument("--case", help="Cas de test à utiliser")
        plan_parser.add_argument("--seed", type=int, help="Graine pour la reproductibilité")
        plan_parser.add_argument("--budget", type=int, default=30000, help="Budget temps en ms")
        plan_parser.add_argument("--output", default="out/", help="Répertoire de sortie")

        # Commande verify
        verify_parser = subparsers.add_parser("verify", help="Vérifier un PCAP")
        verify_parser.add_argument("--pcap", required=True, help="Fichier PCAP à vérifier")
        verify_parser.add_argument("--output", help="Fichier de sortie pour le rapport")

        # Commande audit-pack
        audit_parser = subparsers.add_parser("audit-pack", help="Générer un pack d'audit")
        audit_parser.add_argument("--input", default="out/pcap/", help="Répertoire des PCAPs")
        audit_parser.add_argument("--output", default="out/audit/", help="Répertoire de sortie")
        audit_parser.add_argument("--sign", action="store_true", help="Signer le pack d'audit")

        # Commande metrics
        metrics_parser = subparsers.add_parser("metrics", help="Générer des métriques")
        metrics_parser.add_argument("--input", default="out/pcap/", help="Répertoire des PCAPs")
        metrics_parser.add_argument("--output", default="out/metrics/", help="Répertoire de sortie")
        metrics_parser.add_argument(
            "--format",
            choices=["json", "markdown"],
            default="json",
            help="Format de sortie",
        )

        return parser

    def run(self, args: List[str] = None) -> int:
        """Exécute le CLI avec les arguments donnés."""
        if args is None:
            args = sys.argv[1:]

        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return 1

        try:
            if parsed_args.command == "plan-run":
                return self._run_plan(parsed_args)
            elif parsed_args.command == "verify":
                return self._run_verify(parsed_args)
            elif parsed_args.command == "audit-pack":
                return self._run_audit_pack(parsed_args)
            elif parsed_args.command == "metrics":
                return self._run_metrics(parsed_args)
            else:
                print(f"Commande inconnue: {parsed_args.command}")
                return 1

        except Exception as e:
            print(f"Erreur: {str(e)}")
            return 1

    def _run_plan(self, args: argparse.Namespace) -> int:
        """Exécute la commande plan-run."""
        print(f"🎯 Exécution du plan pour l'objectif: {args.goal}")

        # Créer l'état initial
        initial_state = self._create_initial_state(args.case)

        # Configurer le planificateur
        config = {"seed": args.seed, "budget": {"time_limit_ms": args.budget}}
        self.planner = MetacognitivePlanner(config)

        # Exécuter le plan
        result = self.planner.execute_plan(initial_state, args.goal, config.get("budget"))

        # Sauvegarder les résultats
        self._save_plan_results(result, args.output)

        if result["success"]:
            print("✅ Plan exécuté avec succès")
            return 0
        else:
            print("❌ Plan échoué")
            return 1

    def _run_verify(self, args: argparse.Namespace) -> int:
        """Exécute la commande verify."""
        print(f"🔍 Vérification du PCAP: {args.pcap}")

        # Charger le PCAP
        try:
            with open(args.pcap, "r") as f:
                pcap_data = json.load(f)
            pcap = PCAP(**pcap_data)
        except Exception as e:
            print(f"Erreur lors du chargement du PCAP: {e}")
            return 1

        # Vérifier le PCAP
        verification_result = self.verifier.replay(pcap)

        # Sauvegarder le rapport
        if args.output:
            with open(args.output, "w") as f:
                json.dump(verification_result, f, indent=2, default=str)

        # Afficher le résultat
        verdict = verification_result.get("verdict", "unknown")
        if verdict == "pass":
            print("✅ PCAP vérifié avec succès")
            return 0
        else:
            print(f"❌ PCAP échoué: {verdict}")
            return 1

    def _run_audit_pack(self, args: argparse.Namespace) -> int:
        """Exécute la commande audit-pack."""
        print(f"📦 Génération du pack d'audit depuis: {args.input}")

        # Générer le pack d'audit
        audit_pack = self.audit_pack_generator.generate_audit_pack(args.input, args.sign)

        # Sauvegarder le pack
        os.makedirs(args.output, exist_ok=True)
        output_file = os.path.join(args.output, "audit_pack.json")

        with open(output_file, "w") as f:
            f.write(audit_pack.to_json())

        print(f"✅ Pack d'audit généré: {output_file}")
        return 0

    def _run_metrics(self, args: argparse.Namespace) -> int:
        """Exécute la commande metrics."""
        print(f"📊 Génération des métriques depuis: {args.input}")

        # Collecter les métriques
        metrics = self.metrics_collector.collect_metrics(args.input)

        # Sauvegarder les métriques
        os.makedirs(args.output, exist_ok=True)

        if args.format == "json":
            output_file = os.path.join(args.output, "metrics.json")
            with open(output_file, "w") as f:
                json.dump(metrics, f, indent=2, default=str)
        else:  # markdown
            output_file = os.path.join(args.output, "metrics.md")
            with open(output_file, "w") as f:
                f.write(self._format_metrics_markdown(metrics))

        print(f"✅ Métriques générées: {output_file}")
        return 0

    def _create_initial_state(self, case: str = None) -> XState:
        """Crée l'état initial basé sur le cas."""
        if case == "sanitize_input":
            return create_initial_state(
                hypotheses={"input_sanitization_required"},
                evidences={"user_input_present"},
                obligations=[
                    {"policy": "pytest", "test_file": "test_sanitize.py"},
                    {"policy": "ruff", "max_issues": 0},
                    {
                        "policy": "forbidden_imports",
                        "forbidden_imports": ["eval", "exec"],
                    },
                ],
                artifacts=["sanitize_input.py"],
                sigma={"case": "sanitize_input", "timestamp": self._get_timestamp()},
            )
        elif case == "rate_limiter":
            return create_initial_state(
                hypotheses={"rate_limiting_required"},
                evidences={"api_endpoints_present"},
                obligations=[
                    {"policy": "pytest", "test_file": "test_rate_limit.py"},
                    {"policy": "mypy", "strict": True},
                    {"policy": "docstring", "required": True},
                ],
                artifacts=["rate_limiter.py"],
                sigma={"case": "rate_limiter", "timestamp": self._get_timestamp()},
            )
        elif case == "pure_fn":
            return create_initial_state(
                hypotheses={"pure_function_required"},
                evidences={"functional_programming_style"},
                obligations=[
                    {"policy": "pure_function", "no_side_effects": True},
                    {"policy": "type_hints", "required": True},
                    {"policy": "cyclomatic_complexity", "max_complexity": 5},
                ],
                artifacts=["pure_function.py"],
                sigma={"case": "pure_fn", "timestamp": self._get_timestamp()},
            )
        else:
            # État par défaut
            return create_initial_state(
                hypotheses={"general_improvement"},
                evidences={"code_present"},
                obligations=[
                    {"policy": "pytest", "test_file": "test_general.py"},
                    {"policy": "ruff", "max_issues": 0},
                ],
                artifacts=["general.py"],
                sigma={"case": "general", "timestamp": self._get_timestamp()},
            )

    def _save_plan_results(self, result: Dict[str, Any], output_dir: str) -> None:
        """Sauvegarde les résultats du plan."""
        os.makedirs(output_dir, exist_ok=True)

        # Sauvegarder l'état final
        if "final_state" in result:
            state_file = os.path.join(output_dir, "final_state.json")
            with open(state_file, "w") as f:
                f.write(result["final_state"].to_json())

        # Sauvegarder l'historique d'exécution
        if "execution_history" in result:
            history_file = os.path.join(output_dir, "execution_history.json")
            with open(history_file, "w") as f:
                json.dump(result["execution_history"], f, indent=2, default=str)

        # Sauvegarder les métriques
        if "metrics" in result:
            metrics_file = os.path.join(output_dir, "execution_metrics.json")
            with open(metrics_file, "w") as f:
                json.dump(result["metrics"], f, indent=2, default=str)

    def _format_metrics_markdown(self, metrics: Dict[str, Any]) -> str:
        """Formate les métriques en Markdown."""
        md = "# Métriques du Proof Engine\n\n"

        if "total_pcaps" in metrics:
            md += "## Résumé\n"
            md += f"- **Total PCAPs**: {metrics['total_pcaps']}\n"
            md += f"- **PCAPs réussis**: {metrics.get('successful_pcaps', 0)}\n"
            md += f"- **Taux de succès**: {metrics.get('success_rate', 0):.2%}\n\n"

        if "delta_analysis" in metrics:
            md += "## Analyse Delta\n"
            md += f"- **Delta moyen**: {metrics['delta_analysis'].get('average_delta', 0):.3f}\n"
            md += f"- **Delta max**: {metrics['delta_analysis'].get('max_delta', 0):.3f}\n\n"

        if "cost_analysis" in metrics:
            md += "## Analyse des Coûts\n"
            md += f"- **Coût moyen**: {metrics['cost_analysis'].get('average_cost', 0):.2f}\n"
            md += f"- **Temps moyen**: {metrics['cost_analysis'].get('average_time_ms', 0)}ms\n\n"

        return md

    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        from datetime import datetime

        return datetime.now().isoformat()


def main():
    """Point d'entrée principal du CLI."""
    cli = ProofEngineCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
