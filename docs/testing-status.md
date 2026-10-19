# Testing status

This page records what was actually run and what was not. A check is listed as passing
only if it was run and passed on the development machine.

**Environment used for the checks:** Windows 11 with Git, Git Bash and Python 3.11. Not
installed: Docker, Docker Compose, kubectl, Minikube, WSL, Flask, `prometheus_client`,
PyYAML, flake8, pytest. Hardware virtualization was reported as disabled.

## Summary

| | Count | Meaning |
|---|---|---|
| **Passing** | 151 checks in 10 suites | Static and unit tests that need no Docker, Kubernetes, Jenkins, AppArmor or Flask. |
| **Not run: needs Flask** | 7 test files | `ModuleNotFoundError: No module named 'flask'`. |
| **Not run: needs real infrastructure** | everything else | Image builds, containers, clusters, Jenkins, AppArmor, and every `deploy.sh`, `verify.sh`, `scale.sh`, `failover.sh` and pipeline stage. |

**No lab has been run end-to-end.** Passing tests here say that the files are
internally consistent and that the logic they cover works; they do not show that a
container builds, a manifest is accepted by Kubernetes, a Jenkins job loads, or a
profile loads into a kernel.

## What passes (static and unit tests)

Run each from the repository root (no installs required):

```bash
python labs/05-docker-apparmor/test_profile_static.py                      #  6  profile text checks
(cd labs/06-monitoring-and-jenkins/exporter && python test_simulator.py)   #  5  simulator logic
python labs/06-monitoring-and-jenkins/test_configs.py                      # 14  cross-file config consistency
python labs/07-jenkins-install/test_static.py                              # 18  file structure and safety
bash   labs/08-jenkins-freestyle/test_hello_world.sh                       #  6  sample script behavior
python labs/08-jenkins-freestyle/test_static.py                            # 14  job XML rendering, repo helper
python labs/09-jenkins-flask-pipeline/test_pipeline.py                     # 36  ci/ scripts run for real, Jenkinsfile structure
python labs/10-minikube-multi-app/test_miniyaml.py                         # 10  YAML-subset reader
python labs/10-minikube-multi-app/test_manifests.py                        # 28  manifest and script cross-checks
(cd labs/10-minikube-multi-app/apps/shopping-cart && python test_cart_store.py)   # 14  cart stores (fake Redis)
```

Total 151. The Lab 8 and Lab 9 suites also need `bash` (and `git` for Lab 8, `curl` and `tar` for Lab 9).
Every `.sh` file passes `bash -n` (45 files) and every `.py` file parses (30 files).

Several suites were also checked with deliberate breakages in throwaway copies, to confirm
that they fail when something is wrong (Labs 7, 8, 9 and 10). That shows the tests are
sensitive; it does not test the labs.

## Not tested, by technology

| Technology | What is untested |
|------------|------------------|
| **Docker** | All image builds (every Dockerfile), `docker run`, networks and volumes. Labs 2-10. |
| **Docker Compose** | Every `docker-compose.yml` and compose-based script (labs 6, 7, 8, 9). |
| **Kubernetes / Minikube** | Every manifest has never been applied; they were checked only by the lab's own YAML-subset reader or a light text check, not by the API server. Scaling, self-healing, node draining, topology spread, PodDisruptionBudgets, `imagePullPolicy: Never` image loading onto all nodes. Labs 1, 2, 3, 10. |
| **Jenkins** | Image builds, plugin installation, the init Groovy script (text-checked only), job XML for labs 8 and 9 (well-formed but never loaded by Jenkins), REST job creation and CSRF-crumb calls, the Freestyle build, and all pipeline stages including JUnit publishing and artifact archiving. Labs 6-9. |
| **AppArmor** | The profile has never been loaded into a kernel; `apparmor_parser`, `apply_profile.py` and `check_restrictions.py` have never run. Lab 5. |
| **Flask** | The unit tests in the 7 files below, plus running any Flask app. |
| **Prometheus / Grafana** | `promtool check config`, scraping, alert rules firing, Grafana provisioning loading the dashboard. Lab 6. |
| **Other libraries** | `prometheus_client` (so `delivery_metrics.py` has never executed), the real `redis` client, `pytest`, `flake8`, `gunicorn`. |

The 7 Flask-dependent test files:

```
labs/02-flask-on-minikube/test_app.py
labs/03-replicasets-scaling/test_app.py
labs/04-docker-bridge-network/test_app.py
labs/05-docker-apparmor/test_app.py
labs/09-jenkins-flask-pipeline/app/test_app.py
labs/10-minikube-multi-app/apps/product-catalog/test_app.py
labs/10-minikube-multi-app/apps/shopping-cart/test_app.py
```

## Per-lab table

Legend: **passed** = run and passed here · **not run** = could be run with the missing
dependency installed · **blocked** = needs Docker, Kubernetes, Jenkins or AppArmor ·
**n/a** = the lab has no such tests.

| Lab | Static checks (syntax, config) | Unit tests | Runtime (containers, clusters, Jenkins) |
|-----|--------------------------------|-----------|------------------------------------------|
| 1   | `bash -n` passed; YAML only lightly checked by text (indent, keys, selector match), not parsed | n/a | blocked: kubectl, Minikube |
| 2   | `bash -n`, `py_compile` passed; light YAML text check | not run (Flask) | blocked: Docker, Minikube |
| 3   | `bash -n`, `py_compile` passed; light YAML text check | not run (Flask) | blocked: Docker, Minikube |
| 4   | `bash -n`, `py_compile` passed | not run (Flask) | blocked: Docker |
| 5   | `bash -n`, `py_compile` passed; `test_profile_static.py` passed (profile text only, never loaded into a kernel) | Flask `test_app.py` not run | blocked: Docker, Linux with AppArmor |
| 6   | `bash -n`, `py_compile` passed; `test_configs.py` 14/14 passed (no YAML parser, no `promtool`) | simulator 5/5 passed; `delivery_metrics.py` never executed | blocked: Docker; Jenkins pipeline never executed |
| 7   | `bash -n` passed; `test_static.py` 18/18 passed; Groovy only text-checked | n/a | blocked: Docker; build, plugins, startup, `verify.sh` never run |
| 8   | `bash -n` passed; `test_static.py` 14/14 passed; job XML parses as XML but was never loaded by Jenkins | `test_hello_world.sh` 6/6 passed | blocked: Docker; image build, Jenkins startup, REST job creation, build never run |
| 9   | `bash -n`, `py_compile` passed; job XML parses but was never loaded by Jenkins; `flake8` not run (stand-in style check only) | `test_pipeline.py` 36/36 passed (ci scripts really run, Jenkinsfile structure); Flask `app/test_app.py` not run | blocked: Docker; no pipeline stage ever executed by Jenkins |
| 10  | `bash -n`, `py_compile` passed; `test_manifests.py` 28/28 and `test_miniyaml.py` 10/10 passed (own YAML-subset reader; never validated by the Kubernetes API server) | `test_cart_store.py` 14/14 passed (fake Redis); Flask `test_app.py` in both apps not run | blocked: Docker, Minikube; no cluster, scaling, drain or failover ever run |

Syntax and structural checks do not show that a manifest, pipeline or container works.
Only the runtime column does, and none of it has been run. Update this page when that changes.
