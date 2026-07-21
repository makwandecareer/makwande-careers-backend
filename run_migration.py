from pathlib import Path

from app.database import get_connection, pool


def main() -> None:
    migration_path = Path("migrations/create_billing_tables.sql")

    if not migration_path.exists():
        raise FileNotFoundError(
            f"Migration file not found: {migration_path.resolve()}"
        )

    sql = migration_path.read_text(encoding="utf-8")

    try:
        pool.open()

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)

            conn.commit()

        print("Billing tables created successfully.")

    except Exception:
        print("Billing migration failed.")
        raise

    finally:
        pool.close()


if __name__ == "__main__":
    main()