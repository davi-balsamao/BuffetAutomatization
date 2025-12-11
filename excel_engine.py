import openpyxl
import shutil
import os
from datetime import datetime

# --- CONFIGURAÇÃO DE MAPEAMENTO ---
# Aqui ligamos as chaves do seu JSON às Tags que você escreveu no Excel
# Formato: "Chave_do_JSON": "Tag_no_Excel"
TAGS_LISTAS = {
    # Lista de Salgados (com categorias internas)
    "Salgados.quentes": "{list_salg_qts}",
    "Salgados.frios": "{list_salg_fr}",
    "Salgados.assados": "{list_salg_ass}",
    "Salgados.petit_gourmet": "{list_salg_pg}",

    "Bebidas": "{list_drinks}",

    "Sobremesa": "{{list_sobremesa}}" # Exemplo, caso adicione futuramente
}

TAGS_SIMPLES = {
    "cliente": "{name_client}",
    "data": "{date}",
    "convidados": "{num_guest}",
    "tipo": "{type_recp}"
    "local" "{local}"

}

def achatar_dados(conteudo):
    """
    Transforma dicionários aninhados em uma lista plana de strings para o Excel.
    Ex: {'Frios': ['A', 'B'], 'Quentes': ['C']} vira ['--- FRIOS ---', 'A', 'B', '--- QUENTES ---', 'C']
    """
    lista_final = []
    
    if isinstance(conteudo, list):
        return conteudo
    
    elif isinstance(conteudo, dict):
        for categoria, itens in conteudo.items():
            if itens: # Só adiciona se tiver itens
                # Adiciona um "Subtítulo" visual para separar no Excel
                lista_final.append(f"--- {categoria.upper()} ---") 
                lista_final.extend(itens)
    
    return lista_final

def gerar_excel(dados_json):
    # 1. Definição de Caminhos
    pasta_data = "data"
    arquivo_template = os.path.join(pasta_data, "template_orcamento.xlsx")
    
    # Nome do arquivo de saída com Timestamp para não sobrescrever
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_saida = f"Orcamento_{dados_json['metadados']['cliente'].replace(' ', '_')}_{timestamp}.xlsx"
    caminho_saida = os.path.join("output", nome_saida)

    # Garante que a pasta output existe
    if not os.path.exists("output"):
        os.makedirs("output")

    # 2. Copia o Template (Segurança)
    try:
        shutil.copy(arquivo_template, caminho_saida)
    except FileNotFoundError:
        return {"sucesso": False, "erro": "Template não encontrado em data/template_orcamento.xlsx"}

    # 3. Carrega o Excel na Memória
    wb = openpyxl.load_workbook(caminho_saida)
    ws = wb.active # Pega a primeira aba

    # --- FASE 1: SUBSTITUIÇÃO SIMPLES (Metadados) ---
    # Varre todas as células procurando as tags simples
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                for chave_json, tag_excel in TAGS_SIMPLES.items():
                    if tag_excel in cell.value:
                        # Substitui {{cliente}} pelo valor real
                        valor_real = str(dados_json['metadados'].get(chave_json, ''))
                        cell.value = cell.value.replace(tag_excel, valor_real)

    # --- FASE 2: LISTAS DINÂMICAS (O Motor Complexo) ---
    # Iteramos sobre o dicionário de configuração TAGS_LISTAS
    for chave_json, tag_excel in TAGS_LISTAS.items():
        
        # Busca os itens selecionados no JSON
        itens_brutos = dados_json['cardapio'].get(chave_json, [])
        lista_formatada = achatar_dados(itens_brutos)
        
        # Encontra a linha onde está a tag (Ex: {{list_salgados}})
        linha_tag = -1
        coluna_tag = -1
        
        for row in ws.iter_rows():
            for cell in row:
                if cell.value == tag_excel:
                    linha_tag = cell.row
                    coluna_tag = cell.column
                    break
            if linha_tag != -1: break
        
        # Se achou a tag no Excel...
        if linha_tag != -1:
            if not lista_formatada:
                # CASO A: Lista Vazia -> Deleta a linha da tag e a linha do título acima (regra da sobremesa)
                # Deleta a linha atual (tag) e a anterior (título)
                # Ajuste conforme seu template. Aqui assumo Titulo na linha X, Tag na X+1
                ws.delete_rows(linha_tag - 1, amount=2) 
            else:
                # CASO B: Tem itens -> Expande e Preenche
                qtd_itens = len(lista_formatada)
                
                # 1. Escreve o primeiro item na linha da própria tag (sobrescreve a tag)
                ws.cell(row=linha_tag, column=coluna_tag).value = lista_formatada[0]
                
                # 2. Se tiver mais itens, insere linhas abaixo
                if qtd_itens > 1:
                    ws.insert_rows(linha_tag + 1, amount=qtd_itens - 1)
                    
                    # Preenche as linhas novas
                    for i in range(1, qtd_itens):
                        celula = ws.cell(row=linha_tag + i, column=coluna_tag)
                        celula.value = lista_formatada[i]
                        # Opcional: Copiar estilo da célula original aqui se necessário

    # 4. Salva o Arquivo Final
    wb.save(caminho_saida)
    return {"sucesso": True, "caminho": caminho_saida}