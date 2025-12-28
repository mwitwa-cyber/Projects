# A generic Alembic migration script template
revision = '0001_create_user_and_portfolio_fk'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.add_column('portfolios', sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, index=True))

def downgrade():
    op.drop_column('portfolios', 'user_id')
    op.drop_table('users')
