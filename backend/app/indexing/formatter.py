"""Build the final alphabetical, grouped index structure and its text rendering."""
from __future__ import annotations


def format_index(topic_pages: dict[str, list[int]]) -> dict:
    """Return a structured index grouped by starting character.

    Shape::

        {
          "groups": [
            {"letter": "A", "entries": [{"topic": "Arrays", "pages": [1,2,5]}]},
            ...
          ],
          "total_topics": 12,
          "total_pages_referenced": 9
        }
    """
    entries = sorted(
        ({"topic": t, "pages": sorted(set(p))} for t, p in topic_pages.items()),
        key=lambda e: e["topic"].lower(),
    )

    groups: list[dict] = []
    current_letter: str | None = None
    for entry in entries:
        letter = _group_letter(entry["topic"])
        if letter != current_letter:
            groups.append({"letter": letter, "entries": []})
            current_letter = letter
        groups[-1]["entries"].append(entry)

    all_pages = {p for pages in topic_pages.values() for p in pages}
    return {
        "groups": groups,
        "total_topics": len(entries),
        "total_pages_referenced": len(all_pages),
    }


def format_index_text(index: dict, *, width: int = 40) -> str:
    """Render the structured index as the classic dotted-leader text format."""
    lines: list[str] = []
    for group in index.get("groups", []):
        lines.append(group["letter"])
        for entry in group["entries"]:
            topic = entry["topic"]
            pages = ", ".join(str(p) for p in entry["pages"])
            dots = "." * max(3, width - len(topic))
            lines.append(f"{topic} {dots} {pages}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _group_letter(topic: str) -> str:
    first = topic.strip()[:1].upper()
    return first if first.isalpha() else "#"
