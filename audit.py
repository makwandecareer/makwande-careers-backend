import logging

audit_logger=logging.getLogger("audit")

def log_event(user_id:str, action:str, resource:str):
    audit_logger.info(
        "user=%s action=%s resource=%s",
        user_id,
        action,
        resource,
    )
