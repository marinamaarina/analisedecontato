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

# Verificar se o arquivo foi carregado
if uploaded_file is not None:
    # Carregar os dados da planilha
    df = load_data(uploaded_file)

    # Exibir a tabela com os dados
    st.write("Tabela de Dados:")
    st.dataframe(df)

    # Filtros para as colunas
    st.sidebar.header("Filtros de Análise")

    # Filtro por Empresa
    empresa_filter = st.sidebar.selectbox("Filtrar por Empresa", ["Todas"] + df['Empresa'].unique().tolist())
    if empresa_filter != "Todas":
        df = df[df['Empresa'] == empresa_filter]

    # Filtro por Responsável
    responsavel_filter = st.sidebar.selectbox("Filtrar por Responsável", ["Todos"] + df['Responsável'].unique().tolist())
    if responsavel_filter != "Todos":
        df = df[df['Responsável'] == responsavel_filter]

    # Filtro por Segmento
    segmento_filter = st.sidebar.selectbox("Filtrar por Segmento", ["Todos"] + df['Segmento'].unique().tolist())
    if segmento_filter != "Todos":
        df = df[df['Segmento'] == segmento_filter]

    # Filtro por Cadência
    cadencia_filter = st.sidebar.selectbox("Filtrar por Cadência", ["Todas"] + df['Cadência'].unique().tolist())
    if cadencia_filter != "Todas":
        df = df[df['Cadência'] == cadencia_filter]

    # Filtro por Motivo
    motivo_filter = st.sidebar.selectbox("Filtrar por Motivo", ["Todos"] + df['Motivo'].unique().tolist())
    if motivo_filter != "Todos":
        df = df[df['Motivo'] == motivo_filter]

    # Filtro por Data (Intervalo de datas)
    st.sidebar.write("Filtrar por Data")
    data_inicio = st.sidebar.date_input("Data Início", df['Data'].min())
    data_fim = st.sidebar.date_input("Data Fim", df['Data'].max())
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df[(df['Data'] >= pd.to_datetime(data_inicio)) & (df['Data'] <= pd.to_datetime(data_fim))]

    # Exibir a tabela filtrada
    st.write("Tabela Filtrada:")
    st.dataframe(df)

    # Gráfico de Vendas por Segmento
    st.write("Distribuição de Vendas por Segmento")
    segmento_counts = df['Segmento'].value_counts()
    st.bar_chart(segmento_counts)

    # Gráfico de Vendas por Responsável
    st.write("Vendas por Responsável")
    responsavel_counts = df['Responsável'].value_counts()
    st.bar_chart(responsavel_counts)

    # Gráfico de Vendas por Motivo
    st.write("Vendas por Motivo")
    motivo_counts = df['Motivo'].value_counts()
    st.bar_chart(motivo_counts)

    # Adicional: Mostrar gráfico de vendas ao longo do tempo (data)
    st.write("Vendas ao Longo do Tempo")
    vendas_por_data = df.groupby(df['Data'].dt.to_period('M')).size()
    vendas_por_data.plot(kind='line', marker='o')
    plt.title('Vendas por Mês')
    plt.xlabel('Mês')
    plt.ylabel('Número de Vendas')
    st.pyplot()

    # Exemplo de Alerta: Excedendo um número de vendas para um Responsável
    st.sidebar.header("Configurações de Alerta")
    alerta_responsavel = st.sidebar.selectbox("Responsável para Alerta", ["Todos"] + df['Responsável'].unique().tolist())
    limite_alerta = st.sidebar.number_input("Limite de Vendas para Alerta", min_value=1, value=5)

    if alerta_responsavel != "Todos":
        vendas_responsavel = df[df['Responsável'] == alerta_responsavel].shape[0]
        if vendas_responsavel > limite_alerta:
            st.warning(f"Alerta: O responsável {alerta_responsavel} tem mais de {limite_alerta} vendas!")
        else:
            st.success(f"O responsável {alerta_responsavel} está dentro do limite de vendas.")
    else:
        st.write("Selecione um responsável para configurar alertas.")

else:
    st.write("Carregue um arquivo de vendas para iniciar a análise.")
