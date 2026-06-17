from fastapi import Request
from fastapi.templating import Jinja2Templates

from App.services.hash_service import Hash_Service

templates = Jinja2Templates(directory="App/templates")


class Compare_Service:

    def __init__(self):
        self.hash_service = Hash_Service()

    def normalize_hash_functions(self, hash_repo, hash_functions: list[str] | None):
        available_codes = [
            item["value"]
            for item in self.hash_service.get_hash_function_choices(hash_repo)
        ]
        normalized = []

        for code in hash_functions or []:
            if code in available_codes and code not in normalized:
                normalized.append(code)

        return normalized

    def normalize_collision_method(self, hash_repo, collision_method: str | None):
        available_codes = [
            item["value"]
            for item in self.hash_service.get_collision_method_choices(hash_repo)
        ]

        if collision_method in available_codes:
            return collision_method

        return available_codes[0] if available_codes else None

    def get_selection_key(self, hash_functions: list[str]):
        return ",".join(sorted(hash_functions))

    def ensure_compare_selection(
        self,
        hash_repo,
        hash_functions: list[str] | None,
        collision_method: str | None,
    ):
        normalized_hash_functions = self.normalize_hash_functions(
            hash_repo,
            hash_functions,
        )

        if len(normalized_hash_functions) < 2:
            raise ValueError("Для сравнения нужно выбрать минимум две хеш-функции.")

        normalized_collision_method = self.normalize_collision_method(
            hash_repo,
            collision_method,
        )

        if not normalized_collision_method:
            raise ValueError(
                "Сейчас недоступен ни один метод разрешения коллизий для страницы сравнения."
            )

        hash_functions_info = []
        resolved_functions = []

        for code in normalized_hash_functions:
            info, implementation = self.hash_service.resolve_hash_function(
                hash_repo,
                code,
            )
            hash_functions_info.append(info)
            resolved_functions.append((info, implementation))

        (
            collision_method_info,
            collision_method_object,
            collision_option,
        ) = self.hash_service.resolve_collision_method(
            hash_repo,
            normalized_collision_method,
        )

        return (
            normalized_hash_functions,
            normalized_collision_method,
            hash_functions_info,
            resolved_functions,
            collision_method_info,
            collision_method_object,
            collision_option,
        )

    def trim_compare_process_note(self, process_note: str):
        lines = [line for line in process_note.splitlines() if line.strip()]

        if len(lines) <= 1:
            return process_note

        last_line = lines[-1].lower()
        if "таблиц" in last_line or "индекс" in last_line:
            return "\n".join(lines[:-1])

        return process_note

    def render_compare_selection_page(
        self,
        request: Request,
        current_user,
        hash_repo,
        error: str = None,
        selected_hash_functions: list[str] | None = None,
        selected_collision_method: str | None = None,
        is_guest_compare: bool = False,
    ):
        hash_functions = self.hash_service.get_hash_function_choices(hash_repo)
        collision_methods = self.hash_service.get_collision_method_choices(hash_repo)
        normalized_hash_functions = self.normalize_hash_functions(
            hash_repo,
            selected_hash_functions,
        )
        normalized_collision_method = self.normalize_collision_method(
            hash_repo,
            selected_collision_method,
        )

        return templates.TemplateResponse(
            "compare.html",
            {
                "request": request,
                "current_user": current_user,
                "hash_functions": hash_functions,
                "collision_methods": collision_methods,
                "selected_hash_functions": normalized_hash_functions,
                "selected_collision_method": normalized_collision_method,
                "error": error,
                "has_available_choices": len(hash_functions) >= 2 and bool(collision_methods),
                "is_guest_compare": is_guest_compare,
            },
        )

    def render_compare_workspace(
        self,
        request: Request,
        current_user,
        hash_functions_info,
        collision_method_info,
        selected_hash_functions: list[str],
        selected_collision_method: str,
        entries,
        table_states,
        table_size: int,
        error: str = None,
        success: str = None,
        is_guest_compare: bool = False,
    ):
        return templates.TemplateResponse(
            "compare_workspace.html",
            {
                "request": request,
                "current_user": current_user,
                "hash_functions_info": hash_functions_info,
                "collision_method_info": collision_method_info,
                "selected_hash_functions": selected_hash_functions,
                "selected_collision_method": selected_collision_method,
                "entries": entries,
                "table_states": table_states,
                "table_size": table_size,
                "error": error,
                "success": success,
                "is_guest_compare": is_guest_compare,
            },
        )

    def add_comparison(
        self,
        compare_repo,
        hash_repo,
        current_user,
        hash_functions: list[str],
        collision_method: str,
        message: str,
        guest_token: str = None,
    ):
        (
            normalized_hash_functions,
            normalized_collision_method,
            _hash_functions_info,
            resolved_functions,
            _collision_method_info,
            collision_method_object,
            collision_option,
        ) = self.ensure_compare_selection(
            hash_repo,
            hash_functions,
            collision_method,
        )
        selection_key = self.get_selection_key(normalized_hash_functions)
        collision_context = self.hash_service.build_collision_context(
            hash_repo,
            collision_option,
        )
        scope = self.hash_service.build_storage_scope(current_user, guest_token)

        if not message or not message.strip():
            raise ValueError("Введите сообщение для сравнения хеш-функций.")

        normalized_message = message.strip()
        entry = compare_repo.create_entry(
            selection_key=selection_key,
            collision_method=normalized_collision_method,
            message=normalized_message,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )

        for sort_order, (hash_info, implementation) in enumerate(resolved_functions):
            result = implementation.hash_message(
                normalized_message,
                self.hash_service.TABLE_SIZE,
            )
            compare_repo.create_result(
                compare_entry_id=entry.id,
                hash_function=hash_info["value"],
                hash_label=hash_info["label"],
                hash_value=result.hash_value,
                process_note=self.trim_compare_process_note(result.process_note),
                sort_order=sort_order,
            )

        for hash_info, _implementation in resolved_functions:
            result_entries = compare_repo.get_results_for_selection(
                selection_key=selection_key,
                collision_method=normalized_collision_method,
                hash_function=hash_info["value"],
                user_id=scope.user_id,
                guest_token=scope.guest_token,
            )
            collision_method_object.rebuild_entries(
                result_entries,
                collision_context,
            )

        compare_repo.commit()

    def delete_comparison(
        self,
        compare_repo,
        hash_repo,
        current_user,
        entry_id: int,
        hash_functions: list[str],
        collision_method: str,
        guest_token: str = None,
    ):
        (
            normalized_hash_functions,
            normalized_collision_method,
            _hash_functions_info,
            resolved_functions,
            _collision_method_info,
            collision_method_object,
            collision_option,
        ) = self.ensure_compare_selection(
            hash_repo,
            hash_functions,
            collision_method,
        )
        selection_key = self.get_selection_key(normalized_hash_functions)
        collision_context = self.hash_service.build_collision_context(
            hash_repo,
            collision_option,
        )
        scope = self.hash_service.build_storage_scope(current_user, guest_token)
        entry = compare_repo.get_entry_by_id(
            entry_id=entry_id,
            selection_key=selection_key,
            collision_method=normalized_collision_method,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )

        if not entry:
            raise ValueError("Запись сравнения для удаления не найдена.")

        compare_repo.delete_entry(entry)

        for hash_info, _implementation in resolved_functions:
            result_entries = compare_repo.get_results_for_selection(
                selection_key=selection_key,
                collision_method=normalized_collision_method,
                hash_function=hash_info["value"],
                user_id=scope.user_id,
                guest_token=scope.guest_token,
            )
            collision_method_object.rebuild_entries(
                result_entries,
                collision_context,
            )

        compare_repo.commit()

    def clear_guest_entries(self, compare_repo, guest_token: str):
        if not guest_token:
            return

        compare_repo.delete_scope_entries(guest_token=guest_token)
        compare_repo.commit()
