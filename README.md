# DevOps Lab

A hands-on learning repository for DevOps concepts, tools, and practical exercises.

## Learning Roadmap

1. Kubernetes: Deploying a Hello Pod
2. Flask Application Deployment on Minikube
3. ReplicaSets and Application Scaling
4. Docker Bridge Networking
5. Docker Security and AppArmor
6. Monitoring with Prometheus and Grafana
7. Jenkins Installation
8. Jenkins Freestyle Jobs
9. Jenkins Multi-stage Pipeline for Flask
10. Multi-node Minikube and Multi-application Deployment

## Repository Structure

```
labs/   one folder per lab, each with its own README (see labs/README.md)
docs/   prerequisites and testing status
```

Each lab contains its own README with objectives, prerequisites, implementation steps, commands, and verification instructions. See [labs/README.md](labs/README.md) for the index, [docs/prerequisites.md](docs/prerequisites.md) for tooling, and [docs/testing-status.md](docs/testing-status.md) for what has and has not been tested.

## Status

All ten labs are written, each with its own README, scripts and configuration.

- **Tested:** the static checks and unit tests that need no Docker, Kubernetes, Jenkins, AppArmor
  or Flask. They pass (151 checks).
- **Not tested:** anything that needs those tools. No lab has been run end-to-end against real
  infrastructure, so every deploy, verify and pipeline step is unverified, and the Flask unit tests
  have not been run.

[docs/testing-status.md](docs/testing-status.md) lists exactly what was and was not run.

## Notes

This repository contains my own implementations and explanations. Any third-party material reused will be attributed where appropriate and subject to its applicable license.
