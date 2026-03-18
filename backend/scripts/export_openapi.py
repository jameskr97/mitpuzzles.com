"""export the OpenAPI schema to a JSON file for frontend type generation."""

import json
import sys
from pathlib import Path

from app.main import app

output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
output.write_text(json.dumps(app.openapi(), indent=2))
print(f"exported OpenAPI schema to {output}")
