import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
import logging
import time
from tqdm import tqdm
import networkx as nx

# --- CONFIGURAÇÃO DO LOG ---
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, 
                    format=log_format,
                    handlers=[
                        logging.FileHandler("analise.log", mode='w'),
                        logging.StreamHandler()
                    ])

# --- INÍCIO DO SCRIPT ---
warnings.filterwarnings('ignore')
logging.info("======================================================")
logging.info("=== INICIANDO SCRIPT DE ANÁLISE (MODO HISTÓRICO) ===")
logging.info("======================================================")
start_time_total = time.time()

# --- PASSO 1: CARREGAR, LIMPAR E PREPARAR OS DADOS ---
logging.info("[PASSO 1/5] Iniciando: Carregamento, Limpeza e Preparação dos Dados.")
start_time_step = time.time()
try:
    df_id = pd.read_csv('Base 1 - ID.csv', sep=';')
    df_transacoes = pd.read_csv('Base 2 - Transações.csv', sep=';')
    logging.info(f"Arquivos carregados. Base ID: {df_id.shape[0]} linhas. Base Transações: {df_transacoes.shape[0]} linhas.")
except FileNotFoundError as e:
    logging.error(f"ERRO CRÍTICO: Arquivo não encontrado. Detalhe: {e}")
    exit()

# --- INÍCIO DA CORREÇÃO: Limpeza e Padronização dos IDs ---
logging.info("Realizando limpeza dos IDs (removendo espaços e padronizando para maiúsculas)...")
df_id['ID'] = df_id['ID'].astype(str).str.strip().str.upper()
df_transacoes['ID_PGTO'] = df_transacoes['ID_PGTO'].astype(str).str.strip().str.upper()
df_transacoes['ID_RCBE'] = df_transacoes['ID_RCBE'].astype(str).str.strip().str.upper()
logging.info(f"Limpeza concluída. Número de IDs únicos agora é: {df_id['ID'].nunique()}")
# --- FIM DA CORREÇÃO ---


