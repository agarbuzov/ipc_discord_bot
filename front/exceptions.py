from fastapi import status

from fastapi.exceptions import HTTPException


class Forbidden(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN)
