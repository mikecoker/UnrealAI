import requests

UE5_BASE_URL = "http://localhost:7777"


class UE5ConnectionError(RuntimeError):
    pass


def post(path: str, data: dict) -> dict:
    try:
        resp = requests.post(f"{UE5_BASE_URL}{path}", json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise UE5ConnectionError(
            "UE5 plugin server not running. "
            "Open Unreal Engine with the UnrealAI plugin enabled."
        )
