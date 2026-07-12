import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || (window.location.port === '5173' ? 'http://localhost:8000' : '');
const VERSION = '1.2.53';

const FEEDBACK_TEXT_KN = {
  "Film": "ಚಿತ್ರ",
  "Post-Screening Audience Survey": "ಪ್ರದರ್ಶನದ ನಂತರದ ಪ್ರೇಕ್ಷಕರ ಅಭಿಪ್ರಾಯ",
  "This survey is for audience members after the screening. Phone number is used only for reference and will not be validated against registration.": "ಈ ಅಭಿಪ್ರಾಯ ಫಾರ್ಮ್ ಪ್ರದರ್ಶನದ ನಂತರ ಪ್ರೇಕ್ಷಕರಿಗಾಗಿ. ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ಕೇವಲ ಉಲ್ಲೇಖಕ್ಕಾಗಿ ಬಳಸಲಾಗುತ್ತದೆ.",
  "Language": "ಭಾಷೆ",
  "Kannada": "ಕನ್ನಡ",
  "English": "English",
  "Name": "ಹೆಸರು",
  "Full name": "ಪೂರ್ಣ ಹೆಸರು",
  "Phone Number / Reference": "ಮೊಬೈಲ್ ಸಂಖ್ಯೆ / ಉಲ್ಲೇಖ",
  "Optional phone number or reference ID": "ಐಚ್ಛಿಕ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಉಲ್ಲೇಖ ಸಂಖ್ಯೆ",
  "Consent to contact for further discussion": "ಹೆಚ್ಚಿನ ಚರ್ಚೆಗೆ ಸಂಪರ್ಕಿಸಲು ಒಪ್ಪಿಗೆ",
  "Overall Experience": "ಒಟ್ಟಾರೆ ಅನುಭವ",
  "Story": "ಕಥೆ",
  "Acting / Performances": "ನಟನೆ / ಅಭಿನಯ",
  "Music / Sound": "ಸಂಗೀತ / ಧ್ವನಿ",
  "Pace / Editing": "ವೇಗ / ಸಂಕಲನ",
  "Emotional Impact": "ಭಾವನಾತ್ಮಕ ಪರಿಣಾಮ",
  "Visual Quality / Cinematography": "ದೃಶ್ಯ ಗುಣಮಟ್ಟ / ಛಾಯಾಗ್ರಹಣ",
  "Dialogues": "ಸಂಭಾಷಣೆ",
  "Film Length": "ಚಿತ್ರದ ಅವಧಿ",
  "Did you understand the story clearly?": "ಕಥೆ ನಿಮಗೆ ಸ್ಪಷ್ಟವಾಗಿ ಅರ್ಥವಾಯಿತೇ?",
  "Did you connect with the characters?": "ಪಾತ್ರಗಳೊಂದಿಗೆ ನೀವು ಸಂಪರ್ಕ ಹೊಂದಿದಂತೆ ಅನಿಸಿತೇ?",
  "Theatre or OTT fit?": "ಚಿತ್ರಮಂದಿರ ಅಥವಾ OTTಗೆ ಸೂಕ್ತವೇ?",
  "Audience Type": "ಪ್ರೇಕ್ಷಕರ ಪ್ರಕಾರ",
  "One-word reaction": "ಒಂದು ಪದದಲ್ಲಿ ಪ್ರತಿಕ್ರಿಯೆ",
  "Who is the right audience for this film?": "ಈ ಚಿತ್ರಕ್ಕೆ ಸರಿಯಾದ ಪ್ರೇಕ್ಷಕರು ಯಾರು?",
  "Can we use a short quote from your feedback?": "ನಿಮ್ಮ ಅಭಿಪ್ರಾಯದಿಂದ ಚಿಕ್ಕ ಉಲ್ಲೇಖವನ್ನು ಬಳಸಬಹುದೇ?",
  "Would you recommend this film?": "ಈ ಚಿತ್ರವನ್ನು ನೀವು ಶಿಫಾರಸು ಮಾಡುತ್ತೀರಾ?",
  "Can we contact you for detailed feedback?": "ವಿಸ್ತೃತ ಅಭಿಪ್ರಾಯಕ್ಕಾಗಿ ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಬಹುದೇ?",
  "What did you like the most?": "ನಿಮಗೆ ಹೆಚ್ಚು ಇಷ್ಟವಾದುದು ಏನು?",
  "What can be improved?": "ಏನು ಸುಧಾರಿಸಬಹುದು?",
  "Any memorable scene, character, or moment?": "ನೆನಪಿನಲ್ಲಿ ಉಳಿದ ದೃಶ್ಯ, ಪಾತ್ರ ಅಥವಾ ಕ್ಷಣ?",
  "Additional Remarks": "ಹೆಚ್ಚುವರಿ ಟಿಪ್ಪಣಿಗಳು",
  "Submitting...": "ಸಲ್ಲಿಸಲಾಗುತ್ತಿದೆ...",
  "Submit Feedback": "ಅಭಿಪ್ರಾಯ ಸಲ್ಲಿಸಿ",
  "Select": "ಆಯ್ಕೆಮಾಡಿ",
  "Thank you. Your feedback has been recorded.": "ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಅಭಿಪ್ರಾಯ ದಾಖಲಿಸಲಾಗಿದೆ.",
  "Excellent": "ಅತ್ಯುತ್ತಮ",
  "Good": "ಚೆನ್ನಾಗಿದೆ",
  "Average": "ಸರಾಸರಿ",
  "Weak": "ದುರ್ಬಲ",
  "Poor": "ಕಳಪೆ",
  "Story & Emotions": "ಕಥೆ ಮತ್ತು ಭಾವನೆಗಳು",
  "Pace & Editing": "ವೇಗ ಮತ್ತು ಸಂಕಲನ",
  "Audience Fit": "ಪ್ರೇಕ್ಷಕರಿಗೆ ಸೂಕ್ತತೆ",
  "One Honest Line": "ಒಂದು ನಿಷ್ಠಾವಂತ ಸಾಲು",
  "Expectations & First Reaction": "ನಿರೀಕ್ಷೆಗಳು ಮತ್ತು ಮೊದಲ ಪ್ರತಿಕ್ರಿಯೆ",
  "Story & Narrative": "ಕಥೆ ಮತ್ತು ನಿರೂಪಣೆ",
  "Characters & Performances": "ಪಾತ್ರಗಳು ಮತ್ತು ಅಭಿನಯ",
  "Pace, Length & Editing": "ವೇಗ, ಅವಧಿ ಮತ್ತು ಸಂಕಲನ",
  "Emotional Connect": "ಭಾವನಾತ್ಮಕ ಸಂಪರ್ಕ",
  "Music, Sound & Visuals": "ಸಂಗೀತ, ಧ್ವನಿ ಮತ್ತು ದೃಶ್ಯಗಳು",
  "Overall Opinion": "ಒಟ್ಟಾರೆ ಅಭಿಪ್ರಾಯ",
  "Audience Recommendation": "ಪ್ರೇಕ್ಷಕರಿಗೆ ಶಿಫಾರಸು",
  "Final Feedback": "ಅಂತಿಮ ಅಭಿಪ್ರಾಯ",
  "What were your expectations before watching the film?": "ಚಿತ್ರ ನೋಡುವ ಮೊದಲು ನಿಮ್ಮ ನಿರೀಕ್ಷೆಗಳು ಏನಾಗಿದ್ದವು?",
  "What was your first reaction after watching the film?": "ಚಿತ್ರ ನೋಡಿದ ನಂತರ ನಿಮ್ಮ ಮೊದಲ ಪ್ರತಿಕ್ರಿಯೆ ಏನು?",
  "Did the film meet your expectations?": "ಚಿತ್ರ ನಿಮ್ಮ ನಿರೀಕ್ಷೆಗಳನ್ನು ಪೂರೈಸಿತೇ?",
  "Which part of the story worked best for you?": "ಕಥೆಯ ಯಾವ ಭಾಗ ನಿಮಗೆ ಹೆಚ್ಚು ಚೆನ್ನಾಗಿ ಕೆಲಸ ಮಾಡಿತು?",
  "Which part of the story did not work for you?": "ಕಥೆಯ ಯಾವ ಭಾಗ ನಿಮಗೆ ಅಷ್ಟಾಗಿ ಕೆಲಸ ಮಾಡಲಿಲ್ಲ?",
  "Was any part of the story confusing?": "ಕಥೆಯ ಯಾವುದಾದರೂ ಭಾಗ ಗೊಂದಲಕಾರಕವಾಗಿತ್ತೇ?",
  "Did the grandfather and grandson relationship connect with you?": "ತಾತ ಮತ್ತು ಮೊಮ್ಮಗನ ಸಂಬಂಧ ನಿಮಗೆ ಮನಸಿಗೆ ತಟ್ಟಿತೇ?",
  "Did the grandfather and grandson bonding work for you?": "ತಾತ ಮತ್ತು ಮೊಮ್ಮಗನ ಬಾಂಧವ್ಯ ನಿಮಗೆ ಚೆನ್ನಾಗಿ ತಟ್ಟಿತೇ?",
  "Which character did you like the most?": "ಯಾವ ಪಾತ್ರ ನಿಮಗೆ ಹೆಚ್ಚು ಇಷ್ಟವಾಯಿತು?",
  "Which character did you not connect with?": "ಯಾವ ಪಾತ್ರದೊಂದಿಗೆ ನೀವು ಸಂಪರ್ಕ ಹೊಂದಲಿಲ್ಲ?",
  "How were the performances?": "ಅಭಿನಯ ಹೇಗಿತ್ತು?",
  "Did any performance stand out?": "ಯಾವುದಾದರೂ ಅಭಿನಯ ವಿಶೇಷವಾಗಿ ಗಮನ ಸೆಳೆಯಿತೇ?",
  "Did the film feel slow anywhere?": "ಚಿತ್ರ ಯಾವುದಾದರೂ ಕಡೆ ನಿಧಾನವೆನಿಸಿತೇ?",
  "Which portions felt slow?": "ಯಾವ ಭಾಗಗಳು ನಿಧಾನವೆನಿಸಿತು?",
  "Which scenes felt slow?": "ಯಾವ ದೃಶ್ಯಗಳು ನಿಧಾನವೆನಿಸಿತು?",
  "What would you remove or shorten?": "ನೀವು ಏನು ತೆಗೆದುಹಾಕಲು ಅಥವಾ ಕಡಿಮೆ ಮಾಡಲು ಬಯಸುತ್ತೀರಿ?",
  "Was the film length right?": "ಚಿತ್ರದ ಅವಧಿ ಸರಿಯಾಗಿತ್ತೇ?",
  "Did the emotional moments work for you?": "ಭಾವನಾತ್ಮಕ ಕ್ಷಣಗಳು ನಿಮಗೆ ತಟ್ಟಿತೇ?",
  "Which emotional moment worked best?": "ಯಾವ ಭಾವನಾತ್ಮಕ ಕ್ಷಣ ಹೆಚ್ಚು ಪರಿಣಾಮಕಾರಿಯಾಗಿತ್ತು?",
  "Did you feel connected to the journey from Mysore to Jaipur?": "ಮೈಸೂರುದಿಂದ ಜೈಪುರದ ಪ್ರಯಾಣದೊಂದಿಗೆ ನಿಮಗೆ ಸಂಪರ್ಕ ಮೂಡಿತೇ?",
  "Did the travel journey work for you?": "ಪ್ರಯಾಣದ ಭಾಗ ನಿಮಗೆ ಕೆಲಸ ಮಾಡಿತೇ?",
  "How was the music?": "ಸಂಗೀತ ಹೇಗಿತ್ತು?",
  "How was the background score?": "ಹಿನ್ನೆಲೆ ಸಂಗೀತ ಹೇಗಿತ್ತು?",
  "How were the visuals and cinematography?": "ದೃಶ್ಯಗಳು ಮತ್ತು ಛಾಯಾಗ್ರಹಣ ಹೇಗಿತ್ತು?",
  "How was the sound design?": "ಧ್ವನಿ ವಿನ್ಯಾಸ ಹೇಗಿತ್ತು?",
  "What did you not like?": "ನಿಮಗೆ ಏನು ಇಷ್ಟವಾಗಲಿಲ್ಲ?",
  "What would you change in the film?": "ಚಿತ್ರದಲ್ಲಿ ನೀವು ಏನು ಬದಲಾಯಿಸುತ್ತೀರಿ?",
  "Would you recommend this film to others?": "ಈ ಚಿತ್ರವನ್ನು ನೀವು ಇತರರಿಗೆ ಶಿಫಾರಸು ಮಾಡುತ್ತೀರಾ?",
  "Would this film work in theatres?": "ಈ ಚಿತ್ರ ಚಿತ್ರಮಂದಿರಗಳಲ್ಲಿ ಕೆಲಸ ಮಾಡುತ್ತದೆಯೇ?",
  "Would this film work on OTT?": "ಈ ಚಿತ್ರ OTTಯಲ್ಲಿ ಕೆಲಸ ಮಾಡುತ್ತದೆಯೇ?",
  "Write one honest line to the director.": "ನಿರ್ದೇಶಕರಿಗೆ ಒಂದು ನಿಷ್ಠಾವಂತ ಸಾಲು ಬರೆಯಿರಿ.",
  "Write one honest line to the editor.": "ಸಂಕಲನಕಾರರಿಗೆ ಒಂದು ನಿಷ್ಠಾವಂತ ಸಾಲು ಬರೆಯಿರಿ.",
  "Any final comments?": "ಕೊನೆಯಾಗಿ ಹೇಳಲು ಏನಾದರೂ ಇದೆಯೇ?",
  "Any other feedback?": "ಇನ್ನೇನಾದರೂ ಅಭಿಪ್ರಾಯ ಇದೆಯೇ?",
  "Additional feedback": "ಹೆಚ್ಚುವರಿ ಅಭಿಪ್ರಾಯ",
  "Please explain": "ದಯವಿಟ್ಟು ವಿವರಿಸಿ",
  "Why?": "ಏಕೆ?",
  "Explain briefly": "ಸಂಕ್ಷಿಪ್ತವಾಗಿ ವಿವರಿಸಿ",
  "After Screening: Honest Film Feedback": "ಪ್ರದರ್ಶನದ ನಂತರ: ನಿಷ್ಠಾವಂತ ಚಿತ್ರದ ಅಭಿಪ್ರಾಯ",
  "Be direct. This helps the makers improve positioning and edits.": "ನೇರವಾಗಿ ಹೇಳಿ. ಇದು ನಿರ್ಮಾಪಕರಿಗೆ ಚಿತ್ರದ ಸ್ಥಾನೀಕರಣ ಮತ್ತು ಸಂಕಲನವನ್ನು ಸುಧಾರಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
  "What are the strongest/highest points of the film?": "ಚಿತ್ರದ ಅತ್ಯಂತ ಬಲವಾದ / ಉತ್ತಮ ಅಂಶಗಳು ಯಾವುವು?",
  "What are the weakest/lowest points of the film?": "ಚಿತ್ರದ ದುರ್ಬಲ / ಕಡಿಮೆ ಕೆಲಸ ಮಾಡಿದ ಅಂಶಗಳು ಯಾವುವು?",
  "What did you not like or find unconvincing?": "ನಿಮಗೆ ಏನು ಇಷ್ಟವಾಗಲಿಲ್ಲ ಅಥವಾ ನಂಬಿಕೆಯಾಗಲಿಲ್ಲ?",
  "How strong is the grandfather-grandson emotional bonding?": "ತಾತ ಮತ್ತು ಮೊಮ್ಮಗನ ಭಾವನಾತ್ಮಕ ಬಾಂಧವ್ಯ ಎಷ್ಟು ಬಲವಾಗಿದೆ?",
  "How engaging is the antique camera journey from Mysore to Jaipur?": "ಮೈಸೂರುದಿಂದ ಜೈಪುರದವರೆಗೆ ನಡೆಯುವ ಪುರಾತನ ಕ್ಯಾಮೆರಾ ಪ್ರಯಾಣ ಎಷ್ಟು ಹಿಡಿದಿಡುತ್ತದೆ?",
  "Pace, Length & Removal Suggestions": "ವೇಗ, ಅವಧಿ ಮತ್ತು ತೆಗೆದುಹಾಕುವ ಸಲಹೆಗಳು",
  "Tell us what felt slow, unnecessary, or confusing.": "ನಿಧಾನ, ಅನಗತ್ಯ ಅಥವಾ ಗೊಂದಲಕಾರಕವೆನಿಸಿದ ಭಾಗಗಳನ್ನು ನಮಗೆ ತಿಳಿಸಿ.",
  "Which portions felt slow? Mention scenes or broad parts.": "ಯಾವ ಭಾಗಗಳು ನಿಧಾನವೆನಿಸಿತು? ದೃಶ್ಯಗಳು ಅಥವಾ ಪ್ರಮುಖ ಭಾಗಗಳನ್ನು ಉಲ್ಲೇಖಿಸಿ.",
  "What would you remove, shorten, or rewrite?": "ನೀವು ಏನು ತೆಗೆದುಹಾಕಲು, ಕಡಿಮೆ ಮಾಡಲು ಅಥವಾ ಮರುಬರೆಯಲು ಬಯಸುತ್ತೀರಿ?",
  "Was any part confusing or unclear?": "ಯಾವುದಾದರೂ ಭಾಗ ಗೊಂದಲಕಾರಕವಾಗಿತ್ತೇ ಅಥವಾ ಸ್ಪಷ್ಟವಾಗಿರಲಿಲ್ಲವೇ?",
  "How did the film length feel?": "ಚಿತ್ರದ ಅವಧಿ ಹೇಗನಿಸಿತು?",
  "Final Recommendation": "ಅಂತಿಮ ಶಿಫಾರಸು",
  "Recommendation, audience fit, and permission to contact.": "ಶಿಫಾರಸು, ಸರಿಯಾದ ಪ್ರೇಕ್ಷಕರು ಮತ್ತು ಸಂಪರ್ಕಿಸಲು ಅನುಮತಿ.",
  "One honest line to the director/editor.": "ನಿರ್ದೇಶಕ / ಸಂಕಲನಕಾರರಿಗೆ ಒಂದು ನಿಷ್ಠಾವಂತ ಸಾಲು.",
  "Back": "ಹಿಂದೆ",
  "Next": "ಮುಂದೆ",
  "Previous": "ಹಿಂದೆ",
  "Step": "ಹಂತ",
  "of": "ರಲ್ಲಿ",
  "Basic Details": "ಮೂಲ ವಿವರಗಳು",
  "Ratings": "ಮೌಲ್ಯಮಾಪನ",
  "More Feedback": "ಹೆಚ್ಚಿನ ಅಭಿಪ್ರಾಯ",
  "Thank you for submitting": "ಸಲ್ಲಿಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು",
  "Your feedback has been recorded.": "ನಿಮ್ಮ ಅಭಿಪ್ರಾಯ ದಾಖಲಿಸಲಾಗಿದೆ.",
  "Your honest response will help the makers improve the film.": "ನಿಮ್ಮ ನಿಷ್ಠಾವಂತ ಪ್ರತಿಕ್ರಿಯೆ ಚಿತ್ರವನ್ನು ಇನ್ನಷ್ಟು ಉತ್ತಮಗೊಳಿಸಲು ನಿರ್ಮಾಪಕರಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
  "Submit another feedback": "ಮತ್ತೊಂದು ಅಭಿಪ್ರಾಯ ಸಲ್ಲಿಸಿ",
  "Back to home": "ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ"
};

