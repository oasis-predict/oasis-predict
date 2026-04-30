import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")

PIPELINE = [
    "kalshi_signal_engine.py",
    "kalshi_position_sizer.py",
    "kalshi_trade_sheet_generator.py",
    "kalshi_trade_blotter.py",
    "kalshi_portfolio_summary.py",
]


def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        print(f"[ERROR] Script not found: {script_path}")
        return False

    print("\n" + "=" * 100)
    print(f"RUNNING: {script_name}")
    print("=" * 100)

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print(f"[ERROR] {script_name} failed with exit code {result.returncode}")
        return False

    print(f"[OK] {script_name} completed successfully.")
    return True


def main():
    print("=" * 100)
    print("KALSHI DAILY RUNNER")
    print("=" * 100)
    print(f"Project root: {PROJECT_ROOT}")

    for script_name in PIPELINE:
        success = run_script(script_name)
        if not success:
            print("\nPipeline stopped because of an error.")
            return

    print("\n" + "=" * 100)
    print("DAILY PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 100)


if __name__ == "__main__":
    main()
