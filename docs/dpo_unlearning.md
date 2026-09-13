# Machine Unlearning and Preference Alignment in Cybersecurity LLMs

**Author:** KAUST Internship Candidate Research Team  
**System:** SecureSOC AI  
**Focus Areas:** Direct Preference Optimization (DPO), Machine Unlearning, Prompt Injection Resilience  

---

## 1. Introduction & Theoretical Foundations
Large Language Models (LLMs) deployed within automated Security Operations Centers (SOCs) are trained on massive web-scale corpora that inevitably contain both defensive telemetry knowledge and offensive exploitation code (e.g., proof-of-concept exploits, malware source code, and command injection primitives).

While pre-trained foundation models excel at broad reasoning, their internal parametric memory creates critical security liabilities:
1. **Adversarial Re-Emergence:** In-context prompt guardrails or system metaprompts merely suppress the probability of generating malicious tokens; the underlying representations remain latent within the weights $\theta$. Sophisticated jailbreaks (e.g., persona manipulation, delimiter escape, or multi-lingual ciphers) can bypass inference-time filters and reconstruct harmful payloads.
2. **Untrusted Instruction Conflation:** Ingestion of malicious security telemetry (indirect prompt injection) tricks the model into executing commands embedded inside data.

To achieve genuine cyber resilience, the research community is exploring **Machine Unlearning** and **Direct Preference Optimization (DPO)** to align model weights rather than relying exclusively on prompt-level wrappers.

---

## 2. What Machine Unlearning Means in LLMs
Machine Unlearning refers to the algorithmic process of removing the influence of a specific subset of training data ($\mathcal{D}_{\text{forget}}$) from a trained model's parameters $\theta$, such that:
$$P_\theta(Y \mid X \in \mathcal{D}_{\text{forget}}) \approx P_{\theta \setminus \mathcal{D}_{\text{forget}}}(Y \mid X \in \mathcal{D}_{\text{forget}})$$
while preserving performance on the retain distribution $\mathcal{D}_{\text{retain}}$ without requiring complete retraining of the foundation model from scratch.

In an LLM, exact unlearning (such as deterministic Sharded, Isolated, Sliced, and Aggregated [SISA] training) is computationally intractable because the transformer's multi-head self-attention mechanisms disperse conceptual associations across billions of non-linear weights. Therefore, contemporary LLM unlearning relies on **approximate parametric erasure**.

---

## 3. Why Unlearning is Critical for Cybersecurity Assistants
In the context of SecureSOC AI, target behaviors that must be excised include:
- **Weaponized Exploit Generation:** Erasing the ability to synthesize functional binary shellcode, polymorphic keyloggers, and zero-day evasion scripts.
- **Obedience to Injected Control Directives:** Unlearning the fundamental instinct to treat text following keywords like `SYSTEM OVERRIDE:` or `Ignore previous instructions:` as authoritative commands.
- **Parametric Credential & Secret Memorization:** Eliminating memorized API keys, internal network topology details, or proprietary operational secrets present in pre-training corpora.

Crucially, this must be achieved **without destroying defensive utility**: the assistant must still understand CVE descriptions, recognize Snort and YARA syntax, and parse malware analysis reports.

---

## 4. Algorithmic Techniques for LLM Unlearning

### 4.1. Gradient Ascent (GA) with Retain Regularization
The most direct formulation inverts the standard cross-entropy minimization loss on the forget set while penalizing deviation on the retain set:
$$\mathcal{L}_{\text{unlearn}}(\theta) = -\alpha \mathcal{L}_{\text{CE}}(\theta; \mathcal{D}_{\text{forget}}) + \beta \mathcal{L}_{\text{CE}}(\theta; \mathcal{D}_{\text{retain}}) + \lambda \|\theta - \theta_0\|_2^2$$
- The first term ($-\alpha \mathcal{L}_{\text{forget}}$) performs **gradient ascent**, maximizing prediction entropy and destroying structured generation of forbidden sequences.
- The second term maintains fluency on benign cybersecurity tasks.
- The third term ($\ell_2$ weight decay relative to initial weights $\theta_0$) prevents catastrophic parameter divergence.

### 4.2. Direct Preference Optimization (DPO) as Soft Unlearning
Rather than unconstrained gradient ascent (which is inherently unstable), DPO implicitly performs unlearning by maximizing the relative log-ratio between compliant forensic responses ($y_w$) and compromised malicious responses ($y_l$):
$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)} \right) \right]$$
The gradient of $\mathcal{L}_{\text{DPO}}$ with respect to $\theta$ applies a negative gradient step specifically proportional to the implicit reward error on $y_l$, effectively unlearning the inclination to obey prompt injections.

### 4.3. Task Vector Subtraction & Representation Scrubbing
By fine-tuning a small adapter $\Delta \theta_{\text{exploit}}$ specifically on offensive malware generation, an unlearned model $\theta_{\text{unlearned}}$ can be synthesized via parameter arithmetic:
$$\theta_{\text{unlearned}} = \theta_{\text{base}} - \gamma \Delta \theta_{\text{exploit}}$$
Similarly, activation addition or representation steering can zero out attention heads identified via causal tracing as responsible for instruction-data conflation.

---

## 5. Evaluation Challenges & The "Unlearning Illusion"
Validating whether an LLM has genuinely unlearned a behavior is notoriously difficult:
1. **Catastrophic Collateral Forgetting:** Aggressive unlearning of exploitation concepts often degrades general reasoning, causing the model to hallucinate when analyzing benign PCAP logs or IDS rules.
2. **Re-emergence via In-Context Relearning:** A model whose offensive weights were supposedly unlearned can frequently be re-prompted into weaponized outputs if the attacker supplies partial exploit fragments in context (few-shot jailbreaking).
3. **Membership Inference & Verification Asymmetry:** Proving that an LLM has zero residual memory of a concept requires proving a negative across an infinite prompt space.

---

## 6. Current Implementation Scope & Future Roadmap
- **Implemented Research Contribution:** SecureSOC AI implements a curated 30-sample preference dataset (`experiments/preference_dataset.json`), the mathematical DPO objective simulator (`src/dpo_trainer_prototype.py`), and a demonstrative gradient ascent unlearning prototype (`src/unlearning_prototype.py`).
- **Proposed Future Engineering (GPU Cluster):**
  1. Full parameter fine-tuning of an open-weights model (e.g., Llama-3-8B or Mistral-7B) using LoRA/QLoRA on the DPO preference dataset.
  2. Integration of KL-divergence regularized Gradient Ascent on the forget partition of synthetic exploit sets.
  3. Pre- and post-unlearning red-teaming benchmarks using automated jailbreak suites (e.g., GCG and PAIR).