const FEEDBACK_OPTION_KN = {
  "General Audience": "ಸಾಮಾನ್ಯ ಪ್ರೇಕ್ಷಕರು",
  "Family Audience": "ಕುಟುಂಬ ಪ್ರೇಕ್ಷಕರು",
  "Youth Audience": "ಯುವ ಪ್ರೇಕ್ಷಕರು",
  "Senior Citizens": "ಹಿರಿಯ ನಾಗರಿಕರು",
  "Film / Media Background": "ಚಲನಚಿತ್ರ ಅಥವಾ ಮಾಧ್ಯಮ ಹಿನ್ನೆಲೆ",
  "Artist / Creative Background": "ಕಲಾವಿದ ಅಥವಾ ಸೃಜನಾತ್ಮಕ ಹಿನ್ನೆಲೆ",
  "Working Professionals": "ಉದ್ಯೋಗದಲ್ಲಿರುವ ವೃತ್ತಿಪರರು",
  "Kannada Cinema Audience": "ಕನ್ನಡ ಚಿತ್ರರಂಗದ ಪ್ರೇಕ್ಷಕರು",
  "Festival / Critic Audience": "ಚಿತ್ರೋತ್ಸವ ಅಥವಾ ವಿಮರ್ಶಕ ಪ್ರೇಕ್ಷಕರು",
  "Mostly": "ಬಹುಪಾಲು",
  "Partly": "ಭಾಗಶಃ",
  "Not really": "ಅಷ್ಟಾಗಿ ಇಲ್ಲ",
  "Not at all": "ಇಲ್ಲವೇ ಇಲ್ಲ",
  "Yes": "ಹೌದು",
  "No": "ಇಲ್ಲ",
  "Maybe": "ಬಹುಶಃ",
  "Too long": "ತುಂಬಾ ಉದ್ದವಾಗಿದೆ",
  "Slightly long": "ಸ್ವಲ್ಪ ಉದ್ದವಾಗಿದೆ",
  "Just right": "ಸರಿಯಾಗಿದೆ",
  "Too short": "ತುಂಬಾ ಚಿಕ್ಕದಾಗಿದೆ",
  "Family audience": "ಕುಟುಂಬ ಪ್ರೇಕ್ಷಕರು",
  "Kannada cinema lovers": "ಕನ್ನಡ ಸಿನೆಮಾ ಪ್ರೇಮಿಗಳು",
  "Drama lovers": "ನಾಟಕೀಯ ಕಥೆಗಳ ಅಭಿಮಾನಿಗಳು",
  "Art-house/festival audience": "ಕಲಾತ್ಮಕ ಅಥವಾ ಚಿತ್ರೋತ್ಸವ ಪ್ರೇಕ್ಷಕರು",
  "Urban audience": "ನಗರ ಪ್ರೇಕ್ಷಕರು",
  "Tier-2/town audience": "ಪಟ್ಟಣ ಪ್ರೇಕ್ಷಕರು",
  "Children and families": "ಮಕ್ಕಳು ಮತ್ತು ಕುಟುಂಬಗಳು",
  "Senior citizens": "ಹಿರಿಯ ನಾಗರಿಕರು",
  "OTT audience": "OTT ಪ್ರೇಕ್ಷಕರು",
  "Theatre audience": "ಚಿತ್ರಮಂದಿರ ಪ್ರೇಕ್ಷಕರು",
  "All audiences": "ಎಲ್ಲಾ ಪ್ರೇಕ್ಷಕರು",
  "Emotional": "ಭಾವನಾತ್ಮಕ",
  "Nostalgic": "ನೆನಪು ಮೂಡಿಸುವ",
  "Warm": "ಆತ್ಮೀಯ",
  "Beautiful": "ಸುಂದರ",
  "Touching": "ಮನಮುಟ್ಟುವ",
  "Slow": "ನಿಧಾನ",
  "Confusing": "ಗೊಂದಲಕಾರಕ",
  "Engaging": "ಹಿಡಿದಿಡುವ",
  "Memorable": "ನೆನಪಿನಲ್ಲಿ ಉಳಿಯುವ",
  "Average": "ಸರಾಸರಿ",
  "Powerful": "ಪ್ರಭಾವಶಾಲಿ",
  "Excellent": "ಅತ್ಯುತ್ತಮ",
  "Good": "ಚೆನ್ನಾಗಿದೆ",
  "Weak": "ದುರ್ಬಲ",
  "Poor": "ಕಳಪೆ",
  "Average / ಸರಾಸರಿ": "ಸರಾಸರಿ",
  "Yes / ಹೌದು": "ಹೌದು",
  "No / ಇಲ್ಲ": "ಇಲ್ಲ",
  "Exceeded expectations": "ನಿರೀಕ್ಷೆಗಿಂತ ಉತ್ತಮ",
  "Met expectations": "ನಿರೀಕ್ಷೆ ಪೂರೈಸಿತು",
  "Below expectations": "ನಿರೀಕ್ಷೆಗಿಂತ ಕಡಿಮೆ",
  "Clear": "ಸ್ಪಷ್ಟ",
  "Somewhat clear": "ಸ್ವಲ್ಪ ಸ್ಪಷ್ಟ",
  "Very good": "ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ",
  "Needs improvement": "ಸುಧಾರಣೆ ಅಗತ್ಯ",
  "Too slow": "ತುಂಬಾ ನಿಧಾನ",
  "Slightly slow": "ಸ್ವಲ್ಪ ನಿಧಾನ",
  "Perfect": "ಸರಿಯಾಗಿದೆ",
  "Not emotional": "ಭಾವನಾತ್ಮಕವಾಗಿರಲಿಲ್ಲ",
  "Theatre": "ಚಿತ್ರಮಂದಿರ",
  "OTT": "OTT",
  "Both": "ಎರಡೂ",
  "Neither": "ಯಾವುದೂ ಅಲ್ಲ"
};

function feedbackLabel(lang, text) {
  return lang === 'kn' ? (FEEDBACK_TEXT_KN[text] || FEEDBACK_OPTION_KN[text] || text) : text;
}

function feedbackOption(lang, text) {
  if (lang === 'kn') return FEEDBACK_OPTION_KN[text] || FEEDBACK_TEXT_KN[text] || text;
  return String(text).replace(/ \/ [\u0C80-\u0CFF].*$/u, '');
}


