"""Shopping cart service: GET/POST/DELETE /cart, backed by a shared store."""
import os
import socket

from flask import Flask, jsonify, request

from cart_store import build_store

MAX_ITEM_LENGTH = 100


def create_app(store=None):
    app = Flask(__name__)
    store = store if store is not None else build_store(os.environ)
    pod = socket.gethostname()

    @app.after_request
    def add_pod_header(response):
        response.headers["X-Served-By"] = pod
        return response

    @app.get("/cart")
    def get_cart():
        items = store.items()
        return jsonify(items=items, count=len(items))

    @app.post("/cart")
    def add_item():
        data = request.get_json(silent=True)
        item = data.get("item") if isinstance(data, dict) else None
        if not isinstance(item, str) or not item.strip():
            return jsonify(error="body must be JSON like {\"item\": \"name\"}"), 400
        item = item.strip()
        if len(item) > MAX_ITEM_LENGTH:
            return jsonify(error=f"item longer than {MAX_ITEM_LENGTH} characters"), 400
        store.add(item)
        return jsonify(added=item, count=len(store.items())), 201

    @app.delete("/cart")
    def clear_cart():
        store.clear()
        return "", 204

    @app.get("/livez")
    def livez():
        # Liveness must not depend on Redis: restarting this Pod would not fix Redis.
        return jsonify(status="alive")

    @app.get("/health")
    def health():
        # Readiness does depend on the store: without it this replica cannot serve a cart.
        if store.ping():
            return jsonify(status="ok")
        return jsonify(status="store unavailable"), 503

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
