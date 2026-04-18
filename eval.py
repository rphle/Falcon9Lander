"""Simple template for evaluating autopilot parameter sets"""

import os
import random
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm

SIM_PATH = "./sim"
NUM_RUNS = 10000
QUANTIZE = 3
MAX_WORKERS = os.cpu_count()
FPS = (5, 5)

params = {
    "ATTITUDE_KP": 1.6731,
    "ATTITUDE_KD": 1.5037,
    "LATERAL_KP": 0.0017,
    "LATERAL_KD": 0.0139,
    "MAX_LEAN_COARSE": 24.3468,
    "MAX_LEAN_BURN": 12.7555,
    "MAX_LEAN_FINAL": 16.2987,
    "PHASE_BURN_ALT": 212.3818,
    "PHASE_FINAL_ALT": 10.0000,
    "BURN_MIN_VY": 1.0070,
    "BURN_SAFETY_MARGIN": 5.3543,
    "BURN_THRESHOLD_FRAC": 0.5173,
    "FINAL_TARGET_VY": 1.5661,
    "RCS_DEADBAND_COARSE": 0.0540,
    "RCS_DEADBAND_BURN": 0.0213,
    "RCS_DEADBAND_FINAL": 0.0081,
}

base_args = ["--autopilot", "--headless"]
for k, v in params.items():
    base_args.extend([f"--{k.lower()}", str(round(v, QUANTIZE))])


def run_sim(_):
    """Function to run a single simulation instance."""
    try:
        result = subprocess.run(
            [SIM_PATH] + base_args + ["--fps", str(random.randint(*FPS))],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        match = re.search(r"SCORE=(\d+)", result.stdout)
        return int(match.group(1)) if match else 0
    except Exception:
        return 0


def main():
    scores = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_sim, i) for i in range(NUM_RUNS)]
        for future in tqdm(as_completed(futures), total=NUM_RUNS, desc="Simulating"):
            scores.append(future.result())

    if scores:
        landing_accuracy = sum(1 for s in scores if s > 0) / len(scores)
        average_score = sum(scores) / len(scores)
        print(f"\nLanding accuracy: {landing_accuracy * 100:.2f}%")
        print(f"Average score: {average_score:.2f}")
        print(f"Max score: {max(scores)}")

    print()
    for k, v in params.items():
        print(f"{k} = {round(v, QUANTIZE)}")


if __name__ == "__main__":
    main()
