from __future__ import annotations

from app.database import get_connection, pool


def print_section(title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def print_rows(rows) -> None:
    if not rows:
        print("No records found.")
        return

    for row in rows:
        print(row)


def run_database_audit() -> None:
    print("Opening database connection pool...")

    pool.open(wait=True)

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                print_section("DATABASE TABLES")

                cursor.execute(
                    """
                    SELECT
                        table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                    """
                )

                print_rows(cursor.fetchall())

                print_section("DATABASE INDEXES")

                cursor.execute(
                    """
                    SELECT
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname;
                    """
                )

                print_rows(cursor.fetchall())

                print_section("DATABASE CONSTRAINTS")

                cursor.execute(
                    """
                    SELECT
                        tc.table_name,
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM information_schema.table_constraints AS tc
                    LEFT JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                       AND tc.table_schema = kcu.table_schema
                    LEFT JOIN information_schema.constraint_column_usage AS ccu
                        ON tc.constraint_name = ccu.constraint_name
                       AND tc.table_schema = ccu.table_schema
                    WHERE tc.table_schema = 'public'
                    ORDER BY
                        tc.table_name,
                        tc.constraint_type,
                        tc.constraint_name,
                        kcu.ordinal_position;
                    """
                )

                print_rows(cursor.fetchall())

                print_section("TABLE COLUMNS")

                cursor.execute(
                    """
                    SELECT
                        table_name,
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position;
                    """
                )

                print_rows(cursor.fetchall())

                print_section("FOREIGN KEYS")

                cursor.execute(
                    """
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column,
                        tc.constraint_name
                    FROM information_schema.table_constraints AS tc
                    INNER JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                       AND tc.table_schema = kcu.table_schema
                    INNER JOIN information_schema.constraint_column_usage AS ccu
                        ON tc.constraint_name = ccu.constraint_name
                       AND tc.table_schema = ccu.table_schema
                    WHERE tc.table_schema = 'public'
                      AND tc.constraint_type = 'FOREIGN KEY'
                    ORDER BY tc.table_name, kcu.column_name;
                    """
                )

                print_rows(cursor.fetchall())

                print_section("TABLE ROW ESTIMATES")

                cursor.execute(
                    """
                    SELECT
                        relname AS table_name,
                        n_live_tup AS estimated_rows,
                        n_dead_tup AS estimated_dead_rows,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables
                    ORDER BY relname;
                    """
                )

                print_rows(cursor.fetchall())

        print("\nDatabase audit completed successfully.")

    except Exception as error:
        print("\nDatabase audit failed.")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")
        raise

    finally:
        print("\nClosing database connection pool...")
        pool.close()


if __name__ == "__main__":
    run_database_audit()