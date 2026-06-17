from dataclasses import dataclass
from importlib import import_module

from fastapi import Request
from fastapi.templating import Jinja2Templates

from App.services.hashing.interfaces import (
    Collision_Resolution_Context,
    Collision_Resolution_Interface,
    Hash_Function_Interface,
)

templates = Jinja2Templates(directory="App/templates")


@dataclass(frozen=True)
class DemoStorageScope:
    user_id: int = None
    guest_token: str = None
    is_guest: bool = False


class Hash_Service:
    TABLE_SIZE = 30

    def __init__(self):
        self._implementation_cache = {}

    def build_storage_scope(self, current_user, guest_token: str = None):
        if getattr(current_user, "role", None) == "guest":
            if not guest_token:
                raise ValueError(
                    "Для гостевого режима не создан временный ключ демонстрации."
                )

            return DemoStorageScope(
                user_id=None,
                guest_token=guest_token,
                is_guest=True,
            )

        user_id = getattr(current_user, "id", None)

        if user_id is None:
            raise ValueError(
                "Не удалось определить пользователя для сохранения результатов демонстрации."
            )

        return DemoStorageScope(
            user_id=user_id,
            guest_token=None,
            is_guest=False,
        )

    def _load_implementation(self, implementation_path: str, interface_type):
        if not implementation_path:
            raise ValueError("Для выбранной записи в справочнике не указан путь к реализации.")

        if implementation_path in self._implementation_cache:
            implementation = self._implementation_cache[implementation_path]
        else:
            try:
                module_path, class_name = implementation_path.rsplit(".", 1)
                module = import_module(module_path)
                implementation_class = getattr(module, class_name)
            except (ValueError, ImportError, AttributeError) as exc:
                raise ValueError(
                    f"Не удалось загрузить реализацию {implementation_path}."
                ) from exc

            implementation = implementation_class()
            self._implementation_cache[implementation_path] = implementation

        if not isinstance(implementation, interface_type):
            raise ValueError(
                f"Реализация {implementation_path} не поддерживает ожидаемый интерфейс."
            )

        return implementation

    def _resolve_hash_implementation(self, option):
        return self._load_implementation(
            option.implementation_path,
            Hash_Function_Interface,
        )

    def _resolve_collision_implementation(self, option):
        return self._load_implementation(
            option.implementation_path,
            Collision_Resolution_Interface,
        )

    def serialize_hash_option(self, option, implementation):
        return {
            "value": option.code,
            "label": option.label,
            "description": option.description,
            "digest_bits": implementation.digest_bits,
        }

    def serialize_collision_option(self, option):
        return {
            "value": option.code,
            "label": option.label,
            "description": option.description,
        }

    def get_hash_function_choices(self, repo):
        choices = []

        for option in repo.get_enabled_hash_functions():
            try:
                implementation = self._resolve_hash_implementation(option)
            except ValueError:
                continue

            choices.append(self.serialize_hash_option(option, implementation))

        return choices

    def get_collision_method_choices(self, repo):
        choices = []

        for option in repo.get_enabled_collision_methods():
            try:
                self._resolve_collision_implementation(option)

                if option.step_hash_function_code:
                    step_hash_option = repo.get_hash_function_by_code(
                        option.step_hash_function_code
                    )

                    if not step_hash_option:
                        continue

                    self._resolve_hash_implementation(step_hash_option)
            except ValueError:
                continue

            choices.append(self.serialize_collision_option(option))

        return choices

    def get_default_hash_function_code(self, repo):
        choices = self.get_hash_function_choices(repo)
        return choices[0]["value"] if choices else None

    def get_default_collision_method_code(self, repo):
        choices = self.get_collision_method_choices(repo)
        return choices[0]["value"] if choices else None

    def resolve_hash_function(self, repo, hash_function: str):
        hash_option = repo.get_enabled_hash_function(hash_function)

        if not hash_option:
            raise ValueError(
                "Выбранная хеш-функция недоступна. Проверьте настройки доступных функций."
            )

        hash_implementation = self._resolve_hash_implementation(hash_option)
        return self.serialize_hash_option(hash_option, hash_implementation), hash_implementation

    def resolve_collision_method(self, repo, collision_method: str):
        collision_option = repo.get_enabled_collision_method(collision_method)

        if not collision_option:
            raise ValueError(
                "Выбранный метод разрешения коллизий недоступен. Проверьте настройки доступных методов."
            )

        collision_implementation = self._resolve_collision_implementation(
            collision_option
        )
        return (
            self.serialize_collision_option(collision_option),
            collision_implementation,
            collision_option,
        )

    def normalize_selection(
        self,
        repo,
        hash_function: str = None,
        collision_method: str = None,
    ):
        available_hash_codes = {
            item["value"] for item in self.get_hash_function_choices(repo)
        }
        available_collision_codes = {
            item["value"] for item in self.get_collision_method_choices(repo)
        }

        if hash_function not in available_hash_codes:
            hash_function = self.get_default_hash_function_code(repo)

        if collision_method not in available_collision_codes:
            collision_method = self.get_default_collision_method_code(repo)

        return hash_function, collision_method

    def build_collision_context(self, repo, collision_option):
        step_hash_function = None

        if collision_option.step_hash_function_code:
            step_hash_option = repo.get_hash_function_by_code(
                collision_option.step_hash_function_code
            )

            if not step_hash_option:
                raise ValueError(
                    "Для метода разрешения коллизий не найдена вторичная хеш-функция."
                )

            step_hash_function = self._resolve_hash_implementation(step_hash_option)

        return Collision_Resolution_Context(
            table_size=self.TABLE_SIZE,
            step_hash_function=step_hash_function,
        )

    def resolve_selection(self, repo, hash_function: str, collision_method: str):
        hash_option = repo.get_enabled_hash_function(hash_function)
        collision_option = repo.get_enabled_collision_method(collision_method)

        if not hash_option:
            raise ValueError(
                "Выбранная хеш-функция недоступна. Проверьте настройки доступных функций."
            )

        if not collision_option:
            raise ValueError(
                "Выбранный метод разрешения коллизий недоступен. Проверьте настройки доступных методов."
            )

        hash_implementation = self._resolve_hash_implementation(hash_option)
        collision_implementation = self._resolve_collision_implementation(
            collision_option
        )

        return (
            self.serialize_hash_option(hash_option, hash_implementation),
            hash_implementation,
            self.serialize_collision_option(collision_option),
            collision_implementation,
            collision_option,
        )

    def render_demo_selection_page(
        self,
        request: Request,
        current_user,
        repo,
        error: str = None,
        selected_hash_function: str = None,
        selected_collision_method: str = None,
        is_guest_demo: bool = False,
    ):
        hash_functions = self.get_hash_function_choices(repo)
        collision_methods = self.get_collision_method_choices(repo)
        selected_hash_function, selected_collision_method = self.normalize_selection(
            repo,
            selected_hash_function,
            selected_collision_method,
        )

        return templates.TemplateResponse(
            "demo.html",
            {
                "request": request,
                "current_user": current_user,
                "hash_functions": hash_functions,
                "collision_methods": collision_methods,
                "selected_hash_function": selected_hash_function,
                "selected_collision_method": selected_collision_method,
                "error": error,
                "has_available_choices": bool(hash_functions and collision_methods),
                "is_guest_demo": is_guest_demo,
            },
        )

    def render_demo_workspace(
        self,
        request: Request,
        current_user,
        repo,
        hash_function: str,
        collision_method: str,
        entries,
        error: str = None,
        success: str = None,
        is_guest_demo: bool = False,
    ):
        (
            hash_function_info,
            _hash_function,
            collision_method_info,
            collision_method_object,
            _collision_option,
        ) = self.resolve_selection(repo, hash_function, collision_method)

        return templates.TemplateResponse(
            "demo_workspace.html",
            {
                "request": request,
                "current_user": current_user,
                "hash_function": hash_function,
                "collision_method": collision_method,
                "hash_function_info": hash_function_info,
                "collision_method_info": collision_method_info,
                "entries": entries,
                "table_size": self.TABLE_SIZE,
                "table_state": collision_method_object.build_table_state(
                    entries,
                    self.TABLE_SIZE,
                ),
                "error": error,
                "success": success,
                "is_guest_demo": is_guest_demo,
            },
        )

    def add_message(
        self,
        repo,
        current_user,
        hash_function: str,
        collision_method: str,
        message: str,
        guest_token: str = None,
    ):
        (
            _hash_option,
            hash_function_object,
            _collision_option_data,
            collision_method_object,
            collision_option,
        ) = self.resolve_selection(repo, hash_function, collision_method)
        scope = self.build_storage_scope(current_user, guest_token)

        if not message or not message.strip():
            raise ValueError("Введите сообщение для демонстрации.")

        normalized_message = message.strip()
        result = hash_function_object.hash_message(
            normalized_message,
            self.TABLE_SIZE,
        )

        repo.create_entry(
            hash_function=hash_function,
            collision_method=collision_method,
            message=normalized_message,
            hash_value=result.hash_value,
            process_note=result.process_note,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )

        entries = repo.get_entries(
            hash_function,
            collision_method,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )
        collision_method_object.rebuild_entries(
            entries,
            self.build_collision_context(repo, collision_option),
        )
        repo.commit()

    def delete_message(
        self,
        repo,
        entry_id: int,
        current_user,
        hash_function: str,
        collision_method: str,
        guest_token: str = None,
    ):
        (
            _hash_option,
            _hash_function_object,
            _collision_option_data,
            collision_method_object,
            collision_option,
        ) = self.resolve_selection(repo, hash_function, collision_method)
        scope = self.build_storage_scope(current_user, guest_token)

        entry = repo.get_entry_by_id(
            entry_id,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )

        if not entry:
            raise ValueError("Запись для удаления не найдена.")

        if (
            entry.hash_function != hash_function
            or entry.collision_method != collision_method
        ):
            raise ValueError("Запись не относится к выбранной демонстрации.")

        repo.delete_entry(entry)
        entries = repo.get_entries(
            hash_function,
            collision_method,
            user_id=scope.user_id,
            guest_token=scope.guest_token,
        )
        collision_method_object.rebuild_entries(
            entries,
            self.build_collision_context(repo, collision_option),
        )
        repo.commit()

    def clear_guest_entries(self, repo, guest_token: str):
        if not guest_token:
            return

        repo.delete_scope_entries(guest_token=guest_token)
        repo.commit()
