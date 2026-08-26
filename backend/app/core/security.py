"""Password hashing and policy (RN-15).

Policy: minimum 8 characters, at least one uppercase letter, one number
and one special character. Passwords are stored only as bcrypt hashes.
"""

import re

import bcrypt

POLICY = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


class PasswordPolicyError(ValueError):
    """Raised when a password violates RN-15."""


def validate_policy(plain: str) -> None:
    if not POLICY.search(plain):
        raise PasswordPolicyError(
            "La contraseña debe tener mínimo 8 caracteres, "
            "una mayúscula, un número y un caracter especial."
        )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
