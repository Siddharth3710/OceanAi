📧 OceanAI — Intelligent Email Productivity Agent

A smart AI-powered email assistant built with Streamlit, OpenRouter LLMs, and Python, designed to automate inbox triage, extract action items, draft replies, and provide powerful inbox insights.

🚀 Features
🔍 1. Inbox Processing (AI Categorization + Action Extraction)

Automatically categorizes emails (e.g., Urgent, Reminder, To-Do, Information)

Extracts structured action items using LLMs

Converts free-text tasks into clean JSON

Detects deadlines & key instructions

🤖 2. AI Email Agent

Ask your agent to:

Summarize emails

Extract tasks

Generate clean reply drafts

Provide follow-up recommendations

Answer any custom questions about the email context

📝 3. Auto-Reply Draft Generator

Instantly generate:

Reply subject

Reply body

Optional follow-ups

Clean professional tone

All drafts can be saved for later review.

📊 4. Insights Dashboard

Visual analytics including:

Category distribution

Sender frequency

Email timeline

Keyword analysis

Saved drafts preview

Helps you understand inbox patterns and workload.

📦 5. Clean Project Structure
email_agent/
│── app.py
│── requirements.txt
│── README.md
│── .env (ignored)
│── .env.example
│── core/
│   ├── agent.py
│   ├── processing.py
│   ├── dashboard.py
│   ├── config.py
│   ├── ingest.py
│   └── prompts.py
└── data/
    ├── mock_inbox.json
    ├── prompts.json
    └── processed.json (auto-generated)

🛠️ Installation & Setup
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/OceanAI.git
cd OceanAI

2. Install dependencies
pip install -r requirements.txt

3. Set up environment variables

Create a .env file (already git-ignored):

OPENROUTER_API_KEY=your_openrouter_api_key_here


Never commit your .env.
A safe template is provided in .env.example.

4. Run the app
streamlit run app.py

🔐 Security

✔ .env is ignored via .gitignore
✔ No API keys are stored in the repo
✔ .env.example provides a safe placeholder
✔ All secrets must stay local

🧠 Models Used

Powered by OpenRouter with support for:

google/gemma-2-9b-it (fast, efficient)

Any other model you configure in processing.py or agent.py

📬 Mock Data

You can modify the inbox file located at:

data/mock_inbox.json


This simulates real-world email scenarios for testing.

🤝 Contributing

Contributions are welcome!
Feel free to open:

Issues

Pull Requests

Feature suggestions

📄 License

This project is released under the MIT License.

⭐ Support

If you like this project, please give it a ⭐ on GitHub — it really helps!
