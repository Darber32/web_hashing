from urllib.parse import unquote, urlencode
from uuid import uuid4


from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from App.database import get_db
from App.repositories.education_repository import Education_Repository
from App.repositories.compare_repository import Compare_Repository
from App.repositories.hash_repository import Hash_Repository
from App.services.compare_service import Compare_Service
from App.services.hash_service import Hash_Service

from App.utils.education_page import render_education_page
from App.utils.dependencies import get_current_user
from App.utils.hash_utils import ensure_demo_guest_token, apply_demo_guest_cookie, ensure_compare_guest_token, apply_compare_guest_cookie, build_compare_table_states

router = APIRouter()

templates = Jinja2Templates(directory="App/templates")

@router.get("/", name="index")
def index(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )


@router.get("/login", name="login_page")
def login(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    error: str = None,
):
    if current_user.role != "guest":
        return RedirectResponse(url="/profile", status_code=303)

    error = request.cookies.get("error_msg")
    if error:
        error = unquote(error)
        response.delete_cookie("error_msg")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "current_user": current_user,
            "error": error,
        },
    )


@router.get("/register", name="register_page")
def register(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
):
    if current_user.role != "guest":
        return RedirectResponse(url="/profile", status_code=303)

    error = request.cookies.get("error_msg")
    if error:
        error = unquote(error)
        response.delete_cookie("error_msg")

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "current_user": current_user,
            "error": error,
        },
    )


@router.get("/profile", name="profile")
def profile(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
):
    if current_user.role == "guest":
        return RedirectResponse(url="/login", status_code=303)

    error = request.cookies.get("error_msg")
    if error:
        error = unquote(error)
        response.delete_cookie("error_msg")

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "current_user": current_user,
            "error": error,
        },
    )


@router.get("/education", name="education")
def education(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = None,
):
    repo = Education_Repository(db)
    pages = repo.get_published_pages()

    if not pages:
        return render_education_page(
            request=request,
            current_user=current_user,
            pages=[],
            page=None,
            sections=[],
            error=error,
        )

    page = pages[0]
    sections = repo.get_published_section_tree(page.id)

    return render_education_page(
        request=request,
        current_user=current_user,
        pages=pages,
        page=page,
        sections=sections,
        error=error,
    )


@router.get("/education/{page_slug}", name="education_page")
def education_page(
    page_slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = None,
):
    repo = Education_Repository(db)
    pages = repo.get_published_pages()

    if not pages:
        return RedirectResponse(url="/education", status_code=303)

    page = repo.get_published_page_by_slug(page_slug)

    if not page:
        return RedirectResponse(url="/education", status_code=303)

    sections = repo.get_published_section_tree(page.id)

    return render_education_page(
        request=request,
        current_user=current_user,
        pages=pages,
        page=page,
        sections=sections,
        error=error,
    )


@router.get("/demo", name="demo")
def demo(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = None,
    hash_function: str = None,
    collision_method: str = None,
):
    repo = Hash_Repository(db)
    service = Hash_Service()
    guest_token, should_set_cookie = ensure_demo_guest_token(request, current_user)
    response = service.render_demo_selection_page(
        request=request,
        current_user=current_user,
        repo=repo,
        error=error,
        selected_hash_function=hash_function,
        selected_collision_method=collision_method,
        is_guest_demo=getattr(current_user, "role", None) == "guest",
    )
    return apply_demo_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )


@router.get("/demo/workspace", name="demo_workspace")
def demo_workspace(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    hash_function: str = None,
    collision_method: str = None,
    error: str = None,
    success: str = None,
):
    repo = Hash_Repository(db)
    service = Hash_Service()
    guest_token, should_set_cookie = ensure_demo_guest_token(request, current_user)
    normalized_hash_function, normalized_collision_method = service.normalize_selection(
        repo,
        hash_function,
        collision_method,
    )

    if not normalized_hash_function or not normalized_collision_method:
        response = service.render_demo_selection_page(
            request=request,
            current_user=current_user,
            repo=repo,
            error=error or "Сейчас нет ни одной включённой хеш-функции или метода разрешения коллизий.",
            selected_hash_function=hash_function,
            selected_collision_method=collision_method,
            is_guest_demo=getattr(current_user, "role", None) == "guest",
        )
        return apply_demo_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )

    try:
        scope = service.build_storage_scope(current_user, guest_token)
        entries = repo.get_entries(
            normalized_hash_function,
            normalized_collision_method,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )
        response = service.render_demo_workspace(
            request=request,
            current_user=current_user,
            repo=repo,
            hash_function=normalized_hash_function,
            collision_method=normalized_collision_method,
            entries=entries,
            error=error,
            success=success,
            is_guest_demo=scope.is_guest,
        )
        return apply_demo_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )
    except ValueError as exc:
        response = service.render_demo_selection_page(
            request=request,
            current_user=current_user,
            repo=repo,
            error=str(exc),
            selected_hash_function=normalized_hash_function,
            selected_collision_method=normalized_collision_method,
            is_guest_demo=getattr(current_user, "role", None) == "guest",
        )
        return apply_demo_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )


