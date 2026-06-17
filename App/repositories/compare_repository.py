from sqlalchemy.orm import Session, joinedload, selectinload

from App.models.compare import CompareEntry, CompareResult


class Compare_Repository:

    def __init__(self, db: Session):
        self.db = db

    def _apply_scope_filters(self, query, user_id: int = None, guest_token: str = None):
        if user_id is not None:
            return query.filter(CompareEntry.user_id == user_id)

        if guest_token:
            return query.filter(CompareEntry.guest_token == guest_token)

        return query.filter(CompareEntry.id.is_(None))

    def get_entries(
        self,
        selection_key: str,
        collision_method: str,
        user_id: int = None,
        guest_token: str = None,
    ):
        query = self._apply_scope_filters(
            self.db.query(CompareEntry),
            user_id=user_id,
            guest_token=guest_token,
        )

        return (
            query
            .options(selectinload(CompareEntry.results))
            .filter(
                CompareEntry.selection_key == selection_key,
                CompareEntry.collision_method == collision_method,
            )
            .order_by(CompareEntry.created_at.asc(), CompareEntry.id.asc())
            .all()
        )

    def get_entry_by_id(
        self,
        entry_id: int,
        selection_key: str,
        collision_method: str,
        user_id: int = None,
        guest_token: str = None,
    ):
        query = self._apply_scope_filters(
            self.db.query(CompareEntry),
            user_id=user_id,
            guest_token=guest_token,
        )

        return (
            query
            .options(selectinload(CompareEntry.results))
            .filter(
                CompareEntry.id == entry_id,
                CompareEntry.selection_key == selection_key,
                CompareEntry.collision_method == collision_method,
            )
            .first()
        )

    def create_entry(
        self,
        selection_key: str,
        collision_method: str,
        message: str,
        user_id: int = None,
        guest_token: str = None,
    ):
        if user_id is None and not guest_token:
            raise ValueError("Не удалось определить владельца записи сравнения.")

        entry = CompareEntry(
            user_id=user_id,
            guest_token=guest_token,
            selection_key=selection_key,
            collision_method=collision_method,
            message=message,
        )
        self.db.add(entry)
        self.db.flush()
        self.db.refresh(entry)
        return entry

    def create_result(
        self,
        compare_entry_id: int,
        hash_function: str,
        hash_label: str,
        hash_value: str,
        process_note: str,
        sort_order: int,
    ):
        result = CompareResult(
            compare_entry_id=compare_entry_id,
            hash_function=hash_function,
            hash_label=hash_label,
            hash_value=hash_value,
            process_note=process_note,
            collision_note="",
            initial_slot=0,
            final_slot=0,
            collision_detected=False,
            chain_position=None,
            probe_count=0,
            step_size=None,
            sort_order=sort_order,
        )
        self.db.add(result)
        self.db.flush()
        self.db.refresh(result)
        return result

    def get_results_for_selection(
        self,
        selection_key: str,
        collision_method: str,
        hash_function: str,
        user_id: int = None,
        guest_token: str = None,
    ):
        query = self._apply_scope_filters(
            self.db.query(CompareEntry),
            user_id=user_id,
            guest_token=guest_token,
        )

        return (
            self.db.query(CompareResult)
            .join(CompareEntry, CompareResult.compare_entry_id == CompareEntry.id)
            .options(joinedload(CompareResult.entry))
            .filter(
                CompareEntry.id.in_(
                    query
                    .filter(
                        CompareEntry.selection_key == selection_key,
                        CompareEntry.collision_method == collision_method,
                    )
                    .with_entities(CompareEntry.id)
                ),
                CompareResult.hash_function == hash_function,
            )
            .order_by(CompareEntry.created_at.asc(), CompareEntry.id.asc())
            .all()
        )

    def delete_entry(self, entry):
        self.db.delete(entry)
        self.db.flush()

    def delete_scope_entries(self, user_id: int = None, guest_token: str = None):
        query = self._apply_scope_filters(
            self.db.query(CompareEntry),
            user_id=user_id,
            guest_token=guest_token,
        )
        query.delete(synchronize_session=False)
        self.db.flush()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
