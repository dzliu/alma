import os
import json
from dotenv import load_dotenv, find_dotenv
import re
from typing import List, Dict
from pydantic import BaseModel, validator
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

_ = load_dotenv(find_dotenv())
os.environ["OPENAI_API_KEY"]


class FieldMapping(BaseModel):
    section: str
    label: str
    value: str

    @validator("value", pre=True)
    def ensure_string(cls, v):
        if isinstance(v, bool):
            return "yes" if v else "no"
        return str(v)


class LLMMapper:

    def __init__(self, model_name: str = "gpt-4o", temperature: int = 0):
        self.model_name = model_name
        self.temperature = temperature

    async def get_mapping(self, html_content: str, data: Dict) -> List[FieldMapping]:
        prompt = ChatPromptTemplate.from_messages([("system", (
            "You are an expert form-filling assistant. Analyze the provided HTML and JSON data. "
            "For each fillable field in the form, produce an object with keys section, label, and value. "
            "The section must be one of attorney, client, or part6.\n\n"
            "For checkboxes, please follow these rules exactly:\n\n"
            "1. For the checkbox next to '1.a. I am an attorney eligible to practice law in, and a member in good standing of, "
            "the bar of the highest courts of the following jurisdictions. If you need extra space to complete this section, use the space provided in Part 6. Additional Information.', "
            "output the value from attorney_eligible (output 'yes' if true, or an empty string if false).\n\n"
            "2. For the field labeled '1.c. I (select only one box)', if the JSON value for subject_to_restrictions is 'yes', output 'am'; "
            "if it is 'no', output 'am not'.\n\n"
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
        model = ChatOpenAI(model=self.model_name, temperature=self.temperature)
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
