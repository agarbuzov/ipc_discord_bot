from front import templates


async def error_handler(request, exc):
    return templates.TemplateResponse("error.html", {"request": request, "status_code": exc.status_code,
                                                     "message": exc.detail})
