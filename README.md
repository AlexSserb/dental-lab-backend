# The system of accounting and planning of order fulfillment in the dental laboratory

## Table of contents
* [Introduction](#introduction)
* [Technologies](#technologies)
* [Tools](#tools)
* [Installation](#installation)
* [Knowledge base (RAG)](#knowledge-base)

<a name="introduction"></a>
## Introduction

The system is designed for a dental laboratory. The laboratory receives orders from clients (doctors). Each order consists of products. To perform each product, several dental technicians must perform a sequence of operations. After completing all the work, the doctor accepts and pays for the products.

There are 3 roles in the system:
1. *Doctor*. The doctor can register in the system, place orders and view the progress of his orders.
2. *Dental technician*. A dental technician can receive operations to perform and mark their statuses. There are 4 departments according to which they perform different operations:
   - *Modeling Department.*
   - *CAD/CAM Department.*
   - *Ceramics Department.*
   - *Prosthetics Department.*
3. *Laboratory administrator*. The administrator can view the progress of work, place and adjust orders, and distribute operations to technicians.

<a name="technologies"></a>
## Technologies
* Backend:
  - Python 3.13
  - Django 5
  - Django REST Framework
  - DRF-spectacular (OpenAPI schema generation)
  - django-pgtrigger, django-pghistory
* Frontend:
  - TypeScript
  - React 18
  - Axios
  - Mantine
  - OpenAPI Generator (for automated TS client generation)
* Database:
  - PostgreSQL

<a name="tools"></a>
## Tools
* Git
* Pycharm
* WebStorm
* DataGrip
* Npm
* Pip

<a name="installation"></a>
## Installation
1. Clone backend and frontend repositories:
    ```commandline
    git clone https://github.com/AlexSserb/dental-lab-backend.git
    git clone https://github.com/AlexSserb/dental-lab-frontend.git
    ```
2. Create and configure the database.

    2.1. Ensure your PostgreSQL server is running.

    2.2. Create a database with your user as the owner.

    2.3. In the backend repo copy `.env.example` file as `.env` and update with the following fields with your database credentials:
    ```
    DATABASE_NAME=DatabaseName
    DATABASE_USER=DatabaseUser
    DATABASE_PASSWORD=DatabasePassword
    SECRET_KEY=your_secret_key
    ```

3. Run the backend part.

    3.1. Create and activate virtual environment

    3.2. Install requirements

    3.3. Create migrations and load fixtures:
    ```commandline
    python manage.py makemigrations core accounts orders works operations
    python manage.py migrate
    python manage.py loaddata groups.json users.json statuses.json object_types.json dental_lab_data.json
    ```
    3.4. Start the backend server:
    ```commandline
    python manage.py runserver
    ```

4. Run the frontend part.

    4.1. In the frontend repo copy `.env.example` file as `.env` and update with the following fields with your backend server credentials:
    ```
    VITE_API_URL=http://example.com/
    ```

    4.2. Start the frontend server.
    ```commandline
    npm i
    npm start
    ```

<a name="knowledge-base"></a>
## Knowledge base (RAG)

Technicians and administrators can ask the laboratory knowledge base a question in natural language
(e.g. *"Что делать, если скол керамики после обжига?"*) and get an answer **with citations to the source documents**.
This is Retrieval-Augmented Generation: the model does not answer from memory, it answers from the document
fragments that were found for the question.

Questions about live data ("Which orders are overdue?") are **not** for the knowledge base, they are database queries.

### How it works

```
INGEST (offline, `manage.py ingest_knowledge`)
  documents/knowledge_base/*.md
     -> parse frontmatter -> split into chunks by "##" sections -> embed each chunk (bge-m3)
     -> Document + Chunk rows in PostgreSQL (vector(1024) column + HNSW index)

ASK (online, POST /api/knowledge/ask/)
  question --embed (bge-m3)--> vector
     -> pgvector: top-k nearest chunks by cosine distance (optionally filtered by department)
     -> drop chunks farther than KNOWLEDGE_MAX_DISTANCE  (nothing left -> "no information", LLM is NOT called)
     -> prompt = rules + numbered fragments [1]..[k] + question (plain TEXT, never vectors)
     -> chat model (qwen2.5:3b-instruct) writes the answer and cites fragments as [1], [2]
     -> response = answer + sources (fragment text, document, `cited` flag)
```

Two different models are involved: the **embedding model** (`bge-m3`) turns text into vectors for *finding*
fragments, the **chat model** (`AI_MODEL`) reads the found text and *writes* the answer. Vectors of different
embedding models are not comparable, so the same model must be used for ingest and for questions.

### Corpus

Markdown files in `documents/knowledge_base/` (procedures, materials, defect reports). Each file starts with
frontmatter, which becomes searchable metadata and the citation title:

```markdown
---
title: Скол керамики после обжига
doc_type: defect            # procedure | material | defect
operation_type: Керамика    # Модели | CAD/CAM | Керамика | Протезирование
---
# Скол керамики после обжига

## Причины
...
```

Write each section so it makes sense on its own: a `##` section is the unit that gets retrieved.
The current corpus is synthetic (study project) and must not be used as real clinical guidance.

### Setup

1. The database must have the `pgvector` extension: the compose file uses the `pgvector/pgvector:pg17` image
   and the first `knowledge` migration runs `CREATE EXTENSION vector`.
2. Pull the models into Ollama:
   ```commandline
   ollama pull bge-m3
   ollama pull qwen2.5:3b-instruct
   ```
3. Configure `.env` (see `.env.example`):

   | Variable | Default | Meaning |
   |---|---|---|
   | `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL` | | chat model endpoint (shared with the order-draft feature) |
   | `EMBEDDING_MODEL` | `bge-m3` | embedding model; its output size must equal `Chunk.embedding` dimensions (1024) |
   | `KNOWLEDGE_TOP_K` | `4` | fragments given to the LLM |
   | `KNOWLEDGE_MAX_DISTANCE` | `0.55` | cosine distance above which a fragment is considered unrelated |
   | `KNOWLEDGE_ASK_RATE` | `60/hour` | per-user throttle of the ask endpoint |

4. Apply migrations and load the corpus:
   ```commandline
   python manage.py migrate
   python manage.py ingest_knowledge
   ```

### Commands

#### `ingest_knowledge`

Chunks, embeds and stores the knowledge base. Safe to run repeatedly: unchanged files are skipped, changed files
are re-embedded, files that no longer exist are removed from the database.

```commandline
python manage.py ingest_knowledge                    # sync documents/knowledge_base
python manage.py ingest_knowledge --force            # re-embed everything (e.g. after changing the chunking or the model)
python manage.py ingest_knowledge --path /some/dir   # another folder
```

If you change `EMBEDDING_MODEL` to one with a different vector size, change `dimensions` in `Chunk.embedding`,
create a migration and run `ingest_knowledge --force`.

#### `eval_retrieval`

Measures **retrieval quality only** (the LLM is not involved): for every question in
`knowledge/evals/retrieval_questions.json` it searches the knowledge base and checks whether the expected source
document is among the top results. Run it after every change to chunking, the embedding model or the search
(for example when adding hybrid search) and compare the numbers.

```commandline
python manage.py eval_retrieval                      # failures + summary
python manage.py eval_retrieval --verbose            # every question
python manage.py eval_retrieval --questions my.json  # another question set
```

Example output:

```
Answerable questions: 32
hit rate @1: 100%
hit rate @3: 100%
hit rate @5: 100%
MRR:          1.000
Best distance for unanswerable questions: 0.634, 0.581 (answerable: min 0.209, max 0.489)
```

* **hit rate @k** - share of questions whose expected document is among the top k *distinct documents*.
* **MRR** - mean of 1/rank of the first correct document (1.0 = always first).
* Per-question status: `OK` (rank 1), `#n` (found at rank n), `MISS` (not found), `N/A` (unanswerable on purpose).
* **Unanswerable questions** (`"expected": []`) are excluded from the metrics. Their best distance is printed next
  to the range of real questions, which is how `KNOWLEDGE_MAX_DISTANCE` is calibrated: it should sit in the gap
  between the two.

Add a case by appending to the JSON file:

```json
{"question": "Как хранить циркониевые диски?", "expected": ["materials/zirconia-discs.md"]}
```

Paths are relative to `documents/knowledge_base/`. A good question set contains hard cases (typos, synonyms,
colloquial wording, near-duplicate topics); an easy set scores 100% and cannot show improvements.

Run the commands in Docker with `docker compose exec backend python manage.py <command>`. The image copies the
code and `documents/` at build time, so rebuild (`docker compose up -d --build`) after changing them.