@router.get("/compare", name="compare")
def compare(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    error: str = None,
    hash_function: list[str] | None = Query(None),
    collision_method: str | None = Query(None),
):
    hash_repo = Hash_Repository(db)
    service = Compare_Service()
    guest_token, should_set_cookie = ensure_compare_guest_token(request, current_user)
    response = service.render_compare_selection_page(
        request=request,
        current_user=current_user,
        hash_repo=hash_repo,
        error=error,
        selected_hash_functions=hash_function,
        selected_collision_method=collision_method,
        is_guest_compare=getattr(current_user, "role", None) == "guest",
    )
    return apply_compare_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )


@router.get("/compare/workspace", name="compare_workspace")
def compare_workspace(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    hash_function: list[str] | None = Query(None),
    collision_method: str | None = Query(None),
    error: str = None,
    success: str = None,
):
    hash_repo = Hash_Repository(db)
    compare_repo = Compare_Repository(db)
    service = Compare_Service()
    guest_token, should_set_cookie = ensure_compare_guest_token(request, current_user)

    try:
        (
            normalized_hash_functions,
            normalized_collision_method,
            hash_functions_info,
            _resolved_functions,
            collision_method_info,
            _collision_method_object,
            _collision_option,
        ) = service.ensure_compare_selection(hash_repo, hash_function, collision_method)
    except ValueError as exc:
        response = service.render_compare_selection_page(
            request=request,
            current_user=current_user,
            hash_repo=hash_repo,
            error=error or str(exc),
            selected_hash_functions=hash_function,
            selected_collision_method=collision_method,
            is_guest_compare=getattr(current_user, "role", None) == "guest",
        )
        return apply_compare_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )

    scope = service.hash_service.build_storage_scope(current_user, guest_token)
    selection_key = service.get_selection_key(normalized_hash_functions)
    entries = compare_repo.get_entries(
        selection_key=selection_key,
        collision_method=normalized_collision_method,
        user_id=scope.user_id,
        guest_token=scope.guest_token,
    )

    if any(not result.collision_note for entry in entries for result in entry.results):
        collision_context = service.hash_service.build_collision_context(
            hash_repo,
            _collision_option,
        )

        for hash_function_info in hash_functions_info:
            result_entries = compare_repo.get_results_for_selection(
                selection_key=selection_key,
                collision_method=normalized_collision_method,
                hash_function=hash_function_info["value"],
                user_id=scope.user_id,
                guest_token=scope.guest_token,
            )
            _collision_method_object.rebuild_entries(
                result_entries,
                collision_context,
            )

        compare_repo.commit()
        entries = compare_repo.get_entries(
            selection_key=selection_key,
            collision_method=normalized_collision_method,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )

    table_states = build_compare_table_states(
        service=service,
        compare_repo=compare_repo,
        hash_functions_info=hash_functions_info,
        collision_method_object=_collision_method_object,
        selection_key=selection_key,
        collision_method=normalized_collision_method,
        user_id=scope.user_id,
        guest_token=scope.guest_token,
    )

    response = service.render_compare_workspace(
        request=request,
        current_user=current_user,
        hash_functions_info=hash_functions_info,
        collision_method_info=collision_method_info,
        selected_hash_functions=normalized_hash_functions,
        selected_collision_method=normalized_collision_method,
        entries=entries,
        table_states=table_states,
        table_size=service.hash_service.TABLE_SIZE,
        error=error,
        success=success,
        is_guest_compare=scope.is_guest,
    )
    return apply_compare_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )
