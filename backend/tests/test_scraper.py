"""Test suite verifying Scrapy spiders parsing and pipeline ingestion."""

import uuid

import pytest
from scrapy.http import HtmlResponse

from app.db.vector_store import VectorStore
from app.scraper.pipelines import SchemePipeline
from app.scraper.spiders.myscheme import MySchemeSpider
from app.scraper.spiders.up_portal import UPPortalSpider


def test_myscheme_spider_parsing() -> None:
    """Validate MySchemeSpider css parsing and key extraction from html."""
    spider = MySchemeSpider()

    mock_html = """
    <html>
        <body>
            <div class="scheme-card">
                <h3 class="scheme-title">PM Kisan Samman Nidhi</h3>
                <span class="scheme-category">Agriculture</span>
                <p class="scheme-description">Direct income support of 6000 per year to farmers</p>
                <a class="scheme-link" href="/schemes/pmkisan">View Scheme</a>
                <span class="rule-min-age">18</span>
                <span class="rule-income-limit">200000</span>
            </div>
        </body>
    </html>
    """

    response = HtmlResponse(
        url="https://www.myscheme.gov.in/schemes",
        body=mock_html.encode("utf-8"),
        encoding="utf-8",
    )

    items = list(spider.parse(response))
    assert len(items) == 1
    assert items[0]["name"] == "PM Kisan Samman Nidhi"
    assert items[0]["issuing_body"] == "Central"
    assert items[0]["category"] == "Agriculture"
    assert (
        items[0]["description"]
        == "Direct income support of 6000 per year to farmers"
    )
    assert (
        items[0]["source_url"]
        == "https://www.myscheme.gov.in/schemes/pmkisan"
    )
    assert items[0]["eligibility_rules"] == {"min_age": 18, "income_limit": 200000}


def test_up_portal_spider_parsing() -> None:
    """Validate UPPortalSpider css parsing and key extraction from html."""
    spider = UPPortalSpider()

    mock_html = """
    <html>
        <body>
            <div class="up-scheme-card">
                <h4 class="up-scheme-title">UP Kanya Sumangala Yojana</h4>
                <span class="up-scheme-cat">Women and Child</span>
                <p class="up-scheme-desc">Financial support for girl child birth and education</p>
                <a class="up-scheme-link" href="/page/kanya">Details</a>
                <span class="rule-min-age">0</span>
                <span class="rule-income-limit">300000</span>
            </div>
        </body>
    </html>
    """

    response = HtmlResponse(
        url="https://up.gov.in/en/page/schemes",
        body=mock_html.encode("utf-8"),
        encoding="utf-8",
    )

    items = list(spider.parse(response))
    assert len(items) == 1
    assert items[0]["name"] == "UP Kanya Sumangala Yojana"
    assert items[0]["issuing_body"] == "State"
    assert items[0]["state"] == "Uttar Pradesh"
    assert items[0]["category"] == "Women and Child"
    assert (
        items[0]["description"]
        == "Financial support for girl child birth and education"
    )
    assert items[0]["source_url"] == "https://up.gov.in/page/kanya"
    assert items[0]["eligibility_rules"] == {"min_age": 0, "income_limit": 300000}


@pytest.mark.asyncio
async def test_scraper_pipeline_ingestion() -> None:
    """Validate Scrapy Pipeline ingests scheme items successfully to VectorStore."""
    spider = MySchemeSpider()
    pipeline = SchemePipeline()

    # Clear mock class cache to start clean
    VectorStore._in_memory_schemes.clear()
    store = VectorStore(is_mock=True)

    item = {
        "id": uuid.uuid4(),
        "name": "Pipeline Ingestion Test Scheme",
        "issuing_body": "Central",
        "category": "Agriculture",
        "description": "Financial support and crop insurance for farmers",
        "eligibility_rules": {"min_age": 18},
        "source_url": "https://test.gov/scheme",
    }

    # Process item via pipeline
    await pipeline.process_item(item, spider)

    # Search VectorStore to verify it was stored
    results = await store.search_similar_schemes("crop insurance for farmers")
    assert len(results) == 1
    assert results[0]["name"] == "Pipeline Ingestion Test Scheme"
    assert results[0]["eligibility_rules"]["min_age"] == 18
