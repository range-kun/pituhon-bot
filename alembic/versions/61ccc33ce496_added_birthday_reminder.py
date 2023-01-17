"""Added birthday reminder

Revision ID: 61ccc33ce496
Revises: 986a37448166
Create Date: 2023-01-15 12:15:17.431685

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '61ccc33ce496'
down_revision = '986a37448166'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('user_birthday',
    sa.Column('user_id', sa.BIGINT(), nullable=False),
    sa.Column('date', sa.DATE(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_birthday')
    # ### end Alembic commands ###
