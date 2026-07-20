from app.services.integration_db import initialise_integration_schema
def initialise_openai_and_billing() -> None:
    initialise_integration_schema()
