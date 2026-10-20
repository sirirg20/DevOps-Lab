"""Shared helpers for the Lab 5 Docker SDK scripts."""
import pathlib
import time
import urllib.error
import urllib.request

import docker

HERE = pathlib.Path(__file__).parent
IMAGE = "lab5-flask:1.0"
PROFILE = "lab5-restricted"
LABEL = {"lab": "05-docker-apparmor"}


def client():
    return docker.from_env()


def build_image(cli):
    print(f"==> Building {IMAGE}")
    cli.images.build(path=str(HERE), tag=IMAGE, rm=True)


def run_container(cli, name, apparmor):
    """Start the app with the given AppArmor setting on a random host port."""
    return cli.containers.run(
        IMAGE,
        name=name,
        detach=True,
        ports={"5000/tcp": None},
        security_opt=[f"apparmor={apparmor}"],
        labels=LABEL,
    )


def host_port(cli, container):
    container.reload()
    return container.ports["5000/tcp"][0]["HostPort"]


def wait_for_http(url, attempts=20, delay=0.5):
    last = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.status, resp.read().decode()
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            last = exc
            time.sleep(delay)
    raise RuntimeError(f"{url} did not respond: {last}")


def remove(container):
    try:
        container.remove(force=True)
    except docker.errors.NotFound:
        pass
