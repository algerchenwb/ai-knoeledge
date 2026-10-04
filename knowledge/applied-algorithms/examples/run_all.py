"""Run all numbered examples; return failure if any subprocess fails."""
from pathlib import Path
import subprocess
import sys

for script in sorted(Path(__file__).parent.glob('[0-9][0-9]_*.py')):
    subprocess.run([sys.executable, str(script)], check=True)
