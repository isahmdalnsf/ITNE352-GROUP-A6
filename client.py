import socket
import ssl
import sys
 
from protocol import ProtocolError, recv_message, send_message
 
HOST = "127.0.0.1"
PORT = 5050
CERT_FILE = "cert.pem"
 
 
def prompt(text):
    try:
        return input(text)
    except EOFError:
        raise KeyboardInterrupt
 
 
def prompt_choice(text, valid):
    while True:
        choice = prompt(text).strip()
        if choice in valid:
            return choice
        print(f"Please enter one of: {', '.join(valid)}")
 
 
def prompt_index(text, count):
    while True:
        raw = prompt(text).strip()
        if not raw:
            return 0
        if raw.isdigit():
            n = int(raw)
            if 0 <= n <= count:
                return n
        print(f"Please enter a number between 0 and {count} (0 to cancel).")
 
 
def exchange(sock, request):
    send_message(sock, request)
    response = recv_message(sock)
    if response is None:
        raise ConnectionError("server closed the connection")
    return response
 
 
def fetch_reference(sock, kind):
    resp = exchange(sock, {"type": "ref", "kind": kind})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return []
    return resp.get("items", [])
 
 
def show_recipe_list(items):
    if not items:
        print("  (no recipes found)")
        return
    print(f"  {'#':>3}  {'ID':<8}  Name")
    print(f"  {'-'*3}  {'-'*8}  {'-'*40}")
    for idx, item in enumerate(items, start=1):
        print(f"  {idx:>3}  {item.get('id',''):<8}  {item.get('name','')}")
        thumb = item.get("thumbnail", "")
        if thumb:
            print(f"       thumb: {thumb}")
 
 
def show_recipe_detail(recipe):
    if not recipe:
        print("  (no recipe)")
        return
    print()
    print(f"  Name        : {recipe.get('name','')}")
    print(f"  Category    : {recipe.get('category','')}")
    print(f"  Area        : {recipe.get('area','')}")
    tags = recipe.get("tags", "")
    if tags:
        print(f"  Tags        : {tags}")
    print(f"  YouTube     : {recipe.get('youtube','') or '(none)'}")
    print(f"  Source      : {recipe.get('source','') or '(none)'}")
    print("  Ingredients :")
    for ing in recipe.get("ingredients", []):
        measure = ing.get("measure", "").strip()
        name = ing.get("ingredient", "").strip()
        if measure:
            print(f"    - {name} ({measure})")
        else:
            print(f"    - {name}")
    instr = (recipe.get("instructions", "") or "").strip()
    print("  Instructions:")
    if instr:
        for line in instr.splitlines():
            line = line.strip()
            if line:
                print(f"    {line}")
    else:
        print("    (none)")
    print()
 
 
def show_categories(items):
    if not items:
        print("  (none)")
        return
    for it in items:
        name = it.get("name", "")
        desc = (it.get("description", "") or "").strip().replace("\n", " ")
        if len(desc) > 100:
            desc = desc[:97] + "..."
        if desc:
            print(f"  - {name}: {desc}")
        else:
            print(f"  - {name}")
 
 
def show_simple_names(items):
    if not items:
        print("  (none)")
        return
    for it in items:
        print(f"  - {it.get('name','')}")
 
 
def pick_from_named_list(items, prompt_label):
    if not items:
        print(f"  (no {prompt_label} available)")
        return None
    for idx, it in enumerate(items, start=1):
        print(f"  {idx:>3}. {it.get('name','')}")
    n = prompt_index(f"Choose a {prompt_label} (0 to cancel): ", len(items))
    if n == 0:
        return None
    return items[n - 1].get("name", "")
 
 
def drilldown_recipe(sock, items, option_id):
    if not items:
        return
    n = prompt_index("Pick a recipe number for full details (0 to skip): ", len(items))
    if n == 0:
        return
    meal_id = items[n - 1].get("id", "")
    if not meal_id:
        print("  (selected item has no id)")
        return
    resp = exchange(sock, {"type": "recipe", "op": "lookup",
                           "id": meal_id, "origin": option_id})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return
    show_recipe_detail(resp.get("recipe"))
 
 
def option_search_by_name(sock):
    keyword = prompt("Enter recipe name keyword: ").strip()
    if not keyword:
        print("  (empty keyword)")
        return
    resp = exchange(sock, {"type": "recipe", "op": "search", "query": keyword})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return
    print(f"\nResults for '{keyword}':")
    items = resp.get("items", [])
    show_recipe_list(items)
    drilldown_recipe(sock, items, "1.1")
 
 
def option_filter_by_category(sock):
    categories = fetch_reference(sock, "categories")
    name = pick_from_named_list(categories, "category")
    if not name:
        return
    resp = exchange(sock, {"type": "recipe", "op": "filter_category", "value": name})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return
    print(f"\nRecipes in category '{name}':")
    items = resp.get("items", [])
    show_recipe_list(items)
    drilldown_recipe(sock, items, "1.2")
 
 
