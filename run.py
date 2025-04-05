import asyncio
from form_filler import FormFiller
from data import mock_data_all_fields


def run_tests():
    test_name = "All Fields Data"
    filler = FormFiller("https://mendrika-alma.github.io/form-submission/", mock_data_all_fields)
    print(f"\n================== Running Test Case: {test_name} ==================")
    asyncio.run(filler.fill_form())


if __name__ == "__main__":
    run_tests()
