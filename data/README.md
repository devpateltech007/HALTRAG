# Data Directory

## What Is Included

- `sample_corpus.json` is the local retrieval corpus used by the app.
- `custom_50_questions.json` is our custom 50-question evaluation set.

Each custom question includes the question, expected answer, expected supporting document ids, domain, and difficulty.

## Runtime Knowledge Uploads

The app can append new knowledge to `sample_corpus.json`. Uploaded text is chunked first, then each chunk is stored as a retrievable document with `source=user_upload` or `source=frontend_upload`.

Use the CLI directly.

```bash
python scripts/add_knowledge.py --file notes.txt --title "Lecture Notes" --domain custom --json
```

The model is not retrained. Only the retrieval corpus is updated.

## External Datasets

Large public datasets are not committed to this repo. PubMedQA, TriviaQA, HotpotQA, and QASPER can still be used for later experiments through preprocessing scripts, but the current project demo is centered on the custom 50-question set and dynamic knowledge uploads.