function isPosterRelatedFeedbackText(text) {
  const value = String(text || '').toLowerCase();
  return value.includes('poster') || value.includes('ಪೋಸ್ಟರ್');
}



const emptyRegistration = { name: '', age_group: '', social_background: '', primary_language: '', phone_number: '', remarks: '' };
const emptySurvey = {
  phone_number: '', overall_rating: 5, story_rating: 5, acting_rating: 5, music_rating: 5,
  pace_rating: 5, emotional_impact_rating: 5, visual_quality_rating: 5, dialogue_rating: 5, length_rating: 5,
  understood_story: 'Mostly', connected_with_characters: '', preferred_audience: '', theatre_or_ott: '',
  one_word_reaction: '', audience_type: '', consent_quote: 'No', liked_most: '', improvements: '',
  memorable_scene: '', would_recommend: 'Maybe', contact_permission: 'Yes', consent_contact: 'Yes', remarks: '', name: '', custom_answers: {}
};

const AUDIENCE_TYPE_OPTIONS = [
  'General Audience',
  'Family Audience',
  'Youth Audience',
  'Senior Citizens',
  'Film / Media Background',
  'Artist / Creative Background',
  'Working Professionals',
  'Kannada Cinema Audience',
  'Festival / Critic Audience'
];

const RIGHT_AUDIENCE_OPTIONS = [
  'Family audience',
  'Kannada cinema lovers',
  'Drama lovers',
  'Art-house / festival audience',
  'Urban audience',
  'Tier-2 / town audience',
  'Children and families',
  'Senior citizens',
  'OTT audience',
  'Theatre audience',
  'All audiences'
];

const ONE_WORD_REACTION_OPTIONS = [
  'Emotional',
  'Nostalgic',
  'Warm',
  'Beautiful',
  'Touching',
  'Slow',
  'Confusing',
  'Engaging',
  'Memorable',
  'Average',
  'Powerful'
];

const emptyScreeningDetails = {
  film_title: 'Mysore Studio', film_language: 'Kannada', genre: 'Drama', duration_minutes: '', director: 'Praveen M Prabhu',
  producer: 'PK Picture and High5Studio', synopsis: 'A warm, nostalgic story about memories, cinema, and relationships.',
  screening_date: '2026-07-12', screening_time: '16:00', venue_name: '', venue_city: '', expected_audience_count: 40,
  actual_audience_count: '', audience_age_mix: '', audience_language_mix: '', audience_social_mix: '', remarks: 'Private screening and audience feedback session. 12 July 2026, 4:00 PM onwards.'
};
const emptyUser = { full_name: '', username: '', phone_number: '', password: '', role: 'Admin' };

function apiFetch(path, options = {}) {
  const token = localStorage.getItem('payana_admin_token');
  const isFormData = options.body instanceof FormData;
  const headers = { ...(isFormData ? {} : { 'Content-Type': 'application/json' }), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { ...options, headers }).then(async (response) => {
    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      const message = typeof data === 'string' ? data : data.detail || 'Request failed';
      throw new Error(message);
    }
    return data;
  });
}
function assetUrl(path) { return path ? `${API_BASE}${path}` : ''; }

