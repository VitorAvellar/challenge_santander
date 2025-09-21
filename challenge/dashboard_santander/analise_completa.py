import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import networkx as nx
import warnings
import logging
import time
from tqdm import tqdm # Importando a biblioteca da barra de progresso

# --- CONFIGURAÇÃO DO LOG ---
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, 
                    format=log_format,
                    handlers=[
                        logging.FileHandler("analise.log", mode='w'), # mode='w' para sobrescrever o log a cada execução
                        logging.StreamHandler()
                    ])

# --- INÍCIO DO SCRIPT ---
warnings.filterwarnings('ignore')
logging.info("======================================================")
logging.info("=== INICIANDO SCRIPT OTIMIZADO DE ANÁLISE DE DADOS PJ ===")
logging.info("======================================================")
start_time_total = time.time()

# --- PASSO 1: CARREGAR E PREPARAR OS DADOS ---
# (Esta parte permanece a mesma)
logging.info("[PASSO 1/5] Iniciando: Carregamento e Preparação dos Dados.")
start_time_step = time.time()
try:
    df_id = pd.read_csv('Base 1 - ID.csv', sep=';')
    df_transacoes = pd.read_csv('Base 2 - Transações.csv', sep=';')
    logging.info(f"Arquivos carregados. Base ID: {df_id.shape[0]} linhas. Base Transações: {df_transacoes.shape[0]} linhas.")
except FileNotFoundError as e:
    logging.error(f"ERRO CRÍTICO: Arquivo não encontrado. Detalhe: {e}")
    exit()

logging.info("Iniciando Feature Engineering...")
df_id['DT_ABRT'] = pd.to_datetime(df_id['DT_ABRT'], errors='coerce')
data_referencia = pd.to_datetime(df_id['DT_REFE']).max()
df_id['IDADE_EMPRESA'] = (data_referencia - df_id['DT_ABRT']).dt.days / 365.25
logging.info(f"Coluna 'IDADE_EMPRESA' criada. Data de referência: {data_referencia.date()}")

logging.info("Agregando dados de transações (pagamentos e recebimentos)...")
pagamentos = df_transacoes.groupby('ID_PGTO')['VL'].agg(['sum', 'count']).rename(columns={'sum': 'VL_PAGAMENTOS', 'count': 'QT_PAGAMENTOS'})
recebimentos = df_transacoes.groupby('ID_RCBE')['VL'].agg(['sum', 'count']).rename(columns={'sum': 'VL_RECEBIMENTOS', 'count': 'QT_RECEBIMENTOS'})

