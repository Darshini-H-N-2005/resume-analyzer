# Resume Analyzer

A Flask-based web application that analyzes resumes using Google's Gemini AI. Upload a resume (PDF), get AI-powered feedback, and generate a clean, professionally formatted PDF report.

## Features
- Resume upload and text extraction (PyPDF2)
- AI-powered analysis using Google Gemini API
- Clean PDF report generation (ReportLab)
- User login and admin dashboard
- Resume builder module

## Tech Stack
- **Backend:** Python, Flask
- **AI:** Google Generative AI (Gemini)
- **PDF Processing:** PyPDF2, ReportLab
- **Frontend:** HTML, CSS, JavaScript

## Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/Darshini-H-N-2005/projects.git
cd projects

2. Create a virtual environment
python -m venv venv
venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Create a .env file in the root folder with:
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=your_secret_key_here

5. Run the app
python app.py
```

## Author
**Aaradhya Shankbal**
