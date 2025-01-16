from http import HTTPStatus


class APIException(Exception):
    status_code: int
    code: str
    msg: str
    detail: str
    ex: Exception

    def __init__(
        self,
        *,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        code: str = "000000",
        msg: str = None,
        detail: str = None,
        ex: Exception = None,
    ):
        self.status_code = status_code
        self.code = code
        self.msg = msg
        self.detail = detail
        self.ex = ex
        super().__init__(ex)


class UnauthorizedException(APIException):
    def __init__(self, custom_msg: str = None, ex: Exception = None):
        default_msg = "Authorization Required"
        detail_msg = f"{custom_msg}" if custom_msg else default_msg

        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            msg=f"Authorization Required",
            detail=detail_msg,
            code=f"{HTTPStatus.UNAUTHORIZED}{'1'.zfill(4)}",
            ex=ex,
        )


class TokenExpiredException(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            msg=f"Token Expired",
            detail=f"Token Expired",
            code=f"{HTTPStatus.UNAUTHORIZED}{'1'.zfill(4)}",
            ex=ex,
        )


class TokenDecodeException(APIException):
    def __init__(self, ex: Exception = None):
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            msg=f"Token has been compromised.",
            detail=f"Token has been compromised.",
            code=f"{HTTPStatus.UNAUTHORIZED}{'1'.zfill(4)}",
            ex=ex,
        )


class NotFoundException(APIException):
    def __init__(self, custom_msg: str = None, ex: Exception = None):
        default_msg = HTTPStatus.NOT_FOUND.description
        detail_msg = f"{custom_msg}" if custom_msg else default_msg

        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            msg=HTTPStatus.NOT_FOUND.description,
            detail=detail_msg,
            code=f"{HTTPStatus.NOT_FOUND}{'1'.zfill(4)}",
            ex=ex,
        )


class CustomException(Exception):
    code = HTTPStatus.BAD_GATEWAY
    error_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description

    def __init__(self, message=None):
        if message:
            self.message = message


class BadRequestException(APIException):
    def __init__(self, custom_msg: str = None, ex: Exception = None):
        default_msg = HTTPStatus.BAD_REQUEST.description
        detail_msg = f"{custom_msg}" if custom_msg else default_msg

        super().__init__(
            status_code=HTTPStatus.BAD_REQUEST,
            msg=HTTPStatus.BAD_REQUEST.description,
            detail=detail_msg,
            code=f"{HTTPStatus.BAD_REQUEST}{'1'.zfill(4)}",
            ex=ex,
        )


class ForbiddenException(APIException):
    def __init__(self, custom_msg: str = None, ex: Exception = None):
        default_msg = HTTPStatus.FORBIDDEN.description
        detail_msg = f"{custom_msg}" if custom_msg else default_msg

        super().__init__(
            status_code=HTTPStatus.FORBIDDEN,
            msg=HTTPStatus.FORBIDDEN.description,
            detail=detail_msg,
            code=f"{HTTPStatus.FORBIDDEN}{'1'.zfill(4)}",
            ex=ex,
        )


class UnprocessableEntity(APIException):
    def __init__(self, custom_msg: str = None, ex: Exception = None):
        default_msg = HTTPStatus.UNPROCESSABLE_ENTITY.description
        detail_msg = f"{custom_msg}" if custom_msg else default_msg

        super().__init__(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            msg=HTTPStatus.UNPROCESSABLE_ENTITY.description,
            detail=detail_msg,
            code=f"{HTTPStatus.UNPROCESSABLE_ENTITY}{'1'.zfill(4)}",
            ex=ex,
        )


class DuplicateValueException(APIException):
    def __init__(self, custom_msg: str = None, ex: Exception = None):
        default_msg = HTTPStatus.CONFLICT
        detail_msg = f"{custom_msg}" if custom_msg else default_msg

        super().__init__(
            status_code=HTTPStatus.CONFLICT,
            msg=HTTPStatus.CONFLICT.description,
            detail=detail_msg,
            code=f"{HTTPStatus.CONFLICT}{'1'.zfill(4)}",
            ex=ex,
        )
