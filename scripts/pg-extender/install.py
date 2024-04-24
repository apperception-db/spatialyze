import os
import subprocess


CREATE_PREFIX = 'create or replace function '


files = os.listdir('.')
for file in sorted(files):
    if not file.endswith('.sql'):
        continue

    print("------------------------------------------")
    print(file)
    print("------------------------------------------")
    with open(file, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line.lower().startswith(CREATE_PREFIX):
                line = line[len(CREATE_PREFIX):]
                if line.lower().endswith('as'):
                    line = line[:-len('as')]
                print(line)
    print()
    process = subprocess.Popen(" ".join(["psql", "-h", "localhost", "-p", "5432", "-d", "postgres", "-U", "postgres", "--command", "'SET client_min_messages TO WARNING;'", "--command", f"'\i {file};'"]), shell=True) 
    process.wait()
    print()
    print()
    print()
