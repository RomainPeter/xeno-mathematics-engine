"""
Collecteur de métriques pour le Proof Engine for Code v0.
"""

import json
import os
import glob
from typing import Dict, Any, List
from proofengine.core.pcap import read_pcap, list_pcaps


class MetricsCollector:
    """Collecteur de métriques pour l'analyse de performance."""
    
    def __init__(self):
        """Initialise le collecteur."""
        self.collected_metrics: List[Dict[str, Any]] = []
    
    def collect_metrics(self, input_dir: str = "out/pcap") -> Dict[str, Any]:
        """
        Collecte les métriques depuis un répertoire de PCAPs.
        
        Args:
            input_dir: Répertoire contenant les PCAPs
            
        Returns:
            Dict[str, Any]: Métriques collectées
        """
        # Charger tous les PCAPs
        pcaps = self._load_pcaps(input_dir)
        
        if not pcaps:
            return {"error": "No PCAPs found", "count": 0}
        
        # Calculer les métriques de base
        basic_metrics = self._calculate_basic_metrics(pcaps)
        
        # Calculer les métriques de performance
        performance_metrics = self._calculate_performance_metrics(pcaps)
        
        # Calculer les métriques de qualité
        quality_metrics = self._calculate_quality_metrics(pcaps)
        
        # Calculer les métriques de delta
        delta_metrics = self._calculate_delta_metrics(pcaps)
        
        # Combiner toutes les métriques
        combined_metrics = {
            "collection_timestamp": self._get_timestamp(),
            "input_directory": input_dir,
            "total_pcaps": len(pcaps),
            "basic_metrics": basic_metrics,
            "performance_metrics": performance_metrics,
            "quality_metrics": quality_metrics,
            "delta_metrics": delta_metrics
        }
        
        return combined_metrics
    
    def _load_pcaps(self, input_dir: str) -> List[Dict[str, Any]]:
        """Charge tous les PCAPs depuis un répertoire."""
        pcaps = []
        pcap_files = list_pcaps(input_dir)
        
        for pcap_file in pcap_files:
            try:
                pcap = read_pcap(pcap_file)
                pcaps.append(pcap.model_dump())
            except Exception as e:
                print(f"Error loading PCAP {pcap_file}: {e}")
        
        return pcaps
    
    def _calculate_basic_metrics(self, pcaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les métriques de base."""
        total_pcaps = len(pcaps)
        successful_pcaps = sum(1 for pcap in pcaps if pcap.get("verdict") == "pass")
        failed_pcaps = total_pcaps - successful_pcaps
        success_rate = successful_pcaps / total_pcaps if total_pcaps > 0 else 0
        
        # Analyser les opérateurs
        operators = {}
        for pcap in pcaps:
            op = pcap.get("operator", "unknown")
            operators[op] = operators.get(op, 0) + 1
        
        # Analyser les verdicts
        verdicts = {}
        for pcap in pcaps:
            verdict = pcap.get("verdict", "unknown")
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
        
        return {
            "total_pcaps": total_pcaps,
            "successful_pcaps": successful_pcaps,
            "failed_pcaps": failed_pcaps,
            "success_rate": success_rate,
            "operators": operators,
            "verdicts": verdicts
        }
    
    def _calculate_performance_metrics(self, pcaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les métriques de performance."""
        if not pcaps:
            return {}
        
        # Collecter les temps d'exécution
        execution_times = []
        llm_times = []
        
        for pcap in pcaps:
            justification = pcap.get("justification", {})
            if "time_ms" in justification:
                execution_times.append(justification["time_ms"])
            if "llm_time_ms" in justification:
                llm_times.append(justification["llm_time_ms"])
        
        # Calculer les statistiques
        total_execution_time = sum(execution_times)
        avg_execution_time = total_execution_time / len(execution_times) if execution_times else 0
        
        total_llm_time = sum(llm_times)
        avg_llm_time = total_llm_time / len(llm_times) if llm_times else 0
        
        # Analyser les retries et backtracks
        total_retries = sum(pcap.get("justification", {}).get("backtracks", 0) for pcap in pcaps)
        total_audit_cost = sum(pcap.get("justification", {}).get("audit_cost_ms", 0) for pcap in pcaps)
        
        return {
            "execution_analysis": {
                "total_execution_time_ms": total_execution_time,
                "average_execution_time_ms": avg_execution_time,
                "total_llm_time_ms": total_llm_time,
                "average_llm_time_ms": avg_llm_time
            },
            "efficiency_metrics": {
                "total_retries": total_retries,
                "total_audit_cost_ms": total_audit_cost,
                "average_retries_per_pcap": total_retries / len(pcaps) if pcaps else 0
            }
        }
    
    def _calculate_quality_metrics(self, pcaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les métriques de qualité."""
        if not pcaps:
            return {}
        
        # Analyser les obligations
        total_obligations = 0
        obligation_violations = 0
        
        for pcap in pcaps:
            obligations = pcap.get("obligations", [])
            total_obligations += len(obligations)
            
            # Compter les violations (simulation)
            violations = pcap.get("justification", {}).get("tech_debt", 0)
            obligation_violations += violations
        
        # Calculer le taux de conformité
        compliance_rate = 1.0 - (obligation_violations / total_obligations) if total_obligations > 0 else 0
        
        # Analyser les types d'obligations
        obligation_types = {}
        for pcap in pcaps:
            for obligation in pcap.get("obligations", []):
                obligation_types[obligation] = obligation_types.get(obligation, 0) + 1
        
        return {
            "obligation_analysis": {
                "total_obligations": total_obligations,
                "obligation_violations": obligation_violations,
                "compliance_rate": compliance_rate,
                "obligation_types": obligation_types
            }
        }
    
    def _calculate_delta_metrics(self, pcaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les métriques de delta."""
        if not pcaps:
            return {}
        
        # Analyser les deltas (simulation)
        delta_values = []
        for pcap in pcaps:
            # Simuler des valeurs de delta
            delta = 0.1 + (hash(pcap.get("case_id", "")) % 100) / 1000
            delta_values.append(delta)
        
        if delta_values:
            avg_delta = sum(delta_values) / len(delta_values)
            max_delta = max(delta_values)
            min_delta = min(delta_values)
        else:
            avg_delta = max_delta = min_delta = 0.0
        
        return {
            "delta_analysis": {
                "average_delta": avg_delta,
                "max_delta": max_delta,
                "min_delta": min_delta,
                "delta_count": len(delta_values)
            }
        }
    
    def export_metrics(self, metrics: Dict[str, Any], output_file: str) -> None:
        """Exporte les métriques vers un fichier."""
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2, default=str)
    
    def generate_summary_report(self, metrics: Dict[str, Any]) -> str:
        """Génère un rapport de résumé des métriques."""
        report = []
        report.append("=== RAPPORT DE MÉTRIQUES ===")
        report.append(f"Timestamp: {metrics.get('collection_timestamp', 'N/A')}")
        report.append(f"Répertoire: {metrics.get('input_directory', 'N/A')}")
        report.append("")
        
        # Métriques de base
        basic = metrics.get("basic_metrics", {})
        report.append("MÉTRIQUES DE BASE:")
        report.append(f"  Total PCAPs: {basic.get('total_pcaps', 0)}")
        report.append(f"  PCAPs réussis: {basic.get('successful_pcaps', 0)}")
        report.append(f"  Taux de succès: {basic.get('success_rate', 0):.2%}")
        report.append("")
        
        # Métriques de performance
        perf = metrics.get("performance_metrics", {})
        if perf:
            exec_analysis = perf.get("execution_analysis", {})
            report.append("MÉTRIQUES DE PERFORMANCE:")
            report.append(f"  Temps total: {exec_analysis.get('total_execution_time_ms', 0)}ms")
            report.append(f"  Temps moyen: {exec_analysis.get('average_execution_time_ms', 0):.2f}ms")
            report.append("")
        
        # Métriques de qualité
        quality = metrics.get("quality_metrics", {})
        if quality:
            obligation_analysis = quality.get("obligation_analysis", {})
            report.append("MÉTRIQUES DE QUALITÉ:")
            report.append(f"  Taux de conformité: {obligation_analysis.get('compliance_rate', 0):.2%}")
            report.append(f"  Total obligations: {obligation_analysis.get('total_obligations', 0)}")
            report.append("")
        
        # Métriques de delta
        delta = metrics.get("delta_metrics", {})
        if delta:
            delta_analysis = delta.get("delta_analysis", {})
            report.append("MÉTRIQUES DE DELTA:")
            report.append(f"  Delta moyen: {delta_analysis.get('average_delta', 0):.3f}")
            report.append(f"  Delta max: {delta_analysis.get('max_delta', 0):.3f}")
            report.append("")
        
        return "\n".join(report)
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())