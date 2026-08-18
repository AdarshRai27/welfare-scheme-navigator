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
    assert "Kisan Credit Card" in reply or "KCC" in reply
    assert "Eligibility" in reply or "PM-Kisan" in reply
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
    assert "not eligible for any schemes in our current database" in result["reply_text"]


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

    # 1. Test qualifying profile with Hindi query
    res_ok = await run_agent(
        user_query="पेंशन योजना",
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
        user_query="पेंशन योजना",
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
        user_query="पेंशन योजना",
        extracted_profile={
            "age": 45,
            "annual_income": 30000,
            "state": "Uttar Pradesh",
        },
        language="hi",
    )
    assert len(res_age_err["eligible_schemes"]) == 0


@pytest.mark.asyncio
async def test_complex_demographic_extraction_and_strict_reasoning() -> None:
    """Test extracting exact numbers (age 60, income ₹2 lakh, 1.5 acres land, UP) and strict age bounds."""
    from app.agent.nodes.extract import extract_demographics_from_text
    
    query = (
        "Please check my family's eligibility for government welfare schemes. "
        "I am 60 years old, my wife is 55, our annual household income is ₹2 lakh, "
        "and we own 1.5 acres of land. We live in a village in Uttar Pradesh. "
        "We have no government job or pension. Tell me which schemes we may qualify for."
    )
    
    extracted = extract_demographics_from_text(query)
    assert extracted["age"] == 60
    assert extracted["annual_income"] == 200000
    assert extracted["land_size_hectares"] == 0.61
    assert extracted["state"] == "Uttar Pradesh"

    # Verify agent execution with this profile
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    # Scheme with max_age 40 (must be disqualified for age 60)
    pm_kmy = {
        "id": uuid.uuid4(),
        "name": "PM Kisan Maan Dhan Yojana (PM-KMY)",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Pension for small farmers",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 40,
            "max_land_size_hectares": 2.0,
        },
    }
    # Scheme with land_size <= 2.0 and no age cap (must qualify)
    pm_kisan = {
        "id": uuid.uuid4(),
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support for landowning farmers",
        "eligibility_rules": {
            "max_land_size_hectares": 2.0,
        },
        "source_url": "https://pmkisan.gov.in",
    }
    await store.add_scheme(pm_kmy)
    await store.add_scheme(pm_kisan)

    res = await run_agent(user_query=query, extracted_profile={}, language="en")
    
    # PM-KMY must NOT be in eligible schemes because 60 > 40
    eligible_names = [s["name"] for s in res["eligible_schemes"]]
    assert "PM Kisan Maan Dhan Yojana (PM-KMY)" not in eligible_names
    assert "PM-Kisan Samman Nidhi" in eligible_names


@pytest.mark.asyncio
async def test_hyphenated_age_extraction_and_disqualification() -> None:
    """Test extracting '52-year-old' correctly and strictly disqualifying PM-KMY (max_age 40)."""
    from app.agent.nodes.extract import extract_demographics_from_text
    
    query = (
        "I am a 52-year-old farmer from Uttar Pradesh. My annual income is ₹1.8 lakh "
        "and I own 3 acres of farmland. I belong to an economically weaker family. "
        "What farmer and other government schemes can I apply for?"
    )
    
    extracted = extract_demographics_from_text(query)
    assert extracted["age"] == 52
    assert extracted["annual_income"] == 180000
    assert extracted["land_size_hectares"] == 1.21
    assert extracted["state"] == "Uttar Pradesh"

    # Verify agent execution
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    pm_kmy = {
        "id": uuid.uuid4(),
        "name": "PM Kisan Maan Dhan Yojana (PM-KMY)",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Pension for small farmers",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 40,
            "max_land_size_hectares": 2.0,
        },
        "source_url": "https://maandhan.in",
    }
    pm_kisan = {
        "id": uuid.uuid4(),
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support for landowning farmers",
        "eligibility_rules": {
            "max_land_size_hectares": 2.0,
        },
        "source_url": "https://pmkisan.gov.in",
    }
    await store.add_scheme(pm_kmy)
    await store.add_scheme(pm_kisan)

    res = await run_agent(user_query=query, extracted_profile={}, language="en")
    
    # PM-KMY must NOT be eligible because 52 > 40
    eligible_names = [s["name"] for s in res["eligible_schemes"]]
    assert "PM Kisan Maan Dhan Yojana (PM-KMY)" not in eligible_names
    assert "PM-Kisan Samman Nidhi" in eligible_names
    assert "Required Documents" in res["reply_text"]


