# Profanity-Compliance-Detector
This project analyzes debt-collection call transcripts to evaluate professionalism, compliance, and call quality. Each call is provided as a structured JSON/YAML file with utterance-level details (speaker, text, stime, etime). The system addresses three tasks:1. Profanity Detection, 2.Privacy &amp; Compliance Violation, 3.Call Quality Metrics


# Features
Question 1 – Profanity Detection
Regex Method: Fast and reliable detection of explicit profanity and obfuscations (f@#k, sh1t, etc.).
LLM Method: Context-aware detection of subtle or indirect profanity.

Question 2 – Privacy & Compliance
Regex Method: Identifies PII such as DOB, SSN, account numbers.
LLM Method: Detects whether an agent disclosed sensitive info before identity verification was completed.

Question 3 – Call Quality Metrics
Computes silence (%) and overtalk (%) based on utterance timestamps.
Interactive visualization in Streamlit (per-call view).


# How to Run the Different Analysis Notebooks
1. Install Requirements:
All notebooks and the Streamlit app share the same dependencies:  pip install -r requirements.txt

2. Run the Regex Notebook:
Open notebooks/Profanity&Compliance(RegEx).ipynb and run all cells.
Input: ZIP of JSON/YAML transcripts.
Output: outputs/regex_summary.csv.

3. Run the LLM Notebook:
Open notebooks/Profane&Compliance(LLM).ipynb.
Get a Gemini API key from Google AI Studio
Save the key in a .env file for your reference and add it in the notebook in this location --> genai.configure(api_key="...")
Run all cells.
Input: ZIP of JSON/YAML transcripts.
Output: outputs/gemini_summary.csv.

4. Run the Visualization Notebook:
Open Call_quality_Metrics_Analysis.ipynb to generate aggregate insights on silence and overtalk distributions.
No API key needed.
Only requires requirements.txt.


# Using the Streamlit Web App

The Streamlit app has been deployed to the cloud and can be accessed here:
(https://profanity-compliance-detector-0.streamlit.app/)]
How it works---
The app consumes the two output CSV files:  outputs/gemini_summary.csv (from the LLM notebook) & outputs/regex_summary.csv (from the regex notebook)
Main Page: Lets you explore Q1 (profanity detection) and Q2 (privacy/compliance violations) with filters for method and entity.
Q3 Visualizer Page: Lets you upload a ZIP of calls or paste a JSON prompt to visualize silence and overtalk metrics for individual calls.

# Technical Report
A detailed report with system design, recommendations, and visualization insights is available in the main branch (Technical Report.pdf)
