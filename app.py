import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Pesquisa", layout="wide", page_icon="📊")

# --- PROTEÇÃO POR SENHA ---
def check_password():
    """Retorna True se o usuário digitou a senha correta."""
    def password_entered():
        # Agora a senha é validada de forma segura através do st.secrets
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # não armazena a senha na sessão
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "🔒 Por favor, digite a senha para acessar o dashboard", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "🔒 Por favor, digite a senha para acessar o dashboard", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Senha incorreta")
        return False
    else:
        return True

if not check_password():
    st.stop()  # Impede que o resto do código seja executado até que a senha seja correta

# Função para carregar e limpar os dados
@st.cache_data
def load_data():
    df = pd.read_csv("SoloPesq.csv")
    
    # Garantir que event_timestamp é datetime
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], errors='coerce')
    
    # Ordenar por timestamp para manter o mais recente ao remover duplicatas
    df = df.sort_values('event_timestamp')
    
    # Remover duplicatas pelo email, mantendo o último (mais recente)
    df_cleaned = df.drop_duplicates(subset=['email'], keep='last').copy()
    
    # --- LIMPEZA BÁSICA PARA MELHORAR GRÁFICOS ---
    # Gênero
    df_cleaned['genero'] = df_cleaned['genero'].replace({'Outro': 'Outros'})
    
    # Idade
    map_idade = {
        'Menos de 18 anos': 'Menos de 18',
        '18 a 24 anos': '18-24',
        '25 a 34 anos': '25-34',
        '35 a 44 anos': '35-44',
        '45 a 54 anos': '45-54',
        '55 a 64 anos': '55-64',
        '65 a 74 anos': '65-74',
        'Maior que 75 anos': '75+'
    }
    df_cleaned['idade'] = df_cleaned['idade'].replace(map_idade)
    
    # Renda
    df_cleaned['renda'] = df_cleaned['renda'].replace({'Estou desempregado (a)': 'Estou desempregado(a)'})
    
    return df_cleaned

# Carregando dados
try:
    df = load_data()
except FileNotFoundError:
    st.error("Arquivo SoloPesq.csv não encontrado no diretório. Por favor, verifique.")
    st.stop()

# Título do Dashboard
st.title("📊 Dashboard Analítico - Pesquisa de Perfil")
st.markdown("Bem-vindo ao dashboard interativo. Utilize os filtros na barra lateral para cruzar as informações e obter respostas rápidas (ex: quantas mulheres de 18-24 anos ganham até R$ 2 mil?).")

# --- ORDENAÇÕES LÓGICAS ---
ordem_idade = ['Menos de 18', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+']
ordem_renda = [
    'Estou desempregado(a)',
    'Até R$1.000',
    'R$1.001 a R$2.500',
    'R$2.501 a R$5.000',
    'R$5.001 a R$10.000',
    'R$10.000 a R$20.000',
    'R$20.000 a R$30.000',
    'Mais de R$30.000'
]

# --- BARRA LATERAL (FILTROS) ---
try:
    st.sidebar.image("image_transparent.png", use_column_width=True)
except FileNotFoundError:
    pass

st.sidebar.header("Filtros")
st.sidebar.markdown("Selecione uma ou mais opções para filtrar:")

# Filtro de Gênero
opcoes_genero = df['genero'].dropna().unique().tolist()
filtro_genero = st.sidebar.multiselect("Gênero", opcoes_genero)

# Filtro de Idade (Mostrando ordenado logicamente)
opcoes_idade = [i for i in ordem_idade if i in df['idade'].unique()]
filtro_idade = st.sidebar.multiselect("Faixa Etária", opcoes_idade)

# Filtro de Renda
opcoes_renda = [r for r in ordem_renda if r in df['renda'].unique()]
filtro_renda = st.sidebar.multiselect("Renda", opcoes_renda)

# --- APLICANDO FILTROS ---
df_filtrado = df.copy()

if filtro_genero:
    df_filtrado = df_filtrado[df_filtrado['genero'].isin(filtro_genero)]
if filtro_idade:
    df_filtrado = df_filtrado[df_filtrado['idade'].isin(filtro_idade)]
if filtro_renda:
    df_filtrado = df_filtrado[df_filtrado['renda'].isin(filtro_renda)]

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric("Total de Cadastros (Únicos)", f"{len(df):,}".replace(",", "."))
col2.metric("Total Filtrado", f"{len(df_filtrado):,}".replace(",", "."))
col3.metric("Representatividade", f"{(len(df_filtrado)/len(df))*100:.1f}%" if len(df) > 0 else "0%")

st.markdown("---")

# --- GRÁFICOS ---
if len(df_filtrado) == 0:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    cor_roxa = "#9b59b6"
    
    colA, colB = st.columns(2)
    
    with colA:
        # Gráfico de Gênero (Donut Chart para visual mais moderno)
        df_gen = df_filtrado['genero'].value_counts().reset_index()
        df_gen.columns = ['Gênero', 'Quantidade']
        fig_gen = px.pie(df_gen, names='Gênero', values='Quantidade', title="Distribuição por Gênero", 
                         hole=0.4, color_discrete_sequence=px.colors.sequential.Purples_r)
        fig_gen.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_gen, use_container_width=True)
        
    with colB:
        # Gráfico de Faixa Etária (Ordenado de forma lógica)
        df_idade = df_filtrado['idade'].value_counts().reset_index()
        df_idade.columns = ['Faixa Etária', 'Quantidade']
        fig_idade = px.bar(df_idade, x='Faixa Etária', y='Quantidade', title="Distribuição por Faixa Etária",
                           text_auto=True, color_discrete_sequence=[cor_roxa])
        fig_idade.update_layout(xaxis={'categoryorder':'array', 'categoryarray': ordem_idade})
        fig_idade.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_idade, use_container_width=True)
        
    # Gráfico de Renda (Ordenado de forma lógica)
    df_renda = df_filtrado['renda'].value_counts().reset_index()
    df_renda.columns = ['Renda', 'Quantidade']
    fig_renda = px.bar(df_renda, y='Renda', x='Quantidade', title="Distribuição por Renda", orientation='h',
                       text_auto=True, color_discrete_sequence=[cor_roxa])
    fig_renda.update_layout(yaxis={'categoryorder':'array', 'categoryarray': ordem_renda[::-1]})
    fig_renda.update_traces(textfont_size=12, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_renda, use_container_width=True)

    with st.expander("Visualizar Dados (Amostra de 100 registros)"):
        st.dataframe(df_filtrado.head(100))
