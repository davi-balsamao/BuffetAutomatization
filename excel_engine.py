import openpyxl
import shutil
import os
from datetime import datetime

# --- CONFIGURAÇÃO DE MAPEAMENTO (Tags do seu Excel) ---
# TAGS FIXAS: Listas que têm lugar certo na planilha
TAGS_FIXAS = {
    # Caminho.no.JSON (Dote Notation)  :  Tag no Excel (Exatamente como você digitou)
    "Salgados.quentes": "{list_salg_qts}",
    "Salgados.frios": "{list_salg_fr}",
    "Salgados.assados": "{list_salg_ass}",
    "Salgados.petit_gourmet": "{list_salg_pg}",
    "Bebidas": "{list_drinks}",
    "Sobremesa": "{list_dessert}", 
    "Buffet Infantil": "{list_infantil}"
    # "Mão de Obra": "{list_hw}" (Se implementar futuramente)
}

# TAGS SIMPLES: Apenas substituição de texto
TAGS_SIMPLES = {
    "cliente": "{name_client}",
    "data": "{date}",
    "convidados": "{guest_number}", 
    "tipo": "{type_recp}", # No JSON é 'tipo', no Excel é {type_recp}
    "local": "{local}",
    "obs": "{obs}"
}

# --- FUNÇÕES HELPER ---

def buscar_dados_por_caminho(dados_completos, caminho_string):
    """Navega no JSON usando strings com ponto (Ex: Salgados.quentes)"""
    chaves = caminho_string.split(".")
    conteudo_atual = dados_completos.get('cardapio', {})
    
    try:
        for chave in chaves:
            if isinstance(conteudo_atual, dict):
                conteudo_atual = conteudo_atual.get(chave, [])
            else:
                return []
        return conteudo_atual if isinstance(conteudo_atual, list) else []
    except:
        return []

def expandir_lista_no_excel(ws, tag_excel, lista_dados):
    """
    Localiza uma tag, substitui pelo 1º item e insere linhas para o restante.
    Se a lista for vazia, deleta a linha da tag E a linha anterior (Título).
    """
    linha_tag = -1
    coluna_tag = -1
    
    # 1. Procura a tag na planilha
    for row in ws.iter_rows():
        for cell in row:
            if cell.value == tag_excel:
                linha_tag = cell.row
                coluna_tag = cell.column
                break
        if linha_tag != -1: break
    
    if linha_tag == -1:
        return False # Tag não encontrada
    
    # 2. Lógica de Preenchimento ou Deleção
    if not lista_dados:
        # Se lista vazia: Deleta a linha da Tag e a linha SUPERIOR (Título)
        # Ex: Deleta "SOBREMESA" e "{list_dessert}"
        print(f"Deletando seção vazia para tag: {tag_excel}")
        ws.delete_rows(linha_tag - 1, amount=2)
    else:
        # Se tem dados: Expande
        qtd_itens = len(lista_dados)
        ws.cell(row=linha_tag, column=coluna_tag).value = lista_dados[0] # 1º item sobrescreve tag
        
        if qtd_itens > 1:
            ws.insert_rows(linha_tag + 1, amount=qtd_itens - 1)
            for i in range(1, qtd_itens):
                # Escreve os itens seguintes nas linhas criadas
                celula = ws.cell(row=linha_tag + i, column=coluna_tag)
                celula.value = lista_dados[i]
                # Aqui você poderia copiar o style da celula original se quisesse refinar
    return True

# --- MOTOR PRINCIPAL ---

def gerar_excel(dados_json):
    # 1. Setup
    pasta_data = "data"
    arquivo_template = os.path.join(pasta_data, "template_orcamento.xlsx")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cliente_safe = str(dados_json['metadados']['cliente']).replace(' ', '_')
    nome_saida = f"Orcamento_{cliente_safe}_{timestamp}.xlsx"
    caminho_saida = os.path.join("output", nome_saida)

    if not os.path.exists("output"):
        os.makedirs("output")
        
    try:
        shutil.copy(arquivo_template, caminho_saida)
    except FileNotFoundError:
        return {"sucesso": False, "erro": "Template não encontrado em data/template_orcamento.xlsx"}

    wb = openpyxl.load_workbook(caminho_saida)
    ws = wb.active

    # --- FASE 1: METADADOS (Cabeçalho) ---
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                for chave_pacote, tag_excel in TAGS_SIMPLES.items():
                    if tag_excel in cell.value:
                        # Busca no pacote 'metadados' ou 'obs'
                        if chave_pacote == "obs":
                            valor = dados_json.get("obs", "")
                        else:
                            valor = dados_json['metadados'].get(chave_pacote, "")
                            
                        cell.value = cell.value.replace(tag_excel, str(valor))

    # --- FASE 2: LISTAS PADRÃO (Salgados, Bebidas, etc) ---
    for caminho_json, tag_excel in TAGS_FIXAS.items():
        lista = buscar_dados_por_caminho(dados_json, caminho_json)
        expandir_lista_no_excel(ws, tag_excel, lista)

    # --- FASE 3: LÓGICA ESPECIAL DO JANTAR (Tag Dinâmica) ---
    # Captura o que foi selecionado em "Prato Principal"
    dados_jantar = dados_json['cardapio'].get('Prato Principal', {})
    
    # Flags para encontrar as tags especiais do Jantar
    tag_titulo_jantar = "{1_opcao}"
    tag_lista_jantar = "{list_1_op}"
    
    # Verifica se há items selecionados no Jantar
    tem_jantar = False
    nome_prato_escolhido = ""
    lista_prato_escolhido = []

    if dados_jantar and isinstance(dados_jantar, dict):
        # Varre as chaves (Massa, Chef, etc) para ver qual tem itens
        for categoria, itens in dados_jantar.items():
            if itens and len(itens) > 0:
                nome_prato_escolhido = categoria # Ex: "Massa"
                lista_prato_escolhido = itens    # Ex: ["Penne", "Molho"]
                tem_jantar = True
                break # Pega apenas a primeira categoria preenchida (Regra de Negócio: 1 Opção)

    # APLICAÇÃO NO EXCEL
    if tem_jantar:
        # 1. Substitui o TÍTULO {1_opcao} pelo nome do prato (Ex: "MASSA")
        for row in ws.iter_rows():
            for cell in row:
                if cell.value == tag_titulo_jantar:
                    cell.value = nome_prato_escolhido.upper() # Caixa alta
                    break
        
        # 2. Expande a LISTA na tag {list_1_op}
        expandir_lista_no_excel(ws, tag_lista_jantar, lista_prato_escolhido)
        
    else:
        # Se não tem jantar, deleta as linhas do Jantar
        # Usamos expandir com lista vazia para acionar o delete_rows interno
        expandir_lista_no_excel(ws, tag_lista_jantar, [])
        
        # Nota: O 'expandir' acima deleta a tag {list_1_op} e a linha acima dela.
        # Se a tag {1_opcao} estiver DUAS linhas acima, talvez precise deletar manualmente aqui.
        # Mas pelo padrão (Titulo na linha X, Lista na X+1), o comando acima resolve.

    wb.save(caminho_saida)
    return {"sucesso": True, "caminho": caminho_saida}