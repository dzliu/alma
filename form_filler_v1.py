import os
import json
import asyncio
import re
from datetime import date
from dotenv import load_dotenv, find_dotenv
from playwright.async_api import async_playwright
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, validator
from typing import List, Dict

# -------------------------------------------
# Load API key from .env file
# -------------------------------------------
_ = load_dotenv(find_dotenv())
os.environ["OPENAI_API_KEY"]

TARGET_URL = "https://mendrika-alma.github.io/form-submission/"

# -------------------------------------------
# Complete Mock Data: All Fields Filled (General Case)
# -------------------------------------------
mock_data_all_fields = {
    "attorney": {
        "online_account_number": "A987654321",
        "family_name": "Smith",
        "first_name": "Alice",
        "middle_name": "B.",
        "address_line_1": "789 Corporate Blvd",
        "unit_type": "ste",  # Expect "ste" (suite) to be checked
        "address_line_2": "202",  # Unit number
        "city": "New York",
        "state": "New York",
        "zip_code": "10001",
        "province": "NY Province",
        "country": "United States",
        "daytime_phone": "(212) 555-6789",
        "email": "alice.smith@corporate.com",
        "fax": "2125559876",
        "attorney_eligible": "yes",
        "licensing_state": "NY",
        "bar_number": "NY123456",
        "subject_to_restrictions": "no",
        "law_firm": "Doe & Associates Legal Group",
        "is_nonprofit_rep": False,
        "org_name": "Smith Legal Group",
        "recognized_org": "Doe & Associates Legal Group",
        "associated_with_name": "Former Attorney",
        "accreditation_date": "04/15/2020",
        "associated_with_student": "yes",
        "law_student": "",
        "administrative_case": True,
        "administrative_matter": "Admin Matter 123",
        "civil_case": True,
        "civil_matter": "Civil Matter 456",
        "other_legal": True,
        "other_legal_matter": "Other Legal Matter Example",
        "receipt_number": "NY000111222",
        "client_type": "Beneficiary"
    },
    "client": {
        "family_name": "Brown",
        "first_name": "Charlie",
        "entity_name": "Brown Corp",
        "entity_title": "CEO",
        "reference_number": "REF-2023-9999",
        "id_number": "C123456789",
        "daytime_phone": "6465553333",
        "mobile_phone": "6465554444",
        "email": "charlie.brown@browncorp.com",
        "address_line_1": "456 Industrial Ave",
        "unit_type": "Apt",
        "address_line_2": "101",
        "city": "New York",
        "state": "NY",
        "zip_code": "10018",
        "province": "NY Province",
        "country": "US",
        "send_notices_to_attorney": "Y",
        "send_documents_to_attorney": "Y",
        "send_documents_to_client": "N",
        "signature_date": "05/01/2023"
    },
    "attorney_signature_date": "05/01/2023",
    "additional_signature_date": "05/01/2023",
    "part6": {
        "additional_info": {
            "family_name":
                "Green",
            "given_name":
                "Diana",
            "middle_name":
                "E.",
            "entries_section_2": [{
                "page_number": "1",
                "part_number": "2",
                "item_number": "1.a",
                "additional_info": "Also licensed in New York State Bar, Bar #NY7654321"
            }],
            "entries_section_3": [{
                "page_number": "3",
                "part_number": "3",
                "item_number": "3.c",
                "additional_info": "Extra information for section 3."
            }]
        }
    }
}


# -------------------------------------------
# Pydantic model for LLM mapping (for type hints)
# -------------------------------------------
class FieldMapping(BaseModel):
    section: str
    label: str
    value: str

    @validator("value", pre=True)
    def ensure_string(cls, v):
        if isinstance(v, bool):
            return "yes" if v else "no"
        return str(v)