function downloadAdminCsv(path, filename) {
  const token = localStorage.getItem('payana_admin_token');
  fetch(`${API_BASE}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Download failed');
      }
      return response.blob();
    })
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    })
    .catch((err) => alert(err.message || 'Download failed'));
}

function visiblePages(items, type) { return (items || []).filter((x) => x.page_type === type).sort((a, b) => a.display_order - b.display_order); }
function pageLabel(items, key, fallback) { return items?.find((x) => x.page_key === key)?.page_label || fallback; }
function routeFromHash() {
  let hashView = (window.location.hash || '').replace(/^#\/?/, '').trim();
  if (!hashView) hashView = 'landing';
  if (hashView === 'admin' || hashView === 'login') return 'login';
  if (hashView === '/login' || hashView === '/admin') return 'login';
  return hashView;
}

function App() {
  const [view, setView] = useState(() => routeFromHash());
  const [options, setOptions] = useState({ age_groups: [], social_backgrounds: [], primary_languages: [], statuses: [], roles: [], film_languages: [], film_genres: [], understood_options: [], yes_no_maybe: [], character_connection_options: [], theatre_or_ott_options: [], quote_consent_options: [] });
  const [user, setUser] = useState(null);
  const [loadingMe, setLoadingMe] = useState(true);
  const [pages, setPages] = useState([]);
  const [landing, setLanding] = useState(null);
  const [surveyBuilder, setSurveyBuilder] = useState({ sections: [] });

  async function loadPublic() {
    apiFetch('/api/options').then(setOptions).catch(() => {});
    apiFetch('/api/menu-pages').then((data) => setPages(data.items || [])).catch(() => {});
    apiFetch('/api/landing').then(setLanding).catch(() => {});
    apiFetch('/api/survey-builder').then(setSurveyBuilder).catch(() => {});
  }

  async function loadAdminPages() {
    try {
      const data = await apiFetch('/api/admin/page-settings');
      setPages(data.items || []);
    } catch (err) {
      await loadPublic();
    }
  }

  useEffect(() => {
    loadPublic();
    apiFetch('/api/admin/me')
      .then(async (currentUser) => { setUser(currentUser); await loadAdminPages(); })
      .catch(() => setUser(null))
      .finally(() => setLoadingMe(false));
  }, []);

  useEffect(() => {
    const onHashChange = () => {
      setView(routeFromHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener('hashchange', onHashChange);
    onHashChange();
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  function navigate(next) {
    const target = next === 'admin' ? 'login' : next;
    window.location.hash = target;
    setView(target);
    window.scrollTo(0, 0);
  }
  function logout() {
    apiFetch('/api/admin/logout', { method: 'POST' }).catch(() => {});
    localStorage.removeItem('payana_admin_token');
    setUser(null); navigate('landing');
  }

  const publicPages = visiblePages(pages, 'public').filter((page) => page.page_key !== 'admin');
  const isPublicView = ['landing', 'register', 'survey'].includes(view);
  const filmTitle = landing?.film_title || 'Payana';

  const showTopbar = view !== 'landing';

  return (
    <div>
      {showTopbar && (
        <header className="topbar">
          <div className="brand-mark">P</div>
          <div className="brand-copy">
            <h1>{filmTitle} Screening</h1>
            <p>Private screening registration, audience survey, and admin reporting</p>
          </div>
          <nav className="nav-actions">
            {publicPages.map((page) => (
              <button key={page.page_key} className={view === page.page_key ? 'active' : ''} onClick={() => navigate(page.page_key)}>{page.page_label}</button>
            ))}
            {user && <button className="ghost" onClick={logout}>Logout</button>}
          </nav>
        </header>
      )}

      <main className={view === 'landing' ? 'landing-shell' : 'page-shell'}>
        {view === 'landing' && <LandingPage landing={landing} onNavigate={navigate} pages={pages} user={user} />}
        {view === 'register' && <PublicRegistration options={options} landing={landing} />}
        {view === 'survey' && <AudienceSurvey options={options} landing={landing} surveyBuilder={surveyBuilder} />}
        {!isPublicView && !loadingMe && !user && <AdminLogin onLogin={async (loggedInUser) => { setUser(loggedInUser); await loadAdminPages(); }} />}
        {!isPublicView && !loadingMe && user && <AdminPanel user={user} options={options} pages={pages} setPages={setPages} surveyBuilder={surveyBuilder} onPublicRefresh={loadPublic} onAdminRefresh={loadAdminPages} />}
      </main>

      <footer className="footer">Payana Screening Registration v{VERSION}</footer>
    </div>
  );
}

function LandingPage({ landing, onNavigate, pages, user }) {
  const isSuperAdmin = user?.role === 'Super Admin';
  const buttons = landing?.landing_buttons || {};
  const registerVisible = isSuperAdmin || buttons.show_registration_button !== false;
  const surveyVisible = isSuperAdmin || buttons.show_survey_button !== false;
  const qrVisible = isSuperAdmin || buttons.show_feedback_qr_button !== false;
  const venue = [landing?.venue_name, landing?.venue_city].filter(Boolean).join(', ');
  return (
    <section className="landing-minimal">
      <div className="landing-poster-focus">
        {landing?.poster_url ? <img src={assetUrl(landing.poster_url)} alt={`${landing.film_title || 'Film'} poster`} /> : <div className="poster-placeholder">Poster</div>}
      </div>

      <div className="landing-details-minimal">
        <p className="eyebrow">Private Screening</p>
        <h2>{landing?.film_title || 'Mysore Studio'}</h2>
        <p className="hero-text compact">{landing?.synopsis || 'Join us for a private screening and feedback session.'}</p>

        <div className="landing-meta-row">
          <span>{formatDateOnly(landing?.screening_date) || '12 July 2026'}</span>
          <span>{formatTimeText(landing?.screening_time) || '4:00 PM onwards'}</span>
          {venue && <span>{venue}</span>}
        </div>

        <div className="landing-small-meta">
          <span>{landing?.film_language || 'Kannada'}</span>
          <span>{landing?.genre || 'Drama'}</span>
          <span>Director: {landing?.director || '-'}</span>
          <span>Seats: {landing?.expected_audience_count || 40}</span>
        </div>

        <div className="button-row landing-actions-minimal">
          {!!registerVisible && <button className="primary" onClick={() => onNavigate('register')}>Register for Screening</button>}
          {!!surveyVisible && <button onClick={() => onNavigate('survey')}>Fill Post-Screening Survey</button>}
          {!!qrVisible && <QrDialogButton />}
        </div>
        <p className="muted tiny">The survey is intended for registered audience members after the screening.</p>
      </div>
    </section>
  );
}


function QrDialogButton() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="ghost" onClick={() => setOpen(true)}>Show Feedback QR</button>
      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal qr-modal" onClick={(e) => e.stopPropagation()}>
            <div className="report-header">
              <div>
                <h2>Feedback QR Code</h2>
                <p className="muted">scan this to provide feedback</p>
              </div>
              <button className="ghost" onClick={() => setOpen(false)}>Close</button>
            </div>
            <div className="qr-box">
              <img src="/payana_feedback_qr.png" alt="QR code to provide feedback" />
              <p>scan this to provide feedback</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function PublicRegistration({ options, landing }) {
  const [form, setForm] = useState(emptyRegistration);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  function update(field, value) { setForm((prev) => ({ ...prev, [field]: value })); }
  async function submit(event) {
    event.preventDefault(); setError(''); setMessage(''); setSaving(true);
    try {
      const data = await apiFetch('/api/register', { method: 'POST', body: JSON.stringify(form) });
      setMessage(data.message || landing?.app_config?.registration_success_message || 'Thank you for registering. Seats are limited. Shortlisted participants will be contacted separately.');
      setForm(emptyRegistration);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  }
  return (
    <section className="card form-card">
      <div className="section-title">
        <h2>{landing?.film_title || 'Film'} – Private Screening Registration</h2>
        <p>{formatDateOnly(landing?.screening_date) || '12 July 2026'} · {formatTimeText(landing?.screening_time) || '4:00 PM onwards'} · Please fill in your details.</p>
      </div>
      {message && <div className="notice success">{message}</div>}
      {error && <div className="notice error">{error}</div>}
      <form onSubmit={submit} className="grid-form">
        <label>Name <span>*</span><input value={form.name} onChange={(e) => update('name', e.target.value)} placeholder="Full name" required minLength="2" /></label>
        <label>Age Group <span>*</span><select value={form.age_group} onChange={(e) => update('age_group', e.target.value)} required><option value="">Select age group</option>{options.age_groups.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Social Background <span>*</span><select value={form.social_background} onChange={(e) => update('social_background', e.target.value)} required><option value="">Select background</option>{options.social_backgrounds.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Primary Language <span>*</span><select value={form.primary_language} onChange={(e) => update('primary_language', e.target.value)} required><option value="">Select language</option>{options.primary_languages.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Phone Number <span>*</span><input value={form.phone_number} onChange={(e) => update('phone_number', e.target.value)} placeholder="10-digit mobile number" required pattern="[0-9]{10}" inputMode="numeric" /></label>
        <label className="full-width">Remarks<textarea value={form.remarks} onChange={(e) => update('remarks', e.target.value)} placeholder="Anything you want the film team to know" maxLength="500" /></label>
        <button className="primary full-width" disabled={saving}>{saving ? 'Registering...' : 'Register for Screening'}</button>
      </form>
    </section>
  );
}

function AudienceSurvey({ options, landing, surveyBuilder }) {
  const [form, setForm] = useState(emptySurvey);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [feedbackLang, setFeedbackLang] = useState('kn');
  const [mainStep, setMainStep] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const L = (text) => feedbackLabel(feedbackLang, text);
  const O = (text) => feedbackOption(feedbackLang, text);
  function update(field, value) { setForm((prev) => ({ ...prev, [field]: value })); }
  async function submit(event) {
    event.preventDefault(); setMessage(''); setError(''); setSaving(true);
    try {
      const payload = { ...form, overall_rating: Number(form.overall_rating), story_rating: Number(form.story_rating), acting_rating: Number(form.acting_rating), music_rating: Number(form.music_rating), pace_rating: Number(form.pace_rating), emotional_impact_rating: Number(form.emotional_impact_rating), visual_quality_rating: Number(form.visual_quality_rating), dialogue_rating: Number(form.dialogue_rating), length_rating: Number(form.length_rating) };
      await apiFetch('/api/survey', { method: 'POST', body: JSON.stringify(payload) });
      setMessage(''); setForm(emptySurvey); setMainStep(0); setSubmitted(true);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  }
  const renderOptions = (items = []) => items.map((x) => <option key={x} value={x}>{O(x)}</option>);
  const mainSteps = [L('Basic Details'), L('Ratings'), L('More Feedback'), L('Final Recommendation')];


  if (submitted) {
    return (
      <section className="card form-card wide-form-card feedback-thank-you">
        <div className="thank-you-icon">✓</div>
        <h2>{L('Thank you for submitting')}</h2>
        <p>{L('Your feedback has been recorded.')}</p>
        <p className="muted">{L('Your honest response will help the makers improve the film.')}</p>
        <div className="thank-you-actions">
          <button type="button" className="secondary" onClick={() => { setSubmitted(false); setForm(emptySurvey); setMainStep(0); }}>
            {L('Submit another feedback')}
          </button>
          <button type="button" className="primary" onClick={() => { window.location.hash = ''; window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
            {L('Back to home')}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="card form-card wide-form-card feedback-mobile-wizard">
      <div className="section-title">
        <h2>{landing?.film_title || L('Film')} – {L('Post-Screening Audience Survey')}</h2>
        <p>{L('This survey is for audience members after the screening. Phone number is used only for reference and will not be validated against registration.')}</p>
        <div className="feedback-language-toggle">
          <span>{L('Language')}</span>
          <button type="button" className={feedbackLang === 'kn' ? 'active' : ''} onClick={() => setFeedbackLang('kn')}>{L('Kannada')}</button>
          <button type="button" className={feedbackLang === 'en' ? 'active' : ''} onClick={() => setFeedbackLang('en')}>{L('English')}</button>
        </div>
      </div>

      <div className="wizard-progress main-wizard-progress">
        <div>
          <strong>{L('Step')} {mainStep + 1} {L('of')} {mainSteps.length}</strong>
          <span>{mainSteps[mainStep]}</span>
        </div>
        <div className="wizard-dots">
          {mainSteps.map((s, i) => <button type="button" key={s} className={i === mainStep ? 'active' : ''} onClick={() => setMainStep(i)} />)}
        </div>
      </div>

      {message && <div className="notice success">{message}</div>}
      {error && <div className="notice error">{error}</div>}

      <form onSubmit={submit} className="grid-form">
        {mainStep === 0 && <>
          <label>{L('Name')} <span>*</span><input value={form.name} onChange={(e) => update('name', e.target.value)} placeholder={L('Full name')} required minLength="2" /></label>
          <label>{L('Phone Number / Reference')}<input value={form.phone_number} onChange={(e) => update('phone_number', e.target.value)} placeholder={L('Optional phone number or reference ID')} maxLength="40" /></label>
          <label>{L('Consent to contact for further discussion')} <span>*</span><select value={form.consent_contact} onChange={(e) => update('consent_contact', e.target.value)} required>{renderOptions(['Yes','No'])}</select></label>
          <label>{L('Audience Type')}<select value={form.audience_type} onChange={(e) => update('audience_type', e.target.value)}><option value="">{L('Select')}</option>{renderOptions(AUDIENCE_TYPE_OPTIONS)}</select></label>
        </>}

        {mainStep === 1 && <>
          <label>{L('Overall Experience')} <span>*</span><RatingSelect lang={feedbackLang} value={form.overall_rating} onChange={(v) => update('overall_rating', v)} /></label>
          <label>{L('Story')} <span>*</span><RatingSelect lang={feedbackLang} value={form.story_rating} onChange={(v) => update('story_rating', v)} /></label>
          <label>{L('Acting / Performances')} <span>*</span><RatingSelect lang={feedbackLang} value={form.acting_rating} onChange={(v) => update('acting_rating', v)} /></label>
          <label>{L('Music / Sound')} <span>*</span><RatingSelect lang={feedbackLang} value={form.music_rating} onChange={(v) => update('music_rating', v)} /></label>
          <label>{L('Pace / Editing')} <span>*</span><RatingSelect lang={feedbackLang} value={form.pace_rating} onChange={(v) => update('pace_rating', v)} /></label>
          <label>{L('Emotional Impact')} <span>*</span><RatingSelect lang={feedbackLang} value={form.emotional_impact_rating} onChange={(v) => update('emotional_impact_rating', v)} /></label>
          <label>{L('Visual Quality / Cinematography')} <span>*</span><RatingSelect lang={feedbackLang} value={form.visual_quality_rating} onChange={(v) => update('visual_quality_rating', v)} /></label>
          <label>{L('Dialogues')} <span>*</span><RatingSelect lang={feedbackLang} value={form.dialogue_rating} onChange={(v) => update('dialogue_rating', v)} /></label>
          <label>{L('Film Length')} <span>*</span><RatingSelect lang={feedbackLang} value={form.length_rating} onChange={(v) => update('length_rating', v)} /></label>
        </>}

        {mainStep === 2 && <>
          <label>{L('Did you understand the story clearly?')} <span>*</span><select value={form.understood_story} onChange={(e) => update('understood_story', e.target.value)} required><option value="">{L('Select')}</option>{renderOptions(options.understood_options || [])}</select></label>
          <label>{L('Did you connect with the characters?')}<select value={form.connected_with_characters} onChange={(e) => update('connected_with_characters', e.target.value)}><option value="">{L('Select')}</option>{renderOptions(options.character_connection_options || [])}</select></label>
          <label>{L('Theatre or OTT fit?')}<select value={form.theatre_or_ott} onChange={(e) => update('theatre_or_ott', e.target.value)}><option value="">{L('Select')}</option>{renderOptions(options.theatre_or_ott_options || [])}</select></label>
          <label>{L('One-word reaction')}<select value={form.one_word_reaction} onChange={(e) => update('one_word_reaction', e.target.value)}><option value="">{L('Select')}</option>{renderOptions(ONE_WORD_REACTION_OPTIONS)}</select></label>
          <DynamicSurveyQuestions builder={surveyBuilder} form={form} update={update} lang={feedbackLang} />
        </>}

        {mainStep === 3 && <>
          <label className="full-width">{L('Who is the right audience for this film?')}<select value={form.preferred_audience} onChange={(e) => update('preferred_audience', e.target.value)}><option value="">{L('Select')}</option>{renderOptions(RIGHT_AUDIENCE_OPTIONS)}</select></label>
          <label>{L('Can we use a short quote from your feedback?')} <select value={form.consent_quote} onChange={(e) => update('consent_quote', e.target.value)}>{renderOptions(options.quote_consent_options || ['Yes','No'])}</select></label>
          <label>{L('Would you recommend this film?')} <span>*</span><select value={form.would_recommend} onChange={(e) => update('would_recommend', e.target.value)} required><option value="">{L('Select')}</option>{renderOptions(options.yes_no_maybe || [])}</select></label>
          <label>{L('Can we contact you for detailed feedback?')} <span>*</span><select value={form.contact_permission} onChange={(e) => update('contact_permission', e.target.value)} required><option value="">{L('Select')}</option>{renderOptions(['Yes','No'])}</select></label>
          <label className="full-width">{L('What did you like the most?')}<textarea value={form.liked_most} onChange={(e) => update('liked_most', e.target.value)} maxLength="1000" /></label>
          <label className="full-width">{L('What can be improved?')}<textarea value={form.improvements} onChange={(e) => update('improvements', e.target.value)} maxLength="1000" /></label>
          <label className="full-width">{L('Any memorable scene, character, or moment?')}<textarea value={form.memorable_scene} onChange={(e) => update('memorable_scene', e.target.value)} maxLength="1000" /></label>
          <label className="full-width">{L('Additional Remarks')}<textarea value={form.remarks} onChange={(e) => update('remarks', e.target.value)} maxLength="1000" /></label>
        </>}

        <div className="wizard-actions full-width">
          <button type="button" className="secondary" disabled={mainStep === 0} onClick={() => setMainStep((v) => Math.max(0, v - 1))}>{L('Previous')}</button>
          {mainStep < mainSteps.length - 1 ? (
            <button type="button" className="primary" onClick={() => setMainStep((v) => Math.min(mainSteps.length - 1, v + 1))}>{L('Next')}</button>
          ) : (
            <button className="primary" disabled={saving}>{saving ? L('Submitting...') : L('Submit Feedback')}</button>
          )}
        </div>
      </form>
    </section>
  );
}

function DynamicSurveyQuestions({ builder, form, update, lang = 'en' }) {
  const [sectionStep, setSectionStep] = useState(0);
  const sections = (builder?.sections || [])
    .filter((section) => !isPosterRelatedFeedbackText(section.title) && !isPosterRelatedFeedbackText(section.description))
    .map((section) => ({
      ...section,
      questions: (section.questions || []).filter((q) =>
        !isPosterRelatedFeedbackText(q.question_text) &&
        !isPosterRelatedFeedbackText((q.options || []).join(' '))
      ),
    }))
    .filter((section) => (section.questions || []).length > 0);

  if (!sections.length) return null;

  const currentIndex = Math.min(sectionStep, sections.length - 1);
  const section = sections[currentIndex];

  function setAnswer(qid, value) {
    update('custom_answers', { ...(form.custom_answers || {}), [qid]: value });
  }

  return <div className="survey-wizard full-width">
    <div className="wizard-progress">
      <div>
        <strong>{feedbackLabel(lang, 'Step')} {currentIndex + 1} {feedbackLabel(lang, 'of')} {sections.length}</strong>
        <span>{feedbackLabel(lang, section.title)}</span>
      </div>
      <div className="wizard-dots">
        {sections.map((s, i) => <button type="button" key={s.id} className={i === currentIndex ? 'active' : ''} onClick={() => setSectionStep(i)} aria-label={`Go to step ${i + 1}`} />)}
      </div>
    </div>

    <div className="survey-section full-width">
      <h3>{feedbackLabel(lang, section.title)}</h3>
      {section.description && <p className="muted">{feedbackLabel(lang, section.description)}</p>}
      <div className="grid-form">
        {(section.questions || []).map((q) => <label className="full-width" key={q.id}>{feedbackLabel(lang, q.question_text)} {q.is_required ? <span>*</span> : null}
          {q.question_type === 'multiple_choice'
            ? <select value={(form.custom_answers || {})[q.id] || ''} onChange={(e) => setAnswer(q.id, e.target.value)} required={!!q.is_required}>
                <option value="">{feedbackLabel(lang, 'Select')}</option>
                {(q.options || []).map((opt) => <option key={opt} value={opt}>{feedbackOption(lang, opt)}</option>)}
              </select>
            : <textarea value={(form.custom_answers || {})[q.id] || ''} onChange={(e) => setAnswer(q.id, e.target.value)} required={!!q.is_required} maxLength="2000" />}
        </label>)}
      </div>
    </div>

    <div className="wizard-actions">
      <button type="button" className="secondary" disabled={currentIndex === 0} onClick={() => setSectionStep((v) => Math.max(0, v - 1))}>{feedbackLabel(lang, 'Previous')}</button>
      <button type="button" className="secondary" disabled={currentIndex >= sections.length - 1} onClick={() => setSectionStep((v) => Math.min(sections.length - 1, v + 1))}>{feedbackLabel(lang, 'Next')}</button>
    </div>
  </div>;
}

function RatingSelect({ value, onChange, lang = 'en' }) {
  const labels = {5: 'Excellent', 4: 'Good', 3: 'Average', 2: 'Weak', 1: 'Poor'};
  return <select value={value} onChange={(e) => onChange(e.target.value)} required>
    {[5,4,3,2,1].map((x) => <option key={x} value={x}>{x} - {feedbackOption(lang, labels[x])}</option>)}
  </select>;
}


function AdminPanel({ user, options, pages, setPages, surveyBuilder, onPublicRefresh, onAdminRefresh }) {
  const adminPages = useMemo(() => {
    const visibleAdmin = visiblePages(pages, 'admin');
    if (user.role === 'Super Admin' && !visibleAdmin.find((p) => p.page_key === 'pageSettings')) {
      const settingsPage = (pages || []).find((p) => p.page_key === 'pageSettings') || { page_key: 'pageSettings', page_label: 'Landing Button Settings', page_type: 'admin', is_visible: 1, display_order: 99 };
      return [...visibleAdmin, { ...settingsPage, page_label: settingsPage.page_label || 'Landing Button Settings' }];
    }
    return visibleAdmin;
  }, [pages, user.role]);
  const firstPage = adminPages[0]?.page_key || (user.role === 'Super Admin' ? 'pageSettings' : 'registrations');
  const [tab, setTab] = useState(firstPage);
  const [dashboard, setDashboard] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => { apiFetch('/api/admin/dashboard').then(setDashboard).catch(() => {}); }, [refreshKey]);
  useEffect(() => { if (!adminPages.find((p) => p.page_key === tab)) setTab(firstPage); }, [pages]);
  function canSee(pageKey) { if (['users','audit','pageSettings'].includes(pageKey) && user.role !== 'Super Admin') return false; return true; }
  return (
    <div className="admin-layout">
      <aside className="side-card">
        <h3>{user.full_name}</h3><p>{user.role}</p>
        {adminPages.filter((p) => canSee(p.page_key)).map((page) => <button key={page.page_key} className={tab === page.page_key ? 'active wide' : 'wide'} onClick={() => setTab(page.page_key)}>{page.page_label}</button>)}
      </aside>
      <section className="admin-main">
        {dashboard && <Stats dashboard={dashboard} />}
        {tab === 'registrations' && <Registrations options={options} user={user} onChanged={() => setRefreshKey((x) => x + 1)} />}
        {tab === 'screeningDetails' && <ScreeningDetails options={options} user={user} onPublicRefresh={onPublicRefresh} />}
        {tab === 'surveyReport' && <SurveyReport options={options} onChanged={() => setRefreshKey((x) => x + 1)} />}
        {tab === 'surveyBuilder' && <SurveyBuilder onPublicRefresh={onPublicRefresh} />}
        {tab === 'analytics' && <AnalyticsPage />}
        {tab === 'surveyAnalytics' && <SurveyAnalytics />}
        {tab === 'pageSettings' && user.role === 'Super Admin' && <PageSettings pages={pages} setPages={setPages} onPublicRefresh={onPublicRefresh} onAdminRefresh={onAdminRefresh} />}
        {tab === 'users' && user.role === 'Super Admin' && <Users options={options} />}
        {tab === 'audit' && user.role === 'Super Admin' && <AuditLogs />}
      </section>
    </div>
  );
}
function Stats({ dashboard }) {
  return <div className="stats-grid">
    <div className="stat-card highlight"><span>Total Registered</span><strong>{dashboard.total}</strong></div>
    <div className="stat-card"><span>Shortlisted</span><strong>{dashboard.counts?.Shortlisted || 0}/{dashboard.shortlist_limit}</strong></div>
    <div className="stat-card"><span>Waitlisted</span><strong>{dashboard.counts?.Waitlisted || 0}</strong></div>
    <div className="stat-card"><span>Attended</span><strong>{dashboard.counts?.Attended || 0}</strong></div>
    <div className="stat-card"><span>Survey Responses</span><strong>{dashboard.survey_count || 0}</strong></div>
    <div className="stat-card"><span>Avg Rating</span><strong>{dashboard.average_overall_rating || 0}</strong></div>
  </div>;
}

function Registrations({ options, user, onChanged }) {
  const [items, setItems] = useState([]); const [filters, setFilters] = useState({ search: '', age_group: '', social_background: '', primary_language: '', selection_status: '' });
  const [editing, setEditing] = useState(null); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [aiProposal, setAiProposal] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('Approved');
  const [uploadResult, setUploadResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  async function load() { setError(''); try { const query = new URLSearchParams(filters).toString(); const data = await apiFetch(`/api/admin/registrations?${query}`); setItems(data.items || []); setSelectedIds([]); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  function toggleSelected(id, checked) { setSelectedIds((prev) => checked ? [...new Set([...prev, id])] : prev.filter((x) => x !== id)); }
  function toggleAll(checked) { setSelectedIds(checked ? items.map((x) => x.id) : []); }
  async function bulkApprove() { setError(''); setNotice(''); if (!selectedIds.length) { setError('Please select at least one record.'); return; } try { const data = await apiFetch('/api/admin/registrations-bulk-status', { method: 'PUT', body: JSON.stringify({ ids: selectedIds, selection_status: 'Approved', admin_remarks: 'Approved by Super Admin' }) }); setNotice(`${data.updated} registration(s) approved.`); await load(); onChanged?.(); } catch (err) { setError(err.message); } }
  async function createAiProposal() { setError(''); setNotice(''); setAiLoading(true); try { const data = await apiFetch('/api/admin/ai-approval-proposal'); setAiProposal(data); } catch (err) { setError(err.message); } finally { setAiLoading(false); } }
  async function approveAiProposal() { setError(''); setNotice(''); if (!aiProposal?.selected_ids?.length) { setError('AI proposal has no records to approve.'); return; } try { const data = await apiFetch('/api/admin/ai-approval-proposal/approve', { method: 'POST', body: JSON.stringify({ ids: aiProposal.selected_ids }) }); setNotice(`${data.updated} AI-proposed registration(s) approved.`); setAiProposal(null); await load(); onChanged?.(); } catch (err) { setError(err.message); } }
  async function changeStatus(item, status) { setError(''); setNotice(''); try { await apiFetch(`/api/admin/registrations/${item.id}/status`, { method: 'PUT', body: JSON.stringify({ selection_status: status, admin_remarks: item.admin_remarks || '' }) }); setNotice('Status updated.'); await load(); onChanged?.(); } catch (err) { setError(err.message); } }
  async function saveEdit(event) { event.preventDefault(); setError(''); setNotice(''); try { await apiFetch(`/api/admin/registrations/${editing.id}`, { method: 'PUT', body: JSON.stringify(editing) }); setNotice('Registration updated.'); setEditing(null); await load(); onChanged?.(); } catch (err) { setError(err.message); } }
  async function deleteItem(item) { if (!confirm(`Delete registration for ${item.name}?`)) return; try { await apiFetch(`/api/admin/registrations/${item.id}`, { method: 'DELETE' }); setNotice('Registration deleted.'); await load(); onChanged?.(); } catch (err) { setError(err.message); } }
  function downloadCsv() { downloadWithAuth('/api/admin/registrations/export.csv', `registrations_${dateStamp()}.csv`, setError); }
  function downloadSampleCsv() { downloadWithAuth('/api/admin/registrations/sample.csv', 'registration_upload_template.csv', setError); }
  async function uploadCsv(event) { event.preventDefault(); setError(''); setNotice(''); setUploadResult(null); if (!uploadFile) { setError('Please select a CSV file.'); return; } const fd = new FormData(); fd.append('file', uploadFile); setUploading(true); try { const data = await apiFetch(`/api/admin/registrations/upload-csv?default_status=${encodeURIComponent(uploadStatus)}`, { method: 'POST', body: fd, skipJsonHeader: true }); setUploadResult(data); setNotice(`CSV import complete. Inserted ${data.inserted}, updated ${data.updated}.`); await load(); onChanged?.(); } catch (err) { setError(err.message); } finally { setUploading(false); } }
  function createTestData() { apiFetch('/api/admin/test-data?count=500', { method: 'POST' }).then((d) => { setNotice(`Created ${d.created} test records.`); load(); onChanged?.(); }).catch((e) => setError(e.message)); }
  return <section className="card"><div className="report-header"><div><h2>Registration Report</h2><p className="muted">List, approve and shortlist registered audience members.</p></div><div className="button-row"><button onClick={load}>Refresh</button><button onClick={downloadCsv}>Export CSV</button>{user.role !== 'Viewer' && <button className="primary" onClick={() => setUploadOpen(true)}>Upload Registrations CSV</button>}{user.role !== 'Viewer' && <button onClick={downloadSampleCsv}>Sample CSV</button>}{user.role === 'Super Admin' && <button className="ai-button" onClick={createAiProposal} disabled={aiLoading}>{aiLoading ? 'Creating AI Mix...' : 'Use AI: Create Approval Mix'}</button>}{user.role === 'Super Admin' && <button className="primary" onClick={bulkApprove}>Approve Selected</button>}{user.role === 'Super Admin' && <button onClick={createTestData}>Create Test Data 500</button>}</div></div>
    {notice && <div className="notice success">{notice}</div>}{error && <div className="notice error">{error}</div>}
    <div className="filters"><input placeholder="Search name, phone, remarks" value={filters.search} onChange={(e) => setFilters({...filters, search: e.target.value})}/><select value={filters.age_group} onChange={(e) => setFilters({...filters, age_group: e.target.value})}><option value="">All age groups</option>{options.age_groups.map((x) => <option key={x}>{x}</option>)}</select><select value={filters.social_background} onChange={(e) => setFilters({...filters, social_background: e.target.value})}><option value="">All backgrounds</option>{options.social_backgrounds.map((x) => <option key={x}>{x}</option>)}</select><select value={filters.primary_language} onChange={(e) => setFilters({...filters, primary_language: e.target.value})}><option value="">All languages</option>{options.primary_languages.map((x) => <option key={x}>{x}</option>)}</select><select value={filters.selection_status} onChange={(e) => setFilters({...filters, selection_status: e.target.value})}><option value="">All statuses</option>{options.statuses.map((x) => <option key={x}>{x}</option>)}</select><button className="primary" onClick={load}>Apply</button></div>
    <div className="table-wrap"><table><thead><tr>{user.role === 'Super Admin' && <th><input type="checkbox" checked={items.length > 0 && selectedIds.length === items.length} onChange={(e) => toggleAll(e.target.checked)} /></th>}<th>Name</th><th>Age</th><th>Social Background</th><th>Language</th><th>Phone</th><th>Remarks</th><th>Status</th><th>Admin Remarks</th><th>Created</th><th>Updated</th><th>Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}>{user.role === 'Super Admin' && <td><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={(e) => toggleSelected(item.id, e.target.checked)} /></td>}<td>{item.name}</td><td>{item.age_group}</td><td>{item.social_background}</td><td>{item.primary_language}</td><td>{item.phone_number}</td><td className="remarks-cell">{item.remarks || '-'}</td><td><select disabled={user.role === 'Viewer'} className="compact-select" value={item.selection_status} onChange={(e) => changeStatus(item, e.target.value)}>{options.statuses.map((x) => <option key={x}>{x}</option>)}</select></td><td className="remarks-cell">{item.admin_remarks || '-'}</td><td>{formatDate(item.created_at)}</td><td>{formatDate(item.updated_at)}</td><td className="nowrap">{user.role !== 'Viewer' && <button onClick={() => setEditing(item)}>Edit</button>}{user.role === 'Super Admin' && <button className="danger" onClick={() => deleteItem(item)}>Delete</button>}</td></tr>)}{!items.length && <tr><td colSpan="12" className="empty">No registrations found.</td></tr>}</tbody></table></div>
    {aiProposal && <AiProposalModal proposal={aiProposal} onClose={() => setAiProposal(null)} onApprove={approveAiProposal} />}
    {uploadOpen && <Modal title="Upload Registrations CSV" onClose={() => { setUploadOpen(false); setUploadResult(null); }}><form onSubmit={uploadCsv} className="grid-form one-col"><p className="muted">Upload a CSV with columns such as Name, Age Group, Social Background, Primary Language, Phone Number, Remarks and Selection Status. Phone Number is used to update existing records.</p><label>Default Status<select value={uploadStatus} onChange={(e) => setUploadStatus(e.target.value)}>{options.statuses.map((x) => <option key={x}>{x}</option>)}</select></label><label>CSV File<input type="file" accept=".csv,text/csv" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} required /></label><div className="button-row"><button className="primary" disabled={uploading}>{uploading ? 'Uploading...' : 'Upload and Import'}</button><button type="button" onClick={downloadSampleCsv}>Download Sample CSV</button></div>{uploadResult && <div className="notice success"><b>Import Summary</b><br/>Inserted: {uploadResult.inserted} | Updated: {uploadResult.updated} | Errors: {uploadResult.error_count}{uploadResult.errors?.length ? <div className="upload-errors"><b>First errors/warnings:</b>{uploadResult.errors.slice(0, 10).map((e, idx) => <div key={idx}>Row {e.row || '-'}: {e.error} {e.phone_number ? `(${e.phone_number})` : ''}</div>)}</div> : null}</div>}</form></Modal>}
    {editing && <Modal title="Edit Registration" onClose={() => setEditing(null)}><form onSubmit={saveEdit} className="grid-form"><label>Name<input value={editing.name} onChange={(e) => setEditing({...editing, name: e.target.value})} required /></label><label>Phone<input value={editing.phone_number} onChange={(e) => setEditing({...editing, phone_number: e.target.value})} required /></label><label>Age<select value={editing.age_group} onChange={(e) => setEditing({...editing, age_group: e.target.value})}>{options.age_groups.map((x) => <option key={x}>{x}</option>)}</select></label><label>Social<select value={editing.social_background} onChange={(e) => setEditing({...editing, social_background: e.target.value})}>{options.social_backgrounds.map((x) => <option key={x}>{x}</option>)}</select></label><label>Language<select value={editing.primary_language} onChange={(e) => setEditing({...editing, primary_language: e.target.value})}>{options.primary_languages.map((x) => <option key={x}>{x}</option>)}</select></label><label>Status<select value={editing.selection_status} onChange={(e) => setEditing({...editing, selection_status: e.target.value})}>{options.statuses.map((x) => <option key={x}>{x}</option>)}</select></label><label className="full-width">Remarks<textarea value={editing.remarks || ''} onChange={(e) => setEditing({...editing, remarks: e.target.value})}/></label><label className="full-width">Admin Remarks<textarea value={editing.admin_remarks || ''} onChange={(e) => setEditing({...editing, admin_remarks: e.target.value})}/></label><div className="button-row full-width"><button className="primary">Save</button><button type="button" onClick={() => setEditing(null)}>Cancel</button></div></form></Modal>}
  </section>;
}

function AiProposalModal({ proposal, onClose, onApprove }) {
  const selected = proposal.selected || [];
  function distRows(label, dist) { return <div className="dist-card"><h4>{label}</h4>{Object.entries(dist || {}).map(([k, v]) => <div key={k} className="dist-row"><span>{k}</span><b>{v}</b></div>)}{!Object.keys(dist || {}).length && <p className="muted tiny">No records</p>}</div>; }
  return <Modal title="AI Approval Mix Proposal" onClose={onClose}>
    <div className="notice"><b>Review first:</b> This AI-assisted proposal balances age groups, social backgrounds and primary languages. Records are not changed until you click Approve AI Proposal.</div>
    <div className="stats-grid compact-stats">
      <div className="stat-card"><span>Approval Target</span><strong>{proposal.target_approval_count}</strong></div>
      <div className="stat-card"><span>Already Approved</span><strong>{proposal.existing_approved_count}</strong></div>
      <div className="stat-card highlight"><span>Proposed Now</span><strong>{proposal.proposed_count}</strong></div>
      <div className="stat-card"><span>Candidates Checked</span><strong>{proposal.candidates_considered}</strong></div>
    </div>
    <div className="dist-grid">
      {distRows('Age Group Mix', proposal.proposal_distribution?.age_group)}
      {distRows('Social Background Mix', proposal.proposal_distribution?.social_background)}
      {distRows('Language Mix', proposal.proposal_distribution?.primary_language)}
    </div>
    <ul className="proposal-notes">{(proposal.notes || []).map((note) => <li key={note}>{note}</li>)}</ul>
    <div className="table-wrap proposal-table"><table><thead><tr><th>Name</th><th>Age</th><th>Social Background</th><th>Language</th><th>Phone</th><th>Current Status</th></tr></thead><tbody>{selected.map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.age_group}</td><td>{item.social_background}</td><td>{item.primary_language}</td><td>{item.phone_number}</td><td>{item.selection_status}</td></tr>)}{!selected.length && <tr><td colSpan="6" className="empty">No eligible records were found for approval.</td></tr>}</tbody></table></div>
    <div className="button-row left-actions"><button className="primary" disabled={!selected.length} onClick={onApprove}>Approve AI Proposal</button><button onClick={onClose}>Close</button></div>
  </Modal>;
}

function ScreeningDetails({ options, user, onPublicRefresh }) {
  const canEdit = user.role !== 'Viewer'; const [items, setItems] = useState([]); const [form, setForm] = useState(emptyScreeningDetails); const [posterFile, setPosterFile] = useState(null); const [editingId, setEditingId] = useState(null); const [filters, setFilters] = useState({ search: '', film_language: '', genre: '' }); const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [saving, setSaving] = useState(false);
  async function load() { setError(''); try { const query = new URLSearchParams(filters).toString(); const data = await apiFetch(`/api/admin/screening-details?${query}`); setItems(data.items || []); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  function update(field, value) { setForm((prev) => ({...prev, [field]: value})); }
  function payload() { return { ...form, duration_minutes: form.duration_minutes ? Number(form.duration_minutes) : null, expected_audience_count: form.expected_audience_count ? Number(form.expected_audience_count) : 0, actual_audience_count: form.actual_audience_count ? Number(form.actual_audience_count) : 0 }; }
  async function save(event) { event.preventDefault(); setSaving(true); setError(''); setNotice(''); try { const saved = editingId ? await apiFetch(`/api/admin/screening-details/${editingId}`, { method: 'PUT', body: JSON.stringify(payload()) }) : await apiFetch('/api/admin/screening-details', { method: 'POST', body: JSON.stringify(payload()) }); if (posterFile) { const fd = new FormData(); fd.append('poster', posterFile); await apiFetch(`/api/admin/screening-details/${saved.id}/poster`, { method: 'POST', body: fd }); } setNotice('Film and audience details saved. Landing page updated.'); setForm(emptyScreeningDetails); setPosterFile(null); setEditingId(null); await load(); onPublicRefresh?.(); } catch (err) { setError(err.message); } finally { setSaving(false); } }
  function edit(item) { setEditingId(item.id); setPosterFile(null); setForm({ ...emptyScreeningDetails, ...item, duration_minutes: item.duration_minutes || '', actual_audience_count: item.actual_audience_count || '' }); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  async function deleteItem(id) { if (!confirm('Delete this screening details record?')) return; try { await apiFetch(`/api/admin/screening-details/${id}`, { method: 'DELETE' }); setNotice('Screening details deleted.'); await load(); onPublicRefresh?.(); } catch (err) { setError(err.message); } }
  function downloadCsv() { downloadWithAuth('/api/admin/screening-details/export.csv', `screening_details_${dateStamp()}.csv`, setError); }
  return <section className="card"><div className="report-header"><div><h2>Film & Audience Details</h2><p className="muted">This page controls the landing page content, date/time, poster, venue, and audience demographic mix.</p></div><div className="button-row"><button onClick={load}>Refresh</button><button onClick={downloadCsv}>Export CSV</button></div></div>{notice && <div className="notice success">{notice}</div>}{error && <div className="notice error">{error}</div>}
    {canEdit && <form onSubmit={save} className="grid-form screening-form"><label>Film Title <span>*</span><input value={form.film_title} onChange={(e) => update('film_title', e.target.value)} required /></label><label>Film Language <span>*</span><select value={form.film_language} onChange={(e) => update('film_language', e.target.value)} required><option value="">Select</option>{options.film_languages.map((x) => <option key={x}>{x}</option>)}</select></label><label>Genre <span>*</span><select value={form.genre} onChange={(e) => update('genre', e.target.value)} required><option value="">Select</option>{options.film_genres.map((x) => <option key={x}>{x}</option>)}</select></label><label>Duration, minutes<input type="number" min="1" max="400" value={form.duration_minutes || ''} onChange={(e) => update('duration_minutes', e.target.value)} /></label><label>Director<input value={form.director || ''} onChange={(e) => update('director', e.target.value)} /></label><label>Producer<input value={form.producer || ''} onChange={(e) => update('producer', e.target.value)} /></label><label>Screening Date<input type="date" value={form.screening_date || ''} onChange={(e) => update('screening_date', e.target.value)} /></label><label>Screening Time<input type="time" value={(form.screening_time || '').slice(0,5)} onChange={(e) => update('screening_time', e.target.value)} /></label><label>Venue Name<input value={form.venue_name || ''} onChange={(e) => update('venue_name', e.target.value)} placeholder="Theatre / preview room" /></label><label>Venue City<input value={form.venue_city || ''} onChange={(e) => update('venue_city', e.target.value)} /></label><label>Expected Audience Count<input type="number" min="0" value={form.expected_audience_count || ''} onChange={(e) => update('expected_audience_count', e.target.value)} /></label><label>Actual Audience Count<input type="number" min="0" value={form.actual_audience_count || ''} onChange={(e) => update('actual_audience_count', e.target.value)} /></label><label className="full-width">Upload Poster<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setPosterFile(e.target.files?.[0] || null)} /></label><label className="full-width">Short Synopsis<textarea value={form.synopsis || ''} onChange={(e) => update('synopsis', e.target.value)} maxLength="1000" /></label><label className="full-width">Audience Age Mix<textarea value={form.audience_age_mix || ''} onChange={(e) => update('audience_age_mix', e.target.value)} placeholder="Example: 18-25: 8, 26-35: 12, 36-45: 10, 46+: 10" /></label><label className="full-width">Audience Language Mix<textarea value={form.audience_language_mix || ''} onChange={(e) => update('audience_language_mix', e.target.value)} /></label><label className="full-width">Audience Social Background Mix<textarea value={form.audience_social_mix || ''} onChange={(e) => update('audience_social_mix', e.target.value)} /></label><label className="full-width">Remarks<textarea value={form.remarks || ''} onChange={(e) => update('remarks', e.target.value)} /></label><div className="full-width button-row left-actions"><button className="primary" disabled={saving}>{saving ? 'Saving...' : editingId ? 'Update Details' : 'Save Details'}</button>{editingId && <button type="button" onClick={() => { setEditingId(null); setForm(emptyScreeningDetails); }}>Cancel Edit</button>}</div></form>}
    <div className="filters screening-filters"><input placeholder="Search film, director, producer, venue" value={filters.search} onChange={(e) => setFilters({...filters, search: e.target.value})}/><select value={filters.film_language} onChange={(e) => setFilters({...filters, film_language: e.target.value})}><option value="">All languages</option>{options.film_languages.map((x) => <option key={x}>{x}</option>)}</select><select value={filters.genre} onChange={(e) => setFilters({...filters, genre: e.target.value})}><option value="">All genres</option>{options.film_genres.map((x) => <option key={x}>{x}</option>)}</select><button className="primary" onClick={load}>Apply</button></div>
    <div className="table-wrap"><table className="wide-table"><thead><tr><th>Poster</th><th>Film</th><th>Language</th><th>Genre</th><th>Director</th><th>Screening</th><th>Venue</th><th>Expected</th><th>Actual</th><th>Audience Demographics</th><th>Updated</th><th>Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.poster_url && <img className="thumb" src={assetUrl(item.poster_url)} />}</td><td><b>{item.film_title}</b><br/><span className="muted">{item.synopsis || '-'}</span></td><td>{item.film_language}</td><td>{item.genre}</td><td>{item.director || '-'}</td><td>{formatDateOnly(item.screening_date)} {formatTimeText(item.screening_time)}</td><td>{[item.venue_name, item.venue_city].filter(Boolean).join(', ') || '-'}</td><td>{item.expected_audience_count}</td><td>{item.actual_audience_count}</td><td className="remarks-cell"><b>Age:</b> {item.audience_age_mix || '-'}<br/><b>Language:</b> {item.audience_language_mix || '-'}<br/><b>Social:</b> {item.audience_social_mix || '-'}</td><td>{formatDate(item.updated_at)}</td><td className="nowrap">{canEdit ? <button onClick={() => edit(item)}>Edit</button> : <span className="muted">View only</span>}{user.role === 'Super Admin' && <button className="danger" onClick={() => deleteItem(item.id)}>Delete</button>}</td></tr>)}{!items.length && <tr><td colSpan="12" className="empty">No screening details found.</td></tr>}</tbody></table></div>
  </section>;
}

function SurveyReport({ options, onChanged }) {
  const [items, setItems] = useState([]); const [filters, setFilters] = useState({ search: '', would_recommend: '' }); const [error, setError] = useState('');
  async function load() { setError(''); try { const query = new URLSearchParams(filters).toString(); const data = await apiFetch(`/api/admin/surveys?${query}`); setItems(data.items || []); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  function downloadCsv() { downloadWithAuth('/api/admin/surveys/export.csv', `survey_responses_${dateStamp()}.csv`, setError); }
  return <section className="card"><div className="report-header"><div><h2>Audience Survey Report</h2><p className="muted">Feedback submitted by registered audience after the screening.</p></div><div className="button-row">
              <button onClick={() => downloadAdminCsv('/api/admin/survey-responses/export', 'feedback_responses.csv')}>Download Feedback CSV</button><button onClick={load}>Refresh</button><button onClick={downloadCsv}>Export CSV</button></div></div>{error && <div className="notice error">{error}</div>}<div className="filters small-filters"><input placeholder="Search name, phone, comments" value={filters.search} onChange={(e) => setFilters({...filters, search: e.target.value})}/><select value={filters.would_recommend} onChange={(e) => setFilters({...filters, would_recommend: e.target.value})}><option value="">All recommendation</option>{options.yes_no_maybe.map((x) => <option key={x}>{x}</option>)}</select><button className="primary" onClick={load}>Apply</button></div><div className="table-wrap"><table className="wide-table"><thead><tr><th>Name</th><th>Phone</th><th>Overall</th><th>Story</th><th>Acting</th><th>Music</th><th>Pace</th><th>Emotion</th><th>Visual</th><th>Dialogue</th><th>Length</th><th>Understood</th><th>Characters</th><th>Audience</th><th>Theatre/OTT</th><th>One Word</th><th>Recommend</th><th>Quote OK</th><th>Liked Most</th><th>Improve</th><th>Memorable</th><th>Contact</th><th>Remarks</th><th>Created</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.phone_number}</td><td><b>{item.overall_rating}</b></td><td>{item.story_rating}</td><td>{item.acting_rating}</td><td>{item.music_rating}</td><td>{item.pace_rating}</td><td>{item.emotional_impact_rating}</td><td>{item.visual_quality_rating}</td><td>{item.dialogue_rating}</td><td>{item.length_rating}</td><td>{item.understood_story}</td><td>{item.connected_with_characters || '-'}</td><td>{item.preferred_audience || item.audience_type || '-'}</td><td>{item.theatre_or_ott || '-'}</td><td>{item.one_word_reaction || '-'}</td><td>{item.would_recommend}</td><td>{item.consent_quote || 'No'}</td><td className="remarks-cell">{item.liked_most || '-'}</td><td className="remarks-cell">{item.improvements || '-'}</td><td className="remarks-cell">{item.memorable_scene || '-'}</td><td>{item.contact_permission}</td><td className="remarks-cell">{item.remarks || '-'}</td><td>{formatDate(item.created_at)}</td></tr>)}{!items.length && <tr><td colSpan="24" className="empty">No survey responses found.</td></tr>}</tbody></table></div></section>;
}


function SurveyBuilder({ onPublicRefresh }) {
  const [builder, setBuilder] = useState({ sections: [] });
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [sectionForm, setSectionForm] = useState({ title: '', description: '', display_order: 10, is_active: true });
  const [questionForm, setQuestionForm] = useState({ section_id: '', question_text: '', question_type: 'short_text', options_text: '', is_required: false, display_order: 10, is_active: true });
  async function load() { try { const data = await apiFetch('/api/admin/survey-builder'); const safeData = data || { sections: [] }; setBuilder(safeData); if (!questionForm.section_id && safeData.sections?.[0]) setQuestionForm((p) => ({ ...p, section_id: safeData.sections[0].id })); } catch (err) { setBuilder({ sections: [] }); setError(err.message || 'Unable to load survey builder. Please confirm backend is running.'); } }
  useEffect(() => { load(); }, []);
  async function addSection(e) { e.preventDefault(); setError(''); setNotice(''); try { await apiFetch('/api/admin/survey-sections', { method: 'POST', body: JSON.stringify(sectionForm) }); setSectionForm({ title: '', description: '', display_order: 10, is_active: true }); setNotice('Survey section added.'); await load(); await onPublicRefresh?.(); } catch (err) { setError(err.message); } }
  async function addQuestion(e) { e.preventDefault(); setError(''); setNotice(''); try { const payload = { ...questionForm, section_id: Number(questionForm.section_id), options: questionForm.options_text.split('\n').map((x) => x.trim()).filter(Boolean) }; delete payload.options_text; await apiFetch('/api/admin/survey-questions', { method: 'POST', body: JSON.stringify(payload) }); setQuestionForm((p) => ({ ...p, question_text: '', options_text: '' })); setNotice('Question added.'); await load(); await onPublicRefresh?.(); } catch (err) { setError(err.message); } }
  async function hideQuestion(qid) { try { await apiFetch(`/api/admin/survey-questions/${qid}`, { method: 'DELETE' }); setNotice('Question hidden.'); await load(); await onPublicRefresh?.(); } catch (err) { setError(err.message); } }
  return <section className="card"><div className="report-header"><div><h2>Survey Builder</h2><p className="muted">Build the feedback survey section by section. Supports multiple choice and short text questions.</p></div></div>{notice && <div className="notice success">{notice}</div>}{error && <div className="notice error">{error}</div>}
    <div className="two-col-admin">
      <form className="grid-form one-col" onSubmit={addSection}><h3>Add Section</h3><label>Section Title<input value={sectionForm.title} onChange={(e) => setSectionForm({ ...sectionForm, title: e.target.value })} required /></label><label>Description<textarea value={sectionForm.description} onChange={(e) => setSectionForm({ ...sectionForm, description: e.target.value })} /></label><label>Display Order<input type="number" value={sectionForm.display_order} onChange={(e) => setSectionForm({ ...sectionForm, display_order: Number(e.target.value) })} /></label><label className="toggle-row"><input type="checkbox" checked={sectionForm.is_active} onChange={(e) => setSectionForm({ ...sectionForm, is_active: e.target.checked })} /> Active</label><button className="primary">Add Section</button></form>
      <form className="grid-form one-col" onSubmit={addQuestion}><h3>Add Question</h3><label>Section<select value={questionForm.section_id} onChange={(e) => setQuestionForm({ ...questionForm, section_id: e.target.value })} required>{(builder.sections || []).map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</select></label><label>Question<input value={questionForm.question_text} onChange={(e) => setQuestionForm({ ...questionForm, question_text: e.target.value })} required /></label><label>Question Type<select value={questionForm.question_type} onChange={(e) => setQuestionForm({ ...questionForm, question_type: e.target.value })}><option value="short_text">Short text</option><option value="multiple_choice">Multiple choice</option></select></label><label>Options for Multiple Choice<textarea value={questionForm.options_text} onChange={(e) => setQuestionForm({ ...questionForm, options_text: e.target.value })} placeholder="One option per line" /></label><label>Display Order<input type="number" value={questionForm.display_order} onChange={(e) => setQuestionForm({ ...questionForm, display_order: Number(e.target.value) })} /></label><label className="toggle-row"><input type="checkbox" checked={questionForm.is_required} onChange={(e) => setQuestionForm({ ...questionForm, is_required: e.target.checked })} /> Required</label><button className="primary">Add Question</button></form>
    </div>
    <h3>Current Survey Structure</h3>{(builder.sections || []).map((section) => <div className="builder-section" key={section.id}><h4>{section.title}</h4><p className="muted">{section.description}</p>{(section.questions || []).map((q) => <div className="question-row" key={q.id}><div><b>#{q.display_order}</b> {q.question_text}<br/><span className="muted">{q.question_type}{q.is_required ? ' · required' : ''}{q.options?.length ? ` · Options: ${q.options.join(', ')}` : ''}</span></div><button className="danger" onClick={() => hideQuestion(q.id)}>Hide</button></div>)}</div>)}</section>;
}


function MiniBarChart({ title, data = [], labelKey = 'label', valueKey = 'count' }) {
  const clean = (data || []).filter((x) => x && x[labelKey] !== undefined).slice(0, 10);
  const max = Math.max(1, ...clean.map((x) => Number(x[valueKey] || 0)));
  return (
    <div className="viz-card">
      <h4>{title}</h4>
      {clean.length === 0 ? <p className="muted">No data yet.</p> : clean.map((row, idx) => (
        <div className="bar-row" key={`${row[labelKey]}-${idx}`}>
          <span>{row[labelKey] || 'Unknown'}</span>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(4, (Number(row[valueKey] || 0) / max) * 100)}%` }} /></div>
          <strong>{row[valueKey] || 0}</strong>
        </div>
      ))}
    </div>
  );
}

