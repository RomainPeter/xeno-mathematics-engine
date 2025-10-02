"""
Générateur de rapports pour le Proof Engine for Code v0.
"""

import json
import os
from typing import Any, Dict

from .collect import MetricsCollector


class ReportGenerator:
    """Générateur de rapports de métriques."""

    def __init__(self):
        """Initialise le générateur de rapports."""
        self.collector = MetricsCollector()

    def generate_markdown_report(self, metrics: Dict[str, Any]) -> str:
        """
        Génère un rapport en format Markdown.

        Args:
            metrics: Métriques à rapporter

        Returns:
            str: Rapport en Markdown
        """
        md = []
        md.append("# Rapport de Métriques - Proof Engine v0")
        md.append("")
        md.append(f"**Timestamp:** {metrics.get('collection_timestamp', 'N/A')}")
        md.append(f"**Répertoire:** {metrics.get('input_directory', 'N/A')}")
        md.append("")

        # Métriques de base
        basic = metrics.get("basic_metrics", {})
        md.append("## Métriques de Base")
        md.append("")
        md.append(f"- **Total PCAPs:** {basic.get('total_pcaps', 0)}")
        md.append(f"- **PCAPs réussis:** {basic.get('successful_pcaps', 0)}")
        md.append(f"- **PCAPs échoués:** {basic.get('failed_pcaps', 0)}")
        md.append(f"- **Taux de succès:** {basic.get('success_rate', 0):.2%}")
        md.append("")

        # Opérateurs
        operators = basic.get("operators", {})
        if operators:
            md.append("### Répartition par Opérateur")
            md.append("")
            for operator, count in operators.items():
                md.append(f"- **{operator}:** {count}")
            md.append("")

        # Verdicts
        verdicts = basic.get("verdicts", {})
        if verdicts:
            md.append("### Répartition par Verdict")
            md.append("")
            for verdict, count in verdicts.items():
                md.append(f"- **{verdict}:** {count}")
            md.append("")

        # Métriques de performance
        perf = metrics.get("performance_metrics", {})
        if perf:
            md.append("## Métriques de Performance")
            md.append("")

            exec_analysis = perf.get("execution_analysis", {})
            md.append("### Temps d'Exécution")
            md.append("")
            md.append(f"- **Temps total:** {exec_analysis.get('total_execution_time_ms', 0)}ms")
            md.append(
                f"- **Temps moyen:** {exec_analysis.get('average_execution_time_ms', 0):.2f}ms"
            )
            md.append(f"- **Temps LLM total:** {exec_analysis.get('total_llm_time_ms', 0)}ms")
            md.append(f"- **Temps LLM moyen:** {exec_analysis.get('average_llm_time_ms', 0):.2f}ms")
            md.append("")

            efficiency = perf.get("efficiency_metrics", {})
            md.append("### Métriques d'Efficacité")
            md.append("")
            md.append(f"- **Total retries:** {efficiency.get('total_retries', 0)}")
            md.append(f"- **Coût d'audit total:** {efficiency.get('total_audit_cost_ms', 0)}ms")
            md.append(
                f"- **Retries moyens par PCAP:** {efficiency.get('average_retries_per_pcap', 0):.2f}"
            )
            md.append("")

        # Métriques de qualité
        quality = metrics.get("quality_metrics", {})
        if quality:
            md.append("## Métriques de Qualité")
            md.append("")

            obligation_analysis = quality.get("obligation_analysis", {})
            md.append("### Analyse des Obligations")
            md.append("")
            md.append(f"- **Total obligations:** {obligation_analysis.get('total_obligations', 0)}")
            md.append(
                f"- **Violations d'obligations:** {obligation_analysis.get('obligation_violations', 0)}"
            )
            md.append(
                f"- **Taux de conformité:** {obligation_analysis.get('compliance_rate', 0):.2%}"
            )
            md.append("")

            obligation_types = obligation_analysis.get("obligation_types", {})
            if obligation_types:
                md.append("### Types d'Obligations")
                md.append("")
                for obligation, count in obligation_types.items():
                    md.append(f"- **{obligation}:** {count}")
                md.append("")

        # Métriques de delta
        delta = metrics.get("delta_metrics", {})
        if delta:
            md.append("## Métriques de Delta")
            md.append("")

            delta_analysis = delta.get("delta_analysis", {})
            md.append("### Analyse de l'Écart")
            md.append("")
            md.append(f"- **Delta moyen:** {delta_analysis.get('average_delta', 0):.3f}")
            md.append(f"- **Delta maximum:** {delta_analysis.get('max_delta', 0):.3f}")
            md.append(f"- **Delta minimum:** {delta_analysis.get('min_delta', 0):.3f}")
            md.append(f"- **Nombre de deltas:** {delta_analysis.get('delta_count', 0)}")
            md.append("")

        # Recommandations
        md.append("## Recommandations")
        md.append("")

        success_rate = basic.get("success_rate", 0)
        if success_rate < 0.5:
            md.append(
                "- ⚠️ **Taux de succès faible:** Considérer l'amélioration de la planification"
            )
        elif success_rate > 0.8:
            md.append("- ✅ **Taux de succès élevé:** Le système fonctionne bien")

        avg_time = perf.get("execution_analysis", {}).get("average_execution_time_ms", 0)
        if avg_time > 10000:
            md.append("- ⚠️ **Temps d'exécution élevé:** Optimiser les performances")

        compliance_rate = quality.get("obligation_analysis", {}).get("compliance_rate", 0)
        if compliance_rate < 0.7:
            md.append("- ⚠️ **Conformité faible:** Améliorer la satisfaction des obligations")

        md.append("")
        md.append("---")
        md.append("*Rapport généré automatiquement par Proof Engine v0*")

        return "\n".join(md)

    def generate_json_report(self, metrics: Dict[str, Any]) -> str:
        """
        Génère un rapport en format JSON.

        Args:
            metrics: Métriques à rapporter

        Returns:
            str: Rapport en JSON
        """
        return json.dumps(metrics, indent=2, default=str)

    def save_report(
        self, metrics: Dict[str, Any], output_dir: str, format: str = "markdown"
    ) -> str:
        """
        Sauvegarde un rapport dans un fichier.

        Args:
            metrics: Métriques à rapporter
            output_dir: Répertoire de sortie
            format: Format du rapport ("markdown" ou "json")

        Returns:
            str: Chemin du fichier créé
        """
        os.makedirs(output_dir, exist_ok=True)

        if format == "markdown":
            content = self.generate_markdown_report(metrics)
            filename = "metrics_report.md"
        elif format == "json":
            content = self.generate_json_report(metrics)
            filename = "metrics_report.json"
        else:
            raise ValueError(f"Format non supporté: {format}")

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def generate_comparison_report(self, metrics1: Dict[str, Any], metrics2: Dict[str, Any]) -> str:
        """
        Génère un rapport de comparaison entre deux ensembles de métriques.

        Args:
            metrics1: Premières métriques
            metrics2: Deuxièmes métriques

        Returns:
            str: Rapport de comparaison
        """
        md = []
        md.append("# Rapport de Comparaison - Proof Engine v0")
        md.append("")

        # Comparaison des métriques de base
        basic1 = metrics1.get("basic_metrics", {})
        basic2 = metrics2.get("basic_metrics", {})

        md.append("## Comparaison des Métriques de Base")
        md.append("")
        md.append("| Métrique | Avant | Après | Différence |")
        md.append("|----------|-------|-------|------------|")

        total1 = basic1.get("total_pcaps", 0)
        total2 = basic2.get("total_pcaps", 0)
        md.append(f"| Total PCAPs | {total1} | {total2} | {total2 - total1:+d} |")

        success1 = basic1.get("success_rate", 0)
        success2 = basic2.get("success_rate", 0)
        md.append(
            f"| Taux de succès | {success1:.2%} | {success2:.2%} | {success2 - success1:+.2%} |"
        )

        md.append("")

        # Comparaison des performances
        perf1 = metrics1.get("performance_metrics", {})
        perf2 = metrics2.get("performance_metrics", {})

        if perf1 and perf2:
            md.append("## Comparaison des Performances")
            md.append("")

            exec1 = perf1.get("execution_analysis", {})
            exec2 = perf2.get("execution_analysis", {})

            time1 = exec1.get("average_execution_time_ms", 0)
            time2 = exec2.get("average_execution_time_ms", 0)
            md.append(
                f"**Temps d'exécution moyen:** {time1:.2f}ms → {time2:.2f}ms ({time2 - time1:+.2f}ms)"
            )

            llm1 = exec1.get("average_llm_time_ms", 0)
            llm2 = exec2.get("average_llm_time_ms", 0)
            md.append(f"**Temps LLM moyen:** {llm1:.2f}ms → {llm2:.2f}ms ({llm2 - llm1:+.2f}ms)")

            md.append("")

        # Recommandations basées sur la comparaison
        md.append("## Recommandations")
        md.append("")

        if success2 > success1:
            md.append("- ✅ **Amélioration du taux de succès:** Continuer dans cette direction")
        elif success2 < success1:
            md.append("- ⚠️ **Dégradation du taux de succès:** Analyser les causes")

        if time2 < time1:
            md.append("- ✅ **Amélioration des performances:** Optimisations efficaces")
        elif time2 > time1:
            md.append("- ⚠️ **Dégradation des performances:** Identifier les goulots d'étranglement")

        md.append("")
        md.append("---")
        md.append("*Rapport de comparaison généré automatiquement*")

        return "\n".join(md)
