from front import templates


async def forbidden_handler(request, exc):
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)