async def get_field_mapping_with_llm(html_content: str, data: dict) -> List[FieldMapping]:
    prompt = ChatPromptTemplate.from_messages([("system", (
        "You are an expert form-filling assistant. Analyze the provided HTML and JSON data. "
        "For each fillable field in the form, produce an object with keys section, label, and value. "
        "The section must be one of attorney, client, or part6.\n\n"
        "For checkboxes, please follow these rules exactly:\n\n"
        "1. For the checkbox next to '1.a. I am an attorney eligible to practice law in, and a member in good standing of, the bar of the highest courts of the following jurisdictions. If you need extra space to complete this section, use the space provided in Part 6. Additional Information.', "
        "output the value from attorney_eligible (output 'yes' if true, or an empty string if false).\n\n"
        "2. For the field labeled '1.c. I (select only one box)', if the JSON value for subject_to_restrictions is 'yes', output 'am'; if it is 'no', output 'am not'.\n\n"
        "3. For the checkbox next to '2.a. I am an authorized representative of the following qualified nonprofit religious, charitable, social service, or similar organization.', "
        "output 'yes' if is_nonprofit_rep is true, or an empty string otherwise.\n\n"
        "4. For the checkbox next to '3. I am associated with', output 'yes' if associated_with_student is 'yes', or an empty string otherwise.\n\n"
        "5. For the checkbox next to '1.a. Administrative Case', output 'yes' if administrative_case is true, or an empty string otherwise.\n\n"
        "6. For the checkbox next to '2.a. Civil Case', output 'yes' if civil_case is true, or an empty string otherwise.\n\n"
        "7. For the checkbox next to '3.a. Other Legal Matter', output 'yes' if other_legal is true, or an empty string otherwise.\n\n"
        "8. For the checkbox under '5. I enter my appearance as an attorney or accredited representative at the request of the (select only one box):', "
        "output the value from client_type. For example, if client_type is 'Beneficiary', output Beneficiary; otherwise output an empty string.\n\n"
        "9. For the checkbox next to '1.a. I request that all original notices on an application or petition be sent to the business address of my attorney or representative as listed in this form.', "
        "output 'yes' if send_notices_to_attorney is 'Y', or an empty string otherwise.\n\n"
        "10. For the checkbox next to '1.b. I request that any important documents that I receive be sent to the business address of my attorney or representative.', "
        "output 'yes' if send_documents_to_attorney is 'Y', or an empty string otherwise.\n\n"
        "11. For the checkbox next to '1.c. I request that important documentation be sent to me at my mailing address.', "
        "output an empty string if send_documents_to_client is 'N', and 'yes' otherwise.\n\n"
        "For text fields, simply output the corresponding value from the JSON data. "
        "Return only a valid JSON array of these objects with no additional commentary.\n\n"
        "Example for rule 2: If subject_to_restrictions is 'yes', then for the field labeled '1.c. I (select only one box)', the output should be: 'section': 'attorney', 'label': '1.c. I (select only one box)', 'value': 'am'.\n\n"
        "Example for rule 8: If client_type is 'Beneficiary', then for the corresponding field, output: 'section': 'client', 'label': '5. I enter my appearance as an attorney or accredited representative at the request of the (select only one box):', 'value': 'Beneficiary'."
    )), ("user", "HTML:\n{html}\n\nDATA:\n{data}\n\nReturn only the JSON array.")])
    messages = prompt.format_messages(html=html_content, data=json.dumps(data, indent=2))
    model = ChatOpenAI(model='gpt-4o', temperature=0)
    response = await model.ainvoke(messages)
    cleaned = re.search(r"\[.*\]", response.content, re.DOTALL)
    if cleaned:
        try:
            mapping_list = json.loads(cleaned.group(0))
            return [FieldMapping(**item) for item in mapping_list]
        except Exception as e:
            print("❌ LLM parsing failed:", e)
            print("Raw output:\n", response.content)
            return []
    else:
        print("❌ Could not find JSON array in LLM output.")
        print("Raw output:\n", response.content)
        return []


