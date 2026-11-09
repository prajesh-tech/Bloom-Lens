"""Administrator-only CLI: python -m app.manage_reviewers USERNAME [--role admin]."""
import argparse
import asyncio
import getpass
from sqlalchemy import select, delete
from app.core.browser_sessions import hash_password
from app.core.database import AsyncSessionLocal
from app.models.reviewer import Reviewer, ReviewerSession


async def provision(username: str, password: str, role: str) -> None:
    if not username.strip() or len(username) > 100 or len(password) < 12:
        raise ValueError('Username must contain 1–100 characters; password must contain at least 12 characters.')
    password_hash = await asyncio.to_thread(hash_password, password)
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(Reviewer).where(Reviewer.username == username))).scalar_one_or_none()
        if user is None:
            db.add(Reviewer(username=username, password_hash=password_hash, role=role))
        else:
            user.password_hash, user.role, user.enabled = password_hash, role, True
            await db.execute(delete(ReviewerSession).where(ReviewerSession.reviewer_id == user.id))
        await db.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a reviewer or reset credentials and revoke existing sessions.')
    parser.add_argument('username')
    parser.add_argument('--role', choices=['admin', 'instructor'], default='instructor')
    arguments = parser.parse_args()
    password = getpass.getpass('Password (at least 12 characters): ')
    if password != getpass.getpass('Confirm password: '):
        parser.error('Passwords do not match.')
    asyncio.run(provision(arguments.username, password, arguments.role))
