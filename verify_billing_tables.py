from app.database import get_connection, pool


def main() -> None:
    try:
        pool.open()

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN (
                          'subscriptions',
                          'payment_transactions'
                      )
                    ORDER BY table_name
                    """
                )

                rows = cur.fetchall()

        table_names = [row["table_name"] for row in rows]

        print("Billing tables found:", table_names)

        expected = {"subscriptions", "payment_transactions"}

        if set(table_names) != expected:
            raise RuntimeError(
                "One or more billing tables were not created."
            )

        print("Billing database verification successful.")

    finally:
        pool.close()


if __name__ == "__main__":
    main()