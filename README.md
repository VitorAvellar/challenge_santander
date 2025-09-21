# challenge_santander

Este projeto é uma solução para o Santander Challenge, focada em analisar e classificar empresas (PJ) com base em seu momento de vida e em suas relações financeiras na rede de transações.

A solução consiste em duas partes principais:

1. Um script de processamento de dados (analise_completa.py) que realiza a análise, feature engineering, modelagem e análise de rede.

2. Um dashboard interativo (dashboard.py) construído com Streamlit para visualizar os insights e permitir a consulta individual de empresas.

   ✨ Funcionalidades
. Classificação de Momento de Vida: Utiliza um modelo de clustering (K-Means) para categorizar empresas em estágios como "Pequeno Porte", "Em Crescimento", "Consolidada" e "Grande Porte".

. Análise de Rede Financeira: Mapeia as transações para identificar empresas centrais (hubs) e medir o nível de dependência entre parceiros comerciais.

. Projeções Simplificadas: Oferece uma projeção de recebimentos para o próximo mês baseada no histórico transacional da empresa.

. Dashboard Interativo com Duas Visões:

1. Visão Geral do Portfólio: Painel com métricas agregadas, gráficos interativos e filtros dinâmicos.

2. Análise Individual de Empresa: Ferramenta de busca por ID para obter um perfil detalhado de qualquer empresa, incluindo suas projeções e métricas de rede.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3

. Análise de Dados: Pandas, NumPy

. Machine Learning: Scikit-learn

. Análise de Rede: NetworkX

. Dashboard: Streamlit

. Visualização de Dados: Plotly Express

. Utilitários: Tqdm (para barras de progresso)

🚀 Como Executar o Projeto
Siga os passos abaixo para configurar e rodar a aplicação localmente.

Pré-requisitos
Python 3.8 ou superior instalado.

1. Preparação do Ambiente
Primeiro, organize a estrutura de pastas do projeto. Crie uma pasta principal e coloque os arquivos necessários dentro dela.

<img width="713" height="135" alt="image" src="https://github.com/user-attachments/assets/0634f0d6-4ceb-4bbc-a38b-1b0ffde280bf" />


2. Instalação das Dependências
Abra seu terminal (Prompt de Comando, PowerShell, Terminal), navegue até a pasta do projeto e instale todas as bibliotecas necessárias com um único comando:
<img width="712" height="139" alt="image" src="https://github.com/user-attachments/assets/44769a6d-b86b-46f6-873e-a59a7067cc36" />

3. Execução
A aplicação é executada em duas etapas simples:

Etapa 1: Processar os Dados
Primeiro, execute o script de análise para processar os dados brutos e gerar os arquivos que o dashboard irá consumir.

**python analise_completa.py**

Este script irá:

. Ler **Base 1 - ID.csv** e **Base 2 - Transações.csv**.

. Realizar toda a análise e modelagem.

. Criar os arquivos **empresas_analisadas.csv** e **transacoes_com_data.csv**.

. Salvar um log detalhado da execução em analise.log.

Etapa 2: Iniciar o Dashboard
Com os dados processados, inicie o servidor do Streamlit para visualizar o dashboard.

**streamlit run dashboard.py**

Após executar este comando, uma nova aba será aberta automaticamente no seu navegador, exibindo a aplicação interativa.

📁 Estrutura Final dos Arquivos
Após a execução bem-sucedida da Etapa 1, sua pasta de projeto conterá os seguintes arquivos:
<img width="716" height="194" alt="image" src="https://github.com/user-attachments/assets/c6cfb2d0-f9c9-4298-a302-f0243ea2bed0" />


