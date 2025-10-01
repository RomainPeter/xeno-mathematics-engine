"""
Vérifieur déterministe pour le Proof Engine for Code v0.
Rejoue les PCAPs et vérifie l'intégrité des preuves.
"""

from typing import Any, Dict, List

from proofengine.core.hashing import hash_pcap
from proofengine.core.schemas import PCAP, Proof

from runner.deterministic import DeterministicRunner


class Verifier:
    """Vérifieur déterministe pour les PCAPs."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialise le vérifieur avec une configuration."""
        self.config = config or {}
        self.runner = DeterministicRunner(config)
        self.verification_history: List[Dict[str, Any]] = []

    def replay(self, pcap: PCAP) -> Dict[str, Any]:
        """
        Rejoue un PCAP et vérifie son intégrité.
        Retourne un verdict de vérification.
        """
        start_time = self._get_time_ms()

        try:
            # Vérifier l'intégrité du PCAP
            integrity_check = self._verify_pcap_integrity(pcap)

            # Rejouer les preuves
            replay_results = self._replay_proofs(pcap)

            # Vérifier la cohérence des coûts
            cost_consistency = self._verify_cost_consistency(pcap)

            # Calculer le verdict final
            verdict = self._calculate_verdict(integrity_check, replay_results, cost_consistency)

            # Enregistrer la vérification
            verification_record = {
                "pcap_hash": pcap.pcap_hash,
                "verdict": verdict,
                "integrity_check": integrity_check,
                "replay_results": replay_results,
                "cost_consistency": cost_consistency,
                "verification_time_ms": self._get_time_ms() - start_time,
                "timestamp": self._get_timestamp(),
            }

            self.verification_history.append(verification_record)

            return verification_record

        except Exception as e:
            error_record = {
                "pcap_hash": pcap.pcap_hash,
                "verdict": "error",
                "error": str(e),
                "verification_time_ms": self._get_time_ms() - start_time,
                "timestamp": self._get_timestamp(),
            }

            self.verification_history.append(error_record)
            return error_record

    def _verify_pcap_integrity(self, pcap: PCAP) -> Dict[str, Any]:
        """Vérifie l'intégrité d'un PCAP."""
        # Vérifier le hash du PCAP
        computed_hash = hash_pcap(pcap)
        hash_valid = computed_hash == pcap.pcap_hash

        # Vérifier la cohérence des timestamps
        timestamp_valid = pcap.ts is not None

        # Vérifier la présence des champs obligatoires
        required_fields = ["action", "pre_hash", "obligations", "proofs", "verdict"]
        fields_valid = all(hasattr(pcap, field) for field in required_fields)

        return {
            "hash_valid": hash_valid,
            "timestamp_valid": timestamp_valid,
            "fields_valid": fields_valid,
            "computed_hash": computed_hash,
            "expected_hash": pcap.pcap_hash,
        }

    def _replay_proofs(self, pcap: PCAP) -> Dict[str, Any]:
        """Rejoue les preuves d'un PCAP."""
        replay_results = []

        for proof in pcap.proofs:
            # Rejouer la preuve individuellement
            replay_result = self._replay_single_proof(proof, pcap)
            replay_results.append(replay_result)

        # Calculer les statistiques de replay
        total_proofs = len(pcap.proofs)
        successful_replays = sum(1 for r in replay_results if r.get("success", False))
        success_rate = successful_replays / total_proofs if total_proofs > 0 else 0

        return {
            "replay_results": replay_results,
            "total_proofs": total_proofs,
            "successful_replays": successful_replays,
            "success_rate": success_rate,
        }

    def _replay_single_proof(self, proof: Proof, pcap: PCAP) -> Dict[str, Any]:
        """Rejoue une preuve individuelle."""
        try:
            # Créer un contexte de rejeu basé sur le PCAP
            context = {
                "action": pcap.action,
                "obligations": pcap.obligations,
                "toolchain": pcap.toolchain,
            }

            # Rejouer la preuve avec le runner déterministe
            replayed_proofs, cost = self.runner.run_and_prove(
                context, [{"policy": proof.name}], seed=pcap.toolchain.get("seed")
            )

            # Comparer avec la preuve originale
            if replayed_proofs:
                replayed_proof = replayed_proofs[0]
                success = (
                    replayed_proof.passed == proof.passed and replayed_proof.name == proof.name
                )
            else:
                success = False

            return {
                "proof_name": proof.name,
                "original_passed": proof.passed,
                "replayed_passed": replayed_proof.passed if replayed_proofs else False,
                "success": success,
                "cost": cost.to_dict(),
            }

        except Exception as e:
            return {"proof_name": proof.name, "success": False, "error": str(e)}

    def _verify_cost_consistency(self, pcap: PCAP) -> Dict[str, Any]:
        """Vérifie la cohérence des coûts dans un PCAP."""
        justification = pcap.justification

        # Vérifier que les coûts sont cohérents avec les preuves
        total_proofs = len(pcap.proofs)
        expected_audit_cost = total_proofs * 0.5  # Coût attendu par preuve

        cost_consistency = abs(justification.audit_cost - expected_audit_cost) < 1.0

        # Vérifier la cohérence temporelle
        time_consistency = justification.time_ms > 0 and justification.time_ms < 30000  # 30s max

        # Vérifier la cohérence des risques
        risk_consistency = 0.0 <= justification.risk <= 1.0

        return {
            "cost_consistency": cost_consistency,
            "time_consistency": time_consistency,
            "risk_consistency": risk_consistency,
            "expected_audit_cost": expected_audit_cost,
            "actual_audit_cost": justification.audit_cost,
        }

    def _calculate_verdict(
        self,
        integrity_check: Dict[str, Any],
        replay_results: Dict[str, Any],
        cost_consistency: Dict[str, Any],
    ) -> str:
        """Calcule le verdict final de vérification."""
        # Vérifier l'intégrité
        integrity_valid = (
            integrity_check.get("hash_valid", False)
            and integrity_check.get("timestamp_valid", False)
            and integrity_check.get("fields_valid", False)
        )

        # Vérifier le replay
        replay_valid = replay_results.get("success_rate", 0) > 0.8

        # Vérifier la cohérence des coûts
        cost_valid = (
            cost_consistency.get("cost_consistency", False)
            and cost_consistency.get("time_consistency", False)
            and cost_consistency.get("risk_consistency", False)
        )

        # Verdict final
        if integrity_valid and replay_valid and cost_valid:
            return "pass"
        elif integrity_valid and replay_valid:
            return "pass_with_warnings"
        else:
            return "fail"

    def verify_batch(self, pcaps: List[PCAP]) -> List[Dict[str, Any]]:
        """Vérifie un lot de PCAPs."""
        results = []

        for pcap in pcaps:
            result = self.replay(pcap)
            results.append(result)

        return results

    def get_verification_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de vérification."""
        if not self.verification_history:
            return {"total_verifications": 0}

        total_verifications = len(self.verification_history)
        successful_verifications = sum(
            1
            for r in self.verification_history
            if r.get("verdict") in ["pass", "pass_with_warnings"]
        )
        success_rate = (
            successful_verifications / total_verifications if total_verifications > 0 else 0
        )

        avg_verification_time = (
            sum(r.get("verification_time_ms", 0) for r in self.verification_history)
            / total_verifications
        )

        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "success_rate": success_rate,
            "average_verification_time_ms": avg_verification_time,
            "last_verification": (
                self.verification_history[-1] if self.verification_history else None
            ),
        }

    def _get_time_ms(self) -> int:
        """Retourne le temps actuel en millisecondes."""
        import time

        return int(time.time() * 1000)

    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        from datetime import datetime

        return datetime.now().isoformat()

    def reset_history(self) -> None:
        """Remet à zéro l'historique de vérification."""
        self.verification_history = []
