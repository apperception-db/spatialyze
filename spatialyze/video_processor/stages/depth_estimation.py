import os
from typing import TYPE_CHECKING

import numpy.typing as npt
import PIL.Image as pil
import torch
from bitarray import bitarray
from torchvision import transforms

from ..modules.monodepth2.monodepth2 import networks
from ..modules.monodepth2.monodepth2.layers import disp_to_depth
from ..modules.monodepth2.monodepth2.utils import (
    download_model_if_doesnt_exist,
    monodepth2_models_path,
)
from .decode_frame.decode_frame import DecodeFrame
from .stage import Stage

if TYPE_CHECKING:
    from ..payload import Payload


class DepthEstimation(Stage["npt.NDArray | None"]):
    def _run(self, payload: "Payload") -> "tuple[bitarray | None, dict[str, list] | None]":
        md = monodepth()
        assert payload.metadata is not None
        images: "list[npt.NDArray | None]" = []

        decoded_frames = DecodeFrame.get(payload)
        assert decoded_frames is not None

        for k, m in zip(payload.keep, decoded_frames):
            if k:
                images.append(m)
            else:
                images.append(None)
        metadata = md.eval_all(images)

        return None, {self.classname(): metadata}


MODEL_NAMES = [
    "mono_640x192",
    "stereo_640x192",
    "mono+stereo_640x192",
    "mono_no_pt_640x192",
    "stereo_no_pt_640x192",
    "mono+stereo_no_pt_640x192",
    "mono_1024x320",
    "stereo_1024x320",
    "mono+stereo_1024x320",
]


class monodepth:
    def __init__(self, model_name=MODEL_NAMES[2], no_cuda=False, pred_metric_depth=True) -> None:
        assert model_name in MODEL_NAMES, "Invalid Model Name"

        if torch.cuda.is_available() and not no_cuda:
            self.device = torch.device("cuda")
            # print("GPU Visible")
        else:
            self.device = torch.device("cpu")
            print("GPU not visible; CPU mode")

        if pred_metric_depth and "stereo" not in model_name:
            print(
                "Warning: The pred_metric_depth flag only makes sense for stereo-trained KITTI "
                "models. For mono-trained models, output depths will not in metric space."
            )

        download_model_if_doesnt_exist(model_name=model_name)
        model_path = os.path.join(monodepth2_models_path, model_name)

        # print("-> Loading model from ", model_path)
        encoder_path = os.path.join(model_path, "encoder.pth")
        self.depth_decoder_path = os.path.join(model_path, "depth.pth")

        # LOADING PRETRAINED MODEL
        # print("   Loading pretrained encoder")
        self.encoder = networks.ResnetEncoder(18, False)
        loaded_dict_enc = torch.load(encoder_path, map_location=self.device)

        # extract the height and width of image that this model was trained with
        self.feed_height = loaded_dict_enc["height"]
        self.feed_width = loaded_dict_enc["width"]
        filtered_dict_enc = {
            k: v for k, v in loaded_dict_enc.items() if k in self.encoder.state_dict()
        }
        self.encoder.load_state_dict(filtered_dict_enc)
        self.encoder.to(self.device)
        self.encoder.eval()

        # print("   Loading pretrained decoder")
        self.depth_decoder = networks.DepthDecoder(
            num_ch_enc=self.encoder.num_ch_enc, scales=range(4)
        )

        loaded_dict = torch.load(self.depth_decoder_path, map_location=self.device)
        self.depth_decoder.load_state_dict(loaded_dict)

        self.depth_decoder.to(self.device)
        self.depth_decoder.eval()

    def eval_all(self, input_images: "list[npt.NDArray | None]"):
        output: "list[npt.NDArray | None]" = []
        with torch.no_grad():
            # for im in tqdm(input_images):
            for im in input_images:
                if im is None:
                    output.append(None)
                    continue
                # Load image and preprocess
                input_image = pil.fromarray(im[:, :, [2, 1, 0]])
                original_width, original_height = input_image.size
                input_image = input_image.resize(
                    (self.feed_width, self.feed_height), pil.Resampling.LANCZOS
                )
                input_image = transforms.ToTensor()(input_image).unsqueeze(0)

                # PREDICTION
                input_image = input_image.to(self.device)
                features = self.encoder(input_image)
                outputs = self.depth_decoder(features)

                disp = outputs[("disp", 0)]

                _, depth = disp_to_depth(disp, 0.1, 100)
                depth_resized = torch.nn.functional.interpolate(
                    depth, (original_height, original_width), mode="bilinear", align_corners=False
                )

                output.append(depth_resized.squeeze().cpu().detach().numpy() * 5.4)
        return output
