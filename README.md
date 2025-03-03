<br/>
<p align="center"><img width="60%" src="./data/assets/spatialyze.png" /></p>

<h2 align="center">A Geospatial Video Analytic System with Spatial-Aware Optimizations</h2>
<p align="center">
  <a href="https://github.com/apperception-db/spatialyze/actions/workflows/test.yml"><img
    alt="Github Actions Test Status"
    src="https://img.shields.io/github/actions/workflow/status/apperception-db/spatialyze/test.yml?branch=main&label=Test&style=for-the-badge"
  ></a>
  <a href="https://github.com/apperception-db/spatialyze/actions/workflows/check.yml"><img
    alt="Github Actions Type Check Status"
    src="https://img.shields.io/github/actions/workflow/status/apperception-db/spatialyze/check.yml?branch=main&label=Type%20Check&style=for-the-badge"
  ></a>
  <a href="https://github.com/apperception-db/spatialyze/actions/workflows/lint.yml"><img
    alt="Github Actions Lint Status"
    src="https://img.shields.io/github/actions/workflow/status/apperception-db/spatialyze/lint.yml?branch=main&label=Lint&style=for-the-badge"
  ></a>
  <a href="https://codecov.io/gh/apperception-db/spatialyze"><img
    alt="Codecov Coverage Status"
    src="https://img.shields.io/codecov/c/github/apperception-db/spatialyze/main?label=Coverage&style=for-the-badge"
  ></a>
  <a href="https://github.com/psf/black"><img
    alt="Black Badge"
    src="https://img.shields.io/badge/black-000000.svg?label=Code%20style&style=for-the-badge"
  ></a>
  <br/>
  <a href="https://arxiv.org/abs/2308.03276"><img
    alt="ArXiv Paper"
    src="https://img.shields.io/badge/2308.03276-b31b1b.svg?label=arXiv&style=for-the-badge"
  ></a>
  <a href="https://doi.org/10.14778/3665844.3665846"><img
    alt="DOI"
    src="https://img.shields.io/badge/10.14778/3665844.3665846-000.svg?label=dl.acm&style=for-the-badge"
  ></a>
  <a href="https://vldb.org/pvldb/volumes/17/paper/Spatialyze%3A%20A%20Geospatial%20Video%20Analytics%20System%20with%20Spatial-Aware%20Optimizations"><img
    alt="VLDB"
    src="https://img.shields.io/badge/2024-a3302a.svg?label=vldb&style=for-the-badge"
  ></a>
  <a href="https://spatialyze.github.io"><img
    alt="spatialyze.github.io"
    src="https://img.shields.io/badge/github.io-f8d68c.svg?label=spatialyze&style=for-the-badge"
  ></a>
<!--   <img
    alt="Test Count"
    src="https://gist.githubusercontent.com/chanwutk/b32bb8bf89a237c0f13da5e17abc1cd9/raw/test-count-badge.svg"
  > -->
</p>

## Abstract
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
- docker
- cuda >= 11.7 (If using GPU)
```

## Setup Spatialyze
### Clone the Spatialyze repo
```bash
git clone --recurse-submodules git@github.com:apperception-db/spatialyze.git
cd spatialyze

# clone submodules
git submodule update --init --recursive
```

### Using Docker Compose
```base
docker compose up --build --detach
```

### Development
You can then find the project root in `spatialyze` container inside `/workspace`.
You can then use VSCode's Remote Explorer (Dev Containers) to connect to the running `spatialyze` container.
Once connected, run `cd /workspace && code .` to open VSCode in the project root.

### If using DeepSORT (Optional)
Building `rank_cylib` will speed up DeepSORT.
```bash
cd /workspace/spatialyze/video_processor/modules/yolo_deepsort/deep_sort/deep/reid/torchreid/metrics/rank_cylib
make
# If make does not work (use your current python interpreter)
python setup.py build_ext --inplace
rm -rf build
```

## Spatialyze Demo

Run the following command inside the `spatialyze` container.
```sh
poetry run jupyter-lab
```

The demo notebook first constructs the world. Then it queries for the trajectory of the cars that appeared once in an area of interests within some time interval.
### Example demos
- [evaluation/examples/example-query.ipynb](./evaluation/examples/example-query.ipynb)
- [evaluation/examples/evaluation-queries.ipynb](./evaluation/examples/evaluation-queries.ipynb)

## API Reference
Please visit https://apperception-db.github.io/spatialyze for API Reference.

## Citing Spatialyze
This paper will be presented at [VLDB](https://vldb.org/2024/).
```bib
@article{10.14778/3665844.3665846,
    author = {Kittivorawong, Chanwut and Ge, Yongming and Helal, Yousef and Cheung, Alvin},
    title = {Spatialyze: A Geospatial Video Analytics System with Spatial-Aware Optimizations},
    year = {2024},
    issue_date = {May 2024},
    publisher = {VLDB Endowment},
    volume = {17},
    number = {9},
    issn = {2150-8097},
    url = {https://doi.org/10.14778/3665844.3665846},
    doi = {10.14778/3665844.3665846},
    journal = {Proc. VLDB Endow.},
    month = {june},
    pages = {2136-2148},
    numpages = {13}
}
```

## Codecov
<img width="100%" src="https://codecov.io/gh/apperception-db/spatialyze/graphs/icicle.svg?token=A4FHKVI1Ua" />
