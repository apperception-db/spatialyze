import json
import subprocess
import os


from tqdm import tqdm


REPO_DIR = '/data/chanwutk/projects/spatialyze'
BASE_DATA = './data'


# subprocess.Popen('jupyter nbconvert --to python ./run-ablation.ipynb && mv run-ablation.py ..', cwd=REPO_DIR)
# jupyter.nbconvert.main(['--to', 'python', './run-ablation.ipynb'])


with open(os.path.join(BASE_DATA, 'evaluation', 'ips.json')) as f:
    ips = json.load(f)


processes = []
for i, ip in enumerate(ips):
    process = subprocess.Popen(f'scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {os.path.join(REPO_DIR, "playground/run-all")} chanwutk@{ip}:"/home/chanwutk/"', shell=True)
    processes.append(process)
for i, ip in tqdm(enumerate(processes), total=len(processes)):
    process.wait()


processes = []
for i, ip in enumerate(ips):
    process = subprocess.Popen(f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null chanwutk@{ip} /home/chanwutk/run-all', shell=True)
    processes.append(process)
for i, ip in tqdm(enumerate(processes), total=len(processes)):
    process.wait()

processes = []
for i, ip in enumerate(ips):
    process = subprocess.Popen(
        f"tmux new-session -d -s run-{i} -n run-{i} && " \
        f"tmux send-keys -t run-{i} 'gcpa {ip}' Enter",
        shell=True
    )
    processes.append(process)
for i, ip in tqdm(enumerate(processes), total=len(processes)):
    process.wait()