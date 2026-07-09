from logging import getLogger, basicConfig, INFO, info, critical
from json import dumps
from os import getcwd
from sys import exit
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from src.llm.pure_python_agent import PurePythonFilterAgent
from src.storage.db import SessionLocal, engine
from src.storage.models import RawVacancy, FilteredVacancy, Base


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


from src.config.loader import load_sources_config, ConfigLoadError
from src.adapters.SourceX import SourceXAdapter


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

        adapter = SourceXAdapter(cfg = source_cfg)
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
        results = []
        for item in normalized:
            llm_res = llm.evaluate(item)

            results.append({
                "source_id": item["source_id"],
                "decision": llm_res["decision"],
                "confidence": llm_res["confidence"],
                "reason": llm_res["reason"],
                "tags": dumps(llm_res["tags"]),
                "processed_at": datetime.now(timezone.utc)
            })

        with SessionLocal() as sess:
            for r in results:
                existing = sess.query(FilteredVacancy).filter_by(source_id=r["source_id"]).first()
                if existing:
                    existing.decision = r["decision"]
                    existing.confidence = r["confidence"]
                    existing.reason = r["reason"]
                    existing.tags = r["tags"]
                    existing.processed_at = r["processed_at"]
                    existing.llm_pass = r["llm_pass"]
                else:
                    sess.add(FilteredVacancy(**r))
            sess.commit()

        logger.info(f"[{source_name}] Processed: {len(results)}")

if __name__ == "__main__":
    main()
