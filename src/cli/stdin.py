from __future__ import annotations

import json
import sys


def read_stdin_field(field: str) -> list[str]:
    if sys.stdin.isatty():
        return []
    values = []
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if field not in obj:
                raise ValueError(f"stdin line missing field '{field}': {line}")
            values.append(obj[field])
    except EOFError:
        pass
    return values
