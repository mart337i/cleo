from fastapi import Request
import logging

# Get logger with the correct name
_logger = logging.getLogger(__name__)

async def log_request_info(request: Request):
    """
    Dependency function to log request information.
    """
    _logger.debug(
        f"{request.method} request to {request.url} metadata\n"
        f"\tHeaders: {request.headers}\n"
        f"\tPath Params: {request.path_params}\n"
        f"\tQuery Params: {request.query_params}\n"
        f"\tCookies: {request.cookies}\n"
    )