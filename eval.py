"""Simple template for evaluating autopilot parameter sets"""

import os
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm

SIM_PATH = "./sim"
NUM_RUNS = 10000
QUANTIZE = 3
MAX_WORKERS = os.cpu_count()
FPS = 10

params = {
    "ATTITUDE_KP": 2.200390037976687,
    "ATTITUDE_KD": 3.8210788642448072,
    "LATERAL_KP": 0.003937509152103991,
    "LATERAL_KD": 0.025660669600121835,
    "MAX_LEAN_COARSE": 45,
    "MAX_LEAN_BURN": 28.730191489666343,
    "MAX_LEAN_FINAL": 6.029378989818157,
    "PHASE_BURN_ALT": 100,
    "PHASE_FINAL_ALT": 21.735436731202054,
    "BURN_MIN_VY": 9.02989683134981,
    "BURN_SAFETY_MARGIN": 15,
    "BURN_THRESHOLD_FRACTION": 0.8060667716427831,
    "FINAL_TARGET_VY": 1.416868006870908,
    "RCS_DEADBAND_COARSE": 0.01,
    "RCS_DEADBAND_BURN": 0.03538529657425334,
    "RCS_DEADBAND_FINAL": 0.025287131747565406,
}

base_args = ["--fps", str(FPS), "--headless", "--autopilot"]
for k, v in params.items():
    base_args.extend([f"--{k.lower()}", str(round(v, QUANTIZE))])


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

    print()
    for k, v in params.items():
        print(f"{k} = {round(v, QUANTIZE)}")


if __name__ == "__main__":
    main()
