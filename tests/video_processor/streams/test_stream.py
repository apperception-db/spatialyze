from spatialyze.video_processor.stream.list_images import ListImages
from spatialyze.video_processor.stream.load_images import LoadImages
from spatialyze.video_processor.video import Video


def test_stream_end():
    video = Video('./data/assets', [])

    files = ListImages()
    images = LoadImages(files)

    images.iterate(video)
    assert not images.ended()

    images.execute(video)
    assert images.ended()
