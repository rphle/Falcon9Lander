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
FPS = (5, 30)

params = {
    "ATTITUDE_KP": 2.4115,
    "ATTITUDE_KD": 4.6485,
    "LATERAL_KP": 0.0032,
    "LATERAL_KD": 0.02,
    "MAX_LEAN_COARSE": 59.5399,
    "MAX_LEAN_BURN": 25.2165,
    "MAX_LEAN_FINAL": 27.6865,
    "PHASE_BURN_ALT": 145.0998,
    "PHASE_FINAL_ALT": 2.0,
    "BURN_MIN_VY": 3.8216,
    "BURN_SAFETY_MARGIN": 0.0161,
    "BURN_THRESHOLD_FRAC": 0.3155,
    "FINAL_TARGET_VY": 1.1952,
    "RCS_DEADBAND_COARSE": 0.2109,
    "RCS_DEADBAND_BURN": 0.0439,
    "RCS_DEADBAND_FINAL": 0.0914,
}


template = """# Drive rocket to target angle, damp spin
ATTITUDE_KP = arg("attitude_kp", {ATTITUDE_KP}) -> rad^(-1)
ATTITUDE_KD = arg("attitude_kd", {ATTITUDE_KD}) -> s*rad^(-1)

# Lateral correction: desired lean = KP*x_error + KD*vx
LATERAL_KP = arg("lateral_kp", {LATERAL_KP}) -> m^(-1)
LATERAL_KD = arg("lateral_kd", {LATERAL_KD}) -> s*m^(-1)

# Max lean angles per phase
AUTOPILOT_MAX_LEAN_COARSE = arg("max_lean_coarse", {MAX_LEAN_COARSE}) -> °
AUTOPILOT_MAX_LEAN_BURN   = arg("max_lean_burn", {MAX_LEAN_BURN}) -> °
AUTOPILOT_MAX_LEAN_FINAL  = arg("max_lean_final", {MAX_LEAN_FINAL}) -> °

# Phase Thresholds
PHASE_BURN_ALT = arg("phase_burn_alt", {PHASE_BURN_ALT}) -> m
PHASE_FINAL_ALT = arg("phase_final_alt", {PHASE_FINAL_ALT}) -> m
BURN_MIN_VY = arg("burn_min_vy", {BURN_MIN_VY}) -> m/s
BURN_SAFETY_MARGIN = arg("burn_safety_margin", {BURN_SAFETY_MARGIN}) -> m
BURN_THRESHOLD_FRACTION = arg("burn_threshold_fraction", {BURN_THRESHOLD_FRAC})
FINAL_TARGET_VY = arg("final_target_vy", {FINAL_TARGET_VY}) -> m/s

# RCS Deadbands (lower = more precise)
RCS_DEADBAND_COARSE = arg("rcs_deadband_coarse", {RCS_DEADBAND_COARSE})
RCS_DEADBAND_BURN   = arg("rcs_deadband_burn", {RCS_DEADBAND_BURN})
RCS_DEADBAND_FINAL  = arg("rcs_deadband_final", {RCS_DEADBAND_FINAL})
"""


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

    print(template.format(**{k: round(v, QUANTIZE) for k, v in params.items()}))
    print("========================")
    if scores:
        landing_accuracy = sum(1 for s in scores if s > 0) / len(scores)
        average_score = sum(scores) / len(scores)
        print(f"\nLanding accuracy: {landing_accuracy * 100:.2f}%")
        print(f"Average score: {average_score:.2f}")
        print(f"Max score: {max(scores)}")
        print(f"Min score: {min(s for s in scores if s > 0)}")


if __name__ == "__main__":
    main()
