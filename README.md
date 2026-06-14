# LLM-Augmented Job Search

LLM-driven job search and filtering pipeline.

## Project description

An automated ETL pipeline for extracting vacancy data, filtering it using an LLM, and serving it via a REST API.

### Key features
```text

- **Module architecture**:          adapters, parsers, LLM-agent, storage - all isolated;
- **Type safety and validation**:   Pydantic models for configs, strict data checking;
- **Idempotency**:                  repeating launches do not create duplicates (UPSERT via `merge`);
- **Graceful degradation**:         if LLM is inaccessible, the pipeline continues working with fallback logic;
- **Security**:                     URL and headers are stored in the environment variables - not committed to Git;
- **Ethics of data collection**:    used archive HTML-snapshots for demo - with respect for `robots.txt`;
```

## Architecture




```text
llm-augmented-work-search/
├── src/
│   ├── adapters/			            # data loaders
│   │   ├── base.py                     # abstract interface JobSource
│   │   ├── SourceX.py                  # 
│   │   └── parsers/                    # selectors, source specifics
│   ├── llm/                            # llm-agents for filtration
│   │   ├── agent_interface.py          # abstract interface LLMFilterAgent
│   │   ├── pure_python_agent.py        # realization through Ollama
│   │   └── prompts/
│   ├── storage/                        #
│   │   ├── sqlite.py                   # sqlAlchemy engine, session
│   │   └── models.py             	    # ORM-models
│   ├── api/                            # REST API
│   │   ├── main.py               	    # FASTAPI endpoints
│   ├── utils/      
│   │   └── logger.py
│   └── config/
│       ├── loader.py                   # YAML loader and validator
│       └── models.py                   # Pydantic schemes
├── config/
│   ├── headers_SourceX.json
│   ├── llm.yaml                        # llm parameters
│   └── sources.yaml                    # sources parameters
├── scripts/
│   └── run_pipeline.py           	    # entry point for orchestration
├── data/                               # db directory
│   └── llm_augmented_work_search.db
├── tests/
├── .gitignore
├── pyproject.toml
├── Makefile
└── README.md
```

Example .env:
DB_URL=sqlite:///./data/llm_augmented_work_search.db
SOURCE_X_BASE_URL=https://example.com/search/vacancy
SOURCE_X_REFERER=https://example.com/