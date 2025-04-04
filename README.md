# alma
exercise for alma interview

# 🤖 Web Agent Autofill with LLM + Playwright

This project demonstrates a web automation agent that uses an LLM (GPT-4) to navigate to a web form and automatically fill it out using structured mock data. It simulates real-world tasks like document automation, intelligent form filling, and data entry.

---

## 🌐 Target Form

We are using the following test form provided in the assignment:

**🔗 https://mendrika-alma.github.io/form-submission/**

---

## 📦 Project Structure
web-agent-autofill/
├── form_filler.py        # Main script to run the agent
├── requirements.txt      # Python dependencies
└── README.md             # Project instructions (this file)

---

## 🚀 Features

- 🧠 Uses **OpenAI GPT-4** to intelligently map JSON data fields to form inputs
- 🧭 Navigates and fills out the form using **Playwright**
- ✅ Handles minor label or layout changes using LLM reasoning
- 🔐 Keeps the form private — no submission or public data exposure
- 📄 Easily extendable for other forms or data schemas

---

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Playwright browser driver

---

## 🛠️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/web-agent-autofill.git
cd web-agent-autofill
```
### 2. Install dependencies

pip install -r requirements.txt
playwright install

### 3. Add your OpenAI API key

Ensure you have the OpenAPI key defined in the .env file

### 4. Run the script

python form_filler.py

This will:
	•	Launch the browser
	•	Load the test form
	•	Send the form structure and mock data to GPT-4
	•	Fill in the form fields based on LLM output

🔒 The form is not submitted — as required by the assignment instructions.

⸻

🧪 Sample Mock Data

The agent currently uses attorney-related data like:

{
  "first_name": "John",
  "family_name": "Doe",
  "email": "mdoe@legalfirm.com",
  "city": "Boston"
}

This can be easily extended to include additional sections like client, part6, etc.


