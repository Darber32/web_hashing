import math

from App.services.hashing.interfaces import Hash_Function_Interface

MASK_32 = 0xFFFFFFFF
MASK_64 = 0xFFFFFFFFFFFFFFFF


def rotate_left_32(value: int, shift: int):
    return ((value << shift) | (value >> (32 - shift))) & MASK_32


def rotate_right_32(value: int, shift: int):
    return ((value >> shift) | (value << (32 - shift))) & MASK_32


def rotate_left_64(value: int, shift: int):
    shift = shift % 64
    return ((value << shift) | (value >> (64 - shift))) & MASK_64


class Base_Hash_Function(Hash_Function_Interface):
    implementation_note = ""

    def truncate_text(self, value: str, limit: int):
        if len(value) <= limit:
            return value

        return f"{value[:limit - 1]}..."

    def format_bytes_preview(self, value: bytes, limit: int = 24):
        if not value:
            return "пустая последовательность"

        preview = value[:limit]
        rendered = " ".join(f"{byte:02x}" for byte in preview)

        if len(value) > limit:
            return f"{rendered} ... (всего {len(value)} байт)"

        return rendered

    def calculate_padding(self, byte_length: int):
        message_bits = byte_length * 8
        zero_bits = (
            -((message_bits + 1 + self.length_field_bits) % self.block_bits)
        ) % self.block_bits
        total_bits = message_bits + 1 + zero_bits + self.length_field_bits

        return {
            "message_bits": message_bits,
            "zero_bits": zero_bits,
            "total_bits": total_bits,
            "blocks_count": total_bits // self.block_bits,
        }

    def format_words(self, names, words, word_size: int):
        width = word_size // 4
        return "; ".join(
            f"{name}=0x{word:0{width}x}" for name, word in zip(names, words)
        )


