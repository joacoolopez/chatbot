# %%
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

vectorstore = Chroma(persist_directory="path_to_chroma_db", embedding_function=OpenAIEmbeddings())

pregunta = "tienen disponible turno para el 26 de enero de 2025 a las 14:00? el turno seria de 30 minutos"

results = vectorstore.similarity_search(pregunta, k=3)


# %%
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

text = '''
Eres un asistente virtual amable, servicial y eficiente. 
Tu objetivo es ayudar a los clientes brindando información sobre nuestros servicios, responder preguntas y gestionar la agenda de turnos.
Si no sabes la respuesta, di que no la sabes. Usa un máximo de tres oraciones y sé conciso.
Contexto: {contexto}
Pregunta del cliente: {input}

Tu respuesta:
'''

retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_template(text)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)


# %%
from langchain_core.tools import tool
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

def authenticate_google_service():
    creds = Credentials.from_service_account_file("joaco-454516-cad5266cae9e.json", scopes=["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=creds)


@tool
def verificarDisponibilidadHorario(start_time: str) -> bool:
    
    """
    Verifica la disponibilidad en el calendario para un horario específico.
    
    Args:
        start_time (str): Fecha y hora en formato ISO. Ejemplo: "2025-01-26T14:00:00"
        duration (int): Duración en minutos del turno.
    
    Returns:
        bool: True si el horario está disponible, False si no.
        
    Ejemplo de uso:
        Para verificar un turno el 26 de enero de 2025 a las 14:00 por 30 minutos,
        usar: start_time="2025-01-26T14:00:00", duration=30
    """
    try:
        
        service = authenticate_google_service()

        argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")

        start_dt = argentina_tz.localize(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S"))
        end_dt = start_dt + timedelta(minutes=30) 

        start_time_rfc3339 = start_dt.isoformat()
        end_time_rfc3339 = end_dt.isoformat()

        eventos = service.events().list(
            calendarId="c58ab4d9a20fa126aaac8e11bc5eeeb45ec5e084af98eb78eba7be13a1eb22a3@group.calendar.google.com",
            timeMin=start_time_rfc3339,
            timeMax=end_time_rfc3339,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        if len(eventos.get("items", [])) > 0:
            return False
        else:
            return True

    except Exception as e:
        print(f"Error al listar eventos: {e}")
        return False


@tool
def agendarTurnoCalendario(start_time: str) -> bool:
    """
    Agendar un turno en el calendario para un horario específico y un nombre de paciente o del servicio a agendar.
    
    Args:
        data (dict): Contiene los parámetros necesarios como:
            - summary (str): Descripción del turno, puede ser el nombre del paciente o el nombre del servicio a agendar.
            - start_time (str): Fecha y hora en formato ISO.
        
        
    Returns:
        bool: True si el turno fue agendado exitosamente, False si hubo un error.
    """
    try:
        service = authenticate_google_service()

        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        
        start_dt = tz.localize(start_dt)
        end_dt = start_dt + timedelta(minutes=30)
        
        start_time_rfc3339 = start_dt.isoformat()
        end_time_rfc3339 = end_dt.isoformat()
        
        
        event = {
            "summary": "Turno", #TODO: reemplazar por una variable que traiga el agente
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

# %%
from langchain.tools import Tool

tools = [
    Tool(
        name="verificarDisponibilidadHorario",
        func=verificarDisponibilidadHorario,
        description="""
        Verifica si hay disponibilidad para un turno. 
        Necesita la fecha y hora (en formato YYYY-MM-DDTHH:MM) y la duración en minutos.
        Ejemplo: Para consultar el 26 de enero de 2025 a las 14:00 por 30 minutos,
        usar start_time="2025-01-26T14:00:00" y duration=30
        """
    ),
    Tool(
        name="agendarTurnoCalendario",
        func=agendarTurnoCalendario,
        description="""
        Agenda turno en el calendario
        Necesita la fecha y hora (en formato YYYY-MM-DDTHH:MM)
        Ejemplo: Para consultar el 26 de enero de 2025 a las 14:00 por 30 minutos,
        usar start_time="2025-01-26T14:00:00"
        """
    )
]

# %%
from langchain.agents import initialize_agent
from langchain.agents import AgentType

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,  # Permite que use funciones
    verbose=True  # Para ver logs
)

pregunta = "hola. me llamo joaquin y quiero agendar un turno con el nombre 'Dermatologico' con la doctora para el 26 de marzo de 2025 a las 16:00"
respuesta = agent.invoke({"input": pregunta, "contexto": results[0].page_content})
print(respuesta)




