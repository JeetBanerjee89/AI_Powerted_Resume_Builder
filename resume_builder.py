#importing libraries
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import streamlit as st
from langchain_core.prompts import PromptTemplate, load_prompt
import pdfkit
import tempfile
import unicodedata
import os
import re
import markdown

#loading environment variables
load_dotenv()

#application header
st.header("AI Powered Resume Builder")

#user inputs
user_input_name = st.text_input("Your Name")
user_input_email = st.text_input("Email")
user_input_phone = st.text_input("Phone Number")
user_input_profile_summary = st.text_area("Enter Your Profile Summary:")
user_input_competencies = st.text_area("Enter Your Competencies:")
user_input_education = st.text_area("Enter Your Educational Qualification:")
user_input_certification = st.text_area("Enter Your Certifications:")
user_input_experience = st.text_area("Enter Your Work Experience:")

#template
template = load_prompt('template.json')

# filling template placeholders
prompt = template.invoke({
    'user_input_profile_summary': user_input_profile_summary,
    'user_input_competencies': user_input_competencies,
    'user_input_education': user_input_education,
    'user_input_certification': user_input_certification,
    'user_input_experience': user_input_experience  
})

#generative model
model = ChatOpenAI(model='gpt-4')

#function to extract sections from GPT-output
def extract_section(text, heading):
    pattern = rf"^##\s+{re.escape(heading)}\s*\n+(.*?)(?=\n##\s+|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else ""

# Set wkhtmltopdf path (Download Link: https://wkhtmltopdf.org/downloads.html)
path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

if st.button("Build Resume"):
    result = model.invoke(prompt)
    resume_markdown = result.content
    resume_html = markdown.markdown(resume_markdown)
    st.subheader("Raw Resume Markdown Output")
    st.code(resume_markdown, language="markdown")

    with open("resume_template.html", "r", encoding="utf-8") as f:
        html_template = f.read()

    resume_markdown = unicodedata.normalize("NFKC", resume_markdown).strip()

    profile_summary = extract_section(resume_markdown, "Profile Summary")
    competencies_raw = extract_section(resume_markdown, "Competencies")
    education = extract_section(resume_markdown, "Education")
    certifications = extract_section(resume_markdown, "Certification")
    experience = extract_section(resume_markdown, "Work Experience")

    competencies_html = "".join([f"<li>{item.strip('- ').strip()}</li>" for item in competencies_raw.splitlines() if item.strip()])

    html_filled = html_template.replace("{{name}}", user_input_name)\
        .replace("{{email}}", user_input_email)\
        .replace("{{phone}}", user_input_phone)\
        .replace("{{summary}}", profile_summary)\
        .replace("{{competencies}}", competencies_html)\
        .replace("{{education}}", education)\
        .replace("{{certifications}}", certifications)\
        .replace("{{experience}}", experience)

    # Save HTML to a temp file and convert to PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
        tmp_html.write(html_filled)
        tmp_html_path = tmp_html.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdfkit.from_file(tmp_html_path, tmp_pdf.name, configuration=config)
        pdf_path = tmp_pdf.name

    # Let user download
    with open(pdf_path, "rb") as f:
        st.download_button("Download Resume as PDF", f, "resume.pdf", "application/pdf")