function MiniScoreChart({ title, scores = [] }) {
  const clean = (scores || []).filter((x) => x && x.label);
  return (
    <div className="viz-card">
      <h4>{title}</h4>
      {clean.length === 0 ? <p className="muted">No ratings yet.</p> : clean.map((row, idx) => (
        <div className="score-row" key={`${row.label}-${idx}`}>
          <span>{row.label}</span>
          <div className="score-track"><div className="score-fill" style={{ width: `${Math.min(100, Math.max(0, (Number(row.value || 0) / 5) * 100))}%` }} /></div>
          <strong>{Number(row.value || 0).toFixed(1)}</strong>
        </div>
      ))}
    </div>
  );
}

function AnalyticsVisuals({ analytics }) {
  const registration = analytics?.registration || analytics?.registrations || {};
  const feedback = analytics?.feedback || {};
  const ratings = feedback.average_ratings || feedback.ratings || {};
  const ratingRows = [
    { label: 'Overall', value: ratings.overall_rating || ratings.overall || 0 },
    { label: 'Story', value: ratings.story_rating || ratings.story || 0 },
    { label: 'Acting', value: ratings.acting_rating || ratings.acting || 0 },
    { label: 'Music', value: ratings.music_rating || ratings.music || 0 },
    { label: 'Pace', value: ratings.pace_rating || ratings.pace || 0 },
    { label: 'Emotional impact', value: ratings.emotional_impact_rating || ratings.emotional_impact || 0 },
  ];
  return (
    <div className="analytics-viz-grid">
      <MiniBarChart title="Audience by status" data={registration.status_mix || registration.status || []} />
      <MiniBarChart title="Audience by age group" data={registration.age_group_mix || registration.age_groups || []} />
      <MiniBarChart title="Audience by language" data={registration.primary_language_mix || registration.languages || []} />
      <MiniScoreChart title="Feedback rating averages" scores={ratingRows} />
      <MiniBarChart title="Recommendation response" data={feedback.recommendation_mix || feedback.recommendations || []} />
      <MiniBarChart title="Repeated feedback themes" data={feedback.theme_counts || feedback.repeated_themes || []} />
    </div>
  );
}

