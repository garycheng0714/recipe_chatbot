from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from youtube.domain.mapper.section import SectionMapper
from youtube.domain.mapper.source import SourceMapper
from youtube.stages.save_raw_data import SaveRawData


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_session.begin = MagicMock(return_value=mock_session)

    factory = MagicMock(return_value=mock_session)
    return factory


@pytest.mark.asyncio
async def test_save_raw_data(mock_session_factory):
    mock_repository = Mock()
    mock_repository.insert = AsyncMock()
    mock_repository.insert_bulk_section = AsyncMock()

    with patch.object(SourceMapper, 'from_document', MagicMock(return_value="insert Source")) as mock_source:
        with patch.object(SectionMapper, 'from_document', MagicMock(return_value="insert Sections")) as mock_sections:
            mock_session = mock_session_factory.return_value

            stage = SaveRawData(mock_repository, mock_session_factory)

            await stage.run(MagicMock())

            assert mock_source.call_count == 1
            assert mock_sections.call_count == 1
            mock_repository.insert.assert_called_once_with(mock_session, "insert Source")
            mock_repository.insert_bulk_section.assert_called_once_with(mock_session, "insert Sections")