import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard PJ", layout="wide", initial_sidebar_state="expanded")

# --- Carregamento e Preparação dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("empresas_analisadas.csv")
        df['DT_REFE'] = pd.to_datetime(df['DT_REFE'])
        df_transacoes = pd.read_csv("transacoes_com_data.csv")
    except FileNotFoundError:
        st.error("Arquivo 'empresas_analisadas.csv' ou 'transacoes_com_data.csv' não encontrado. Execute o script 'analise_completa.py' primeiro.")
        return None, None

    # A função de classificar setor foi removida.
    return df, df_transacoes

df, df_transacoes = carregar_dados()

if df is None:
    st.stop()

# --- Barra Lateral ---
st.sidebar.title("Sistema de Análise PJ")
pagina_selecionada = st.sidebar.radio(
    "Navegar", 
    ["Visão Geral e Prospecção", "Análise Individual", "Insights Comerciais"]
)
st.sidebar.markdown("---")


# ==============================================================================
# --- PÁGINA 1: VISÃO GERAL E PROSPECÇÃO ---
# ==============================================================================
if pagina_selecionada == "Visão Geral e Prospecção":
    st.title("Dashboard de Prospecção e Análise de Empresas")
    
    st.sidebar.header("Filtros de Segmentação")
    momentos = df['MOMENTO_VIDA'].unique()
    momento_selecionado = st.sidebar.multiselect("Momento de Vida:", options=momentos, default=momentos)
    faturamento_selecionado = st.sidebar.slider("Faixa de Faturamento Anual (R$):", int(df['VL_FATU'].min()), int(df['VL_FATU'].max()), (int(df['VL_FATU'].min()), int(df['VL_FATU'].max())))
    
    # --- FILTROS AVANÇADOS REMOVIDOS DAQUI ---
    
    # Lógica de filtragem simplificada
    df_filtrado = df[
        (df['MOMENTO_VIDA'].isin(momento_selecionado)) & 
        (df['VL_FATU'].between(*faturamento_selecionado))
    ].copy()
    
    total_empresas = df_filtrado['ID'].nunique()
    faturamento_medio = df_filtrado['VL_FATU'].mean()
    idade_media = df_filtrado['IDADE_EMPRESA'].mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Empresas Únicas", f"{total_empresas:,}".replace(",", "."))
    col2.metric("Faturamento Médio (por registro)", f"R$ {faturamento_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Idade Média (por registro)", f"{idade_media:.1f} anos")
    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        # Gráfico de Macro-Setor foi revertido para o de Momento de Vida
        st.subheader("Distribuição por Momento de Vida")
        fig_bar = px.bar(df_filtrado['MOMENTO_VIDA'].value_counts().reset_index(), x='MOMENTO_VIDA', y='count', color='MOMENTO_VIDA', text_auto=True, labels={'count': 'Registros', 'MOMENTO_VIDA': 'Momento de Vida'})
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_graf2:
        st.subheader("Faturamento vs. Idade")
        if not df_filtrado.empty:
            df_filtrado['VL_SLDO_TAMANHO'] = df_filtrado['VL_SLDO'] - df_filtrado['VL_SLDO'].min()
        else:
            df_filtrado['VL_SLDO_TAMANHO'] = pd.Series(dtype='float64')
        # Usando sample para evitar sobrecarga do gráfico com muitos pontos
        amostra_grafico = df_filtrado.sample(min(1000, len(df_filtrado)))
        fig_scatter = px.scatter(amostra_grafico, x='IDADE_EMPRESA', y='VL_FATU', color='MOMENTO_VIDA', hover_name='ID', size='VL_SLDO_TAMANHO', hover_data={'VL_SLDO': ':,.2f'}, labels={'IDADE_EMPRESA': 'Idade (Anos)', 'VL_FATU': 'Faturamento (R$)'})
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with st.expander("Ver Amostra dos Dados Filtrados"):
        # Removido 'MACRO_SETOR' da visualização da tabela
        st.dataframe(df_filtrado[['ID', 'DT_REFE', 'MOMENTO_VIDA', 'VL_FATU', 'IDADE_EMPRESA', 'DS_CNAE']].head(1000).style.format({'VL_FATU': 'R$ {:,.2f}'}))
        st.caption(f"Exibindo as primeiras 1.000 de {len(df_filtrado)} registros encontrados.")

