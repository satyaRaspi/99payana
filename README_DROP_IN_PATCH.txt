Feedback thank-you page patch v1.2.53

Adds a confirmation page after feedback submission:

"Thank you for submitting. Your feedback has been recorded."

Keeps:
- Mobile wizard feedback format
- Kannada / English toggle
- Poster questions removed

Extract into C:\99mysore and overwrite files.

Contains only:
- frontend/src/main.jsx
- frontend/src/styles.css
- frontend/package.json
- frontend/dist/

Push:
git add -A
git add -f frontend/dist
git commit -m "Add feedback thank you page v1.2.53"
git push -u origin main --force