function AnalyticsPage() {
  const [registrationData, setRegistrationData] = useState(null);
  const [feedbackData, setFeedbackData] = useState(null);
  const [error, setError] = useState('');
  async function load() {
    setError('');
    try {
      const [reg, fb] = await Promise.all([
        apiFetch('/api/admin/registration-analytics'),
        apiFetch('/api/admin/survey-analytics'),
      ]);
      setRegistrationData(reg);
      setFeedbackData(fb);
    } catch (err) { setError(err.message); }
  }
  useEffect(() => { load(); }, []);
  if (error) return <section className="card"><div className="notice error">{error}</div></section>;
  if (!registrationData || !feedbackData) return <section className="card">Loading analytics...</section>;
  return <section className="card analytics-page">
    <div className="report-header"><div><h2>Analytics</h2><p className="muted">Registration and feedback analytics in one place for screening review.</p></div><div className="button-row"><button onClick={() => downloadAdminCsv('/api/admin/survey-responses/export', 'feedback_responses.csv')}>Download Feedback CSV</button><button onClick={load}>Refresh</button><button onClick={() => apiFetch('/api/admin/test-data?count=80', { method: 'POST' }).then(load)}>Create Test Data</button></div></div>
    <RegistrationAnalytics data={registrationData} />
    <FeedbackAnalyticsBlock data={feedbackData} />
  </section>;
}

