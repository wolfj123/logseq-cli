from __future__ import annotations

import json


def format_output(
    data: dict | list,
    fields: list[str] | None = None,
    plain: bool = False,
) -> str:
    items = data if isinstance(data, list) else [data]

    if fields:
        items = [{k: item[k] for k in fields if k in item} for item in items]

    if plain:
        blocks = []
        for item in items:
            lines = [f"{k}: {v}" for k, v in item.items()]
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks) + "\n"

    return "\n".join(json.dumps(item) for item in items) + "\n"