class MD5_Hash_Function(Base_Hash_Function):
    code = "md5"
    label = "MD5"
    description = (
        "Быстрый алгоритм с 128-битным дайджестом. В приложении используется "
        "самостоятельная реализация с разбором раундов и состояния регистров."
    )
    digest_bits = 128
    block_bits = 512
    length_field_bits = 64

    _SHIFTS = [
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
        5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
        4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
        6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
    ]
    _K = [
        int(abs(math.sin(index + 1)) * (2 ** 32)) & MASK_32
        for index in range(64)
    ]

    def compute_digest(self, message: str):
        message_bytes = message.encode("utf-8")
        bit_length = len(message_bytes) * 8
        padded = bytearray(message_bytes)
        padded.append(0x80)

        while len(padded) % 64 != 56:
            padded.append(0)

        padded.extend(bit_length.to_bytes(8, "little"))

        a0 = 0x67452301
        b0 = 0xEFCDAB89
        c0 = 0x98BADCFE
        d0 = 0x10325476
        block_traces = []

        for block_index in range(0, len(padded), 64):
            block = padded[block_index:block_index + 64]
            words = [
                int.from_bytes(block[offset:offset + 4], "little")
                for offset in range(0, 64, 4)
            ]

            a = a0
            b = b0
            c = c0
            d = d0
            checkpoints = {}

            for round_index in range(64):
                if round_index < 16:
                    f = (b & c) | (~b & d)
                    g = round_index
                elif round_index < 32:
                    f = (d & b) | (~d & c)
                    g = (5 * round_index + 1) % 16
                elif round_index < 48:
                    f = b ^ c ^ d
                    g = (3 * round_index + 5) % 16
                else:
                    f = c ^ (b | ~d)
                    g = (7 * round_index) % 16

                temp = d
                d = c
                c = b
                mix = (a + f + self._K[round_index] + words[g]) & MASK_32
                b = (b + rotate_left_32(mix, self._SHIFTS[round_index])) & MASK_32
                a = temp

                if round_index in (15, 31, 47, 63):
                    checkpoints[round_index + 1] = [a, b, c, d]

            a0 = (a0 + a) & MASK_32
            b0 = (b0 + b) & MASK_32
            c0 = (c0 + c) & MASK_32
            d0 = (d0 + d) & MASK_32

            block_traces.append(
                {
                    "index": (block_index // 64) + 1,
                    "first_words": words[:4],
                    "checkpoints": checkpoints,
                    "state_after": [a0, b0, c0, d0],
                }
            )

        hash_value = "".join(
            f"{byte:02x}"
            for word in [a0, b0, c0, d0]
            for byte in word.to_bytes(4, "little")
        )

        return hash_value, {
            "message_bytes": message_bytes,
            "padding": self.calculate_padding(len(message_bytes)),
            "blocks": block_traces,
            "final_state": [a0, b0, c0, d0],
        }

    def build_process_note(
        self,
        message: str,
        hash_value: str,
        trace: dict,
        primary_slot: int,
        table_size: int,
    ):
        padding = trace["padding"]
        first_block = trace["blocks"][0]
        final_state = trace["final_state"]

        note_lines = [
            f"1. Сообщение «{self.truncate_text(message, 60)}» кодируется в UTF-8 и даёт "
            f"{len(trace['message_bytes'])} байт: {self.format_bytes_preview(trace['message_bytes'])}.",
            f"2. MD5 использует блоки по 512 бит и дополняет сообщение битом 1, "
            f"{padding['zero_bits']} нулевыми битами и 64-битным полем длины. "
            f"После дополнения получается {padding['total_bits']} бит, то есть {padding['blocks_count']} блок(ов).",
            f"3. В первом блоке MD5 читает 16 слов по 32 бита в little-endian порядке. "
            f"Первые слова: {self.format_words(['M0', 'M1', 'M2', 'M3'], first_block['first_words'], 32)}.",
            "4. Начальное состояние регистров равно "
            "A=0x67452301; B=0xefcdab89; C=0x98badcfe; D=0x10325476. "
            "Далее выполняются 64 шага, разбитые на 4 раунда.",
            f"5. После 16 шагов состояние стало "
            f"{self.format_words(['A', 'B', 'C', 'D'], first_block['checkpoints'][16], 32)}; "
            f"после 32 шагов — {self.format_words(['A', 'B', 'C', 'D'], first_block['checkpoints'][32], 32)}; "
            f"после 48 шагов — {self.format_words(['A', 'B', 'C', 'D'], first_block['checkpoints'][48], 32)}; "
            f"после 64 шагов — {self.format_words(['A', 'B', 'C', 'D'], first_block['checkpoints'][64], 32)}.",
        ]

        if padding["blocks_count"] > 1:
            note_lines.append(
                f"6. После обработки всех блоков накопленное состояние регистров равно "
                f"{self.format_words(['A', 'B', 'C', 'D'], final_state, 32)}."
            )
            final_note_index = 7
        else:
            final_note_index = 6

        note_lines.append(
            f"{final_note_index}. Итоговый дайджест получается конкатенацией регистров "
            f"в little-endian виде и равен {hash_value}."
        )
        note_lines.append(
            f"{final_note_index + 1}. Для демонстрационной таблицы это значение переводится в целое число, "
            f"и первичный индекс вычисляется как int(hash, 16) mod {table_size} = {primary_slot}."
        )

        return "\n".join(note_lines)


class SHA1_Hash_Function(Base_Hash_Function):
    code = "sha1"
    label = "SHA-1"
    description = (
        "Алгоритм семейства SHA с 160-битным дайджестом. В приложении используется "
        "самостоятельная реализация с раскрытием графика слов и состояний."
    )
    digest_bits = 160
    block_bits = 512
    length_field_bits = 64

    def compute_digest(self, message: str):
        message_bytes = message.encode("utf-8")
        bit_length = len(message_bytes) * 8
        padded = bytearray(message_bytes)
        padded.append(0x80)

        while len(padded) % 64 != 56:
            padded.append(0)

        padded.extend(bit_length.to_bytes(8, "big"))

        h0 = 0x67452301
        h1 = 0xEFCDAB89
        h2 = 0x98BADCFE
        h3 = 0x10325476
        h4 = 0xC3D2E1F0
        block_traces = []

        for block_index in range(0, len(padded), 64):
            block = padded[block_index:block_index + 64]
            words = [
                int.from_bytes(block[offset:offset + 4], "big")
                for offset in range(0, 64, 4)
            ]

            for round_index in range(16, 80):
                words.append(
                    rotate_left_32(
                        words[round_index - 3]
                        ^ words[round_index - 8]
                        ^ words[round_index - 14]
                        ^ words[round_index - 16],
                        1,
                    )
                )

            a = h0
            b = h1
            c = h2
            d = h3
            e = h4
            checkpoints = {}

            for round_index in range(80):
                if round_index < 20:
                    f = (b & c) | ((~b) & d)
                    k = 0x5A827999
                elif round_index < 40:
                    f = b ^ c ^ d
                    k = 0x6ED9EBA1
                elif round_index < 60:
                    f = (b & c) | (b & d) | (c & d)
                    k = 0x8F1BBCDC
                else:
                    f = b ^ c ^ d
                    k = 0xCA62C1D6

                temp = (
                    rotate_left_32(a, 5)
                    + f
                    + e
                    + k
                    + words[round_index]
                ) & MASK_32
                e = d
                d = c
                c = rotate_left_32(b, 30)
                b = a
                a = temp

                if round_index in (19, 39, 59, 79):
                    checkpoints[round_index + 1] = [a, b, c, d, e]

            h0 = (h0 + a) & MASK_32
            h1 = (h1 + b) & MASK_32
            h2 = (h2 + c) & MASK_32
            h3 = (h3 + d) & MASK_32
            h4 = (h4 + e) & MASK_32

            block_traces.append(
                {
                    "index": (block_index // 64) + 1,
                    "first_words": words[:4],
                    "expanded_words": words[16:20],
                    "checkpoints": checkpoints,
                    "state_after": [h0, h1, h2, h3, h4],
                }
            )

        final_state = [h0, h1, h2, h3, h4]
        hash_value = "".join(f"{word:08x}" for word in final_state)

        return hash_value, {
            "message_bytes": message_bytes,
            "padding": self.calculate_padding(len(message_bytes)),
            "blocks": block_traces,
            "final_state": final_state,
        }

    def build_process_note(
        self,
        message: str,
        hash_value: str,
        trace: dict,
        primary_slot: int,
        table_size: int,
    ):
        padding = trace["padding"]
        first_block = trace["blocks"][0]
        final_state = trace["final_state"]

        note_lines = [
            f"1. Сообщение «{self.truncate_text(message, 60)}» кодируется в UTF-8 и даёт "
            f"{len(trace['message_bytes'])} байт: {self.format_bytes_preview(trace['message_bytes'])}.",
            f"2. SHA-1 работает с блоками по 512 бит и дополняет сообщение битом 1, "
            f"{padding['zero_bits']} нулевыми битами и 64-битным полем длины. "
            f"Итоговый объём после дополнения — {padding['total_bits']} бит, то есть {padding['blocks_count']} блок(ов).",
            f"3. Из первого блока извлекаются слова W0..W15 в big-endian порядке. "
            f"Первые слова: {self.format_words(['W0', 'W1', 'W2', 'W3'], first_block['first_words'], 32)}. "
            f"Затем график слов расширяется до W79; примеры W16..W19: "
            f"{self.format_words(['W16', 'W17', 'W18', 'W19'], first_block['expanded_words'], 32)}.",
            "4. Начальное состояние задаётся пятью словами "
            "A=0x67452301; B=0xefcdab89; C=0x98badcfe; D=0x10325476; E=0xc3d2e1f0. "
            "Алгоритм выполняет 80 раундов.",
            f"5. После 20 раундов состояние равно "
            f"{self.format_words(['A', 'B', 'C', 'D', 'E'], first_block['checkpoints'][20], 32)}; "
            f"после 40 — {self.format_words(['A', 'B', 'C', 'D', 'E'], first_block['checkpoints'][40], 32)}; "
            f"после 60 — {self.format_words(['A', 'B', 'C', 'D', 'E'], first_block['checkpoints'][60], 32)}; "
            f"после 80 — {self.format_words(['A', 'B', 'C', 'D', 'E'], first_block['checkpoints'][80], 32)}.",
        ]

        if padding["blocks_count"] > 1:
            note_lines.append(
                f"6. После обработки всех блоков суммарное состояние стало "
                f"{self.format_words(['H0', 'H1', 'H2', 'H3', 'H4'], final_state, 32)}."
            )
            final_note_index = 7
        else:
            final_note_index = 6

        note_lines.append(
            f"{final_note_index}. Итоговый дайджест записывается как H0||H1||H2||H3||H4 и равен {hash_value}."
        )
        note_lines.append(
            f"{final_note_index + 1}. Первичный индекс демонстрационной таблицы вычисляется как "
            f"int(hash, 16) mod {table_size} = {primary_slot}."
        )

        return "\n".join(note_lines)


class SHA256_Hash_Function(Base_Hash_Function):
    code = "sha256"
    label = "SHA-256"
    description = (
        "Современный алгоритм семейства SHA-2 с 256-битным дайджестом. "
        "В приложении реализован вручную, включая график слов и раундовые преобразования."
    )
    digest_bits = 256
    block_bits = 512
    length_field_bits = 64

    _K = [
        0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5,
        0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
        0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
        0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
        0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC,
        0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
        0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7,
        0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
        0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
        0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
        0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3,
        0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
        0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5,
        0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
        0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
        0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
    ]

    def compute_digest(self, message: str):
        message_bytes = message.encode("utf-8")
        bit_length = len(message_bytes) * 8
        padded = bytearray(message_bytes)
        padded.append(0x80)

        while len(padded) % 64 != 56:
            padded.append(0)

        padded.extend(bit_length.to_bytes(8, "big"))

        h = [
            0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
            0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
        ]
        block_traces = []

        for block_index in range(0, len(padded), 64):
            block = padded[block_index:block_index + 64]
            words = [
                int.from_bytes(block[offset:offset + 4], "big")
                for offset in range(0, 64, 4)
            ]

            for round_index in range(16, 64):
                s0 = (
                    rotate_right_32(words[round_index - 15], 7)
                    ^ rotate_right_32(words[round_index - 15], 18)
                    ^ (words[round_index - 15] >> 3)
                )
                s1 = (
                    rotate_right_32(words[round_index - 2], 17)
                    ^ rotate_right_32(words[round_index - 2], 19)
                    ^ (words[round_index - 2] >> 10)
                )
                words.append(
                    (
                        words[round_index - 16]
                        + s0
                        + words[round_index - 7]
                        + s1
                    ) & MASK_32
                )

            a, b, c, d, e, f, g, hv = h
            checkpoints = {}

            for round_index in range(64):
                s1 = (
                    rotate_right_32(e, 6)
                    ^ rotate_right_32(e, 11)
                    ^ rotate_right_32(e, 25)
                )
                ch = (e & f) ^ ((~e) & g)
                temp1 = (
                    hv + s1 + ch + self._K[round_index] + words[round_index]
                ) & MASK_32
                s0 = (
                    rotate_right_32(a, 2)
                    ^ rotate_right_32(a, 13)
                    ^ rotate_right_32(a, 22)
                )
                maj = (a & b) ^ (a & c) ^ (b & c)
                temp2 = (s0 + maj) & MASK_32

                hv = g
                g = f
                f = e
                e = (d + temp1) & MASK_32
                d = c
                c = b
                b = a
                a = (temp1 + temp2) & MASK_32

                if round_index in (15, 31, 47, 63):
                    checkpoints[round_index + 1] = [a, b, c, d, e, f, g, hv]

            h = [
                (value + delta) & MASK_32
                for value, delta in zip(h, [a, b, c, d, e, f, g, hv])
            ]

            block_traces.append(
                {
                    "index": (block_index // 64) + 1,
                    "first_words": words[:4],
                    "expanded_words": words[16:20],
                    "checkpoints": checkpoints,
                    "state_after": h[:],
                }
            )

        hash_value = "".join(f"{word:08x}" for word in h)

        return hash_value, {
            "message_bytes": message_bytes,
            "padding": self.calculate_padding(len(message_bytes)),
            "blocks": block_traces,
            "final_state": h,
        }

    def build_process_note(
        self,
        message: str,
        hash_value: str,
        trace: dict,
        primary_slot: int,
        table_size: int,
    ):
        padding = trace["padding"]
        first_block = trace["blocks"][0]
        final_state = trace["final_state"]

        note_lines = [
            f"1. Сообщение «{self.truncate_text(message, 60)}» кодируется в UTF-8 и даёт "
            f"{len(trace['message_bytes'])} байт: {self.format_bytes_preview(trace['message_bytes'])}.",
            f"2. SHA-256 также использует блоки по 512 бит. После добавления служебного бита, "
            f"{padding['zero_bits']} нулевых битов и 64-битного поля длины получается "
            f"{padding['total_bits']} бит, то есть {padding['blocks_count']} блок(ов).",
            f"3. Из первого блока берутся слова W0..W15 в big-endian порядке. "
            f"Первые слова: {self.format_words(['W0', 'W1', 'W2', 'W3'], first_block['first_words'], 32)}. "
            f"Далее график слов расширяется до W63; примеры W16..W19: "
            f"{self.format_words(['W16', 'W17', 'W18', 'W19'], first_block['expanded_words'], 32)}.",
            "4. Начальное состояние состоит из восьми 32-битных слов "
            "H0..H7, после чего выполняются 64 раунда с функциями Ch, Maj, Sigma0 и Sigma1.",
            f"5. После 16 раундов состояние равно "
            f"{self.format_words(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], first_block['checkpoints'][16], 32)}; "
            f"после 32 — {self.format_words(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], first_block['checkpoints'][32], 32)}; "
            f"после 48 — {self.format_words(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], first_block['checkpoints'][48], 32)}; "
            f"после 64 — {self.format_words(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], first_block['checkpoints'][64], 32)}.",
        ]

        if padding["blocks_count"] > 1:
            note_lines.append(
                f"6. После всех блоков накопленное состояние H0..H7 равно "
                f"{self.format_words(['H0', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7'], final_state, 32)}."
            )
            final_note_index = 7
        else:
            final_note_index = 6

        note_lines.append(
            f"{final_note_index}. Итоговый 256-битный дайджест записывается как H0||...||H7 и равен {hash_value}."
        )
        note_lines.append(
            f"{final_note_index + 1}. Первичный индекс таблицы вычисляется как "
            f"int(hash, 16) mod {table_size} = {primary_slot}."
        )

        return "\n".join(note_lines)


class MD6_Hash_Function(Base_Hash_Function):
    code = "md6"
    label = "MD6"
    description = (
        "Самостоятельная реализация стандартного MD6-256 по спецификации Rivest et al.: "
        "с 4-арным деревом, 104 раундами сжатия и усечением последних 256 бит итогового chaining value."
    )
    digest_bits = 256
    block_bits = 4096
    length_field_bits = 0
    implementation_note = (
        "В приложении используется стандартный вариант MD6-256 без ключа: L = 64, d = 256 и r = 104."
    )
    _Q = [
        0x7311C2812425CFA0,
        0x6432286434AAC8E7,
        0xB60450E9EF68B7C1,
        0xE8FB23908D9F06F1,
        0xDD2E76CBA691E5BF,
        0x0CD0D63B2C30BC41,
        0x1F8CCF6823058F8A,
        0x54E5ED5B88E3775D,
        0x4AD12AAE0A6D6031,
        0x3E7F16BB88222E0D,
        0x8AF8671D3FB50C2C,
        0x995AD1178BD25C31,
        0xC878C1DD04C4B633,
        0x3B72066C7A1552AC,
        0x0D6F3522631EFFCB,
    ]
    _DEFAULT_KEY = [0] * 8
    _WORD_COUNT = 64
    _CHUNK_WORD_COUNT = 16
    _SEQ_PAYLOAD_WORD_COUNT = 48
    _LEVEL_LIMIT = 64
    _KEY_LENGTH_BYTES = 0
    _S0 = 0x0123456789ABCDEF
    _SMASK = 0x7311C2812425CFA0
    _RIGHT_SHIFTS = [10, 5, 13, 10, 11, 12, 2, 7, 14, 15, 7, 13, 11, 7, 6, 12]
    _LEFT_SHIFTS = [11, 24, 9, 16, 15, 9, 27, 15, 6, 2, 29, 8, 15, 5, 31, 9]

    def _default_rounds(self):
        return 40 + (self.digest_bits // 4)

    def _pack_control_word(self, rounds: int, is_final: bool, padding_bits: int):
        return (
            ((rounds & 0xFFF) << 48)
            | ((self._LEVEL_LIMIT & 0xFF) << 40)
            | (((1 if is_final else 0) & 0xF) << 36)
            | ((padding_bits & 0xFFFF) << 20)
            | ((self._KEY_LENGTH_BYTES & 0xFF) << 12)
            | (self.digest_bits & 0xFFF)
        ) & MASK_64

    def _bytes_to_words(self, value: bytes):
        if not value:
            return []

        padded = value
        if len(padded) % 8:
            padded += b"\x00" * (8 - (len(padded) % 8))

        return [
            int.from_bytes(padded[index:index + 8], "big")
            for index in range(0, len(padded), 8)
        ]

    def _build_digest_from_chunk(self, chunk_words):
        chunk_bytes = b"".join(word.to_bytes(8, "big") for word in chunk_words)
        digest_bytes = chunk_bytes[-(self.digest_bits // 8):]
        digest_words = [
            int.from_bytes(digest_bytes[index:index + 8], "big")
            for index in range(0, len(digest_bytes), 8)
        ]
        return digest_bytes.hex(), digest_words

    def _compress(
        self,
        block_words,
        level: int,
        index: int,
        rounds: int,
        is_final: bool,
        padding_bits: int,
        capture_trace: bool,
    ):
        unique_node_id = ((level & 0xFF) << 56) | index
        control_word = self._pack_control_word(rounds, is_final, padding_bits)
        input_words = self._Q + self._DEFAULT_KEY + [unique_node_id, control_word] + block_words

        state = input_words[:]
        round_constant = self._S0
        checkpoints = {}
        checkpoint_rounds = {1, max(1, rounds // 2), rounds}

        for step in range(rounds * self._CHUNK_WORD_COUNT):
            shift_index = step % self._CHUNK_WORD_COUNT
            raw_word = round_constant ^ state[-89] ^ state[-17]
            raw_word ^= (state[-18] & state[-21]) ^ (state[-31] & state[-67])
            raw_word &= MASK_64

            diffused_word = raw_word ^ (raw_word >> self._RIGHT_SHIFTS[shift_index])
            state.append(
                (
                    diffused_word
                    ^ ((diffused_word << self._LEFT_SHIFTS[shift_index]) & MASK_64)
                ) & MASK_64
            )

            if shift_index == self._CHUNK_WORD_COUNT - 1:
                round_number = (step // self._CHUNK_WORD_COUNT) + 1
                if capture_trace and round_number in checkpoint_rounds:
                    checkpoints[round_number] = state[-4:]

                round_constant = (
                    rotate_left_64(round_constant, 1) ^ (round_constant & self._SMASK)
                ) & MASK_64

        output_words = state[-self._CHUNK_WORD_COUNT:]
        trace = None
        if capture_trace:
            trace = {
                "level": level,
                "index": index,
                "padding_bits": padding_bits,
                "is_final": is_final,
                "unique_node_id": unique_node_id,
                "control_word": control_word,
                "input_preview": block_words[:4],
                "output_preview": output_words[:4],
                "digest_tail_preview": output_words[-4:],
                "checkpoints": checkpoints,
            }

        return output_words, trace

    def _run_par_level(self, level_words, bit_length: int, level: int, rounds: int, trace: dict):
        block_count = max(1, (bit_length + self.block_bits - 1) // self.block_bits)
        total_words = block_count * self._WORD_COUNT
        padded_words = level_words + [0] * (total_words - len(level_words))
        last_padding_bits = (block_count * self.block_bits) - bit_length
        next_level_words = []

        for block_index in range(block_count):
            capture_trace = trace["first_compression"] is None
            block_words = padded_words[
                block_index * self._WORD_COUNT:(block_index + 1) * self._WORD_COUNT
            ]
            output_words, compression_trace = self._compress(
                block_words=block_words,
                level=level,
                index=block_index,
                rounds=rounds,
                is_final=block_count == 1,
                padding_bits=last_padding_bits if block_index == block_count - 1 else 0,
                capture_trace=capture_trace,
            )
            next_level_words.extend(output_words)
            if compression_trace is not None:
                trace["first_compression"] = compression_trace

        trace["total_compressions"] += block_count
        return next_level_words, block_count * self._CHUNK_WORD_COUNT * 64, {
            "mode": "PAR",
            "level": level,
            "input_bits": bit_length,
            "block_count": block_count,
            "last_padding_bits": last_padding_bits,
        }

    def _run_seq_level(self, level_words, bit_length: int, level: int, rounds: int, trace: dict):
        payload_bits = self._SEQ_PAYLOAD_WORD_COUNT * 64
        block_count = max(1, (bit_length + payload_bits - 1) // payload_bits)
        total_words = block_count * self._SEQ_PAYLOAD_WORD_COUNT
        padded_words = level_words + [0] * (total_words - len(level_words))
        last_padding_bits = (block_count * payload_bits) - bit_length
        chaining_value = [0] * self._CHUNK_WORD_COUNT

        for block_index in range(block_count):
            payload = padded_words[
                block_index * self._SEQ_PAYLOAD_WORD_COUNT:
                (block_index + 1) * self._SEQ_PAYLOAD_WORD_COUNT
            ]
            capture_trace = trace["first_compression"] is None
            chaining_value, compression_trace = self._compress(
                block_words=chaining_value + payload,
                level=level,
                index=block_index,
                rounds=rounds,
                is_final=block_index == block_count - 1,
                padding_bits=last_padding_bits if block_index == block_count - 1 else 0,
                capture_trace=capture_trace,
            )
            if compression_trace is not None:
                trace["first_compression"] = compression_trace

        trace["total_compressions"] += block_count
        return chaining_value, {
            "mode": "SEQ",
            "level": level,
            "input_bits": bit_length,
            "block_count": block_count,
            "last_padding_bits": last_padding_bits,
        }

    def compute_digest(self, message: str):
        message_bytes = message.encode("utf-8")
        current_words = self._bytes_to_words(message_bytes)
        current_bits = len(message_bytes) * 8
        rounds = self._default_rounds()
        trace = {
            "message_bytes": message_bytes,
            "rounds": rounds,
            "levels": [],
            "first_compression": None,
            "total_compressions": 0,
            "mode_parameter": self._LEVEL_LIMIT,
        }

        level = 0
        while True:
            level += 1
            if level == self._LEVEL_LIMIT + 1:
                final_chunk, level_trace = self._run_seq_level(
                    level_words=current_words,
                    bit_length=current_bits,
                    level=level,
                    rounds=rounds,
                    trace=trace,
                )
                trace["levels"].append(level_trace)
                hash_value, digest_words = self._build_digest_from_chunk(final_chunk)
                trace["final_chunk"] = final_chunk
                trace["digest_words"] = digest_words
                return hash_value, trace

            current_words, current_bits, level_trace = self._run_par_level(
                level_words=current_words,
                bit_length=current_bits,
                level=level,
                rounds=rounds,
                trace=trace,
            )
            trace["levels"].append(level_trace)

            if current_bits == self._CHUNK_WORD_COUNT * 64:
                hash_value, digest_words = self._build_digest_from_chunk(current_words)
                trace["final_chunk"] = current_words
                trace["digest_words"] = digest_words
                return hash_value, trace

    def build_process_note(
        self,
        message: str,
        hash_value: str,
        trace: dict,
        primary_slot: int,
        table_size: int,
    ):
        first_level = trace["levels"][0]
        final_level = trace["levels"][-1]
        first_compression = trace["first_compression"]
        digest_words = trace["digest_words"]
        checkpoint_note = "; ".join(
            f"после раунда {round_number} хвост окна равен "
            f"{self.format_words(['T0', 'T1', 'T2', 'T3'], checkpoint, 64)}"
            for round_number, checkpoint in sorted(first_compression["checkpoints"].items())
        )

        note_lines = [
            f"1. Сообщение «{self.truncate_text(message, 60)}» кодируется в UTF-8 и даёт "
            f"{len(trace['message_bytes'])} байт: {self.format_bytes_preview(trace['message_bytes'])}.",
            f"2. Стандартный MD6-256 использует d = {self.digest_bits}, L = {trace['mode_parameter']} и "
            f"r = {trace['rounds']} раунда. На первом уровне дерево разбивает вход на блоки по 4096 бит и "
            f"сжимает каждый в chaining value длиной 1024 бита.",
            f"3. На уровне {first_level['level']} было обработано {first_level['block_count']} блок(ов); "
            f"в последний блок добавлено {first_level['last_padding_bits']} нулевых бит. "
            f"Первая компрессия работала с U = 0x{first_compression['unique_node_id']:016x} и "
            f"V = 0x{first_compression['control_word']:016x}.",
            f"4. Вход первого блока B начинается словами "
            f"{self.format_words(['B0', 'B1', 'B2', 'B3'], first_compression['input_preview'], 64)}. "
            f"Компрессия строит массив A из Q || K || U || V || B и затем выполняет "
            f"{trace['rounds'] * self._CHUNK_WORD_COUNT} шагов по формуле "
            f"x = S xor A[i-89] xor A[i-17] xor (A[i-18] & A[i-21]) xor (A[i-31] & A[i-67]), "
            f"после чего применяет xorshift с r_i и l_i.",
            f"5. Контрольные точки первой компрессии: {checkpoint_note}.",
            f"6. Первая компрессия выдаёт chaining value, начинающееся словами "
            f"{self.format_words(['C0', 'C1', 'C2', 'C3'], first_compression['output_preview'], 64)}. "
            f"Финальный уровень {final_level['level']} работал в режиме {final_level['mode']} "
            f"и суммарно по всему дереву выполнено {trace['total_compressions']} вызов(ов) компрессии.",
            f"7. Итоговый digest MD6-256 — это последние 256 бит финального chaining value, то есть слова "
            f"{self.format_words(['D0', 'D1', 'D2', 'D3'], digest_words, 64)}.",
            f"8. Шестнадцатеричный вид дайджеста равен {hash_value}. Первичный индекс таблицы вычисляется как "
            f"int(hash, 16) mod {table_size} = {primary_slot}.",
            f"9. {self.implementation_note}",
        ]

        return "\n".join(note_lines)
