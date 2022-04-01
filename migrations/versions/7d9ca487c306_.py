"""empty message

Revision ID: 7d9ca487c306
Revises: 99e3b123b6b8
Create Date: 2022-04-01 09:52:03.335721

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d9ca487c306'
down_revision = '99e3b123b6b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('profiles', sa.Column('avatar', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('profiles', 'avatar')
    # ### end Alembic commands ###