# Feature Engineering
logging.info("Iniciando Feature Engineering...")
df_id['DT_REFE'] = pd.to_datetime(df_id['DT_REFE'], errors='coerce')
df_id['DT_ABRT'] = pd.to_datetime(df_id['DT_ABRT'], errors='coerce')
df_id['IDADE_EMPRESA'] = (df_id['DT_REFE'] - df_id['DT_ABRT']).dt.days / 365.25
logging.info("Coluna 'IDADE_EMPRESA' criada para cada snapshot de tempo.")
logging.info("Agregando dados de transações...")
pagamentos = df_transacoes.groupby('ID_PGTO')['VL'].agg(['sum', 'count']).rename(columns={'sum': 'VL_PAGAMENTOS', 'count': 'QT_PAGAMENTOS'})
recebimentos = df_transacoes.groupby('ID_RCBE')['VL'].agg(['sum', 'count']).rename(columns={'sum': 'VL_RECEBIMENTOS', 'count': 'QT_RECEBIMENTOS'})
df_final = df_id.merge(pagamentos, left_on='ID', right_index=True, how='left')
df_final = df_final.merge(recebimentos, left_on='ID', right_index=True, how='left')
df_final.fillna(0, inplace=True)
logging.info(f"PASSO 1 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 2: CLASSIFICAÇÃO DE MOMENTO DE VIDA (K-MEANS) ---
logging.info("\n[PASSO 2/5] Iniciando: Classificação de Momento de Vida para cada registro.")
start_time_step = time.time()
features = ['VL_FATU', 'VL_SLDO', 'IDADE_EMPRESA', 'VL_PAGAMENTOS', 'VL_RECEBIMENTOS']
X = df_final[features]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
K_CLUSTERS = 4
kmeans = KMeans(n_clusters=K_CLUSTERS, random_state=42, n_init=10)
df_final['CLUSTER'] = kmeans.fit_predict(X_scaled)
cluster_means = df_final.groupby('CLUSTER')[features].mean().sort_values('VL_FATU')
mapeamento = {cluster_means.index[0]: 'Pequeno Porte', cluster_means.index[1]: 'Em Crescimento', cluster_means.index[2]: 'Consolidada', cluster_means.index[3]: 'Grande Porte'}
df_final['MOMENTO_VIDA'] = df_final['CLUSTER'].map(mapeamento)
logging.info(f"PASSO 2 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 3: ANÁLISE DE REDE (OTIMIZADO) ---
logging.info("\n[PASSO 3/5] Iniciando: Análise da Rede de Transações.")
start_time_step = time.time()
G = nx.from_pandas_edgelist(df_transacoes, 'ID_PGTO', 'ID_RCBE', ['VL'], create_using=nx.DiGraph())
centralidade = nx.degree_centrality(G)
df_final['CENTRALIDADE'] = df_final['ID'].map(centralidade).fillna(0)
logging.info("Calculando nível de dependência máxima...")
total_pagamentos = df_transacoes.groupby('ID_PGTO')['VL'].sum()
total_recebimentos = df_transacoes.groupby('ID_RCBE')['VL'].sum()
max_pgto_parceiro = df_transacoes.groupby(['ID_PGTO', 'ID_RCBE'])['VL'].sum().groupby('ID_PGTO').max()
max_rcbe_parceiro = df_transacoes.groupby(['ID_RCBE', 'ID_PGTO'])['VL'].sum().groupby('ID_RCBE').max()
dependencia_pgto = (max_pgto_parceiro / total_pagamentos).rename("dep_pgto")
dependencia_rcbe = (max_rcbe_parceiro / total_recebimentos).rename("dep_rcbe")
df_dependencia = pd.concat([dependencia_pgto, dependencia_rcbe], axis=1).fillna(0)
dependencia_maxima = df_dependencia.max(axis=1)
df_final['NIVEL_DEPENDENCIA'] = df_final['ID'].map(dependencia_maxima).fillna(0)
logging.info(f"PASSO 3 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 4: MODELO DE PROJEÇÃO MELHORADO ---
logging.info("\n[PASSO 4/5] Iniciando: Modelo de Projeção de Recebimentos.")
start_time_step = time.time()
df_transacoes['DT_REFE'] = pd.to_datetime(df_transacoes['DT_REFE'], errors='coerce')
df_transacoes['MES_ANO'] = df_transacoes['DT_REFE'].dt.to_period('M')
recebimentos_mensais = df_transacoes.groupby(['ID_RCBE', 'MES_ANO'])['VL'].sum().reset_index()
projecoes = {}
empresas_unicas = recebimentos_mensais['ID_RCBE'].unique()
logging.info(f"Calculando projeções para {len(empresas_unicas)} empresas com histórico de recebimentos...")
for empresa_id in tqdm(empresas_unicas, desc="Calculando Projeções"):
    dados_empresa = recebimentos_mensais[recebimentos_mensais['ID_RCBE'] == empresa_id].sort_values('MES_ANO')
    n_months = len(dados_empresa)
    projecao = 0
    if n_months == 1:
        projecao = dados_empresa['VL'].iloc[-1]
    elif n_months == 2:
        mes1_val, mes2_val = dados_empresa['VL'].iloc[0], dados_empresa['VL'].iloc[1]
        if mes1_val > 0:
            taxa_crescimento = mes2_val / mes1_val
            projecao = mes2_val * taxa_crescimento
        else:
            projecao = mes2_val
    elif n_months >= 3:
        mes_ultimo_val, mes_penultimo_val = dados_empresa['VL'].iloc[-1], dados_empresa['VL'].iloc[-2]
        projecao = (mes_ultimo_val * 0.7) + (mes_penultimo_val * 0.3)
    projecoes[empresa_id] = max(0, projecao)
df_final['PROJECAO_RECEBIMENTO'] = df_final['ID'].map(projecoes).fillna(0)
logging.info(f"PASSO 4 concluído em {time.time() - start_time_step:.2f} segundos.")


# --- PASSO 5: SALVAR RESULTADOS ---
logging.info("\n[PASSO 5/5] Iniciando: Salvamento dos Arquivos Finais.")
start_time_step = time.time()
df_final.to_csv('empresas_analisadas.csv', index=False)
logging.info("Arquivo 'empresas_analisadas.csv' salvo com sucesso.")
df_transacoes.to_csv('transacoes_com_data.csv', index=False)
logging.info(f"PASSO 5 concluído em {time.time() - start_time_step:.2f} segundos.")

# --- FIM DO SCRIPT ---
logging.info("\n=======================================================")
logging.info(f"=== ANÁLISE CONCLUÍDA COM SUCESSO ===")
logging.info(f"=== Tempo Total de Execução: {time.time() - start_time_total:.2f} segundos ===")
logging.info("=======================================================")