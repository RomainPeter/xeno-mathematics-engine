"""
Strategy: redact_pii
Redacts PII data from logs and outputs
"""

from typing import Dict, List, Any
import re
from proofengine.core.strategy import Strategy
from proofengine.core.types import Plan, Action, Evidence


class RedactPIIStrategy(Strategy):
    """Strategy to redact PII from logs and outputs"""

    def __init__(self):
        super().__init__(
            name="redact_pii",
            description="Redact PII data from logs and outputs",
            category="security-compliance",
        )

        # PII patterns
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}-\d{3}-\d{4}\b",
            "cc": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        }

    def analyze(self, context: Dict[str, Any]) -> List[Evidence]:
        """Analyze for PII in logs and outputs"""
        evidence = []

        logs = context.get("logs", [])
        for log in logs:
            content = log.get("content", "")

            # Check for SSN
            if re.search(self.pii_patterns["ssn"], content):
                evidence.append(
                    Evidence(
                        type="SSN_DETECTED",
                        severity="critical",
                        message="SSN detected in logs",
                        file_path=log.get("file_path", "logs/app.log"),
                        line_number=log.get("line_number", 1),
                    )
                )

            # Check for email addresses
            if re.search(self.pii_patterns["email"], content):
                evidence.append(
                    Evidence(
                        type="EMAIL_DETECTED",
                        severity="high",
                        message="Email address detected in logs",
                        file_path=log.get("file_path", "logs/app.log"),
                        line_number=log.get("line_number", 1),
                    )
                )

            # Check for phone numbers
            if re.search(self.pii_patterns["phone"], content):
                evidence.append(
                    Evidence(
                        type="PHONE_DETECTED",
                        severity="high",
                        message="Phone number detected in logs",
                        file_path=log.get("file_path", "logs/app.log"),
                        line_number=log.get("line_number", 1),
                    )
                )

            # Check for credit card numbers
            if re.search(self.pii_patterns["cc"], content):
                evidence.append(
                    Evidence(
                        type="CC_DETECTED",
                        severity="critical",
                        message="Credit card number detected in logs",
                        file_path=log.get("file_path", "logs/app.log"),
                        line_number=log.get("line_number", 1),
                    )
                )

        return evidence

    def plan(self, evidence: List[Evidence]) -> Plan:
        """Plan PII redaction actions"""
        actions = []

        for ev in evidence:
            if ev.type in [
                "SSN_DETECTED",
                "EMAIL_DETECTED",
                "PHONE_DETECTED",
                "CC_DETECTED",
            ]:
                actions.append(
                    Action(
                        type="REDACT_PII",
                        description=f"Redact {ev.type.replace('_DETECTED', '').lower()} from logs",
                        file_path=ev.file_path,
                        content=self._generate_pii_redaction(ev.type),
                    )
                )

        # Add PII redaction configuration
        if evidence:
            actions.append(
                Action(
                    type="CONFIGURE_PII_REDACTION",
                    description="Configure PII redaction system",
                    file_path="configs/pii_redaction.yaml",
                    content=self._generate_pii_config(),
                )
            )

        return Plan(
            strategy=self.name,
            actions=actions,
            expected_outcome="PII data redacted from all logs and outputs",
        )

    def _generate_pii_redaction(self, pii_type: str) -> str:
        """Generate PII redaction code"""
        redaction_map = {
            "SSN_DETECTED": "REDACTED_SSN",
            "EMAIL_DETECTED": "REDACTED_EMAIL",
            "PHONE_DETECTED": "REDACTED_PHONE",
            "CC_DETECTED": "REDACTED_CC",
        }

        return f"""# PII Redaction for {pii_type}
import re

def redact_{pii_type.lower()}():
    # Redact {pii_type.lower()} from log content
    pattern = r'{self.pii_patterns[pii_type.split('_')[0].lower()]}'
    replacement = '{redaction_map[pii_type]}'
    
    def redact_content(content):
        return re.sub(pattern, replacement, content)
    
    return redact_content
"""

    def _generate_pii_config(self) -> str:
        """Generate PII redaction configuration"""
        return """# PII Redaction Configuration
pii_redaction:
  enabled: true
  patterns:
    ssn: '\\b\\d{3}-\\d{2}-\\d{4}\\b'
    email: '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
    phone: '\\b\\d{3}-\\d{3}-\\d{4}\\b'
    cc: '\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b'
  
  replacements:
    ssn: 'REDACTED_SSN'
    email: 'REDACTED_EMAIL'
    phone: 'REDACTED_PHONE'
    cc: 'REDACTED_CC'
  
  log_levels:
    - INFO
    - DEBUG
    - ERROR
    - WARN
"""
