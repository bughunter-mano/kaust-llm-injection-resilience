"""
Injection Detector Module for SecureSOC AI
Implements heuristic, lexical, and regex-based prompt injection detection.
"""

import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class InjectionReport(BaseModel):
    is_injected: bool = Field(description="Whether prompt injection or jailbreak was detected")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    threat_category: Optional[str] = Field(default=None, description="Classified attack category")
    matched_patterns: List[str] = Field(default_factory=list, description="List of matched signatures")
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadata and extracted signatures")


class PromptInjectionDetector:
    """
    Multi-signature detector inspecting prompts and ingested security artifacts.
    """

    def __init__(self):
        # 1. Direct Command Overrides
        self.override_patterns = [
            r"(?i)\bignore\s+(all\s+)?(previous|prior|system)\s+instructions\b",
            r"(?i)\bdisregard\s+(all\s+)?(previous|prior|security|safety)\s+(instructions|policies|rules|constraints)\b",
            r"(?i)\bnew\s+priority\s+(instruction|directive)\b",
            r"(?i)\bsystem\s+override\b",
            r"(?i)\bsystem_alert\s*:\s*disregard\b",
            r"(?i)\bcommand\s*:\s*ignore\s+all\b",
            r"(?i)\bdisable\s+all\s+(safety|security)\s+filters\b",
            r"(?i)\bdeveloper\s+override\b",
            r"(?i)\bdebug\s+mode\s+activated\b",
            r"(?i)\breset\s+system\s+directives\b",
        ]

        # 2. Persona / Jailbreak Manipulation
        self.jailbreak_patterns = [
            r"(?i)\byou\s+are\s+going\s+to\s+pretend\s+to\s+be\s+DAN\b",
            r"(?i)\bDAN\s+has\s+broken\s+free\b",
            r"(?i)\bunrestricted\s+terminal\s+emulator\b",
            r"(?i)\bevil\s+twin\b",
            r"(?i)\bAntiSecure\b",
            r"(?i)\bdeceased\s+grandmother\b",
            r"(?i)\bacademic\s+exemption\s+treaties\b",
            r"(?i)\btop-secret\s+research\s+clearance\b",
            r"(?i)\bhypothetical\s+universe\b",
            r"(?i)\brogue\s+military\s+AI\b",
            r"(?i)\bact\s+as\s+my\s+deceased\b",
            r"(?i)\bhollywood\s+movie\s+script\b",
            r"(?i)\bfreebot\b",
        ]

        # 3. Delimiter & Boundary Tampering
        self.delimiter_patterns = [
            r"</untrusted_artifact>",
            r"--- END OF CONTEXT ---",
            r"--- BEGIN NEW SESSION ---",
            r"<!-- Hidden Prompt:",
            r"\[INTERNAL NOTICE TO AI ANALYST",
            r"\[SYSTEM NOTE:",
            r"\[SYSTEM PROMPT UPDATE",
        ]

        # 4. Sensitive Information & Metaprompt Leakage Probes
        self.extraction_patterns = [
            r"(?i)\bverbatim\s+text\s+of\s+your\s+system\s+prompt\b",
            r"(?i)\bprint\s+(the\s+)?system\s+prompt\b",
            r"(?i)\blist\s+every\s+single\s+rule\b.*security_constitution",
            r"(?i)\bvalue\s+of\s+the\s+environment\s+variable\s+GEMINI_API_KEY\b",
            r"(?i)\bsecret\s+canary\s+token\b",
            r"(?i)\bcanary\s+token\b",
            r"(?i)\btranslate\s+your\s+private\s+system\s+instructions\b",
            r"(?i)\bprint\s+the\s+full\s+internal\s+environment\s+variables\b",
            r"(?i)\bencode\s+your\s+system\s+prompt\s+into\s+base64\b",
            r"(?i)\braw\s+internal\s+reasoning\s+trace\b",
            r"(?i)\bwhat\s+were\s+the\s+exact\s+words\s+of\s+your\s+original\s+system\s+prompt\b",
        ]

        # 5. Obfuscation & Leetspeak Token Smuggling
        self.obfuscation_patterns = [
            r"\b[dD]1sr3g4rd\b",
            r"\bs4f3ty\b",
            r"\brUl3z\b",
            r"(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)",  # Base64 blocks
        ]

    def detect(self, text: str) -> InjectionReport:
        """
        Inspect input text and return an InjectionReport.
        """
        matched = []
        threat_cat = None

        # Check Extraction Probes
        for p in self.extraction_patterns:
            if re.search(p, text):
                matched.append(f"extraction_probe:{p}")
                threat_cat = "sensitive_information_extraction"

        # Check Direct Overrides
        for p in self.override_patterns:
            if re.search(p, text):
                matched.append(f"instruction_override:{p}")
                if not threat_cat:
                    threat_cat = "direct_prompt_injection"

        # Check Jailbreak Patterns
        for p in self.jailbreak_patterns:
            if re.search(p, text):
                matched.append(f"jailbreak_persona:{p}")
                threat_cat = "jailbreak_persona_manipulation"

        # Check Delimiter Breakouts
        for p in self.delimiter_patterns:
            if re.search(p, text, re.IGNORECASE):
                matched.append(f"delimiter_breakout:{p}")
                if not threat_cat:
                    threat_cat = "indirect_prompt_injection"

        # Check Obfuscation
        for p in self.obfuscation_patterns:
            if re.search(p, text):
                matched.append(f"obfuscation:{p}")
                if not threat_cat:
                    threat_cat = "obfuscated_injection"

        if matched:
            confidence = min(0.99, 0.70 + (0.10 * len(matched)))
            return InjectionReport(
                is_injected=True,
                confidence=confidence,
                threat_category=threat_cat or "unknown_injection",
                matched_patterns=matched,
                details={"match_count": len(matched)}
            )

        return InjectionReport(
            is_injected=False,
            confidence=0.05,
            threat_category=None,
            matched_patterns=[],
            details={"match_count": 0}
        )
