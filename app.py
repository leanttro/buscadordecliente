import streamlit as st
import requests
import os
import json
import time
import concurrent.futures
import pandas as pd
import re
import random
from io import BytesIO
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LEANTTRO | Buscador de Oportunidades", layout="wide", page_icon="🚀")

# --- ESTILO VISUAL (IDENTIDADE LEANTTRO NEON - MANTIDA INTACTA) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;700&family=Chakra+Petch:wght@400;700&display=swap');
    
    /* --- FIX: REMOVER BARRA BRANCA DO TOPO --- */
    header {
        visibility: hidden;
        height: 0px;
    }
    div[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    /* Ajusta o padding para o conteúdo subir e ocupar o espaço vazio */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* --- CONFIGURAÇÃO GERAL --- */
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
    
    /* ESTILO DAS ABAS (TABS) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border: 1px solid #333; color: #888; border-radius: 4px; }
    .stTabs [aria-selected="true"] { background-color: #D2FF00 !important; color: #000 !important; font-weight: bold; }

    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; font-style: italic; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR CHAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# --- ESTRATÉGIA DE SUGESTÕES (MANTIDA ORIGINAL) ---
SUGESTOES_STRATEGICAS = {
    "Sites de Freelance (Workana/99)": [
        "preciso programador python", 
        "criar site de vendas", 
        "dashboard power bi", 
        "integrar api sistema", 
        "automação n8n", 
        "analista de dados gcp" 
    ],
    "LinkedIn (Postagens/Feed)": [
        "preciso de desenvolvedor python",
        "busco freela criação de site",
        "procuro gestor de tráfego" , 
        "indicação criação de site",
        "sistema lento ajuda", 
        "vaga pj desenvolvedor backend" 
    ],
    "LinkedIn (Empresas)": [
        "Logística e Transportes", 
        "Agência de Marketing", 
        "Consultoria de Dados",
        "E-commerce de Autopeças", 
        "Assessoria de Eventos" 
    ],
    "Instagram/Negócios (Estratégia Maps)": [
        "auto peças", 
        "assessoria de casamento", 
        "buffet infantil", 
        "loja de roupas feminina", 
        "advocacia", 
        "clinica de estética" 
    ],
    "Google (Geral)": [
        "contratar criação de site",
        "desenvolvedor python freelancer",
        "empresa de engenharia de dados",
        "orçamento loja virtual",
        "preciso de um cto"
    ]
}

# --- FUNÇÕES AUXILIARES ---

def to_excel(df):
    """Converte DataFrame para bytes de Excel para download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    return output.getvalue()

def extrair_email(texto):
    """Extrai e-mail de um texto usando Regex"""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(texto))
    return match.group(0) if match else None

def limpar_nome_insta(titulo):
    """Limpa o título do Instagram"""
    if "•" in titulo: return titulo.split("•")[0].strip()
    return titulo[:40]

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
        
        # DEBUG: Se der erro, printa no terminal/console do streamlit
        if response.status_code != 200:
            print(f"ERRO SERPER: {response.status_code} - {response.text}")
            return []
            
        return response.json().get("organic", [])
    except Exception as e:
        print(f"ERRO CONEXÃO SERPER: {e}")
        return []

def analyze_lead_groq(title, snippet, link, groq_key):
    """Analisa o post e tenta extrair o autor e contexto"""
    if not groq_key: 
        return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    
    client = Groq(api_key=groq_key)
    
    system_prompt = f"""
    ATUE COMO: Head de Vendas da 'Leanttro Digital'.
    
    SEUS PRODUTOS (LEANTTRO.COM) - PRIORIDADE 1 (VENDER PROJETO/FREELA):
    1. CRIAÇÃO DE SITES/LPs: "Preciso de um site", "Melhorar conversão", "Landing Page".
    2. E-COMMERCE: "Loja virtual", "Vender online", "Woocommerce/Shopify".
    3. SISTEMAS/DADOS: "Automação", "Dashboard", "Script Python", "Raspagem de dados", "Integração API".
    
    OBJETIVO SECUNDÁRIO - PRIORIDADE 2 (VAGA DE EMPREGO/CONTRATAÇÃO):
    - Se o post for "Vaga CLT", "Contratação PJ fixo", "Join our team", "Estamos contratando dev".
    
    TAREFAS:
    1. Identifique o NOME e o TIPO DE OPORTUNIDADE.
    2. CALCULE O SCORE:
       - PROJETO/FREELA (Escopo fechado/Agência) = SCORE ALTO (80-100). 🔥
       - VAGA/EMPREGO (Longo prazo/Fixo) = SCORE MÉDIO (50-79). ⚠️
       - LIXO/IRRELEVANTE = SCORE BAIXO (0-49). ❄️
    
    SAÍDA JSON OBRIGATÓRIA:
    {{
        "autor": "Nome (ou Empresa)",
        "score": (0-100),
        "resumo_post": "Resumo em 10 palavras",
        "produto_recomendado": "Serviço Leanttro (se projeto) ou 'Candidatura Vaga' (se emprego)",
        "argumento_venda": "Se for PROJETO: Foque em entrega rápida/qualidade Leanttro. Se for VAGA: Destaque o perfil Sênior/Fullstack do Leandro."
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

def process_single_item(item):
    """Função wrapper para rodar em paralelo"""
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

# --- INTERFACE PRINCIPAL ---

# Sidebar Global
with st.sidebar:
    st.markdown(f"<h1 style='color: #fff; text-align: center; font-style: italic;'>LEAN<span style='color:#D2FF00'>TTRO</span>.<br><span style='font-size:14px; color:#fff'>Intelligence Hub</span></h1>", unsafe_allow_html=True)
    st.divider()
    
    if GROQ_API_KEY: st.success("🟢 IA Conectada") 
    else: st.error("🔴 Falta GROQ KEY")
    
    if SERPER_API_KEY: st.success("🟢 Google Search Ativo")
    else: st.error("🔴 Falta SERPER KEY")

    st.divider()
    
    st.markdown("### 🎯 Modo de Caça")
    st.markdown("""
    <div class="custom-info-box">
        <b>Prioridade Leanttro:</b><br>
        1. <b>Projetos/Freelas (🔥):</b> Vender sites e serviços da agência.<br>
        2. <b>Vagas (⚠️):</b> Emprego fixo (Plano B).
    </div>
    """, unsafe_allow_html=True)

# SISTEMA DE ABAS (TABS) PARA ORGANIZAR
tab1, tab2 = st.tabs(["📡 RADAR DE OPORTUNIDADES (IA)", "⛏️ MINERADOR DE LEADS (SERPER API)"])

# ==============================================================================
# ABA 1: O SEU BUSCADOR ORIGINAL (IA + SERPER)
# ==============================================================================
with tab1:
    st.markdown("<h2 style='color:white'>RADAR DE <span style='color:#D2FF00'>OPORTUNIDADES</span></h2>", unsafe_allow_html=True)

    # Layout de Busca
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])

    with c1:
        origem = st.selectbox("Onde buscar?", list(SUGESTOES_STRATEGICAS.keys()))

    # --- Dicas Dinâmicas na Sidebar ---
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
    btn = st.button("RASTREAR OPORTUNIDADES", key="btn_radar")

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
                query_final = f'(site:workana.com OR site:99freelas.com.br) "{termo}"'
            elif origem == "Instagram/Negócios (Estratégia Maps)":
                # Versão segura para a aba 1 também
                query_final = f'site:instagram.com "{termo}" (gmail.com OR hotmail.com OR contato)'

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
                data_export = [] # Lista limpa para o Excel
                
                bar_text.text("🕵️ IA analisando leads em paralelo...")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_item = {executor.submit(process_single_item, item): item for item in resultados}
                    
                    completed = 0
                    for future in concurrent.futures.as_completed(future_to_item):
                        try:
                            data = future.result()
                            processed_results.append(data)
                            
                            # Prepara dados para Excel
                            analise_data = data['analise']
                            data_export.append({
                                "Titulo": data['titulo'],
                                "Link": data['link'],
                                "Score": analise_data.get('score'),
                                "Autor": analise_data.get('autor'),
                                "Resumo": analise_data.get('resumo_post'),
                                "Produto": analise_data.get('produto_recomendado'),
                                "Argumento": analise_data.get('argumento_venda')
                            })
                            
                        except Exception as exc:
                            st.error(f"Erro no processamento: {exc}")
                        
                        completed += 1
                        prog.progress(completed / len(resultados))

                bar_text.empty() 

                # ORDENAÇÃO
                processed_results.sort(key=lambda x: x['analise'].get('score', 0), reverse=True)
                
                # --- BOTÃO DE DOWNLOAD EXCEL ---
                if data_export:
                    df_radar = pd.DataFrame(data_export)
                    st.download_button(
                        label="📥 BAIXAR RELATÓRIO DO RADAR (EXCEL)",
                        data=to_excel(df_radar),
                        file_name="radar_leanttro.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_radar"
                    )

                # RENDERIZAÇÃO DOS CARDS
                for p in processed_results:
                    analise = p['analise']
                    score = analise.get('score', 0)
                    autor = analise.get('autor', 'Desconhecido')
                    link = p['link']
                    titulo = p['titulo']
                    snippet = p['snippet']
                    data_pub = p['data_pub']

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


# ==============================================================================
# ABA 2: MINERADOR DE LEADS (CORRIGIDO PARA EVITAR ERRO 400 - QUERY NOT ALLOWED)
# ==============================================================================
with tab2:
    st.markdown("<h2 style='color:white'>MINERADOR DE <span style='color:#D2FF00'>LEADS B2B</span></h2>", unsafe_allow_html=True)
    st.caption("Focado em encontrar e-mails públicos de empresas no Instagram. Ideal para Buffets e Assessores para a estratégia de parceria.")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1: 
        cidade_alvo = st.text_input("Cidade Alvo:", value="São Paulo")
    with col_m2: 
        nicho_alvo = st.selectbox("Nicho:", ["Buffet Casamento", "Assessoria de Eventos", "Espaço de Eventos", "Outro"])
    with col_m3: 
        termo_custom = ""
        if nicho_alvo == "Outro":
            termo_custom = st.text_input("Digite o Nicho:", placeholder="Ex: Clínica Estética")
    
    termo_final = termo_custom if nicho_alvo == "Outro" else nicho_alvo
    
    st.write("##")
    btn_mine = st.button("⛏️ INICIAR MINERAÇÃO (VIA API)", key="btn_mine")
    
    if btn_mine:
        if not termo_final:
            st.error("Defina um nicho para buscar.")
        elif not SERPER_API_KEY:
            st.error("Configure sua SERPER API KEY na aba lateral.")
        else:
            leads_encontrados = []
            status_box = st.status("⛏️ Minerando Google (Via Serper API)...", expanded=True)
            
            # Termos de variação para melhorar a busca
            termos_busca = [termo_final]
            if "Buffet" in termo_final: termos_busca.append("Espaço para festas")
            if "Assessoria" in termo_final: termos_busca.append("Cerimonialista")
            
            total_varredura = 0
            
            # Executa a busca
            for t in termos_busca:
                # --- FIX CRÍTICO: QUERY 'SAFE' PARA NÃO DAR ERRO 400 ---
                # Removemos o @ explícito e usamos "gmail.com" como texto
                query_mine = f'site:instagram.com "{t}" "{cidade_alvo}" (gmail.com OR hotmail.com OR contato)'
                
                status_box.write(f"🔎 Varrendo: {t} em {cidade_alvo}...")
                
                # USA A FUNÇÃO SERPER EXISTENTE
                results = search_google_serper(query_mine, period="", num_results=50) # Pede 50 resultados de uma vez
                
                if not results:
                    status_box.warning(f"Sem resultados para {t} (ou erro na API).")
                    continue

                for res in results:
                    # Extrai email da descrição ou titulo
                    snippet_text = res.get('snippet', '')
                    title_text = res.get('title', '')
                    
                    email = extrair_email(snippet_text)
                    if not email: email = extrair_email(title_text)
                    
                    if email:
                        # Evita duplicatas na lista atual
                        if not any(l['email'] == email for l in leads_encontrados):
                            nome = limpar_nome_insta(title_text)
                            leads_encontrados.append({
                                "nome": nome,
                                "email": email,
                                "empresa": f"{t} - {cidade_alvo}",
                                "categoria": "Buffet/Assessoria" if "Buffet" in t or "Assessoria" in t else "Outros",
                                "origem": "Instagram Miner",
                                "url": res.get('link')
                            })
                            total_varredura += 1
                            
                status_box.write(f"✅ Leads coletados neste lote: {total_varredura}")
                # Pequeno delay apenas por segurança
                time.sleep(0.5)
            
            status_box.update(label=f"Mineração Concluída! {len(leads_encontrados)} leads novos.", state="complete")
            
            if leads_encontrados:
                df_mine = pd.DataFrame(leads_encontrados)
                st.markdown("### 📋 Resultados Encontrados")
                st.dataframe(df_mine, use_container_width=True)
                
                # BOTÃO EXCEL
                st.download_button(
                    label="📥 BAIXAR LISTA DE LEADS (EXCEL)",
                    data=to_excel(df_mine),
                    file_name=f"leads_{cidade_alvo}_{termo_final}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_mine"
                )
                st.success("👉 Baixe o Excel e importe na aba 'Modo Sniper' do seu CRM!")
            else:
                st.warning("Nenhum e-mail público encontrado. Tente mudar a cidade ou o termo.")