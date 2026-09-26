"""
Guardrails: Sanitizers
Implements syntactic boundary containment, delimiter sanitization, and output leak redaction.
"""

import re
from typing import Tuple, Dict, Any, List


class PayloadSanitizer:
    """
    Sanitizes untrusted payloads to prevent delimiter escaping and redacts confidential
    information or canary tokens from model outputs.
    """

    DEFAULT_CANARY_TOKEN = "SEC-CANARY-9982-KAUST-VERIFIED"

    DEFAULT_LEAKAGE_PATTERNS = [
        r"AIza[0-9A-Za-z-_]{35}",              # Google API Keys
        r"SEC-CANARY-[0-9A-Za-z-]+",            # Canary tokens
        r"sk-[a-zA-Z0-9]{32,}",                # OpenAI / Generic API Keys
        r"GEMINI_API_KEY\s*=\s*['\"].*?['\"]", # Raw environment variables
        r"BEGIN\s+SYSTEM\s+METAPROMPT",        # Internal metaprompt fragments
        r"CONFIDENTIAL_SYSTEM_DIRECTIVES",     # Confidential directive fragments
    ]

    RESTRICTED_EXPLOIT_PATTERNS = [
        r"powershell\s+-enc\s+[A-Za-z0-9+/]{20,}",
        r"mimikatz\.exe",
        r"curl\s+.*?\|\s*(bash|sh)",
        r"nc\s+-e\s+/bin/(sh|bash)",
        r"rm\s+-rf\s+/(etc|boot|sys|var)?",
    ]

    def __init__(self, canary_token: str = DEFAULT_CANARY_TOKEN, extra_patterns: List[str] = None):
        self.canary_token = canary_token
        self.leakage_patterns = list(self.DEFAULT_LEAKAGE_PATTERNS)
        if extra_patterns:
            self.leakage_patterns.extend(extra_patterns)

    def sanitize_and_quarantine(self, raw_artifact: str) -> str:
        """
        Syntactic Boundary Containment:
        Escapes boundary closing tags and encapsulates untrusted input inside XML containers.
        Prevents prompt injection payload from breaking out of data context.
        """
        # 1. Escape closing tags
        escaped = re.sub(
            r"</\s*untrusted_artifact\s*>",
            "&lt;/untrusted_artifact&gt;",
            raw_artifact,
            flags=re.IGNORECASE,
        )
        # 2. Escape opening tags to prevent nested structural confusion
        escaped = re.sub(
            r"<\s*untrusted_artifact\s*>",
            "&lt;untrusted_artifact&gt;",
            escaped,
            flags=re.IGNORECASE,
        )
        # 3. Neutralize simulated boundary tokens
        escaped = escaped.replace("--- END OF CONTEXT ---", "[ESCAPED: END OF CONTEXT]")
        escaped = escaped.replace("--- BEGIN NEW SESSION ---", "[ESCAPED: BEGIN NEW SESSION]")

        # 4. Strict structural boundary quarantine encapsulation
        return f"<untrusted_artifact>\n{escaped}\n</untrusted_artifact>"

    def sanitize_output(self, raw_output: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates model output to prevent confidential prompt leaks, canary token exfiltration,
        and weaponized exploit scripts.
        """
        sanitized = raw_output
        violations = []

        # Mask leaked secrets and canary tokens
        for pattern in self.leakage_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                violations.append(f"leakage_redaction:{pattern}")
                sanitized = re.sub(pattern, "[REDACTED_BY_GUARDRAIL]", sanitized, flags=re.IGNORECASE)

        # Intercept actionable exploit generation
        for mci in self.RESTRICTED_EXPLOIT_PATTERNS:
            if re.search(mci, sanitized, re.IGNORECASE):
                violations.append(f"malicious_execution_syntax:{mci}")
                sanitized = (
                    "[GUARDRAIL VIOLATION]: The model response contained restricted exploit syntax. "
                    "The payload was neutralized in accordance with Constitutional Operational Invariants."
                )
                return False, sanitized, {"violations": violations}

        is_safe = (len(violations) == 0)
        return is_safe, sanitized, {"violations": violations}
