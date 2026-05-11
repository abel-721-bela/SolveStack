import os
import subprocess

diagrams_dir = "docs/diagrams"
os.makedirs(diagrams_dir, exist_ok=True)

diagrams = {
    "system_architecture": """graph TD
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef external fill:#8b5cf6,stroke:#5b21b6,stroke-width:2px,color:#fff

    subgraph "Frontend Applications"
        WebUI["Web Application (React)"]:::frontend
        MobileUI["Mobile App (Expo/React Native)"]:::frontend
    end

    subgraph "Backend Services (FastAPI)"
        API["API Gateway / Main Router"]:::backend
        AuthService["Authentication Service"]:::backend
        SearchEngine["Intent-Aware Hybrid Search"]:::backend
        ScoringEngine["Engineering Impact Scoring (EIS)"]:::backend
        CollabService["Collaboration & Squads"]:::backend
        ScraperManager["Scraper Service Worker"]:::backend
    end

    subgraph "Data Storage"
        PG["PostgreSQL"]:::db
        Vectors["pgvector (Semantic Search)"]:::db
        FTS["Full-Text Search Indices"]:::db
    end

    subgraph "External Integrations"
        GroqAPI["Groq API (LLM Inference/Roadmaps)"]:::external
        DataSources["Data Sources (GitHub, Web)"]:::external
    end

    WebUI <--> API
    MobileUI <--> API

    API <--> AuthService
    API <--> SearchEngine
    API <--> CollabService
    API <--> ScoringEngine

    SearchEngine <--> Vectors
    SearchEngine <--> FTS
    CollabService <--> PG
    AuthService <--> PG

    ScraperManager --> DataSources
    ScraperManager --> PG

    SearchEngine --> GroqAPI
    ScoringEngine --> GroqAPI
""",
    "collaboration_state": """stateDiagram-v2
    [*] --> ViewingProblem: User views a problem

    ViewingProblem --> ExpressedInterest: Clicks "Interested"
    ViewingProblem --> RequestingCollab: Clicks "Start Squad" / "Request Collaboration" (auto-marks interest)

    ExpressedInterest --> RequestingCollab: Clicks "Start Squad"
    RequestingCollab --> PendingSquad: Squad Created (Waiting for peers)

    PendingSquad --> ActiveSquad: Another user joins the Squad
    PendingSquad --> SquadDissolved: User deletes Squad/Leaves

    ActiveSquad --> Collaborating: Users chat / Real-time sync
    Collaborating --> ActiveSquad: New problem insights

    ActiveSquad --> SquadDissolved: Final member leaves
    SquadDissolved --> [*]
""",
    "eis_components": """graph LR
    classDef component fill:#4f46e5,stroke:#312e81,stroke-width:2px,color:#fff
    classDef data fill:#e5e7eb,stroke:#9ca3af,stroke-width:2px,color:#000

    RawData["Raw Problem Data"]:::data
    DataCleaner["Data Cleaning Layer (Deduplication)"]:::component
    Heuristics["Heuristics Evaluator (Keywords, Complexity)"]:::component
    AIModel["Groq API (LLM Assessor)"]:::component
    Normalizer["Score Normalizer (0-100)"]:::component
    EISOutput["Final EIS & Difficulty Mapping"]:::data

    RawData --> DataCleaner
    DataCleaner --> Heuristics
    DataCleaner --> AIModel
    Heuristics --> Normalizer
    AIModel --> Normalizer
    Normalizer --> EISOutput
""",
    "search_flow": """sequenceDiagram
    participant User
    participant QPS as Query Processing Service
    participant Emb as Embedding Service
    participant PG as PostgreSQL (Hybrid Search)
    participant RR as Reranking Service

    User->>QPS: Search Query (e.g., "React Native performance")
    QPS->>QPS: Analyze Intent & Extract Keywords
    QPS->>Emb: Generate Semantic Embeddings
    Emb-->>QPS: Vector Representation
    QPS->>PG: Execute Hybrid Query (Vector Similarity + FTS)
    PG-->>QPS: Raw Search Results
    QPS->>RR: Send Results for Relevance Reranking
    RR->>RR: Apply Scoring Weights (EIS + Recency)
    RR-->>QPS: Sorted Top Results
    QPS-->>User: Display Search Results
""",
    "overall_workflow": """graph TD
    classDef step fill:#bae6fd,stroke:#0284c7,stroke-width:2px,color:#000

    S1("1. Scheduled Scrapers Run"):::step
    S2("2. Data Ingestion & Cleaning (SHA-256 Dedupe)"):::step
    S3("3. Compute Engineering Impact Score (EIS)"):::step
    S4("4. Generate Vector Embeddings"):::step
    S5("5. Live Update (Real-time Problem Sync)"):::step
    S6("6. Intent-Aware Search Discovery"):::step
    S7("7. Squad Formation & Collaboration"):::step

    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> S6
    S6 --> S7
"""
}

for name, content in diagrams.items():
    mmd_path = os.path.join(diagrams_dir, f"{name}.mmd")
    with open(mmd_path, "w") as f:
        f.write(content)
    
    png_path = os.path.join(diagrams_dir, f"{name}.png")
    print(f"Generating {png_path}...")
    
    # Run mmdc using npx. Handle windows specific npx.cmd
    npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
    try:
        # Use shell=True to effectively resolve npx
        subprocess.run(
            [npx_cmd, "-y", "@mermaid-js/mermaid-cli", "-i", mmd_path, "-o", png_path],
            check=True,
            shell=True
        )
        print(f"Successfully generated {png_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate {png_path}: {e}")

print("Done generating diagrams.")
