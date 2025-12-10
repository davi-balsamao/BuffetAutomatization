# 🍽️ Buffet Automatization

> **Status:** Em Desenvolvimento 🚧

Sistema de automação de processos de negócio (BPA) desenvolvido para gestão ágil de orçamentos e contratos de Buffet. A ferramenta elimina o preenchimento manual de documentos, padroniza a saída em Excel e reduz erros operacionais.

## 🎯 Objetivo do Projeto
Transformar um fluxo manual e repetitivo em uma aplicação web local, intuitiva e custo zero. O sistema permite:
1.  **Gerar Orçamentos:** Seleção dinâmica de cardápio (Salgados, Jantar, Bebidas) e cálculo de mão de obra.
2.  **Gerar Contratos:** Conversão do orçamento aprovado em contrato formal com cláusulas jurídicas e campos de assinatura.
3.  **Flexibilidade:** Saída em arquivos `.xlsx` (Excel) totalmente editáveis para ajustes finos pós-geração.

## 🛠️ Stack Tecnológica
Projeto construído com foco em simplicidade de implantação e eficiência local.

* **Linguagem:** `Python 3.10+`
* **Frontend/UI:** `Streamlit` (Interface web reativa rodando localmente).
* **Engine de Excel:** `OpenPyXL` (Manipulação de templates `.xlsx` preservando formatação).
* **Banco de Dados:** `JSON` (Armazenamento leve de cardápios e cláusulas).

## 🚀 Funcionalidades Principais

### 1. Módulo de Orçamento
* Formulário interativo para dados do evento (Data, Local, Convidados).
* Seleção múltipla de itens do cardápio (Frios, Quentes, Assados, Petit Gourmet).
* Input manual de precificação (conforme regra de negócio variável).
* Geração de arquivo Excel baseado em template pré-formatado.

### 2. Módulo de Contrato
* Hereditariedade de dados do orçamento aprovado.
* Inclusão automática das Condições Gerais (9 cláusulas contratuais).
* Formatação pronta para impressão e assinatura.

## 📂 Estrutura do Projeto
A organização segue o padrão MVC simplificado para Data Apps:

BuffetAutomatization/
├── .venv/                  # Ambiente Virtual (Isolamento)
├── assets/                 # Imagens e Logos
├── data/
│   └── cardapio.json       # "Banco de dados" dos pratos e cláusulas
├── templates/
│   ├── template_orcamento.xlsx  # Modelo Excel vazio (Design)
│   └── template_contrato.xlsx   # Modelo Contrato vazio
├── output/                 # Pasta onde os arquivos gerados são salvos
├── app.py                  # Ponto de entrada da aplicação (Main)
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação

## ⚙️ Instalação e Execução (Local)

### Pré-requisitos
* Python instalado e adicionado ao PATH.

### Passo a Passo
1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/BuffetAutomatization.git](https://github.com/seu-usuario/BuffetAutomatization.git)
    cd BuffetAutomatization
    ```

2.  **Configure o Ambiente Virtual:**
    ```bash
    # Windows
    python -m venv .venv
    .\.venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install streamlit openpyxl
    ```

4.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```
    *O navegador abrirá automaticamente no endereço `http://localhost:8501`.*

## 📦 Como Entregar para o Cliente (Deployment Local)
Como o usuário final não é técnico, o projeto inclui um script executável (`iniciar_programa.bat`) que:
1.  Ativa o ambiente virtual ocultamente.
2.  Inicia o servidor Streamlit.
3.  Abre o navegador padrão do usuário pronto para uso.

## 📝 Licença
Este projeto é de uso privado e educacional.

---
**Desenvolvido por Davi Ladeira**
*Estudante de Ciência de Dados - UFMG*