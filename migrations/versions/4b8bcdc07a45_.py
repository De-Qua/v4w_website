"""empty message

Revision ID: 4b8bcdc07a45
Revises: 350b23cba52e
Create Date: 2021-01-21 02:19:14.323065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b8bcdc07a45'
down_revision = '350b23cba52e'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_trackusage():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_trackusage():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_users():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_type_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(batch_op.f('fk_token_token_type_id_token_type'), 'token_type', ['token_type_id'], ['id'])
        batch_op.drop_column('token_type')

    # ### end Alembic commands ###


def downgrade_users():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_type', sa.VARCHAR(length=10), nullable=False))
        batch_op.drop_constraint(batch_op.f('fk_token_token_type_id_token_type'), type_='foreignkey')
        batch_op.drop_column('token_type_id')

    # ### end Alembic commands ###


def upgrade_ideas():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_ideas():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_feed_err():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_feed_err():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

