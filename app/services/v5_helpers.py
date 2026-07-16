import json
from uuid import uuid4

from app.database import get_connection


def get_employer_for_user(user_id: str) -> dict | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employers WHERE owner_user_id=%s",
                (user_id,),
            )
            return cursor.fetchone()


def create_notification(
    *,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: str | None = None,
) -> str:
    notification_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO notifications (
                    id,user_id,notification_type,title,message,action_url
                )
                VALUES (%s,%s,%s,%s,%s,%s)
                ''',
                (
                    notification_id,
                    user_id,
                    notification_type,
                    title,
                    message,
                    action_url,
                ),
            )
        connection.commit()

    return notification_id


def write_audit_log(
    *,
    actor_user_id: str | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    audit_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO audit_logs (
                    id,actor_user_id,action,entity_type,entity_id,metadata
                )
                VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                ''',
                (
                    audit_id,
                    actor_user_id,
                    action,
                    entity_type,
                    entity_id,
                    json.dumps(metadata or {}),
                ),
            )
        connection.commit()

    return audit_id
