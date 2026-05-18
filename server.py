

import json
import socket
import threading
import urllib.parse
import urllib.request
from datetime import datetime

from protocol import ProtocolError, recv_message, send_message

GROUP_ID = "G1"
HOST = "0.0.0.0"
PORT = 5050
BACKLOG = 8

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1/"
HTTP_TIMEOUT = 15  # seconds

RECIPE_LIST_LIMIT = 15
INGREDIENT_FILE_LIMIT = 50

REFERENCE_FILE = f"reference_{GROUP_ID}.json"


reference_cache = {
    "categories": [],
    "areas": [],
    "ingredients": [],
}

clients_lock = threading.Lock()
file_lock = threading.Lock()
log_lock = threading.Lock()
clients_online = {}  # addr -> name


def log(message):
    """Thread-safe timestamped console output."""
    stamp = datetime.now().strftime("%H:%M:%S")
    with log_lock:
        print(f"[{stamp}] {message}", flush=True)



def http_get_json(path, params=None):
    """GET <MEALDB_BASE><path>?<params> and return the parsed JSON dict."""
    url = MEALDB_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ITNE352-RDS/1.0"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def build_reference_cache():
    """Fetch the three reference lists once and populate reference_cache."""
    log("Fetching reference data from TheMealDB ...")

    cat_list = http_get_json("list.php", {"c": "list"}).get("meals") or []
    area_list = http_get_json("list.php", {"a": "list"}).get("meals") or []
    ing_list = http_get_json("list.php", {"i": "list"}).get("meals") or []

    cat_details = http_get_json("categories.php").get("categories") or []
    desc_by_name = {c.get("strCategory", ""): c.get("strCategoryDescription", "")
                    for c in cat_details}

    reference_cache["categories"] = [
        {"name": c.get("strCategory", ""),
         "description": desc_by_name.get(c.get("strCategory", ""), "")}
        for c in cat_list if c.get("strCategory")
    ]
    reference_cache["areas"] = [
        {"name": a.get("strArea", "")}
        for a in area_list if a.get("strArea")
    ]
    reference_cache["ingredients"] = [
        {"name": i.get("strIngredient", "")}
        for i in ing_list if i.get("strIngredient")
    ]

    log(f"Cached {len(reference_cache['categories'])} categories, "
        f"{len(reference_cache['areas'])} areas, "
        f"{len(reference_cache['ingredients'])} ingredients.")


def persist_reference_file():
    snapshot = {
        "group_id": GROUP_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "categories": reference_cache["categories"],
        "areas": reference_cache["areas"],
        "ingredients": reference_cache["ingredients"][:INGREDIENT_FILE_LIMIT],
    }
    with open(REFERENCE_FILE, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=2)
    log(f"Wrote reference cache to {REFERENCE_FILE}.")


def brief_recipe(meal):
    return {
        "id": meal.get("idMeal", ""),
        "name": meal.get("strMeal", ""),
        "thumbnail": meal.get("strMealThumb", ""),
    }


def full_recipe(meal):
    """Project a raw meal record to the fields required by Table 3."""
    ingredients = []
    for i in range(1, 21):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if name:
            ingredients.append({"ingredient": name, "measure": measure})
    return {
        "id": meal.get("idMeal", ""),
        "name": meal.get("strMeal", ""),
        "category": meal.get("strCategory", ""),
        "area": meal.get("strArea", ""),
        "instructions": meal.get("strInstructions", ""),
        "ingredients": ingredients,
        "youtube": meal.get("strYoutube", ""),
        "source": meal.get("strSource", ""),
        "tags": meal.get("strTags", ""),
        "thumbnail": meal.get("strMealThumb", ""),
    }


def save_recipe_response(client_name, option, payload):
    safe_name = "".join(ch for ch in client_name if ch.isalnum() or ch in "-_") or "client"
    path = f"{safe_name}_{option}_{GROUP_ID}.json"
    record = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "option": option,
        "payload": payload,
    }
    with file_lock:
        history = []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
                if isinstance(existing, list):
                    history = existing
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        history.append(record)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(history, fh, ensure_ascii=False, indent=2)


def handle_reference(kind):
    """Serve a reference list from the in-memory cache."""
    if kind == "categories":
        return {"status": "ok", "kind": "categories",
                "items": reference_cache["categories"]}
    if kind == "areas":
        return {"status": "ok", "kind": "areas",
                "items": reference_cache["areas"]}
    if kind == "ingredients":
        return {"status": "ok", "kind": "ingredients",
                "items": reference_cache["ingredients"]}
    return {"status": "error", "message": f"unknown reference kind: {kind}"}


