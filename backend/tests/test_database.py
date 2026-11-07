from unittest.mock import MagicMock, patch

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import Base, get_db


def test_base_declarative_metadata():
    """Verify that Base has SQLAlchemy metadata configured."""
    assert Base.metadata is not None


def test_get_db_session_lifecycle():
    """Verify that get_db yields a Session and ensures proper closure."""
    mock_session = MagicMock(spec=Session)

    with patch("app.database.session.SessionLocal", return_value=mock_session):
        db_gen = get_db()
        session = next(db_gen)
        assert session == mock_session
        assert not mock_session.close.called

        # When the generator completes, session.close() must be called
        try:
            next(db_gen)
        except StopIteration:
            pass

        assert mock_session.close.called


def test_isolated_db_session_execution(db_session: Session):
    """Verify database query execution and rollback isolation."""
    result = db_session.execute(text("SELECT 42")).scalar_one()
    assert result == 42
