"""Shop portal: the whole infrastructure in one config (no YAML needed)."""

from pathlib import Path

import aws_cdk as cdk

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import (
    ApiGatewayConfig,
    LambdaConfig,
    RouteConfig,
    S3Config,
    ScheduleTriggerConfig,
    TopicConfig,
    TriggerConfig,
    WebAppConfig,
)

HERE = Path(__file__).parent  # makes the src paths work from any folder
SRC = HERE / "src"

app = cdk.App()

config = WebAppConfig(
    app_name="shop-portal",
    environment="dev",  # dev | staging | prod
    owner_team="shop-team",
    cost_center="CC-3001",
    buckets={
        # '/' -> the web app (index.html)
        "website": S3Config(bucket_name="shop-portal-web-dev-12345", cdn_default=True),
        # '/assets/*' -> JS, CSS, images (objects live under the assets/ prefix)
        "assets": S3Config(bucket_name="shop-portal-assets-dev-12345", cdn_path="/assets/*"),
        # private data bucket: only the Lambdas that are granted access can use it
        "invoices": S3Config(bucket_name="shop-portal-invoices-dev-12345"),
    },
    topics={"orders": TopicConfig(topic_name="shop-orders")},
    lambdas={
        # --- API Lambdas (behind API Gateway) ---
        "users": LambdaConfig(
            function_name="shop-users",
            entry_point_dir=str(SRC / "users"),
        ),
        "orders": LambdaConfig(
            function_name="shop-orders-api",
            entry_point_dir=str(SRC / "orders"),
            bucket_access={"invoices": "read_write"},  # injects BUCKET_INVOICES
        ),
        # --- Background Lambdas (no API route) ---
        "worker": LambdaConfig(
            function_name="shop-order-worker",
            entry_point_dir=str(SRC / "worker"),
            memory_mb=256,
            timeout_seconds=60,
            triggers=TriggerConfig(sns=["orders"]),  # runs for every message on the topic
        ),
        "reports": LambdaConfig(
            function_name="shop-reports",
            entry_point_dir=str(SRC / "reports"),
            bucket_access={"invoices": "read"},  # read only
            triggers=TriggerConfig(schedule=ScheduleTriggerConfig(expression="rate(1 day)")),
        ),
    },
    api_gateway=ApiGatewayConfig(
        rate_limit=1000,
        burst_limit=500,
        routes=[
            RouteConfig(path="/api/users", function="users"),
            RouteConfig(path="/api/orders", function="orders"),
            RouteConfig(path="/api/reports", function="reports"),
        ],
    ),
)

ServerlessWebAppStack(app, "ShopPortalStack", config=config)
app.synth()
