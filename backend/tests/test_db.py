"""Test suite verifying SQL models mappings and vector store fallback logic."""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Scheme, SchemeDocumentRequired, ScrapeRun
from app.db.vector_store import VectorStore, generate_mock_embedding


def test_db_mappings() -> None:
    """Validate model class columns and constraints using SQLite in-memory."""
    # Set up memory SQLite engine
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        scheme_id = uuid.uuid4()
        # 1. Insert Scheme
        scheme = Scheme(
            id=scheme_id,
            name="UP Pension Scheme",
            issuing_body="State",
            state="Uttar Pradesh",
            category="Pension",
            description="Financial monthly support for senior citizens.",
            eligibility_rules={"min_age": 60, "income_limit": 46080},
            source_url="https://sspy-up.gov.in",
        )
        session.add(scheme)

        # 2. Insert Required Documents
        doc = SchemeDocumentRequired(
            scheme_id=scheme_id,
            document_type="income_certificate",
            mandatory=True,
        )
        session.add(doc)

        # 3. Insert Scrape Audit log
        run = ScrapeRun(
            source_name="up_portal",
            status="success",
            schemes_added=1,
            schemes_updated=0,
        )
        session.add(run)

        session.commit()

        # Queries & Asserts
        db_scheme = session.query(Scheme).filter_by(id=scheme_id).first()
        assert db_scheme is not None
        assert db_scheme.name == "UP Pension Scheme"
        assert db_scheme.eligibility_rules["min_age"] == 60
        assert len(db_scheme.documents) == 1
        assert db_scheme.documents[0].document_type == "income_certificate"

        db_run = session.query(ScrapeRun).first()
        assert db_run is not None
        assert db_run.status == "success"
        assert db_run.schemes_added == 1

    finally:
        session.close()


@pytest.mark.asyncio
async def test_vector_store_mock_search() -> None:
    """Validate in-memory vector store ranking fallback works properly."""
    store = VectorStore(is_mock=True)

    scheme_agri = {
        "id": uuid.uuid4(),
        "name": "PM Kisan agri",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support for landowning farmers across India",
        "eligibility_rules": {},
    }

    scheme_edu = {
        "id": uuid.uuid4(),
        "name": "UP Scholar edu",
        "issuing_body": "State",
        "state": "Uttar Pradesh",
        "category": "Education",
        "description": "Educational financial scholarship support for school students",
        "eligibility_rules": {},
    }

    # Add schemes to memory store
    await store.add_scheme(scheme_agri)
    await store.add_scheme(scheme_edu)

    # Search: query containing agricultural keywords
    res_agri = await store.search_similar_schemes("Show me schemes for farmers")
    assert len(res_agri) > 0
    assert res_agri[0]["name"] == "PM Kisan agri"

    # Search: query containing educational keywords
    res_edu = await store.search_similar_schemes("Looking for student scholarships")
    assert len(res_edu) > 0
    assert res_edu[0]["name"] == "UP Scholar edu"
