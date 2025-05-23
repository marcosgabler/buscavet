# -*- coding: utf-8 -*-
"""buscavet2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1y7AwId9CAyluYlguXOpD5WtwZuyhVY3F
"""

# Commented out IPython magic to ensure Python compatibility.
from IPython import get_ipython
from IPython.display import display, Markdown
# %%
from IPython import get_ipython
from IPython.display import display
# %%
# %pip -q install google-genai google-adk googlemaps
# %%
# Configura a API Key do Google Gemini

import os
from google.colab import userdata

os.environ["GOOGLE_API_KEY"] = userdata.get('GOOGLE_API_KEY')

# Configura a API Key do Google Maps
# Certifique-se de ter uma chave de API do Google Maps armazenada em secrets com o nome 'GOOGLE_MAPS_API_KEY'
try:
  os.environ["GOOGLE_MAPS_API_KEY"] = userdata.get('GOOGLE_MAPS_API_KEY')
except userdata.SecretNotFoundError:
  print("ATENÇÃO: Chave GOOGLE_MAPS_API_KEY não encontrada nos secrets do Colab.")
  print("Por favor, adicione sua chave de API do Google Maps aos secrets com o nome 'GOOGLE_MAPS_API_KEY'.")

# %%
# Configura o cliente da SDK do Gemini

from google import genai

client = genai.Client()

MODEL_ID = "gemini-2.0-flash"
# %%
# Instalar Framework de agentes do Google ################################################
# Já instalado no passo anterior
# %%
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types  # Para criar conteúdos (Content e Part)
import textwrap # Para formatar melhor a saída de texto
import requests # Para fazer requisições HTTP
import warnings
import googlemaps # Importa a biblioteca googlemaps

warnings.filterwarnings("ignore")
# %%
# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
def call_agent(agent: Agent, message_text: str) -> str:
    # Cria um serviço de sessão em memória
    session_service = InMemorySessionService()
    # Cria uma nova sessão (você pode personalizar os IDs conforme necessário)
    session = session_service.create_session(app_name=agent.name, user_id="user1", session_id="session1")
    # Cria um Runner para o agente
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    # Cria o conteúdo da mensagem de entrada
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    # Itera assincronamente pelos eventos retornados durante a execução do agente
    for event in runner.run(user_id="user1", session_id="session1", new_message=content):
        if event.is_final_response():
          for part in event.content.parts:
            if part.text is not None:
              final_response += part.text
              final_response += "\n"
    return final_response
# %%
# Função auxiliar para exibir texto formatado em Markdown no Colab
def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))
# %%
#######################################################
# --- Agente 1: Buscador de Clínicas Veterinárias --- #
#######################################################
def agente_buscador_veterinarias(cep):
    buscador_veterinarias = Agent(
        name="agente_buscador_veterinarias",
        model="gemini-2.0-flash",
        instruction=f"""
        Você é um assistente de pesquisa. Sua tarefa é usar a ferramenta de busca do google (google_search)
        para encontrar clínicas veterinárias que funcionam 24 horas perto do CEP {cep}.
        Liste as clínicas encontradas com seus nomes, endereços e, se possível, telefones.
        Priorize resultados que explicitamente mencionem atendimento 24 horas.
        Forneça o máximo de detalhes de endereço possível para ajudar na geração do link do mapa.
        """,
        description="Agente que busca clínicas veterinárias 24 horas no Google",
        tools=[google_search]
    )

    entrada_do_agente_buscador = f"Clínicas veterinárias 24 horas perto do CEP {cep}"

    clinicas_encontradas = call_agent(buscador_veterinarias, entrada_do_agente_buscador)
    return clinicas_encontradas
