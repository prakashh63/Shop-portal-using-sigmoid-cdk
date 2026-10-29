import json


def handler(event, context):
    """Runs for every message published to the 'orders' SNS topic."""
    processed = []
    for record in event.get("Records", []):
        message = json.loads(record["Sns"]["Message"])
        print(f"sending confirmation email for order {message.get('order_id')}")
        processed.append(message.get("order_id"))
    return {"processed": processed}
