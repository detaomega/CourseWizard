# Quick Start Guide

## Setup

1.  **Start Qdrant:**
    ```bash
    # Ensure Docker is running
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```
    (Or `docker compose up -d` if using a `docker-compose.yml` for Qdrant)

2.  **Install Dependencies:**
    (From project root)
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database (Load Data):**
    (From `database` directory)
    ```bash
    python scripts/embed_upload.py
    ```

4.  **Start API Service:**
    (From `database` directory)
    ```bash
    python api/api.py
    ```
    (Development with Uvicorn: `uvicorn api.api:app --reload`)

## Verify Installation

(Run from `database` directory)
- **Test Query:** `python test/test_query.py`
- **Test API:** `python test/test_api.py`
- **Interactive Query:** `python test/test_query_interact.py`

## Database Management

(Run from `database` directory)
- **Reset DB:** `python scripts/reset_db.py`
- **Reset & Reload:** `python scripts/reset_db.py && python scripts/embed_upload.py`

## Services

- **Course API Docs:** `http://localhost:8000/docs`
- **Qdrant Dashboard:** `http://localhost:6334`
- **Qdrant API:** `http://localhost:6333` 