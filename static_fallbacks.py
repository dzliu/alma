from datetime import date
from playwright.async_api import async_playwright
from data import mock_data_all_fields


class StaticFallbacks:

    async def fill_signature_dates(self, page):
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

    async def apply_part6(self, page):
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

    async def fill_unit_info(self, page, section: str):
        if section == "attorney":
            data = mock_data_all_fields["attorney"]
            unit_value = data.get("unit_type", "").strip().lower()
            number = data.get("address_line_2", "").strip()
            selectors = {"apt": "#apt", "ste": "#ste", "flr": "#flr"}
            desired = unit_value
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
                        f"⚠️ [Static] Client unit number '{number}' is not a valid integer; skipping."
                    )
        else:
            print(f"⚠️ Unknown section '{section}' for unit info.")
