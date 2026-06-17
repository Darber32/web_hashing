from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="App/templates")


def get_education_neighbors(pages, current_page):
    if not current_page:
        return None, None

    current_index = None

    for index, page in enumerate(pages):
        if page.id == current_page.id:
            current_index = index
            break

    if current_index is None:
        return None, None

    previous_page = pages[current_index - 1] if current_index > 0 else None
    next_page = pages[current_index + 1] if current_index < len(pages) - 1 else None

    return previous_page, next_page


def render_education_page(
    request: Request,
    current_user,
    pages,
    page,
    sections,
    error: str = None,
):
    previous_page, next_page = get_education_neighbors(pages, page)

    return templates.TemplateResponse(
        "education.html",
        {
            "request": request,
            "page": page,
            "pages": pages,
            "sections": sections,
            "previous_page": previous_page,
            "next_page": next_page,
            "current_user": current_user,
            "error": error,
        },
    )