def option_filter_by_area(sock):
    areas = fetch_reference(sock, "areas")
    name = pick_from_named_list(areas, "area")
    if not name:
        return
    resp = exchange(sock, {"type": "recipe", "op": "filter_area", "value": name})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return
    print(f"\nRecipes from '{name}':")
    items = resp.get("items", [])
    show_recipe_list(items)
    drilldown_recipe(sock, items, "1.3")
 
 
def option_filter_by_ingredient(sock):
    raw = prompt("Enter an ingredient (single word, spaces become _): ").strip()
    if not raw:
        print("  (empty ingredient)")
        return
    ingredient = raw.replace(" ", "_")
    resp = exchange(sock, {"type": "recipe", "op": "filter_ingredient", "value": ingredient})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return
    print(f"\nRecipes containing '{ingredient}':")
    items = resp.get("items", [])
    show_recipe_list(items)
    drilldown_recipe(sock, items, "1.4")
 
 
def option_random_recipe(sock):
    resp = exchange(sock, {"type": "recipe", "op": "random"})
    if resp.get("status") != "ok":
        print(f"Error: {resp.get('message', 'unknown error')}")
        return
    print("\nRandom recipe:")
    show_recipe_detail(resp.get("recipe"))
 
 
RECIPES_MENU = (
    "\nRecipes Menu\n"
    "  1.1  Search by name\n"
    "  1.2  Filter by category\n"
    "  1.3  Filter by area\n"
    "  1.4  Filter by ingredient\n"
    "  1.5  Random recipe\n"
    "  1.6  Back to main menu\n"
)
 
REFERENCE_MENU = (
    "\nReference Menu\n"
    "  2.1  List all categories\n"
    "  2.2  List all areas\n"
    "  2.3  List all ingredients\n"
    "  2.4  Back to main menu\n"
)
 
MAIN_MENU = (
    "\nMain Menu\n"
    "  1  Browse recipes\n"
    "  2  Reference lists\n"
    "  3  Quit\n"
)
 
 
def recipes_menu_loop(sock):
    actions = {
        "1.1": option_search_by_name,
        "1.2": option_filter_by_category,
        "1.3": option_filter_by_area,
        "1.4": option_filter_by_ingredient,
        "1.5": option_random_recipe,
    }
    while True:
        print(RECIPES_MENU)
        choice = prompt_choice("Choose an option: ",
                               {"1.1", "1.2", "1.3", "1.4", "1.5", "1.6"})
        if choice == "1.6":
            return
        actions[choice](sock)
 
 
def reference_menu_loop(sock):
    while True:
        print(REFERENCE_MENU)
        choice = prompt_choice("Choose an option: ", {"2.1", "2.2", "2.3", "2.4"})
        if choice == "2.4":
            return
        if choice == "2.1":
            items = fetch_reference(sock, "categories")
            print("\nCategories:")
            show_categories(items)
        elif choice == "2.2":
            items = fetch_reference(sock, "areas")
            print("\nAreas:")
            show_simple_names(items)
        elif choice == "2.3":
            items = fetch_reference(sock, "ingredients")
            print(f"\nIngredients (showing first 50 of {len(items)}):")
            show_simple_names(items[:50])
 
 
def main_menu_loop(sock):
    while True:
        print(MAIN_MENU)
        choice = prompt_choice("Choose an option: ", {"1", "2", "3"})
        if choice == "1":
            recipes_menu_loop(sock)
        elif choice == "2":
            reference_menu_loop(sock)
        else:
            return
 
 
def main():
    print("Recipe Discovery System - Client")
    name = prompt("Enter your name: ").strip() or "anonymous"
 
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls.load_verify_locations(CERT_FILE)
 
    try:
        raw = socket.create_connection((HOST, PORT), timeout=30)
        sock = tls.wrap_socket(raw, server_hostname=HOST)
    except OSError as exc:
        print(f"Cannot connect to {HOST}:{PORT}: {exc}")
        sys.exit(1)
 
    sock.settimeout(None)
    try:
        send_message(sock, {"type": "hello", "name": name})
        welcome = recv_message(sock)
        if welcome is None or welcome.get("status") != "ok":
            print("Server refused the connection.")
            return
        print(f"Connected. Server says: {welcome.get('message','')}")
 
        try:
            main_menu_loop(sock)
        except KeyboardInterrupt:
            print("\n(interrupted)")
        finally:
            try:
                send_message(sock, {"type": "bye"})
                recv_message(sock)
            except (OSError, ProtocolError):
                pass
    except (OSError, ConnectionError, ProtocolError) as exc:
        print(f"Network error: {exc}")
    finally:
        try:
            sock.close()
        except OSError:
            pass
        print("Goodbye.")
 
 
if __name__ == "__main__":
    main()
