import asyncio
from playwright.async_api import async_playwright
from llm_mapper import LLMMapper
from field_filler import fill_field_dynamic
from static_fallbacks import StaticFallbacks
from data import mock_data_all_fields

TARGET_URL = "https://mendrika-alma.github.io/form-submission/"


class FormFiller:

    def __init__(self, target_url: str, mock_data: dict):
        self.target_url = target_url
        self.mock_data = mock_data
        self.mapper = LLMMapper()
        self.static = StaticFallbacks()

    async def fill_form(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            print(f"🌐 Navigating to {self.target_url}")
            await page.goto(self.target_url)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            await page.wait_for_selector(".form-container", timeout=60000)

            # Get the raw HTML.
            raw_html = await page.content()

            # LLM CALL: Get mapping from raw HTML and mock data.
            llm_mappings = await self.mapper.get_mapping(raw_html, self.mock_data)
            if llm_mappings:
                print("\n📋 LLM Mappings:")
                for mapping in llm_mappings:
                    print(mapping)
                    await fill_field_dynamic(page, mapping)
            else:
                print("⚠️ No LLM mappings returned.")

            # Minimal static fallbacks.
            await self.static.fill_signature_dates(page)
            await self.static.apply_part6(page)
            await self.static.fill_unit_info(page, "attorney")
            await self.static.fill_unit_info(page, "client")

            print("\nℹ️ Skipping signature fields as required by assignment.")
            print("\n✅ Done. Form filled (without signing) but not submitted.")
            await asyncio.sleep(1000000)
            await browser.close()
