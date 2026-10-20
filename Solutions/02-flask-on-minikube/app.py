"""Small Flask service used to practise deploying to Kubernetes."""
import os
import socket

from flask import Flask, jsonify

app = Flask(__name__)

PORT = int(os.environ.get("PORT", "15000"))
GREETING = os.environ.get("GREETING", "Hello from Flask on Minikube!")


@app.route("/")
def index():
    return GREETING + "\n"


@app.route("/healthz")
def healthz():
    return jsonify(status="ok")


@app.route("/whoami")
def whoami():
    # Inside a Pod the hostname is the Pod name, which is handy for later labs.
    return jsonify(pod=socket.gethostname())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
