
import re
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from App.repositories.education_repository import Education_Repository

templates = Jinja2Templates(directory="App/templates")

def build_route_url(
    request: Request,
    route_name: str,
    path_params: dict | None = None,
    success: str | None = None,
    error: str | None = None,
    query_params: dict | None = None,
):
    url = str(request.url_for(route_name, **(path_params or {})))
    params = {}

    if success:
        params["success"] = success

    if error:
        params["error"] = error

    for key, value in (query_params or {}).items():
        if value in (None, ""):
            continue

        params[key] = value

    if not params:
        return url

    return f"{url}?{urlencode(params)}"


def redirect_to_route(
    request: Request,
    route_name: str,
    path_params: dict | None = None,
    success: str | None = None,
    error: str | None = None,
    query_params: dict | None = None,
):
    return RedirectResponse(
        url=build_route_url(
            request,
            route_name,
            path_params=path_params,
            success=success,
            error=error,
            query_params=query_params,
        ),
        status_code=303,
    )


def ensure_admin(current_user):
    return getattr(current_user, "role", None) == "admin"

def normalize_slug(raw_value: str):
    slug = re.sub(r"[^a-z0-9_-]+", "-", (raw_value or "").strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")

    if not slug:
        raise ValueError(
            "Строка-идентификатор должна содержать латинские буквы, цифры, дефис или подчёркивание."
        )

    return slug


def parse_sort_order(raw_value: str):
    value = (raw_value or "").strip()

    if not value:
        return 0

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("Поле порядка должно быть целым числом.") from exc


def optional_parent_id(raw_value: str | None):
    value = (raw_value or "").strip()

    if not value:
        return None

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("Некорректный идентификатор родительской статьи.") from exc


def resolve_parent_section(
    education_repo: Education_Repository,
    page_id: int,
    parent_id: int | None,
    current_section_id: int | None = None,
):
    if parent_id is None:
        return None

    parent = education_repo.get_section_by_id(parent_id)

    if not parent or parent.page_id != page_id:
        raise ValueError("Выбранная родительская статья не найдена в этой странице.")

    if current_section_id is not None and parent.id == current_section_id:
        raise ValueError("Статья не может быть родительской сама для себя.")

    current = parent
    while current is not None:
        if current.id == current_section_id:
            raise ValueError("Нельзя сделать дочернюю статью родителем текущей.")

        current = (
            education_repo.get_section_by_id(current.parent_id)
            if current.parent_id is not None
            else None
        )

    return parent


def render_admin_template(
    request: Request,
    current_user,
    template_name: str,
    admin_section: str,
    admin_title: str,
    admin_description: str,
    error: str | None = None,
    success: str | None = None,
    **context,
):
    payload = {
        "request": request,
        "current_user": current_user,
        "error": error,
        "success": success,
        "admin_section": admin_section,
        "admin_title": admin_title,
        "admin_description": admin_description,
    }
    payload.update(context)
    return templates.TemplateResponse(template_name, payload)


def build_page_statistics(education_repo: Education_Repository):
    section_counts_by_page = {}
    published_section_counts_by_page = {}

    for section in education_repo.get_sections():
        section_counts_by_page[section.page_id] = (
            section_counts_by_page.get(section.page_id, 0) + 1
        )

        if section.is_published:
            published_section_counts_by_page[section.page_id] = (
                published_section_counts_by_page.get(section.page_id, 0) + 1
            )

    return section_counts_by_page, published_section_counts_by_page


def build_article_groups(education_repo: Education_Repository, pages):
    return [
        {
            "page": page,
            "sections": education_repo.get_flat_section_hierarchy(page.id),
        }
        for page in pages
    ]


def resolve_selected_page(
    education_repo: Education_Repository,
    pages,
    requested_page_id: int | None,
):
    if not pages:
        return None, None

    if requested_page_id is None:
        return pages[0], None

    page = education_repo.get_page_by_id(requested_page_id)

    if page:
        return page, None

    return pages[0], "Выбранная страница не найдена. Открыта первая доступная страница."