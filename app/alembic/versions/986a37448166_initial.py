"""Initial
Revision ID: 986a37448166
Revises:
Create Date: 2022-11-19 18:35:40.157600
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "986a37448166"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "history_record",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("date", sa.DATE(), nullable=True),
        sa.Column("log", sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "max_server_messages_for_period",
        sa.Column("period", sa.VARCHAR(), nullable=True),
        sa.Column("date", sa.DATE(), nullable=True),
        sa.Column("amount", sa.INTEGER(), nullable=True),
    )
    op.create_table(
        "max_server_symbols_for_period",
        sa.Column("period", sa.VARCHAR(), nullable=True),
        sa.Column("date", sa.DATE(), nullable=True),
        sa.Column("amount", sa.INTEGER(), nullable=True),
    )
    op.create_table(
        "phrase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("author", sa.TEXT(), nullable=True),
        sa.Column("text", sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_overall_stats",
        sa.Column("user_id", sa.BIGINT(), nullable=False),
        sa.Column("messages", sa.INTEGER(), nullable=True),
        sa.Column("symbols", sa.INTEGER(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "user_max_messages_for_day",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("messages", sa.INTEGER(), nullable=True),
        sa.Column("record_date", sa.DATE(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_max_messages_for_month",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("messages", sa.INTEGER(), nullable=True),
        sa.Column("record_date", sa.DATE(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_max_messages_for_week",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("messages", sa.INTEGER(), nullable=True),
        sa.Column("record_date", sa.DATE(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_max_symbols_for_day",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("symbols", sa.INTEGER(), nullable=True),
        sa.Column("record_date", sa.DATE(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_max_symbols_for_month",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("symbols", sa.INTEGER(), nullable=True),
        sa.Column("record_date", sa.DATE(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_max_symbols_for_week",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("symbols", sa.INTEGER(), nullable=True),
        sa.Column("record_date", sa.DATE(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_stats_for_current_month",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("messages", sa.INTEGER(), nullable=True),
        sa.Column("symbols", sa.INTEGER(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_stats_for_current_week",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("messages", sa.INTEGER(), nullable=True),
        sa.Column("symbols", sa.INTEGER(), nullable=True),
        sa.Column("user_id", sa.BIGINT(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_overall_stats.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_stats_for_current_week")
    op.drop_table("user_stats_for_current_month")
    op.drop_table("user_max_symbols_for_week")
    op.drop_table("user_max_symbols_for_month")
    op.drop_table("user_max_symbols_for_day")
    op.drop_table("user_max_messages_for_week")
    op.drop_table("user_max_messages_for_month")
    op.drop_table("user_max_messages_for_day")
    op.drop_table("user_overall_stats")
    op.drop_table("phrase")
    op.drop_table("max_server_symbols_for_period")
    op.drop_table("max_server_messages_for_period")
    op.drop_table("history_record")
    # ### end Alembic commands ###
