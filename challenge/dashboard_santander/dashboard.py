import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard de Análise PJ", layout="wide")

# --- Carregamento dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("empresas_analisadas.csv")
        df['DT_REFE'] = pd.to_datetime(df['DT_REFE']) # Garante que a data é datetime
        df_transacoes = pd.read_csv("transacoes_com_data.csv")
        return df, df_transacoes
    except FileNotFoundError:
        st.error("Arquivo 'empresas_analisadas.csv' ou 'transacoes_com_data.csv' não encontrado. Execute o script 'analise_completa.py' primeiro.")
        return None, None

df, df_transacoes = carregar_dados()

if df is None:
    st.stop()

# --- Barra Lateral e Título ---
st.sidebar.title("Santander Challenge PJ")
pagina_selecionada = st.sidebar.radio("Navegar", ["Visão Geral do Portfólio", "Análise Individual de Empresa"])
st.sidebar.markdown("---")


# ==============================================================================
# --- PÁGINA 1: VISÃO GERAL DO PORTFÓLIO ---
# ==============================================================================
if pagina_selecionada == "Visão Geral do Portfólio":
    # (Esta página permanece igual à versão anterior)
    st.title("📊 Dashboard de Análise de Momento de Vida de Empresas")
    st.sidebar.header("Filtros Interativos")
    momentos = df['MOMENTO_VIDA'].unique()
    momento_selecionado = st.sidebar.multiselect("Momento de Vida:", options=momentos, default=momentos)
    faturamento_selecionado = st.sidebar.slider("Faixa de Faturamento Anual (R$):", int(df['VL_FATU'].min()), int(df['VL_FATU'].max()), (int(df['VL_FATU'].min()), int(df['VL_FATU'].max())))
    df_filtrado = df[df['MOMENTO_VIDA'].isin(momento_selecionado) & (df['VL_FATU'] >= faturamento_selecionado[0]) & (df['VL_FATU'] <= faturamento_selecionado[1])].copy()
    total_empresas = df_filtrado['ID'].nunique() # Corrigido para contar empresas únicas
    faturamento_medio = df_filtrado['VL_FATU'].mean()
    idade_media = df_filtrado['IDADE_EMPRESA'].mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Empresas Únicas", f"{total_empresas:,}".replace(",", "."))
    col2.metric("Faturamento Médio (por registro)", f"R$ {faturamento_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Idade Média (por registro)", f"{idade_media:.1f} anos")
    st.markdown("---")
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.subheader("Distribuição por Momento de Vida (por registro)")
        fig_bar = px.bar(df_filtrado['MOMENTO_VIDA'].value_counts().reset_index(), x='MOMENTO_VIDA', y='count', color='MOMENTO_VIDA', text_auto=True, labels={'count': 'Quantidade de Registros', 'MOMENTO_VIDA': 'Momento de Vida'})
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_graf2:
        st.subheader("Faturamento vs. Idade por Momento de Vida")
        if not df_filtrado.empty:
            df_filtrado['VL_SLDO_TAMANHO'] = df_filtrado['VL_SLDO'] - df_filtrado['VL_SLDO'].min()
        else:
            df_filtrado['VL_SLDO_TAMANHO'] = pd.Series(dtype='float64')
        fig_scatter = px.scatter(df_filtrado, x='IDADE_EMPRESA', y='VL_FATU', color='MOMENTO_VIDA', hover_name='ID', size='VL_SLDO_TAMANHO', hover_data={'VL_SLDO': ':,.2f'}, labels={'IDADE_EMPRESA': 'Idade da Empresa (Anos)', 'VL_FATU': 'Faturamento Anual (R$)'})
        st.plotly_chart(fig_scatter, use_container_width=True)
    st.subheader("Amostra dos Dados Filtrados")
    st.dataframe(df_filtrado[['ID', 'DT_REFE', 'MOMENTO_VIDA', 'VL_FATU', 'IDADE_EMPRESA', 'DS_CNAE']].head(1000).style.format({'VL_FATU': 'R$ {:,.2f}'}))
    st.caption(f"Exibindo as primeiras 1.000 de {len(df_filtrado)} registros encontrados.")

# ==============================================================================
# --- PÁGINA 2: ANÁLISE INDIVIDUAL DE EMPRESA (REFORMULADA) ---
# ==============================================================================
elif pagina_selecionada == "Análise Individual de Empresa":
    st.title("🔍 Análise Histórica e Projeções por Empresa")
    
    # Use os IDs únicos para a seleção
    id_unicos = df['ID'].unique()
    id_pesquisado = st.selectbox("Selecione o ID da Empresa:", options=id_unicos)

    if id_pesquisado:
        # Pega todos os registros da empresa selecionada e ordena por data
        dados_empresa = df[df['ID'] == id_pesquisado].sort_values('DT_REFE')
        
        # Pega o registro mais recente para métricas de valor único
        ultimo_registro = dados_empresa.iloc[-1]
        
        st.header(f"Resultados para: {ultimo_registro['ID']}")
        st.markdown(f"**CNAE:** {ultimo_registro['DS_CNAE']}")
        
        st.markdown("---")

        # --- Gráfico de Evolução ---
        st.subheader("Evolução Mensal do Faturamento e Saldo")
        fig_evolucao = px.line(
            dados_empresa, 
            x='DT_REFE', 
            y=['VL_FATU', 'VL_SLDO'], 
            markers=True,
            labels={'value': 'Valor (R$)', 'DT_REFE': 'Data de Referência'},
            title="Faturamento e Saldo ao Longo do Tempo"
        )
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- Métricas Médias e Projeção ---
        st.subheader("Métricas do Período e Projeções")
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Médio", f"R$ {dados_empresa['VL_FATU'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Saldo Médio", f"R$ {dados_empresa['VL_SLDO'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Projeção Próximo Mês", f"R$ {ultimo_registro['PROJECAO_RECEBIMENTO']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")
        
        # --- Detalhamento dos Registros ---
        st.subheader("Registros Históricos Detalhados")
        st.dataframe(dados_empresa[['DT_REFE', 'MOMENTO_VIDA', 'VL_FATU', 'VL_SLDO', 'IDADE_EMPRESA']].style.format({
            'VL_FATU': 'R$ {:,.2f}',
            'VL_SLDO': 'R$ {:,.2f}',
            'IDADE_EMPRESA': '{:.1f} anos'
        }))

        # --- Análise de Rede (valores são constantes para a empresa) ---
        st.subheader("Análise de Rede e Dependência (Total do Período)")
        col_net1, col_net2 = st.columns(2)
        with col_net1:
            st.metric("Nível de Centralidade na Rede", f"{ultimo_registro['CENTRALIDADE']:.2%}")
            st.info("Mede a 'popularidade' da empresa com base no total de transações.")
        with col_net2:
            st.metric("Nível de Dependência Máxima", f"{ultimo_registro['NIVEL_DEPENDENCIA']:.2%}")
            st.info("Indica a % máxima de transações com um único parceiro.")