"""Desc

Revision ID: 3bf95e5bd64d
Revises: None
Create Date: 2014-11-12 21:37:14.182786

"""

# revision identifiers, used by Alembic.
revision = '3bf95e5bd64d'
down_revision = None

from alembic import op
import sqlalchemy as sa

from cue.db import types


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('endpoint_types',
    sa.Column('type', sa.SmallInteger(), autoincrement=False, nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('type')
    )
    op.create_table('clusters',
    sa.Column('id', types.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('nic', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('nodes',
    sa.Column('id', types.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('cluster_id', types.UUID(), nullable=True),
    sa.Column('node_id', sa.String(length=36), nullable=False),
    sa.Column('flavor', sa.SmallInteger(), nullable=False),
    sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('endpoints',
    sa.Column('id', types.UUID(), nullable=False),
    sa.Column('uri', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['nodes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('endpoints')
    op.drop_table('nodes')
    op.drop_table('clusters')
    op.drop_table('endpoint_types')
    ### end Alembic commands ###