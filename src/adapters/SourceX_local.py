from logging import getLogger
from pathlib import Path
from typing import Iterator
from bs4 import BeautifulSoup
from src.adapters.base import JobSource
from src.adapters.parsers.sourcex_parser import parse_page
from src.config.models import SourceConfig

logger = getLogger(__name__)

class SourceXLocalAdapter(JobSource):

    source_name = "SourceX_local"

    def __init__(self, cfg: SourceConfig):
        self.cfg = cfg
        self._project_root = Path(__file__).resolve().parent.parent.parent
        self._saved_pages = self._project_root / "saved_pages"

    def fetch_raw(self) -> list[dict]:
        """Main method orchestrates pagination and parsing"""

        results = []
        for soup in self._paginate():
            results.extend(parse_page(soup))

        return results

    def _paginate(self) -> Iterator[BeautifulSoup]:
        """Yields HTML content for each page to parse"""

        files_list = [f for f in self._saved_pages.iterdir() if (f.is_file() and not (".gitkeep" in f.name))]
        files_list.sort(key=lambda x: x.name)

        logger.info(f"Found {len(files_list)} HTML files in {self._saved_pages}")

        if not files_list:
            return

        for file in files_list:
            logger.debug(f"Processing file: {file.name}")
            with open(self._saved_pages / file, "r", encoding="utf-8") as f:
                html = f.read()

            yield BeautifulSoup(html, "lxml")
