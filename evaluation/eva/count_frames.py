import os
import cv2
video_path = "/data/apperception-data/processed/nuscenes/full-dataset-v1.0/Trainval/videos"

with open('./scene-names.txt', 'r') as f:
    scenes = f.read().split('\n')

count  = 0
for s in scenes:
    video_name = f"boston-seaport-scene-{s}-CAM_FRONT_LEFT.mp4"
    cap = cv2.VideoCapture(os.path.join(video_path, video_name))
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(s, num_frames)
    count += num_frames
print(count)
