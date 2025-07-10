"""
Alembic migration environment.
"""
from __future__ import with_statement
import sys
from logging.config import fileConfig
from pathlib import Path
from alembic import context

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all your models so that db.metadata is populated
import hackerservice.models

# Import config and db metadata
from config.settings import DevConfig as Config
from hackerservice.extensions import db

target_metadata = db.metadata

# Setup logging
config = context.config
fileConfig(config.config_file_name)

def run_migrations_offline():
    url = Config.SQLALCHEMY_DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'}
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sqlalchemy import create_engine
    connectable = create_engine(Config.SQLALCHEMY_DATABASE_URI)
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

