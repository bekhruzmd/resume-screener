# Gemini Resume Screener

Welcome to the **Gemini Resume Screener** – your next-level tool to sift through resumes like a boss. Forget endless hours of manual screening. This tool pulls text from PDFs and DOCX files, compares it against your job requirements, and spits out detailed candidate reports. Say hello to a smoother, smarter hiring process.

## What It Does

- **Extracts Resume Data:** Seamlessly reads PDF and DOCX files.
- **Deep Dive Analysis:** Breaks down each resume against your job criteria.
- **Score-Based Filtering:** Calculates an overall score based on skills, experience, and fit.
- **Comprehensive Reporting:** Generates a CSV of results and detailed candidate reports for quick insights.
- **Batch Processing:** Drop your resumes in the folder, and let the tool do the heavy lifting.

## Getting Started

### Prerequisites

- **Python 3.6+** – Make sure you’re running a modern version.
- **Gemini API Key** – This tool uses Gemini for content analysis. Pop your key into your environment (or use a `.env` file).
- A bit of command-line magic and comfort with Python setups.

### Installation

1. **Clone the Repo:**
    ```bash
    git clone https://github.com/yourusername/gemini-resume-screener.git
    cd gemini-resume-screener
    ```

2. **Set Up Your Virtual Environment (Optional but Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure Your API Key:**
    Create a `.env` file in the project root and add:
    ```
    GEMINI_API_KEY=your_gemini_api_key_here
    ```

5. **Add Your Resumes:**
    Create a folder called `resumes` in the root directory and load it up with your PDF/DOCX resumes.

## How to Use

Run the main script, sit back, and watch the magic happen:
```bash
python main.py
