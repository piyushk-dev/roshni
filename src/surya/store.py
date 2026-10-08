"""Per-user bot state in one DynamoDB table: language, location, last estimate."""

from __future__ import annotations

import json
import os
import time

USER_TTL_DAYS = 90
MESSAGE_TTL_DAYS = 2
_table = None


def _t():
    global _table
    if _table is None:
        import boto3

        _table = boto3.resource("dynamodb").Table(os.environ["SESSION_TABLE"])
    return _table


def claim_message(message_id: str) -> bool:
    """True the first time a message id is seen. Meta retries webhooks, so repeats are dropped."""
    from botocore.exceptions import ClientError

    try:
        _t().put_item(
            Item={"pk": f"MSG#{message_id}", "expires": int(time.time()) + MESSAGE_TTL_DAYS * 86400},
            ConditionExpression="attribute_not_exists(pk)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def get_user(wa_id: str) -> dict:
    item = _t().get_item(Key={"pk": f"USER#{wa_id}"}).get("Item")
    return json.loads(item["data"]) if item else {}


def put_user(wa_id: str, data: dict) -> None:
    _t().put_item(Item={"pk": f"USER#{wa_id}", "data": json.dumps(data), "expires": int(time.time()) + USER_TTL_DAYS * 86400})
