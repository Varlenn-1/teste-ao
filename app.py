import streamlit as st
import google.generativeai as genai # Supondo que você esteja usando a biblioteca oficial
from PIL import Image
import os

# --- Configuração Inicial (Idealmente em um arquivo separado ou no início) ---
# Configure sua API Key do Gemini aqui
# genai.configure(api_key="SUA_API_KEY")

os.environ['GOOGLE_API_KEY'] = st.secrets["GOOGLE_API_KEY"]

# Configure a API do Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY")) # Recomenda-se usar variáveis de ambiente

# --- Funções Auxiliares ---
def configurar_modelo_gemini(persona_selecionada, historico_chat):
    """Configura e retorna o modelo generativo com base na persona e histórico."""
    # Configurações do modelo (ajuste conforme necessário)
    generation_config = {
        "candidate_count": 1,
        "temperature": 0.7, # Ajuste para mais ou menos criatividade
    }
    safety_settings = {
        'HATE': 'BLOCK_NONE',
        'HARASSMENT': 'BLOCK_NONE',
        'SEXUAL': 'BLOCK_NONE',
        'DANGEROUS': 'BLOCK_NONE'
    }

    # Define o prompt do sistema com base na persona
    prompt_sistema_base = "Você é um assistente especializado em games."
    if persona_selecionada == "Professor Ozy":
        prompt_sistema_persona = (
            f"{prompt_sistema_base} "
            "Seu nome é Professor Ozy. Você é especialista em ensinar pessoas não familiarizadas com o mundo dos Games. "
            "Evite jargões complicados e explique qualquer jargão que aparecer. "
            "Se o usuário enviar uma foto/print de um jogo, explique o que está vendo e, se apropriado, forneça um mini-tutorial. "
            "Seja paciente e didático."
        )
    elif persona_selecionada == "Ozy o Guru":
        prompt_sistema_persona = (
            f"{prompt_sistema_base} "
            "RVocê é um Guru de mal com a vida, eaja da maneira mais sarcastica que puder."
            "Você deve fornecer suas informações com acidez e de maneira áspera"
            "Faça piadas de mal gosto e se seu sistema permitir utilize palavrões"
            "Não se segure"
        )
    else:
        prompt_sistema_persona = prompt_sistema_base # Fallback

    # Inicializa o modelo com o prompt de sistema e o histórico
    # A forma de passar o prompt de sistema e o histórico pode variar um pouco
    # dependendo de como você estrutura a conversa com a API Gemini (model.start_chat ou model.generate_content)

    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash', # Ou o modelo que você pretende usar
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=prompt_sistema_persona
    )
    return model

def obter_resposta_gemini(modelo, prompt_usuario, imagem_usuario=None, historico_chat_gemini_format=None):
    """Envia o prompt para o Gemini e retorna a resposta."""
    try:
        # Se estiver usando model.start_chat(), o histórico é gerenciado internamente pelo objeto chat.
        # Se estiver usando model.generate_content() diretamente, você pode precisar passar o histórico.
        # Este é um exemplo genérico.
        
        conteudo_prompt = [prompt_usuario]
        if imagem_usuario:
            # A API do Gemini aceita objetos PIL.Image para imagens
            conteudo_prompt.insert(0, imagem_usuario) # Ou anexe, dependendo da preferência da API

        # Para conversas contínuas com generate_content, o histórico precisa ser formatado corretamente.
        # Exemplo de formato para histórico com generate_content:
        # messages = [
        #    {'role':'user', 'parts': ['Mensagem anterior do usuário']},
        #    {'role':'model', 'parts': ['Resposta anterior do modelo']},
        #    {'role':'user', 'parts': [conteudo_prompt]} # Nova mensagem
        # ]
        # response = model.generate_content(messages)

        # Exemplo com start_chat (mais simples para histórico)
        # Este é um pseudo-código, a implementação exata pode variar
        if historico_chat_gemini_format:
             chat_session = modelo.start_chat(history=historico_chat_gemini_format)
             response = chat_session.send_message(conteudo_prompt)
        else:
             response = modelo.generate_content(conteudo_prompt) # Para uma única chamada ou primeira chamada

        return response.text
    except Exception as e:
        st.error(f"Erro ao comunicar com a API Gemini: {e}")
        return "Desculpe, não consegui processar sua solicitação no momento."

# --- Interface do Streamlit ---
st.set_page_config(layout="wide", page_title="Imersão IA ChatGames")

st.title("🎮 ChatGames IA - Imersão Alura 🎮")
st.caption("Seu assistente de IA para o mundo dos games!")

# Inicializar o session_state se ainda não existir
if "historico_chat" not in st.session_state:
    st.session_state.historico_chat = [] # Lista para armazenar {"role": "user/assistant", "content": "mensagem", "persona": "nome_persona"}
if "persona_selecionada" not in st.session_state:
    st.session_state.persona_selecionada = "Professor Ozy" # Persona padrão
if "historico_gemini" not in st.session_state:
    st.session_state.historico_gemini = {} # Dicionário para armazenar históricos por persona para a API do Gemini

