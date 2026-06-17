from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy.orm import Session

from uuid import uuid4
from urllib.parse import urlencode

from App.repositories.hash_repository import Hash_Repository
from App.services.hash_service import Hash_Service
from App.services.compare_service import Compare_Service
from App.repositories.compare_repository import Compare_Repository

DEMO_GUEST_COOKIE_NAME = "demo_guest_token"
COMPARE_GUEST_COOKIE_NAME = "compare_guest_token"

def ensure_demo_guest_token(request: Request, current_user):
    if getattr(current_user, "role", None) != "guest":
        return None, False

    guest_token = request.cookies.get(DEMO_GUEST_COOKIE_NAME)

    if guest_token:
        return guest_token, False

    return uuid4().hex, True


def apply_demo_guest_cookie(
    response: Response,
    current_user,
    guest_token: str,
    should_set_cookie: bool,
):
    if getattr(current_user, "role", None) != "guest":
        return response

    if guest_token and should_set_cookie:
        response.set_cookie(
            key=DEMO_GUEST_COOKIE_NAME,
            value=guest_token,
            httponly=True,
            samesite="lax",
        )

    return response


def build_demo_workspace_url(
    request: Request,
    hash_function: str,
    collision_method: str,
    success: str = None,
):
    params = {
        "hash_function": hash_function,
        "collision_method": collision_method,
    }

    if success:
        params["success"] = success

    return f"{request.url_for('demo_workspace')}?{urlencode(params)}"


def render_demo_error_state(
    service: Hash_Service,
    repo: Hash_Repository,
    request: Request,
    current_user,
    guest_token: str,
    hash_function: str,
    collision_method: str,
    error: str,
):
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
            error=error,
            selected_hash_function=hash_function,
            selected_collision_method=collision_method,
            is_guest_demo=getattr(current_user, "role", None) == "guest",
        )
        return response

    scope = service.build_storage_scope(current_user, guest_token)
    entries = repo.get_entries(
        normalized_hash_function,
        normalized_collision_method,
        user_id=scope.user_id,
        guest_token=scope.guest_token,
    )

    try:
        return service.render_demo_workspace(
            request=request,
            current_user=current_user,
            repo=repo,
            hash_function=normalized_hash_function,
            collision_method=normalized_collision_method,
            entries=entries,
            error=error,
            is_guest_demo=scope.is_guest,
        )
    except ValueError:
        return service.render_demo_selection_page(
            request=request,
            current_user=current_user,
            repo=repo,
            error=error,
            selected_hash_function=normalized_hash_function,
            selected_collision_method=normalized_collision_method,
            is_guest_demo=getattr(current_user, "role", None) == "guest",
        )

def ensure_compare_guest_token(request: Request, current_user):
    if getattr(current_user, "role", None) != "guest":
        return None, False

    guest_token = request.cookies.get(COMPARE_GUEST_COOKIE_NAME)

    if guest_token:
        return guest_token, False

    return uuid4().hex, True


def apply_compare_guest_cookie(
    response: Response,
    current_user,
    guest_token: str,
    should_set_cookie: bool,
):
    if getattr(current_user, "role", None) != "guest":
        return response

    if guest_token and should_set_cookie:
        response.set_cookie(
            key=COMPARE_GUEST_COOKIE_NAME,
            value=guest_token,
            httponly=True,
            samesite="lax",
        )

    return response


def build_compare_workspace_url(
    request: Request,
    hash_functions: list[str],
    collision_method: str,
    success: str = None,
):
    params = [("hash_function", code) for code in hash_functions]
    params.append(("collision_method", collision_method))

    if success:
        params.append(("success", success))

    return f"{request.url_for('compare_workspace')}?{urlencode(params)}"


def render_compare_error_state(
    service: Compare_Service,
    compare_repo: Compare_Repository,
    hash_repo: Hash_Repository,
    request: Request,
    current_user,
    guest_token: str,
    hash_functions: list[str] | None,
    collision_method: str | None,
    error: str,
):
    normalized_hash_functions = service.normalize_hash_functions(
        hash_repo,
        hash_functions,
    )
    normalized_collision_method = service.normalize_collision_method(
        hash_repo,
        collision_method,
    )

    if len(normalized_hash_functions) < 2:
        return service.render_compare_selection_page(
            request=request,
            current_user=current_user,
            hash_repo=hash_repo,
            error=error,
            selected_hash_functions=hash_functions,
            selected_collision_method=collision_method,
            is_guest_compare=getattr(current_user, "role", None) == "guest",
        )

    try:
        (
            normalized_hash_functions,
            normalized_collision_method,
            hash_functions_info,
            _resolved,
            collision_method_info,
            _collision_method_object,
            _collision_option,
        ) = service.ensure_compare_selection(
            hash_repo,
            normalized_hash_functions,
            normalized_collision_method,
        )
    except ValueError:
        return service.render_compare_selection_page(
            request=request,
            current_user=current_user,
            hash_repo=hash_repo,
            error=error,
            selected_hash_functions=hash_functions,
            selected_collision_method=collision_method,
            is_guest_compare=getattr(current_user, "role", None) == "guest",
        )
    scope = service.hash_service.build_storage_scope(current_user, guest_token)
    selection_key = service.get_selection_key(normalized_hash_functions)
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

    return service.render_compare_workspace(
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
        is_guest_compare=scope.is_guest,
    )


def build_compare_table_states(
    service: Compare_Service,
    compare_repo: Compare_Repository,
    hash_functions_info,
    collision_method_object,
    selection_key: str,
    collision_method: str,
    user_id: int = None,
    guest_token: str = None,
):
    table_states = []

    for hash_function_info in hash_functions_info:
        function_entries = compare_repo.get_results_for_selection(
            selection_key=selection_key,
            collision_method=collision_method,
            hash_function=hash_function_info["value"],
            user_id=user_id,
            guest_token=guest_token,
        )
        table_states.append(
            {
                **hash_function_info,
                "table_state": collision_method_object.build_table_state(
                    function_entries,
                    service.hash_service.TABLE_SIZE,
                ),
            }
        )

    return table_states
