from unittest.mock import MagicMock, AsyncMock

import pytest

from youtube.domain.video_document import VideoDocument, TranscriptSegment
from youtube.stages.fetch_video import FetchVideoTransformer
from youtube.video import YouTubeVideo


@pytest.mark.asyncio
async def test_fetch_video_transformer():
    document = VideoDocument(id="123")
    transcript = TranscriptSegment(text="test", start=0, duration=10)

    yt = YouTubeVideo(MagicMock())
    yt.get_video_info = AsyncMock(return_value=document)
    yt.get_transcript_segments = AsyncMock(return_value=[transcript])

    stage = FetchVideoTransformer(yt)

    await stage.run(document)

    yt.get_video_info.assert_called_once_with("123")
    yt.get_transcript_segments.assert_called_once_with("123")

    assert document.transcripts == [transcript]
