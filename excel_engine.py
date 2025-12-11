import openpyxl
import shutil
import os
from datetime import datetime

# --- 1. MAPEAMENTO DE LISTAS (Fixas) ---
TAGS_FIXAS = {
    # Salgados
    "Salgados.quentes": "{list_salg_qts}",
    "Salgados.frios": "{list_salg_fr}",
    "Salgados.assados": "{list_salg_ass}",
    "Salgados.petit_gourmet": "{list_salg_pg}",
    
    # Bebidas e Doces
    "Bebidas": "{list_drinks}",
    "Sobremesa": "{list_dessert}", 
    
    # Específicos
    "Buffet Infantil": "{list_infantil}",
    "Mão de Obra": "{list_hw}"  # <--- Adicionado Mão de Obra
}

# --- 2. MAPEAMENTO DE CAMPOS SIMPLES (Texto) ---
TAGS_SIMPLES = {
    "cliente": "{name_client}",
    "data": "{date}",
    "convidados": "{guest_number}", 
    "local": "{local}",
    "obs": "{obs}",
    
    # O valor total precisa vir do input do usuário na Etapa 3
    "valor_total": "{valor_total}", 
    
    # O tipo da festa e a lista específica do tipo
    "tipo": "{type_recepcao}"
}

# --- 3. FUNÇÕES HELPER ---

def buscar_dados_por_caminho(dados_completos, caminho_string):
    """Navega no JSON (ex: Salgados.quentes)"""
    chaves = caminho_string.split(".")
    conteudo_atual = dados_completos.get('cardapio', {})
    
    # Se a chave for Mão de Obra, busca fora do cardápio se necessário, 
    # mas assumiremos que você vai colocar dentro do cardápio no JSON.
    try:
        for chave in chaves:
            if isinstance(conteudo_atual, dict):
                conteudo_atual = conteudo_atual.get(chave, [])
            else:
                return []
        return conteudo_atual if isinstance(conteudo_atual, list) else []
    except:
        return []

def substituir_tag_simples(ws, tag, valor):
    """Substitui texto em qualquer lugar da planilha (busca parcial)"""
    valor_str = str(valor)
    for row in ws.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                if tag in cell.value:
                    cell.value = cell.value.replace(tag, valor_str)

def expandir_lista_no_excel(ws, tag_excel, lista_dados):
    """Expande linhas para listas ou deleta se vazio"""
    linha_tag = -1
    coluna_tag = -1
    
    # Localiza a tag
    for row in ws.iter_rows():
        for cell in row:
            if cell.value == tag_excel: # Para listas, mantemos busca exata na célula da tag
                linha_tag = cell.row
                coluna_tag = cell.column
                break
        if linha_tag != -1: break
    
    if linha_tag == -1: return False
    
    # Lógica de Escrita
    if not lista_dados:
        try:
            # Deleta a linha da tag E a linha de cima (Título)
            ws.delete_rows(linha_tag - 1, amount=2)
        except:
            pass
    else:
        qtd_itens = len(lista_dados)
        ws.cell(row=linha_tag, column=coluna_tag).value = lista_dados[0]
        
        if qtd_itens > 1:
            ws.insert_rows(linha_tag + 1, amount=qtd_itens - 1)
            for i in range(1, qtd_itens):
                ws.cell(row=linha_tag + i, column=coluna_tag).value = lista_dados[i]
    return True

# --- 4. MOTOR PRINCIPAL ---

