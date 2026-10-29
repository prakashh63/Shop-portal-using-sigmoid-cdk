import json

# Demo data. A real app would read a database here.
USERS = [
    {"id": "1", "name": "Asha", "city": "Bengaluru"},
    {"id": "2", "name": "Ravi", "city": "Chennai"},
]


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    path = (event.get("path") or "").rstrip("/")
    user_id = path.rsplit("/", 1)[-1]
    if user_id != "users":  # /api/users/<id>
        for user in USERS:
            if user["id"] == user_id:
                return _response(200, {"service": "users", "user": user})
        return _response(404, {"service": "users", "error": f"user {user_id} not found"})
    return _response(200, {"service": "users", "users": USERS, "served_by": context.function_name})
