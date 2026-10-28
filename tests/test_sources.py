"""The source list rule (sources/README.md): every unique source is listed once.

Checked automatically: every registered source ID in the ontology and the
datasets, and every link in the course notes' `Research Materials`. Sources cited
only in prose (decisions, reviews, commits) are checked by the reviewer.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIST = (ROOT / "sources" / "SOURCES.md").read_text(encoding="utf-8")


def registered_sources():
    files = [ROOT / "ontology" / "hip.yaml",
             *sorted((ROOT / "ontology" / "quantitative_data").glob("*.yaml"))]
    ids = {}
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for sid, entry in (data.get("sources") or {}).items():
            ids[sid] = entry
    return ids


def test_every_registered_source_is_listed_once():
    sources = registered_sources()
    assert sources
    for sid, entry in sources.items():
        assert LIST.count(f"`{sid}`") == 1, f"{sid} must appear exactly once in sources/SOURCES.md"
        if entry.get("url"):
            assert entry["url"].rstrip("/") in LIST, f"{sid}: registry URL missing from the list"


def test_every_research_materials_link_is_listed():
    text = (ROOT / "Research Materials").read_text(encoding="utf-8")
    links = [u for u in re.findall(r"https?://\S+", text)]
    assert links
    for url in links:
        assert url.rstrip("/") in LIST, f"{url} from Research Materials is missing from sources/SOURCES.md"


def test_no_source_id_listed_that_the_data_does_not_register():
    listed = set(re.findall(r"`(SRC:[A-Z0-9_]+)`", LIST))
    assert listed == set(registered_sources())
