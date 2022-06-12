from fastapi.exception_handlers import http_exception_handler
from front import templates


async def error_handler(request, exc):
    if exc.status_code >= 400:
        return templates.TemplateResponse("error.html", {"request": request, "status_code": exc.status_code,
                                                         "message": exc.detail})
    return await http_exception_handler(request, exc)
