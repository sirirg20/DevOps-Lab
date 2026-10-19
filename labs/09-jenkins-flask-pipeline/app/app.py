"""Small Flask service that the Lab 9 pipeline builds, tests, packages and deploys."""
import pathlib

from flask import Flask, jsonify

VERSION_FILE = pathlib.Path(__file__).with_name("VERSION")


def read_version():
    """The pipeline writes VERSION into the package; a source checkout has none."""
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "dev"
    except FileNotFoundError:
        return "dev"


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Hello from the Flask pipeline!\n"

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.route("/version")
    def version():
        return jsonify(version=read_version())

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
