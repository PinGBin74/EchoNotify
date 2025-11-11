import asyncio
from logging.config import fileConfig
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from echonotify.infrastructure.database.models import Base
from echonotify.settings import Settings

from echonotify.user.models import UserProfile, RefreshToken

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = Settings()
DATABASE_URL = settings.DATABASE_URL or settings.db_url


def include_object(object, name, type_, reflected, compare_to):
    postgis_schemas = {"tiger", "topology", "tiger_data"}
    postgis_tables = {
        "spatial_ref_sys",
        "geometry_columns",
        "geography_columns",
        "raster_columns",
        "raster_overviews",
        "topology",
        "layer",
        "street_type_lookup",
        "countysub_lookup",
        "pagc_lex",
        "direction_lookup",
        "tabblock20",
        "secondary_unit_lookup",
        "faces",
        "tabblock",
        "county",
        "pagc_gaz",
        "addr",
        "featnames",
        "pagc_rules",
        "geocode_settings_default",
        "bg",
        "countysub_lookup",
        "state_lookup",
        "place",
        "cousub",
        "zcta5",
        "zip_lookup_all",
        "edges",
        "zip_lookup_base",
        "state",
        "zip_state_loc",
        "loader_platform",
        "zip_state",
        "place_lookup",
        "addrfeat",
        "sight_tests",
        "loader_variables",
        "zip_lookup",
        "tract",
        "loader_lookuptables",
        "geocode_settings",
        "zip_lookup_base",
        "county_lookup",
        "tabblock20",
        "geocode_settings",
        "zip_state",
        "direction_lookup",
        "pagc_rules",
        "cousub",
        "countysub_lookup",
        "secondary_unit_lookup",
        "tract",
        "faces",
        "topology",
        "loader_lookuptables",
        "zip_state_loc",
        "loader_platform",
        "zip_lookup_all",
        "zcta5",
        "featnames",
        "loader_variables",
        "edges",
        "layer",
        "zip_lookup",
        "county_lookup",
        "addr",
        "addrfeat",
        "bg",
        "state",
        "street_type_lookup",
        "pagc_gaz",
        "pagc_lex",
        "place",
        "state_lookup",
        "geocode_settings_default",
    }
    if type_ == "table":
        if hasattr(object, "schema") and object.schema in postgis_schemas:
            return False
        if name in postgis_tables:
            return False
    if type_ == "index":
        if hasattr(object, "table"):
            table = object.table
            if hasattr(table, "schema") and table.schema in postgis_schemas:
                return False
            if table.name in postgis_tables:
                return False
    return True


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_schemas=False,
        version_table_schema=target_metadata.schema,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode with async engine"""
    connectable = create_async_engine(DATABASE_URL, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())