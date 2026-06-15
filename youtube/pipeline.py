from youtube.domain.video_document import VideoDocument
from youtube.stage.base import Stage


class Pipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, context: VideoDocument):
        for stage in self.stages:
            context = stage.run(context)
        return context