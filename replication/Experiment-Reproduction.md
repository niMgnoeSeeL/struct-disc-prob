# Instructions for reproducing the experiments on the paper "Dependency-aware Residual Risk Analysis"

This document explains how to reproduce the experiments from the paper and how to run the modified AFL++ on your own targets. We built our implementation on top of AFL++ to record:

- number of discovered basic blocks
- number of singleton basic blocks (executed only once so far)
- number of singleton clusters (see the paper for the definition)

The instructions are split into two parts:

1. Using modified AFL++ to record fuzzing information.
2. Integrating modified AFL++ with FuzzBench to reproduce the experiments.

If you only want to reproduce the paper's experiments, you can follow Part 2 directly. If you want to apply the modified AFL++ to your own targets, follow Part 1 first.

## Directory Structure

The directory contains three sub-directories:

- `modi-aflpp/`: Resources used to modify AFL++. Recording the fuzzing information for residual risk analysis is done by using the custom post processing feature of AFL++. The resources include the source code files: `custom_post_run.c`, `set.h`, and `set.c`. The shared `custom_post_run.c` is for the greybox version; for blackbox and blackbox-no-reduction versions, use the respective branches in the modified AFL++ repository.
- `docker/`: Docker-based environment to run the modified AFL++ and produce `records.csv`, the recorded residual risk information, on a sample target (`libxml2`).
- `resources/`: The resource directory that contains the subject programs and interfaces to combine with FuzzBench. It contains the subject programs used in the experiments in the paper.

## Environment Setup

Our implementation is built on top of AFL++ and FuzzBench. Therefore the environment requirements are the same as for AFL++ and FuzzBench. Below are the documents that provide the instructions to set up the environment for AFL++ and FuzzBench:

