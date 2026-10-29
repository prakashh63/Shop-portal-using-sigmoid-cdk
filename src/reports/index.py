import json
import os


def _count_invoices():
    bucket = os.environ.get("BUCKET_INVOICES")  # injected by bucket_access (read only)
    if not bucket:
        return None  # running locally
    import boto3

    response = boto3.client("s3").list_objects_v2(Bucket=bucket, Prefix="invoices/")
    return response.get("KeyCount", 0)


def handler(event, context):
    """Called by API Gateway (/api/reports) and by the daily schedule."""
    report = {"service": "reports", "invoice_count": _count_invoices()}
    if "httpMethod" in event:  # came through API Gateway
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(report),
        }
    print(json.dumps(report))  # came from the schedule: just log it
    return report
