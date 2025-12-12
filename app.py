import streamlit as st
import json
import os
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Buffet Automatization", layout="wide", page_icon="🍽️")

# --- CSS WIZARD ---
st.markdown("""
    <style>
        .step-title { font-size: 24px; font-weight: bold; color: #4F8BF9; margin-bottom: 20px; }
        .stButton button { width: 100%; border-radius: 5px; height: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADO ---
def inicializar_estado():
    if 'step' not in st.session_state: st.session_state.step = 1
    
    # Passo 1
    if 'cliente' not in st.session_state: st.session_state.cliente = ""
    if 'data_evento' not in st.session_state: st.session_state.data_evento = date.today()
    if 'local' not in st.session_state: st.session_state.local = ""
    if 'qtd_convidados' not in st.session_state: st.session_state.qtd_convidados = 100
    if 'tipo_festa' not in st.session_state: st.session_state.tipo_festa = "Tradicional"
    
    # Passo 2
    if 'cardapio_selecionado' not in st.session_state: st.session_state.cardapio_selecionado = {}
    
    # Passo 3
    if 'obs' not in st.session_state: st.session_state.obs = ""
    if 'valor_total' not in st.session_state: st.session_state.valor_total = ""
    if 'total_salgados' not in st.session_state: st.session_state.total_salgados = 0

inicializar_estado()

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    caminho_arquivo = os.path.join("data", "cardapio.json")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

dados = carregar_dados()

# --- FUNÇÕES AUXILIARES ---
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
# 📍 FLUXO WIZARD
# ==============================================================================
st.progress({1: 0.33, 2: 0.66, 3: 1.0}[st.session_state.step])

# --- PASSO 1: DADOS CLIENTE ---
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
        
        opcoes = ["Tradicional", "Infantil", "Cantinho Mineiro", "Casamento", "Aniversário 15 anos"]
        idx = opcoes.index(st.session_state.tipo_festa) if st.session_state.tipo_festa in opcoes else 0
        st.session_state.tipo_festa = st.selectbox("Tipo de Recepção", opcoes, index=idx)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Próximo ➡️", type="primary"):
        if not st.session_state.cliente:
            st.warning("Preencha o nome do cliente!")
        else:
            next_step()
            st.rerun()

# --- PASSO 2: CARDÁPIO ---
elif st.session_state.step == 2:
    st.markdown(f'<div class="step-title">🍴 Passo 2: O que será servido?</div>', unsafe_allow_html=True)
    if st.button("⬅️ Voltar"):
        prev_step()
        st.rerun()
    
    escolhas = {}
    
    with st.expander("🥐 Salgados", expanded=True):
        if "Salgados" in dados:
            escolhas["Salgados"] = renderizar_secao("Salgados", dados["Salgados"], "main")
            
    with st.expander("🍝 Prato Principal"):
        if "Prato Principal" in dados:
            escolhas["Prato Principal"] = renderizar_secao("Prato Principal", dados["Prato Principal"], "main")
            
    with st.expander("🍹 Bebidas e Doces"):
        c1, c2 = st.columns(2)
        with c1:
            if "Bebidas" in dados:
                escolhas["Bebidas"] = renderizar_secao("Bebidas", dados["Bebidas"], "main")
        with c2:
            if "Sobremesa" in dados:
                escolhas["Sobremesa"] = renderizar_secao("Sobremesa", dados["Sobremesa"], "main")

    # NOVA SEÇÃO: MÃO DE OBRA
    with st.expander("👷 Equipe / Mão de Obra"):
        if "Mão de Obra" in dados:
            escolhas["Mão de Obra"] = renderizar_secao("Mão de Obra", dados["Mão de Obra"], "main")

    if st.session_state.tipo_festa == "Infantil":
        with st.expander("🧸 Buffet Infantil", expanded=True):
            if "Buffet Infantil" in dados:
                escolhas["Buffet Infantil"] = renderizar_secao("Buffet Infantil", dados["Buffet Infantil"], "main")

    if st.session_state.tipo_festa == "Cantinho Mineiro":
        with st.expander("Cantinho Mineiro", expanded=True):
            if "Cantinho Mineiro" in dados:
                escolhas["Cantinho Mineiro"] = renderizar_secao("Cantinho Mineiro", dados["Cantinho Mineiro"], "main")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Próximo ➡️", type="primary"):
        st.session_state.cardapio_selecionado = escolhas
        next_step()
        st.rerun()

# --- PASSO 3: FINALIZAÇÃO ---
elif st.session_state.step == 3:
    st.markdown('<div class="step-title">✅ Passo 3: Fechamento</div>', unsafe_allow_html=True)
    
    st.info(f"Cliente: **{st.session_state.cliente}** | Data: **{st.session_state.data_evento.strftime('%d/%m/%Y')}**")
    

    st.write("### 💰 Valores e Quantitativos") 
    
    col_val1, col_val2 = st.columns(2)
    with col_val1:
        st.session_state.valor_total = st.text_input("Valor Total (R$)", value=st.session_state.valor_total)
    with col_val2:
        # Novo campo numérico
        st.session_state.total_salgados = st.number_input("Total de Salgados (un)", min_value=0, step=10, value=st.session_state.total_salgados)
    

    # Campo Novo: Valor Total
    # st.write("### 💰 Valores")
    # st.session_state.valor_total = st.text_input("Valor Total do Orçamento (R$)", value=st.session_state.valor_total, placeholder="Ex: 5.500,00")

    # Campo: Total de Salgados
    # st.write("### Total de Salgados")
    # st.session_state.total_salg = st.text_input("Quantidade total de salgados", value=st.session_state.total_salg, placeholder="Ex: 600")
    
    st.write("### 📝 Observações")
    st.session_state.obs = st.text_area("Cláusulas Extras / Obs", value=st.session_state.obs)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Editar"):
            prev_step()
            st.rerun()
    with c2:
        if st.button("💾 GERAR EXCEL", type="primary"):
            pacote = {
                "metadados": {
                    "cliente": st.session_state.cliente,
                    "data": st.session_state.data_evento.strftime("%d/%m/%Y"),
                    "convidados": st.session_state.qtd_convidados,
                    "tipo": st.session_state.tipo_festa,
                    "local": st.session_state.local,
                    "valor_total": st.session_state.valor_total, # Passando o valor
                    "qtd_salgados": st.session_state.total_salgados
                },
                "cardapio": st.session_state.cardapio_selecionado,
                "obs": st.session_state.obs
            }
            
            with st.spinner("Gerando..."):
                try:
                    from excel_engine import gerar_excel
                    res = gerar_excel(pacote)
                    if res["sucesso"]:
                        st.balloons()
                        with open(res["caminho"], "rb") as f:
                            st.download_button("📥 BAIXAR .XLSX", f, os.path.basename(res["caminho"]))
                    else:
                        st.error(f"Erro: {res.get('erro')}")
                except Exception as e:
                    st.error(f"Erro Crítico: {e}")