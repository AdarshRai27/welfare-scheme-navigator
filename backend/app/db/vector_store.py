"""Vector store manager and database connection helper."""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base, Scheme

logger = logging.getLogger(__name__)


def generate_mock_embedding(text: str) -> List[float]:
    """Generates a deterministic 1024-dimensional vector from input text.

    Uses md5 hashing of words so that identical texts return identical vectors.

    Args:
        text: Input string description.

    Returns:
        List of 1024 floats.
    """
    words = text.lower().split()
    vector = [0.0] * 1024
    if not words:
        return vector

    for idx, word in enumerate(words):
        # Create deterministic hash index
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        pos = h % 1024
        # Add deterministic value based on position
        vector[pos] += 0.1 + (idx * 0.01)
        vector[(pos + 13) % 1024] -= 0.05

    # Normalize vector to unit length
    magnitude = sum(val**2 for val in vector) ** 0.5
    if magnitude > 0:
        vector = [val / magnitude for val in vector]

    return vector


class DBManager:
    """Manages async PostgreSQL connection engine and sessions."""

    def __init__(self, database_url: str) -> None:
        """Initialize database connections with fallback handling.

        Args:
            database_url: Database connection string.
        """
        self.database_url: str = database_url
        self.engine: Optional[Any] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self.is_mock_mode: bool = False

        try:
            # We use pg16 image with asyncpg driver
            self.engine = create_async_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
            )
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            logger.info("SQLAlchemy database engine initialized.")
        except Exception as err:
            logger.warning(
                f"Failed to initialize real database engine: {err}. Mock mode enabled."
            )
            self.is_mock_mode = True

    async def init_db(self) -> None:
        """Initialize database schemas (run tables creation if in live mode)."""
        if self.engine and not self.is_mock_mode:
            try:
                async with self.engine.begin() as conn:
                    # Activate extension and create tables
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables initialized successfully.")
            except Exception as err:
                logger.error(
                    f"Error running table migrations: {err}. Falling back to mock database storage."
                )
                self.is_mock_mode = True


# Initialize global database manager
db_manager = DBManager(settings.DATABASE_URL)


class VectorStore:
    """Handles pgvector embedding registration and similarity search."""

    # Class-level mock database cache for fallback modes
    _in_memory_schemes: List[Dict[str, Any]] = []

    def __init__(
        self, session: Optional[AsyncSession] = None, is_mock: bool = False
    ) -> None:
        """Initialize VectorStore with optional live DB session.

        Args:
            session: AsyncSession database context.
            is_mock: Force mock fallback mode.
        """
        self.session: Optional[AsyncSession] = session
        self.is_mock: bool = is_mock or db_manager.is_mock_mode

    async def add_scheme(self, scheme_data: Dict[str, Any]) -> None:
        """Insert or update a scheme in the vector store with embeddings.

        Args:
            scheme_data: Dictionary matching the Scheme schema attributes.
        """
        description = scheme_data.get("description", "")
        embedding = generate_mock_embedding(description)
        scheme_data["embedding"] = embedding

        if not self.is_mock and self.session:
            try:
                scheme = Scheme(
                    id=scheme_data.get("id"),
                    name=scheme_data["name"],
                    issuing_body=scheme_data["issuing_body"],
                    state=scheme_data.get("state"),
                    category=scheme_data["category"],
                    description=description,
                    eligibility_rules=scheme_data["eligibility_rules"],
                    source_url=scheme_data.get("source_url"),
                    embedding=embedding,
                )
                self.session.add(scheme)
                await self.session.commit()
                return
            except Exception as err:
                logger.error(f"Failed to add scheme to Postgres: {err}")

        # Fallback cache
        self._in_memory_schemes.append(scheme_data)

    async def search_similar_schemes(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search and rank schemes similar to query using cosine similarity.

        Args:
            query: User's voice/text question about welfare.
            limit: Maximum count of results.

        Returns:
            List of top matched scheme records.
        """
        if not self.is_mock and self.session:
            try:
                query_vector = generate_mock_embedding(query)
                # Select schemes ordered by pgvector cosine distance
                stmt = (
                    select(Scheme)
                    .order_by(Scheme.embedding.cosine_distance(query_vector))
                    .limit(limit)
                )
                result = await self.session.execute(stmt)
                schemes = result.scalars().all()
                return [
                    {
                        "id": s.id,
                        "name": s.name,
                        "issuing_body": s.issuing_body,
                        "state": s.state,
                        "category": s.category,
                        "description": s.description,
                        "eligibility_rules": s.eligibility_rules,
                        "source_url": s.source_url,
                    }
                    for s in schemes
                ]
            except Exception as err:
                logger.error(f"Postgres vector search failed: {err}")

        # In-Memory local intersection keyword ranking
        query_words = [
            qw.strip(".,!?\"'").rstrip("s")
            for qw in query.lower().split()
            if len(qw.strip(".,!?\"'")) > 1
        ]
        results = []
        stop_words = {"for", "to", "in", "a", "the", "of", "and", "me", "show", "is", "look"}

        for s in self._in_memory_schemes:
            desc_words = [
                dw.strip(".,!?\"'").rstrip("s")
                for dw in s.get("description", "").lower().split()
            ]
            score = 0.0
            for qw in query_words:
                if qw in stop_words:
                    if qw in desc_words:
                        score += 0.05
                else:
                    for dw in desc_words:
                        if qw in dw or dw in qw:
                            score += 1.0
                            break
            results.append((score, s))

        # Sort descending by score
        results.sort(key=lambda x: x[0], reverse=True)
        
        ret_schemes = []
        for res in results[:limit]:
            s_copy = dict(res[1])
            s_copy.pop("embedding", None)
            ret_schemes.append(s_copy)
        return ret_schemes