function RegistrationAnalytics({ data }) {
  return <div className="analytics-block"><h3>1. Registration Analytics</h3>
    <div className="stats-grid">
      <div className="stat-card highlight"><span>Total Registrations</span><strong>{data.total}</strong></div>
      <div className="stat-card"><span>Expected Capacity</span><strong>{data.expected_capacity}</strong></div>
      <div className="stat-card"><span>Approved / Shortlisted / Attended</span><strong>{data.approved_like}</strong></div>
      <div className="stat-card"><span>Waitlisted</span><strong>{data.waitlisted}</strong></div>
      <div className="stat-card"><span>Rejected</span><strong>{data.rejected}</strong></div>
      <div className="stat-card"><span>Feedback Received</span><strong>{data.feedback_from_registered}</strong></div>
    </div>
    <div className="analytics-viz-grid">
      <MiniBarChart title="Status Mix" data={data.demographics.selection_status || []} valueKey="value" />
      <MiniBarChart title="Age Group Mix" data={data.demographics.age_group || []} valueKey="value" />
      <MiniBarChart title="Language Mix" data={data.demographics.primary_language || []} valueKey="value" />
      <MiniBarChart title="Daily Registration Trend" data={data.daily_registrations || []} valueKey="value" />
    </div>
    <div className="notice success"><b>AI-assisted registration view</b><ul>{(data.ai_insights || []).map((x) => <li key={x}>{x}</li>)}</ul></div>
    <div className="dist-grid">
      <Distribution title="Status Mix" items={data.demographics.selection_status} />
      <Distribution title="Age Group Mix" items={data.demographics.age_group} />
      <Distribution title="Social Background Mix" items={data.demographics.social_background} />
      <Distribution title="Primary Language Mix" items={data.demographics.primary_language} />
    </div>
    <h4>Daily Registration Trend</h4>
    <div className="table-wrap"><table><thead><tr><th>Date</th><th>Registrations</th></tr></thead><tbody>{(data.daily_registrations || []).map((r) => <tr key={r.label}><td>{r.label}</td><td>{r.value}</td></tr>)}{!(data.daily_registrations || []).length && <tr><td colSpan="2" className="empty">No registrations yet.</td></tr>}</tbody></table></div>
  </div>;
}