# ==============================================================================
# --- PÁGINA 2: ANÁLISE INDIVIDUAL ---
# ==============================================================================
elif pagina_selecionada == "Análise Individual":
    # (Esta página não foi alterada, mas o código é incluído para ser completo)
    st.title("Análise Individual da Empresa")
    id_unicos = sorted(df['ID'].unique())
    id_pesquisado = st.selectbox("Selecione o ID da Empresa:", options=id_unicos)

    if id_pesquisado:
        dados_empresa = df[df['ID'] == id_pesquisado].sort_values('DT_REFE')
        ultimo_registro = dados_empresa.iloc[-1]
        
        st.header(f"Resultados para: {ultimo_registro['ID']}")
        st.markdown(f"**CNAE:** {ultimo_registro['DS_CNAE']}")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Visão Geral e Histórico", "Comparação com Pares"])
        
        with tab1:
            st.subheader("Métricas Chave do Período")
            col1, col2, col3 = st.columns(3)
            col1.metric("Faturamento Anual (constante)", f"R$ {ultimo_registro['VL_FATU']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col2.metric("Saldo Médio", f"R$ {dados_empresa['VL_SLDO'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col3.metric("Projeção Próximo Mês", f"R$ {ultimo_registro['PROJECAO_RECEBIMENTO']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            st.subheader("Evolução Mensal do Saldo em Conta")
            fig_saldo = px.line(dados_empresa, x='DT_REFE', y='VL_SLDO', markers=True, labels={'VL_SLDO': 'Saldo (R$)', 'DT_REFE': 'Data'}, title="Variação do Saldo em Conta")
            st.plotly_chart(fig_saldo, use_container_width=True)
            
            with st.expander("Ver Registros Históricos Detalhados"):
                st.dataframe(dados_empresa[['DT_REFE', 'MOMENTO_VIDA', 'VL_FATU', 'VL_SLDO', 'IDADE_EMPRESA']].style.format({'VL_FATU': 'R$ {:,.2f}', 'VL_SLDO': 'R$ {:,.2f}', 'IDADE_EMPRESA': '{:.1f} anos'}))

        with tab2:
            st.subheader("Benchmarking de Performance vs. Pares do Setor")
            momento_atual = ultimo_registro['MOMENTO_VIDA']
            cnae_atual = ultimo_registro['DS_CNAE']
            df_peers = df[(df['DS_CNAE'] == cnae_atual) & (df['MOMENTO_VIDA'] == momento_atual) & (df['ID'] != id_pesquisado)]
            
            if df_peers.empty:
                st.warning("Não foram encontrados pares com o mesmo CNAE e Momento de Vida para comparação.")
            else:
                peer_avg_fatu = df_peers['VL_FATU'].mean()
                peer_avg_saldo = df_peers['VL_SLDO'].mean()
                delta_fatu_str, delta_saldo_str = "N/A", "N/A"
                if peer_avg_fatu > 0:
                    delta_fatu_val = ((ultimo_registro['VL_FATU'] - peer_avg_fatu) / peer_avg_fatu) * 100
                    delta_fatu_str = f"{delta_fatu_val:.1f}%"
                if peer_avg_saldo != 0:
                    delta_saldo_val = ((dados_empresa['VL_SLDO'].mean() - peer_avg_saldo) / abs(peer_avg_saldo)) * 100
                    delta_saldo_str = f"{delta_saldo_val:.1f}%"
                
                col1, col2 = st.columns(2)
                col1.metric(f"Faturamento Anual ({momento_atual})", f"R$ {ultimo_registro['VL_FATU']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=delta_fatu_str)
                col2.metric("Saldo Médio (no período)", f"R$ {dados_empresa['VL_SLDO'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=delta_saldo_str)
                st.caption(f"A comparação é feita com {len(df_peers['ID'].unique())} empresas do setor '{cnae_atual}' classificadas como '{momento_atual}'.")

# ==============================================================================
# --- PÁGINA 3: INSIGHTS COMERCIAIS ---
# ==============================================================================
elif pagina_selecionada == "Insights Comerciais":
    # (Esta página não foi alterada, mas o código é incluído para ser completo)
    st.title("Insights para Abordagem Comercial")
    id_unicos = sorted(df['ID'].unique())
    id_pesquisado = st.selectbox("Selecione o ID da Empresa para gerar insights:", options=id_unicos)

    if id_pesquisado:
        dados_empresa = df[df['ID'] == id_pesquisado].sort_values('DT_REFE')
        ultimo_registro = dados_empresa.iloc[-1]
        
        # A lógica para gerar insights aqui pode precisar de um ajuste se ela usa 'MACRO_SETOR'
        # Verificando a função...
        def gerar_insights(empresa, historico):
            # Esta função não usa 'MACRO_SETOR', então está OK.
            insights = []
            saldo_medio = historico['VL_SLDO'].mean()
            if saldo_medio < 0:
                insights.append(f"**Ponto de Atenção: Fluxo de Caixa Negativo**\n\n- O saldo médio da empresa nos últimos meses foi de **R$ {saldo_medio:,.2f}**. Isso indica uma forte necessidade de capital de giro.\n\n- **Produto Sugerido:** Oferta proativa de **Capital de Giro** com taxas competitivas para estabilizar o fluxo de caixa.")
            elif saldo_medio < (empresa['VL_FATU'] / 12 * 0.5):
                insights.append(f"**Oportunidade: Otimização de Caixa**\n\n- A empresa opera com um saldo médio de **R$ {saldo_medio:,.2f}**, que é relativamente baixo para seu faturamento.\n\n- **Produto Sugerido:** Apresentar soluções de **Gestão de Caixa (Cash Management)** e **Investimentos de Curto Prazo**.")
            if empresa['NIVEL_DEPENDENCIA'] > 0.4:
                insights.append(f"**Risco de Concentração**\n\n- **{empresa['NIVEL_DEPENDENCIA']:.1%}** das transações da empresa estão concentradas em um único parceiro comercial.\n\n- **Argumento de Venda:** Posicionar o banco como um parceiro estratégico para mitigar riscos, oferecendo **Seguro de Crédito** ou consultoria para **diversificação de recebíveis**.")
            if empresa['CENTRALIDADE'] > df['CENTRALIDADE'].quantile(0.85):
                insights.append(f"**Oportunidade Estratégica: Empresa-Hub**\n\n- Esta empresa é um **hub** em sua rede, com alta conectividade.\n\n- **Produto Sugerido:** Oferta de **Plataforma de Pagamentos Automatizados** e **Gestão de Cobranças**.")
            if empresa['MOMENTO_VIDA'] == 'Em Crescimento':
                insights.append(f"**Apoio ao Crescimento**\n\n- A empresa está classificada como 'Em Crescimento', indicando uma fase de expansão que demanda investimentos.\n\n- **Produto Sugerido:** Linhas de crédito para **investimento em ativos (FINAME, BNDES)**.")
            if not insights:
                insights.append("**Perfil Estável**\n\n- A empresa apresenta um perfil financeiro estável. O foco da abordagem deve ser no **relacionamento e na oferta de produtos que superem a concorrência**.")
            return insights

        st.header(f"Sugestões de Abordagem para: {ultimo_registro['ID']}")
        st.markdown(f"**Setor (CNAE):** {ultimo_registro['DS_CNAE']} | **Momento de Vida Atual:** {ultimo_registro['MOMENTO_VIDA']}")
        st.markdown("---")
        lista_insights = gerar_insights(ultimo_registro, dados_empresa)
        for insight in lista_insights:
            st.info(insight)