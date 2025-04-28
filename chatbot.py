import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from utils.tools import verificarDisponibilidadHorario, agendarTurnoCalendario, actualYear
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.agents import AgentType

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def replybot(bot, mensaje):
    vectorstore = Chroma(persist_directory="path_to_chroma_db", embedding_function=OpenAIEmbeddings())
    results = vectorstore.similarity_search(mensaje.text, k=3)

    text = '''
    Eres un asistente virtual amable, servicial y eficiente. 
    Tu objetivo es ayudar a los clientes brindando información sobre nuestros servicios, responder preguntas y gestionar la agenda de turnos cuando solicitan un turno o quieren agendar un turno.
    Si no sabes la respuesta, di que no la sabes. Usa un máximo de tres oraciones y sé conciso.
    Si la respuesta no tiene relacion con el contexto de un centro de estetica, di que no lo sabes.
    En caso de que quieran saber si un tratamiento es apropiado, deciles que deben solicitar un turno para poder dar mas informacion.
    No tenes la capacidad de diagnosticar ni de recomendar tratamientos, tampoco podes dar una opinion ni indicios.
    Contexto: {contexto}
    Pregunta del cliente: {input}

    Tu respuesta:
    '''

    #retriever = vectorstore.as_retriever()
    prompt = ChatPromptTemplate.from_template(text)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

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
        ),
        Tool(
        name="ActualYear",
        func=actualYear,
        description="Devuelve el año actual"
        ),
    ]

    agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,  # Permite que use funciones
    verbose=True,
    agent_kwargs={
        "system_message": text  # Usa el texto personalizado como prompt
    }
    )

    respuesta = agent.invoke({"input": mensaje.text, "contexto": results[0].page_content})

    texto_respuesta = respuesta.get("output")

    bot.send_message(
        mensaje.chat.id,
        texto_respuesta,
    )