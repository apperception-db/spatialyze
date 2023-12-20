from spatialyze.video_processor.stream.list_images import ListImages
from spatialyze.video_processor.stream.load_images import LoadImages
from spatialyze.video_processor.video.video import Video


def test_stream_end():
    video = Video('./data/assets', [])

    files = ListImages()
    images = LoadImages(files)

    outputs = images.iterate(video)
    assert not images.ended()

    list(outputs)
    assert images.ended()
