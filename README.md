# Medico

Medico is a Streamlit chat app for general health information. It can send a question and, when attached and acknowledged, an image to Google Gemini. It is an educational tool, not a diagnostic service or substitute for a licensed clinician.

## Run locally

1. Use Python 3.10 or newer and create a virtual environment.
2. Install dependencies with: pip install -r requirements.txt
3. Copy .env.example to .env and set GEMINI_API_KEY to your own key.
4. Run: streamlit run app.py

The model can be changed with GEMINI_MODEL. The default is gemini-3.8-flash.

On the current machine, the prepared environment can be started from PowerShell with:

    cd C:\medico
    .\.venv312\Scripts\python.exe -m streamlit run app.py --server.port 8502

## Publish on Streamlit Community Cloud

1. Connect the GitHub repository and create a Community Cloud app with app.py as the entrypoint.
2. In the app's Secrets settings, add the key outside the repository:

    GEMINI_API_KEY = "your_key_here"

3. Set the app's sharing setting to public when ready.

The app reads the key on the server; it is never placed in a browser field or committed to this repository. Do not upload your local .env file. Anyone who can access a public app can submit Gemini requests using the configured account's quota; set suitable API quotas and monitor usage.

## Privacy and safety

Questions and attached images are sent to Google Gemini when submitted. Avoid sharing identifying or highly sensitive information. The app displays an emergency-care reminder and directs users to seek professional care for personal decisions. AI can be wrong.

Images are limited to 10 MB and supported PNG, JPEG, or WEBP formats. The former YOLOv8 COCO detector was removed because it was not trained to identify medical findings.
