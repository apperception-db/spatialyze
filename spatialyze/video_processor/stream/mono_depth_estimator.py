import numpy.typing as npt
import PIL.Image as Image
import torch
from torchvision import transforms

from .data_types import Skip, skip

from ..modules.monodepth2.monodepth2.layers import disp_to_depth
from ..stages.depth_estimation import monodepth
from .stream import Stream
from ..video import Video


class MonoDepthEstimator(Stream[npt.NDArray]):
    def __init__(self, frames: Stream[npt.NDArray]):
        self.frames = frames

    def _stream(self, video: Video):
        with torch.no_grad():
            md = monodepth()
            for img in self.frames.stream(video):
                if isinstance(img, Skip):
                    yield skip
                    continue

                # Load image and preprocess
                input_image = Image.fromarray(img[:, :, [2, 1, 0]])
                original_width, original_height = input_image.size
                input_image = input_image.resize((md.feed_width, md.feed_height), Image.LANCZOS)
                input_image = transforms.ToTensor()(input_image).unsqueeze(0)

                # PREDICTION
                input_image = input_image.to(md.device)
                features = md.encoder(input_image)
                outputs = md.depth_decoder(features)

                disp = outputs[("disp", 0)]

                _, depth = disp_to_depth(disp, 0.1, 100)
                depth_resized = torch.nn.functional.interpolate(
                    depth, (original_height, original_width), mode="bilinear", align_corners=False
                )

                yield depth_resized.squeeze().cpu().detach().numpy() * 5.4