function FeedbackAnalyticsBlock({ data }) {
  return <div className="analytics-block"><h3>2. Feedback Analytics</h3>
    <div className="stats-grid">
      <div className="stat-card highlight"><span>Feedback Responses</span><strong>{data.feedback_total}</strong></div>
      <div className="stat-card"><span>Overall Avg</span><strong>{data.average_ratings.overall_rating}</strong></div>
      <div className="stat-card"><span>Story Avg</span><strong>{data.average_ratings.story_rating}</strong></div>
      <div className="stat-card"><span>Pace Avg</span><strong>{data.average_ratings.pace_rating}</strong></div>
      <div className="stat-card"><span>Emotion Avg</span><strong>{data.average_ratings.emotional_impact_rating}</strong></div>
      <div className="stat-card"><span>Length Avg</span><strong>{data.average_ratings.length_rating}</strong></div>
    </div>
    <div className="analytics-viz-grid">
      <MiniScoreChart title="Feedback Rating Averages" scores={[
        { label: 'Overall', value: data.average_ratings.overall_rating || 0 },
        { label: 'Story', value: data.average_ratings.story_rating || 0 },
        { label: 'Pace', value: data.average_ratings.pace_rating || 0 },
        { label: 'Emotion', value: data.average_ratings.emotional_impact_rating || 0 },
        { label: 'Length', value: data.average_ratings.length_rating || 0 },
      ]} />
      <MiniBarChart title="Feedback Age Group" data={data.demographics.age_group || []} valueKey="value" />
      <MiniBarChart title="Feedback Language" data={data.demographics.primary_language || []} valueKey="value" />
      <MiniBarChart title="Top Multiple Choice Answers" data={(data.multiple_choice_distribution || []).slice(0, 8).map((x) => ({ label: `${x.question_text}: ${x.label}`, value: x.value }))} valueKey="value" />
    </div>
    <div className="notice success"><b>AI-assisted feedback view</b><ul>{(data.ai_insights || []).map((x) => <li key={x}>{x}</li>)}</ul></div>
    <div className="dist-grid">
      <Distribution title="Age Group" items={data.demographics.age_group} />
      <Distribution title="Social Background" items={data.demographics.social_background} />
      <Distribution title="Primary Language" items={data.demographics.primary_language} />
    </div>
    <h4>Multiple Choice Answer Distribution</h4>
    <div className="table-wrap"><table><thead><tr><th>Question</th><th>Answer</th><th>Count</th></tr></thead><tbody>{(data.multiple_choice_distribution || []).map((r, i) => <tr key={i}><td>{r.question_text}</td><td>{r.label}</td><td>{r.value}</td></tr>)}{!(data.multiple_choice_distribution || []).length && <tr><td colSpan="3" className="empty">No multiple choice answers yet.</td></tr>}</tbody></table></div>
    <h4>Repeated Text Themes</h4>
    <div className="dist-grid">{Object.entries(data.themes || {}).map(([k, v]) => <div className="dist-card" key={k}><h4>{k}</h4><strong>{v}</strong></div>)}</div>
  </div>;
}

function SurveyAnalytics() {
  const [data, setData] = useState(null); const [error, setError] = useState('');
  async function load() { try { setData(await apiFetch('/api/admin/survey-analytics')); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  if (error) return <section className="card"><div className="notice error">{error}</div></section>;
  if (!data) return <section className="card">Loading analytics...</section>;
  return <section className="card"><div className="report-header"><div><h2>Feedback Analytics</h2><p className="muted">Rating trends, demographic mix, answer distribution and AI-assisted insight summary.</p></div><div className="button-row"><button onClick={load}>Refresh</button><button onClick={() => apiFetch('/api/admin/test-data?count=80', { method: 'POST' }).then(load)}>Create Test Data</button></div></div>
    <div className="stats-grid"><div className="stat-card highlight"><span>Registrations</span><strong>{data.registration_total}</strong></div><div className="stat-card"><span>Feedback</span><strong>{data.feedback_total}</strong></div><div className="stat-card"><span>Overall Avg</span><strong>{data.average_ratings.overall_rating}</strong></div><div className="stat-card"><span>Pace Avg</span><strong>{data.average_ratings.pace_rating}</strong></div><div className="stat-card"><span>Emotion Avg</span><strong>{data.average_ratings.emotional_impact_rating}</strong></div><div className="stat-card"><span>Length Avg</span><strong>{data.average_ratings.length_rating}</strong></div></div>
    <h3>AI-assisted Insights</h3><div className="notice success"><ul>{(data.ai_insights || []).map((x) => <li key={x}>{x}</li>)}</ul></div>
    <h3>Demographic Mix</h3><div className="dist-grid"><Distribution title="Age Group" items={data.demographics.age_group} /><Distribution title="Social Background" items={data.demographics.social_background} /><Distribution title="Primary Language" items={data.demographics.primary_language} /></div>
    <h3>Multiple Choice Answer Distribution</h3><div className="table-wrap"><table><thead><tr><th>Question</th><th>Answer</th><th>Count</th></tr></thead><tbody>{(data.multiple_choice_distribution || []).map((r, i) => <tr key={i}><td>{r.question_text}</td><td>{r.label}</td><td>{r.value}</td></tr>)}{!(data.multiple_choice_distribution || []).length && <tr><td colSpan="3" className="empty">No multiple choice answers yet.</td></tr>}</tbody></table></div>
    <h3>Repeated Text Themes</h3><div className="dist-grid">{Object.entries(data.themes || {}).map(([k, v]) => <div className="dist-card" key={k}><h4>{k}</h4><strong>{v}</strong></div>)}</div>
  </section>;
}
function Distribution({ title, items }) { return <div className="dist-card"><h4>{title}</h4>{(items || []).map((x) => <div className="dist-row" key={x.label}><span>{x.label || 'Not specified'}</span><b>{x.value}</b></div>)}</div>; }

function PageSettings({ onPublicRefresh }) {
  const [settings, setSettings] = useState({ show_registration_button: true, show_survey_button: true, show_feedback_qr_button: true });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  async function load() {
    try {
      const data = await apiFetch('/api/admin/landing-buttons');
      setSettings({
        show_registration_button: data.show_registration_button !== false,
        show_survey_button: data.show_survey_button !== false,
        show_feedback_qr_button: data.show_feedback_qr_button !== false,
      });
    } catch (err) { setError(err.message); }
  }
  useEffect(() => { load(); }, []);
  function update(field, value) { setSettings((prev) => ({ ...prev, [field]: value })); }
  async function save() {
    setError(''); setNotice('');
    try {
      const data = await apiFetch('/api/admin/landing-buttons', { method: 'PUT', body: JSON.stringify(settings) });
      setSettings({
        show_registration_button: data.show_registration_button !== false,
        show_survey_button: data.show_survey_button !== false,
        show_feedback_qr_button: data.show_feedback_qr_button !== false,
      });
      await onPublicRefresh?.();
      setNotice('Landing page button settings updated. These settings affect only the landing page buttons. Login and Super Admin access are always available.');
    } catch (err) { setError(err.message); }
  }
  return <section className="card"><h2>Landing Page Button Settings</h2><p className="muted">Use this page only to show or hide landing page actions. This does not hide public menu links, admin menu items, admin actions, Login, or Super Admin access.</p>{notice && <div className="notice success">{notice}</div>}{error && <div className="notice error">{error}</div>}
    <div className="settings-box"><h3>Landing Page Buttons</h3><div className="grid-form">
      <label className="toggle-row"><input type="checkbox" checked={!!settings.show_registration_button} onChange={(e) => update('show_registration_button', e.target.checked)} /> Show Registration button on landing page</label>
      <label className="toggle-row"><input type="checkbox" checked={!!settings.show_survey_button} onChange={(e) => update('show_survey_button', e.target.checked)} /> Show Post-Screening Survey button on landing page</label>
      <label className="toggle-row"><input type="checkbox" checked={settings.show_feedback_qr_button !== false} onChange={(e) => update('show_feedback_qr_button', e.target.checked)} /> Show Feedback QR link on landing page</label>
    </div></div>
    <div className="notice"><b>Note:</b> These settings apply only to the landing page actions. The Registration and Survey pages remain accessible through the menu and admin workflow. Super Admin always sees the buttons on the landing page.</div>
    <div className="button-row left-actions"><button className="primary" onClick={save}>Save Button Settings</button></div></section>;
}

function Users({ options }) {
  const [items, setItems] = useState([]); const [form, setForm] = useState(emptyUser); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  async function load() { try { const data = await apiFetch('/api/admin/users'); setItems(data.items || []); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  function update(field, value) { setForm((prev) => ({...prev, [field]: value})); }
  async function create(event) { event.preventDefault(); setError(''); setNotice(''); try { await apiFetch('/api/admin/users', { method: 'POST', body: JSON.stringify(form) }); setNotice('Admin user created.'); setForm(emptyUser); await load(); } catch (err) { setError(err.message); } }
  async function setActive(item, is_active) { try { await apiFetch(`/api/admin/users/${item.id}/status`, { method: 'PUT', body: JSON.stringify({ is_active }) }); setNotice('User status updated.'); await load(); } catch (err) { setError(err.message); } }
  async function reset(item) { const password = prompt(`Enter new password for ${item.username}`); if (!password) return; try { await apiFetch(`/api/admin/users/${item.id}/reset-password`, { method: 'PUT', body: JSON.stringify({ password }) }); setNotice('Password reset.'); } catch (err) { setError(err.message); } }
  return <section className="card"><h2>User Management</h2><p className="muted">Create admin users and control access.</p>{notice && <div className="notice success">{notice}</div>}{error && <div className="notice error">{error}</div>}<form onSubmit={create} className="grid-form user-form"><label>Full Name<input value={form.full_name} onChange={(e) => update('full_name', e.target.value)} required /></label><label>Username<input value={form.username} onChange={(e) => update('username', e.target.value)} required /></label><label>Phone<input value={form.phone_number} onChange={(e) => update('phone_number', e.target.value)} /></label><label>Password<input value={form.password} onChange={(e) => update('password', e.target.value)} type="password" required minLength="6" /></label><label>Role<select value={form.role} onChange={(e) => update('role', e.target.value)}>{options.roles.map((x) => <option key={x}>{x}</option>)}</select></label><button className="primary">Create User</button></form><div className="table-wrap"><table><thead><tr><th>Name</th><th>Username</th><th>Phone</th><th>Role</th><th>Active</th><th>Last Login</th><th>Created</th><th>Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.full_name}</td><td>{item.username}</td><td>{item.phone_number}</td><td>{item.role}</td><td>{item.is_active ? 'Yes' : 'No'}</td><td>{formatDate(item.last_login_at)}</td><td>{formatDate(item.created_at)}</td><td className="nowrap"><button onClick={() => reset(item)}>Reset Password</button><button onClick={() => setActive(item, !item.is_active)}>{item.is_active ? 'Disable' : 'Enable'}</button></td></tr>)}</tbody></table></div></section>;
}

function AuditLogs() {
  const [items, setItems] = useState([]); const [error, setError] = useState('');
  useEffect(() => { apiFetch('/api/admin/audit-logs').then((data) => setItems(data.items || [])).catch((err) => setError(err.message)); }, []);
  return <section className="card"><h2>Audit Logs</h2>{error && <div className="notice error">{error}</div>}<div className="table-wrap"><table><thead><tr><th>Date</th><th>User</th><th>Module</th><th>Action</th><th>Record</th><th>Old</th><th>New</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{formatDate(item.created_at)}</td><td>{item.username || 'Public/System'}</td><td>{item.module_name}</td><td>{item.action}</td><td>{item.record_id || '-'}</td><td className="log-cell">{item.old_value}</td><td className="log-cell">{item.new_value}</td></tr>)}</tbody></table></div></section>;
}

function Modal({ title, children, onClose }) { return <div className="modal-backdrop"><section className="card modal"><div className="report-header"><h2>{title}</h2><button onClick={onClose}>Close</button></div>{children}</section></div>; }
function downloadWithAuth(path, filename, onError) { const token = localStorage.getItem('payana_admin_token'); fetch(`${API_BASE}${path}`, { headers: { Authorization: `Bearer ${token}` } }).then((res) => { if (!res.ok) throw new Error('Export failed'); return res.blob(); }).then((blob) => { const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url); }).catch((err) => onError(err.message)); }
function dateStamp() { return new Date().toISOString().slice(0, 10); }
function formatDate(value) { if (!value) return '-'; try { return new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }); } catch { return value; } }
function formatDateOnly(value) { if (!value) return ''; try { const [y, m, d] = value.split('-'); if (y && m && d) return new Date(Number(y), Number(m)-1, Number(d)).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }); return value; } catch { return value; } }
function formatTimeText(value) { if (!value) return ''; if (value === '16:00') return '4:00 PM onwards'; const [h, m] = value.split(':'); if (!h) return value; const date = new Date(); date.setHours(Number(h), Number(m || 0), 0); return date.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' }); }

createRoot(document.getElementById('root')).render(<App />);
