from json import dumps
from logging import getLogger, basicConfig, INFO, info, critical
from os import getcwd
from sys import exit
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from src.adapters.registry import get_adapter_class
from src.llm.pure_python_agent import PurePythonFilterAgent
from src.storage.db import SessionLocal, engine
from src.storage.models import RawVacancy, FilteredVacancy, Base


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


from src.config.loader import load_sources_config, ConfigLoadError


basicConfig(level=INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = getLogger(__name__)

info(f"CWD: {getcwd()}")
info(f"__file__: {__file__}")

def main():
    # 1. Initialization
    config_path = Path(__file__).resolve().parent.parent / "config" / "sources.yaml"

    try:
        config = load_sources_config(config_path)
    except ConfigLoadError as e:
        critical(f"Pipeline aborted: {e}")
        exit(1)

    Base.metadata.create_all(engine)

    for source_name, source_cfg in config.sources.items():
        if not source_cfg.enabled:
            logger.info(f"Skipping disabled source: {source_name}")
            continue

        logger.info(f"Starting pipeline for: {source_name} (query: {source_cfg.query})")

        adapter_class = get_adapter_class(source_name)
        adapter = adapter_class(cfg=source_cfg)
        llm = PurePythonFilterAgent()

        # 2. Fetch & Normalize
        raw_items = adapter.fetch_raw()
        normalized = [adapter.normalize(r) for r in raw_items]
        logger.info(f"Fetched {len(normalized)} items")

        # 3. Idempotent Upsert Raw
        with SessionLocal() as sess:
            for item in normalized:
                existing = sess.query(RawVacancy).filter_by(source_id=item["source_id"]).first()
                if existing:
                    existing.title = item["title"]
                    existing.company = item["company"]
                    existing.url = item["url"]
                    existing.description = item["description"]
                    existing.raw_data = item["raw_data"]
                    existing.fetched_at = datetime.now(timezone.utc)
                else:
                    sess.add(RawVacancy(**item))

            sess.commit()

        # 4. LLM Filter & Save
        results = llm.evaluate_batch(normalized)

        with SessionLocal() as sess:
            for item, llm_res in zip(normalized, results):
                existing = sess.query(FilteredVacancy).filter_by(source_id=item["source_id"]).first()
                if existing:
                    existing.decision = llm_res.decision
                    existing.confidence = llm_res.confidence
                    existing.reason = llm_res.reason
                    existing.tags = dumps(llm_res.tags)
                    existing.processed_at = datetime.now(timezone.utc)
                else:
                    sess.add(FilteredVacancy(
                        source_id=item["source_id"],
                        decision=llm_res.decision,
                        confidence=llm_res.confidence,
                        reason=llm_res.reason,
                        tags=dumps(llm_res.tags),
                        processed_at=datetime.now(timezone.utc)
                    ))
            sess.commit()

        logger.info(f"[{source_name}] Processed: {len(results)}")

if __name__ == "__main__":
    main()
