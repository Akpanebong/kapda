class PrimaryKeySlug(int):
    def __new__(cls, value, slug=""):
        instance = super().__new__(cls, value)
        instance.slug = slug
        return instance


class PrimaryKeySlugConverter:
    """Accept either a numeric primary key or ``pk-slug`` in URL paths."""
    regex = r"\d+(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?"

    def to_python(self, value):
        parts = value.split("-", 1)
        return PrimaryKeySlug(int(parts[0]), parts[1] if len(parts) > 1 else "")

    def to_url(self, value):
        if hasattr(value, "pk") and getattr(value, "slug", None):
            return f"{value.pk}-{value.slug}"
        return str(value)
