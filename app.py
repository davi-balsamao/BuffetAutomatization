import streamlit as st
import json
import os
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Buffet Automatization", layout="wide", page_icon="🍽️")

# --- CSS PARA DEIXAR O WIZARD BONITO ---
st.markdown("""
    <style>
        .step-title { font-size: 24px; font-weight: bold; color: #4F8BF9; margin-bottom: 20px; }
        .stButton button { width: 100%; border-radius: 5px; height: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO SEGURA DO ESTADO (BLINDAGEM) ---
def inicializar_estado():
    # Variáveis de Navegação
    if 'step' not in st.session_state: st.session_state.step = 1
    
    # Variáveis do Passo 1 (Dados)
    if 'cliente' not in st.session_state: st.session_state.cliente = ""
    if 'data_evento' not in st.session_state: st.session_state.data_evento = date.today()
    if 'local' not in st.session_state: st.session_state.local = ""
    if 'qtd_convidados' not in st.session_state: st.session_state.qtd_convidados = 100
    if 'tipo_festa' not in st.session_state: st.session_state.tipo_festa = "Tradicional"
    
    # Variáveis do Passo 2 (Cardápio)
    if 'cardapio_selecionado' not in st.session_state: st.session_state.cardapio_selecionado = {}
    if 'obs' not in st.session_state: st.session_state.obs = ""

inicializar_estado()

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    caminho_arquivo = os.path.join("data", "cardapio.json")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("ERRO: Arquivo data/cardapio.json não encontrado!")
        return {}

dados = carregar_dados()

# --- FUNÇÕES LÓGICAS ---
def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1

def selecionar_todos(chave_checkbox, chave_multiselect, opcoes):
    if st.session_state[chave_checkbox]:
        st.session_state[chave_multiselect] = opcoes
    else:
        st.session_state[chave_multiselect] = []

def chave_widget_id(pai, filho):
    return f"{pai}_{filho}".replace(" ", "_").lower()

def renderizar_secao(titulo, conteudo, chave_pai):
    if isinstance(conteudo, list):
        chave_multiselect = f"sel_{chave_pai}_{titulo}"
        chave_checkbox = f"chk_{chave_widget_id(chave_pai, titulo)}"
        
        # Garante que a chave existe antes de criar o widget
        if chave_multiselect not in st.session_state:
            st.session_state[chave_multiselect] = []

        c1, c2 = st.columns([3, 1])
        with c1: st.markdown(f"**{titulo.capitalize()}**")
        with c2: 
            st.checkbox("Selecionar Todos", key=chave_checkbox, on_change=selecionar_todos, args=(chave_checkbox, chave_multiselect, conteudo))
        
        return st.multiselect(f"Selecione {titulo}", options=conteudo, key=chave_multiselect, label_visibility="collapsed")
    
    elif isinstance(conteudo, dict):
        st.subheader(f"📂 {titulo.capitalize()}")
        selecoes = {}
        abas = st.tabs([k.capitalize() for k in conteudo.keys()])
        for i, (sub_cat, itens) in enumerate(conteudo.items()):
            with abas[i]:
                chave_nova = f"{chave_pai}_{titulo}"
                selecoes[sub_cat] = renderizar_secao(sub_cat, itens, chave_nova)
        return selecoes

# ==============================================================================
# 📍 FLUXO WIZARD (PASSO A PASSO)
# ==============================================================================

# Barra de Progresso Visual
progresso = {1: 0.33, 2: 0.66, 3: 1.0}
st.progress(progresso[st.session_state.step])

# --- PASSO 1: DADOS DO CLIENTE ---
if st.session_state.step == 1:
    st.markdown('<div class="step-title">📍 Passo 1: Quem é o cliente?</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.cliente = st.text_input("Nome do Cliente", value=st.session_state.cliente)
            st.session_state.data_evento = st.date_input("Data da Festa", value=st.session_state.data_evento)
        with col2:
            st.session_state.local = st.text_input("Local da Festa", value=st.session_state.local)
            st.session_state.qtd_convidados = st.number_input("Qtd. Convidados", min_value=10, step=5, value=st.session_state.qtd_convidados)
        
        opcoes_festa = ["Tradicional", "Infantil", "Boteco Mineiro", "Coquetel"]
        try:
            index_festa = opcoes_festa.index(st.session_state.tipo_festa)
        except:
            index_festa = 0
            
        st.session_state.tipo_festa = st.selectbox("Tipo de Recepção", opcoes_festa, index=index_festa)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Próximo: Escolher Cardápio ➡️", type="primary"):
        if not st.session_state.cliente:
            st.warning("⚠️ O nome do cliente é obrigatório!")
        else:
            next_step()
            st.rerun()

# --- PASSO 2: ESCOLHA DO CARDÁPIO ---
elif st.session_state.step == 2:
    st.markdown(f'<div class="step-title">🍴 Passo 2: O que será servido? ({st.session_state.tipo_festa})</div>', unsafe_allow_html=True)
    
    if st.button("⬅️ Voltar aos Dados"):
        prev_step()
        st.rerun()
    
    escolhas_temp = {}
    
    # 1. SALGADOS
    with st.expander("🥐 Salgados", expanded=True):
        if "salgados" in dados:
            escolhas_temp["Salgados"] = renderizar_secao("Salgados", dados["salgados"], "main")
            
    # 2. PRATO PRINCIPAL (Antigo Jantar)
    with st.expander("🍝 Prato Principal"):
        if "Prato Principal" in dados:
            escolhas_temp["Prato Principal"] = renderizar_secao("Prato Principal", dados["Prato Principal"], "main")
            
    # 3. BEBIDAS E DOCES
    with st.expander("🍹 Bebidas e Sobremesas"):
        c1, c2 = st.columns(2)
        with c1:
            if "bebidas" in dados:
                escolhas_temp["Bebidas"] = renderizar_secao("Bebidas", dados["bebidas"], "main")
        with c2:
            if "sobremesa" in dados:
                escolhas_temp["Sobremesa"] = renderizar_secao("Sobremesa", dados["sobremesa"], "main")

    # 4. INFANTIL
    if st.session_state.tipo_festa == "Infantil":
        with st.expander("🧸 Buffet Infantil", expanded=True):
            if "Buffet Infantil" in dados:
                escolhas_temp["Buffet Infantil"] = renderizar_secao("Buffet Infantil", dados["Buffet Infantil"], "main")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Próximo: Revisar e Baixar ➡️", type="primary"):
        st.session_state.cardapio_selecionado = escolhas_temp
        next_step()
        st.rerun()

# --- PASSO 3: FINALIZAÇÃO ---
elif st.session_state.step == 3:
    st.markdown('<div class="step-title">✅ Passo 3: Revisão Final</div>', unsafe_allow_html=True)
    
    st.info(f"Cliente: **{st.session_state.cliente}** | Local: **{st.session_state.local}**")
    
    st.session_state.obs = st.text_area("Observações / Cláusulas Extras", value=st.session_state.obs)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Editar Cardápio"):
            prev_step()
            st.rerun()
            
    with c2:
        if st.button("💾 GERAR EXCEL AGORA", type="primary"):
            
            pacote_dados = {
                "metadados": {
                    "cliente": st.session_state.cliente,
                    "data": st.session_state.data_evento.strftime("%d/%m/%Y"),
                    "convidados": st.session_state.qtd_convidados,
                    "tipo": st.session_state.tipo_festa,
                    "local": st.session_state.local
                },
                "cardapio": st.session_state.cardapio_selecionado,
                "obs": st.session_state.obs
            }
            
            with st.spinner("Gerando arquivo..."):
                try:
                    from excel_engine import gerar_excel
                    resultado = gerar_excel(pacote_dados)
                    
                    if resultado["sucesso"]:
                        st.balloons()
                        with open(resultado["caminho"], "rb") as file:
                            st.download_button(
                                label="📥 CLIQUE PARA BAIXAR (.xlsx)",
                                data=file,
                                file_name=os.path.basename(resultado["caminho"]),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.error(f"Erro no Motor: {resultado.get('erro')}")
                except Exception as e:
                    st.error(f"Erro Crítico: {e}")