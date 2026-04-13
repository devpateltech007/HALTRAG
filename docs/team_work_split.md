# Team Work Split

## Team Members

- **Dev Patel**
- **Kenil Vaghasiya**

## Shared Work

Both team members contributed equally to the following activities:

- **Brainstorming** — joint meetings to define the project scope, target domain, and research questions.
- **Literature review** — both read the core papers (RAG, hallucination surveys) and discussed takeaways.
- **Architecture design** — whiteboarded the pipeline together; both contributed ideas on hallucination taxonomy.
- **Dataset exploration** — each person explored 2 of the 4 candidate datasets and we compared notes.
- **Code review** — reviewed each other's experiment scripts before committing.
- **Documentation** — both contributed to the README and design docs.

## Individual Focus Areas

| Area | Primary Owner | Notes |
|------|---------------|-------|
| Retrieval module & baselines | Dev | Implemented `baseline_retrieval.py`; will lead BM25 and dense retrieval integration |
| Hallucination analysis & typing | Kenil | Implemented `hallucination_label_sketch.py`; will lead NLI-based detection work |
| Dataset preprocessing | Dev | Explored PubMedQA and TriviaQA; will handle data download and preprocessing scripts |
| Architecture documentation | Kenil | Drafted `architecture.md` and the pipeline diagram |
| Experiment logging & notes | Dev | Primary author of `initial_experiments.md` |
| Progress tracking | Kenil | Primary author of `progress_log.md` |
| Repository setup | Dev | Set up repo structure, `.gitignore`, `requirements.txt` |
| Sample data creation | Kenil | Created `sample_corpus.json` with medical/legal examples |

## Planned Split for Next Phase

| Upcoming Task | Assigned To |
|---------------|-------------|
| Integrate rank_bm25 | Dev |
| Download & preprocess PubMedQA | Dev |
| NLI-based hallucination detection | Kenil |
| Generator module (LLM integration) | Both |
| Evaluation framework | Both |
| Annotation guidelines for hallucination typing | Kenil |
| Dense retrieval experiments | Dev |

## Collaboration Process

- We meet twice a week (Tuesdays and Thursdays) to sync progress.
- We use GitHub issues to track tasks and a shared Google Doc for meeting notes.
- Code is reviewed by the other person before merging to main.
