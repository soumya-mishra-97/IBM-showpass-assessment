from rest_framework.exceptions import APIException


class BadRequestError(APIException):
    status_code = 400
    default_detail = "Invalid request"
    default_code = "bad_request"


class NotFoundError(APIException):
    status_code = 404
    default_detail = "Resource not found"
    default_code = "not_found"
