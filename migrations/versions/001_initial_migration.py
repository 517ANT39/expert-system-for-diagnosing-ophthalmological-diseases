"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-10-15 12:37:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Создаем таблицу doctors
    op.create_table('doctors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('registered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Создаем таблицу patients с простыми строками вместо ENUM
    op.create_table('patients',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('birthday', sa.Date(), nullable=False),
        sa.Column('sex', sa.String(length=1), nullable=False),  # 'M' или 'F'
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('allergies', sa.String(length=1000), nullable=True),
        sa.Column('chronic_diseases', sa.String(length=1000), nullable=True),
        sa.Column('current_medications', sa.String(length=1000), nullable=True),
        sa.Column('family_anamnes', sa.String(length=1000), nullable=True),
        sa.Column('notes', sa.String(length=2000), nullable=True),
        sa.Column('registered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создаем таблицу consultations с простыми строками вместо ENUM
    op.create_table('consultations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('consultation_date', sa.DateTime(), nullable=True),
        sa.Column('sub_graph_find_diagnosis', sa.JSON(), nullable=True),
        sa.Column('final_diagnosis', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),  # 'draft', 'active', etc.
        sa.Column('notes', sa.String(length=2000), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('consultations')
    op.drop_table('patients')
    op.drop_table('doctors')