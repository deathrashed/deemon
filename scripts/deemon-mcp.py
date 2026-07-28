#!/usr/bin/env python3
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from deemon.integrations.mcp import main


if __name__ == "__main__":
    main()
