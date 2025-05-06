import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# ========================================
# CONFIGURAÇÃO DA PÁGINA
# ========================================
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

# ========================================
# FUNÇÕES PRINCIPAIS
# ========================================

@st.cache_data
def load_data(uploaded_file):
    """Carrega e trata os dados do arquivo."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, parse_dates=True, dayfirst=True, infer_datetime_format=True)
        else:
            df = pd.read_excel(uploaded_file, parse_dates=True)
        
        # Padroniza nomes de colunas
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Identifica coluna de data automaticamente
        date_cols = [col for col in df.columns if any(keyword in col for keyword in ['data', 'date', 'dt'])]
        if date_cols:
            df['data'] = pd.to_datetime(df[date_cols[0]], errors='coerce', dayfirst=True)
        
        # Verifica colunas essenciais
        required_cols = {'valor': ['valor', 'total', 'venda', 'amount'],
                        'empresa': ['empresa', 'cliente', 'customer'],
                        'vendedor': ['vendedor', 'responsavel', 'seller']}
        
        for standard_col, possible_cols in required_cols.items():
            for col in possible_cols:
                if col in df.columns:
                    df.rename(columns={col: standard_col}, inplace=True)
                    break
        
        # Conversão de tipos e limpeza
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df = df.dropna(subset=['data', 'valor'])
        
        # Adiciona colunas temporais
        df['mês'] = df['data'].dt.to_period('M').astype(str)
        df['trimestre'] = df['data'].dt.to_period('Q').astype(str)
        df['ano'] = df['data'].dt.year.astype(str)
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {str(e)}")
        return None

def create_filters(df):
    """Cria os filtros na sidebar."""
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de período
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    date_range = st.sidebar.date_input(
        "Período",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
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
        "Faixa de Valor (R$)",
        min_val, max_val, (min_val, max_val)
    )
    
    return {
        'date_range': date_range,
        'empresas': empresas,
        'vendedores': vendedores,
        'val_range': val_range
    }

def apply_filters(df, filters):
    """Aplica os filtros selecionados."""
    filtered_df = df.copy()
    
    # Filtros de data
    filtered_df = filtered_df[
        (filtered_df['data'].dt.date >= filters['date_range'][0]) & 
        (filtered_df['data'].dt.date <= filters['date_range'][1])
    ]
    
    # Outros filtros
    filtered_df = filtered_df[
        (filtered_df['empresa'].isin(filters['empresas'])) &
        (filtered_df['vendedor'].isin(filters['vendedores'])) &
        (filtered_df['valor'] >= filters['val_range'][0]) &
        (filtered_df['valor'] <= filters['val_range'][1])
    ]
    
    return filtered_df

def display_metrics(df):
    """Exibe as métricas principais."""
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

def create_visualizations(df):
    """Cria as visualizações gráficas."""
    st.subheader("📈 Visualizações")
    
    # Abas para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs([
        "Evolução Temporal", 
        "Desempenho por Vendedor", 
        "Top Clientes", 
        "Distribuição"
    ])
    
    with tab1:
        # Evolução temporal
        temp_df = df.groupby('mês').agg({'valor': 'sum'}).reset_index()
        fig = px.line(
            temp_df, x='mês', y='valor',
            title="Vendas Mensais",
            labels={'valor': 'Valor (R$)', 'mês': 'Mês'},
            markers=True
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Desempenho por vendedor
        seller_df = df.groupby('vendedor').agg({
            'valor': 'sum',
            'empresa': 'nunique'
        }).sort_values('valor', ascending=False).reset_index()
        
        fig = px.bar(
            seller_df, x='vendedor', y='valor',
            color='empresa',
            title="Vendas por Vendedor",
            labels={'valor': 'Valor (R$)', 'vendedor': 'Vendedor', 'empresa': 'Clientes Únicos'},
            text_auto='.2s'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Top clientes
        top_clients = df.groupby('empresa')['valor'].sum().nlargest(10).reset_index()
        
        fig = px.bar(
            top_clients, x='empresa', y='valor',
            title="Top 10 Clientes",
            labels={'valor': 'Valor (R$)', 'empresa': 'Empresa'},
            color='valor',
            text_auto='.2s'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Distribuição de valores
        fig = px.box(
            df, y='valor', x='vendedor',
            title="Distribuição de Valores por Vendedor",
            points="all"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_alerts(df):
    """Exibe alertas inteligentes."""
    st.sidebar.header("⚠️ Alertas")
    threshold = st.sidebar.number_input("Limite para alertas (R$)", value=10000)
    
    with st.expander("🔔 Alertas", expanded=True):
        # Vendedores abaixo do limiar
        low_performers = df.groupby('vendedor')['valor'].sum()[lambda x: x < threshold]
        if not low_performers.empty:
            st.warning("**Vendedores com Baixo Desempenho**")
            for seller, amount in low_performers.items():
                st.write(f"- {seller}: R$ {amount:,.2f}")
        
        # Clientes inativos
        latest_date = df['data'].max()
        inactive = set(df['empresa'].unique()) - set(df[df['data'] >= (latest_date - pd.Timedelta(days=90))]['empresa'].unique())
        if inactive:
            st.warning(f"**Clientes Inativos (últimos 90 dias):** {len(inactive)}")

# ========================================
# FUNÇÃO PRINCIPAL
# ========================================

def main():
    st.title("📊 Painel de Análise de Vendas")
    st.markdown("Visualize e analise o desempenho de vendas com métricas detalhadas.")
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Carregue seu arquivo de vendas (CSV ou Excel)",
        type=["csv", "xlsx", "xls"],
        help="O arquivo deve conter colunas para data, valor e identificadores"
    )
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        if df is not None:
            # Pré-visualização dos dados
            with st.expander("🔍 Visualizar Dados", expanded=False):
                st.dataframe(df.head(3))
                st.write(f"Registros carregados: {len(df):,}")
                st.write(f"Período: {df['data'].min().date()} a {df['data'].max().date()}")
            
            # Filtros e processamento
            filters = create_filters(df)
            filtered_df = apply_filters(df, filters)
            
            # Exibição dos resultados
            display_metrics(filtered_df)
            create_visualizations(filtered_df)
            display_alerts(filtered_df)
            
            # Exportação
            st.sidebar.download_button(
                "💾 Exportar Dados",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"vendas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("Carregue um arquivo para iniciar a análise")

if __name__ == "__main__":
    main()
