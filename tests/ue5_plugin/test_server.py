import sys, json, threading
from http.client import HTTPConnection

# Add plugin Python path so imports work
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_health_check_returns_ok():
    """Server should respond to GET /health with {"ok": true}."""
    from server import UnrealAIServer

    srv = UnrealAIServer(port=17777)
    t = threading.Thread(target=srv.serve_once, daemon=True)
    t.start()

    conn = HTTPConnection("localhost", 17777)
    conn.request("GET", "/health")
    resp = conn.getresponse()
    body = json.loads(resp.read())
    conn.close()
    srv.shutdown()

    assert resp.status == 200
    assert body == {"ok": True, "service": "unreal-ai"}
