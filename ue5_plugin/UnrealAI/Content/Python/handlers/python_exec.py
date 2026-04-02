"""Python script execution handler: run Python code inside the UE5 editor."""
import io
import sys


def execute(body: dict) -> dict:
    script = body.get("script")
    if not script:
        return {"ok": False, "error": "script is required"}
    try:
        buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = buf
        try:
            exec(compile(script, "<mcp_script>", "exec"), {})  # noqa: S102
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return {"ok": True, "result": buf.getvalue()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def execute_file(body: dict) -> dict:
    file_path = body.get("file_path")
    if not file_path:
        return {"ok": False, "error": "file_path is required"}
    try:
        with open(file_path, "r") as f:
            script = f.read()
    except OSError as e:
        return {"ok": False, "error": str(e)}
    return execute({"script": script})
