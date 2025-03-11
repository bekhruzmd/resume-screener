import os
import re
import pandas as pd
import PyPDF2
from docx import Document
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables for API keys
load_dotenv()

# Configure the Gemini AI API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No Gemini API key found. Please set the GEMINI_API_KEY environment variable.")

# Updated Gemini configuration with correct model name
genai.configure(api_key=GEMINI_API_KEY)
# Use the correct model name - gemini-1.5-pro or gemini-1.0-pro based on availability
model = genai.GenerativeModel('gemini-1.5-pro')  # Try this first
# Fallback option in case the above model isn't available
# model = genai.GenerativeModel('gemini-1.0-pro')

class GeminiResumeScreener:
    def __init__(self, job_description, skills_required, experience_years=0):
        """
        Initialize the resume screener with job requirements
        
        Parameters:
        - job_description: String containing detailed job description
        - skills_required: List of critical skills for the position
        - experience_years: Minimum years of experience required
        """
        self.job_description = job_description
        self.skills_required = skills_required
        self.experience_years = experience_years
        
        # Dictionary to store results
        self.results = {}
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF files"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _extract_text_from_docx(self, docx_path):
        """Extract text from DOCX files"""
        try:
            # Fixed docx handling
            doc = Document(docx_path)
            text = " ".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX {docx_path}: {e}")
            return ""
    
    def _analyze_resume_with_gemini(self, resume_text):
        """
        Use Gemini AI to analyze the resume and extract relevant information
        """
        # Trim resume text if it's too long (Gemini has input limits)
        max_length = 30000  # Safe length for input
        if len(resume_text) > max_length:
            resume_text = resume_text[:max_length]
        
        prompt = f"""
        Analyze the following resume against the job requirements. 
        
        JOB DESCRIPTION:
        {self.job_description}
        
        REQUIRED SKILLS:
        {', '.join(self.skills_required)}
        
        MINIMUM YEARS OF EXPERIENCE:
        {self.experience_years}
        
        RESUME:
        {resume_text}
        
        Please provide a JSON response with the following structure:
        {{
            "skills_found": ["list", "of", "skills", "found", "in", "resume"],
            "skills_match_percent": percentage_of_required_skills_found,
            "experience_years": estimated_years_of_work_experience,
            "experience_match": boolean_if_experience_meets_requirements,
            "strengths": ["list", "of", "candidate", "strengths"],
            "weaknesses": ["list", "of", "candidate", "weaknesses"],
            "relevance_score": score_from_0_to_100_on_overall_job_fit,
            "additional_insights": "any_additional_insights_about_the_candidate"
        }}
        
        Analyze the resume thoroughly and be accurate in your assessment.
        """
        
        try:
            response = model.generate_content(prompt)
            result = response.text
            
            # Extract JSON from response (handling potential formatting issues)
            import json
            # Find JSON content in the response
            json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result
            
            # Clean up the string to ensure it's valid JSON
            json_str = re.sub(r'[^\x00-\x7F]', '', json_str)  # Remove non-ASCII characters
            json_str = re.sub(r'```', '', json_str)  # Remove any remaining markdown code blocks
            
            # Parse JSON
            analysis = json.loads(json_str)
            return analysis
            
        except Exception as e:
            print(f"Error analyzing resume with Gemini AI: {e}")
            # Return default values if AI analysis fails
            return {
                "skills_found": [],
                "skills_match_percent": 0,
                "experience_years": 0,
                "experience_match": False,
                "strengths": [],
                "weaknesses": ["Unable to analyze resume properly"],
                "relevance_score": 0,
                "additional_insights": "Error occurred during AI analysis"
            }
    
    def process_resume(self, file_path):
        """Process a single resume file"""
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract text based on file type
        if file_ext == '.pdf':
            resume_text = self._extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            resume_text = self._extract_text_from_docx(file_path)
        else:
            print(f"Unsupported file format: {file_ext}")
            return None
        
        if not resume_text:
            print(f"Could not extract text from {file_path}")
            return None
        
        print(f"Processing resume: {file_name}")
        
        # Analyze resume using Gemini AI
        analysis = self._analyze_resume_with_gemini(resume_text)
        
        # Calculate overall match score
        # 40% weight to skills, 30% to experience, 30% to relevance
        overall_score = (
            (analysis.get("skills_match_percent", 0) * 0.4) + 
            (analysis.get("experience_match", False) * 30) + 
            (analysis.get("relevance_score", 0) * 0.3)
        )
        
        # Store results
        result = {
            'file_name': file_name,
            'skills_found': analysis.get("skills_found", []),
            'skills_match_percent': analysis.get("skills_match_percent", 0),
            'experience_years': analysis.get("experience_years", 0),
            'experience_match': analysis.get("experience_match", False),
            'strengths': analysis.get("strengths", []),
            'weaknesses': analysis.get("weaknesses", []),
            'relevance_score': analysis.get("relevance_score", 0),
            'additional_insights': analysis.get("additional_insights", ""),
            'overall_score': overall_score,
            'qualified': overall_score >= 70  # Consider candidates with 70+ score as qualified
        }
        
        self.results[file_path] = result
        return result
    
    def process_resume_directory(self, directory_path):
        """Process all resumes in a directory"""
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path) and file_path.lower().endswith(('.pdf', '.docx', '.doc')):
                self.process_resume(file_path)
    
    def get_top_candidates(self, n=5):
        """Return top N candidates based on overall score"""
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]['overall_score'],
            reverse=True
        )
        
        return sorted_results[:n]
    
    def export_results(self, output_path='resume_screening_results.csv'):
        """Export screening results to CSV"""
        results_list = []
        for file_path, result in self.results.items():
            row = {
                'file_name': result['file_name'],
                'skills_found': ', '.join(result['skills_found']),
                'skills_match_percent': result['skills_match_percent'],
                'experience_years': result['experience_years'],
                'strengths': ', '.join(result['strengths']),
                'weaknesses': ', '.join(result['weaknesses']),
                'relevance_score': result['relevance_score'],
                'additional_insights': result['additional_insights'],
                'overall_score': result['overall_score'],
                'qualified': result['qualified']
            }
            results_list.append(row)
        
        df = pd.DataFrame(results_list)
        df.to_csv(output_path, index=False)
        print(f"Results exported to {output_path}")
        
        return df

    def generate_candidate_report(self, file_path):
        """Generate a detailed report for a specific candidate"""
        if file_path not in self.results:
            print(f"No results found for {file_path}")
            return None
        
        result = self.results[file_path]
        
        prompt = f"""
        Generate a detailed candidate assessment report based on the following analysis:
        
        Candidate: {result['file_name']}
        Skills Found: {', '.join(result['skills_found'])}
        Skills Match: {result['skills_match_percent']}%
        Experience: {result['experience_years']} years
        Strengths: {', '.join(result['strengths'])}
        Weaknesses: {', '.join(result['weaknesses'])}
        Relevance Score: {result['relevance_score']}%
        Additional Insights: {result['additional_insights']}
        Overall Score: {result['overall_score']}%
        Qualified: {'Yes' if result['qualified'] else 'No'}
        
        The report should include:
        1. Executive summary
        2. Detailed skills assessment
        3. Experience evaluation
        4. Strengths and weaknesses analysis
        5. Recommendation for next steps (interview, reject, or keep in pool)
        """
        
        try:
            response = model.generate_content(prompt)
            report = response.text
            return report
        except Exception as e:
            print(f"Error generating candidate report: {e}")
            return "Unable to generate candidate report."


