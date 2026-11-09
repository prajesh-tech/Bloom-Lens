import os
import subprocess
import sys
import sqlite3


def test_upload_migration_upgrade_and_rollback(tmp_path):
    database = tmp_path / 'migration.db'
    environment = {**os.environ, 'DATABASE_URL': f'sqlite+aiosqlite:///{database}'}
    for arguments in [('upgrade', 'head'), ('downgrade', 'c0a1b2c3d4e5'), ('upgrade', 'head')]:
        result = subprocess.run([sys.executable, '-m', 'alembic', *arguments], env=environment, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        with sqlite3.connect(database) as connection:
            columns = {row[1] for row in connection.execute('PRAGMA table_info(question_papers)')}
        assert ('file_hash' in columns) == (arguments[0] == 'upgrade')
