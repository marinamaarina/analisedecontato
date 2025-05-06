import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Análise de Vendas", layout="wide")

# Título
st.title("Análise de Vendas")

# Função para carregar a planilha
@st.cache
def load_data(file):
    return pd.read_excel(file)

# Subir o arquivo de vendas
uploaded_file = st.file_uploader("Escolha uma planilha", type=["xlsx"])

if uploaded_file is not None:
    # Carregar os dados da planilha
    df = load_data(uploaded_file)
    
    # Exibir a tabela com os dados
    st.write("Tabela de Dados:")
    st.dataframe(df)

    # Mostrar uma visão geral das colunas
    st.write("Visão Geral:")
    st.write(df.describe())

    # Exemplo de análise: distribuição de vendas por segmento
    st.write("Distribuição de Vendas por Segmento")
    segmento_counts = df['Segmento'].value_counts()
    st.bar_chart(segmento_counts)

    # Exemplo de análise: vendas por responsável
    st.write("Vendas por Responsável")
    responsavel_counts = df['Responsável'].value_counts()
    st.bar_chart(responsavel_counts)

    # Filtrar dados por cadência
    cadencia = st.selectbox("Selecione a Cadência", df['Cadência'].unique())
    cadencia_df = df[df['Cadência'] == cadencia]
    st.write(f"Vendas com Cadência: {cadencia}")
    st.dataframe(cadencia_df)
    
    # Adicional: Mostrar gráfico de vendas ao longo do tempo (data)
    st.write("Vendas ao Longo do Tempo")
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    vendas_por_data = df.groupby(df['Data'].dt.to_period('M')).size()
    vendas_por_data.plot(kind='line', marker='o')
    plt.title('Vendas por Mês')
    plt.xlabel('Mês')
    plt.ylabel('Número de Vendas')
    st.pyplot()
