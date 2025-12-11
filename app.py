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

# --- 3. TÍTULO E SIDEBAR (Dados do Evento) ---
st.title("🍽️ Gerador de Orçamento - Buffet")
st.markdown("---")

with st.sidebar:
    st.header("📝 Dados do Evento")
    cliente = st.text_input("Nome do Cliente")
    data_evento = st.date_input("Data da Festa", value=date.today())
    local = st.text_input("Local da Festa")
    
    # Validação simples para evitar erro de cálculo
    qtd_convidados = st.number_input("Qtd. Convidados", min_value=10, step=5, value=100)
    
    tipo_festa = st.selectbox("Tipo de Recepção", ["Tradicional", "Infantil", "Boteco Mineiro", "Coquetel"])
    st.info(f"Modo selecionado: **{tipo_festa}**")

# --- 4. FUNÇÃO MÁGICA: RENDERIZAÇÃO RECURSIVA ---
# Essa função resolve o problema do seu JSON ter estruturas mistas (Listas vs Dicts)
def renderizar_secao(titulo, conteudo, chave_pai):
    """
    Cria a interface visual dependendo se o conteúdo é uma Lista ou um Dicionário.
    """
    # Se for uma LISTA (Ex: Bebidas, Buffet Infantil) -> Cria um Multiselect simples
    if isinstance(conteudo, list):
        # Cria uma chave única para o streamlit não se perder
        chave_widget = f"sel_{chave_pai}_{titulo}" 
        return st.multiselect(f"Selecione: {titulo.capitalize()}", options=conteudo, key=chave_widget)
    
    # Se for um DICIONÁRIO (Ex: Salgados -> Frios, Quentes) -> Cria Abas ou Expander
    elif isinstance(conteudo, dict):
        st.subheader(f"📂 {titulo.capitalize()}")
        selecoes_internas = {}
        
        # Cria abas para cada subcategoria (Frios, Quentes, etc.)
        abas = st.tabs([k.capitalize() for k in conteudo.keys()])
        
        for i, (sub_cat, itens) in enumerate(conteudo.items()):
            with abas[i]:
                # Chama a lógica de lista para cada aba
                chave_widget = f"sel_{chave_pai}_{titulo}_{sub_cat}"
                selecoes_internas[sub_cat] = st.multiselect(
                    f"Opções de {sub_cat}", 
                    options=itens, 
                    key=chave_widget
                )
        return selecoes_internas

# --- 5. O FORMULÁRIO PRINCIPAL ---
# Usamos st.form para evitar recarregamento a cada clique (Performance)
with st.form("form_orcamento"):
    
    st.write("### Monte o Cardápio")
    
    # Dicionário que vai guardar TUDO o que o usuário escolher
    escolhas_usuario = {}

    # ITERAÇÃO INTELIGENTE: Varre o JSON e cria os campos
    if dados:
        col1, col2 = st.columns(2)
        
        # Coluna 1: Comidas
        with col1:
            if "salgados" in dados:
                escolhas_usuario["Salgados"] = renderizar_secao("Salgados", dados["salgados"], "main")
            
            st.divider()
            
            if "Prato Principal" in dados:
                escolhas_usuario["Jantar"] = renderizar_secao("Prato Principal", dados["Prato Principal"], "main")

        # Coluna 2: Bebidas e Outros
        with col2:
            if "bebidas" in dados:
                escolhas_usuario["Bebidas"] = renderizar_secao("Bebidas", dados["bebidas"], "main")
            
            st.divider()
            
            if "Buffet Infantil" in dados:
                # Exemplo de lógica condicional visual
                if tipo_festa == "Infantil":
                    st.success("Opções Infantis Habilitadas")
                    escolhas_usuario["Infantil"] = renderizar_secao("Buffet Infantil", dados["Buffet Infantil"], "main")
                else:
                    st.caption("Menu Infantil oculto (Selecione 'Infantil' no menu lateral para ver)")

    # --- RODAPÉ DO FORMULÁRIO ---
    st.markdown("---")
    observacoes = st.text_area("Observações Gerais / Cláusulas Extras")
    
    # Botão de Submissão
    enviado = st.form_submit_button("💾 Gerar Prévia dos Dados")

# --- 6. VISUALIZAÇÃO DO OUTPUT (DEBUG) ---
if enviado:
    st.success("Dados capturados com sucesso!")
    
    # Cria o objeto final que será enviado para o Excel na Etapa 3
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
    
    # Mostra o JSON estruturado na tela para você conferir
    with st.expander("🔍 Ver JSON que será enviado para o Excel"):
        st.json(pacote_dados)