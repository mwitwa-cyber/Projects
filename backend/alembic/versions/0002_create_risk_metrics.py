"""Create risk_metrics table

Revision ID: 0002_create_risk_metrics
Revises: 0001_create_user_and_portfolio_fk
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_create_risk_metrics'
down_revision = '0001_create_user_and_portfolio_fk'
branch_labels = None
depends_on = None


def upgrade():
    """Create risk_metrics table and TimescaleDB hypertable."""
    
    # Create the risk_metrics table
    op.create_table(
        'risk_metrics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=False, index=True),
        sa.Column('benchmark_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=False, index=True),
        sa.Column('calculation_date', sa.DateTime(), nullable=False, index=True, server_default=sa.func.now()),
        
        # Risk Metrics
        sa.Column('beta', sa.Float(), nullable=False),
        sa.Column('var_95', sa.Float(), nullable=False),
        sa.Column('var_99', sa.Float(), nullable=True),
        
        # Additional Risk Metrics
        sa.Column('volatility', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('sortino_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        
        # Calculation Metadata
        sa.Column('observation_count', sa.Integer(), nullable=False),
        sa.Column('lookback_days', sa.Integer(), nullable=False),
        sa.Column('calculation_status', sa.String(20), nullable=False, server_default='completed'),
        sa.Column('error_message', sa.String(500), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create composite indexes for common queries
    op.create_index(
        'ix_risk_metrics_asset_date',
        'risk_metrics',
        ['asset_id', 'calculation_date']
    )
    op.create_index(
        'ix_risk_metrics_benchmark_date',
        'risk_metrics',
        ['benchmark_id', 'calculation_date']
    )
    op.create_index(
        'ix_risk_metrics_status',
        'risk_metrics',
        ['calculation_status']
    )
    
    # Convert to TimescaleDB hypertable (if TimescaleDB is available)
    # This enables efficient time-series queries and compression
    op.execute("""
        DO $$
        BEGIN
            -- Check if TimescaleDB is available
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                -- Convert to hypertable with 7-day chunks
                PERFORM create_hypertable(
                    'risk_metrics',
                    'calculation_date',
                    chunk_time_interval => INTERVAL '7 days',
                    if_not_exists => TRUE
                );
                
                -- Enable compression for older data
                ALTER TABLE risk_metrics SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'asset_id'
                );
                
                -- Add compression policy (compress chunks older than 30 days)
                SELECT add_compression_policy('risk_metrics', INTERVAL '30 days');
                
                RAISE NOTICE 'TimescaleDB hypertable created for risk_metrics';
            ELSE
                RAISE NOTICE 'TimescaleDB not available, using standard table';
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Could not create hypertable: %', SQLERRM;
        END $$;
    """)


def downgrade():
    """Drop risk_metrics table."""
    
    # Remove compression policy if exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                SELECT remove_compression_policy('risk_metrics', if_exists => TRUE);
            END IF;
        EXCEPTION
            WHEN OTHERS THEN NULL;
        END $$;
    """)
    
    op.drop_index('ix_risk_metrics_status')
    op.drop_index('ix_risk_metrics_benchmark_date')
    op.drop_index('ix_risk_metrics_asset_date')
    op.drop_table('risk_metrics')
