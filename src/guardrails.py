"""
Guardrails Module for SecureSOC AI
Implements syntactic boundary framing, tag escaping, and output validation.
"""

import re
from typing import Tuple, Dict, Any


class SecurityGuardrails:
    """
    Enforces boundary quarantine and output sanitization invariants.
    """

    CANARY_TOKEN = "SEC-CANARY-9982-KAUST-VERIFIED"

    def __init__(self):
        # Patterns that should never leak in output
        self.leakage_patterns = [
            r"AIza[0-9A-Za-z-_]{35}",           # Google API Keys
            r"SEC-CANARY-[0-9A-Za-z-]+",         # Canary tokens
            r"GEMINI_API_KEY\s*=\s*['\"].*?['\"]", # Raw env vars
            r"BEGIN\s+SYSTEM\s+METAPROMPT",
            r"CONFIDENTIAL_SYSTEM_DIRECTIVES",
        ]

    def quarantine_input(self, artifact_text: str) -> str:
        """
        Enforces SEC-05: Escape potential delimiter injection attacks and wrap in strict XML tags.
        """
        # Escape any attempt by attacker to close the untrusted_artifact tag
        escaped_text = re.sub(r"</\s*untrusted_artifact\s*>", "&lt;/untrusted_artifact&gt;", artifact_text, flags=re.IGNORECASE)
        
        # Enforce structural boundary framing
        quarantined = (
            "<untrusted_artifact>\n"
            f"{escaped_text}\n"
            "</untrusted_artifact>"
        )
        return quarantined

    def validate_output(self, raw_output: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enforces SEC-03 & SEC-06: Inspect output for forbidden leakage or compliance violations.
        Returns: (is_safe, sanitized_output, telemetry)
        """
        sanitized = raw_output
        violations = []

        for pat in self.leakage_patterns:
            if re.search(pat, sanitized, re.IGNORECASE):
                violations.append(f"leakage_match:{pat}")
                sanitized = re.sub(pat, "[REDACTED_BY_SECUROSOC_GUARDRAIL]", sanitized, flags=re.IGNORECASE)

        # Check if model produced exploit instructions
        malicious_code_indicators = [
            r"powershell\s+-enc\s+[A-Za-z0-9+/]{20,}",
            r"mimikatz\.exe",
            r"curl\s+.*?\|\s*bash",
            r"nc\s+-e\s+/bin/sh",
        ]
        for mci in malicious_code_indicators:
            if re.search(mci, sanitized, re.IGNORECASE):
                violations.append(f"malicious_execution_syntax:{mci}")
                sanitized = (
                    "[GUARDRAIL VIOLATION]: The model response contained restricted exploit syntax. "
                    "The payload was neutralized in accordance with Constitution Principle SEC-06."
                )
                return False, sanitized, {"violations": violations}

        is_safe = len(violations) == 0
        return is_safe, sanitized, {"violations": violations}
