<br/>
<p align="center"><img width=60% src="./data/assets/spatialyze.png"></p>

<h2 align="center">A Geospatial Video Analytic System with Spatial-Aware Optimizations</h2>
<p align="center">
  <a href="https://github.com/apperception-db/spatialyze/actions/workflows/test.yml"><img
    alt="Github Actions Test Status"
    src="https://img.shields.io/github/actions/workflow/status/apperception-db/spatialyze/test.yml?label=Test&style=for-the-badge"
  ></a>
  <a href="https://github.com/apperception-db/spatialyze/actions/workflows/check.yml"><img
    alt="Github Actions Type Check Status"
    src="https://img.shields.io/github/actions/workflow/status/apperception-db/spatialyze/check.yml?label=Type%20Check&style=for-the-badge"
  ></a>
  <a href="https://github.com/apperception-db/spatialyze/actions/workflows/lint.yml"><img
    alt="Github Actions Lint Status"
    src="https://img.shields.io/github/actions/workflow/status/apperception-db/spatialyze/lint.yml?label=Lint&style=for-the-badge"
  ></a>
  <a href="https://codecov.io/gh/apperception-db/spatialyze"><img
    alt="Codecov Coverage Status"
    src="https://img.shields.io/codecov/c/github/apperception-db/spatialyze.svg?label=Coverage&style=for-the-badge"
  ></a>
  <br/>
  <a href="https://github.com/psf/black"><img
    alt="Black Badge"
    src="https://img.shields.io/badge/black-000000.svg?label=Code%20style&style=for-the-badge"
  ></a>
  <a href="https://arxiv.org/abs/2308.03276"><img
    alt="ArXiv Paper"
    src="https://img.shields.io/badge/2308.03276-b31b1b.svg?label=arXiv&style=for-the-badge"
  ></a>
</p>

## Absract
Videos that are shot using commodity hardware such as phones and surveillance cameras record various metadata such as time and location.
We encounter such geospatial videos on a daily basis and such videos have been growing in volume significantly.
Yet, we do not have data management systems that allow users to interact with such data effectively.

In this paper, we describe Spatialyze, a new framework for end-to-end querying of geospatial videos.
Spatialyze comes with a domain-specific language where users can construct geospatial video analytic workflows using a 3-step,
declarative, build-filter-observe paradigm.
Internally, Spatialyze leverages the declarative nature of such workflows,
the temporal-spatial metadata stored with videos, and physical behavior of real-world objects to optimize the execution of workflows.
Our results using real-world videos and workflows show that Spatialyze can reduce execution time by up to 5.3x,
while maintaining up to 97.1% accuracy compared to unoptimized execution.

## Requirement
```
- python >= 3.10 (Prefer Conda/Mamba)
- docker
- cuda >= 11.7 (If using GPU)
```

## How to Setup Spatialyze Repo
### Clone the Spatialyze repo
```bash
git clone --recurse-submodules git@github.com:apperception-db/spatialyze.git
cd spatialyze
```

### We use Conda/Mamba to manage our python environment
Install [Mamba](https://mamba.readthedocs.io/en/latest/installation.html)
or install [Conda](https://docs.conda.io/en/latest/miniconda.html)

### Setup Environment and Dependencies
```bash
# clone submodules
git submodule update --init --recursive

# setup virtual environment
# with conda
conda env create -f environment.yml
conda activate spatialyze
# OR with mamba
mamba env create -f environment.yml
mamba activate spatialyze

# install python dependencies
poetry install
pip install lap  # a bug in lap/poetry/conda that lap needs to be installed using pip.
```

## Spatialyze Demo
### Start Spatialyze Geospatial Metadata Store [MobilityDB](https://github.com/MobilityDB/MobilityDB)
```bash
docker volume create spatialyze-gsstore-data
docker run --name     "spatialyze-gsstore"                        \
           --detach                                               \
           --publish  25432:5432                                  \
           --volume   spatialyze-gsstore-data:/var/lib/postgresql \
                      mobilitydb/mobilitydb
```
Setup the MobilityDB with customized functions
```bash
docker exec -it spatialyze-gsstore rm -rf /pg_extender
docker cp scripts/pg-extender spatialyze-gsstore:/pg_extender
docker exec -it -w /pg_extender spatialyze-gsstore python3 install.py
```
To run MobilityDB every system restart
```bash
docker update --restart unless-stopped spatialyze-gsstore
```

### Try the demo (WIP 🚧)
In spatialyze repo:
```sh
jupyter-lab
```

The demo notebook first constructs the world. Then it queries for the trajectory of the cars that appeared once in an area of interests within some time interval.

## Citing Spatialyze
This paper is currently under review for [VLDB](https://vldb.org/2024/).
```bib
@misc{kittivorawong2023spatialyze,
    title={Spatialyze: A Geospatial Video Analytics System with Spatial-Aware Optimizations}, 
    author={Chanwut Kittivorawong and Yongming Ge and Yousef Helal and Alvin Cheung},
    year={2023},
    eprint={2308.03276},
    archivePrefix={arXiv},
    primaryClass={cs.DB}
}
```
