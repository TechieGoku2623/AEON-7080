"""Initial schema. Equivalent to the SQLAlchemy models.

Revision ID: 0001
"""

from alembic import op

from aeon_api.db import Base
from aeon_api import models  # noqa: F401

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
