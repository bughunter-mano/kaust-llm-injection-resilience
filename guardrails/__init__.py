"""
Guardrails Package
Defensive boundaries, validation interceptors, sanitizers, and constitutional enforcement templates
for LLM injection cyber-resilient assistants.
"""

from guardrails.interceptors import ValidationInterceptor
from guardrails.sanitizers import PayloadSanitizer
from guardrails.constitutional_templates import (
    ConstitutionalTemplateEngine,
    CONSTITUTIONAL_INVARIANTS,
)

# For backwards compatibility with existing references
class SecurityGuardrails:
    """Compatibility wrapper preserving the legacy interface."""
    def __init__(self):
        self.sanitizer = PayloadSanitizer()

    def quarantine_input(self, artifact_text: str) -> str:
        return self.sanitizer.sanitize_and_quarantine(artifact_text)

    def validate_output(self, raw_output: str):
        return self.sanitizer.sanitize_output(raw_output)

__all__ = [
    "ValidationInterceptor",
    "PayloadSanitizer",
    "ConstitutionalTemplateEngine",
    "CONSTITUTIONAL_INVARIANTS",
    "SecurityGuardrails",
]