- [Build and install AFL++](https://aflplus.plus/building/)
- [FuzzBench Prerequisites](https://google.github.io/fuzzbench/getting-started/prerequisites/) (Only for Part 2)

### System Requirements

Measured on the single-run Docker image (blackbox branch):

- Docker image size: 7.44 GB (`aflpp-covrec-blackbox:latest`)
- `/opt/AFLplusplus`: 2.7 GB
- `/opt/libxml2`: 108 MB
- Output dir after a short run: 460 KB (`/opt/libxml2/fuzz/out`)
- Container memory (after 5s of `afl-fuzz`): 36.85 MiB (via `docker stats --no-stream`)

Full FuzzBench reproduction requirements depend on the number of benchmarks, time budgets, and repetitions; measure on your target setup.

FuzzBench does not publish fixed system requirements. Its local experiment guide notes that trials do not enforce resource limits (CPU/memory), and provides flags to limit runner and measurer CPU usage. See the FuzzBench local experiment guide for details:

- https://github.com/google/fuzzbench/blob/master/docs/running-a-local-experiment/running_a_local_experiment.md

### Reproducibility Scope

- **Single-run**: Docker-based run in `docker` builds AFL++ (branch selectable) and runs a sample target (`libxml2`) to produce `records.csv`.
- **Full experiments**: FuzzBench integration using `resources/fuzzers` and `resources/benchmarks` to reproduce the paper's blackbox/blackbox-no-reduction/greybox experiments.

### Expected Runtime / Cost

These are typical ranges and depend on hardware:

- Docker build (AFL++ + dependencies, single-run image): < 30 minutes.
- Single-run example (libxml2): depends on fuzzing duration.
- Full FuzzBench experiments: depends on the number of benchmarks, trials, and time budgets.

### Output Data Locations

- AFL++ custom post-run metrics: `records.csv` in the AFL++ output directory (`-o`).
- Example Docker run: `/opt/libxml2/fuzz/out/records.csv` inside the container.
- FuzzBench results: the standard FuzzBench output directories under your FuzzBench workspace.

## Part 1: Using Modified AFL++ to Record Fuzzing Information

We modified AFL++ to record the fuzzing information. The modified AFL++ is available at https://github.com/niMgnoeSeeL/aflpp-covrec. The repository contains three branches:

- `blackbox`: The branch contains the modified AFL++ to record the fuzzing information for blackbox fuzzing.
- `blackbox-no-reduction`: The branch contains the modified AFL++ to record the fuzzing information for blackbox fuzzing without the node reduction.
- `greybox`: The branch contains the modified AFL++ to record the fuzzing information for greybox fuzzing.

We also provide a Docker-based setup under `docker` that builds AFL++ from a chosen branch (`AFLPP_BRANCH=blackbox|blackbox-no-reduction|greybox`) and prepares a single-run example. See `docker/Dockerfile` and `docker/commands.sh` for build/run commands.

### Build (manual)

1. Clone the modified AFL++ repository:

    ```bash
    $ git clone -b {branch} {modified-aflpp-repo} {aflpp-root} # branch: blackbox | blackbox-no-reduction | greybox
    ```

2. Ordinary AFL++ build steps:

    ```bash
    $ cd {aflpp-root}
    $ sudo make && sudo make install
    ```

3. Build `custom_post_run.c`

    `custom_post_run.c` is a file that contains the code to record the fuzzing information. The file is available in the `{aflpp-root}/custom_mutators/examples` directory. The code in the file is called after each run of the target program with the input generated by AFL++. The code records the fuzzing information and writes it to a file: `records.csv` in the AFL++ output directory.

    If you want to use the most recent version of AFL++, you need to manually add `custom_post_run.c` from our git repository or from `modi-aflpp/` to the `{aflpp-root}/custom_mutators/examples` directory.

    To build `custom_post_run.c`, follow the instructions below:

    ```bash
    $ cd {aflpp-root}/custom_mutators/examples
    $ gcc -shared -fPIC -Wall -O3 -I${aflpp-root}/include set.h set.c custom_post_run.c -o custom_post_run.so
    $ export AFL_CUSTOM_MUTATOR_LIBRARY="${aflpp-root}/custom_mutators/examples/custom_post_run.so"
    ```

4. Build and run the target program with AFL++

    Follow the instructions in the AFL++ documentation to build and run the target program with AFL++. Then, the regular fuzzing process will be conducted, and the fuzzing information will be recorded in the `records.csv` file in the AFL++ output directory.

    > In folder `modi-aflpp`, we separately provide the resources used to modify AFL++: `custom_post_run.c`, `set.h`, and `set.c`. Those files are not needed to run the modified AFL++ with the docker image or with FuzzBench, as they are already included in the modified AFL++ repository. However, they are provided for reference and can be used to understand how the fuzzing information is recorded.

## Part 2: Integrating Modified AFL++ with FuzzBench

To conduct the experiments on FuzzBench, we need to integrate the modified AFL++ with FuzzBench. Below are the instructions to integrate the modified AFL++ with FuzzBench:

### 1) Clone the FuzzBench repository

```bash
$ git clone {fuzzbench-repo}
$ cd fuzzbench
```

### 2) Copy the modified AFL++ fuzzer directories

The list of fuzzers in FuzzBench is available in the `fuzzers` directory. One can add a new fuzzer by adding a new directory under the `fuzzers` directory. To integrate the modified AFL++ with FuzzBench, copy the directories under `resources/fuzzers` to the `fuzzers` directory in the FuzzBench repository.

```bash
$ cd replication
$ cp -r resources/fuzzers/blackbox {fuzzbench-repo}/fuzzers
$ cp -r resources/fuzzers/blackbox-no-reduction {fuzzbench-repo}/fuzzers
$ cp -r resources/fuzzers/greybox {fuzzbench-repo}/fuzzers
```

### 3) Build and run the modified AFL++ with FuzzBench

With the following command, the modified AFL++ will be built and run with FuzzBench.

```bash
$ cd {fuzzbench-repo}
$ make build-{blackbox,blackbox-no-reduction,greybox}-{benchmark}
$ make run-{blackbox,blackbox-no-reduction,greybox}-{benchmark}
```

### Subject Programs Used in the Experiments

Under `resources/benchmarks`, we provide the list of subject programs used in the experiments.

1. It contains eight subject programs used for discovery probability analysis (RQ1, 2, and 4): `sqlite3`, `freetype2`, `libxml2`, `libjpeg`, `zlib`, `libpcap`, `jsoncpp`, and `libpng`. Those subject programs are from the FuzzBench benchmark suite (commit: `2920e74f192e1b7add95eb5ac49b0e0049d1c876`). Their directories are named as `cov_<subject>`, where `<subject>` is the name of the subject program.

2. It also contains four subject programs used for residual risk analysis (RQ3): `assimp`, `file`, `harfbuzz`, and `libxml2`. Those subject programs are from the FuzzBench benchmark suite (branch: `new-exp`) and the previous study "Regression Greybox Fuzzing" by Zhu et al. (CCS'21). Their directories are named as `bug_<subject>`, where `<subject>` is the name of the subject program.

We share the subject programs in case the FuzzBench benchmark suite is updated.

To run the experiments, copy the subject programs to the `fuzzbench-repo/benchmarks` directory.

```bash
$ cd replication
$ cp -r resources/benchmarks/* {fuzzbench-repo}/benchmarks
```
