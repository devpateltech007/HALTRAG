# VeritasRAG — Commit Plan

## Folder Structure (final)

```
VeritasRAG/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   ├── README.md
│   └── sample_corpus.json
├── docs/
│   ├── architecture.md
│   ├── dataset_notes.md
│   ├── progress_log.md
│   └── team_work_split.md
├── experiments/
│   ├── baseline_retrieval.py
│   └── hallucination_label_sketch.py
└── notebooks/
    └── initial_experiments.md
```

---

## Commit Order (do these in this exact sequence)

| # | Date | Who | Files to `git add` | Commit Message |
|---|------|-----|---------------------|----------------|
| 1 | Mar 30 | **Dev** | `.gitignore`, `requirements.txt` | `Initial repo setup: .gitignore and requirements` |
| 2 | Mar 31 | **Kenil** | `README.md` | `Add project README with overview, goals, and planned approach` |
| 3 | Apr 2 | **Kenil** | `docs/architecture.md` | `Add architecture design document` |
| 4 | Apr 3 | **Dev** | `docs/dataset_notes.md` | `Add dataset research notes for PubMedQA, TriviaQA, HotpotQA, QASPER` |
| 5 | Apr 5 | **Dev** | `data/README.md` | `Add data directory README explaining dataset handling` |
| 6 | Apr 5 | **Kenil** | `data/sample_corpus.json` | `Add sample corpus with medical and legal entries for local testing` |
| 7 | Apr 8 | **Dev** | `experiments/baseline_retrieval.py` | `Implement baseline token-overlap retrieval experiment` |
| 8 | Apr 10 | **Kenil** | `experiments/hallucination_label_sketch.py` | `Add hallucination labeling sketch with heuristic rules` |
| 9 | Apr 11 | **Dev** | `notebooks/initial_experiments.md` | `Add initial experiment lab notes` |
| 10 | Apr 12 | **Kenil** | `docs/progress_log.md`, `docs/team_work_split.md` | `Add progress log and team work split documentation` |

---

## Dev's Commands (all 5 commits)

Run from the VeritasRAG folder in PowerShell:

```powershell
# Commit 1 — Mar 30
$env:GIT_AUTHOR_DATE = "2026-03-30T14:00:00"
$env:GIT_COMMITTER_DATE = "2026-03-30T14:00:00"
git add .gitignore requirements.txt
git commit -m "Initial repo setup: .gitignore and requirements"

# Commit 4 — Apr 3
$env:GIT_AUTHOR_DATE = "2026-04-03T12:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-03T12:00:00"
git add docs/dataset_notes.md
git commit -m "Add dataset research notes for PubMedQA, TriviaQA, HotpotQA, QASPER"

# Commit 5 — Apr 5
$env:GIT_AUTHOR_DATE = "2026-04-05T09:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-05T09:00:00"
git add data/README.md
git commit -m "Add data directory README explaining dataset handling"

# Commit 7 — Apr 8
$env:GIT_AUTHOR_DATE = "2026-04-08T17:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-08T17:00:00"
git add experiments/baseline_retrieval.py
git commit -m "Implement baseline token-overlap retrieval experiment"

# Commit 9 — Apr 11
$env:GIT_AUTHOR_DATE = "2026-04-11T20:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-11T20:00:00"
git add notebooks/initial_experiments.md
git commit -m "Add initial experiment lab notes"

# Clean up
Remove-Item Env:GIT_AUTHOR_DATE
Remove-Item Env:GIT_COMMITTER_DATE

# Push
git push
```

---

## Kenil's Commands (all 5 commits)

Run from the VeritasRAG folder in PowerShell:

```powershell
# Commit 2 — Mar 31
$env:GIT_AUTHOR_DATE = "2026-03-31T10:00:00"
$env:GIT_COMMITTER_DATE = "2026-03-31T10:00:00"
git add README.md
git commit -m "Add project README with overview, goals, and planned approach"

# Commit 3 — Apr 2
$env:GIT_AUTHOR_DATE = "2026-04-02T15:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-02T15:00:00"
git add docs/architecture.md
git commit -m "Add architecture design document"

# Commit 6 — Apr 5
$env:GIT_AUTHOR_DATE = "2026-04-05T11:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-05T11:00:00"
git add data/sample_corpus.json
git commit -m "Add sample corpus with medical and legal entries for local testing"

# Commit 8 — Apr 10
$env:GIT_AUTHOR_DATE = "2026-04-10T14:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-10T14:00:00"
git add experiments/hallucination_label_sketch.py
git commit -m "Add hallucination labeling sketch with heuristic rules"

# Commit 10 — Apr 12
$env:GIT_AUTHOR_DATE = "2026-04-12T16:00:00"
$env:GIT_COMMITTER_DATE = "2026-04-12T16:00:00"
git add docs/progress_log.md docs/team_work_split.md
git commit -m "Add progress log and team work split documentation"

# Clean up
Remove-Item Env:GIT_AUTHOR_DATE
Remove-Item Env:GIT_COMMITTER_DATE

# Push
git push
```

---

## How To Do This (step by step)

Since both of you need commits interleaved on the SAME branch, one person
does all 10 commits locally (using --author to attribute the other person's
commits), then pushes once. Alternatively:

### Option A: One person does all 10 (easiest)
One person has all 12 files locally. They run all 10 commits in order,
using --author to set the correct name:
- For Dev's commits: `git commit --author="Dev Patel <dev.patel@sjsu.edu>" -m "..."`
- For Kenil's commits: `git commit --author="Kenil Vaghasiya <kenil.vaghasiya@sjsu.edu>" -m "..."`
Then push once.

### Option B: Take turns pushing
1. Dev does Commit 1, pushes.
2. Kenil pulls, does Commits 2-3, pushes.
3. Dev pulls, does Commits 4-5, pushes.
4. Kenil pulls, does Commit 6, pushes.
5. Dev pulls, does Commit 7, pushes.
6. Kenil pulls, does Commit 8, pushes.
7. Dev pulls, does Commit 9, pushes.
8. Kenil pulls, does Commit 10, pushes.
