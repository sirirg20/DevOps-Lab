# Labs

Each lab lives in its own folder and follows the same layout:

```
labs/NN-name/
├── README.md     objectives, prerequisites, steps, verification, cleanup
├── deploy.sh     (where applicable) automates the steps in the README
├── cleanup.sh    (where applicable) removes everything the lab created
└── ...           lab-specific source, manifests and configuration
```

| #  | Lab                                          | Folder                       | Status  |
|----|----------------------------------------------|------------------------------|---------|
| 1  | Kubernetes: Hello Pod                        | `01-k8s-hello-pod`           | written, untested at runtime |
| 2  | Flask application on Minikube                | `02-flask-on-minikube`       | written, untested at runtime |
| 3  | ReplicaSets and scaling                      | `03-replicasets-scaling`     | written, untested at runtime |
| 4  | Docker bridge networking                     | `04-docker-bridge-network`   | written, untested at runtime |
| 5  | Docker security and AppArmor                 | `05-docker-apparmor`         | written, untested at runtime (needs Linux + AppArmor) |
| 6  | Prometheus/Grafana monitoring + Jenkins      | `06-monitoring-and-jenkins`  | written, untested at runtime |
| 7  | Jenkins installation                         | `07-jenkins-install`         | written, untested at runtime |
| 8  | Jenkins Freestyle job                        | `08-jenkins-freestyle`       | written, untested at runtime |
| 9  | Multi-stage Jenkins pipeline for Flask       | `09-jenkins-flask-pipeline`  | written, untested at runtime |
| 10 | Multi-node Minikube, multiple applications   | `10-minikube-multi-app`      | written, untested at runtime |

All ten labs are written. Most labs add extra scripts and files beyond the layout above.

**What "written, untested at runtime" means.** The lab's files exist and its static
checks and dependency-free unit tests pass (where it has any). Nothing has been run
against real Docker, Kubernetes/Minikube, Jenkins or AppArmor, and the Flask unit tests
have not been run. Treat every `deploy.sh`, `verify.sh`, pipeline and manifest as
untested until you run it.

**Run one Jenkins lab at a time.** Labs 6, 7, 8 and 9 each start their own Jenkins
controller on host port 8080. Stop one (`./cleanup.sh`) before starting another. Labs 7, 8
and 9 honor `JENKINS_PORT`; Lab 6's `jenkins.sh` always uses 8080.

See [`../docs/prerequisites.md`](../docs/prerequisites.md) for tooling and ports, and
[`../docs/testing-status.md`](../docs/testing-status.md) for exactly what was and was not
run on this machine.
