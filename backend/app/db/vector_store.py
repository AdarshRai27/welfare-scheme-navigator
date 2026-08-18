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
    _has_seeded: bool = False

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

    @classmethod
    def load_seed_schemes(cls, force: bool = False) -> None:
        """Loads all schemes from schemes_seed.json into memory catalog."""
        if force or not cls._in_memory_schemes:
            import json
            import os
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                seed_path = os.path.join(current_dir, "schemes_seed.json")
                if os.path.exists(seed_path):
                    with open(seed_path, "r", encoding="utf-8") as f:
                        cls._in_memory_schemes = json.load(f)
                    cls._has_seeded = True
                    logger.info(
                        f"[VECTOR STORE] Loaded {len(cls._in_memory_schemes)} schemes into in-memory catalog."
                    )
            except Exception as err:
                logger.warning(f"[VECTOR STORE] Failed loading in-memory schemes: {err}")

    _ensure_in_memory_loaded = load_seed_schemes

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
        """Search and rank schemes similar to query using cosine similarity and semantic keywords.

        Args:
            query: User's voice/text question about welfare.
            limit: Maximum count of results.

        Returns:
            List of top matched scheme records.
        """
        if not self._in_memory_schemes and not self._has_seeded and not self.is_mock:
            self.load_seed_schemes()

        # If live database session or session_factory is available
        if not self.is_mock:
            session_to_use = self.session
            close_session = False
            if not session_to_use and db_manager.session_factory:
                session_to_use = db_manager.session_factory()
                close_session = True

            if session_to_use:
                try:
                    query_vector = generate_mock_embedding(query)
                    stmt = (
                        select(Scheme)
                        .order_by(Scheme.embedding.cosine_distance(query_vector))
                        .limit(limit)
                    )
                    result = await session_to_use.execute(stmt)
                    schemes = result.scalars().all()
                    if schemes:
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
                    logger.warning(f"Postgres vector search fallback to in-memory: {err}")
                finally:
                    if close_session:
                        await session_to_use.close()

        # In-Memory semantic multi-field search
        query_lower = query.lower()
        query_tokens = [
            w.strip(".,!?\"':;()[]{}").rstrip("s")
            for w in query_lower.split()
            if len(w.strip(".,!?\"':;()[]{}")) > 1
        ]

        # Domain Synonym Expansions
        synonym_map = {
            "kisan": ["farmer", "agriculture", "land", "crop", "pm-kisan", "fasal"],
            "farmer": ["kisan", "agriculture", "land", "crop", "pm-kisan", "tractor"],
            "kheti": ["agriculture", "farmer", "kisan", "crop"],
            "loan": ["mudra", "credit", "pmegp", "subsidy", "finance", "svanidhi", "business"],
            "startup": ["mudra", "business", "pmegp", "entrepreneur", "loan"],
            "dukan": ["mudra", "svanidhi", "business", "vendor", "shop"],
            "business": ["mudra", "pmegp", "msme", "loan", "vishwakarma"],
            "pension": ["old age", "vridha", "senior", "maan dhan", "social security", "atal"],
            "senior": ["pension", "vridha", "old age", "elderly", "60", "70"],
            "vridha": ["pension", "senior", "old age"],
            "mahila": ["women", "female", "girl", "matru", "ladli", "kanya", "widow", "shg"],
            "women": ["mahila", "female", "girl", "matru", "ladli", "kanya", "widow", "shg"],
            "female": ["mahila", "women", "girl", "ladli", "kanya"],
            "widow": ["vidhwa", "pension", "destitute", "women"],
            "vidhwa": ["widow", "pension", "destitute", "women"],
            "student": ["scholarship", "education", "college", "school", "matric", "coaching"],
            "scholarship": ["student", "education", "tuition", "fellowship", "merit"],
            "padhai": ["education", "scholarship", "student", "school"],
            "health": ["ayushman", "hospital", "medical", "insurance", "treatment", "arogya"],
            "hospital": ["ayushman", "health", "medical", "treatment", "cashless"],
            "ayushman": ["health", "hospital", "pmjay", "medical", "treatment"],
            "solar": ["surya", "electricity", "bijli", "roof", "kusum", "pump"],
            "bijli": ["solar", "surya", "electricity", "power", "unit"],
            "house": ["awas", "pmay", "pucca", "makan", "housing"],
            "makan": ["awas", "pmay", "house", "housing", "pucca"],
            "awas": ["housing", "house", "pmay", "makan"],
            "divyang": ["disability", "handicap", "disabled", "pension", "assistive"],
            "disability": ["divyang", "handicap", "disabled", "pension", "adip"],
            "artisan": ["vishwakarma", "craft", "toolkit", "shilpkar"],
            "shilpkar": ["vishwakarma", "artisan", "toolkit"],
        }

        expanded_tokens = set(query_tokens)
        for token in query_tokens:
            if token in synonym_map:
                expanded_tokens.update(synonym_map[token])

        stop_words = {"for", "to", "in", "a", "the", "of", "and", "me", "show", "is", "look", "i", "am", "want", "need", "chahiye", "mera", "meri", "hai", "ka", "ki", "ke", "ko"}

        results = []
        for s in self._in_memory_schemes:
            name_text = s.get("name", "").lower()
            cat_text = s.get("category", "").lower()
            desc_text = s.get("description", "").lower()
            body_text = s.get("issuing_body", "").lower()
            state_text = (s.get("state") or "").lower()

            score = 0.0

            # State check: If query mentions a specific state (e.g. "bihar", "up", "maharashtra", "rajasthan")
            if state_text and state_text in query_lower:
                score += 5.0

            # Exact name or keyword matches
            for token in expanded_tokens:
                if token in stop_words:
                    continue
                if token in name_text:
                    score += 4.0
                if token in cat_text:
                    score += 3.0
                if token in desc_text:
                    score += 1.5
                if token in body_text:
                    score += 1.0

            results.append((score, s))

        # Sort descending by relevance score
        results.sort(key=lambda x: x[0], reverse=True)

        ret_schemes = []
        for res in results[:limit]:
            s_copy = dict(res[1])
            s_copy.pop("embedding", None)
            ret_schemes.append(s_copy)

        # Fallback to first few schemes if no score matched
        if not ret_schemes and self._in_memory_schemes:
            for s in self._in_memory_schemes[:limit]:
                s_copy = dict(s)
                s_copy.pop("embedding", None)
                ret_schemes.append(s_copy)

        return ret_schemes

