import streamlit as st
import requests
import os
import json
import time
import concurrent.futures
import pandas as pd
import re
import random
import datetime
from io import BytesIO
from groq import Groq
import urllib3
import functools

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="LEANTTRO | Buscador de Oportunidades", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;700&display=swap');
    
    header {
        visibility: hidden;
        height: 0px;
    }
    div[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Kanit', sans-serif; }
    
    section[data-testid="stSidebar"] {
        background-color: #111111 !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    .stCode pre, .stCode code {
        background-color: #1a1a1a !important;
        color: #7742df !important;
        border: 1px solid #333 !important;
    }

    .stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    
    .custom-info-box {
        background-color: #1a1a1a;
        border-left: 4px solid #7742df;
        padding: 15px;
        color: #ffffff !important;
        font-size: 14px;
        margin-bottom: 20px;
        border-radius: 4px;
        border: 1px solid #333;
        line-height: 1.5;
    }

    div.stButton > button { 
        background-color: #7742df; color: #ffffff; border: none; 
        border-radius: 4px; font-weight: 600; width: 100%; 
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { 
        background-color: #ffffff; color: #7742df;
        box-shadow: 0 0 15px rgba(119, 66, 223, 0.3);
    }
    
    .stTextInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stNumberInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stSelectbox > div > div { background-color: #111; color: white; border: 1px solid #333; }
    .stTextArea > div > div > textarea { color: #fff; background-color: #111; border: 1px solid #333; }

    .lead-card {
        background-color: #0a0a0a !important; padding: 25px; border-radius: 8px;
        border: 1px solid #222; margin-bottom: 20px;
        position: relative; overflow: hidden;
    }
    .lead-card:hover { border-color: #7742df; }
    
    .score-hot { border-left: 4px solid #7742df; } 
    .score-warm { border-left: 4px solid #555; }    
    .score-cold { border-left: 4px solid #333; }    

    .lead-title { font-family: 'Kanit', sans-serif; font-size: 20px; font-weight: bold; color: #fff; margin-bottom: 5px; text-decoration: none; display: block; }
    .lead-title:hover { color: #7742df; }
    
    .tag-nicho { 
        background-color: #1a1a1a; color: #bbb; padding: 2px 8px; 
        border-radius: 4px; font-size: 10px; font-family: monospace;
        border: 1px solid #333; margin-right: 5px;
    }

    .recommendation-box {
        background-color: #111; border: 1px dashed #333; 
        padding: 10px; margin-top: 15px; border-radius: 4px;
    }
    .rec-title { color: #7742df; font-weight: bold; font-size: 12px; font-family: monospace; }
    .rec-text { font-size: 13px; color: #ddd; margin-top: 4px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border: 1px solid #333; color: #888; border-radius: 4px; }
    .stTabs [aria-selected="true"] { background-color: #7742df !important; color: #ffffff !important; font-weight: bold; border-color: #7742df; }

    h1, h2, h3 { font-family: 'Kanit', sans-serif; font-weight: 600; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
TRACKING_FILE = "leanttro_tracking.json"

def get_tracking_data():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r') as f:
            return json.load(f)
    else:
        data = {
            "start_date": str(datetime.date.today()),
            "last_run_date": str(datetime.date.today()),
            "sent_today": 0,
            "last_run_hour": str(datetime.datetime.now().strftime("%Y-%m-%d %H")),
            "sent_this_hour": 0
        }
        with open(TRACKING_FILE, 'w') as f:
            json.dump(data, f)
        return data

def save_tracking_data(data):
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f)

def get_daily_limit(start_date_str):
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    today = datetime.date.today()
    days_passed = (today - start_date).days
    weeks_passed = days_passed // 7
    limit = 30 + (weeks_passed * 10)
    return min(limit, 120)

if "mensagem_padrao" not in st.session_state:
    st.session_state.mensagem_padrao = "Opa {primeiro_nome}, tudo bem? Vi que vocês atendem no {bairro}. Tentei achar o site de vcs no Google e não consegui, tá fora do ar?"

if "system_prompt_padrao" not in st.session_state:
    st.session_state.system_prompt_padrao = """
    ATUE COMO: Head de Vendas da Leanttro Digital.
    
    OBJETIVO: Encontrar quem está COMPRANDO ou BUSCANDO serviços, ignore quem está vendendo.
    
    PRODUTOS: Catálogo online, Site simples, Automação de WhatsApp, IA para negócios, Identidade visual.
    
    TAREFAS:
    1. Identifique se o autor ESTÁ BUSCANDO o serviço (Score 80 a 100).
    2. Se for alguém VENDENDO ou agência concorrente, Score é ZERO.
    3. Identifique o NOME e o TIPO DE OPORTUNIDADE.
    
    SAÍDA JSON OBRIGATÓRIA:
    {
        "autor": "Nome de quem busca",
        "score": (0-100),
        "resumo_post": "Resumo do que a pessoa precisa",
        "produto_recomendado": "Serviço exato",
        "argumento_venda": "Como abordar para vender rápido"
    }
    """

if "saudacoes" not in st.session_state:
    st.session_state.saudacoes = ["Opa", "Olá", "Tudo bem", "Oi", "Fala"]

if "delay_min" not in st.session_state:
    st.session_state.delay_min = 300

if "delay_max" not in st.session_state:
    st.session_state.delay_max = 400

if "blacklist" not in st.session_state:
    st.session_state.blacklist = set()

SUGESTOES_STRATEGICAS = {
    "Sites de Freelance (Workana/99)": [
        "procuro desenvolvedor site", 
        "preciso de automação whatsapp", 
        "criar catálogo online", 
        "busco especialista em IA", 
        "fazer landing page urgente" 
    ],
    "LinkedIn (Postagens/Feed)": [
        "alguém recomenda empresa para site",
        "busco profissional automação",
        "indicação criador de catálogo", 
        "preciso integrar IA no meu negócio",
        "busco agência para landing page"
    ],
    "Grupos Facebook / Web": [
        "preciso de um site", 
        "alguém faz catálogo digital", 
        "procuro quem faça automação",
        "indicação de desenvolvedor web", 
        "orçamento para site" 
    ]
}

FONTES_MINERADOR = {
    "Instagram": "site:instagram.com",
    "Facebook": "site:facebook.com",
    "LinkedIn": "site:linkedin.com/company",
    "Geral (Maps/Web)": ""
}

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    return output.getvalue()

def extrair_email(texto):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(texto))
    return match.group(0) if match else None

def extrair_whatsapp(texto):
    padrao = r'(?:(?:\+|00)?55\s?)?(?:\(?([1-9][0-9])\)?\s?)?(?:((?:9\d|[2-9])\d{3})\-?(\d{4}))'
    match = re.search(padrao, str(texto))
    
    if match:
        ddd, parte1, parte2 = match.groups()
        if not ddd: ddd = "11" 
        
        numero_limpo = f"55{ddd}{parte1}{parte2}".replace(" ", "").replace("-", "")
        return numero_limpo
    return None

def limpar_nome(titulo):
    if "•" in titulo: return titulo.split("•")[0].strip()
    if "-" in titulo: return titulo.split("-")[0].strip()
    if "|" in titulo: return titulo.split("|")[0].strip()
    return titulo[:50]

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
        if response.status_code != 200:
            return []
        return response.json().get("organic", [])
    except:
        return []

def analyze_lead_groq(title, snippet, link, groq_key, system_prompt):
    if not groq_key: 
        return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    
    client = Groq(api_key=groq_key)
    
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
    except:
        return {"score": 0, "autor": "Erro", "produto_recomendado": "Erro IA", "argumento_venda": "Falha na análise"}

def process_single_item(item, system_prompt):
    titulo = item.get('title', '')
    link = item.get('link', '')
    snippet = item.get('snippet', '')
    data_pub = item.get('date', 'Data n/d')
    
    analise = analyze_lead_groq(titulo, snippet, link, GROQ_API_KEY, system_prompt)
    
    return {
        "item": item,
        "analise": analise,
        "titulo": titulo,
        "link": link,
        "snippet": snippet,
        "data_pub": data_pub
    }

with st.sidebar:
    st.markdown(f"<h1 style='color: #fff; text-align: center; font-weight: 600;'>LEAN<span style='color:#7742df'>TTRO</span>.<br><span style='font-size:14px; color:#fff'>Intelligence Hub</span></h1>", unsafe_allow_html=True)
    st.divider()
    
    if GROQ_API_KEY: st.success("🟢 IA Conectada") 
    else: st.error("🔴 Falta GROQ KEY")
    
    if SERPER_API_KEY: st.success("🟢 Google Search Ativo")
    else: st.error("🔴 Falta SERPER KEY")

    st.divider()
    tracking_info = get_tracking_data()
    limite_atual = get_daily_limit(tracking_info["start_date"])
    st.markdown("### 🎯 Sistema Antiban")
    st.markdown(f"Limite de hoje: {limite_atual} mensagens.")
    st.markdown("Envios a cada 6 minutos (Máx 10/hora).")

tab1, tab2, tab3 = st.tabs(["📡 RADAR DE OPORTUNIDADES (COMPRADORES)", "⛏️ MINERADOR ISOLADO (DADOS)", "⚙️ CONTROLE E SEGURANÇA"])

with tab1:
    st.markdown("<h2 style='color:white'>RADAR DE <span style='color:#7742df'>OPORTUNIDADES REAIS</span></h2>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])

    with c1:
        origem = st.selectbox("Onde buscar?", list(SUGESTOES_STRATEGICAS.keys()))

    with st.sidebar:
        st.markdown("### 💡 Buscas de Intenção")
        dicas_atuais = SUGESTOES_STRATEGICAS.get(origem, [])
        for dica in dicas_atuais:
            st.code(dica, language="text")

    with c2:
        termo = st.text_input("Intenção de busca:", placeholder="Ex: preciso de site")
    with c3:
        tempo = st.selectbox("Período:", ["Últimas 24 Horas", "Última Semana", "Último Mês", "Qualquer data"])
    with c4:
        qtd = st.number_input("Qtd", 1, 50, 10)

    st.write("##")
    btn = st.button("RASTREAR COMPRADORES", key="btn_radar")

    if btn and termo:
        if not (GROQ_API_KEY and SERPER_API_KEY):
            st.error("Configure as chaves no Dokploy.")
        else:
            periodo_api = ""
            if "24 Horas" in tempo: periodo_api = "qdr:d"
            elif "Semana" in tempo: periodo_api = "qdr:w"
            elif "Mês" in tempo: periodo_api = "qdr:m"

            query_final = termo
            if origem == "LinkedIn (Postagens/Feed)":
                query_final = f'site:linkedin.com/posts "{termo}"'
            elif origem == "Sites de Freelance (Workana/99)":
                query_final = f'(site:workana.com OR site:99freelas.com.br) "{termo}"'
            elif origem == "Grupos Facebook / Web":
                query_final = f'"{termo}"'

            resultados = search_google_serper(query_final, periodo_api, qtd)
            
            if not resultados:
                st.warning("Nenhum sinal de compra. Tente outro termo.")
            else:
                bar_text = st.empty()
                prog = st.progress(0)
                processed_results = []
                data_export = [] 
                
                bar_text.text("IA filtrando apenas quem quer comprar...")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_item = {executor.submit(process_single_item, item, st.session_state.system_prompt_padrao): item for item in resultados}
                    completed = 0
                    for future in concurrent.futures.as_completed(future_to_item):
                        try:
                            data = future.result()
                            processed_results.append(data)
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
                        except:
                            pass
                        completed += 1
                        prog.progress(completed / len(resultados))

                bar_text.empty() 
                processed_results.sort(key=lambda x: x['analise'].get('score', 0), reverse=True)
                
                if data_export:
                    df_radar = pd.DataFrame(data_export)
                    st.download_button(label="📥 BAIXAR RELATÓRIO DO RADAR", data=to_excel(df_radar), file_name="radar_leanttro.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                for p in processed_results:
                    analise = p['analise']
                    score = analise.get('score', 0)
                    if score < 50:
                        continue

                    autor = analise.get('autor', 'Desconhecido')
                    link = p['link']
                    titulo = p['titulo']
                    snippet = p['snippet']
                    data_pub = p['data_pub']

                    css_class = "score-hot" if score >= 80 else "score-warm"
                    icon = "🔥 HOT" if score >= 80 else "⚠️ MORNO"

                    card_html = f"""
                    <div class="lead-card {css_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color: #7742df; font-weight:bold; font-family:monospace;">{icon} SCORE: {score}</span>
                            <span class="tag-nicho">Autor: {autor}</span>
                        </div>
                        <a href="{link}" target="_blank" style="background:#222; color:#fff; padding:5px 10px; text-decoration:none; border-radius:4px; font-size:12px;">VER POST 🔗</a>
                    </div>
                    <div style="margin-top:10px;"><a href="{link}" target="_blank" class="lead-title">{titulo}</a></div>
                    <div style="color:#666; font-size:11px; margin-bottom:5px;">🕒 {data_pub} | {snippet[:200]}...</div>
                    <div class="recommendation-box">
                        <div class="rec-title">// ESTRATÉGIA:</div>
                        <div style="color: #fff; font-weight:bold;">OFERTAR: {analise.get('produto_recomendado', 'N/A').upper()}</div>
                        <div class="rec-text"><span style="color:#666">RESUMO:</span> {analise.get('resumo_post', '')}</div>
                        <div class="rec-text" style="color:#7742df; margin-top:5px;">💡 " {analise.get('argumento_venda', '')} "</div>
                    </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

with tab2:
    st.markdown("<h2 style='color:white'>MINERADOR <span style='color:#7742df'>ISOLADO DE DADOS</span></h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        nicho = st.text_input("Nicho:", value="Clínica Odontológica")
    with c2:
        cidade = st.text_input("Cidade Base:", value="São Paulo")
    with c3:
        fonte_alvo = st.selectbox("Fonte Específica:", list(FONTES_MINERADOR.keys()))

    bairros_txt = st.text_area("Lista de Bairros (Separados por vírgula):", value="Centro, Pinheiros, Itaim Bibi", height=80)
    
    if "leads_isolados" not in st.session_state:
        st.session_state["leads_isolados"] = []

    c_btn1, c_btn2 = st.columns([1, 1])

    with c_btn1:
        if st.button("🚀 INICIAR EXTRAÇÃO", key="btn_zap_mine"):
            lista_bairros = [b.strip() for b in bairros_txt.split(',') if b.strip()]
            novos_leads = []
            
            progress_text = st.empty()
            bar = st.progress(0)
            
            prefixo_fonte = FONTES_MINERADOR[fonte_alvo]

            for i, bairro in enumerate(lista_bairros):
                progress_text.text(f"Escaneando {bairro.upper()} no {fonte_alvo}...")
                
                query_base = f'{prefixo_fonte} "{nicho}" "{bairro}" "{cidade}"'
                queries = [
                    f'{query_base} "whatsapp"',
                    f'{query_base} "@gmail.com" OR "@hotmail.com"'
                ]
                
                for q in queries:
                    resultados = search_google_serper(q.strip(), period="", num_results=20)
                    for r in resultados:
                        texto_completo = (r.get('title', '') + " " + r.get('snippet', '')).lower()
                        zap = extrair_whatsapp(texto_completo)
                        email = extrair_email(texto_completo)
                        
                        if zap or email:
                            id_unico = zap if zap else email
                            exists_global = any((l['Whatsapp'] == zap and zap) or (l['Email'] == email and email) for l in st.session_state["leads_isolados"])
                            exists_local = any((l['Whatsapp'] == zap and zap) or (l['Email'] == email and email) for l in novos_leads)
                            
                            if not exists_global and not exists_local:
                                novos_leads.append({
                                    "Empresa": limpar_nome(r.get('title', '')),
                                    "Nicho": nicho,
                                    "Bairro": bairro,
                                    "Whatsapp": zap if zap else "",
                                    "Email": email if email else "",
                                    "Fonte": fonte_alvo,
                                    "Link": r.get('link')
                                })
                
                bar.progress((i + 1) / len(lista_bairros))
                time.sleep(0.5) 
                
            progress_text.text("Extração finalizada.")
            if novos_leads:
                st.session_state["leads_isolados"].extend(novos_leads)
                st.success(f"{len(novos_leads)} CONTATOS ENCONTRADOS!")
            else:
                st.warning("Nada encontrado. Mude o nicho ou a fonte.")

    if st.session_state["leads_isolados"]:
        df = pd.DataFrame(st.session_state["leads_isolados"])
        st.write("---")
        st.markdown(f"### 📋 BASE DE DADOS: {len(df)} REGISTROS")
        st.dataframe(df, width='stretch') 
        
        c_down, c_fire = st.columns(2)
        with c_down:
            st.download_button("📥 BAIXAR BASE", data=to_excel(df), file_name="base_minerada.xlsx")

        with c_fire:
            if st.button("🔥 DISPARAR PARA NÚMEROS EXTRAÍDOS"):
                df_zap = df[df['Whatsapp'] != ""]
                if len(df_zap) == 0:
                    st.warning("Nenhum contato com WhatsApp nesta lista.")
                else:
                    sucessos = 0
                    erros = 0
                    duplicates = 0
                    limit_break = False
                    msg_bar = st.progress(0)
                    
                    tracking = get_tracking_data()
                    today_str = str(datetime.date.today())
                    current_hour_str = str(datetime.datetime.now().strftime("%Y-%m-%d %H"))
                    
                    if tracking["last_run_date"] != today_str:
                        tracking["sent_today"] = 0
                        tracking["last_run_date"] = today_str
                        
                    if tracking["last_run_hour"] != current_hour_str:
                        tracking["sent_this_hour"] = 0
                        tracking["last_run_hour"] = current_hour_str
                        
                    daily_limit = get_daily_limit(tracking["start_date"])
                    
                    for idx, row in df_zap.iterrows():
                        msg_bar.progress((idx + 1) / len(df_zap))
                        
                        if tracking["sent_today"] >= daily_limit:
                            st.warning(f"Limite diário de {daily_limit} atingido.")
                            limit_break = True
                            break
                            
                        if tracking["sent_this_hour"] >= 10:
                            st.warning("Limite de 10 por hora atingido. Aguarde a virada de hora.")
                            limit_break = True
                            break
                        
                        numero = row['Whatsapp']
                        if numero in st.session_state.blacklist:
                            duplicates += 1
                            continue
                        
                        try:
                            saudacao_escolhida = random.choice(st.session_state.saudacoes) if st.session_state.saudacoes else "Opa"
                            mensagem_com_saudacao = st.session_state.mensagem_padrao.replace("{saudacao}", saudacao_escolhida)
                            primeiro_nome = row['Empresa'].split(' ')[0]
                            mensagem_fria = mensagem_com_saudacao.format(primeiro_nome=primeiro_nome, bairro=row['Bairro'])
                            
                            payload = {"number": numero, "message": mensagem_fria}
                            res = requests.post("http://213.199.56.207:3001/disparar", json=payload, timeout=20)
                            
                            if res.status_code == 200:
                                sucessos += 1
                                tracking["sent_today"] += 1
                                tracking["sent_this_hour"] += 1
                                st.session_state.blacklist.add(numero)
                                save_tracking_data(tracking)
                            else:
                                erros += 1
                        except:
                            erros += 1
                        
                        delay = random.randint(max(300, st.session_state.delay_min), max(400, st.session_state.delay_max))
                        time.sleep(delay)
                    
                    if limit_break:
                        st.warning(f"Travado pelo limite de segurança. Enviados agora: {sucessos} | Total do dia: {tracking['sent_today']}")
                    else:
                        st.success(f"Finalizado. Enviados agora: {sucessos} | Total do dia: {tracking['sent_today']} | Falhas: {erros} | Duplicados: {duplicates}")

with tab3:
    st.markdown("<h2 style='color:white'>⚙️ CONTROLE E <span style='color:#7742df'>SEGURANÇA</span></h2>", unsafe_allow_html=True)
    
    st.markdown("### ✍️ Mensagem Fria")
    nova_mensagem = st.text_area("Edite a mensagem:", value=st.session_state.mensagem_padrao, height=100)
    if nova_mensagem != st.session_state.mensagem_padrao:
        st.session_state.mensagem_padrao = nova_mensagem
    
    st.divider()
    
    st.markdown("### 🗣️ Variações de Saudação")
    saudacoes_input = st.text_input("Lista separada por vírgula:", value=", ".join(st.session_state.saudacoes))
    if saudacoes_input:
        nova_lista = [s.strip() for s in saudacoes_input.split(",") if s.strip()]
        if nova_lista and nova_lista != st.session_state.saudacoes:
            st.session_state.saudacoes = nova_lista
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⏱️ Delay (Proteção Extrema)")
        min_delay = st.number_input("Mínimo (Travado em 300s / 5min):", min_value=300, max_value=600, value=max(300, st.session_state.delay_min))
        if min_delay != st.session_state.delay_min:
            st.session_state.delay_min = min_delay
    with col2:
        max_delay = st.number_input("Máximo:", min_value=350, max_value=800, value=max(350, st.session_state.delay_max))
        if max_delay != st.session_state.delay_max:
            st.session_state.delay_max = max_delay
    
    st.divider()
    
    st.markdown("### 🔒 Progresso de Envios")
    tracking = get_tracking_data()
    daily_lim = get_daily_limit(tracking["start_date"])
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Limite de hoje", daily_lim)
    with col_b:
        st.metric("Enviados hoje", tracking["sent_today"])
    with col_c:
        st.metric("Enviados nesta hora", f"{tracking['sent_this_hour']} / 10")
    
    if st.button("🔄 Zerar dados (Perigo)"):
        os.remove(TRACKING_FILE)
        st.session_state.blacklist = set()
        st.rerun()