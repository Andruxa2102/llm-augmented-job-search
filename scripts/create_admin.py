"""Create the first administrator script"""
from pathlib import Path
from sys import argv, exit, path

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in path:
    path.insert(0, str(SRC_DIR))


from src.storage.db import SessionLocal
from src.storage.models import User
from src.api.security import hash_password


def create_admin(username: str, password: str):
    """Create an administrator record in the database"""

    with SessionLocal() as sess:
        existing = sess.query(User).filter(User.username == username).first()
        if existing:
            print(f"❌ User '{username}' already exists")
            return

        print(f"Hash:   {hash_password(password)}")

        admin = User(
            username=username,
            hashed_password=hash_password(password),
            is_admin=True
        )
        sess.add(admin)
        sess.commit()

        print(f"Admin '{username}' created successfully")
        print(f"ID: {admin.id}")
        print(f"Is Admin: {admin.is_admin}")


if __name__ == "__main__":

    if len(argv) < 3:
        print("Usage: python scripts/create_admin.py <username> <password>")
        print("Example: python scripts/create_admin.py admin my_secure_password")
        exit(1)

    user = argv[1]
    passw = argv[2]

    print(f"Password repr: {repr(passw)}")
    print(f"Password bytes: {len(passw.encode('utf-8'))}")

    create_admin(user, passw)