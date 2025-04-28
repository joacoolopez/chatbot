from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Autenticación con la cuenta de servicio
def authenticate_google_service():
    creds = Credentials.from_service_account_file("joaco-454516-cad5266cae9e.json", scopes=["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=creds)

# Función para crear un evento en Google Calendar
def create_calendar_event(summary: str, description: str, start_time: str, end_time: str, timezone: str = "America/Argentina/Buenos_Aires", attendees: list = None):
    service = authenticate_google_service()

    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": timezone},
        "end": {"dateTime": end_time, "timeZone": timezone},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    created_event = service.events().insert(calendarId="lopezjoaco02@gmail.com", body=event).execute()
    return created_event.get("htmlLink")


if __name__ == "__main__":
    try:
        evento_url = create_calendar_event(
            summary="Reunión con el equipo",
            description="Discutir avances del proyecto de IA",
            start_time="2025-03-22T14:00:00-03:00",
            end_time="2025-03-22T15:00:00-03:00"
        )
        print(f"Evento creado: {evento_url}")
    except Exception as e:
        print(e)
