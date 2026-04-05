# Data Directory

## Why Full Datasets Are Not Included

The datasets we're evaluating (PubMedQA, TriviaQA, HotpotQA, QASPER) are large and hosted by their respective maintainers. Including them in the repository would be impractical and violate best practices for version control.

- **PubMedQA**: ~200MB+ (artificially generated split)
- **TriviaQA**: ~2.5GB (with evidence documents)
- **HotpotQA**: ~600MB (fullwiki setting)
- **QASPER**: ~300MB (full papers)

## What Is Included

- **`sample_corpus.json`** — A small, hand-crafted corpus of 8 entries with medical and legal content. This is used for local development and testing of the retrieval and hallucination analysis prototypes.

## How Datasets Will Be Used Later

Once we move past the prototyping phase:

1. We'll add download and preprocessing scripts under a `scripts/` directory.
2. Raw data will be stored locally in `data/raw/` (gitignored).
3. Processed data will go in `data/processed/` (also gitignored).
4. Only small sample files and metadata will be committed to the repo.
