"""Scrapy Spider for Uttar Pradesh State Portal."""

from typing import Any, Dict, Generator

import scrapy
from scrapy.http import Response


class UPPortalSpider(scrapy.Spider):
    """Scrapes state welfare schemes and rules from the Uttar Pradesh portal."""

    name: str = "up_portal"
    allowed_domains: list[str] = ["up.gov.in", "localhost", "127.0.0.1"]
    start_urls: list[str] = ["https://up.gov.in/en/page/schemes"]

    def parse(
        self, response: Response, **kwargs: Any
    ) -> Generator[Dict[str, Any], None, None]:
        """Parses the UP state portal listing page and yields scheme item dicts.

        Args:
            response: Scrapy HTTP response object.

        Yields:
            Dictionary matching the Scheme schema attributes.
        """
        # Select individual state scheme containers
        cards = response.css(".up-scheme-card")
        for card in cards:
            title = card.css(".up-scheme-title::text").get()
            if not title:
                continue

            name = title.strip()
            category = card.css(".up-scheme-cat::text").get(default="General").strip()
            description = card.css(".up-scheme-desc::text").get(default="").strip()
            link = card.css("a.up-scheme-link::attr(href)").get(default="")
            source_url = response.urljoin(link)

            # Extract basic rules if present as CSS hooks (useful for testing)
            min_age = card.css(".rule-min-age::text").get()
            income_limit = card.css(".rule-income-limit::text").get()

            eligibility_rules: Dict[str, Any] = {}
            if min_age:
                try:
                    eligibility_rules["min_age"] = int(min_age.strip())
                except ValueError:
                    pass
            if income_limit:
                try:
                    eligibility_rules["income_limit"] = int(income_limit.strip())
                except ValueError:
                    pass

            yield {
                "name": name,
                "issuing_body": "State",
                "state": "Uttar Pradesh",
                "category": category,
                "description": description,
                "eligibility_rules": eligibility_rules,
                "source_url": source_url,
            }
