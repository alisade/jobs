"""Print the service's OpenAPI document (used by `make contract`)."""

import json

from catalog.app import create_app

if __name__ == "__main__":
    print(json.dumps(create_app().openapi(), indent=2, sort_keys=True))
