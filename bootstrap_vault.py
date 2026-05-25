"""Create the vault directory structure and seed files."""
from __future__ import annotations
import os
from pathlib import Path


def bootstrap(vault_path: str) -> None:
    root = Path(vault_path)
    dirs = [
        "raw/articles",
        "raw/papers",
        "raw/assets",
        "wiki/entities",
        "wiki/concepts",
        "wiki/sources",
        "wiki/answers",
        "prompts",
        "skills",
        "agents",
        "feed",
        "experiments",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"  created {d}/")

    index = root / "wiki" / "index.md"
    if not index.exists():
        index.write_text(
            "---\ntitle: Content Catalog\ndate: 2026-05-25\n---\n\n# Content Catalog\n\n"
            "_No pages yet. Run INGEST to add content._\n",
            encoding="utf-8",
        )
        print("  created wiki/index.md")

    log = root / "wiki" / "log.md"
    if not log.exists():
        log.write_text(
            "---\ntitle: Operation Log\n---\n\n# Operation Log\n\n",
            encoding="utf-8",
        )
        print("  created wiki/log.md")

    print(f"\nVault bootstrapped at: {root.resolve()}")


if __name__ == "__main__":
    vault_path = os.getenv("VAULT_PATH", "./vault")
    print(f"Bootstrapping vault at: {vault_path}")
    bootstrap(vault_path)
