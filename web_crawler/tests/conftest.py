import pytest

@pytest.fixture
def read_mock_data():

    def _read(filename: str) -> str:
        with open("web_crawler/tests/mocks/{}".format(filename), "r") as f:
            html = f.read()
        return html

    return _read