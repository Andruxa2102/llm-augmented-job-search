from typing import Type
from src.adapters.base import JobSource
from src.adapters.SourceX import SourceXAdapter
from src.adapters.SourceX_local import SourceXLocalAdapter


ADAPTER_REGISTRY: dict[str, Type[JobSource]] = {
    "SourceX_DE": SourceXAdapter,
    "SourceX_DWH": SourceXAdapter,
    "SourceX_ETL": SourceXAdapter,
    "SourceX_local": SourceXLocalAdapter,
}


def get_adapter_class(source_name: str) -> Type[JobSource]:
    """Get adapter class by name of a source"""
    adapter_class = ADAPTER_REGISTRY.get(source_name)

    if adapter_class is None:
        raise ValueError(
            f"No adapter registered for source '{source_name}'. "
            f"Available: {list(ADAPTER_REGISTRY.keys())}"
        )

    return adapter_class