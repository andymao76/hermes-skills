# Dify 1.14.2 DSL Import Mechanism

## Key Source Files (from `~/dify/api/`)

| File | Purpose |
|------|---------|
| `services/app_dsl_service.py` | Main `export_dsl()` and `import_dsl()` logic |
| `models/workflow.py` | `Workflow` model — stores graph as JSON text column |
| `constants/dsl_version.py` | `CURRENT_APP_DSL_VERSION = "0.6.0"` |

## How export_dsl() Works

```python
# app_dsl_service.py:514
export_data = {
    "version": CURRENT_DSL_VERSION,  # "0.6.0"
    "kind": "app",
    "app": {
        "name": app_model.name,
        "mode": app_model.mode,
        "icon": app_model.icon,
        "icon_type": app_model.icon_type,
        "icon_background": app_model.icon_background,
        "description": app_model.description,
        "use_icon_as_answer_icon": app_model.use_icon_as_answer_icon,
    },
}
# For advanced-chat or workflow modes:
export_data["workflow"] = workflow.to_dict(include_secret=include_secret)
export_data["dependencies"] = [...]  # Plugin deps analysis
```

## Workflow Dict Structure

`workflow.to_dict()` returns the `graph` (JSON → parsed dict), `features`, `conversation_variables`, `environment_variables` fields from the DB model — it's not reconstructed, just deserialized.

## How import_dsl() Works

1. Parse YAML → dict
2. Validate `version` compatibility via `check_version_compatibility(imported_dsl_version)` — supports version upgrade/downgrade
3. Extract `app` metadata, create `App` DB row
4. Call `_import_workflow_app()` for advanced-chat/workflow modes (or `_import_model_config_app()` for simpler modes)
5. Store graph as JSON in `Workflow.graph` column
6. Return app_id

## Import Compatibility

- DSL versions are forward-compatible (newish import works on olderish runtime)
- `check_version_compatibility()` allows version from "0.1.0" and above
- If version check fails, the import button just shows an error toast — no details logged in the UI
- The most common import failure reasons (in order):
  1. Invalid YAML syntax
  2. Missing required top-level fields (`version`, `kind`, `app`)
  3. Wrong `kind` value (not `"app"`)
  4. Node/edge format mismatch from old DSL versions
  5. Plugin dependencies that can't be resolved
