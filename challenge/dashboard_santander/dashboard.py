import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard de Análise PJ", layout="wide")

# --- Carregamento dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("empresas_analisadas.csv")
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
    st.title("📊 Dashboard de Análise de Momento de Vida de Empresas")
    
    # Filtros na barra lateral
    st.sidebar.header("Filtros Interativos")
    momentos = df['MOMENTO_VIDA'].unique()
    momento_selecionado = st.sidebar.multiselect("Momento de Vida:", options=momentos, default=momentos)
    
    faturamento_selecionado = st.sidebar.slider(
        "Faixa de Faturamento Anual (R$):", 
        int(df['VL_FATU'].min()), int(df['VL_FATU'].max()), 
        (int(df['VL_FATU'].min()), int(df['VL_FATU'].max()))
    )

    df_filtrado = df[
        df['MOMENTO_VIDA'].isin(momento_selecionado) &
        (df['VL_FATU'] >= faturamento_selecionado[0]) & 
        (df['VL_FATU'] <= faturamento_selecionado[1])
    ].copy() 

    # Métricas Principais
    total_empresas = df_filtrado.shape[0]
    faturamento_medio = df_filtrado['VL_FATU'].mean()
    idade_media = df_filtrado['IDADE_EMPRESA'].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Empresas", f"{total_empresas:,}".replace(",", "."))
    col2.metric("Faturamento Médio", f"R$ {faturamento_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Idade Média", f"{idade_media:.1f} anos")

    st.markdown("---")

    # Gráficos
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.subheader("Distribuição por Momento de Vida")
        fig_bar = px.bar(
            df_filtrado['MOMENTO_VIDA'].value_counts().reset_index(),
            x='MOMENTO_VIDA', y='count', color='MOMENTO_VIDA', text_auto=True,
            labels={'count': 'Quantidade de Empresas', 'MOMENTO_VIDA': 'Momento de Vida'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_graf2:
        st.subheader("Faturamento vs. Idade por Momento de Vida")
        
        if not df_filtrado.empty:
            df_filtrado['VL_SLDO_TAMANHO'] = df_filtrado['VL_SLDO'] - df_filtrado['VL_SLDO'].min()
        else:
            df_filtrado['VL_SLDO_TAMANHO'] = pd.Series(dtype='float64')

        fig_scatter = px.scatter(
            df_filtrado, x='IDADE_EMPRESA', y='VL_FATU', color='MOMENTO_VIDA',
            hover_name='ID', 
            size='VL_SLDO_TAMANHO',
            hover_data={'VL_SLDO': ':,.2f'},
            labels={'IDADE_EMPRESA': 'Idade da Empresa (Anos)', 'VL_FATU': 'Faturamento Anual (R$)'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # <<< INÍCIO DA CORREÇÃO >>>
    st.subheader("Amostra dos Dados das Empresas Filtradas")
    
    # Exibimos apenas as primeiras 1000 linhas para manter o dashboard rápido.
    st.dataframe(df_filtrado[['ID', 'MOMENTO_VIDA', 'VL_FATU', 'IDADE_EMPRESA', 'DS_CNAE', 'CENTRALIDADE', 'NIVEL_DEPENDENCIA']].head(1000).style.format({
        'VL_FATU': 'R$ {:,.2f}',
        'CENTRALIDADE': '{:.2%}',
        'NIVEL_DEPENDENCIA': '{:.2%}'
    }))
    
    # Adicionamos uma legenda para informar o usuário
    st.caption(f"Exibindo as primeiras 1.000 de {len(df_filtrado)} empresas encontradas.")
    # <<< FIM DA CORREÇÃO >>>


# ==============================================================================
# --- PÁGINA 2: ANÁLISE INDIVIDUAL DE EMPRESA ---
# ==============================================================================
elif pagina_selecionada == "Análise Individual de Empresa":
    st.title("🔍 Análise e Projeções por Empresa")
    
    id_pesquisado = st.selectbox("Selecione o ID da Empresa:", options=df['ID'].unique())

    if id_pesquisado:
        empresa = df[df['ID'] == id_pesquisado].iloc[0]
        
        st.header(f"Resultados para: {empresa['ID']}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Momento de Vida", empresa['MOMENTO_VIDA'])
        col2.metric("Faturamento Anual", f"R$ {empresa['VL_FATU']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Saldo Atual", f"R$ {empresa['VL_SLDO']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col4.metric("Idade", f"{empresa['IDADE_EMPRESA']:.1f} anos")
        
        st.metric(
        "**Projeção de Recebimento para o Próximo Mês (Simplificado)**",
        f"R$ {empresa['PROJECAO_RECEBIMENTO']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption("Projeção baseada em regressão linear sobre o histórico de recebimentos.")
        
        st.markdown("---")
        
        st.subheader("Análise de Rede e Dependência")
        col_net1, col_net2 = st.columns(2)
        
        with col_net1:
            st.metric("Nível de Centralidade na Rede", f"{empresa['CENTRALIDADE']:.2%}")
            st.info("Mede a 'popularidade' da empresa, ou seja, com quantas outras ela se conecta. Valores altos indicam um hub.")
        
        with col_net2:
            st.metric("Nível de Dependência Máxima", f"{empresa['NIVEL_DEPENDENCIA']:.2%}")
            st.info("Indica a porcentagem máxima de transações (pagamentos ou recebimentos) com um único parceiro.")

        st.subheader("Histórico de Transações Mensais")
        transacoes_empresa_pg = df_transacoes[df_transacoes['ID_PGTO'] == id_pesquisado]
        transacoes_empresa_rc = df_transacoes[df_transacoes['ID_RCBE'] == id_pesquisado]
        
        pagamentos_mes = transacoes_empresa_pg.groupby('MES_ANO')['VL'].sum().reset_index().rename(columns={'VL': 'Pagamentos'})
        recebimentos_mes = transacoes_empresa_rc.groupby('MES_ANO')['VL'].sum().reset_index().rename(columns={'VL': 'Recebimentos'})
        
        if not pagamentos_mes.empty or not recebimentos_mes.empty:
            hist_transacoes = pd.merge(pagamentos_mes, recebimentos_mes, on='MES_ANO', how='outer').fillna(0)
            hist_transacoes['MES_ANO'] = hist_transacoes['MES_ANO'].astype(str)
            
            fig_hist = px.bar(
                hist_transacoes, x='MES_ANO', y=['Pagamentos', 'Recebimentos'],
                barmode='group', labels={'value': 'Valor (R$)', 'MES_ANO': 'Mês'},
                title=f"Pagamentos vs. Recebimentos de {id_pesquisado}"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.write("Não há histórico de transações para exibir.")