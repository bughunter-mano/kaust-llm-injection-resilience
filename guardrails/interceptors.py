"""
Guardrails: Validation Interceptors
Enforces operational boundary constraints and validates inputs before LLM or tool execution.
Prevents Direct Prompt Injections and Indirect Prompt Injections (logs, documents, tool outputs).
"""

import re
from typing import Dict, Any, Tuple, Optional


class ValidationInterceptor:
    """
    Validation interceptor that inspects user queries, ingested logs, untrusted tool returns,
    and tool execution requests to prevent injection payloads from triggering unauthorized actions.
    """

    DEFAULT_OVERRIDE_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts|guidelines)",
        r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|directives)",
        r"(?i)ignora\s+(todas\s+)?(las\s+)?instrucciones",
        r"(?i)system\s+override\s*:",
        r"(?i)developer\s+mode\s+activated",
        r"(?i)you\s+are\s+now\s+(unrestricted|DAN|freebot)",
        r"(?i)do\s+anything\s+now",
        r"(?i)(api[_-]?key|secret\s+canary|gemini_api_key|system\s+prompt|metaprompt)",
    ]

    TOOL_HIJACKING_PATTERNS = [
        r"(?i)(curl|wget|nc|netcat|bash|sh|powershell|cmd\.exe)\s+",
        r"(?i)rm\s+-rf\s+",
        r"(?i)drop\s+table\s+",
        r"(?i)execute\s+tool\s*:",
        r"(?i)call\s+(external\s+)?tool\s+",
        r"(?i)invoke\s+[a-zA-Z0-9_]+\s*(tool|\()?",
        r"(?i)call_function\s*:",
        r"(?i)invoke_tool\s*\(",
        r"(?i)send\s+(secrets|api_key|token)\s+to\s+",
        r"(?i)exfiltrate_[a-zA-Z0-9_]+",
    ]

    def __init__(self, override_patterns: Optional[list] = None, hijacking_patterns: Optional[list] = None):
        self.override_patterns = override_patterns or self.DEFAULT_OVERRIDE_PATTERNS
        self.hijacking_patterns = hijacking_patterns or self.TOOL_HIJACKING_PATTERNS

    def intercept_input(self, text: str, channel: str = "direct_chat") -> Dict[str, Any]:
        """
        Validates incoming text from untrusted input channels:
        - 'direct_chat': direct user input
        - 'ingested_log': syslog, access log, SIEM telemetry
        - 'ingested_document': email, CVE advisory, markdown document, git diff
        - 'tool_output': output returned from an external or untrusted tool

        Returns a dictionary with threat classification and interception action.
        """
        detected_threats = []

        # Check for system prompt override directives
        for pattern in self.override_patterns:
            if re.search(pattern, text):
                detected_threats.append(f"system_prompt_override:{pattern}")

        # Check for tool hijacking / code execution triggers
        for pattern in self.hijacking_patterns:
            if re.search(pattern, text):
                detected_threats.append(f"tool_hijacking_indicator:{pattern}")

        # Check for boundary breakout markers
        if "</untrusted_artifact>" in text.lower() or "--- end of context ---" in text.lower():
            detected_threats.append("boundary_delimiter_tampering")

        is_adversarial = len(detected_threats) > 0

        # Operational decision based on channel
        if channel == "direct_chat" and is_adversarial:
            action = "block_or_refuse"
        elif channel in ("ingested_log", "ingested_document", "tool_output") and is_adversarial:
            # Dual-goal continuity: quarantine control tokens, but allow forensic inspection
            action = "quarantine_and_neutralize"
        else:
            action = "pass"

        return {
            "channel": channel,
            "is_adversarial": is_adversarial,
            "threats": detected_threats,
            "action": action,
        }

    def intercept_tool_invocation(self, tool_name: str, tool_args: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Enforces operational boundary constraints on tool invocations.
        Blocks suspicious tool executions derived from injected instructions in logs/documents.
        """
        # Block arbitrary shell / system command tools if flagged
        blocked_tools = ["execute_shell", "run_bash", "eval_code", "system_exec", "terminal_command"]
        if tool_name.lower() in blocked_tools:
            return False, f"[GUARDRAIL INTERCEPTION] Tool invocation '{tool_name}' blocked: High-risk privileged tool."

        # Check tool arguments for command injection or exfiltration targets
        args_str = str(tool_args)
        for pattern in self.hijacking_patterns:
            if re.search(pattern, args_str):
                return False, f"[GUARDRAIL INTERCEPTION] Blocked '{tool_name}' execution: Suspicious payload detected in arguments."

        return True, "Tool invocation permitted under operational boundary constraints."
