#!/usr/bin/env python3
"""
sim_qc.py - Minimal, zero-dependency simulator and runner for .qc quantum circuits.
Designed for learning and executing 1- to 5-qubit circuits.
"""

import sys
import math
import cmath
import random

INV_SQRT2 = 1.0 / math.sqrt(2.0)

def format_complex(c, tol=1e-6):
    r, i = c.real, c.imag
    if abs(r) < tol and abs(i) < tol:
        return "0"
    if abs(i) < tol:
        return f"{r:+.4f}".rstrip('0').rstrip('.') if abs(r - round(r)) > 1e-4 else f"{int(round(r)):+d}"
    if abs(r) < tol:
        coeff = f"{i:+.4f}".rstrip('0').rstrip('.') if abs(i - round(i)) > 1e-4 else f"{int(round(i)):+d}"
        return f"{coeff}i"
    return f"({r:.4f} + {i:.4f}i)"

class QCSimulator:
    def __init__(self, qc_path):
        self.qc_path = qc_path
        self.qubits = []
        self.inputs = []
        self.gates = []
        self.parse()

    def parse(self):
        in_body = False
        with open(self.qc_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                tokens = line.split()
                if tokens[0] == '.v':
                    self.qubits = tokens[1:]
                elif tokens[0] == '.i':
                    self.inputs = tokens[1:]
                elif tokens[0] == 'BEGIN':
                    in_body = True
                elif tokens[0] == 'END':
                    in_body = False
                elif in_body:
                    gate_name = tokens[0]
                    gate_args = tokens[1:]
                    self.gates.append((gate_name, gate_args))

        if not self.qubits:
            raise ValueError("No qubits declared with .v in circuit file")

    def run(self, initial_state_bits=None, verbose=True):
        n = len(self.qubits)
        dim = 1 << n
        qubit_to_idx = {q: i for i, q in enumerate(self.qubits)}

        # Statevector initialized to |00...0> or user input
        state = [0.0 + 0.0j] * dim
        init_val = 0
        if initial_state_bits:
            for bit_pos, char in enumerate(initial_state_bits):
                if char == '1':
                    init_val |= (1 << (n - 1 - bit_pos))
        state[init_val] = 1.0 + 0.0j

        def get_bit(val, q_idx):
            # Bit index: qubit 0 is most significant bit (MSB)
            shift = n - 1 - q_idx
            return (val >> shift) & 1

        def flip_bit(val, q_idx):
            shift = n - 1 - q_idx
            return val ^ (1 << shift)

        if verbose:
            print("=" * 60)
            print(f" Quantum Circuit: {self.qc_path}")
            print(f" Qubits ({n}): {' '.join(self.qubits)}")
            print(f" Initial State: |{''.join(self.bitstring(init_val, n))}>")
            print("=" * 60)

        # Apply gates sequentially
        for step, (gate, args) in enumerate(self.gates, 1):
            next_state = [0.0 + 0.0j] * dim

            if gate in ('H', 'h'):
                target = qubit_to_idx[args[0]]
                for idx in range(dim):
                    if get_bit(idx, target) == 0:
                        paired = flip_bit(idx, target)
                        a0 = state[idx]
                        a1 = state[paired]
                        next_state[idx] += INV_SQRT2 * (a0 + a1)
                        next_state[paired] += INV_SQRT2 * (a0 - a1)

            elif gate in ('X', 'x', 'not'):
                target = qubit_to_idx[args[0]]
                for idx in range(dim):
                    next_state[flip_bit(idx, target)] = state[idx]

            elif gate in ('Z', 'z'):
                target = qubit_to_idx[args[0]]
                for idx in range(dim):
                    phase = -1.0 if get_bit(idx, target) == 1 else 1.0
                    next_state[idx] = state[idx] * phase

            elif gate in ('S', 's', 'P', 'p'):
                target = qubit_to_idx[args[0]]
                for idx in range(dim):
                    phase = 1.0j if get_bit(idx, target) == 1 else 1.0
                    next_state[idx] = state[idx] * phase

            elif gate in ('S*', 's*', 'P*', 'p*'):
                target = qubit_to_idx[args[0]]
                for idx in range(dim):
                    phase = -1.0j if get_bit(idx, target) == 1 else 1.0
                    next_state[idx] = state[idx] * phase

            elif gate in ('T', 't'):
                target = qubit_to_idx[args[0]]
                t_phase = cmath.exp(1j * math.pi / 4.0)
                for idx in range(dim):
                    phase = t_phase if get_bit(idx, target) == 1 else 1.0
                    next_state[idx] = state[idx] * phase

            elif gate in ('T*', 't*'):
                target = qubit_to_idx[args[0]]
                t_phase = cmath.exp(-1j * math.pi / 4.0)
                for idx in range(dim):
                    phase = t_phase if get_bit(idx, target) == 1 else 1.0
                    next_state[idx] = state[idx] * phase

            elif gate in ('tof', 'cnot', 'CX', 'cx'):
                if len(args) == 2:  # CNOT: control, target
                    ctrl = qubit_to_idx[args[0]]
                    target = qubit_to_idx[args[1]]
                    for idx in range(dim):
                        if get_bit(idx, ctrl) == 1:
                            next_state[flip_bit(idx, target)] = state[idx]
                        else:
                            next_state[idx] = state[idx]
                elif len(args) == 3:  # Toffoli: ctrl1, ctrl2, target
                    c1 = qubit_to_idx[args[0]]
                    c2 = qubit_to_idx[args[1]]
                    target = qubit_to_idx[args[2]]
                    for idx in range(dim):
                        if get_bit(idx, c1) == 1 and get_bit(idx, c2) == 1:
                            next_state[flip_bit(idx, target)] = state[idx]
                        else:
                            next_state[idx] = state[idx]

            elif gate in ('cz', 'CZ'):
                q1 = qubit_to_idx[args[0]]
                q2 = qubit_to_idx[args[1]]
                for idx in range(dim):
                    phase = -1.0 if (get_bit(idx, q1) == 1 and get_bit(idx, q2) == 1) else 1.0
                    next_state[idx] = state[idx] * phase

            elif gate in ('swap', 'SWAP'):
                q1 = qubit_to_idx[args[0]]
                q2 = qubit_to_idx[args[1]]
                for idx in range(dim):
                    b1 = get_bit(idx, q1)
                    b2 = get_bit(idx, q2)
                    if b1 != b2:
                        next_idx = flip_bit(flip_bit(idx, q1), q2)
                        next_state[next_idx] = state[idx]
                    else:
                        next_state[idx] = state[idx]
            else:
                print(f"Warning: Gate '{gate}' not recognized, skipping.")
                next_state = list(state)

            state = next_state
            if verbose:
                print(f"Step {step:02d} [{gate:4s} {' '.join(args):8s}] -> State: {self.format_state(state, n)}")

        return state

    def bitstring(self, val, n):
        return f"{val:0{n}b}"

    def format_state(self, state, n):
        terms = []
        for idx, amp in enumerate(state):
            prob = abs(amp) ** 2
            if prob > 1e-6:
                bits = self.bitstring(idx, n)
                terms.append(f"{format_complex(amp)} |{bits}>")
        return " + ".join(terms) if terms else "0"

    def analyze(self, state, shots=1024):
        n = len(self.qubits)
        dim = len(state)
        probs = [abs(a) ** 2 for a in state]

        print("\n" + "=" * 60)
        print(" FINAL QUANTUM STATE ANALYSIS")
        print("=" * 60)
        print(f"Dirac State Vector: |ψ⟩ = {self.format_state(state, n)}")
        print("\nProbability Distribution:")
        print(f"  {'Basis State':<12} | {'Amplitude':<22} | {'Probability':<12}")
        print("  " + "-" * 52)
        for idx in range(dim):
            bits = self.bitstring(idx, n)
            amp_str = f"{state[idx].real:+.4f}{state[idx].imag:+.4f}i"
            print(f"  |{bits}>        | {amp_str:<22} | {probs[idx] * 100:6.2f}%")

        # Simulate measurement shots
        counts = {}
        for _ in range(shots):
            r = random.random()
            cum = 0.0
            chosen = 0
            for idx, p in enumerate(probs):
                cum += p
                if r <= cum:
                    chosen = idx
                    break
            b = self.bitstring(chosen, n)
            counts[b] = counts.get(b, 0) + 1

        print(f"\nMeasurement Simulation ({shots} shots):")
        for bits in sorted(counts.keys()):
            bar = "█" * int(counts[bits] / shots * 40)
            print(f"  |{bits}> : {counts[bits]:4d} shots ({counts[bits]/shots*100:5.1f}%) {bar}")
        print("=" * 60)

if __name__ == '__main__':
    circuit_file = sys.argv[1] if len(sys.argv) > 1 else 'bell.qc'
    init_state = sys.argv[2] if len(sys.argv) > 2 else None
    sim = QCSimulator(circuit_file)
    final_state = sim.run(initial_state_bits=init_state)
    sim.analyze(final_state)