# -------------------------------------------
# DYNAMIC FIELD FILLING (using LLM mapping)
# -------------------------------------------
async def fill_field_dynamic(page, mapping_item: FieldMapping):
    label_text = mapping_item.label
    value = mapping_item.value

    # Special handling for subject_to_restrictions mapping (1.c. I (select only one box))
    if "1.c. I (select only one box)" in label_text:
        normalized = value.strip().lower()  # Expected to be "am" or "am not"
        if normalized == "am":
            am_checkbox = page.locator("#am-subject")
            not_checkbox = page.locator("#not-subject")
            if not await am_checkbox.is_checked():
                await am_checkbox.click()
            if await not_checkbox.is_checked():
                await not_checkbox.click()
            print(f"✅ [Dynamic] Set '1.c. I (select only one box)' to 'am'")
        elif normalized == "am not":
            am_checkbox = page.locator("#am-subject")
            not_checkbox = page.locator("#not-subject")
            if not await not_checkbox.is_checked():
                await not_checkbox.click()
            if await am_checkbox.is_checked():
                await am_checkbox.click()
            print(f"✅ [Dynamic] Set '1.c. I (select only one box)' to 'am not'")
        else:
            print(
                f"⚠️ [Dynamic] Unexpected value '{value}' for '1.c. I (select only one box)'; skipping."
            )
        return

    # Special handling for client_type mapping (appearance checkbox)
    if "I enter my appearance as an attorney" in label_text:
        # Find all checkboxes with name 'client-type'
        checkboxes = page.locator("input[name='client-type']")
        count = await checkboxes.count()
        matched = False
        for i in range(count):
            checkbox = checkboxes.nth(i)
            checkbox_id = await checkbox.get_attribute("id")
            # Get the label associated with this checkbox
            checkbox_label = page.locator(f"label[for='{checkbox_id}']").first
            label_val = (await checkbox_label.inner_text()).strip()
            # If the mock value appears in the label text (case-insensitive), that's our target.
            if value.strip().lower() in label_val.lower():
                if not await checkbox.is_checked():
                    await checkbox.click()
                print(f"✅ [Dynamic] Set appearance checkbox to '{label_val}'")
                matched = True
            else:
                if await checkbox.is_checked():
                    await checkbox.uncheck()
        if not matched:
            print(f"⚠️ [Dynamic] No appearance checkbox label matched client_type value '{value}'")
        return

    if label_text.strip() == "2.d. Additional Information":
        print(f"ℹ️ [Dynamic] Skipping dynamic fill for '{label_text}' (handled statically).")
        return

    try:
        label_locator = page.locator("label", has_text=label_text).first
        if await label_locator.count() == 0:
            print(f"⚠️ [Dynamic] Label '{label_text}' not found; skipping.")
            return
        input_id = await label_locator.get_attribute("for")
        if input_id:
            field_locator = page.locator(f"#{input_id}")
        else:
            field_locator = label_locator.locator(
                "xpath=following-sibling::*[self::input or self::textarea or self::select][1]")
        if await field_locator.count() == 0:
            print(f"⚠️ [Dynamic] Field for '{label_text}' not found; skipping.")
            return
        tag = await field_locator.evaluate("el => el.tagName.toLowerCase()")
        if tag == "input":
            input_type = await field_locator.get_attribute("type")
            if input_type == "checkbox":
                # Generic checkbox handling: if value is empty, uncheck.
                if value.strip() == "":
                    await field_locator.uncheck()
                    print(f"✅ [Dynamic] Left checkbox '{label_text}' unchecked (value empty).")
                else:
                    desired = str(value).strip().lower() in ["yes", "true", "1", "on"]
                    current = await field_locator.is_checked()
                    if current != desired:
                        await field_locator.click()
                    print(f"✅ [Dynamic] Set checkbox '{label_text}' to {desired}")
            else:
                await field_locator.fill(value)
                print(f"✅ [Dynamic] Filled '{label_text}' with '{value}'")
        elif tag == "select":
            await field_locator.select_option(value=value)
            print(f"✅ [Dynamic] Selected '{label_text}' with '{value}'")
        else:
            await field_locator.fill(value)
            print(f"✅ [Dynamic] Filled '{label_text}' with '{value}'")
    except Exception as e:
        print(f"⚠️ [Dynamic] Error processing mapping for '{label_text}': {e}")


# -------------------------------------------
# Minimal Static Fallback: Fill signature dates.
# -------------------------------------------
async def fill_signature_dates(page):
    client_sig = mock_data_all_fields["client"].get("signature_date",
                                                    "") or date.today().strftime("%m/%d/%Y")
    attorney_sig = mock_data_all_fields.get("attorney_signature_date",
                                            "") or date.today().strftime("%m/%d/%Y")
    additional_sig = mock_data_all_fields.get("additional_signature_date",
                                              "") or date.today().strftime("%m/%d/%Y")
    try:
        await page.fill("#client-signature-date", client_sig)
        await page.fill("#attorney-signature-date", attorney_sig)
        await page.fill("#student-signature-date", additional_sig)
        print(
            f"✅ [Static] Filled signature dates: Client: {client_sig}, Attorney: {attorney_sig}, Student: {additional_sig}"
        )
    except Exception as e:
        print("⚠️ [Static] Error filling signature dates:", e)


# -------------------------------------------
# Minimal Static Fallback for Part 6 Additional Info.
# -------------------------------------------
async def apply_static_part6(page):
    try:
        await page.fill("#add-info-family-name",
                        mock_data_all_fields["part6"]["additional_info"]["family_name"])
        await page.fill("#add-info-given-name",
                        mock_data_all_fields["part6"]["additional_info"]["given_name"])
        await page.fill("#add-info-middle-name",
                        mock_data_all_fields["part6"]["additional_info"]["middle_name"])
        print("✅ [Static] Filled Part 6 name fields")
    except Exception as e:
        print("⚠️ [Static] Error filling Part 6 name fields:", e)
    entries_sec2 = mock_data_all_fields["part6"]["additional_info"].get("entries_section_2", [])
    entries_sec3 = mock_data_all_fields["part6"]["additional_info"].get("entries_section_3", [])
    text_sec2 = "\n".join(entry.get("additional_info", "") for entry in entries_sec2)
    text_sec3 = "\n".join(entry.get("additional_info", "") for entry in entries_sec3)
    try:
        if text_sec2.strip():
            await page.fill("#add-info-text-2d", text_sec2)
            print("✅ [Static] Filled Part 6 additional info (section 2) with:", text_sec2)
        if text_sec3.strip():
            await page.fill("#add-info-text-3d", text_sec3)
            print("✅ [Static] Filled Part 6 additional info (section 3) with:", text_sec3)
    except Exception as e:
        print("⚠️ [Static] Error filling Part 6 additional info:", e)


