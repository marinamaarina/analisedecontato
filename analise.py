import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Análise de Vendas Avançada",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .css-1aumxhk {
        background-color: #ffffff;
        background-image: none;
    }
    .st-b7 {
        color: #2c3e50;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Título e descrição
st.title("📊 Painel de Análise de Vendas")
st.markdown("""
    Visualize e analise o desempenho de vendas com métricas detalhadas e gráficos interativos.
    Utilize os filtros na barra lateral para personalizar sua análise.
""")
st.markdown("---")

# Função para carregar dados
@st.cache_data
def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Verificar e padronizar colunas
        required_cols = {'data': ['Data', 'DATE', 'data_venda'],
                        'valor': ['Valor', 'VALUE', 'total'],
                        'empresa': ['Empresa', 'Cliente', 'CLIENTE'],
                        'vendedor': ['Vendedor', 'Responsável', 'VENDEDOR']}
        
        for standard_col, possible_cols in required_cols.items():
            for col in possible_cols:
                if col in df.columns:
                    df.rename(columns={col: standard_col}, inplace=True)
                    break
        
        # Conversão de tipos
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Remover linhas com valores críticos ausentes
        df = df.dropna(subset=['data', 'valor', 'empresa'])
        
        # Adicionar colunas derivadas
        df['mês'] = df['data'].dt.to_period('M').astype(str)
        df['trimestre'] = df['data'].dt.to_period('Q').astype(str)
        df['ano'] = df['data'].dt.year.astype(str)
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        return None

# Componentes da barra lateral
def sidebar_filters(df):
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de período
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    date_range = st.sidebar.date_input(
        "Período",
        [min_date, max_date],
        min_date=min_date,
        max_date=max_date
    )
    
    # Filtros de seleção múltipla
    empresas = st.sidebar.multiselect(
        "Empresas",
        options=sorted(df['empresa'].unique()),
        default=df['empresa'].unique()
    )
    
    vendedores = st.sidebar.multiselect(
        "Vendedores",
        options=sorted(df['vendedor'].unique()),
        default=df['vendedor'].unique()
    )
    
    # Filtro de valor
    min_val, max_val = float(df['valor'].min()), float(df['valor'].max())
    val_range = st.sidebar.slider(
        "Faixa de Valor",
        min_val, max_val, (min_val, max_val)
    )
    
    # Filtro temporal
    time_granularity = st.sidebar.selectbox(
        "Agrupamento Temporal",
        ["Diário", "Semanal", "Mensal", "Trimestral", "Anual"]
    )
    
    return {
        'date_range': date_range,
        'empresas': empresas,
        'vendedores': vendedores,
        'val_range': val_range,
        'time_granularity': time_granularity
    }

# Aplicar filtros
def apply_filters(df, filters):
    filtered_df = df.copy()
    
    # Filtrar por data
    filtered_df = filtered_df[
        (filtered_df['data'].dt.date >= filters['date_range'][0]) & 
        (filtered_df['data'].dt.date <= filters['date_range'][1])
    ]
    
    # Filtrar por empresa e vendedor
    filtered_df = filtered_df[
        (filtered_df['empresa'].isin(filters['empresas'])) &
        (filtered_df['vendedor'].isin(filters['vendedores']))
    ]
    
    # Filtrar por valor
    filtered_df = filtered_df[
        (filtered_df['valor'] >= filters['val_range'][0]) &
        (filtered_df['valor'] <= filters['val_range'][1])
    ]
    
    # Determinar agrupamento temporal
    if filters['time_granularity'] == "Diário":
        filtered_df['periodo'] = filtered_df['data'].dt.date.astype(str)
    elif filters['time_granularity'] == "Semanal":
        filtered_df['periodo'] = filtered_df['data'].dt.to_period('W').astype(str)
    elif filters['time_granularity'] == "Mensal":
        filtered_df['periodo'] = filtered_df['mês']
    elif filters['time_granularity'] == "Trimestral":
        filtered_df['periodo'] = filtered_df['trimestre']
    else:
        filtered_df['periodo'] = filtered_df['ano']
    
    return filtered_df

# Métricas de resumo
def display_summary_metrics(df):
    st.subheader("📌 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Vendido", f"R$ {df['valor'].sum():,.2f}")
    
    with col2:
        st.metric("Nº de Transações", f"{len(df):,}")
    
    with col3:
        st.metric("Ticket Médio", f"R$ {df['valor'].mean():,.2f}")
    
    with col4:
        st.metric("Clientes Únicos", f"{df['empresa'].nunique():,}")
    
    st.markdown("---")

# Visualizações gráficas
def display_visualizations(df, time_granularity):
    st.subheader("📈 Visualizações")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Evolução Temporal", 
        "Distribuição por Vendedor", 
        "Top Clientes", 
        "Análise Detalhada"
    ])
    
    with tab1:
        # Gráfico de evolução temporal
        temp_df = df.groupby('periodo').agg({
            'valor': 'sum',
            'empresa': 'nunique'
        }).reset_index()
        
        fig = px.line(
            temp_df,
            x='periodo',
            y='valor',
            title=f"Vendas {time_granularity.lower()} (Total: R$ {df['valor'].sum():,.2f})",
            labels={'valor': 'Valor (R$)', 'periodo': 'Período'},
            markers=True
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Gráfico de desempenho por vendedor
        vendedor_df = df.groupby('vendedor').agg({
            'valor': ['sum', 'count'],
            'empresa': 'nunique'
        }).reset_index()
        vendedor_df.columns = ['Vendedor', 'Valor Total', 'Nº Vendas', 'Clientes Únicos']
        
        fig = px.bar(
            vendedor_df.sort_values('Valor Total', ascending=False),
            x='Vendedor',
            y='Valor Total',
            color='Nº Vendas',
            title="Desempenho por Vendedor",
            text='Valor Total',
            hover_data=['Clientes Únicos']
        )
        fig.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Top clientes
        top_clientes = df.groupby('empresa')['valor'].sum().nlargest(10).reset_index()
        
        fig = px.bar(
            top_clientes,
            x='empresa',
            y='valor',
            title="Top 10 Clientes por Valor",
            labels={'valor': 'Valor (R$)', 'empresa': 'Empresa'},
            text='valor',
            color='valor',
            color_continuous_scale='Blues'
        )
        fig.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Análise detalhada
        st.dataframe(
            df.sort_values('valor', ascending=False),
            column_config={
                "data": st.column_config.DateColumn("Data"),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "empresa": "Empresa",
                "vendedor": "Vendedor"
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )

# Sistema de alertas
def display_alerts(df):
    st.sidebar.header("⚠️ Alertas")
    
    # Configuração de limiares
    alert_threshold = st.sidebar.number_input(
        "Limite para alertas (R$)", 
        min_value=0, 
        value=10000,
        step=1000
    )
    
    # Verificar alertas
    with st.expander("🔔 Alertas e Insights", expanded=True):
        # Vendedores com baixo desempenho
        low_performers = df.groupby('vendedor')['valor'].sum().nsmallest(3)
        if any(low_performers < alert_threshold):
            st.warning("**Vendedores com Baixo Desempenho**")
            for seller, amount in low_performers.items():
                st.write(f"- {seller}: R$ {amount:,.2f}")
        
        # Clientes inativos recentemente
        latest_date = df['data'].max()
        active_customers = df[df['data'] >= (latest_date - pd.Timedelta(days=90))]['empresa'].unique()
        all_customers = df['empresa'].unique()
        inactive_customers = set(all_customers) - set(active_customers)
        
        if inactive_customers:
            st.warning(f"**Clientes Inativos (últimos 90 dias):** {len(inactive_customers)}")
            if st.button("Mostrar lista"):
                st.write(list(inactive_customers))
        
        # Transações anômalas (outliers)
        Q1 = df['valor'].quantile(0.25)
        Q3 = df['valor'].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df['valor'] < (Q1 - 1.5 * IQR)) | (df['valor'] > (Q3 + 1.5 * IQR))]
        
        if not outliers.empty:
            st.info(f"**Transações Anômalas Detectadas:** {len(outliers)}")
            st.dataframe(outliers, hide_index=True)

