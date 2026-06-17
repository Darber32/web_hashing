from sqlalchemy.orm import Session

from App.models.education import EducationPage, EducationSection


class Education_Repository:

    def __init__(self, db: Session):
        self.db = db

    def get_published_page_by_slug(self, slug: str):
        return (
            self.db.query(EducationPage)
            .filter(
                EducationPage.slug == slug,
                EducationPage.is_published.is_(True),
            )
            .first()
        )

    def get_page_by_slug(self, slug: str):
        return (
            self.db.query(EducationPage)
            .filter(EducationPage.slug == slug)
            .first()
        )

    def get_pages(self):
        return (
            self.db.query(EducationPage)
            .order_by(EducationPage.sort_order.asc(), EducationPage.id.asc())
            .all()
        )

    def get_page_by_id(self, page_id: int):
        return (
            self.db.query(EducationPage)
            .filter(EducationPage.id == page_id)
            .first()
        )

    def get_published_pages(self):
        return (
            self.db.query(EducationPage)
            .filter(EducationPage.is_published.is_(True))
            .order_by(EducationPage.sort_order.asc(), EducationPage.id.asc())
            .all()
        )

    def create_page(self, **values):
        page = EducationPage(**values)
        self.db.add(page)
        self.db.flush()
        self.db.refresh(page)
        return page

    def delete_page(self, page: EducationPage):
        (
            self.db.query(EducationSection)
            .filter(EducationSection.page_id == page.id)
            .delete(synchronize_session=False)
        )
        self.db.delete(page)
        self.db.flush()

    def get_sections(self):
        return (
            self.db.query(EducationSection)
            .order_by(
                EducationSection.page_id.asc(),
                EducationSection.sort_order.asc(),
                EducationSection.id.asc(),
            )
            .all()
        )

    def get_sections_for_page(self, page_id: int):
        return (
            self.db.query(EducationSection)
            .filter(EducationSection.page_id == page_id)
            .order_by(EducationSection.sort_order.asc(), EducationSection.id.asc())
            .all()
        )

    def get_section_by_id(self, section_id: int):
        return (
            self.db.query(EducationSection)
            .filter(EducationSection.id == section_id)
            .first()
        )

    def get_section_by_page_and_slug(self, page_id: int, slug: str):
        return (
            self.db.query(EducationSection)
            .filter(
                EducationSection.page_id == page_id,
                EducationSection.slug == slug,
            )
            .first()
        )

    def create_section(self, **values):
        section = EducationSection(**values)
        self.db.add(section)
        self.db.flush()
        self.db.refresh(section)
        return section

    def delete_section(self, section: EducationSection):
        section_ids = self.get_section_descendant_ids(section.id)
        (
            self.db.query(EducationSection)
            .filter(EducationSection.id.in_(section_ids))
            .delete(synchronize_session=False)
        )
        self.db.flush()

    def get_section_descendant_ids(self, section_id: int):
        return self._collect_section_descendant_ids_from_sections(
            section_id,
            self.get_sections(),
        )

    def _collect_section_descendant_ids(self, section_id: int):
        return self._collect_section_descendant_ids_from_sections(
            section_id,
            self.get_sections(),
        )

    def _collect_section_descendant_ids_from_sections(self, section_id: int, sections):
        children_by_parent = {}

        for section in sections:
            children_by_parent.setdefault(section.parent_id, []).append(section.id)

        ids = []
        stack = [section_id]

        while stack:
            current_id = stack.pop()
            ids.append(current_id)
            stack.extend(children_by_parent.get(current_id, []))

        return ids

    def get_section_hierarchy(self, page_id: int, published_only: bool = False):
        sections = (
            self.db.query(EducationSection)
            .filter(EducationSection.page_id == page_id)
            .order_by(EducationSection.sort_order.asc(), EducationSection.id.asc())
            .all()
        )

        if published_only:
            return self._build_published_section_hierarchy(sections)

        return self._build_section_hierarchy(sections)

    def get_flat_section_hierarchy(
        self,
        page_id: int,
        published_only: bool = False,
        exclude_ids: set[int] | None = None,
    ):
        nodes = self.get_section_hierarchy(page_id, published_only=published_only)
        return self._flatten_section_hierarchy(
            nodes,
            depth=0,
            parent_title=None,
            exclude_ids=exclude_ids or set(),
        )

    def get_parent_section_options(
        self,
        page_id: int,
        current_section_id: int | None = None,
    ):
        excluded_ids = set()

        if current_section_id is not None:
            excluded_ids = set(self.get_section_descendant_ids(current_section_id))

        return self.get_flat_section_hierarchy(
            page_id,
            published_only=False,
            exclude_ids=excluded_ids,
        )

    def get_published_section_tree(self, page_id: int):
        nodes = self.get_section_hierarchy(page_id, published_only=True)
        return self._serialize_section_nodes(nodes)

    def _build_section_hierarchy(self, sections):
        nodes = {}
        roots = []

        for section in sections:
            nodes[section.id] = {"section": section, "children": []}

        for section in sections:
            node = nodes[section.id]

            if section.parent_id and section.parent_id in nodes:
                nodes[section.parent_id]["children"].append(node)
            else:
                roots.append(node)

        return self._sort_section_nodes(roots)

    def _build_published_section_hierarchy(self, sections):
        all_nodes = self._build_section_hierarchy(sections)
        return self._filter_published_nodes(all_nodes)

    def _sort_section_nodes(self, nodes):
        ordered_nodes = sorted(
            nodes,
            key=lambda node: (
                node["section"].sort_order,
                node["section"].id,
            ),
        )

        for node in ordered_nodes:
            node["children"] = self._sort_section_nodes(node["children"])

        return ordered_nodes

    def _filter_published_nodes(self, nodes):
        published_nodes = []

        for node in nodes:
            section = node["section"]

            if not section.is_published:
                continue

            published_nodes.append(
                {
                    "section": section,
                    "children": self._filter_published_nodes(node["children"]),
                }
            )

        return published_nodes

    def _flatten_section_hierarchy(
        self,
        nodes,
        depth: int,
        parent_title: str | None,
        exclude_ids: set[int],
    ):
        items = []

        for node in nodes:
            section = node["section"]

            if section.id not in exclude_ids:
                items.append(
                    {
                        "section": section,
                        "depth": depth,
                        "parent_title": parent_title,
                    }
                )

            items.extend(
                self._flatten_section_hierarchy(
                    node["children"],
                    depth=depth + 1,
                    parent_title=section.title,
                    exclude_ids=exclude_ids,
                )
            )

        return items

    def _serialize_section_nodes(self, nodes):
        serialized = []

        for node in nodes:
            section = node["section"]
            serialized.append(
                {
                    "id": section.id,
                    "title": section.title,
                    "slug": section.slug,
                    "summary": section.summary,
                    "content": section.content,
                    "sort_order": section.sort_order,
                    "children": self._serialize_section_nodes(node["children"]),
                }
            )

        return serialized

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