# -------------------------------------------
# Minimal Static Fallback for Unit Info.
# -------------------------------------------
async def fill_unit_info(page, section: str):
    if section == "attorney":
        data = mock_data_all_fields["attorney"]
        unit_value = data.get("unit_type", "").strip().lower()  # e.g. "ste"
        number = data.get("address_line_2", "").strip()
        # Define selectors for all three checkboxes.
        selectors = {"apt": "#apt", "ste": "#ste", "flr": "#flr"}
        desired = unit_value
        # Check the desired checkbox and uncheck the others.
        for key, selector in selectors.items():
            checkbox = page.locator(selector)
            if key == desired:
                if not await checkbox.is_checked():
                    await checkbox.check()
                    print(f"✅ [Static] Checked '{key.upper()}' in attorney section")
            else:
                if await checkbox.is_checked():
                    await checkbox.uncheck()
                    print(f"✅ [Static] Unchecked '{key.upper()}' in attorney section")
        number_selector = "#apt-number"
        if number:
            try:
                int(number)
                await page.fill(number_selector, number)
                print(f"✅ [Static] Filled attorney unit number with '{number}'")
            except ValueError:
                print(
                    f"⚠️ [Static] Attorney unit number '{number}' is not a valid integer; skipping."
                )
    elif section == "client":
        data = mock_data_all_fields["client"]
        if not data.get("unit_type", "").strip():
            data["unit_type"] = mock_data_all_fields["attorney"].get("unit_type", "").strip()
            data["address_line_2"] = mock_data_all_fields["attorney"].get("address_line_2",
                                                                          "").strip()
        unit_value = data.get("unit_type", "").strip().lower()
        number = data.get("address_line_2", "").strip()
        selectors = {"apt": "#client-apt", "ste": "#client-ste", "flr": "#client-flr"}
        desired = unit_value
        for key, selector in selectors.items():
            checkbox = page.locator(selector)
            if key == desired:
                if not await checkbox.is_checked():
                    await checkbox.check()
                    print(f"✅ [Static] Checked '{key.upper()}' in client section")
            else:
                if await checkbox.is_checked():
                    await checkbox.uncheck()
                    print(f"✅ [Static] Unchecked '{key.upper()}' in client section")
        number_selector = "#client-apt-number"
        if number:
            try:
                int(number)
                await page.fill(number_selector, number)
                print(f"✅ [Static] Filled client unit number with '{number}'")
            except ValueError:
                print(
                    f"⚠️ [Static] Client unit number '{number}' is not a valid integer; skipping.")
    else:
        print(f"⚠️ Unknown section '{section}' for unit info.")


# -------------------------------------------
# MAIN FORM FILLING FUNCTION (Entirely LLM-driven)
# -------------------------------------------
async def fill_form(mock_data_input: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        print(f"🌐 Navigating to {TARGET_URL}")
        await page.goto(TARGET_URL)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        await page.wait_for_selector(".form-container", timeout=60000)

        # Get the raw HTML.
        raw_html = await page.content()

        # LLM CALL: Get mapping from raw HTML and mock data.
        llm_mappings = await get_field_mapping_with_llm(raw_html, mock_data_all_fields)
        if llm_mappings:
            print("\n📋 LLM Mappings:")
            for mapping in llm_mappings:
                print(mapping)
                await fill_field_dynamic(page, mapping)
        else:
            print("⚠️ No LLM mappings returned.")

        # Minimal static fallbacks.
        await fill_signature_dates(page)
        await apply_static_part6(page)
        await fill_unit_info(page, "attorney")
        await fill_unit_info(page, "client")

        print("\nℹ️ Skipping signature fields as required by assignment.")

        print("\n✅ Done. Form filled (without signing) but not submitted.")
        await asyncio.sleep(1000000)
        await browser.close()


# -------------------------------------------
# TEST CASE: Run with All Fields Mock Data
# -------------------------------------------
def run_tests():
    test_name = "All Fields Data"
    data = mock_data_all_fields
    print(f"\n================== Running Test Case: {test_name} ==================")
    asyncio.run(fill_form(data))


if __name__ == "__main__":
    run_tests()
