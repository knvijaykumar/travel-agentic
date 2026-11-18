import os, sys, json
sys.path.insert(0, os.getcwd())

from backend.app.main import app

openapi = app.openapi()
paths = openapi.get("paths", {})

print(f"Total OpenAPI Paths: {len(paths)}")
print(f"{'PATH':<50} {'METHODS':<15} {'SUMMARY / TAGS'}")
print("=" * 100)

for path, methods in sorted(paths.items()):
    for method, details in methods.items():
        summary = details.get("summary", "")
        tags = ",".join(details.get("tags", []))
        print(f"{path:<50} {method.upper():<15} {summary} [{tags}]")
