"""
Creates a login account, or updates an existing one (role, scope, password).
This is the only way to create accounts: there is no public sign-up.

From the project root, venv active (one line each in PowerShell):

  # Department Coordinator: full access to one department
  python -m scripts.create_coordinator --username aqsa --email aqsa@example.com --role department_coordinator --department "Computer Science"

  # Program Coordinator: read-only, one program
  python -m scripts.create_coordinator --username bscs --email bscs@example.com --role program_coordinator --program "BS Computer Science"

  # Faculty: linked to an instructor, sees only their own data
  python -m scripts.create_coordinator --username maria --role faculty --instructor "Dr Maria Tariq"

You are asked for a password if you don't pass --password. Running it again for
an existing username changes that account's role and scope. A faculty account's
email defaults to the instructor's email. Each instructor can have one login.
"""

import argparse
import getpass

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Department, Instructor, Program, User

ROLES = ("department_coordinator", "program_coordinator", "faculty")


def create_or_update_coordinator(db, username, role, email=None, password=None,
                                 department=None, program=None, instructor=None):
    department_id = program_id = instructor_id = None
    default_email = None

    if role == "department_coordinator":
        dept = db.query(Department).filter_by(name=department).first() if department else None
        if dept is None:
            raise ValueError(f"Department not found: {department!r}. Use --department with an existing name.")
        department_id = dept.id
    elif role == "program_coordinator":
        prog = db.query(Program).filter_by(name=program).first() if program else None
        if prog is None:
            raise ValueError(f"Program not found: {program!r}. Use --program with an existing name.")
        program_id = prog.id
    elif role == "faculty":
        matches = db.query(Instructor).filter_by(name=instructor).all() if instructor else []
        if len(matches) != 1:
            raise ValueError(f"Instructor not found (or ambiguous): {instructor!r}. "
                             "Use --instructor with the exact name.")
        instructor_id, default_email = matches[0].id, matches[0].email
        clash = db.query(User).filter(User.instructor_id == instructor_id, User.username != username).first()
        if clash is not None:
            raise ValueError(f"{instructor} already has a login ({clash.username}).")
    else:
        raise ValueError(f"Role must be one of {ROLES}.")

    if password is not None and not (8 <= len(password.encode()) <= 72):
        raise ValueError("Password must be between 8 and 72 characters.")

    email = email or default_email
    user = db.query(User).filter_by(username=username).first()
    created = user is None
    if created:
        if not email or not password:
            raise ValueError("A new account needs both an email and a password.")
        user = User(username=username, email=email, hashed_password=hash_password(password))
        db.add(user)
    else:
        if email:
            user.email = email
        if password:
            user.hashed_password = hash_password(password)

    user.role = role
    user.department_id = department_id
    user.program_id = program_id
    user.instructor_id = instructor_id
    user.is_active = True
    db.commit()
    return user, created


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create or update a login account.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email")
    parser.add_argument("--role", required=True, choices=ROLES)
    parser.add_argument("--department", help="Department name (department_coordinator)")
    parser.add_argument("--program", help="Program name (program_coordinator)")
    parser.add_argument("--instructor", help="Exact instructor name (faculty)")
    parser.add_argument("--password", help="Prompted for if omitted")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        exists = db.query(User).filter_by(username=args.username).first() is not None
        password = args.password
        if password is None and not exists:
            password = getpass.getpass("Password (8-72 characters): ")
        try:
            user, created = create_or_update_coordinator(
                db, args.username, args.role, args.email, password,
                args.department, args.program, args.instructor)
        except ValueError as error:
            raise SystemExit(f"Error: {error}")
        scope = (f"department_id={user.department_id}" if user.department_id
                 else f"program_id={user.program_id}" if user.program_id
                 else f"instructor_id={user.instructor_id}")
        print(f"{'Created' if created else 'Updated'} {user.username} ({user.role}, {scope}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
