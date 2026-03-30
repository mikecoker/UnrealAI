import sys
sys.path.insert(0, "ue5_plugin/UnrealAI/Content/Python")


def test_get_actors_returns_list(mock_unreal):
    import types

    actor_a = types.SimpleNamespace(
        get_name=lambda: "BP_Character_1",
        get_class=lambda: types.SimpleNamespace(get_name=lambda: "BP_Character_C"),
        get_actor_location=lambda: mock_unreal.Vector(100, 200, 0),
    )
    mock_unreal.EditorLevelLibrary.get_all_level_actors = lambda: [actor_a]

    from handlers.scene import get_actors
    result = get_actors({})

    assert result["ok"] is True
    assert len(result["actors"]) == 1
    assert result["actors"][0]["name"] == "BP_Character_1"
    assert result["actors"][0]["class"] == "BP_Character_C"
    assert result["actors"][0]["location"] == {"x": 100, "y": 200, "z": 0}


def test_get_actor_detail_not_found(mock_unreal):
    mock_unreal.EditorLevelLibrary.get_all_level_actors = lambda: []

    from handlers.scene import get_actor_detail
    result = get_actor_detail({"name": "NonExistent"})

    assert result["ok"] is False
    assert "not found" in result["error"].lower()


def test_screenshot_triggers_console_command(mock_unreal):
    commands_run = []
    mock_unreal.SystemLibrary.execute_console_command = (
        lambda ctx, cmd: commands_run.append(cmd)
    )

    from handlers.scene import screenshot
    result = screenshot({"width": 1920, "height": 1080})

    assert result["ok"] is True
    assert any("HighResShot" in c for c in commands_run)
    assert "path" in result
