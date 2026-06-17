from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Hash_Computation_Result:
    hash_value: str
    primary_slot: int
    process_note: str


@dataclass
class Collision_Resolution_Context:
    table_size: int
    step_hash_function: "Hash_Function_Interface"


class Hash_Function_Interface(ABC):
    code: str
    label: str
    description: str
    digest_bits: int
    block_bits: int
    length_field_bits: int
    implementation_note: str

    @abstractmethod
    def compute_digest(self, message: str) -> tuple[str, dict[str, Any]]:
        pass

    @abstractmethod
    def build_process_note(
        self,
        message: str,
        hash_value: str,
        trace: dict[str, Any],
        primary_slot: int,
        table_size: int,
    ) -> str:
        pass

    def hash_message(self, message: str, table_size: int) -> Hash_Computation_Result:
        hash_value, trace = self.compute_digest(message)
        primary_slot = int(hash_value, 16) % table_size
        process_note = self.build_process_note(
            message=message,
            hash_value=hash_value,
            trace=trace,
            primary_slot=primary_slot,
            table_size=table_size,
        )

        return Hash_Computation_Result(
            hash_value=hash_value,
            primary_slot=primary_slot,
            process_note=process_note,
        )

    def digest_text(self, message: str) -> str:
        hash_value, _ = self.compute_digest(message)
        return hash_value


class Collision_Resolution_Interface(ABC):
    code: str
    label: str
    description: str

    @abstractmethod
    def rebuild_entries(self, entries, context: Collision_Resolution_Context):
        pass

    @abstractmethod
    def build_table_state(self, entries, table_size: int):
        pass
