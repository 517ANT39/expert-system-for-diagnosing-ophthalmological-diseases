import os
import sys
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'solution'))

from solution.app.models.database_models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # ПРОСТОЙ И РАБОЧИЙ СПОСОБ - создаем engine напрямую
    connectable = create_engine(get_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()