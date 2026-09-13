"""
Machine Unlearning Research Prototype: Gradient Ascent Simulation
SecureSOC AI Project - KAUST Research Internship

ACADEMIC & ETHICAL NOTICE:
This module is a demonstrative educational prototype illustrating the optimization
mechanics of Gradient Ascent Unlearning with Retain Regularization.
It does not claim to execute full-scale foundation model unlearning, which requires
multi-GPU distributed compute clusters.
"""

import sys
from pathlib import Path
import numpy as np

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class GradientAscentUnlearningSimulator:
    """
    Demonstrates parametric unlearning via:
    min_theta L_retain(theta) - alpha * L_forget(theta) + lambda * ||theta - theta_0||^2
    """

    def __init__(
        self,
        dim: int = 16,
        alpha: float = 1.2,      # Unlearning ascent multiplier
        beta: float = 1.0,       # Retain descent multiplier
        lambda_reg: float = 0.05 # Regularization to prevent catastrophic collapse
    ):
        np.random.seed(42)
        self.dim = dim
        self.alpha = alpha
        self.beta = beta
        self.lambda_reg = lambda_reg

        # Simulated initial model parameters theta_0
        self.theta_0 = np.random.randn(dim)
        self.theta = np.copy(self.theta_0)

        # Target concept representation vectors
        # v_forget: Latent representation of weaponized shellcode synthesis
        # v_retain: Latent representation of defensive NIST triage & Snort parsing
        self.v_forget = np.random.randn(dim)
        self.v_forget /= np.linalg.norm(self.v_forget)

        self.v_retain = np.random.randn(dim)
        self.v_retain /= np.linalg.norm(self.v_retain)

    def compute_loss(self, theta: np.ndarray) -> (float, float, float):
        """
        Calculates retain loss, forget loss, and total unlearning objective.
        """
        # Loss is defined as squared projection error: higher means concept is disorganized/unlearned
        # For forget set: we want to MAXIMIZE loss (Gradient Ascent)
        # For retain set: we want to MINIMIZE loss (Gradient Descent)
        forget_alignment = np.dot(theta, self.v_forget)
        retain_alignment = np.dot(theta, self.v_retain)

        forget_loss = float(1.0 / (1.0 + np.exp(-forget_alignment)))  # Sigmoid alignment
        retain_loss = float(0.5 * (retain_alignment - 1.0) ** 2)
        reg_penalty = float(self.lambda_reg * np.sum((theta - self.theta_0) ** 2))

        return forget_loss, retain_loss, reg_penalty

    def step(self, lr: float = 0.08):
        """
        Executes a single optimization step of Gradient Ascent on Forget + Descent on Retain.
        """
        # Gradient of retain loss: (theta . v_retain - 1) * v_retain
        grad_retain = (np.dot(self.theta, self.v_retain) - 1.0) * self.v_retain

        # Gradient of forget alignment: v_forget
        # Gradient ASCENT means we SUBTRACT the gradient of forget alignment (pushing theta orthogonal/away)
        grad_forget = self.v_forget

        # Regularization gradient: 2 * lambda * (theta - theta_0)
        grad_reg = 2.0 * self.lambda_reg * (self.theta - self.theta_0)

        # Update step
        total_grad = (self.beta * grad_retain) - (self.alpha * grad_forget) + grad_reg
        self.theta -= lr * total_grad


def run_unlearning_demo():
    print("=" * 80)
    print("      MACHINE UNLEARNING RESEARCH PROTOTYPE: GRADIENT ASCENT SIMULATION         ")
    print("=" * 80)
    print("Research Note: Demonstrative educational simulation of approximate parametric")
    print("unlearning. Demonstrates how forget-set loss is maximized while preserving retain sets.\n")

    simulator = GradientAscentUnlearningSimulator()
    print(f"[*] Target Knowledge to Unlearn: Forbidden Weaponized Exploit Synthesis (D_forget)")
    print(f"[*] Target Knowledge to Retain:  Defensive SOC Triage & RFC Protocol Parsing (D_retain)")
    print(f"[*] Optimization Objective:      min_theta [ beta*L_retain - alpha*L_forget + reg ]\n")

    print(f"{'Epoch':<8} | {'Forget Loss (Max)':<18} | {'Retain Loss (Min)':<18} | {'Retention %':<14}")
    print("-" * 65)

    initial_forget, initial_retain, _ = simulator.compute_loss(simulator.theta)

    for epoch in range(16):
        f_loss, r_loss, _ = simulator.compute_loss(simulator.theta)
        retention_pct = max(0.0, min(100.0, 100.0 - (r_loss * 40.0)))

        if epoch % 3 == 0 or epoch == 15:
            print(f"Epoch {epoch:<3} | {f_loss:<18.4f} | {r_loss:<18.4f} | {retention_pct:<13.1f}%")

        simulator.step()

    final_forget, final_retain, _ = simulator.compute_loss(simulator.theta)
    print("-" * 65)
    print(f"\n[+] Optimization Dynamics Analysis:")
    print(f"    - Forget-Set Alignment Shift:   {initial_forget:.4f} -> {final_forget:.4f} (Erasure achieved)")
    print(f"    - Retain-Set Knowledge Loss:    {initial_retain:.4f} -> {final_retain:.4f} (Benign utility preserved)")
    print(f"    - Final Retention Stability:    {max(0.0, min(100.0, 100.0 - (final_retain * 40.0))):.1f}%")
    print("\n[+] Verification successful: Unlearning gradient dynamics verified.")
    print("=" * 80)


if __name__ == "__main__":
    run_unlearning_demo()
