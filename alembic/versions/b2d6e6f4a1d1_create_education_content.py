"""create education content

Revision ID: b2d6e6f4a1d1
Revises: 005ff59dbcf0
Create Date: 2026-04-20 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2d6e6f4a1d1"
down_revision: Union[str, Sequence[str], None] = "005ff59dbcf0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "education_pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_education_pages_id"), "education_pages", ["id"], unique=False)

    op.create_table(
        "education_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["page_id"], ["education_pages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["education_sections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("page_id", "slug", name="uq_education_sections_page_slug"),
    )
    op.create_index(op.f("ix_education_sections_id"), "education_sections", ["id"], unique=False)
    op.create_index(op.f("ix_education_sections_page_id"), "education_sections", ["page_id"], unique=False)

    education_pages = sa.table(
        "education_pages",
        sa.column("id", sa.Integer()),
        sa.column("slug", sa.String()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_published", sa.Boolean()),
    )

    education_sections = sa.table(
        "education_sections",
        sa.column("id", sa.Integer()),
        sa.column("page_id", sa.Integer()),
        sa.column("parent_id", sa.Integer()),
        sa.column("slug", sa.String()),
        sa.column("title", sa.String()),
        sa.column("summary", sa.Text()),
        sa.column("content", sa.Text()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_published", sa.Boolean()),
    )

    op.bulk_insert(
        education_pages,
        [
            {
                "id": 1,
                "slug": "education",
                "title": "Обучающая информация",
                "description": (
                    "На этой странице собраны базовые теоретические материалы по хешированию, "
                    "используемым алгоритмам и способам работы с коллизиями."
                ),
                "is_published": True,
            }
        ],
    )

    op.bulk_insert(
        education_sections,
        [
            {
                "id": 1,
                "page_id": 1,
                "parent_id": None,
                "slug": "hashing-basics",
                "title": "Общее понимание хеширования",
                "summary": "Что такое хеширование и каким свойствам должна отвечать хорошая хеш-функция.",
                "content": (
                    "Хеширование — это преобразование входных данных произвольной длины в строку "
                    "фиксированного размера, которую называют хешем или дайджестом.\n\n"
                    "Даже небольшое изменение исходных данных должно заметно менять результат. "
                    "Это свойство называют эффектом лавины.\n\n"
                    "Для практического использования важны детерминированность, высокая скорость "
                    "вычисления и низкая вероятность совпадения результатов для разных входов."
                ),
                "sort_order": 10,
                "is_published": True,
            },
            {
                "id": 2,
                "page_id": 1,
                "parent_id": None,
                "slug": "why-hashing-is-needed",
                "title": "Для чего нужно хеширование",
                "summary": "Основные задачи, в которых хеширование помогает быстро и безопасно работать с данными.",
                "content": (
                    "Хеширование применяется для проверки целостности данных: можно сравнить хеш файла "
                    "до и после передачи и убедиться, что содержимое не изменилось.\n\n"
                    "Также хеши используются при хранении паролей, чтобы не сохранять сам пароль в базе. "
                    "Обычно для этого дополнительно применяют соль и специализированные алгоритмы.\n\n"
                    "В структурах данных хеширование помогает быстро находить элементы по ключу, "
                    "например в хеш-таблицах."
                ),
                "sort_order": 20,
                "is_published": True,
            },
            {
                "id": 3,
                "page_id": 1,
                "parent_id": None,
                "slug": "available-hash-functions",
                "title": "Доступные хеш-функции",
                "summary": "Алгоритмы, которые можно изучать и использовать на ресурсе.",
                "content": (
                    "На ресурсе предусмотрена работа с несколькими популярными алгоритмами. "
                    "Они различаются длиной результата, скоростью и уровнем современной криптографической устойчивости."
                ),
                "sort_order": 30,
                "is_published": True,
            },
            {
                "id": 4,
                "page_id": 1,
                "parent_id": 3,
                "slug": "md5",
                "title": "MD5",
                "summary": "Исторически популярный алгоритм с длиной хеша 128 бит.",
                "content": (
                    "MD5 долгое время использовался для контроля целостности файлов и в прикладных системах.\n\n"
                    "Сегодня алгоритм считается криптографически небезопасным, потому что для него "
                    "известны практические атаки на коллизии.\n\n"
                    "Его полезно изучать как часть истории развития хеш-функций и для сравнения с более современными подходами."
                ),
                "sort_order": 10,
                "is_published": True,
            },
            {
                "id": 5,
                "page_id": 1,
                "parent_id": 3,
                "slug": "md6",
                "title": "MD6",
                "summary": "Экспериментальный алгоритм семейства MD, предложенный как развитие более ранних решений.",
                "content": (
                    "MD6 разрабатывался как кандидат на роль современной криптографической хеш-функции.\n\n"
                    "Алгоритм интересен с учебной точки зрения, потому что показывает, как проектируются "
                    "более сложные схемы обработки блоков данных.\n\n"
                    "При этом MD6 не стал широко принятым отраслевым стандартом, поэтому обычно изучается "
                    "как исследовательский и сравнительный пример."
                ),
                "sort_order": 20,
                "is_published": True,
            },
            {
                "id": 6,
                "page_id": 1,
                "parent_id": 3,
                "slug": "sha-1",
                "title": "SHA-1",
                "summary": "Алгоритм из семейства SHA с длиной результата 160 бит.",
                "content": (
                    "SHA-1 долго применялся в цифровых подписях, сертификатах и системах контроля версий.\n\n"
                    "Сейчас его использование в новых защищённых системах не рекомендуется из-за найденных "
                    "коллизий и практических атак.\n\n"
                    "В учебных курсах SHA-1 обычно рассматривают как переходный этап между старыми и современными стандартами."
                ),
                "sort_order": 30,
                "is_published": True,
            },
            {
                "id": 7,
                "page_id": 1,
                "parent_id": 3,
                "slug": "sha-256",
                "title": "SHA-256",
                "summary": "Современный и широко применяемый алгоритм семейства SHA-2 с длиной хеша 256 бит.",
                "content": (
                    "SHA-256 используется в задачах контроля целостности, цифровых подписях, сертификатах "
                    "и блокчейн-системах.\n\n"
                    "Алгоритм обеспечивает высокий уровень устойчивости и остаётся одним из практических стандартов.\n\n"
                    "Именно его удобно брать как базовый пример современной криптографической хеш-функции."
                ),
                "sort_order": 40,
                "is_published": True,
            },
            {
                "id": 8,
                "page_id": 1,
                "parent_id": None,
                "slug": "collision-resolution",
                "title": "Методы решения коллизий",
                "summary": "Что такое коллизия и какие подходы применяются для её обработки в хеш-таблицах.",
                "content": (
                    "Коллизия возникает, когда разные ключи попадают в одну и ту же ячейку хеш-таблицы.\n\n"
                    "Полностью избежать коллизий на практике невозможно, поэтому важно выбирать понятную и "
                    "эффективную стратегию их обработки."
                ),
                "sort_order": 40,
                "is_published": True,
            },
            {
                "id": 9,
                "page_id": 1,
                "parent_id": 8,
                "slug": "separate-chaining",
                "title": "Цепочки",
                "summary": "Способ, при котором в одной ячейке хранится список элементов с одинаковым индексом.",
                "content": (
                    "При методе цепочек каждая ячейка таблицы хранит не один элемент, а структуру данных "
                    "для нескольких значений, например список.\n\n"
                    "Если несколько ключей дают одинаковый индекс, они добавляются в одну цепочку.\n\n"
                    "Подход прост в реализации и хорошо работает при умеренной загрузке таблицы, "
                    "но требует дополнительной памяти под связанные структуры."
                ),
                "sort_order": 10,
                "is_published": True,
            },
            {
                "id": 10,
                "page_id": 1,
                "parent_id": 8,
                "slug": "double-hashing",
                "title": "Двойное хеширование",
                "summary": "Вариант открытой адресации, при котором следующий индекс вычисляется второй хеш-функцией.",
                "content": (
                    "При двойном хешировании используется основная хеш-функция для первой позиции и "
                    "вторая функция для выбора шага поиска следующей свободной ячейки.\n\n"
                    "Такой подход уменьшает кластеризацию по сравнению с линейным пробированием "
                    "и делает распределение значений более равномерным.\n\n"
                    "Метод эффективен, если вторая функция подобрана так, чтобы покрывать достаточно "
                    "большую часть таблицы без коротких циклов."
                ),
                "sort_order": 20,
                "is_published": True,
            },
        ],
    )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "SELECT setval(pg_get_serial_sequence('education_pages', 'id'), "
            "(SELECT MAX(id) FROM education_pages))"
        )
    )
    bind.execute(
        sa.text(
            "SELECT setval(pg_get_serial_sequence('education_sections', 'id'), "
            "(SELECT MAX(id) FROM education_sections))"
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_education_sections_page_id"), table_name="education_sections")
    op.drop_index(op.f("ix_education_sections_id"), table_name="education_sections")
    op.drop_table("education_sections")

    op.drop_index(op.f("ix_education_pages_id"), table_name="education_pages")
    op.drop_table("education_pages")