# %%
#####################################################
# --- Agente 2: Formatador de Resultados com Mapa --- #
#####################################################
def agente_formatador_resultados_mapa(clinicas_encontradas):
    formatador = Agent(
        name="agente_formatador_resultados_mapa",
        model="gemini-2.0-flash",
        instruction="""
        Você é um formatador de texto. Recebeu uma lista de clínicas veterinárias com seus detalhes (nome, endereço, telefone).
        Sua tarefa é formatar essas informações de maneira clara e concisa, listando cada clínica
        e seus detalhes em tópicos, fácil de ler para o usuário.
        Para cada clínica com endereço disponível, tente gerar um link para o Google Maps.
        Se não encontrou nenhuma clínica, informe isso ao usuário.
        """,
        description="Agente que formata os resultados da busca por clínicas veterinárias e adiciona links para o Google Maps.",
    )

    entrada_do_agente_formatador = f"Lista de clínicas veterinárias encontradas:\n{clinicas_encontradas}\n\nPara cada clínica com endereço, por favor, gere um link para o Google Maps."

    resultados_formatados = call_agent(formatador, entrada_do_agente_formatador)

    # Adicionar a lógica para gerar links do Google Maps aqui
    # Isso pode ser feito iterando sobre os resultados formatados e usando a biblioteca googlemaps
    # No entanto, o agente formatador já está instruído a tentar gerar os links,
    # dependendo da sua capacidade de processar e interagir com essa informação.
    # Uma abordagem mais robusta seria processar a saída do agente e usar a API do Google Maps
    # no código Python principal para gerar os links. Vamos implementar essa abordagem.

    return resultados_formatados

# %%
# Função para gerar link do Google Maps a partir de um endereço
def generate_google_maps_link(address):
    if "GOOGLE_MAPS_API_KEY" not in os.environ:
      return "Chave de API do Google Maps não configurada."

    try:
      gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAPS_API_KEY"])
      geocode_result = gmaps.geocode(address)

      if geocode_result:
        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']
        return f"[Ver no Google Maps](https://www.google.com/maps?q={latitude},{longitude})"
      else:
        return "Endereço não encontrado para gerar o link do mapa."
    except Exception as e:
      return f"Erro ao gerar link do mapa: {e}"


# %%
print("🐾 Iniciando o Sistema de Busca por Clínicas Veterinárias 24 Horas 🐾")

# --- Obter o CEP do Usuário ---
cep_usuario = input("❓ Por favor, digite o CEP da região onde você deseja buscar clínicas veterinárias 24 horas: ")

# Inserir lógica do sistema de agentes ################################################
if not cep_usuario:
    print("Você esqueceu de digitar o CEP!")
else:
    print(f"Maravilha! Buscando clínicas veterinárias 24 horas perto do CEP {cep_usuario}...")

    clinicas_encontradas = agente_buscador_veterinarias(cep_usuario)
    # print("\n--- 📝 Resultado da Busca (Agente 1) ---\n")
    # display(to_markdown(clinicas_encontradas))
    # print("--------------------------------------------------------------")

    # O agente formatador agora tenta incluir informações para gerar links
    resultados_formatados_agente = agente_formatador_resultados_mapa(clinicas_encontradas)

    # Processar a saída do agente formatador para adicionar links do Google Maps
    linhas_resultados = resultados_formatados_agente.split('\n')
    resultados_finais_com_mapa = []

    current_clinic_info = []
    for linha in linhas_resultados:
        current_clinic_info.append(linha)
        if "Endereço:" in linha:
            address_parts = linha.split("Endereço:")
            if len(address_parts) > 1:
                address = address_parts[1].strip()
                map_link = generate_google_maps_link(address)
                current_clinic_info.append(f"{map_link}\n") # Adiciona o link do mapa
        elif not linha.strip() and current_clinic_info:
            # Fim das informações de uma clínica, adicione tudo aos resultados finais
            resultados_finais_com_mapa.extend(current_clinic_info)
            current_clinic_info = []

    # Adicionar quaisquer informações restantes (última clínica)
    if current_clinic_info:
        resultados_finais_com_mapa.extend(current_clinic_info)


    print("\n📝 Clínicas Veterinárias 24 Horas Encontradas PERTO DE VOCÊ\n")
    display(to_markdown("\n".join(resultados_finais_com_mapa)))
    print("--------------------------------------------------------------")