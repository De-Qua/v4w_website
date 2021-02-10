"""empty message

Revision ID: f1d862df0139
Revises: 14656c90e26c
Create Date: 2021-01-18 16:54:50.423008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1d862df0139'
down_revision = '14656c90e26c'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    pass


def downgrade_():
    pass


def upgrade_trackusage():
    pass


def downgrade_trackusage():
    pass


def upgrade_users():
    pass


def downgrade_users():
    pass


def upgrade_ideas():
    pass


def downgrade_ideas():
    pass


def upgrade_feed_err():
    pass


def downgrade_feed_err():
    pass

