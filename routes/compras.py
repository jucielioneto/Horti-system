from flask import Blueprint
from flask import jsonify
from flask import request
from flask import send_file

from models.produto import (
    list_orders,
    list_order_items,
    consolidate_purchases,
    create_logistics_plan_from_consolidation,
    seed_default_suppliers,
    list_store_order_totals,
    assign_supplier,
    list_assignments,
    consolidated_by_supplier,
)

from utils.export_excel import export_store_excel
from utils.export_word import export_consolidated_word


compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/pedidos", methods=["GET"])  # list orders with filters
def pedidos() -> tuple:
    store = request.args.get("store")
    rows = list_orders(store, None)
    return jsonify(rows), 200


@compras_bp.route("/pedido/<int:order_id>", methods=["GET"])  # order detail
def pedido_detail(order_id: int) -> tuple:
    rows = list_order_items(order_id)
    return jsonify(rows), 200


@compras_bp.route("/store/<string:store_code>/totais", methods=["GET"])  # totais por loja (todos os pedidos)
def store_totais(store_code: str) -> tuple:
    rows = list_store_order_totals(store_code)
    return jsonify(rows), 200


@compras_bp.route("/assign", methods=["POST"])  # define fornecedor para (loja, produto)
def set_assign() -> tuple:
    data = request.get_json(force=True)
    store_code = data.get("store_code")
    product_code = data.get("product_code")
    supplier = data.get("supplier")
    assign_supplier(store_code, product_code, supplier)
    return jsonify({"ok": True}), 200


@compras_bp.route("/store/<string:store_code>/assignments", methods=["GET"])  # ver atribuições por loja
def get_assignments(store_code: str) -> tuple:
    rows = list_assignments(store_code)
    return jsonify(rows), 200


@compras_bp.route("/relatorio/consolidado-fornecedor", methods=["GET"])  # consolidado por fornecedor
def rel_consolidado_fornecedor() -> tuple:
    rows = consolidated_by_supplier()
    return jsonify(rows), 200


@compras_bp.route("/relatorio/consolidado", methods=["GET"])  # consolidated across stores
def rel_consolidado() -> tuple:
    rows = consolidate_purchases()
    return jsonify(rows), 200


@compras_bp.route("/enviar-logistica", methods=["POST"])  # finalize and send to logistics
def enviar_logistica() -> tuple:
    data = request.get_json(force=True) if request.data else {}
    supplier = data.get("supplier")
    consolidated = consolidate_purchases()
    create_logistics_plan_from_consolidation(consolidated, supplier)
    return jsonify({"ok": True, "count": len(consolidated)}), 200


@compras_bp.route("/export/excel", methods=["GET"])  # download consolidated Excel
def export_excel() -> tuple:
    consolidated = consolidate_purchases()
    rows = [
        {"code": r["code"], "name": r["name"], "quantity": r["total_quantity"], "unit": r["unit"]}
        for r in consolidated
    ]
    content = export_store_excel(rows, "Consolidado")
    from io import BytesIO
    bio = BytesIO(content)
    return send_file(
        bio,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="consolidado.xlsx",
    )


@compras_bp.route("/export/word", methods=["GET"])  # download consolidated Word
def export_word() -> tuple:
    consolidated = consolidate_purchases()
    rows = [
        {"code": r["code"], "name": r["name"], "quantity": r["total_quantity"], "unit": r["unit"]}
        for r in consolidated
    ]
    content = export_consolidated_word(rows, "Relatório Consolidado")
    from io import BytesIO
    bio = BytesIO(content)
    return send_file(
        bio,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name="consolidado.docx",
    )