@pytest.mark.asyncio
async def test_hindi_birth_year_and_pure_hindi_output() -> None:
    """Test extracting birth year 1964, name, and pure Hindi output."""
    from app.agent.nodes.extract import extract_demographics_from_text
    
    query = (
        "मेरा नाम रमेश कुमार है, मेरी उम्र 59 साल है, लेकिन मेरे आधार कार्ड में जन्म वर्ष 1964 है। "
        "मेरे परिवार की आय ₹1.9 लाख है और मेरे पास यूपी में 2 एकड़ जमीन है। "
        "मैं किन वरिष्ठ नागरिक और किसान योजनाओं के लिए पात्र हूँ?"
    )
    
    extracted = extract_demographics_from_text(query)
    assert extracted["age"] == 62
    assert extracted["annual_income"] == 190000
    assert extracted["land_size_hectares"] == 0.81
    assert extracted["state"] == "Uttar Pradesh"
    assert "रमेश कुमार" in extracted["name"]

    # Verify agent execution
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    pm_kisan = {
        "id": uuid.uuid4(),
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support for landowning farmers",
        "eligibility_rules": {
            "max_land_size_hectares": 2.0,
        },
        "source_url": "https://pmkisan.gov.in",
    }
    up_pension = {
        "id": uuid.uuid4(),
        "name": "UP Senior Pension Scheme",
        "issuing_body": "State",
        "state": "Uttar Pradesh",
        "category": "Pension",
        "description": "Old age pension support for citizens in UP",
        "eligibility_rules": {
            "min_age": 60,
            "income_limit": 200000,
        },
        "source_url": "https://sspy-up.gov.in",
    }
    await store.add_scheme(pm_kisan)
    await store.add_scheme(up_pension)

    res = await run_agent(user_query=query, extracted_profile={}, language="hi")
    
    assert len(res["eligible_schemes"]) == 2
    # Verify Hindi translations in reply
    assert "पीएम-किसान" in res["reply_text"] or "PM-Kisan" in res["reply_text"]
    assert "पात्र हैं" in res["reply_text"]
    assert "दस्तावेज़" in res["reply_text"]


@pytest.mark.asyncio
async def test_domain_limitation_guardrail_off_topic() -> None:
    """Test that off-topic programming or general sports queries are strictly refused."""
    off_topic_query = "Can you write a Python script using fastsort algorithm to sort numbers?"
    res = await run_agent(user_query=off_topic_query, extracted_profile={}, language="en")
    assert res["query_intent"] == "OFF_TOPIC"
    assert "Indian government welfare schemes" in res["reply_text"]
    assert "specifically designed" in res["reply_text"]


@pytest.mark.asyncio
async def test_didit_generic_image_scan_success() -> None:
    """Test that Didit ID scan with non-standard image filename (e.g. IMG_2026.jpg) succeeds."""
    from app.services.didit import DiditService
    service = DiditService()
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"A" * 500
    res = await service.extract_identity_document(fake_image_bytes, filename_hint="IMG_4892.jpg")
    assert res["provider"] == "didit"
    assert res["document_type"] == "aadhaar"
    assert res["extracted_fields"]["verified_status"] is True
    assert "XXXX" in res["extracted_fields"]["aadhaar_number"]