# Example usage
if __name__ == "__main__":
    # Sample job description and required skills
    job_description = """
    We are looking for a Front-End Developer to join our team. The ideal candidate has strong 
    experience with React, JavaScript, HTML, and CSS. Knowledge of responsive design principles 
    and experience with UI/UX best practices is essential. Familiarity with state management 
    solutions like Redux is a plus. The candidate should have at least 2 years of experience 
    in a similar role.
    """
    
    required_skills = [
        "JavaScript", "React", "HTML", "CSS", "Responsive Design", 
        "UI/UX", "Redux", "Git"
    ]
    
    # Initialize the screener
    screener = GeminiResumeScreener(
        job_description=job_description,
        skills_required=required_skills,
        experience_years=2
    )
    
    # Process resumes in a directory
    resumes_dir =  os.path.join(os.path.dirname(__file__), "resumes")  # Change this to your directory containing resumes
    if os.path.exists(resumes_dir):
        print(f"Found resumes directory. Processing files...")
        screener.process_resume_directory(resumes_dir)
        
        if len(screener.results) == 0:
            print("No resume files were successfully processed. Please check your resume files and formats.")
        else:
            # Get top candidates
            top_candidates = screener.get_top_candidates(n=5)
            print(f"\nSuccessfully processed {len(screener.results)} resumes.")
            print("\nTop Candidates:")
            for i, (file_path, result) in enumerate(top_candidates, 1):
                print(f"{i}. {result['file_name']} - Score: {result['overall_score']:.2f}%")
                print(f"   Skills: {', '.join(result['skills_found'])}")
                print(f"   Experience: {result['experience_years']} years")
                print(f"   Strengths: {', '.join(result['strengths'])}")
                print(f"   Qualified: {'Yes' if result['qualified'] else 'No'}")
                print()
                
                # Generate detailed report for top candidates
                if i <= 3:  # Generate reports only for top 3 candidates
                    print(f"   Generating detailed report for candidate {i}...")
                    report = screener.generate_candidate_report(file_path)
                    report_file = f"report_{result['file_name'].split('.')[0]}.txt"
                    with open(report_file, 'w') as f:
                        f.write(report)
                    print(f"   Detailed report saved to {report_file}")
                print()
            
            # Export results
            screener.export_results()
    else:
        print(f"Directory '{resumes_dir}' not found. Please create a folder named 'resumes' and add your resume files.")