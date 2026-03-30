"""
Auto-executed by UE5 when the UnrealAI plugin loads.
Starts the HTTP server after a single tick to ensure the editor is ready.
"""
import unreal

_server = None
_started = False


def _on_first_tick(_delta):
    global _server, _started
    if _started:
        return
    _started = True
    from server import UnrealAIServer
    _server = UnrealAIServer(port=7777)
    _server.start()


unreal.register_slate_post_tick_callback(_on_first_tick)
