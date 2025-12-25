"""add_chat_tables

Revision ID: c1d2e3f4g5h6
Revises: b8c9d4e5f6a7
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, None] = 'b8c9d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_room table
    op.create_table(
        'chat_room',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('support_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.id'], ),
        sa.ForeignKeyConstraint(['support_id'], ['user_profile.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_room_id'), 'chat_room', ['id'], unique=False)
    op.create_index(op.f('ix_chat_room_user_id'), 'chat_room', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_room_support_id'), 'chat_room', ['support_id'], unique=False)

    # Create chat_message table
    op.create_table(
        'chat_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('sender_role', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='sent'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['room_id'], ['chat_room.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['user_profile.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_message_id'), 'chat_message', ['id'], unique=False)
    op.create_index(op.f('ix_chat_message_room_id'), 'chat_message', ['room_id'], unique=False)
    op.create_index(op.f('ix_chat_message_created_at'), 'chat_message', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    op.drop_index(op.f('ix_chat_message_created_at'), table_name='chat_message')
    op.drop_index(op.f('ix_chat_message_room_id'), table_name='chat_message')
    op.drop_index(op.f('ix_chat_message_id'), table_name='chat_message')
    op.drop_table('chat_message')

    op.drop_index(op.f('ix_chat_room_support_id'), table_name='chat_room')
    op.drop_index(op.f('ix_chat_room_user_id'), table_name='chat_room')
    op.drop_index(op.f('ix_chat_room_id'), table_name='chat_room')
    op.drop_table('chat_room')
