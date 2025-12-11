import streamlit as st
import json
import os
from datetime import date

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Buffet Automatization", layout="wide", page_icon="🍽️")

# --- 2. CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    caminho_arquivo = os.path.join("data", "cardapio.json")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Arquivo cardapio.json não encontrado!")
        return {}

dados = carregar_dados()

# --- 3. CALLBACKS (O Segredo da Atualização) ---
def selecionar_todos(chave_checkbox, chave_multiselect, opcoes):
    """
    Função chamada IMEDIATAMENTE quando o usuário clica no checkbox.
    Ela força a atualização da lista no banco de memória do Streamlit.
    """
    # Verifica se o checkbox está marcado
    if st.session_state[chave_checkbox]:
        st.session_state[chave_multiselect] = opcoes # Seleciona tudo
    else:
        st.session_state[chave_multiselect] = [] # Limpa tudo

# --- 4. INTERFACE ---
st.title("🍽️ Gerador de Orçamento - Buffet")
st.markdown("---")

with st.sidebar:
    st.header("📝 Dados do Evento")
    cliente = st.text_input("Nome do Cliente")
    data_evento = st.date_input("Data da Festa", value=date.today())
    local = st.text_input("Local da Festa")
    qtd_convidados = st.number_input("Qtd. Convidados", min_value=10, step=5, value=100)
    tipo_festa = st.selectbox("Tipo de Recepção", ["Tradicional", "Infantil", "Boteco Mineiro", "Coquetel"])

# --- 5. FUNÇÃO DE RENDERIZAÇÃO (COM CALLBACK) ---
def renderizar_secao(titulo, conteudo, chave_pai):
    
    # CASO 1: LISTA
    if isinstance(conteudo, list):
        chave_multiselect = f"sel_{chave_pai}_{titulo}"
        chave_checkbox = f"chk_{chave_widget_id(chave_pai, titulo)}" # Helper simples para ID único

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{titulo.capitalize()}**")
        with c2:
            # CHECKBOX COM CALLBACK
            # on_change: Chama a função antes de redesenhar a tela
            # args: Passa os IDs e a lista de opções para a função saber o que fazer
            st.checkbox(
                "Selecionar Todos", 
                key=chave_checkbox, 
                on_change=selecionar_todos,
                args=(chave_checkbox, chave_multiselect, conteudo)
            )
        
        return st.multiselect(
            f"Selecione {titulo}",
            options=conteudo,
            key=chave_multiselect, # O Callback vai injetar dados aqui
            label_visibility="collapsed"
        )
    
    # CASO 2: DICIONÁRIO (Recursão)
    elif isinstance(conteudo, dict):
        st.subheader(f"📂 {titulo.capitalize()}")
        selecoes_internas = {}
        abas = st.tabs([k.capitalize() for k in conteudo.keys()])
        
        for i, (sub_cat, itens) in enumerate(conteudo.items()):
            with abas[i]:
                chave_nova = f"{chave_pai}_{titulo}"
                selecoes_internas[sub_cat] = renderizar_secao(sub_cat, itens, chave_nova)
        return selecoes_internas

# Helper para gerar IDs consistentes e evitar erro de Duplicate Key ID
def chave_widget_id(pai, filho):
    return f"{pai}_{filho}".replace(" ", "_").lower()

# --- 6. MONTAGEM DO FORMULÁRIO ---
st.write("### Monte o Cardápio")
escolhas_usuario = {}

if dados:
    col1, col2 = st.columns(2)
    
    with col1:
        if "salgados" in dados:
            escolhas_usuario["Salgados"] = renderizar_secao("Salgados", dados["salgados"], "main")
        st.divider()
        if "Prato Principal" in dados:
            escolhas_usuario["Jantar"] = renderizar_secao("Prato Principal", dados["Prato Principal"], "main")

    with col2:
        if "bebidas" in dados:
            escolhas_usuario["Bebidas"] = renderizar_secao("Bebidas", dados["bebidas"], "main")
        st.divider()
        if "Buffet Infantil" in dados:
            if tipo_festa == "Infantil":
                escolhas_usuario["Infantil"] = renderizar_secao("Buffet Infantil", dados["Buffet Infantil"], "main")

# --- 7. BOTÃO FINAL ---
st.markdown("---")
observacoes = st.text_area("Observações Gerais")

if st.button("💾 Gerar Prévia dos Dados", type="primary"):
    pacote_dados = {
        "metadados": {
            "cliente": cliente,
            "data": data_evento.strftime("%d/%m/%Y"),
            "convidados": qtd_convidados,
            "tipo": tipo_festa
        },
        "cardapio": escolhas_usuario,
        "obs": observacoes
    }
    
    st.success("✅ Dados capturados!")
    with st.expander("🔍 Ver JSON Final", expanded=True):
        st.json(pacote_dados)