import json
import os
import uuid

SAMPLE_ORDERS = [
    {"order_id": "A100", "items": ["keyboard"], "status": "SHIPPED"},
    {"order_id": "A101", "items": ["mouse", "pad"], "status": "PACKED"},
]


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _save_invoice(order):
    """Write the invoice to the private invoices bucket (only this Lambda may write there)."""
    bucket = os.environ.get("BUCKET_INVOICES")  # injected by bucket_access
    if not bucket:
        return None  # running locally
    import boto3  # included in the Lambda runtime

    key = f"invoices/{order['order_id']}.json"
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(order).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{bucket}/{key}"


def handler(event, context):
    if event.get("httpMethod") == "POST":
        payload = json.loads(event.get("body") or "{}")
        order = {
            "order_id": uuid.uuid4().hex[:8],
            "items": payload.get("items", []),
            "status": "CREATED",
        }
        return _response(201, {"service": "orders", "order": order, "invoice": _save_invoice(order)})
    return _response(200, {"service": "orders", "orders": SAMPLE_ORDERS})
