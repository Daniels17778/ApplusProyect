from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

BASE_DIR = Path(__file__).resolve().parent.parent

CREDENTIALS = BASE_DIR / "credentials" / "client_secret.json"

TOKEN = BASE_DIR / "credentials" / "token.json"


def autenticar():

    creds = None

    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS),
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )


        TOKEN.write_text(creds.to_json())

    return creds


if __name__ == "__main__":

    autenticar()

    print("✅ Gmail conectado correctamente")