# Função principal
def main():
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "📤 Carregue seu arquivo de vendas (CSV ou Excel)",
        type=["csv", "xlsx", "xls"],
        help="O arquivo deve conter colunas para data, valor, empresa e vendedor"
    )
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        if df is not None:
            # Mostrar pré-visualização dos dados
            with st.expander("🔍 Visualizar Dados Carregados", expanded=False):
                st.dataframe(df.head(), hide_index=True)
                st.write(f"Total de registros: {len(df):,}")
                st.write(f"Período coberto: {df['data'].min().date()} a {df['data'].max().date()}")
            
            # Filtros e processamento
            filters = sidebar_filters(df)
            filtered_df = apply_filters(df, filters)
            
            # Exibir resultados
            display_summary_metrics(filtered_df)
            display_visualizations(filtered_df, filters['time_granularity'])
            display_alerts(filtered_df)
            
            # Opção para exportar
            st.sidebar.download_button(
                "💾 Exportar Dados Filtrados",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"vendas_filtradas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("Por favor, carregue um arquivo para iniciar a análise")
        st.image("https://cdn.pixabay.com/photo/2017/08/06/22/01/upload-2598377_1280.png", 
                width=400, caption="Arraste e solte seu arquivo de vendas aqui")

if __name__ == "__main__":
    main()
