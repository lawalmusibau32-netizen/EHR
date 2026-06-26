class BaseRepository:
    """Common repository base for future Oracle-backed data access layers."""

    def __init__(self, pool) -> None:
        self.pool = pool

