#!/usr/bin/env python3
"""
Orchestrator LLM adapter with PromptContract
"""

import json
from typing import Any, Dict, List, Optional

from proofengine.adapters.openrouter import OpenRouterAdapter


class PromptContract:
    """PromptContract builder for different operators"""

    @staticmethod
    def build_meet_contract(
        task: str, inputs: List[Dict[str, Any]], constraints: List[str]
    ) -> Dict[str, Any]:
        """Build Meet operator contract"""
        return {
            "version": "0.1.0",
            "role": "Meet",
            "task": task,
            "inputs": inputs,
            "constraints": constraints,
            "output_schema_uri": "https://spec.proof.engine/v0.1/plan.schema.json",
            "budgets": {"tokens": 400, "latency_ms": 2000},
        }

    @staticmethod
    def build_generalize_contract(
        task: str, inputs: List[Dict[str, Any]], constraints: List[str]
    ) -> Dict[str, Any]:
        """Build Generalize operator contract"""
        return {
            "version": "0.1.0",
            "role": "Generalize",
            "task": task,
            "inputs": inputs,
            "constraints": constraints,
            "output_schema_uri": "https://spec.proof.engine/v0.1/pcap.schema.json",
            "budgets": {"tokens": 600, "latency_ms": 3000},
        }

    @staticmethod
    def build_refute_contract(
        task: str, inputs: List[Dict[str, Any]], constraints: List[str]
    ) -> Dict[str, Any]:
        """Build Refute operator contract"""
        return {
            "version": "0.1.0",
            "role": "Refute",
            "task": task,
            "inputs": inputs,
            "constraints": constraints,
            "output_schema_uri": "https://spec.proof.engine/v0.1/failreason.schema.json",
            "budgets": {"tokens": 300, "latency_ms": 1500},
        }


class OrchestratorLLMAdapter:
    """Orchestrator adapter for LLM calls with PromptContract"""

    def __init__(self, llm_adapter: Optional[OpenRouterAdapter] = None):
        self.llm_adapter = llm_adapter or OpenRouterAdapter()
        self.contract_builder = PromptContract()

    def _contract_to_messages(self, contract: Dict[str, Any]) -> List[Dict[str, str]]:
        """Convert PromptContract to LLM messages"""
        system_prompt = f"""You are a proof-carrying action generator.
Role: {contract['role']}
Task: {contract['task']}
Constraints: {', '.join(contract['constraints'])}
Output must be valid JSON matching the schema at {contract['output_schema_uri']}"""

        user_prompt = f"""Generate a response for:
Task: {contract['task']}
Inputs: {json.dumps(contract['inputs'], indent=2)}
Constraints: {json.dumps(contract['constraints'], indent=2)}

Return valid JSON only."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _validate_response(self, response: str, schema_uri: str) -> bool:
        """Basic validation of LLM response"""
        try:
            data = json.loads(response)
            # Basic schema validation based on URI
            if "plan.schema.json" in schema_uri:
                return "plan" in data and isinstance(data["plan"], list)
            elif "pcap.schema.json" in schema_uri:
                return "action" in data and "operator" in data
            elif "failreason.schema.json" in schema_uri:
                return "reason" in data and "category" in data
            return True
        except json.JSONDecodeError:
            return False

    def call_meet(
        self, task: str, x_summary: Dict[str, Any], obligations: List[str]
    ) -> Dict[str, Any]:
        """Call Meet operator (planning)"""
        inputs = [
            {"name": "x_summary", "type": "object", "value": json.dumps(x_summary)},
            {"name": "obligations", "type": "array", "value": json.dumps(obligations)},
        ]
        constraints = [
            "JSON output only",
            "Plan must be actionable",
            "Consider all obligations",
        ]

        contract = self.contract_builder.build_meet_contract(task, inputs, constraints)
        messages = self._contract_to_messages(contract)

        response, meta = self.llm_adapter.call_llm(
            messages, expected_schema=contract["output_schema_uri"]
        )

        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        # Validate response
        if not self._validate_response(content, contract["output_schema_uri"]):
            content = '{"plan": ["fallback_step"], "est_success": 0.5}'

        return {"response": json.loads(content), "meta": meta, "contract": contract}

    def call_generalize(
        self, task: str, context: Dict[str, Any], constraints: List[str]
    ) -> Dict[str, Any]:
        """Call Generalize operator (action generation)"""
        inputs = [
            {"name": "context", "type": "object", "value": json.dumps(context)},
            {"name": "constraints", "type": "array", "value": json.dumps(constraints)},
        ]

        contract = self.contract_builder.build_generalize_contract(task, inputs, constraints)
        messages = self._contract_to_messages(contract)

        response, meta = self.llm_adapter.call_llm(
            messages, expected_schema=contract["output_schema_uri"]
        )

        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        # Validate response
        if not self._validate_response(content, contract["output_schema_uri"]):
            content = '{"action": {"name": "fallback", "params": {}}, "operator": "generalize"}'

        return {"response": json.loads(content), "meta": meta, "contract": contract}

    def call_refute(
        self, task: str, evidence: Dict[str, Any], constraints: List[str]
    ) -> Dict[str, Any]:
        """Call Refute operator (failure analysis)"""
        inputs = [
            {"name": "evidence", "type": "object", "value": json.dumps(evidence)},
            {"name": "constraints", "type": "array", "value": json.dumps(constraints)},
        ]

        contract = self.contract_builder.build_refute_contract(task, inputs, constraints)
        messages = self._contract_to_messages(contract)

        response, meta = self.llm_adapter.call_llm(
            messages, expected_schema=contract["output_schema_uri"]
        )

        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        # Validate response
        if not self._validate_response(content, contract["output_schema_uri"]):
            content = '{"reason": "validation_failed", "category": "syntax_error"}'

        return {"response": json.loads(content), "meta": meta, "contract": contract}

    def ping(self) -> Dict[str, Any]:
        """Test LLM connectivity"""
        return self.llm_adapter.ping()
