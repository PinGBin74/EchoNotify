"""add_is_public_to_chat_room

Revision ID: 05df9ddfbfe9
Revises: c1d2e3f4g5h6
Create Date: 2025-12-25 22:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "05df9ddfbfe9"
down_revision: Union[str, None] = "c1d2e3f4g5h6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_room",
        sa.Column(
            "is_public", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_room", "is_public")
