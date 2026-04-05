"""
create_admin.py — One-time script to create or reset an admin account.

Run this from your project root BEFORE starting the app:

    python create_admin.py

It will prompt you for a username and password, hash the password,
and store it in the admins table in your database.

You can run it again any time to update an existing admin's password.
"""

from dotenv import load_dotenv
load_dotenv()

from database import init_db
from auth_page import register_admin
import getpass


def main():
    print("=" * 50)
    print("  Salary Prediction App — Admin Setup")
    print("=" * 50)

    # Make sure the admins table exists
    print("\nInitialising database tables...")
    init_db()

    print("\nEnter the admin account details.")
    print("(If this username already exists, the password will be updated.)\n")

    username = input("Admin username: ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        return

    password = getpass.getpass("Admin password: ")
    confirm  = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("❌ Passwords do not match. Try again.")
        return

    success, msg = register_admin(username, password)
    if success:
        print(f"\n✅ {msg}")
        print(f"\nYou can now log in at: http://localhost:8501/?admin=1")
        print(f"Username : {username}")
        print(f"Password : (the one you just set)\n")
    else:
        print(f"\n❌ {msg}\n")


if __name__ == "__main__":
    main()
