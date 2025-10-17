from flask import Blueprint
from flask import jsonify
from flask import request
from flask import send_file

from models.produto import (
    list_logistics,
    update_received,
    store_totals,
)


logistica_bp = Blueprint("logistica", __name__)


@logistica_bp.route("/itens", methods=["GET"])  # list logistics items
def itens() -> tuple:
    supplier = request.args.get("supplier")
    q = request.args.get("q")
    rows = list_logistics(supplier, q)
    return jsonify(rows), 200


@logistica_bp.route("/recebimento/<int:plan_id>", methods=["PUT"])  # update received qty
def recebimento(plan_id: int) -> tuple:
    data = request.get_json(force=True)
    qty = float(data.get("received_quantity", 0))
    update_received(plan_id, qty)
    return jsonify({"ok": True}), 200


from utils.export_excel import export_store_excel
from utils.export_txt import export_store_txt


@logistica_bp.route("/export/store/<string:store_code>/excel", methods=["GET"])  # per-store Excel
def export_store_excel_route(store_code: str) -> tuple:
    rows = store_totals(store_code)
    content = export_store_excel(rows, store_code)
    from io import BytesIO
    bio = BytesIO(content)
    return send_file(
        bio,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{store_code.lower()}_pedido.xlsx",
    )


@logistica_bp.route("/export/store/<string:store_code>/txt", methods=["GET"])  # per-store TXT (VR MASTER)
def export_store_txt_route(store_code: str) -> tuple:
    rows = store_totals(store_code)
    content = export_store_txt(rows)
    from io import BytesIO
    bio = BytesIO(content)
    return send_file(
        bio,
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name=f"{store_code.lower()}_vr_master.txt",
    )

# New endpoints for supplier-focused logistics view
from models.produto import get_connection


@logistica_bp.route("/fornecedores", methods=["GET"])  # list suppliers present in logistics_plan
def fornecedores() -> tuple:
    sql = (
        "SELECT DISTINCT sp.name as supplier FROM logistics_plan lp LEFT JOIN suppliers sp ON sp.id = lp.supplier_id "
        "WHERE lp.sent_to_logistics = 1 ORDER BY supplier"
    )
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return jsonify([r["supplier"] for r in rows if r["supplier"]]), 200


@logistica_bp.route("/plano-fornecedor", methods=["GET"])  # items by supplier with per-store split
def plano_fornecedor() -> tuple:
    supplier = request.args.get("supplier")
    search = request.args.get("q")
    sql = (
        "SELECT lp.id as plan_id, p.code, p.name, p.unit, sp.name as supplier, lp.expected_quantity, "
        "COALESCE(lr.received_quantity, 0) as received_quantity "
        "FROM logistics_plan lp JOIN products p ON p.id = lp.product_id "
        "LEFT JOIN suppliers sp ON sp.id = lp.supplier_id "
        "LEFT JOIN logistics_received lr ON lr.logistics_plan_id = lp.id WHERE lp.sent_to_logistics = 1"
    )
    params = []
    if supplier:
        sql += " AND sp.name = ?"
        params.append(supplier)
    if search:
        sql += " AND (p.code LIKE ? OR p.name LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    sql += " ORDER BY p.code"
    with get_connection() as conn:
        items = [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
        # attach distribution per store
        for it in items:
            dist_rows = conn.execute(
                "SELECT s.code as store_code, s.name as store_name, ld.quantity FROM logistics_distribution ld JOIN stores s ON s.id = ld.store_id WHERE ld.logistics_plan_id = ?",
                (it["plan_id"],)
            ).fetchall()
            it["distribution"] = [dict(r) for r in dist_rows]
        return jsonify(items), 200


@logistica_bp.route("/distribuir/<int:plan_id>", methods=["POST"])  # save per-store distribution
def distribuir(plan_id: int) -> tuple:
    data = request.get_json(force=True)
    distribution = data.get("distribution", [])  # [{store_code, quantity}]
    with get_connection() as conn:
        # resolve store ids and upsert
        for d in distribution:
            store_code = d.get("store_code")
            qty = float(d.get("quantity", 0))
            store = conn.execute("SELECT id FROM stores WHERE code = ?", (store_code,)).fetchone()
            if not store:
                continue
            conn.execute(
                "INSERT INTO logistics_distribution(logistics_plan_id, store_id, quantity) VALUES(?, ?, ?) "
                "ON CONFLICT(logistics_plan_id, store_id) DO UPDATE SET quantity=excluded.quantity",
                (plan_id, int(store["id"]), qty)
            )
        conn.commit()
    return jsonify({"ok": True}), 200


