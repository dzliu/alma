# data.py
mock_data_all_fields = {
    "attorney": {
        "online_account_number": "A987654321",
        "family_name": "Smith",
        "first_name": "Alice",
        "middle_name": "B.",
        "address_line_1": "789 Corporate Blvd",
        "unit_type": "ste",  # Use "ste" for suite.
        "address_line_2": "202",  # Unit number
        "city": "New York",
        "state": "New York",
        "zip_code": "10001",
        "province": "NY Province",
        "country": "United States",
        "daytime_phone": "(212) 555-6789",
        "email": "alice.smith@corporate.com",
        "fax": "2125559876",
        "attorney_eligible": "no",  # Example: "no" means the checkbox should not be checked.
        "licensing_state": "NY",
        "bar_number": "NY123456",
        "subject_to_restrictions": "yes",  # Should check "am" in 1.c.
        "law_firm": "Doe & Associates Legal Group",
        "is_nonprofit_rep": True,
        "org_name": "Smith Legal Group",
        "recognized_org": "Doe & Associates Legal Group",
        "associated_with_name": "Former Attorney",
        "accreditation_date": "04/15/2020",
        "associated_with_student": "yes",
        "law_student": "",
        "administrative_case": False,
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
        "send_notices_to_attorney": "N",
        "send_documents_to_attorney": "Y",
        "send_documents_to_client": "Y",
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
