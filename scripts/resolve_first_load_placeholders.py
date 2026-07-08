import json
import sys
import urllib.error
import urllib.request


API = "http://localhost:8001"
UPLOAD_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 4


def request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc


def main() -> None:
    token = request(
        "/auth/login",
        "POST",
        {"email": "admin@mantenimiento.local", "password": "Admin123!"},
    )["access_token"]

    lines = {line["name"]: line for line in request("/production-lines", token=token)}
    equipment = {item["name"]: item for item in request("/equipment", token=token)}
    pending = [
        row
        for row in request("/corrections/pending", token=token)
        if row["uploaded_file_id"] == UPLOAD_ID and str(row["equipo"]).strip().lower() == "error"
    ]

    created = 0
    corrected = 0
    placeholders: dict[str, int] = {}
    for row in pending:
        line_name = row["linea"]
        if line_name not in lines:
            continue
        placeholder_name = f"Equipo sin identificar - {line_name}"
        if placeholder_name in placeholders:
            equipment_id = placeholders[placeholder_name]
        elif placeholder_name in equipment:
            equipment_id = equipment[placeholder_name]["id"]
            placeholders[placeholder_name] = equipment_id
        else:
            item = request(
                "/equipment",
                "POST",
                {"name": placeholder_name, "production_line_id": lines[line_name]["id"], "is_active": True},
                token=token,
            )
            equipment_id = item["id"]
            equipment[placeholder_name] = item
            placeholders[placeholder_name] = equipment_id
            created += 1

        request(f"/raw-events/{row['id']}/correction", "PATCH", {"equipment_id": equipment_id}, token=token)
        corrected += 1

    print(json.dumps({"upload_id": UPLOAD_ID, "placeholders_created": created, "rows_corrected": corrected}, ensure_ascii=False))


if __name__ == "__main__":
    main()
