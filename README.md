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

