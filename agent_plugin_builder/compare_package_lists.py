import json
from itertools import groupby, islice
from pathlib import Path
from typing import Any, Iterable


def load_package_names(file_path: Path) -> set[str]:
    with file_path.open("r") as f:
        packages_dict = json.load(f)
        return {p["download_info"]["url"].split("/")[-1] for p in packages_dict["install"]}


def take(n: int, iterable: Iterable[Any]) -> list[str]:
    "Return first n items of the iterable as a list."
    return list(islice(iterable, n))


def all_equal(packages: Iterable[Any]) -> bool:
    "Returns True if all the elements are equal to each other."
    return len(take(2, groupby(packages, None))) <= 1
