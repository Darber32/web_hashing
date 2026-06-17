from fastapi import APIRouter, Depends, Form, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from App.database import get_db
from App.utils.dependencies import get_current_user

from App.repositories.hash_repository import Hash_Repository
from App.services.hash_service import Hash_Service
from App.utils.hash_utils import *


router = APIRouter(prefix="/hash")


@router.post("/demo/workspace/add", name="demo_add")
def demo_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    hash_function: str = Form(...),
    collision_method: str = Form(...),
    message: str = Form(""),
):
    repo = Hash_Repository(db)
    service = Hash_Service()
    guest_token, should_set_cookie = ensure_demo_guest_token(request, current_user)

    try:
        service.add_message(
            repo,
            current_user,
            hash_function,
            collision_method,
            message,
            guest_token=guest_token,
        )
    except ValueError as exc:
        repo.rollback()
        response = render_demo_error_state(
            service=service,
            repo=repo,
            request=request,
            current_user=current_user,
            guest_token=guest_token,
            hash_function=hash_function,
            collision_method=collision_method,
            error=str(exc),
        )
        return apply_demo_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )

    response = RedirectResponse(
        url=build_demo_workspace_url(
            request,
            hash_function,
            collision_method,
            success="Сообщение добавлено в демонстрационную таблицу.",
        ),
        status_code=303,
    )
    return apply_demo_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )


@router.post("/demo/workspace/delete/{entry_id}", name="demo_delete")
def demo_delete(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    hash_function: str = Form(...),
    collision_method: str = Form(...),
):
    repo = Hash_Repository(db)
    service = Hash_Service()
    guest_token, should_set_cookie = ensure_demo_guest_token(request, current_user)

    try:
        service.delete_message(
            repo,
            entry_id,
            current_user,
            hash_function,
            collision_method,
            guest_token=guest_token,
        )
    except ValueError as exc:
        repo.rollback()
        response = render_demo_error_state(
            service=service,
            repo=repo,
            request=request,
            current_user=current_user,
            guest_token=guest_token,
            hash_function=hash_function,
            collision_method=collision_method,
            error=str(exc),
        )
        return apply_demo_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )

    response = RedirectResponse(
        url=build_demo_workspace_url(
            request,
            hash_function,
            collision_method,
            success="Сообщение удалено из демонстрационной таблицы.",
        ),
        status_code=303,
    )
    return apply_demo_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )


@router.post("/demo/workspace/clear", name="demo_clear")
def demo_clear(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if getattr(current_user, "role", None) != "guest":
        return Response(status_code=204)

    guest_token = request.cookies.get(DEMO_GUEST_COOKIE_NAME)

    if not guest_token:
        return Response(status_code=204)

    repo = Hash_Repository(db)
    service = Hash_Service()
    service.clear_guest_entries(repo, guest_token)
    return Response(status_code=204)


@router.post("/compare/workspace/add", name="compare_add")
def compare_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    hash_function: list[str] = Form(...),
    collision_method: str = Form(...),
    message: str = Form(""),
):
    hash_repo = Hash_Repository(db)
    compare_repo = Compare_Repository(db)
    service = Compare_Service()
    guest_token, should_set_cookie = ensure_compare_guest_token(request, current_user)

    try:
        service.add_comparison(
            compare_repo=compare_repo,
            hash_repo=hash_repo,
            current_user=current_user,
            hash_functions=hash_function,
            collision_method=collision_method,
            message=message,
            guest_token=guest_token,
        )
    except ValueError as exc:
        compare_repo.rollback()
        response = render_compare_error_state(
            service=service,
            compare_repo=compare_repo,
            hash_repo=hash_repo,
            request=request,
            current_user=current_user,
            guest_token=guest_token,
            hash_functions=hash_function,
            collision_method=collision_method,
            error=str(exc),
        )
        return apply_compare_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )

    response = RedirectResponse(
        url=build_compare_workspace_url(
            request,
            service.normalize_hash_functions(hash_repo, hash_function),
            service.normalize_collision_method(hash_repo, collision_method),
            success="Сообщение добавлено в таблицу сравнения.",
        ),
        status_code=303,
    )
    return apply_compare_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )


@router.post("/compare/workspace/delete/{entry_id}", name="compare_delete")
def compare_delete(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    hash_function: list[str] = Form(...),
    collision_method: str = Form(...),
):
    hash_repo = Hash_Repository(db)
    compare_repo = Compare_Repository(db)
    service = Compare_Service()
    guest_token, should_set_cookie = ensure_compare_guest_token(request, current_user)

    try:
        service.delete_comparison(
            compare_repo=compare_repo,
            hash_repo=hash_repo,
            current_user=current_user,
            entry_id=entry_id,
            hash_functions=hash_function,
            collision_method=collision_method,
            guest_token=guest_token,
        )
    except ValueError as exc:
        compare_repo.rollback()
        response = render_compare_error_state(
            service=service,
            compare_repo=compare_repo,
            hash_repo=hash_repo,
            request=request,
            current_user=current_user,
            guest_token=guest_token,
            hash_functions=hash_function,
            collision_method=collision_method,
            error=str(exc),
        )
        return apply_compare_guest_cookie(
            response,
            current_user,
            guest_token,
            should_set_cookie,
        )

    response = RedirectResponse(
        url=build_compare_workspace_url(
            request,
            service.normalize_hash_functions(hash_repo, hash_function),
            service.normalize_collision_method(hash_repo, collision_method),
            success="Строка сравнения удалена.",
        ),
        status_code=303,
    )
    return apply_compare_guest_cookie(
        response,
        current_user,
        guest_token,
        should_set_cookie,
    )


@router.post("/compare/workspace/clear", name="compare_clear")
def compare_clear(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if getattr(current_user, "role", None) != "guest":
        return Response(status_code=204)

    guest_token = request.cookies.get(COMPARE_GUEST_COOKIE_NAME)

    if not guest_token:
        return Response(status_code=204)

    compare_repo = Compare_Repository(db)
    service = Compare_Service()
    service.clear_guest_entries(compare_repo, guest_token)
    return Response(status_code=204)