def gerar_excel(dados_json):
    pasta_data = "data"
    arquivo_template = os.path.join(pasta_data, "template_orcamento.xlsx")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_cliente = str(dados_json['metadados']['cliente'] or "SemNome")
    nome_saida = f"Orcamento_{nome_cliente.replace(' ', '_')}_{timestamp}.xlsx"
    caminho_saida = os.path.join("output", nome_saida)

    if not os.path.exists("output"): os.makedirs("output")
    try:
        shutil.copy(arquivo_template, caminho_saida)
    except FileNotFoundError:
        return {"sucesso": False, "erro": "Template não encontrado!"}

    wb = openpyxl.load_workbook(caminho_saida)
    ws = wb.active

    # --- FASE 1: METADADOS E VALORES (Substituição Flexível) ---
    # Aqui resolvemos o problema do {valor_total} e {type_recepcao}
    for chave, valor in dados_json['metadados'].items():
        if chave in TAGS_SIMPLES:
            tag = TAGS_SIMPLES[chave]
            substituir_tag_simples(ws, tag, valor)
            
    # Obs é separado
    substituir_tag_simples(ws, "{obs}", dados_json.get("obs", ""))

    # --- FASE 2: LISTAS FIXAS ---
    # Resolvemos Mão de Obra, Sobremesa, Salgados
    for caminho_json, tag_excel in TAGS_FIXAS.items():
        lista = buscar_dados_por_caminho(dados_json, caminho_json)
        expandir_lista_no_excel(ws, tag_excel, lista)

    # --- FASE 3: LISTA ESPECIAL (TIPO DE RECEPÇÃO) ---
    # Se a festa for "Boteco Mineiro", precisamos preencher a lista específica
    # Assumindo que no JSON existe uma chave igual ao nome do tipo da festa
    tipo_festa = dados_json['metadados'].get('tipo') # Ex: "Boteco Mineiro"
    tag_lista_tipo = "{list_type_recp}"
    
    # Busca dinâmica: Tenta achar "Boteco Mineiro" no cardápio
    lista_especifica = dados_json['cardapio'].get(tipo_festa, [])
    
    # Se não achou com o nome exato, tenta mapeamentos comuns ou deixa vazio
    if not lista_especifica and tipo_festa == "Infantil":
         lista_especifica = dados_json['cardapio'].get("Buffet Infantil", [])

    expandir_lista_no_excel(ws, tag_lista_tipo, lista_especifica)


    # --- FASE 4: PRATO PRINCIPAL (A CORREÇÃO DO TÍTULO) ---
    dados_prato = dados_json['cardapio'].get('Prato Principal', {})
    categorias = []
    if isinstance(dados_prato, dict):
        for k, v in dados_prato.items():
            if v: categorias.append((k, v)) # (Nome, Lista)

    # Slot 1
    tag_titulo_1 = "{1_opcao}"
    tag_lista_1 = "{list_1_op}"
    
    if len(categorias) > 0:
        nome_prato, lista_prato = categorias[0]
        # AQUI ESTÁ A CORREÇÃO: Usamos a função substituir_tag_simples
        substituir_tag_simples(ws, tag_titulo_1, nome_prato.upper())
        expandir_lista_no_excel(ws, tag_lista_1, lista_prato)
    else:
        expandir_lista_no_excel(ws, tag_lista_1, []) # Deleta

    # Slot 2 (Se existir no futuro)
    if len(categorias) > 1:
        nome_prato_2, lista_prato_2 = categorias[1]
        substituir_tag_simples(ws, "{2_opcao}", nome_prato_2.upper())
        expandir_lista_no_excel(ws, "{list_2_op}", lista_prato_2)

    wb.save(caminho_saida)
    return {"sucesso": True, "caminho": caminho_saida}
```

### 📋 O que você precisa fazer agora (Pré-requisitos)

Para que esse código funcione e preencha as lacunas que você mencionou (Mão de Obra, Sobremesa no menu, Valor Total), precisamos atualizar rapidamente o **JSON** e o **App**.

**1. Atualize o `cardapio.json` (Adicione Mão de Obra e Ajuste Chaves):**
Você precisa adicionar a chave `"Mão de Obra"` no JSON para o código encontrá-la.

```json
{
    "salgados": { ... },
    "Mão de Obra": [
        "Cozinheira",
        "Copeira",
        "Garçom",
        "Recepcionista"
    ],
    ... (resto do arquivo)
}
```

**2. Ajuste Crítico no `app.py` (Para Sobremesa e Valor):**

Vou te passar apenas o trecho que você deve adicionar no **Passo 3** do seu `app.py` para capturar o valor total, já que ele não existia.

No bloco `elif st.session_state.step == 3:`, adicione isso antes do botão de gerar:

```python
# No passo 3 do app.py
st.markdown("### 💰 Fechamento")
valor_total = st.text_input("Valor Total do Orçamento (R$)", placeholder="Ex: 5.000,00")

# ... (botão gerar)
# DENTRO do dicionário pacote_dados, adicione:
"metadados": {
    # ... outros campos ...
    "valor_total": valor_total # <--- Isso vai preencher a tag {valor_total}
},