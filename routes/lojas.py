from flask import Blueprint
from flask import jsonify
from flask import request

from models.produto import (
    init_schema,
    seed_default_stores,
    seed_default_suppliers,
    list_products,
    create_order,
)
from utils.import_excel import import_products_from_excel


lojas_bp = Blueprint("lojas", __name__)


@lojas_bp.route("/init", methods=["POST"])  # initialize DB if needed
def init() -> tuple:
    init_schema()
    seed_default_stores()
    seed_default_suppliers()
    # Optional Excel import if provided path
    data = request.get_json(silent=True) or {}
    excel_path = data.get("excel_path")
    imported = 0
    if excel_path:
        try:
            imported = import_products_from_excel(excel_path)
        except Exception:
            imported = 0
    return jsonify({"ok": True, "imported": imported}), 200


@lojas_bp.route("/produtos", methods=["GET"])  # list products with optional search
def produtos() -> tuple:
    search = request.args.get("q")
    rows = list_products(search)
    return jsonify(rows), 200


@lojas_bp.route("/pedido", methods=["POST"])  # create order
def pedido() -> tuple:
    data = request.get_json(force=True)
    store_code = data.get("store_code")
    items = data.get("items", [])
    order_id = create_order(store_code, None, items)
    return jsonify({"order_id": order_id}), 201


