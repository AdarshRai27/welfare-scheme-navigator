"""Test suite verifying LangGraph reasoning, rule evaluation, and forward-chaining."""

import uuid

import pytest

from app.agent.graph import run_agent
from app.db.vector_store import VectorStore


@pytest.mark.asyncio
async def test_agent_pm_kisan_eligibility_and_forward_chain() -> None:
    """Test that qualifying for PM-Kisan triggers forward-chained agri schemes."""
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    # 1. Ingest PM-Kisan scheme
    pm_kisan = {
        "id": uuid.uuid4(),
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support for landowning farmers across India",
        "eligibility_rules": {
            "land_size_limit": 2.0,  # Max 2 hectares
        },
        "source_url": "https://pmkisan.gov.in",
    }
    await store.add_scheme(pm_kisan)

    # 2. Run agent with qualifying profile (1.5 hectares)
    result = await run_agent(
        user_query="agricultural scheme for farmers",
        extracted_profile={"land_size_hectares": 1.5},
        language="en",
    )

    # 3. Asserts
    eligible = result["eligible_schemes"]
    suggested = result["suggested_schemes"]
    reply = result["reply_text"]

    assert len(eligible) == 1
    assert eligible[0]["name"] == "PM-Kisan Samman Nidhi"
    # Verify forward-chaining triggered
    assert len(suggested) == 2
    assert suggested[0]["name"] == "Kisan Credit Card (KCC)"
    assert suggested[1]["name"] == "Pradhan Mantri Fasal Bima Yojana (PMFBY)"
    # Verify output composed
    assert "Kisan Credit Card" in reply
    assert "Required Checklist" in reply


@pytest.mark.asyncio
async def test_agent_pm_kisan_ineligibility() -> None:
    """Test that exceeding the land size threshold renders the user ineligible."""
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    pm_kisan = {
        "id": uuid.uuid4(),
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support for landowning farmers across India",
        "eligibility_rules": {
            "land_size_limit": 2.0,
        },
    }
    await store.add_scheme(pm_kisan)

    # Run agent with ineligible profile (2.5 hectares)
    result = await run_agent(
        user_query="agricultural scheme for farmers",
        extracted_profile={"land_size_hectares": 2.5},
        language="en",
    )

    assert len(result["eligible_schemes"]) == 0
    assert len(result["suggested_schemes"]) == 0
    assert "do not currently qualify" in result["reply_text"]


@pytest.mark.asyncio
async def test_agent_state_pension_eligibility() -> None:
    """Test that age and state filters apply correctly for state pension schemes."""
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    up_pension = {
        "id": uuid.uuid4(),
        "name": "UP Senior Pension Scheme",
        "issuing_body": "State",
        "state": "Uttar Pradesh",
        "category": "Pension",
        "description": "Old age pension support for citizens in UP",
        "eligibility_rules": {
            "min_age": 60,
            "income_limit": 46080,
        },
    }
    await store.add_scheme(up_pension)

    # 1. Test qualifying profile
    res_ok = await run_agent(
        user_query="pension scheme",
        extracted_profile={
            "age": 65,
            "annual_income": 30000,
            "state": "Uttar Pradesh",
        },
        language="hi",
    )
    assert len(res_ok["eligible_schemes"]) == 1
    assert res_ok["eligible_schemes"][0]["name"] == "UP Senior Pension Scheme"
    assert "पात्र हैं" in res_ok["reply_text"]

    # 2. Test state mismatch (user resides in Bihar)
    res_state_err = await run_agent(
        user_query="pension scheme",
        extracted_profile={
            "age": 65,
            "annual_income": 30000,
            "state": "Bihar",
        },
        language="hi",
    )
    assert len(res_state_err["eligible_schemes"]) == 0

    # 3. Test age mismatch (user is 45 years old)
    res_age_err = await run_agent(
        user_query="pension scheme",
        extracted_profile={
            "age": 45,
            "annual_income": 30000,
            "state": "Uttar Pradesh",
        },
        language="hi",
    )
    assert len(res_age_err["eligible_schemes"]) == 0
