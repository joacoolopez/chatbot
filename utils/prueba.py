from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

def authenticate_google_service():
    creds = Credentials.from_service_account_file("joaco-454516-cad5266cae9e.json", scopes=["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=creds)


def verificarDisponibilidadHorario(start_time: str) -> bool:
    try:
        service = authenticate_google_service()

        # Definir la zona horaria de Buenos Aires
        tz = pytz.timezone('America/Argentina/Buenos_Aires')

        # Convertir el horario de inicio y fin con zona horaria
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        start_dt = tz.localize(start_dt)  # Localiza la fecha en la zona horaria

        # Definir el horario de fin (30 minutos después)
        end_dt = start_dt + timedelta(minutes=30)

        # Convertir a RFC3339 con zona horaria
        start_time_rfc3339 = start_dt.isoformat()
        end_time_rfc3339 = end_dt.isoformat()

        # Crear el cuerpo de la solicitud
        body = {
            "timeMin": start_time_rfc3339,
            "timeMax": end_time_rfc3339,
            "timeZone": "America/Argentina/Buenos_Aires",
            "items": [{"id": "primary"}]  # Usar 'primary' si no sabes el ID del calendario
        }
        
        # Consultar la disponibilidad
        response = service.freebusy().query(body=body).execute()

        # Obtener los eventos ocupados
        busy_times = response.get("calendars", {}).get("primary", {}).get("busy", [])

        if busy_times:
            return False
        else:
            return True

    except Exception as e:
        print(f"Error al verificar disponibilidad: {e}")
        return False


from datetime import datetime
import pytz

def listar_eventos(start_time: str, end_time: str):
    try:
        service = authenticate_google_service()

        # Definir la zona horaria de Argentina
        argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")

        # Convertir los tiempos de string a datetime con la zona horaria correcta
        start_dt = argentina_tz.localize(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S"))
        end_dt = argentina_tz.localize(datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S"))

        start_time_rfc3339 = start_dt.isoformat()  # No agregar "Z" porque ya incluye la zona horaria correcta
        end_time_rfc3339 = end_dt.isoformat()

        print(start_time_rfc3339)

        eventos = service.events().list(
            calendarId="c58ab4d9a20fa126aaac8e11bc5eeeb45ec5e084af98eb78eba7be13a1eb22a3@group.calendar.google.com",
            timeMin=start_time_rfc3339,
            timeMax=end_time_rfc3339,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        return eventos.get("items", [])

    except Exception as e:
        print(f"Error al listar eventos: {e}")
        return []


# # Llamada a la función
eventos = listar_eventos("2025-03-26T15:00:00", "2025-03-26T15:30:00")

print(eventos)



def agendarTurnoCalendario(summary: str, start_time: str) -> bool:
    """
    Agendar un turno en el calendario para un horario específico.
    
    Args:
        summary (str): Descripcion del turno.
        start_time (str): Fecha y hora en formato ISO. Ejemplo: "2025-01-26T14:00"
        
    Returns:
        bool: True si el turno fue agendado exitosamente, False si hubo un error.
    """
    try:
        service = authenticate_google_service()
        
        # Convertir start_time a datetime
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        
        # Definir la zona horaria de Buenos Aires
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        
        # Localizar la fecha en la zona horaria correcta
        start_dt = tz.localize(start_dt)
        
        # Calcular el horario de fin (30 minutos después)
        end_dt = start_dt + timedelta(minutes=30)
        
        # Convertir las fechas al formato RFC3339
        start_time_rfc3339 = start_dt.isoformat()
        end_time_rfc3339 = end_dt.isoformat()

        # Si no se pasa un resumen, asignar "turno"
        if not summary:
            summary = "turno"
        
        # Crear el evento
        event = {
            "summary": summary,
            "start": {"dateTime": start_time_rfc3339, "timeZone": "America/Argentina/Buenos_Aires"},
            "end": {"dateTime": end_time_rfc3339, "timeZone": "America/Argentina/Buenos_Aires"},
        }

        # Insertar el evento en el calendario
        created_event = service.events().insert(calendarId="c58ab4d9a20fa126aaac8e11bc5eeeb45ec5e084af98eb78eba7be13a1eb22a3@group.calendar.google.com", body=event).execute()
        
        # Retornar el enlace al evento creado
        return created_event.get("htmlLink")
    
    except Exception as e:
        print(f"Error al agendar el evento: {e}")
        return False
    
# response = agendarTurnoCalendario("prueba01", "2025-03-26T15:00:00")
# print(response)

response = verificarDisponibilidadHorario("2025-03-26T15:00:00")
print(response)



def crearCalendario():
    try:
        service = authenticate_google_service()

        # Crear el calendario para la cuenta de servicio
        calendar = {
            'summary': 'Calendario de la Cuenta de Servicio',  # Título del calendario
            'timeZone': 'America/Argentina/Buenos_Aires'  # Zona horaria
        }

        created_calendar = service.calendars().insert(body=calendar).execute()
        calendar_id = created_calendar['id']  # Obtener el ID del calendario creado
        print(f"Calendario creado con éxito. ID: {calendar_id}")
        return calendar_id
    
    except Exception as e:
        print(f"Error al crear el calendario: {e}")

# Crear el calendario
#calendar_id = crearCalendario()

def compartirCalendario(calendar_id: str, email: str):
    try:
        service = authenticate_google_service()

        # Crear la regla de acceso para compartir el calendario
        rule = {
            'scope': {
                'type': 'user',
                'value': email,  # El email de la cuenta que quieres que vea el calendario
            },
            'role': 'reader',  # Permitir solo lectura (para ver)
        }

        # Insertar la regla de acceso
        service.acl().insert(calendarId=calendar_id, body=rule).execute()
        print(f"Calendario compartido con {email}")
    except Exception as e:
        print(f"Error al compartir el calendario: {e}")

# Llamada de ejemplo para compartir el calendario
#compartirCalendario("c58ab4d9a20fa126aaac8e11bc5eeeb45ec5e084af98eb78eba7be13a1eb22a3@group.calendar.google.com", "c58ab4d9a20fa126aaac8e11bc5eeeb45ec5e084af98eb78eba7be13a1eb22a3@group.calendar.google.com")