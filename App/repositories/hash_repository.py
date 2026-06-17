from sqlalchemy.orm import Session

from App.models.demo import DemoEntry
from App.models.hash_catalog import CollisionMethodOption, HashFunctionOption


class Hash_Repository:

    def __init__(self, db: Session):
        self.db = db

    def get_enabled_hash_functions(self):
        return (
            self.db.query(HashFunctionOption)
            .filter(HashFunctionOption.is_enabled.is_(True))
            .order_by(HashFunctionOption.sort_order.asc(), HashFunctionOption.id.asc())
            .all()
        )

    def get_hash_functions(self):
        return (
            self.db.query(HashFunctionOption)
            .order_by(HashFunctionOption.sort_order.asc(), HashFunctionOption.id.asc())
            .all()
        )

    def get_hash_function_by_id(self, option_id: int):
        return (
            self.db.query(HashFunctionOption)
            .filter(HashFunctionOption.id == option_id)
            .first()
        )

    def get_enabled_hash_function(self, code: str):
        return (
            self.db.query(HashFunctionOption)
            .filter(
                HashFunctionOption.code == code,
                HashFunctionOption.is_enabled.is_(True),
            )
            .first()
        )

    def get_hash_function_by_code(self, code: str):
        return (
            self.db.query(HashFunctionOption)
            .filter(HashFunctionOption.code == code)
            .first()
        )

    def get_enabled_collision_methods(self):
        return (
            self.db.query(CollisionMethodOption)
            .filter(CollisionMethodOption.is_enabled.is_(True))
            .order_by(
                CollisionMethodOption.sort_order.asc(),
                CollisionMethodOption.id.asc(),
            )
            .all()
        )

    def get_collision_methods(self):
        return (
            self.db.query(CollisionMethodOption)
            .order_by(
                CollisionMethodOption.sort_order.asc(),
                CollisionMethodOption.id.asc(),
            )
            .all()
        )

    def get_collision_method_by_id(self, option_id: int):
        return (
            self.db.query(CollisionMethodOption)
            .filter(CollisionMethodOption.id == option_id)
            .first()
        )

    def get_enabled_collision_method(self, code: str):
        return (
            self.db.query(CollisionMethodOption)
            .filter(
                CollisionMethodOption.code == code,
                CollisionMethodOption.is_enabled.is_(True),
            )
            .first()
        )

    def get_collision_method_by_code(self, code: str):
        return (
            self.db.query(CollisionMethodOption)
            .filter(CollisionMethodOption.code == code)
            .first()
        )

    def _apply_demo_scope_filters(self, query, user_id: int = None, guest_token: str = None):
        if user_id is not None:
            return query.filter(DemoEntry.user_id == user_id)

        if guest_token:
            return query.filter(DemoEntry.guest_token == guest_token)

        return query.filter(DemoEntry.id.is_(None))

    def get_entries(
        self,
        hash_function: str,
        collision_method: str,
        user_id: int = None,
        guest_token: str = None,
    ):
        query = self._apply_demo_scope_filters(
            self.db.query(DemoEntry),
            user_id=user_id,
            guest_token=guest_token,
        )

        return (
            query
            .filter(
                DemoEntry.hash_function == hash_function,
                DemoEntry.collision_method == collision_method,
            )
            .order_by(DemoEntry.created_at.asc(), DemoEntry.id.asc())
            .all()
        )

    def get_entry_by_id(
        self,
        entry_id: int,
        user_id: int = None,
        guest_token: str = None,
    ):
        query = self._apply_demo_scope_filters(
            self.db.query(DemoEntry),
            user_id=user_id,
            guest_token=guest_token,
        )
        return query.filter(DemoEntry.id == entry_id).first()

    def create_entry(
        self,
        hash_function: str,
        collision_method: str,
        message: str,
        hash_value: str,
        process_note: str,
        user_id: int = None,
        guest_token: str = None,
    ):
        if user_id is None and not guest_token:
            raise ValueError("Не удалось определить владельца демонстрационной записи.")

        entry = DemoEntry(
            user_id=user_id,
            guest_token=guest_token,
            hash_function=hash_function,
            collision_method=collision_method,
            message=message,
            hash_value=hash_value,
            process_note=process_note,
            collision_note="",
            initial_slot=0,
            final_slot=0,
            collision_detected=False,
            chain_position=None,
            probe_count=0,
            step_size=None,
        )

        self.db.add(entry)
        self.db.flush()
        self.db.refresh(entry)

        return entry

    def delete_entry(self, entry):
        self.db.delete(entry)
        self.db.flush()

    def delete_scope_entries(self, user_id: int = None, guest_token: str = None):
        query = self._apply_demo_scope_filters(
            self.db.query(DemoEntry),
            user_id=user_id,
            guest_token=guest_token,
        )
        query.delete(synchronize_session=False)
        self.db.flush()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
