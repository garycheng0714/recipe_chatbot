import json
from typing import List

import pytest
from pydantic import TypeAdapter

from youtube.tests.retrieve.model import TestSet


@pytest.fixture(scope="class")
def test_set_reader():

    def _reader(file_path: str) -> list[TestSet]:
        with open(file_path, 'r') as f:
            pairs = json.load(f)
        return TypeAdapter(List[TestSet]).validate_python(pairs)

    return _reader