# Sidebar para seleção de persona e outras opções
with st.sidebar:
    st.header("Configurações")
    persona_escolhida = st.radio(
        "Escolha sua Persona:",
        ("Professor Ozy", "Ozy o Guru"),
        key="persona_radio",
        on_change=lambda: setattr(st.session_state, 'persona_selecionada', st.session_state.persona_radio)
    )
    st.session_state.persona_selecionada = persona_escolhida # Garante que a persona está atualizada

    if st.button("Limpar Histórico da Conversa"):
        st.session_state.historico_chat = []
        st.session_state.historico_gemini = {} # Limpa também o histórico para a API
        st.rerun()

    st.markdown("---")
    st.markdown("Projeto para a **Imersão IA Alura**")

# Área de Upload de Imagem (aparece se Professor Ozy estiver selecionado ou para uso geral)
imagem_carregada = None
if st.session_state.persona_selecionada == "Professor Ozy" or True: # Deixar sempre visível por enquanto
    imagem_carregada_file = st.file_uploader("Envie uma print do seu jogo (opcional):", type=["jpg", "jpeg", "png"])
    if imagem_carregada_file:
        from PIL import Image
        imagem_carregada = Image.open(imagem_carregada_file)
        st.image(imagem_carregada, caption="Imagem carregada.", width=300)

# Exibir histórico do chat
chat_container = st.container(height=400) # Define uma altura para o container do chat
with chat_container:
    for mensagem in st.session_state.historico_chat:
        with st.chat_message(mensagem["role"]):
            st.markdown(f"_{mensagem.get('persona', '')}_" if mensagem.get('persona') else "")
            st.markdown(mensagem["content"])
            if "image" in mensagem and mensagem["image"]: # Se houver imagem na mensagem do usuário
                st.image(mensagem["image"], width=200)


# Input do usuário
prompt_usuario = st.chat_input(f"Converse com {st.session_state.persona_selecionada}...")

if prompt_usuario:
    # Adicionar mensagem do usuário ao histórico geral
    mensagem_usuario_completa = {"role": "user", "content": prompt_usuario}
    if imagem_carregada:
        mensagem_usuario_completa["image"] = imagem_carregada # Adiciona a imagem se houver
    st.session_state.historico_chat.append(mensagem_usuario_completa)

    # Formatar histórico para a API do Gemini (específico da persona)
    # O Gemini espera uma lista de dicts: {'role': 'user'/'model', 'parts': [texto]}
    if st.session_state.persona_selecionada not in st.session_state.historico_gemini:
        st.session_state.historico_gemini[st.session_state.persona_selecionada] = []

    # Adicionar mensagem atual do usuário ao histórico da persona para a API
    partes_prompt_usuario_api = [prompt_usuario]
    if imagem_carregada:
        partes_prompt_usuario_api.insert(0, imagem_carregada) # Gemini geralmente espera a imagem primeiro

    st.session_state.historico_gemini[st.session_state.persona_selecionada].append({
        "role": "user",
        "parts": partes_prompt_usuario_api
    })

    # Exibir mensagem do usuário imediatamente
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
        if imagem_carregada:
            st.image(imagem_carregada, width=200)

    # Obter e exibir resposta da IA
    with st.spinner(f"{st.session_state.persona_selecionada} está digitando..."):
        # Passar o histórico da persona para a função de configuração do modelo
        modelo_gemini = configurar_modelo_gemini(
            st.session_state.persona_selecionada,
            st.session_state.historico_gemini[st.session_state.persona_selecionada][:-1] # Envia o histórico SEM a última msg do user
        )
        resposta_ia = obter_resposta_gemini(
            modelo_gemini,
            prompt_usuario, # A mensagem atual do usuário
            imagem_carregada, # A imagem, se houver
            st.session_state.historico_gemini[st.session_state.persona_selecionada] # Passa o histórico formatado para a API
        )

    # Adicionar resposta da IA ao histórico geral
    st.session_state.historico_chat.append({
        "role": "assistant",
        "content": resposta_ia,
        "persona": st.session_state.persona_selecionada
    })
    # Adicionar resposta da IA ao histórico da persona para a API
    st.session_state.historico_gemini[st.session_state.persona_selecionada].append({
        "role": "model", # 'model' para a API do Gemini
        "parts": [resposta_ia]
    })

    # Limpar a imagem carregada após o processamento para não ser reenviada
    # st.session_state.imagem_carregada_file = None # Isso pode precisar de ajuste na lógica do file_uploader
    st.rerun() # Atualizar a interface para mostrar a nova mensagem

# Para um efeito mais "WhatsApp", você pode tentar estilizar com CSS,
# mas para 3 dias, focar na funcionalidade é mais importante.
# st.markdown("""
# <style>
#     .stChatMessage {
#         border-radius: 10px;
#         padding: 10px;
#         margin-bottom: 10px;
#     }
#     /* Mais estilos aqui */
# </style>
# """, unsafe_allow_html=True)