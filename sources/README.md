# Sources

One place to find every source this project has used for its research. The list itself is [`SOURCES.md`](SOURCES.md).

## The rule

**Every unique source gets listed once in `SOURCES.md`.** That includes:

- every source registered in the data (the `sources:` blocks of `ontology/*.yaml` and `ontology/quantitative_data/*.yaml`);
- every source cited in `docs/DECISIONS.md`, a review in `docs/reviews/`, or a commit or PR;
- research and background links from the course notes (`Notes`, `Research Materials`);
- sources that were cited but not opened (mark them **Cited, not accessed**).

A source used several times is still listed once; add the new use to its **Used for** column.

## How to add a source

Whoever first uses a source adds it in the same PR that uses it. The builder does this; the reviewer checks it.

1. Check `SOURCES.md` first. If the source is already there, only add the new use.
2. Otherwise add one row in the right section, with:
   - **ID:** the registry ID (`SRC:...`) if the data cites it, otherwise `—`;
   - **Source:** authors, year, title, venue, as published. Do not guess missing details; write "details not recorded";
   - **Link:** DOI or stable URL (PubMed Central, publisher, official documentation);
   - **Used for:** what the project used it for, with the decision or file (for example `D-056`, `gluteus_maximus.yaml`);
   - **Status:** `Read` (opened and used), `Cited, not accessed` (named because another source relies on it), or `Background` (read for context, no claim depends on it).
3. Keep rows in alphabetical order by first author or title within each section.

`tests/test_sources.py` fails if a registered `SRC:` ID or a link in `Research Materials` is missing from `SOURCES.md`, so the rule is checked on every test run. Sources cited only in prose (decisions, reviews, commits) are not checked automatically; the reviewer checks those.

This list records where information came from. It does not say a source supports any particular value; that is recorded on each datum and in the decision log.
