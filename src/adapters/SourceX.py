from os import getenv
from json import load, JSONDecodeError
from time import sleep
from random import uniform
from bs4 import BeautifulSoup
from httpx import Client, HTTPError
from pathlib import Path
from typing import Iterator
from src.adapters.base import JobSource
from src.config.models import SourceConfig
from src.adapters.parsers.sourcex_parser import parse_page, parse_max_pages_hint, has_vacancies
from logging import getLogger


logger = getLogger(__name__)


class SourceXAdapter(JobSource):

    source_name = "SourceX"

    def __init__(self, cfg: SourceConfig):
        self.cfg = cfg
        self._project_root = Path(__file__).resolve().parent.parent.parent

    def _load_headers(self) -> dict:
        """Load headers from JSON file or return default headers"""

        default_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://hh.ru',
            'Connection': 'keep-alive'
    }

        if self.cfg.headers_file:
            headers_path = self._project_root / self.cfg.headers_file

            if headers_path.exists():
                try:
                    with open(headers_path, "r", encoding="utf-8") as f:
                        custom_headers = load(f)

                        for key, value in custom_headers.items():
                            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                                env_var = value[2:-1]
                                resolved = getenv(env_var)
                                if resolved:
                                    custom_headers[key] = resolved
                                else:
                                    logger.warning(f"Env var {env_var} not found for header {key}")

                        default_headers.update(custom_headers)
                        logger.debug(f"Loaded headers from {headers_path}")
                except (JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load headers from {headers_path}: {e}")

        self._headers = default_headers
        return self._headers


    def fetch_raw(self) -> list[dict]:
        """Main method orchestrates pagination and parsing"""
        results = []
        for soup in self._paginate():
            results.extend(parse_page(soup))

        return results


    def _paginate(self) -> Iterator[BeautifulSoup]:
        """Yields HTML content for each page to parse"""

        if not self.cfg.pagination.enabled:
            html = self._fetch_page(1)
            yield BeautifulSoup(html, "lxml")
            return

        page = self.cfg.pagination.start_page
        config_limit = self.cfg.pagination.max_pages if self.cfg.pagination.max_pages > 0 else float('inf')
        effective_limit = 0
        html_hint = None

        while True:
            html = self._fetch_page(page)

            if not html.strip():
                logger.warning(f"Empty response at page {page}, stopping")
                break

            soup = BeautifulSoup(html, "lxml")

            if page == self.cfg.pagination.start_page and html_hint is None:
                parsed = parse_max_pages_hint(soup)
                html_hint = parsed if parsed and parsed > 0 else config_limit
                effective_limit = min(html_hint, config_limit)
                logger.info(f"Pagination limit: config={config_limit}, html_hint={html_hint}")

            if self.cfg.pagination.stop_on_empty and not has_vacancies(soup):
                logger.warning(f"No vacancies at page {page}, stopping")
                break

            yield soup

            if page >= effective_limit:
                logger.info(f"Reached effective limit ({effective_limit}), stopping")
                break

            delay = uniform(self.cfg.rate_limit.min_delay_s, self.cfg.rate_limit.max_delay_s)
            sleep(delay)
            page += 1

    def _fetch_page(self, page: int) -> str:
        """Fetches single page HTML from Web"""

        if page == 1:
            params = {
                "text": self.cfg.query
            }
        else:
            params = {
                "text": self.cfg.query,
                self.cfg.pagination.param_name: page
            }

        headers = self._load_headers()

        try:
            with Client(timeout=30.0) as client:
                response = client.get(
                    str(self.cfg.base_url),
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.text
        except HTTPError as e:
            logger.error(f"HTTP error on page {page}: {e}")
            return ""
