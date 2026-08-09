import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote an existing GrowthOS user to admin")
    parser.add_argument("email", help="Exact email of an already registered user")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == args.email)).scalar_one_or_none()
        if user is None:
            print("User not found; register the account normally first.")
            return 1
        user.role = "admin"; db.commit()
        print(f"Admin role granted to {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
