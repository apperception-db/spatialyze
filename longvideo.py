#!/usr/bin/env python
# coding: utf-8

# In[21]:


import cv2
import os
import json
import pickle
from tqdm import tqdm


# In[ ]:





# In[9]:


def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            # Jupyter notebook or qtconsole
            return True
        elif shell == 'TerminalInteractiveShell':
            # Terminal running IPython
            return False
        else:
            # Other type (?)
            return False
    except NameError:
        # Probably standard Python interpreter
        return False


if is_notebook():
    get_ipython().run_line_magic('cd', '../..')
    from tqdm.notebook import tqdm
    from nbutils.report_progress import report_progress
else:
    from tqdm import tqdm
    from evaluation.ablation.nbutils.report_progress import report_progress


# In[4]:


# NUSCENES_PROCESSED_DATA = "NUSCENES_PROCESSED_DATA"
# print(NUSCENES_PROCESSED_DATA in os.environ)
# print(os.environ['NUSCENES_PROCESSED_DATA'])


# # In[12]:


# DATA_DIR = os.environ[NUSCENES_PROCESSED_DATA]
# # with open(os.path.join(DATA_DIR, "videos", "frames.pkl"), "rb") as f:
# #     videos = pickle.load(f)
# with open(os.path.join(DATA_DIR, 'videos', 'videos.json'), 'r') as f:
#     videos = json.load(f)
# type(videos)
# videos[0]


# In[10]:


# with open('./data/evaluation/video-samples/boston-seaport.txt', 'r') as f:
#     sampled_scenes = f.read().split('\n')
# print(sampled_scenes[0], sampled_scenes[-1], len(sampled_scenes))


# In[17]:

with open('/home/chanwutk/data/boston-seaport-scene-0655-CAM_FRONT.pkl', 'rb') as f:
# with open(os.path.join(DATA_DIR, 'videos', 'boston-seaport-scene-' + sampled_scenes[0] + '-CAM_FRONT.pkl'), 'rb') as f:
    video = pickle.load(f)
video_filename = video['filename']


# In[18]:


video_filename


# In[25]:


frames = []
cap = cv2.VideoCapture(os.path.join('/home/chanwutk/data/', video_filename))
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frames.append(frame)
cap.release()
cv2.destroyAllWindows()


# In[28]:

n = 633

for i in [3]:
    result = cv2.VideoWriter(f'./loop-video-{i}0.avi',  
                            cv2.VideoWriter_fourcc(*'MJPG'), 
                            20, (1600, 900)) 
    for i in tqdm(range(n * i)):
        for frame in frames:
            result.write(frame) 
    result.release() 
    cv2.destroyAllWindows()


# In[ ]:




