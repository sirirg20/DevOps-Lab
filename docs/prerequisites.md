# Prerequisites

Nothing in this list has been installed or exercised on the development machine
beyond Git, Python and Git Bash; see [testing-status.md](testing-status.md). The
table says what each lab's scripts and tests genuinely call.

## Tools

| Tool | Needed by | Why |
|------|-----------|-----|
| Git | all (clone); 6 (`jenkins.sh`), 8 (`make_sample_repo.sh`) | Those two scripts run `git` on the host. |
| Bash and GNU userland (`tar`, `sed`, `awk`, `grep`, `head`, `sort`, `tr`, `base64`, `mktemp`, `seq`) | every `*.sh` script, and the Lab 8 and Lab 9 test suites | Scripts start with `#!/usr/bin/env bash`. Written for Linux, WSL or Git Bash and use GNU options (`stat -c`, `xargs -r`, `mv -T`, `head -n -N`); not tested on macOS. |
| Docker (Engine or Desktop) | 2-10; 1-3 and 10 when Minikube uses the Docker driver | Builds images and runs containers. |
| Docker **Compose plugin** (`docker compose`) | 6, 7, 8, 9 | `deploy.sh`/`cleanup.sh`/`verify.sh` call `docker compose`. The scripts check for it and stop with a message. |
| Minikube and kubectl | 1, 2, 3, 10 | Local Kubernetes. Minikube needs a driver (Docker, Hyper-V or VirtualBox). |
| `curl` on the host | 4 (`verify.sh`), 7 (`verify.sh`), 8 and 9 (`lib.sh`, `verify.sh`), and the Lab 9 test suite | Calls ports published on localhost. Lab 10 runs `curl` inside a pod instead, so it needs none on the host. |
| Python 3.10+ | 5-10 for the dependency-free tests; 5 for its SDK scripts | The tests use only the standard library. |
| Flask (`pip install -r requirements.txt` in the lab) | only to run the Flask unit tests in labs 2, 3, 4, 5, 9, 10 | The apps run inside containers, so Flask is not needed on the host to deploy anything. |
| Docker SDK for Python (`pip install -r requirements-sdk.txt`) | 5 | `apply_profile.py` and `check_restrictions.py`. |
| Linux kernel with AppArmor, `apparmor_parser`, `sudo` | 5 | AppArmor is a Linux feature; see Lab 5's README. |

Plugins, Jenkins and the monitoring components (Prometheus, Grafana, Redis, MySQL)
run from container images and need no host install. The first run downloads those
images, so you need internet access.

## Ports

| Port (host) | Used by | Notes |
|-------------|---------|-------|
| 8080 | Jenkins in labs 6, 7, 8 and 9 | **Run only one Jenkins lab at a time.** Labs 7, 8 and 9 honor `JENKINS_PORT`; Lab 6's `jenkins.sh` always uses 8080. Run the lab's `cleanup.sh` before starting another. Bound to `127.0.0.1` in labs 7, 8 and 9. |
| 5001 | Lab 4 (`web` container) | |
| 8000, 9090, 3000 | Lab 6 (exporter, Prometheus, Grafana) | |
| random | Labs 1-3 and 10 (via `minikube service`), Lab 5 test containers | Chosen by Minikube or Docker. |

## Rough resources (estimates, not measured)

- Lab 10 starts three Minikube nodes; plan for about 6 CPUs and 6 GB of RAM.
- Each Jenkins controller wants about 1 GB or more. Lab 6 also runs three other containers.

## Windows notes

- Run the shell scripts from Git Bash or WSL 2.
- Minikube with the Docker driver needs hardware virtualization enabled in firmware
  and Docker Desktop's WSL 2 backend (or Hyper-V). Virtualization was reported as disabled on
  the development machine.
- Lab 5 (AppArmor) cannot run on native Windows. Use a real Linux machine or a VM where you
  control the kernel; Docker Desktop's built-in VM does not let you load custom host profiles.
- Lab 6's `jenkins.sh` mounts the Docker socket and is recommended for Linux or WSL.
- Do not run Docker or Minikube as root just to avoid a permission error. Lab 10 deliberately
  never uses Minikube's `--force`.

## Python setup (only for running the Flask unit tests)

```bash
python -m venv .venv
source .venv/bin/activate          # Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt    # from the lab folder
python -m unittest -v
```

## Conventions

- Scripts try to be idempotent: re-running `deploy.sh` should not fail if resources already
  exist, and `cleanup.sh` should not fail if they are gone. This is the intent; it has not been
  run against real infrastructure.
- No secrets are committed. Credentials come from environment variables or a local `.env` file
  (git-ignored); labs ship a `.env.example` where needed. Scripts that need a password generate
  a random one into `.env` if it is missing.
