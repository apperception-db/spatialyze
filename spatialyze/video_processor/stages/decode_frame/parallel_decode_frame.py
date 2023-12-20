import multiprocessing
from functools import reduce
from multiprocessing import Pool
from typing import TYPE_CHECKING

import cv2

from .decode_frame import DecodeFrame

if TYPE_CHECKING:
    import numpy.typing as npt

    from ...payload import Payload


def decode(args: "tuple[str, int, int]"):
    videofile, start, end = args
    cap = cv2.VideoCapture(videofile)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    out: "list[npt.NDArray]" = []
    for _ in range(start, end):
        ret, frame = cap.read()
        if not ret:
            break
        out.append(frame)
    cap.release()
    assert len(out) == end - start, (len(out), start, end)
    return out, start, end


class ParallelDecodeFrame(DecodeFrame):
    # @cache
    def _run(self, payload: "Payload"):
        try:
            metadata: "list[npt.NDArray]" = []

            n_cpus = multiprocessing.cpu_count()
            n_frames = len(payload.video)
            assert n_frames == len(payload.keep), (n_frames, len(payload.keep))

            q, mod = divmod(n_frames, n_cpus)
            frames_per_cpu = [q + (i < mod) for i in range(n_cpus)]

            def _r(acc: "tuple[int, list[tuple[int, int]]]", frames: int):
                start, arr = acc
                end = start + frames
                return (end, arr + [(start, end)])

            frame_slices = reduce(_r, frames_per_cpu, (0, []))[1]

            with Pool(n_cpus) as pool:
                inputs = ((payload.video.videofile, start, end) for start, end in frame_slices)
                out = [*ParallelDecodeFrame.tqdm(pool.imap_unordered(decode, inputs), total=n_cpus)]
                for o, _, _ in sorted(out, key=lambda x: x[1]):
                    metadata.extend(o)
            cv2.destroyAllWindows()

            assert len(metadata) == len(payload.video), (
                len(metadata),
                len(payload.video),
                [(s, e, len(o)) for o, s, e in sorted(out, key=lambda x: x[1])],
            )

            return None, {self.classname(): metadata}
        except BaseException:
            _, output = DecodeFrame()._run(payload)
            return None, {self.classname(): DecodeFrame.get(output)}
