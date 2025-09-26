"""
Générateur stochastique pour le Proof Engine for Code v0.
Génère des variantes de patches avec LLM.
"""

from typing import List, Dict, Any, Optional
from proofengine.core.llm_client import LLMClient, LLMConfig
from proofengine.core.schemas import PatchProposal
from .prompts import GEN_SYSTEM, GEN_USER_TMPL, VARIANT_SYSTEM, VARIANT_USER_TMPL, SAFETY_SYSTEM, SAFETY_USER_TMPL


class StochasticGenerator:
    """Générateur stochastique de patches."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialise le générateur."""
        self.llm = LLMClient(config)
        self.generation_history: List[Dict[str, Any]] = []
    
    def propose_variants(self, task: str, context: str, obligations: List[str], 
                        k: int = 3) -> List[PatchProposal]:
        """
        Propose k variantes de patches pour une tâche.
        
        Args:
            task: Tâche à accomplir
            context: Contexte du code
            obligations: Obligations à satisfaire
            k: Nombre de variantes à générer
            
        Returns:
            List[PatchProposal]: Liste des propositions de patches
        """
        variants = []
        
        for i in range(k):
            try:
                # Générer une variante
                variant = self._generate_single_variant(
                    task, context, obligations, i, k
                )
                variants.append(variant)
                
                # Enregistrer dans l'historique
                self._record_generation(task, variant, i)
                
            except Exception as e:
                # Variante de fallback en cas d'erreur
                fallback = PatchProposal(
                    patch_unified="",
                    rationale=f"Fallback variant due to error: {str(e)}",
                    predicted_obligations_satisfied=[],
                    risk_score=0.8,
                    notes=f"Error in generation: {str(e)}"
                )
                variants.append(fallback)
        
        return variants
    
    def _generate_single_variant(self, task: str, context: str, obligations: List[str], 
                               variant_num: int, total_variants: int) -> PatchProposal:
        """Génère une variante individuelle."""
        # Choisir le type de variante
        if variant_num == 0:
            # Variante principale
            system_prompt = GEN_SYSTEM
            user_prompt = GEN_USER_TMPL.format(
                task=task,
                context=context,
                obligations=obligations
            )
        elif variant_num == 1 and total_variants > 2:
            # Variante alternative
            system_prompt = VARIANT_SYSTEM
            user_prompt = VARIANT_USER_TMPL.format(
                task=task,
                context=context,
                obligations=obligations,
                variant_num=variant_num
            )
        else:
            # Variante sécurisée
            system_prompt = SAFETY_SYSTEM
            user_prompt = SAFETY_USER_TMPL.format(
                task=task,
                context=context,
                obligations=obligations
            )
        
        # Générer avec le LLM
        data, meta = self.llm.generate_json(
            system_prompt,
            user_prompt,
            seed=1000 + variant_num,
            temperature=0.8,
            max_tokens=1500
        )
        
        # Extraire les données
        patch_unified = data.get("patch_unified", "")
        rationale = data.get("rationale", "")
        predicted_obligations = data.get("predicted_obligations_satisfied", [])
        risk_score = float(data.get("risk_score", 0.5))
        notes = data.get("notes", "")
        
        return PatchProposal(
            patch_unified=patch_unified,
            rationale=rationale,
            predicted_obligations_satisfied=predicted_obligations,
            risk_score=risk_score,
            notes=notes,
            llm_meta=meta
        )
    
    def generate_safety_variant(self, task: str, context: str, obligations: List[str]) -> PatchProposal:
        """Génère une variante axée sur la sécurité."""
        user_prompt = SAFETY_USER_TMPL.format(
            task=task,
            context=context,
            obligations=obligations
        )
        
        try:
            data, meta = self.llm.generate_json(
                SAFETY_SYSTEM,
                user_prompt,
                seed=2000,
                temperature=0.6,
                max_tokens=1500
            )
            
            return PatchProposal(
                patch_unified=data.get("patch_unified", ""),
                rationale=data.get("rationale", ""),
                predicted_obligations_satisfied=data.get("predicted_obligations_satisfied", []),
                risk_score=float(data.get("risk_score", 0.3)),
                notes=data.get("notes", ""),
                llm_meta=meta
            )
            
        except Exception as e:
            return PatchProposal(
                patch_unified="",
                rationale=f"Safety variant generation failed: {str(e)}",
                predicted_obligations_satisfied=[],
                risk_score=0.9,
                notes=f"Error: {str(e)}"
            )
    
    def _record_generation(self, task: str, proposal: PatchProposal, variant_num: int) -> None:
        """Enregistre une génération dans l'historique."""
        record = {
            "task": task,
            "variant_num": variant_num,
            "patch_length": len(proposal.patch_unified),
            "risk_score": proposal.risk_score,
            "obligations_satisfied": proposal.predicted_obligations_satisfied,
            "timestamp": self._get_timestamp()
        }
        
        self.generation_history.append(record)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de génération."""
        if not self.generation_history:
            return {"total_generations": 0}
        
        total_generations = len(self.generation_history)
        avg_risk = sum(g["risk_score"] for g in self.generation_history) / total_generations
        avg_patch_length = sum(g["patch_length"] for g in self.generation_history) / total_generations
        
        # Analyser les obligations satisfaites
        all_obligations = []
        for g in self.generation_history:
            all_obligations.extend(g["obligations_satisfied"])
        
        obligation_counts = {}
        for obligation in all_obligations:
            obligation_counts[obligation] = obligation_counts.get(obligation, 0) + 1
        
        return {
            "total_generations": total_generations,
            "average_risk_score": avg_risk,
            "average_patch_length": avg_patch_length,
            "obligation_frequency": obligation_counts,
            "last_generation": self.generation_history[-1] if self.generation_history else None
        }
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    def clear_history(self) -> None:
        """Remet à zéro l'historique."""
        self.generation_history = []