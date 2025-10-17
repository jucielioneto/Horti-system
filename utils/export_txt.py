from typing import List, Dict, Any


def export_store_txt(rows: List[Dict[str, Any]]) -> bytes:
    # Format: CODE ; QUANTITY with dot decimal, no rounding, one product per line
    lines = []
    for row in rows:
        code = str(row.get("code")).strip()
        qty = row.get("quantity")
        if isinstance(qty, float):
            qty_str = ("%f" % qty).rstrip("0").rstrip(".") if "." in ("%f" % qty) else str(qty)
        else:
            qty_str = str(qty)
        lines.append(f"{code} ; {qty_str}")
    content = "\n".join(lines) + "\n"
    return content.encode("utf-8")


