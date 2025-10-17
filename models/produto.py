import os
import sqlite3
from typing import Iterable, List, Optional, Tuple, Dict, Any


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "horti.db")
DB_PATH = os.path.abspath(DB_PATH)


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        # products
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                unit TEXT NOT NULL CHECK(unit IN ('KG','UN'))
            );
            """
        )

        # suppliers
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            """
        )

        # stores
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT UNIQUE NOT NULL
            );
            """
        )

        # orders (by store)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(store_id) REFERENCES stores(id)
            );
            """
        )

        # order items
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
            """
        )

        # purchases consolidated for logistics
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logistics_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                supplier_id INTEGER,
                expected_quantity REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                sent_to_logistics INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
            );
            """
        )

        # received quantities in logistics
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logistics_received (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logistics_plan_id INTEGER NOT NULL,
                received_quantity REAL NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(logistics_plan_id) REFERENCES logistics_plan(id)
            );
            """
        )

        # assignment of supplier per store/product (for current cycle)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS supplier_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL,
                UNIQUE(store_id, product_id),
                FOREIGN KEY(store_id) REFERENCES stores(id),
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
            );
            """
        )

        # logistics distribution: how expected/received is split to stores per product
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logistics_distribution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logistics_plan_id INTEGER NOT NULL,
                store_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                UNIQUE(logistics_plan_id, store_id),
                FOREIGN KEY(logistics_plan_id) REFERENCES logistics_plan(id),
                FOREIGN KEY(store_id) REFERENCES stores(id)
            );
            """
        )

        conn.commit()


DEFAULT_STORES = [
    ("PIT", "PITUBA"),
    ("VIT", "VITÓRIA"),
    ("VIL", "VILAS"),
    ("API", "APIPEMA"),
    ("RES", "RESTAURANTE"),
    ("PAD", "PADARIA"),
]


def seed_default_stores() -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        for code, name in DEFAULT_STORES:
            cur.execute(
                "INSERT OR IGNORE INTO stores(code, name) VALUES(?, ?)", (code, name)
            )
        conn.commit()


DEFAULT_SUPPLIERS = [
    "erico",
    "irece",
    "elisangela",
    "terra comercio",
    "leo inhame",
    "rubia",
    "solo vivo",
    "bernadete",
]


def seed_default_suppliers() -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        for name in DEFAULT_SUPPLIERS:
            cur.execute("INSERT OR IGNORE INTO suppliers(name) VALUES(?)", (name,))
        conn.commit()


def upsert_product(code: str, name: str, unit: str) -> None:
    unit = unit.upper()
    if unit not in ("KG", "UN"):
        raise ValueError("unit must be 'KG' or 'UN'")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO products(code, name, unit) VALUES(?, ?, ?) ON CONFLICT(code) DO UPDATE SET name=excluded.name, unit=excluded.unit",
            (code, name, unit),
        )
        conn.commit()


def list_products(search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = "SELECT id, code, name, unit FROM products"
    params: Tuple[Any, ...] = tuple()
    if search:
        sql += " WHERE code LIKE ? OR name LIKE ?"
        like = f"%{search}%"
        params = (like, like)
    sql += " ORDER BY code ASC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_or_create_supplier(name: str) -> int:
    name = name.strip()
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM suppliers WHERE name = ?", (name,)).fetchone()
        if row:
            return int(row["id"])
        cur = conn.execute("INSERT INTO suppliers(name) VALUES(?)", (name,))
        conn.commit()
        return int(cur.lastrowid)


def create_order(store_code: str, supplier_name: Optional[str], items: List[Dict[str, Any]]) -> int:
    with get_connection() as conn:
        store = conn.execute("SELECT id FROM stores WHERE code = ?", (store_code,)).fetchone()
        if not store:
            raise ValueError("Unknown store code")
        cur = conn.execute(
            "INSERT INTO orders(store_id) VALUES(?)",
            (int(store["id"]),),
        )
        order_id = int(cur.lastrowid)

        for item in items:
            code = str(item["code"]).strip()
            qty = float(item["quantity"])
            prod = conn.execute("SELECT id FROM products WHERE code = ?", (code,)).fetchone()
            if not prod:
                raise ValueError(f"Unknown product code: {code}")
            conn.execute(
                "INSERT INTO order_items(order_id, product_id, quantity) VALUES(?, ?, ?)",
                (order_id, int(prod["id"]), qty),
            )
        conn.commit()
        return order_id


def list_orders(store_code: Optional[str] = None, supplier: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = (
        "SELECT o.id, o.created_at, s.code AS store_code, s.name AS store_name "
        "FROM orders o JOIN stores s ON s.id = o.store_id WHERE 1=1"
    )
    params: List[Any] = []
    if store_code:
        sql += " AND s.code = ?"
        params.append(store_code)
    sql += " ORDER BY o.created_at DESC, o.id DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


def list_order_items(order_id: int) -> List[Dict[str, Any]]:
    sql = (
        "SELECT p.code, p.name, p.unit, oi.quantity FROM order_items oi "
        "JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ? ORDER BY p.code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (order_id,)).fetchall()
        return [dict(row) for row in rows]


def list_store_order_totals(store_code: str) -> List[Dict[str, Any]]:
    # Per store, per product totals across orders
    sql = (
        "SELECT p.id as product_id, p.code, p.name, p.unit, SUM(oi.quantity) as quantity "
        "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
        "JOIN products p ON p.id = oi.product_id JOIN stores s ON s.id = o.store_id "
        "WHERE s.code = ? GROUP BY p.id, p.code, p.name, p.unit ORDER BY p.code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (store_code,)).fetchall()
        return [dict(row) for row in rows]


def assign_supplier(store_code: str, product_code: str, supplier_name: str) -> None:
    with get_connection() as conn:
        store = conn.execute("SELECT id FROM stores WHERE code = ?", (store_code,)).fetchone()
        prod = conn.execute("SELECT id FROM products WHERE code = ?", (product_code,)).fetchone()
        supplier_id = get_or_create_supplier(supplier_name)
        if not store or not prod:
            raise ValueError("Unknown store or product")
        conn.execute(
            "INSERT INTO supplier_assignments(store_id, product_id, supplier_id) VALUES(?, ?, ?) "
            "ON CONFLICT(store_id, product_id) DO UPDATE SET supplier_id=excluded.supplier_id",
            (int(store["id"]), int(prod["id"]), supplier_id),
        )
        conn.commit()


def list_assignments(store_code: str) -> List[Dict[str, Any]]:
    sql = (
        "SELECT p.code, p.name, p.unit, sp.name as supplier FROM supplier_assignments sa "
        "JOIN stores s ON s.id = sa.store_id JOIN products p ON p.id = sa.product_id "
        "JOIN suppliers sp ON sp.id = sa.supplier_id WHERE s.code = ? ORDER BY p.code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (store_code,)).fetchall()
        return [dict(row) for row in rows]


def consolidated_by_supplier() -> List[Dict[str, Any]]:
    # Sum totals per supplier using assignments; items without assignment won't appear
    sql = (
        "SELECT sp.name as supplier, p.code, p.name, p.unit, SUM(oi.quantity) as total_quantity "
        "FROM supplier_assignments sa JOIN orders o ON o.store_id = sa.store_id "
        "JOIN order_items oi ON oi.order_id = o.id AND oi.product_id = sa.product_id "
        "JOIN products p ON p.id = oi.product_id JOIN suppliers sp ON sp.id = sa.supplier_id "
        "GROUP BY sp.name, p.code, p.name, p.unit ORDER BY sp.name, p.code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def consolidate_purchases() -> List[Dict[str, Any]]:
    # Sum quantities per product across all orders
    sql = (
        "SELECT p.id as product_id, p.code, p.name, p.unit, SUM(oi.quantity) as total_quantity "
        "FROM order_items oi JOIN products p ON p.id = oi.product_id "
        "GROUP BY p.id, p.code, p.name, p.unit ORDER BY p.code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def store_totals(store_code: str) -> List[Dict[str, Any]]:
    # Sum quantities per product for a given store across all its orders
    sql = (
        "SELECT p.code, p.name, p.unit, SUM(oi.quantity) as quantity "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "JOIN products p ON p.id = oi.product_id "
        "JOIN stores s ON s.id = o.store_id "
        "WHERE s.code = ? "
        "GROUP BY p.code, p.name, p.unit "
        "ORDER BY p.code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (store_code,)).fetchall()
        return [dict(row) for row in rows]


def create_logistics_plan_from_consolidation(consolidated: List[Dict[str, Any]], supplier_name: Optional[str]) -> None:
    supplier_id: Optional[int] = None
    if supplier_name:
        supplier_id = get_or_create_supplier(supplier_name)
    with get_connection() as conn:
        for row in consolidated:
            conn.execute(
                "INSERT INTO logistics_plan(product_id, supplier_id, expected_quantity, sent_to_logistics) VALUES(?, ?, ?, 1)",
                (int(row["product_id"]), supplier_id, float(row["total_quantity"]))
            )
        conn.commit()


def list_logistics(filter_supplier: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = (
        "SELECT lp.id as plan_id, p.code, p.name, p.unit, sp.name as supplier, lp.expected_quantity, "
        "COALESCE(lr.received_quantity, 0) as received_quantity "
        "FROM logistics_plan lp "
        "JOIN products p ON p.id = lp.product_id "
        "LEFT JOIN suppliers sp ON sp.id = lp.supplier_id "
        "LEFT JOIN logistics_received lr ON lr.logistics_plan_id = lp.id "
        "WHERE lp.sent_to_logistics = 1"
    )
    params: List[Any] = []
    if filter_supplier:
        sql += " AND sp.name = ?"
        params.append(filter_supplier)
    if search:
        sql += " AND (p.code LIKE ? OR p.name LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    sql += " ORDER BY p.code"
    with get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


def update_received(plan_id: int, received_quantity: float) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM logistics_received WHERE logistics_plan_id = ?", (plan_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE logistics_received SET received_quantity = ?, updated_at = datetime('now') WHERE id = ?",
                (received_quantity, int(row["id"]))
            )
        else:
            conn.execute(
                "INSERT INTO logistics_received(logistics_plan_id, received_quantity) VALUES(?, ?)",
                (plan_id, received_quantity)
            )
        conn.commit()


