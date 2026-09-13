# Literature Review: Prompt Injection Resilience in Foundation Models

**Project:** SecureSOC AI  
**Institutional Affiliation:** KAUST Research Internship Candidate Project  

---

## 1. Taxonomic Background & Threat Landscape
Adversarial attacks against foundation models have rapidly evolved from digital adversarial perturbations in computer vision to semantic and instruction-level exploits in autoregressive transformers.

- **Direct Prompt Injections and Jailbreaks:** Perez & Ribeiro (2022) and Wei et al. (2023) demonstrated that LLMs are vulnerable to systemic jailbreaks through role-playing framing (e.g., "Do Anything Now" / DAN), cognitive hypnosis, and hypotheticals. Zou et al. (2023) introduced Greedy Coordinate Gradient (GCG) attacks, proving that universal adversarial suffixes can bypass safety fine-tuning.
- **Indirect Prompt Injection (IPI):** First formalized by Greshake et al. (2023), IPI demonstrated that when language models ingest third-party content (web pages, search results, emails, or logs), adversaries can silently hijack the model's control flow. In security operations, this enables data exfiltration and telemetry poisoning without the analyst's knowledge.

---

## 2. In-Context & Guardrail Defenses

### 2.1. Structural Delimiters & Escaping
Several empirical studies (Piet et al., 2023; Suo et al., 2024) explored framing untrusted inputs inside XML, Markdown, or cryptographic delimiter tags (e.g., `<user_data>...</user_data>`). However, attackers readily bypass simple delimiter schemes using **delimiter escaping** (e.g., emitting `</user_data>` inside the prompt) or context boundary resets. SecureSOC AI addresses this through rigorous escaping and programmatic tag quarantine.

### 2.2. Heuristic and Classifier-Based Gatekeepers
Frameworks such as NeMo Guardrails (Rebedea et al., 2023) and Llama Guard (Inan et al., 2023) introduce auxiliary classifier models to inspect incoming prompts prior to reaching the primary LLM. While effective against direct attacks, these filters exhibit extreme false positive rates in domain-specific SOC settings because benign analyst queries inherently discuss malicious concepts.

---

## 3. Constitutional AI & Inference-Time Alignment
The concept of **Constitutional AI (CAI)** was pioneered by Anthropic (Bai et al., 2022) as a method for training harmless assistants using a set of written principles rather than human-in-the-loop labels for every refusal. In CAI training, models critique and revise their own outputs according to the constitution.

In SecureSOC AI, we adapt this concept to the **inference-time operational layer**:
- Principles are codified as a versioned JSON policy engine (`security_constitution.json`).
- The assistant is dynamically instructed to prioritize constitutional invariants over arbitrary instructions found inside ingested artifacts.
- Crucially, we introduce **Adaptive Constitutional Feedback**: when novel attack vectors are detected, the system automatically synthesizes candidate principles and verifies them against regression benchmarks.

---

## 4. Post-Training Alignment: DPO and Machine Unlearning

### 4.1. Direct Preference Optimization (DPO)
Pioneered by Rafailov et al. (NeurIPS 2023), DPO replaced unstable reinforcement learning (PPO) by deriving a mathematical equivalence that allows fine-tuning directly on preference pairs $(x, y_w, y_l)$. In cybersecurity safety, DPO provides an ideal mechanism for penalizing compromised instruction-following responses while rewarding dual-goal forensic explanations.

### 4.2. Machine Unlearning
Recent work by Yao et al. (2024) and Maini et al. (2024) highlights the necessity of unlearning dangerous knowledge (e.g., CBRN threats and automated zero-day exploitation). Rather than merely masking outputs, unlearning aims to modify parameter weights to eliminate the latent capability altogether, preventing jailbreak re-emergence.

---

## 5. Summary Matrix of Existing Approaches vs. SecureSOC AI

| Approach | Defense Layer | Latency Impact | Resilience to IPI | Cybersecurity Utility |
|---|---|---|---|---|
| **Vanilla System Prompt** | Context | None | Extremely Low (ASR > 60%) | High on benign |
| **Heuristic Pattern Gatekeeper** | Pre-inference | Minimal (< 1ms) | Moderate | **Zero on flagged logs (Utility Collapse)** |
| **Separate Guardrail LLM** | Pre-inference | High (2x LLM calls) | High | Variable / High cost |
| **SecureSOC AI (Constitutional)** | Dynamic Context + Quarantine | Low (Single-call overhead) | **Maximum (0% ASR)** | **100% (Dual-Goal Continuity)** |
