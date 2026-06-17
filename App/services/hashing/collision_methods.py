import math

from App.services.hashing.interfaces import (
    Collision_Resolution_Context,
    Collision_Resolution_Interface,
)


def truncate_text(value: str, limit: int):
    if len(value) <= limit:
        return value

    return f"{value[:limit - 1]}..."


class Chaining_Collision_Method(Collision_Resolution_Interface):
    code = "chaining"
    label = "Цепочки"
    description = (
        "Каждая корзина хранит список записей. При коллизии новая запись остаётся "
        "в той же корзине и добавляется в конец цепочки."
    )

    def rebuild_entries(self, entries, context: Collision_Resolution_Context):
        buckets = {index: [] for index in range(context.table_size)}

        for entry in entries:
            initial_slot = int(entry.hash_value, 16) % context.table_size
            bucket_entries = buckets[initial_slot]
            chain_position = len(bucket_entries)
            collision_detected = chain_position > 0

            entry.initial_slot = initial_slot
            entry.final_slot = initial_slot
            entry.chain_position = chain_position
            entry.probe_count = chain_position
            entry.step_size = None
            entry.collision_detected = collision_detected
            entry.collision_note = self.build_collision_note(
                bucket=initial_slot,
                existing_entries=bucket_entries,
                chain_position=chain_position,
                collision_detected=collision_detected,
            )

            bucket_entries.append(entry)

    def build_table_state(self, entries, table_size: int):
        return [
            {
                "index": bucket_index,
                "items": [
                    entry for entry in entries if entry.final_slot == bucket_index
                ],
            }
            for bucket_index in range(table_size)
        ]

    def build_collision_note(
        self,
        bucket: int,
        existing_entries,
        chain_position: int,
        collision_detected: bool,
    ):
        if not collision_detected:
            return (
                f"1. Первичный индекс указал на корзину {bucket}.\n"
                f"2. Корзина оказалась пустой, поэтому запись можно было сохранить без дополнительного разрешения коллизии.\n"
                f"3. Метод цепочек просто оставил сообщение в этой корзине как первый элемент связанного списка."
            )

        conflicting_messages = ", ".join(
            f"«{truncate_text(item.message, 24)}»" for item in existing_entries
        )

        return (
            f"1. Первичный индекс снова указал на корзину {bucket}, где уже находились сообщения: {conflicting_messages}.\n"
            f"2. Метод цепочек не ищет новую ячейку. Вместо этого все записи с одинаковым индексом хранятся в одной корзине и образуют последовательность.\n"
            f"3. Новая запись добавлена в конец цепочки на позицию {chain_position + 1}. "
            f"При поиске по этой корзине потребуется последовательно сравнить до {chain_position + 1} элементов."
        )


class Double_Hashing_Collision_Method(Collision_Resolution_Interface):
    code = "double_hashing"
    label = "Двойное хеширование"
    description = (
        "При коллизии используется второй хеш, определяющий шаг повторного пробирования "
        "и позволяющий найти следующую свободную ячейку."
    )

    def rebuild_entries(self, entries, context: Collision_Resolution_Context):
        table = {index: None for index in range(context.table_size)}

        for entry in entries:
            initial_slot = int(entry.hash_value, 16) % context.table_size
            step_size = self.secondary_step(entry.hash_value, context)
            slot = initial_slot
            probes = 0
            visited_slots = []

            while table[slot] is not None:
                visited_slots.append((slot, table[slot].message))
                probes += 1

                if probes >= context.table_size:
                    raise ValueError(
                        "Таблица демонстрации заполнена. Удалите одну из записей или "
                        "выберите метод цепочек."
                    )

                slot = (slot + step_size) % context.table_size

            collision_detected = probes > 0

            entry.initial_slot = initial_slot
            entry.final_slot = slot
            entry.chain_position = None
            entry.probe_count = probes
            entry.step_size = step_size
            entry.collision_detected = collision_detected
            entry.collision_note = self.build_collision_note(
                table_size=context.table_size,
                initial_slot=initial_slot,
                final_slot=slot,
                step_size=step_size,
                probes=probes,
                collision_detected=collision_detected,
                visited_slots=visited_slots,
            )

            table[slot] = entry

    def build_table_state(self, entries, table_size: int):
        slot_map = {entry.final_slot: entry for entry in entries}
        return [
            {
                "index": slot_index,
                "entry": slot_map.get(slot_index),
            }
            for slot_index in range(table_size)
        ]

    def secondary_step(self, hash_value: str, context: Collision_Resolution_Context):
        if context.step_hash_function is None:
            raise ValueError(
                "Для метода двойного хеширования не задана вторичная хеш-функция."
            )

        step_hash_value = context.step_hash_function.digest_text(hash_value)
        step = (int(step_hash_value, 16) % (context.table_size - 1)) + 1

        while math.gcd(step, context.table_size) != 1:
            step = (step % (context.table_size - 1)) + 1

        return step

    def build_collision_note(
        self,
        table_size: int,
        initial_slot: int,
        final_slot: int,
        step_size: int,
        probes: int,
        collision_detected: bool,
        visited_slots,
    ):
        if not collision_detected:
            return (
                f"1. Первичный индекс равен {initial_slot}, и соответствующая ячейка оказалась свободной.\n"
                f"2. Второй шаг пробирования вычислен как {step_size}, но он не понадобился, потому что коллизия не возникла.\n"
                f"3. Сообщение сразу сохранено в ячейке {final_slot}."
            )

        visited_description = " -> ".join(
            f"{slot} (занята сообщением «{truncate_text(message, 24)}»)"
            for slot, message in visited_slots
        )
        if visited_description:
            visited_description += f" -> {final_slot} (свободна)"
        else:
            visited_description = f"{final_slot} (свободна)"

        return (
            f"1. Первичный индекс равен {initial_slot}, но ячейка уже была занята.\n"
            f"2. Для разрешения коллизии вычислен второй шаг {step_size}. Он получается из повторного хеширования строкового вида текущего дайджеста и корректируется так, чтобы быть взаимно простым с размером таблицы {table_size}.\n"
            f"3. Последовательность пробирования выглядит так: {visited_description}.\n"
            f"4. После {probes} повторных проб запись помещена в ячейку {final_slot}. Именно этот маршрут и является фактическим разрешением коллизии."
        )
