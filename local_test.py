"""Run all four Lambda handlers on your machine with fake events. No AWS needed."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent


def load_handler(folder: str):
    spec = importlib.util.spec_from_file_location(f"{folder}_index", HERE / "src" / folder / "index.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.handler


def context(name: str):
    return SimpleNamespace(function_name=name, aws_request_id="local-test-1")


def show(title: str, result) -> None:
    print(f"\n--- {title}")
    print(json.dumps(result, indent=2))


show("GET /api/users", load_handler("users")({"path": "/api/users"}, context("shop-users")))
show("GET /api/users/2", load_handler("users")({"path": "/api/users/2"}, context("shop-users")))
show("GET /api/orders", load_handler("orders")({"httpMethod": "GET"}, context("shop-orders-api")))
show(
    "POST /api/orders",
    load_handler("orders")(
        {"httpMethod": "POST", "body": json.dumps({"items": ["keyboard"]})},
        context("shop-orders-api"),
    ),
)
show("GET /api/reports", load_handler("reports")({"httpMethod": "GET"}, context("shop-reports")))
show("daily schedule -> reports", load_handler("reports")({}, context("shop-reports")))
sns_event = {"Records": [{"Sns": {"Message": json.dumps({"order_id": "A200"})}}]}
show("SNS message -> worker", load_handler("worker")(sns_event, context("shop-order-worker")))
