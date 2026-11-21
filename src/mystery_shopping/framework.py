"""Mystery shopping evaluation framework: channels, service-quality dimensions, criteria and weights.

This is a generic, independently designed framework for evaluating a public-facing judicial
services entity. It is not taken from, and does not reproduce, any client's internal framework.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw" / "mystery_shopper_observations_SYNTHETIC_raw.csv"
DATA_CLEAN = ROOT / "data" / "processed" / "mystery_shopper_observations_SYNTHETIC_clean.csv"
CLEANING_LOG = ROOT / "data" / "processed" / "cleaning_log.csv"
FIGURES = ROOT / "outputs" / "figures"
TABLES = ROOT / "outputs" / "tables"
SCORECARDS = ROOT / "outputs" / "scorecards"
POWERBI = ROOT / "powerbi"
TEMPLATES = ROOT / "questionnaires"
REPORTS = ROOT / "reports"

SEED = 2025
CHANNELS = ["Email", "Telephone", "Social media", "Registry", "Ancillary services"]
CHANNEL_GROUP = {"Email": "Remote", "Telephone": "Remote", "Social media": "Remote", "Registry": "In person", "Ancillary services": "In person"}
WAVES = ["Wave 1", "Wave 2"]

DIMENSIONS = ["Response time", "Communication quality", "Professionalism", "Information accuracy", "Resolution effectiveness", "Customer experience"]
# Dimension weights in the overall Service Quality Index (sum = 1)
DIMENSION_WEIGHTS = {"Response time": 0.15, "Communication quality": 0.15, "Professionalism": 0.15,
                     "Information accuracy": 0.25, "Resolution effectiveness": 0.20, "Customer experience": 0.10}
TARGET_SCORE = 80  # dimension / index score regarded as meeting the service standard (0-100)

# Response-time service standards per channel (an illustrative assumption, in minutes)
RESPONSE_STANDARD_MIN = {"Email": 1440, "Telephone": 1, "Social media": 120, "Registry": 15, "Ancillary services": 20}
RESPONSE_UNIT = {"Email": "minutes to first reply", "Telephone": "minutes until answered by a person", "Social media": "minutes to first reply",
                 "Registry": "minutes waiting before being served", "Ancillary services": "minutes waiting before being served"}

SCENARIOS = {
    "Email": ["Filing procedure enquiry", "Court fee enquiry", "Request for case status guidance", "Document requirements for a claim"],
    "Telephone": ["Hearing date enquiry", "Court fee enquiry", "How to submit an appeal", "Opening hours and location"],
    "Social media": ["General service enquiry", "E-services login help", "Accessibility enquiry", "Complaint escalation"],
    "Registry": ["Submitting documents at the counter", "Certified copy request", "Case file inspection request", "Payment of court fees"],
    "Ancillary services": ["Translation service enquiry", "Notarisation / attestation", "Mediation information session", "Visitor and accessibility support"],
}

# Criteria: (id, dimension, question, channels it applies to). Each is scored 0 (No), 1 (Partly), 2 (Yes).
CRITERIA = [
    ("RT1", "Response time", "Was the first response received within the service standard for this channel?", CHANNELS),
    ("RT2", "Response time", "Was an expected resolution time communicated?", CHANNELS),
    ("CQ1", "Communication quality", "Was the response clear and free of unexplained jargon?", CHANNELS),
    ("CQ2", "Communication quality", "Was the response offered or provided in the customer's preferred language (Arabic / English)?", CHANNELS),
    ("CQ3", "Communication quality", "Was the written response well structured and free of errors?", ["Email", "Social media"]),
    ("CQ4", "Communication quality", "Did the agent listen without interrupting and confirm understanding?", ["Telephone", "Registry", "Ancillary services"]),
    ("PR1", "Professionalism", "Was the customer greeted courteously and addressed respectfully?", CHANNELS),
    ("PR2", "Professionalism", "Did the staff member identify themselves (name or ID)?", ["Telephone", "Registry", "Ancillary services", "Email"]),
    ("PR3", "Professionalism", "Did the staff member keep a neutral, impartial tone (no legal advice given)?", CHANNELS),
    ("IA1", "Information accuracy", "Was the information provided correct against the published procedure?", CHANNELS),
    ("IA2", "Information accuracy", "Was the information complete (documents, fees, timelines)?", CHANNELS),
    ("IA3", "Information accuracy", "Was the customer directed to the correct official page, form or e-service?", CHANNELS),
    ("RE1", "Resolution effectiveness", "Was the enquiry resolved at first contact?", CHANNELS),
    ("RE2", "Resolution effectiveness", "If not resolved, was a clear next step or referral given?", CHANNELS),
    ("RE3", "Resolution effectiveness", "Was the transaction completed correctly (documents accepted, receipt issued)?", ["Registry", "Ancillary services"]),
    ("CX1", "Customer experience", "Was the environment / channel easy to use (signage, menus, accessibility)?", CHANNELS),
    ("CX2", "Customer experience", "Did the interaction feel efficient overall?", CHANNELS),
]


def criteria_for(channel: str) -> list[tuple]:
    return [c for c in CRITERIA if channel in c[3]]
