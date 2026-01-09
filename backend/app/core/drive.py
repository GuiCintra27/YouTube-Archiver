"""
Drive route helpers.
"""
from fastapi import Request

from app.core.exceptions import DriveNotAuthenticatedException
from app.drive.manager import drive_manager


def require_drive_auth(_: Request) -> None:
    if not drive_manager.is_authenticated():
        raise DriveNotAuthenticatedException()
