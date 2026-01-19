import streamlit as st
import requests
import os
import json
import time
import concurrent.futures
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LEANTTRO | Buscador de Oportunidades", layout="wide", page_icon="🚀")

# --- ESTILO VISUAL (IDENTIDADE LEANTTRO NEON) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;700&family=Chakra+Petch:wght@400;700&display=swap');
    
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Kanit', sans-serif; }
    
    /* --- BARRA LATERAL (SIDEBAR) --- */
    section[data-testid="stSidebar"] {
        background-color: #2e2e2e !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* --- CORREÇÃO DE VISIBILIDADE: CAIXAS DE CÓDIGO (st.code) --- */
    .stCode pre, .stCode code {
        background-color: #111 !important;
        color: #D2FF00 !important; /* Verde Neon */
        border: 1px solid #444 !important;
    }

    /* --- TEXTOS/LABELS DOS INPUTS (BRANCO) --- */
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    
    /* Caixa de Informação Customizada */
    .custom-info-box {
        background-color: #1a1a1a;
        border-left: 4px solid #D2FF00;
        padding: 15px;
        color: #ffffff !important;
        font-size: 14px;
        margin-bottom: 20px;
        border-radius: 4px;
        border: 1px solid #444;
        line-height: 1.5;
    }

    /* Botão Principal Neon */
    div.stButton > button { 
        background-color: #D2FF00; color: #000; border: none; 
        border-radius: 4px; font-weight: 800; width: 100%; 
        text-transform: uppercase; font-style: italic;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { 
        background-color: #ffffff; 
        box-shadow: 0 0 15px rgba(210, 255, 0, 0.5);
        transform: skewX(-5deg);
    }
    
    /* Inputs */
    .stTextInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stNumberInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stSelectbox > div > div { background-color: #111; color: white; border: 1px solid #333; }

    /* Card do Lead */
    .lead-card {
        background-color: #0a0a0a !important; padding: 25px; border-radius: 8px;
        border: 1px solid #222; margin-bottom: 20px;
        position: relative; overflow: hidden;
    }
    .lead-card:hover { border-color: #D2FF00; }
    
    /* Scores */
    .score-hot { border-left: 4px solid #D2FF00; } 
    .score-warm { border-left: 4px solid #fff; }    
    .score-cold { border-left: 4px solid #333; }    

    .lead-title { font-family: 'Chakra Petch', sans-serif; font-size: 20px; font-weight: bold; color: #fff; margin-bottom: 5px; text-decoration: none; display: block; }
    .lead-title:hover { color: #D2FF00; }
    
    .tag-nicho { 
        background-color: #1a1a1a; color: #bbb; padding: 2px 8px; 
        border-radius: 4px; font-size: 10px; font-family: monospace;
        border: 1px solid #333; margin-right: 5px;
    }

    .recommendation-box {
        background-color: #111; border: 1px dashed #444; 
        padding: 10px; margin-top: 15px; border-radius: 4px;
    }
    .rec-title { color: #D2FF00; font-weight: bold; font-size: 12px; font-family: monospace; }
    .rec-text { font-size: 13px; color: #ddd; margin-top: 4px; }
    
    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; font-style: italic; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR CHAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# --- ESTRATÉGIA DE SUGESTÕES (BASEADA NO LEANTTRO.COM E CURRÍCULO) ---
SUGESTOES_STRATEGICAS = {
    "Sites de Freelance (Workana/99)": [
        "preciso programador python", # Venda Skill Técnica
        "criar site de vendas", # Venda Produto Loja Virtual
        "dashboard power bi", # Venda Skill Dados
        "integrar api sistema", # Venda Skill Backend
        "automação n8n", # Venda Skill Automação
        "analista de dados gcp" # Venda Skill Engenharia
    ],
    "LinkedIn (Postagens/Feed)": [
        "preciso de desenvolvedor python",
        "busco engenheiro de dados",
        "procuro gestor de tráfego" , # (Pode vender LP para os clientes deles)
        "indicação criação de site",
        "sistema lento ajuda", # Oportunidade de Refatoração/Consultoria
        "vaga pj desenvolvedor backend"
    ],
    "LinkedIn (Empresas)": [
        "Logística e Transportes", # Seu background na Elo Brindes
        "Agência de Marketing", # Parceria White Label
        "Consultoria de Dados",
        "E-commerce de Autopeças", # Seu nicho de portfólio
        "Assessoria de Eventos" # Para vender o sistema de casamentos
    ],
    "Instagram/Negócios (Estratégia Maps)": [
        "auto peças", # Venda: E-commerce Leanttro
        "assessoria de casamento", # Venda: Site de Casamento/Lista
        "buffet infantil", # Venda: Site de Festas
        "loja de roupas feminina", # Venda: Loja Virtual
        "advocacia", # Venda: Site Institucional
        "clinica de estética" # Venda: Site Institucional + Agendamento
    ],
    "Google (Geral)": [
        "contratar criação de site",
        "desenvolvedor python freelancer",
        "empresa de engenharia de dados",
        "orçamento loja virtual",
        "preciso de um cto"
    ]
}

# --- FUNÇÕES ---

def search_google_serper(query, period, num_results=10):
    url = "https://google.serper.dev/search"
    payload_dict = {
        "q": query,
        "num": num_results,
        "gl": "br", 
        "hl": "pt-br"
    }
    if period:
        payload_dict["tbs"] = period

    payload = json.dumps(payload_dict)
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            st.error(f"Erro Serper: {response.text}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return []

def analyze_lead_groq(title, snippet, link, groq_key):
    """Analisa o post e tenta extrair o autor e contexto"""
    if not groq_key: 
        return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    
    client = Groq(api_key=groq_key)
    
    system_prompt = f"""
    ATUE COMO: Head de Vendas da 'Leanttro Digital'.
    
    SEUS PRODUTOS (LEANTTRO.COM):
    1. CRIAÇÃO DE SITES: Institucionais, Landing Pages (Foco em conversão).
    2. E-COMMERCE: Lojas virtuais completas (Foco em Auto Peças e Varejo).
    3. FESTAS/EVENTOS: Sites para casamento, listas de presentes, RSVP.
    4. SOFTWARE CUSTOM: Sistemas Python, Dashboards Power BI, Engenharia de Dados (GCP/SQL).
    
    SEU PERFIL TÉCNICO (LEANDRO):
    Dev Full Stack (Python/Flask), Eng. de Dados (GCP, BigQuery, ETL), Automação (N8N).
    
    TAREFAS:
    1. Identifique o NOME DA PESSOA ou NOME DA EMPRESA.
    2. Analise se é LEAD DE VENDA (quer site/sistema) ou VAGA/FREELA (quer dev).
    3. Defina um SCORE (0-100) baseado no fit com o portfólio Leanttro.
    
    SAÍDA JSON OBRIGATÓRIA:
    {{
        "autor": "Nome (ou Empresa)",
        "score": (0-100),
        "resumo_post": "Resumo em 10 palavras",
        "produto_recomendado": "Qual serviço Leanttro oferecer?",
        "argumento_venda": "Dica curta de abordagem técnica ou comercial."
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TITULO: {title}\nSNIPPET: {snippet}\nLINK: {link}"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"score": 0, "autor": "Erro", "produto_recomendado": "Erro IA", "argumento_venda": "Falha na análise"}

# Função wrapper para rodar em paralelo
def process_single_item(item):
    titulo = item.get('title', '')
    link = item.get('link', '')
    snippet = item.get('snippet', '')
    data_pub = item.get('date', 'Data n/d')
    
    # Chama a IA
    analise = analyze_lead_groq(titulo, snippet, link, GROQ_API_KEY)
    
    return {
        "item": item,
        "analise": analise,
        "titulo": titulo,
        "link": link,
        "snippet": snippet,
        "data_pub": data_pub
    }

# --- INTERFACE ---

# 1. Definição do Estado da Seleção (Para pegar as dicas corretas)
# Precisamos definir a selectbox antes de usar na sidebar para as dicas serem reativas
# Mas no Streamlit a ordem visual importa. Usaremos um placeholder ou lógica direta.

with st.sidebar:
    st.markdown(f"<h1 style='color: #fff; text-align: center; font-style: italic;'>LEAN<span style='color:#D2FF00'>TTRO</span>.<br><span style='font-size:14px; color:#fff'>Buscador de Oportunidades</span></h1>", unsafe_allow_html=True)
    st.divider()
    
    if GROQ_API_KEY: st.success("🟢 IA Conectada") 
    else: st.error("🔴 Falta GROQ KEY")
    
    if SERPER_API_KEY: st.success("🟢 Google Search Ativo")
    else: st.error("🔴 Falta SERPER KEY")

    st.divider()
    
    # Placeholder para as dicas (será preenchido após o usuário selecionar a origem na área principal,
    # mas como Streamlit roda o script todo, vamos definir a origem logo abaixo e usar aqui)
    
    st.markdown("### 🎯 Modo de Caça")
    st.markdown("""
    <div class="custom-info-box">
        <b>Estratégia Leanttro:</b><br>
        O sistema analisa se o lead precisa de <b>Sites/E-commerce</b> (Produto) ou <b>Dev Python/Dados</b> (Serviço).
    </div>
    """, unsafe_allow_html=True)


st.markdown("<h2 style='color:white'>O QUE VAMOS <span style='color:#D2FF00'>CAÇAR</span> HOJE?</h2>", unsafe_allow_html=True)

# Layout de Busca
c1, c2, c3, c4 = st.columns([3, 3, 2, 1])

with c1:
    origem = st.selectbox("Onde buscar?", list(SUGESTOES_STRATEGICAS.keys()))

# --- VOLTA PARA A SIDEBAR PARA RENDERIZAR AS DICAS DINÂMICAS ---
with st.sidebar:
    st.markdown("### 💡 Sugestões para esta Fonte")
    dicas_atuais = SUGESTOES_STRATEGICAS.get(origem, [])
    for dica in dicas_atuais:
        st.code(dica, language="text")

with c2:
    termo = st.text_input("Termo ou Nicho:", placeholder="Copie uma sugestão ao lado...")
with c3:
    tempo = st.selectbox("Período:", [
        "Últimas 24 Horas",
        "Última Semana",
        "Último Mês",
        "Qualquer data"
    ])
with c4:
    qtd = st.number_input("Qtd", 1, 50, 8)

st.write("##")
btn = st.button("RASTREAR OPORTUNIDADES")

if btn and termo:
    if not (GROQ_API_KEY and SERPER_API_KEY):
        st.error("⚠️ Configure as chaves de API no Dokploy!")
    else:
        # TRATAMENTO DO FILTRO DE TEMPO
        periodo_api = ""
        if "24 Horas" in tempo: periodo_api = "qdr:d"
        elif "Semana" in tempo: periodo_api = "qdr:w"
        elif "Mês" in tempo: periodo_api = "qdr:m"

        # CONSTRUÇÃO DA QUERY INTELIGENTE
        query_final = termo
        
        if origem == "LinkedIn (Empresas)":
            query_final = f'site:linkedin.com/company "{termo}"'
        elif origem == "LinkedIn (Postagens/Feed)":
            query_final = f'site:linkedin.com/posts "{termo}"'
        elif origem == "Sites de Freelance (Workana/99)":
            # Busca nas duas maiores plataformas ao mesmo tempo
            query_final = f'(site:workana.com OR site:99freelas.com.br) "{termo}"'
        elif origem == "Instagram/Negócios (Estratégia Maps)":
            # Estratégia para achar empresas com contato
            query_final = f'site:instagram.com "{termo}" "gmail.com"'

        st.caption(f"🔎 Buscando: `{query_final}` | Fonte: `{origem}`")

        # BUSCA + PROCESSAMENTO PARALELO
        resultados = search_google_serper(query_final, periodo_api, qtd)
        
        if not resultados:
            st.warning("Nenhum sinal encontrado. Tente termos mais amplos.")
        else:
            bar_text = st.empty()
            prog = st.progress(0)
            
            # Lista para guardar os resultados processados
            processed_results = []
            
            bar_text.text("🕵️ IA analisando leads em paralelo...")
            
            # Usando ThreadPoolExecutor para rodar várias análises ao mesmo tempo
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Submete todas as tarefas
                future_to_item = {executor.submit(process_single_item, item): item for item in resultados}
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_item):
                    try:
                        data = future.result()
                        processed_results.append(data)
                    except Exception as exc:
                        st.error(f"Erro no processamento: {exc}")
                    
                    completed += 1
                    prog.progress(completed / len(resultados))

            bar_text.empty() # Limpa o texto de carregamento

            # RENDERIZAÇÃO DOS CARDS (Ordenados por Score)
            processed_results.sort(key=lambda x: x['analise'].get('score', 0), reverse=True)

            for p in processed_results:
                analise = p['analise']
                score = analise.get('score', 0)
                autor = analise.get('autor', 'Desconhecido')
                link = p['link']
                titulo = p['titulo']
                snippet = p['snippet']
                data_pub = p['data_pub']

                # Define estilo
                css_class = "score-cold"
                icon = "❄️"
                if score >= 80:
                    css_class = "score-hot"
                    icon = "🔥 HOT"
                elif score >= 50:
                    css_class = "score-warm"
                    icon = "⚠️ MORNO"

                card_html = f"""
<div class="lead-card {css_class}">
<div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
        <span style="color: #D2FF00; font-weight:bold; font-family:monospace;">{icon} SCORE: {score}</span>
        <span class="tag-nicho">Autor: {autor}</span>
    </div>
    <a href="{link}" target="_blank" style="background:#222; color:#fff; padding:5px 10px; text-decoration:none; border-radius:4px; font-size:12px;">VER POST 🔗</a>
</div>

<div style="margin-top:10px;">
    <a href="{link}" target="_blank" class="lead-title">{titulo}</a>
</div>
<div style="color:#666; font-size:11px; margin-bottom:5px;">🕒 {data_pub} | {snippet[:200]}...</div>

<div class="recommendation-box">
    <div class="rec-title">// ESTRATÉGIA:</div>
    <div style="color: #fff; font-weight:bold;">OFERTAR: {analise.get('produto_recomendado', 'N/A').upper()}</div>
    <div class="rec-text"><span style="color:#666">RESUMO:</span> {analise.get('resumo_post', '')}</div>
    <div class="rec-text" style="color:#D2FF00; margin-top:5px;">💡 " {analise.get('argumento_venda', '')} "</div>
</div>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)