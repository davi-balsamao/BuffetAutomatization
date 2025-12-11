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

# --- 3. CALLBACKS (Gerenciamento de Estado) ---
def selecionar_todos(chave_checkbox, chave_multiselect, opcoes):
    """Callback para o botão 'Selecionar Todos'"""
    if st.session_state[chave_checkbox]:
        st.session_state[chave_multiselect] = opcoes
    else:
        st.session_state[chave_multiselect] = []

def chave_widget_id(pai, filho):
    """Helper para criar IDs únicos"""
    return f"{pai}_{filho}".replace(" ", "_").lower()

# --- 4. FUNÇÃO DE RENDERIZAÇÃO ---
def renderizar_secao(titulo, conteudo, chave_pai):
    
    # CASO 1: LISTA (Bebidas, Sobremesa, Infantil)
    if isinstance(conteudo, list):
        chave_multiselect = f"sel_{chave_pai}_{titulo}"
        chave_checkbox = f"chk_{chave_widget_id(chave_pai, titulo)}"

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{titulo.capitalize()}**")
        with c2:
            st.checkbox(
                "Selecionar Todos", 
                key=chave_checkbox, 
                on_change=selecionar_todos,
                args=(chave_checkbox, chave_multiselect, conteudo)
            )
        
        return st.multiselect(
            f"Selecione {titulo}",
            options=conteudo,
            key=chave_multiselect,
            label_visibility="collapsed"
        )
    
    # CASO 2: DICIONÁRIO (Salgados, Jantar)
    elif isinstance(conteudo, dict):
        st.subheader(f"📂 {titulo.capitalize()}")
        selecoes_internas = {}
        abas = st.tabs([k.capitalize() for k in conteudo.keys()])
        
        for i, (sub_cat, itens) in enumerate(conteudo.items()):
            with abas[i]:
                chave_nova = f"{chave_pai}_{titulo}"
                selecoes_internas[sub_cat] = renderizar_secao(sub_cat, itens, chave_nova)
        return selecoes_internas

# --- 5. INTERFACE PRINCIPAL ---
st.title("🍽️ Gerador de Orçamento - Buffet")
st.markdown("---")

with st.sidebar:
    st.header("📝 Dados do Evento")
    cliente = st.text_input("Nome do Cliente")
    data_evento = st.date_input("Data da Festa", value=date.today())
    local = st.text_input("Local da Festa")
    qtd_convidados = st.number_input("Qtd. Convidados", min_value=10, step=5, value=100)
    tipo_festa = st.selectbox("Tipo de Recepção", ["Tradicional", "Infantil", "Boteco Mineiro", "Coquetel"])

# --- 6. MONTAGEM DO CARDÁPIO ---
st.write("### Monte o Cardápio")
escolhas_usuario = {}

if dados:
    col1, col2 = st.columns(2)
    
    # COLUNA DA ESQUERDA (Comidas Pesadas)
    with col1:
        if "salgados" in dados:
            escolhas_usuario["Salgados"] = renderizar_secao("Salgados", dados["salgados"], "main")
        
        st.divider()
        
        if "Prato Principal" in dados:
            # Atenção: A chave deve ser "Prato Principal" para bater com o JSON
            escolhas_usuario["Prato Principal"] = renderizar_secao("Prato Principal", dados["Prato Principal"], "main")

    # COLUNA DA DIREITA (Bebidas, Doces e Extras)
    with col2:
        if "sobremesa" in dados:
            # Nova seção de Sobremesa
            escolhas_usuario["Sobremesa"] = renderizar_secao("Sobremesa", dados["sobremesa"], "main")

        st.divider()

        if "bebidas" in dados:
            escolhas_usuario["Bebidas"] = renderizar_secao("Bebidas", dados["bebidas"], "main")
        
        st.divider()
        
        if "Buffet Infantil" in dados:
            if tipo_festa == "Infantil":
                st.success("Opções Infantis Habilitadas")
                escolhas_usuario["Buffet Infantil"] = renderizar_secao("Buffet Infantil", dados["Buffet Infantil"], "main")
            else:
                st.caption("Menu Infantil oculto (Mude o tipo para 'Infantil' para ver)")

# --- 7. RODAPÉ E GERAÇÃO ---
st.markdown("---")
observacoes = st.text_area("Observações Gerais")

if st.button("💾 Gerar Orçamento Excel", type="primary"):
    
    pacote_dados = {
        "metadados": {
            "cliente": cliente,
            "data": data_evento.strftime("%d/%m/%Y"),
            "convidados": qtd_convidados,
            "tipo": tipo_festa,
            "local": local
        },
        "cardapio": escolhas_usuario,
        "obs": observacoes
    }
    
    with st.spinner("Processando planilha..."):
        try:
            # Importação aqui dentro para garantir que o arquivo existe na execução
            from excel_engine import gerar_excel
            resultado = gerar_excel(pacote_dados)
            
            if resultado["sucesso"]:
                st.success("Orçamento gerado com sucesso!")
                with open(resultado["caminho"], "rb") as file:
                    st.download_button(
                        label="📥 Baixar Arquivo (.xlsx)",
                        data=file,
                        file_name=os.path.basename(resultado["caminho"]),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(f"Erro no Motor Excel: {resultado.get('erro')}")
                
        except Exception as e:
            st.error(f"Erro crítico: {e}")
            st.write("Detalhes para debug:", e)