def handle_recipe(req, client_name):
    """Forward a recipe request to TheMealDB and shape the response."""
    op = req.get("op", "")

    if op == "search":
        query = (req.get("query") or "").strip()
        if not query:
            return {"status": "error", "message": "empty search query"}
        data = http_get_json("search.php", {"s": query})
        meals = data.get("meals") or []
        items = [brief_recipe(m) for m in meals[:RECIPE_LIST_LIMIT]]
        resp = {"status": "ok", "kind": "recipe_list", "op": op,
                "query": query, "items": items}
        save_recipe_response(client_name, "1.1", resp)
        return resp

    if op in ("filter_category", "filter_area", "filter_ingredient"):
        value = (req.get("value") or "").strip()
        if not value:
            return {"status": "error", "message": "empty filter value"}
        param_key = {"filter_category": "c",
                     "filter_area": "a",
                     "filter_ingredient": "i"}[op]
        if op == "filter_ingredient":
            value = value.replace(" ", "_")
        data = http_get_json("filter.php", {param_key: value})
        meals = data.get("meals") or []
        items = [brief_recipe(m) for m in meals[:RECIPE_LIST_LIMIT]]
        option_id = {"filter_category": "1.2",
                     "filter_area": "1.3",
                     "filter_ingredient": "1.4"}[op]
        resp = {"status": "ok", "kind": "recipe_list", "op": op,
                "value": value, "items": items}
        save_recipe_response(client_name, option_id, resp)
        return resp

    if op == "random":
        data = http_get_json("random.php")
        meals = data.get("meals") or []
        if not meals:
            return {"status": "error", "message": "no random meal returned"}
        resp = {"status": "ok", "kind": "recipe_detail", "op": op,
                "recipe": full_recipe(meals[0])}
        save_recipe_response(client_name, "1.5", resp)
        return resp

    if op == "lookup":
        meal_id = (req.get("id") or "").strip()
        origin = (req.get("origin") or "lookup").strip()
        if not meal_id:
            return {"status": "error", "message": "missing meal id"}
        data = http_get_json("lookup.php", {"i": meal_id})
        meals = data.get("meals") or []
        if not meals:
            return {"status": "error", "message": f"no meal found for id {meal_id}"}
        resp = {"status": "ok", "kind": "recipe_detail", "op": op,
                "recipe": full_recipe(meals[0])}
        save_recipe_response(client_name, origin, resp)
        return resp

    return {"status": "error", "message": f"unknown recipe op: {op}"}



def describe_request(req):
    """Build a short human-readable summary for the console log."""
    rtype = req.get("type", "?")
    if rtype == "ref":
        return f"ref/{req.get('kind', '?')}"
    if rtype == "recipe":
        op = req.get("op", "?")
        for key in ("query", "value", "id"):
            if req.get(key):
                return f"recipe/{op}({key}={req.get(key)})"
        return f"recipe/{op}"
    if rtype == "bye":
        return "bye"
    return rtype


def request_source(req):
    """Return 'cache' or 'TheMealDB' for the given request."""
    if req.get("type") == "ref":
        return "cache"
    if req.get("type") == "recipe":
        return "TheMealDB"
    return "n/a"


def handle_client(conn, addr):
    client_name = f"{addr[0]}:{addr[1]}"
    try:
        hello = recv_message(conn)
        if not hello or hello.get("type") != "hello":
            send_message(conn, {"status": "error",
                                "message": "expected hello message first"})
            return
        client_name = (hello.get("name") or "").strip() or client_name
        with clients_lock:
            clients_online[addr] = client_name
        log(f"Client connected: {client_name} from {addr[0]}:{addr[1]}")
        send_message(conn, {"status": "ok", "kind": "welcome",
                            "message": f"hello {client_name}",
                            "group_id": GROUP_ID})

        while True:
            req = recv_message(conn)
            if req is None:
                break
            summary = describe_request(req)
            source = request_source(req)
            log(f"[{client_name}] request: {summary}  source: {source}")

            rtype = req.get("type")
            try:
                if rtype == "ref":
                    resp = handle_reference(req.get("kind", ""))
                elif rtype == "recipe":
                    resp = handle_recipe(req, client_name)
                elif rtype == "bye":
                    send_message(conn, {"status": "ok", "kind": "bye"})
                    break
                else:
                    resp = {"status": "error",
                            "message": f"unknown request type: {rtype}"}
            except urllib.request.URLError as exc:
                resp = {"status": "error",
                        "message": f"upstream error: {exc.reason}"}
            except Exception as exc:  # last-resort guard
                resp = {"status": "error",
                        "message": f"server error: {exc}"}

            send_message(conn, resp)

    except ProtocolError as exc:
        log(f"[{client_name}] protocol error: {exc}")
    except (ConnectionResetError, ConnectionAbortedError):
        log(f"[{client_name}] connection reset")
    except OSError as exc:
        log(f"[{client_name}] socket error: {exc}")
    finally:
        with clients_lock:
            clients_online.pop(addr, None)
        try:
            conn.close()
        except OSError:
            pass
        log(f"Client disconnected: {client_name}")



def main():
    build_reference_cache()
    persist_reference_file()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(BACKLOG)
        log(f"Listening on {HOST}:{PORT} (group {GROUP_ID})")
        try:
            while True:
                conn, addr = srv.accept()
                t = threading.Thread(target=handle_client,
                                     args=(conn, addr),
                                     daemon=True)
                t.start()
        except KeyboardInterrupt:
            log("Server shutting down (keyboard interrupt).")


if __name__ == "__main__":
    main()