df_final = df_id.merge(pagamentos, left_on='ID', right_index=True, how='left')
df_final = df_final.merge(recebimentos, left_on='ID', right_index=True, how='left')
df_final.fillna(0, inplace=True)
logging.info(f"PASSO 1 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 2: CLASSIFICAÇÃO DE MOMENTO DE VIDA (K-MEANS) ---
# (Esta parte permanece a mesma)
logging.info("\n[PASSO 2/5] Iniciando: Classificação de Momento de Vida.")
start_time_step = time.time()
features = ['VL_FATU', 'VL_SLDO', 'IDADE_EMPRESA', 'VL_PAGAMENTOS', 'VL_RECEBIMENTOS']
logging.info(f"Features selecionadas para clusterização: {features}")
X = df_final[features]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
logging.info("Dados normalizados com StandardScaler.")
K_CLUSTERS = 4
kmeans = KMeans(n_clusters=K_CLUSTERS, random_state=42, n_init=10)
df_final['CLUSTER'] = kmeans.fit_predict(X_scaled)
logging.info(f"Modelo K-Means treinado com k={K_CLUSTERS}.")
cluster_means = df_final.groupby('CLUSTER')[features].mean().sort_values('VL_FATU')
logging.info("Médias dos clusters para interpretação:\n" + cluster_means.to_string())
mapeamento = {cluster_means.index[0]: 'Pequeno Porte', cluster_means.index[1]: 'Em Crescimento', cluster_means.index[2]: 'Consolidada', cluster_means.index[3]: 'Grande Porte'}
df_final['MOMENTO_VIDA'] = df_final['CLUSTER'].map(mapeamento)
logging.info(f"PASSO 2 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 3: ANÁLISE DE REDE (OTIMIZADO) ---
logging.info("\n[PASSO 3/5] Iniciando: Análise da Rede de Transações (Versão Otimizada).")
start_time_step = time.time()
G = nx.from_pandas_edgelist(df_transacoes, 'ID_PGTO', 'ID_RCBE', ['VL'], create_using=nx.DiGraph())
logging.info(f"Grafo de rede criado com {G.number_of_nodes()} nós e {G.number_of_edges()} arestas.")

logging.info("Calculando centralidade de grau...")
centralidade = nx.degree_centrality(G)
df_final['CENTRALIDADE'] = df_final['ID'].map(centralidade).fillna(0)

logging.info("Calculando nível de dependência máxima (método vetorizado)...")
# Calcula o valor total pago e recebido por cada empresa
total_pagamentos = df_transacoes.groupby('ID_PGTO')['VL'].sum()
total_recebimentos = df_transacoes.groupby('ID_RCBE')['VL'].sum()

# Encontra o maior valor transacionado com um único parceiro para pagamentos
max_pgto_parceiro = df_transacoes.groupby(['ID_PGTO', 'ID_RCBE'])['VL'].sum().groupby('ID_PGTO').max()
# Encontra o maior valor transacionado com um único parceiro para recebimentos
max_rcbe_parceiro = df_transacoes.groupby(['ID_RCBE', 'ID_PGTO'])['VL'].sum().groupby('ID_RCBE').max()

# Calcula a taxa de dependência
dependencia_pgto = (max_pgto_parceiro / total_pagamentos).rename("dep_pgto")
dependencia_rcbe = (max_rcbe_parceiro / total_recebimentos).rename("dep_rcbe")

# Combina as duas taxas de dependência
df_dependencia = pd.concat([dependencia_pgto, dependencia_rcbe], axis=1).fillna(0)
df_final['NIVEL_DEPENDENCIA'] = df_dependencia.max(axis=1)

logging.info("Colunas 'CENTRALIDADE' e 'NIVEL_DEPENDENCIA' criadas.")
logging.info(f"PASSO 3 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 4: MODELO DE PROJEÇÃO SIMPLIFICADO ---
logging.info("\n[PASSO 4/5] Iniciando: Modelo de Projeção de Faturamento.")
start_time_step = time.time()
df_transacoes['DT_REFE'] = pd.to_datetime(df_transacoes['DT_REFE'], errors='coerce')
df_transacoes['MES_ANO'] = df_transacoes['DT_REFE'].dt.to_period('M')

recebimentos_mensais = df_transacoes.groupby(['ID_RCBE', 'MES_ANO'])['VL'].sum().reset_index()
recebimentos_mensais['MES_ANO_ORD'] = recebimentos_mensais['MES_ANO'].apply(lambda x: x.to_timestamp()).astype('int64')

projecoes = {}
empresas_unicas = recebimentos_mensais['ID_RCBE'].unique()
logging.info(f"Calculando projeções para {len(empresas_unicas)} empresas...")

# Usando tqdm para a barra de progresso
for empresa_id in tqdm(empresas_unicas, desc="Calculando Projeções"):
    dados_empresa = recebimentos_mensais[recebimentos_mensais['ID_RCBE'] == empresa_id].sort_values('MES_ANO')
    
    if len(dados_empresa) < 2:
        projecao = dados_empresa['VL'].iloc[-1] if len(dados_empresa) == 1 else 0
    else:
        X_proj = dados_empresa[['MES_ANO_ORD']]
        y_proj = dados_empresa['VL']
        model = LinearRegression()
        model.fit(X_proj, y_proj)
        proximo_mes_ord = X_proj.iloc[-1].values[0] + 2628000 * 10**9
        projecao = model.predict([[proximo_mes_ord]])[0]
        
    projecoes[empresa_id] = max(0, projecao)

df_final['PROJECAO_RECEBIMENTO'] = df_final['ID'].map(projecoes).fillna(0)
logging.info("Projeções calculadas e adicionadas ao dataframe final.")
logging.info(f"PASSO 4 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 5: SALVAR RESULTADOS ---
logging.info("\n[PASSO 5/5] Iniciando: Salvamento dos Arquivos Finais.")
start_time_step = time.time()
df_final.to_csv('empresas_analisadas.csv', index=False)
logging.info("Arquivo 'empresas_analisadas.csv' salvo com sucesso.")
df_transacoes.to_csv('transacoes_com_data.csv', index=False)
logging.info("Arquivo 'transacoes_com_data.csv' salvo com sucesso.")
logging.info(f"PASSO 5 concluído em {time.time() - start_time_step:.2f} segundos.")

# --- FIM DO SCRIPT ---
logging.info("\n=======================================================")
logging.info(f"=== ANÁLISE CONCLUÍDA COM SUCESSO ===")
logging.info(f"=== Tempo Total de Execução: {time.time() - start_time_total:.2f} segundos ===")
logging.info("=======================================================")