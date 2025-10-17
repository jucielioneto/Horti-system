import os
from flask import Flask
from flask import jsonify
from flask import request
from flask import send_from_directory
from flask_cors import CORS

# Local imports
from routes.lojas import lojas_bp
from routes.compras import compras_bp
from routes.logistica import logistica_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # Blueprints
    app.register_blueprint(lojas_bp, url_prefix="/api/lojas")
    app.register_blueprint(compras_bp, url_prefix="/api/compras")
    app.register_blueprint(logistica_bp, url_prefix="/api/logistica")

    @app.route("/api/health", methods=["GET"])  # simple readiness probe
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    # Serve frontend files
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

    @app.route("/", methods=["GET"])  # root serves frontend index
    def index() -> any:
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>", methods=["GET"])  # serve other frontend assets
    def static_files(path: str) -> any:
        return send_from_directory(frontend_dir, path)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


