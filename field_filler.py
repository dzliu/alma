from llm_mapper import FieldMapping


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
            # If the mock value (e.g. 'Beneficiary') appears in the label text (case-insensitive), that's our target.
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
