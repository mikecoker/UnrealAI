"""
Provides a mock `unreal` module so UE5 plugin handlers can be tested
without a running Unreal Engine editor.
"""
import sys
import types
import pytest


def _make_mock_unreal():
    mod = types.ModuleType("unreal")

    # --- Asset creation helpers ---
    class _AssetTools:
        def create_asset(self, name, path, asset_class, factory):
            obj = types.SimpleNamespace(
                get_name=lambda: name,
                get_path_name=lambda: f"{path}{name}",
            )
            return obj

    class _AssetToolsHelpers:
        @staticmethod
        def get_asset_tools():
            return _AssetTools()

    mod.AssetToolsHelpers = _AssetToolsHelpers

    # --- Blueprint factory ---
    class _BlueprintFactory:
        parent_class = None

    mod.BlueprintFactory = _BlueprintFactory
    mod.Blueprint = object()

    # --- BlueprintEditorLibrary ---
    class _BlueprintEditorLibrary:
        @staticmethod
        def add_member_variable(bp, name, var_type):
            return True

        @staticmethod
        def compile_blueprint(bp):
            return []  # no errors

        @staticmethod
        def get_all_graphs(bp):
            return []

        @staticmethod
        def add_component(bp, component_class, name):
            return types.SimpleNamespace(get_name=lambda: name)

    mod.BlueprintEditorLibrary = _BlueprintEditorLibrary

    # --- EditorAssetLibrary ---
    class _EditorAssetLibrary:
         @staticmethod
         def load_asset(path):
             return types.SimpleNamespace(
                 get_name=lambda: path.split("/")[-1],
                 get_path_name=lambda: path,
             )

         @staticmethod
         def list_assets(path, recursive=True, include_folder=False):
             return []

         @staticmethod
         def make_directory(path):
             return True

         @staticmethod
         def does_asset_exist(path):
             return False

         @staticmethod
         def save_asset(path):
             return True

    mod.EditorAssetLibrary = _EditorAssetLibrary

    # --- EditorLevelLibrary ---
    class _EditorLevelLibrary:
        @staticmethod
        def get_all_level_actors():
            return []

    mod.EditorLevelLibrary = _EditorLevelLibrary

    # --- Material factory ---
    class _MaterialFactoryNew:
        pass

    mod.MaterialFactoryNew = _MaterialFactoryNew
    mod.Material = object()

    # --- MaterialEditingLibrary ---
    class _MaterialEditingLibrary:
        @staticmethod
        def create_material_expression(material, expression_class, node_x=0, node_y=0):
            return types.SimpleNamespace(
                get_name=lambda: expression_class.__name__,
            )

        @staticmethod
        def connect_material_expressions(from_expr, from_pin, to_expr, to_pin):
            return True

        @staticmethod
        def connect_material_property(from_expr, from_pin, prop):
            return True

        @staticmethod
        def recompile_material(material):
            pass

    mod.MaterialEditingLibrary = _MaterialEditingLibrary

    # --- Expression classes (used as identifiers) ---
    class _ExprClass:
        def __init__(self, name):
            self.__name__ = name

    for expr in ["MaterialExpressionMultiply", "MaterialExpressionAdd",
                  "MaterialExpressionLerp", "MaterialExpressionTextureSample",
                  "MaterialExpressionConstant", "MaterialExpressionConstant3Vector",
                  "MaterialExpressionScalarParameter", "MaterialExpressionVectorParameter",
                  "MaterialExpressionEmissiveColor"]:
        setattr(mod, expr, _ExprClass(expr))

    # --- SystemLibrary ---
    class _SystemLibrary:
        @staticmethod
        def execute_console_command(world_context, command):
            pass

    mod.SystemLibrary = _SystemLibrary

    # --- AssetRegistry (for bp_list) ---
    class _ARFilter:
        def __init__(self, **kwargs):
            pass

    class _AssetRegistry:
        @staticmethod
        def get_assets(f):
            return []

    class _AssetRegistryHelpers:
        @staticmethod
        def get_asset_registry():
            return _AssetRegistry()

    mod.ARFilter = _ARFilter
    mod.AssetRegistryHelpers = _AssetRegistryHelpers

    # --- load_class helper ---
    mod.load_class = lambda outer, path: type(path.split(".")[-1], (), {})()


    # --- Actor transform helpers ---
    class _Vector:
        def __init__(self, x=0, y=0, z=0):
            self.x, self.y, self.z = x, y, z

    mod.Vector = _Vector

    # --- EdGraphPinType (for add_variable) ---
    class _EdGraphPinType:
        pc_type = ""
        def import_text(self, text):
            self.pc_type = text
    mod.EdGraphPinType = _EdGraphPinType

    # --- Component base classes (for get_components_by_class) ---
    mod.ActorComponent = type("ActorComponent", (), {})
    mod.StaticMeshComponent = type("StaticMeshComponent", (), {})

    # --- log ---
    mod.log = lambda msg: None
    mod.log_warning = lambda msg: None
    mod.log_error = lambda msg: None

    # --- Tick callback (no-op in tests) ---
    mod.register_slate_post_tick_callback = lambda fn: None
    mod.unregister_slate_post_tick_callback = lambda handle: None

    return mod


@pytest.fixture(autouse=True)
def mock_unreal(monkeypatch):
    """Inject mock unreal module before importing any handler under test."""
    mock = _make_mock_unreal()
    monkeypatch.setitem(sys.modules, "unreal", mock)
    yield mock
