"""Simple template for evaluating autopilot parameter sets"""

import os
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm

SIM_PATH = "./sim"
NUM_RUNS = 500
MAX_WORKERS = os.cpu_count()
FPS = 10

params = {
    "ATTITUDE_KP": 3.5,
    "ATTITUDE_KD": 2.5,
    "LATERAL_KP": 0.025,
    "LATERAL_KD": 0.085,
    "MAX_LEAN_COARSE": 25,
    "MAX_LEAN_BURN": 15,
    "MAX_LEAN_FINAL": 10,
    "PHASE_BURN_ALT": 180,
    "PHASE_FINAL_ALT": 35,
    "BURN_MIN_VY": 3,
    "BURN_SAFETY_MARGIN": 4,
    "BURN_THRESHOLD_FRACTION": 0.85,
    "FINAL_TARGET_VY": 4,
    "RCS_DEADBAND_COARSE": 0.08,
    "RCS_DEADBAND_BURN": 0.04,
    "RCS_DEADBAND_FINAL": 0.01,
}

base_args = ["--fps", str(FPS), "--headless", "--autopilot"]
for k, v in params.items():
    base_args.extend([f"--{k.lower()}", str(v)])


def run_sim(_):
    """Function to run a single simulation instance."""
    try:
        result = subprocess.run(
            [SIM_PATH] + base_args,
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


if __name__ == "__main__":
    main()
