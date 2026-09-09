"""
Legacy MySQL helper.

The application now reads credentials from backend/.env and uses
backend/app/database/connection.py. This file is kept so older scripts
do not break, but it no longer embeds a password.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.database.connection import get_connection  # noqa: E402

db = get_connection()
cursor = db.cursor(dictionary=True)
