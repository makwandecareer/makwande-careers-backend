from alembic import op
import sqlalchemy as sa

revision = "0002_database_optimization"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # AI usage indexes
    op.create_index("ix_ai_usage_user_feature", "ai_usage", ["user_id", "feature"])
    op.create_index("ix_ai_usage_created_at", "ai_usage", ["created_at"])

    # CV drafts indexes
    op.create_index("ix_cv_user_updated", "cv_drafts", ["user_id", "updated_at"])

    # Jobs indexes (if table exists)
    try:
        op.create_index("ix_jobs_status", "jobs", ["status"])
        op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    except Exception:
        pass


def downgrade() -> None:
    for name, table in [
        ("ix_ai_usage_user_feature","ai_usage"),
        ("ix_ai_usage_created_at","ai_usage"),
        ("ix_cv_user_updated","cv_drafts"),
        ("ix_jobs_status","jobs"),
        ("ix_jobs_created_at","jobs"),
    ]:
        try:
            op.drop_index(name, table_name=table)
        except Exception:
            pass
