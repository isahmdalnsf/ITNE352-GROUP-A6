
import os
import socket
import subprocess
import sys
import time

from protocol import recv_message, send_message

HOST = "127.0.0.1"
PORT = 5050
REPORT = "smoke_report.txt"
SERVER_LOG = "server_stdout.log"


def write_report(lines):
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def wait_for_port(host, port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.5)
    return False


def call(sock, request):
    send_message(sock, request)
    return recv_message(sock)


def main():
    results = []
    results.append(f"started at {time.strftime('%H:%M:%S')}")

    log_fh = open(SERVER_LOG, "w", encoding="utf-8")
    server = subprocess.Popen(
        [sys.executable, "-u", "server.py"],
        stdout=log_fh, stderr=subprocess.STDOUT,
    )
    try:
        if not wait_for_port(HOST, PORT, timeout=60):
            results.append("FAIL: server did not open port within 60s")
            return results
        results.append("PASS: server is listening on TCP port")

        if not os.path.exists("reference_G1.json"):
            results.append("FAIL: reference_G1.json was not written at startup")
        else:
            size = os.path.getsize("reference_G1.json")
            results.append(f"PASS: reference_G1.json exists ({size} bytes)")

        sock = socket.create_connection((HOST, PORT), timeout=10)
        send_message(sock, {"type": "hello", "name": "smoke_tester"})
        welcome = recv_message(sock)
        if welcome and welcome.get("status") == "ok":
            results.append(f"PASS: hello/welcome handshake -> {welcome.get('message')}")
        else:
            results.append(f"FAIL: handshake response = {welcome!r}")
            return results

        r = call(sock, {"type": "ref", "kind": "categories"})
        ok = r.get("status") == "ok" and len(r.get("items", [])) > 0
        results.append(f"{'PASS' if ok else 'FAIL'}: 2.1 categories -> {len(r.get('items',[]))} items")

        r = call(sock, {"type": "ref", "kind": "areas"})
        ok = r.get("status") == "ok" and len(r.get("items", [])) > 0
        results.append(f"{'PASS' if ok else 'FAIL'}: 2.2 areas -> {len(r.get('items',[]))} items")

        r = call(sock, {"type": "ref", "kind": "ingredients"})
        ok = r.get("status") == "ok" and len(r.get("items", [])) > 0
        results.append(f"{'PASS' if ok else 'FAIL'}: 2.3 ingredients -> {len(r.get('items',[]))} items")

        r = call(sock, {"type": "recipe", "op": "search", "query": "chicken"})
        items = r.get("items", [])
        ok = r.get("status") == "ok"
        results.append(f"{'PASS' if ok else 'FAIL'}: 1.1 search chicken -> {len(items)} items")
        if items:
            r = call(sock, {"type": "recipe", "op": "lookup",
                            "id": items[0]["id"], "origin": "1.1"})
            ok = r.get("status") == "ok" and r.get("recipe", {}).get("name")
            results.append(f"{'PASS' if ok else 'FAIL'}: 1.1 lookup first hit -> {r.get('recipe',{}).get('name')}")

        r = call(sock, {"type": "recipe", "op": "filter_category", "value": "Seafood"})
        results.append(f"{'PASS' if r.get('status')=='ok' else 'FAIL'}: 1.2 Seafood -> {len(r.get('items',[]))} items")

        r = call(sock, {"type": "recipe", "op": "filter_area", "value": "Italian"})
        results.append(f"{'PASS' if r.get('status')=='ok' else 'FAIL'}: 1.3 Italian -> {len(r.get('items',[]))} items")

        r = call(sock, {"type": "recipe", "op": "filter_ingredient", "value": "chicken_breast"})
        results.append(f"{'PASS' if r.get('status')=='ok' else 'FAIL'}: 1.4 chicken_breast -> {len(r.get('items',[]))} items")

        r = call(sock, {"type": "recipe", "op": "random"})
        ok = r.get("status") == "ok" and r.get("recipe", {}).get("name")
        results.append(f"{'PASS' if ok else 'FAIL'}: 1.5 random -> {r.get('recipe',{}).get('name')}")

        expected = [f"smoke_tester_{opt}_G1.json" for opt in
                    ("1.1", "1.2", "1.3", "1.4", "1.5")]
        for path in expected:
            if os.path.exists(path):
                results.append(f"PASS: {path} written ({os.path.getsize(path)} bytes)")
            else:
                results.append(f"FAIL: {path} missing")

        send_message(sock, {"type": "bye"})
        recv_message(sock)
        sock.close()
        results.append("PASS: clean bye/close")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        log_fh.close()
        results.append("")
        results.append("===== captured server stdout =====")
        try:
            with open(SERVER_LOG, "r", encoding="utf-8") as fh:
                results.append(fh.read())
        except OSError as exc:
            results.append(f"(could not read server log: {exc})")

    return results


if __name__ == "__main__":
    write_report(main())
    print(f"wrote {REPORT}")
