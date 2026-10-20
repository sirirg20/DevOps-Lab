"""Product catalog service: read-only list of products."""
import socket

from flask import Flask, jsonify

PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 55000},
    {"id": 2, "name": "Smartphone", "price": 22000},
    {"id": 3, "name": "Headphones", "price": 2500},
]


def create_app():
    app = Flask(__name__)
    pod = socket.gethostname()

    @app.after_request
    def add_pod_header(response):
        # Lets you see which replica answered (the hostname is the Pod name).
        response.headers["X-Served-By"] = pod
        return response

    @app.route("/products")
    def products():
        return jsonify(PRODUCTS)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
