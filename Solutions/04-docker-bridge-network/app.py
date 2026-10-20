"""Flask API that reports whether its sibling containers are reachable by name."""
import os
import socket

from flask import Flask, jsonify

app = Flask(__name__)

PORT = int(os.environ.get("PORT", "5001"))
DEPENDENCIES = {
    "db": (os.environ.get("DB_HOST", "db"), int(os.environ.get("DB_PORT", "3306"))),
    "cache": (os.environ.get("CACHE_HOST", "cache"), int(os.environ.get("CACHE_PORT", "6379"))),
}


def probe(host, port, timeout=2):
    """Resolve `host` through Docker DNS and try a TCP connection."""
    result = {"host": host, "port": port}
    try:
        result["address"] = socket.gethostbyname(host)
    except socket.gaierror as exc:
        result.update(resolved=False, reachable=False, error=str(exc))
        return result
    result["resolved"] = True
    try:
        with socket.create_connection((host, port), timeout=timeout):
            result["reachable"] = True
    except OSError as exc:
        result.update(reachable=False, error=str(exc))
    return result


@app.route("/about")
def about():
    return jsonify(service="flask-api", container=socket.gethostname(), port=PORT)


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/deps")
def deps():
    results = {name: probe(host, port) for name, (host, port) in DEPENDENCIES.items()}
    ok = all(r["reachable"] for r in results.values())
    return jsonify(ok=ok, dependencies=results), (200 if ok else 503)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
