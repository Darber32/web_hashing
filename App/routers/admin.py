from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from App.database import get_db
from App.repositories.education_repository import Education_Repository
from App.repositories.hash_repository import Hash_Repository
from App.utils.dependencies import get_current_user

from App.utils.admin_utils import *

router = APIRouter()
templates = Jinja2Templates(directory="App/templates")


@router.get("/admin", name="admin")
def admin(
    request: Request,
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    return redirect_to_route(
        request,
        "admin_hash_functions",
        success=success,
        error=error,
    )


@router.get("/admin/hash-functions", name="admin_hash_functions")
def admin_hash_functions(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    hash_repo = Hash_Repository(db)
    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/hash_functions.html",
        admin_section="hash-functions",
        admin_title="Хеш-функции",
        admin_description=(
            "Включайте и выключайте алгоритмы, доступные пользователям на страницах "
            "демонстрации и сравнения."
        ),
        error=error,
        success=success,
        hash_functions=hash_repo.get_hash_functions(),
    )


@router.post("/admin/hash-functions/{option_id}/toggle", name="admin_toggle_hash_function")
def admin_toggle_hash_function(
    option_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    hash_repo = Hash_Repository(db)
    option = hash_repo.get_hash_function_by_id(option_id)

    if not option:
        return redirect_to_route(
            request,
            "admin_hash_functions",
            error="Хеш-функция не найдена.",
        )

    option.is_enabled = not option.is_enabled
    hash_repo.commit()

    action = "включена" if option.is_enabled else "выключена"
    return redirect_to_route(
        request,
        "admin_hash_functions",
        success=f"Хеш-функция {option.label} {action}.",
    )


@router.post(
    "/admin/hash-functions/{option_id}/order",
    name="admin_update_hash_function_order",
)
def admin_update_hash_function_order(
    option_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort_order: str = Form("0"),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    hash_repo = Hash_Repository(db)
    option = hash_repo.get_hash_function_by_id(option_id)

    if not option:
        return redirect_to_route(
            request,
            "admin_hash_functions",
            error="Хеш-функция не найдена.",
        )

    try:
        option.sort_order = parse_sort_order(sort_order)
        hash_repo.commit()
        return redirect_to_route(
            request,
            "admin_hash_functions",
            success=f"Порядок для {option.label} обновлён.",
        )
    except ValueError as exc:
        hash_repo.rollback()
        return redirect_to_route(
            request,
            "admin_hash_functions",
            error=str(exc),
        )


@router.get("/admin/collision-methods", name="admin_collision_methods")
def admin_collision_methods(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    hash_repo = Hash_Repository(db)
    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/collision_methods.html",
        admin_section="collision-methods",
        admin_title="Методы разрешения коллизий",
        admin_description=(
            "Управляйте тем, какие методы разрешения коллизий доступны в демонстрации "
            "и на странице сравнения хеш-функций."
        ),
        error=error,
        success=success,
        collision_methods=hash_repo.get_collision_methods(),
    )


@router.post(
    "/admin/collision-methods/{option_id}/toggle",
    name="admin_toggle_collision_method",
)
def admin_toggle_collision_method(
    option_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    hash_repo = Hash_Repository(db)
    option = hash_repo.get_collision_method_by_id(option_id)

    if not option:
        return redirect_to_route(
            request,
            "admin_collision_methods",
            error="Метод разрешения коллизий не найден.",
        )

    option.is_enabled = not option.is_enabled
    hash_repo.commit()

    action = "включён" if option.is_enabled else "выключен"
    return redirect_to_route(
        request,
        "admin_collision_methods",
        success=f"Метод {option.label} {action}.",
    )


@router.post(
    "/admin/collision-methods/{option_id}/order",
    name="admin_update_collision_method_order",
)
def admin_update_collision_method_order(
    option_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    sort_order: str = Form("0"),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    hash_repo = Hash_Repository(db)
    option = hash_repo.get_collision_method_by_id(option_id)

    if not option:
        return redirect_to_route(
            request,
            "admin_collision_methods",
            error="Метод разрешения коллизий не найден.",
        )

    try:
        option.sort_order = parse_sort_order(sort_order)
        hash_repo.commit()
        return redirect_to_route(
            request,
            "admin_collision_methods",
            success=f"Порядок для {option.label} обновлён.",
        )
    except ValueError as exc:
        hash_repo.rollback()
        return redirect_to_route(
            request,
            "admin_collision_methods",
            error=str(exc),
        )


@router.get("/admin/pages", name="admin_pages")
def admin_pages(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    pages = education_repo.get_pages()
    section_counts_by_page, published_section_counts_by_page = build_page_statistics(
        education_repo
    )

    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/pages.html",
        admin_section="pages",
        admin_title="Страницы обучения",
        admin_description=(
            "Создавайте и редактируйте страницы учебного раздела. Каждая страница "
            "может содержать собственную иерархию статей."
        ),
        error=error,
        success=success,
        pages=pages,
        section_counts_by_page=section_counts_by_page,
        published_section_counts_by_page=published_section_counts_by_page,
    )


@router.get("/admin/pages/new", name="admin_new_page")
def admin_new_page(
    request: Request,
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    page_data = {
        "title": "",
        "slug": "",
        "description": "",
        "sort_order": 0,
        "is_published": True,
    }
    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/page_form.html",
        admin_section="pages",
        admin_title="Новая страница обучения",
        admin_description=(
            "Создайте отдельную страницу для учебных материалов. После сохранения к ней "
            "можно будет добавлять статьи."
        ),
        error=error,
        success=success,
        form_mode="create",
        page=page_data,
    )


@router.get("/admin/pages/{page_id}/edit", name="admin_edit_page")
def admin_edit_page(
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    page = education_repo.get_page_by_id(page_id)

    if not page:
        return redirect_to_route(request, "admin_pages", error="Страница обучения не найдена.")

    section_counts_by_page, published_section_counts_by_page = build_page_statistics(
        education_repo
    )

    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/page_form.html",
        admin_section="pages",
        admin_title=f"Редактирование страницы: {page.title}",
        admin_description=(
            "Изменяйте параметры страницы, управляйте публикацией и переходите к "
            "добавлению статей."
        ),
        error=error,
        success=success,
        form_mode="edit",
        page=page,
        section_count=section_counts_by_page.get(page.id, 0),
        published_section_count=published_section_counts_by_page.get(page.id, 0),
    )


@router.post("/admin/pages/create", name="admin_create_page")
def admin_create_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    title: str = Form(""),
    slug: str = Form(""),
    description: str = Form(""),
    sort_order: str = Form("0"),
    is_published: str | None = Form(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)

    try:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("У страницы должен быть заголовок.")

        normalized_slug = normalize_slug(slug)
        if education_repo.get_page_by_slug(normalized_slug):
            raise ValueError("Страница с такой строкой-идентификатором уже существует.")

        page = education_repo.create_page(
            title=normalized_title,
            slug=normalized_slug,
            description=description.strip() or None,
            sort_order=parse_sort_order(sort_order),
            is_published=is_published is not None,
        )
        education_repo.commit()
        return redirect_to_route(
            request,
            "admin_edit_page",
            path_params={"page_id": page.id},
            success="Страница обучения создана.",
        )
    except (ValueError, IntegrityError) as exc:
        education_repo.rollback()
        return redirect_to_route(
            request,
            "admin_new_page",
            error=str(exc),
        )


@router.post("/admin/pages/{page_id}/update", name="admin_update_page")
def admin_update_page(
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    title: str = Form(""),
    slug: str = Form(""),
    description: str = Form(""),
    sort_order: str = Form("0"),
    is_published: str | None = Form(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    page = education_repo.get_page_by_id(page_id)

    if not page:
        return redirect_to_route(request, "admin_pages", error="Страница обучения не найдена.")

    try:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("У страницы должен быть заголовок.")

        normalized_slug = normalize_slug(slug)
        slug_owner = education_repo.get_page_by_slug(normalized_slug)
        if slug_owner and slug_owner.id != page.id:
            raise ValueError("Страница с таким такой строкой-идентификатором уже существует.")

        page.title = normalized_title
        page.slug = normalized_slug
        page.description = description.strip() or None
        page.sort_order = parse_sort_order(sort_order)
        page.is_published = is_published is not None
        education_repo.commit()
        return redirect_to_route(
            request,
            "admin_edit_page",
            path_params={"page_id": page.id},
            success="Страница обучения обновлена.",
        )
    except (ValueError, IntegrityError) as exc:
        education_repo.rollback()
        return redirect_to_route(
            request,
            "admin_edit_page",
            path_params={"page_id": page.id},
            error=str(exc),
        )


@router.post("/admin/pages/{page_id}/delete", name="admin_delete_page")
def admin_delete_page(
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    page = education_repo.get_page_by_id(page_id)

    if not page:
        return redirect_to_route(request, "admin_pages", error="Страница обучения не найдена.")

    education_repo.delete_page(page)
    education_repo.commit()
    return redirect_to_route(
        request,
        "admin_pages",
        success="Страница обучения удалена.",
    )


@router.get("/admin/articles", name="admin_articles")
def admin_articles(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    pages = education_repo.get_pages()

    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/articles.html",
        admin_section="articles",
        admin_title="Статьи обучения",
        admin_description=(
            "Работайте с учебными статьями отдельно от страниц. Список ниже выстроен "
            "по иерархии: сначала родительская статья, затем её дочерние материалы."
        ),
        error=error,
        success=success,
        article_groups=build_article_groups(education_repo, pages),
        has_pages=bool(pages),
    )


@router.get("/admin/articles/new", name="admin_new_section")
def admin_new_section(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page_id: int | None = Query(None),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    pages = education_repo.get_pages()

    if not pages:
        return redirect_to_route(
            request,
            "admin_pages",
            error="Сначала создайте страницу обучения, а затем добавляйте статьи.",
        )

    selected_page, page_error = resolve_selected_page(education_repo, pages, page_id)
    section_data = {
        "title": "",
        "slug": "",
        "summary": "",
        "content": "",
        "sort_order": 0,
        "is_published": True,
        "parent_id": None,
    }

    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/section_form.html",
        admin_section="articles",
        admin_title="Новая статья",
        admin_description=(
            "Создайте отдельную статью и при необходимости вложите её в уже существующую "
            "структуру выбранной страницы."
        ),
        error=error or page_error,
        success=success,
        form_mode="create",
        section=section_data,
        available_pages=pages,
        selected_page=selected_page,
        parent_options=education_repo.get_parent_section_options(selected_page.id),
    )


@router.get("/admin/articles/{section_id}/edit", name="admin_edit_section")
def admin_edit_section(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = Query(None),
    success: str = Query(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    section = education_repo.get_section_by_id(section_id)

    if not section:
        return redirect_to_route(request, "admin_articles", error="Статья обучения не найдена.")

    page = education_repo.get_page_by_id(section.page_id)

    return render_admin_template(
        request=request,
        current_user=current_user,
        template_name="admin/section_form.html",
        admin_section="articles",
        admin_title=f"Редактирование статьи: {section.title}",
        admin_description=(
            "Изменяйте заголовок, содержимое, вложенность и порядок отображения статьи "
            "внутри выбранной страницы."
        ),
        error=error,
        success=success,
        form_mode="edit",
        section=section,
        available_pages=education_repo.get_pages(),
        selected_page=page,
        parent_options=education_repo.get_parent_section_options(
            page.id,
            current_section_id=section.id,
        ),
    )


@router.post("/admin/sections/create", name="admin_create_section")
def admin_create_section(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page_id: int = Form(...),
    parent_id: str | None = Form(None),
    title: str = Form(""),
    slug: str = Form(""),
    summary: str = Form(""),
    content: str = Form(""),
    sort_order: str = Form("0"),
    is_published: str | None = Form(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    page = education_repo.get_page_by_id(page_id)

    if not page:
        return redirect_to_route(
            request,
            "admin_articles",
            error="Страница для новой статьи не найдена.",
        )

    try:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("У статьи должен быть заголовок.")

        normalized_slug = normalize_slug(slug)
        if education_repo.get_section_by_page_and_slug(page_id, normalized_slug):
            raise ValueError("Статья с такой строкой-идентификатором уже существует в этой странице.")

        parent = resolve_parent_section(
            education_repo,
            page_id=page.id,
            parent_id=optional_parent_id(parent_id),
        )

        section = education_repo.create_section(
            page_id=page.id,
            parent_id=parent.id if parent else None,
            title=normalized_title,
            slug=normalized_slug,
            summary=summary.strip() or None,
            content=content.strip() or None,
            sort_order=parse_sort_order(sort_order),
            is_published=is_published is not None,
        )
        education_repo.commit()
        return redirect_to_route(
            request,
            "admin_edit_section",
            path_params={"section_id": section.id},
            success="Статья обучения создана.",
        )
    except (ValueError, IntegrityError) as exc:
        education_repo.rollback()
        return redirect_to_route(
            request,
            "admin_new_section",
            error=str(exc),
            query_params={"page_id": page.id},
        )


@router.post("/admin/sections/{section_id}/update", name="admin_update_section")
def admin_update_section(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    parent_id: str | None = Form(None),
    title: str = Form(""),
    slug: str = Form(""),
    summary: str = Form(""),
    content: str = Form(""),
    sort_order: str = Form("0"),
    is_published: str | None = Form(None),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    section = education_repo.get_section_by_id(section_id)

    if not section:
        return redirect_to_route(request, "admin_articles", error="Статья обучения не найдена.")

    try:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("У статьи должен быть заголовок.")

        normalized_slug = normalize_slug(slug)
        slug_owner = education_repo.get_section_by_page_and_slug(
            section.page_id,
            normalized_slug,
        )
        if slug_owner and slug_owner.id != section.id:
            raise ValueError("Статья с такой строкой-идентификатором уже существует в этой странице.")

        parent = resolve_parent_section(
            education_repo,
            page_id=section.page_id,
            parent_id=optional_parent_id(parent_id),
            current_section_id=section.id,
        )

        section.parent_id = parent.id if parent else None
        section.title = normalized_title
        section.slug = normalized_slug
        section.summary = summary.strip() or None
        section.content = content.strip() or None
        section.sort_order = parse_sort_order(sort_order)
        section.is_published = is_published is not None
        education_repo.commit()
        return redirect_to_route(
            request,
            "admin_edit_section",
            path_params={"section_id": section.id},
            success="Статья обучения обновлена.",
        )
    except (ValueError, IntegrityError) as exc:
        education_repo.rollback()
        return redirect_to_route(
            request,
            "admin_edit_section",
            path_params={"section_id": section.id},
            error=str(exc),
        )


@router.post("/admin/sections/{section_id}/delete", name="admin_delete_section")
def admin_delete_section(
    section_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not ensure_admin(current_user):
        return RedirectResponse(url="/", status_code=303)

    education_repo = Education_Repository(db)
    section = education_repo.get_section_by_id(section_id)

    if not section:
        return redirect_to_route(request, "admin_articles", error="Статья обучения не найдена.")

    education_repo.delete_section(section)
    education_repo.commit()
    return redirect_to_route(
        request,
        "admin_articles",
        success="Статья обучения удалена.",
    )
