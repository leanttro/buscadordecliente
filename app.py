import streamlit as st
import pandas as pd
import requests
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime, date
import time
import os
import random
import urllib3
import json
import urllib.parse
import re
import concurrent.futures
from io import BytesIO
import base64

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="LEANTTRO CRM", layout="wide", page_icon="⚡")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"

# --- CSS VISUAL (NOVO TEMA: AMIGÁVEL, LIMPO E MODERNO) ---
st.markdown("""
<style>
    /* IMPORTANDO FONTE MODERNA */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* VARIÁVEIS DE COR (TEMA CLARO/SAAS) */
    :root {
        --bg-color: #F8FAFC;
        --surface: #FFFFFF;
        --text-main: #0F172A;
        --text-muted: #64748B;
        --primary: #3B82F6; /* Azul Amigável */
        --primary-hover: #2563EB;
        --border: #E2E8F0;
        --radius: 12px;
    }

    /* GLOBAL */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        color: var(--text-main);
        letter-spacing: -0.02em;
    }

    p, span, label, div {
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }

    /* BOTÕES PRINCIPAIS */
    div.stButton > button {
        background-color: var(--primary) !important;
        color: #FFFFFF !important;
        border: none;
        border-radius: var(--radius);
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
    }
    div.stButton > button:hover {
        background-color: var(--primary-hover) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
    }
    
    /* LINK BUTTON (GMAIL ETC) */
    a[data-testid="stLinkButton"] {
        background-color: var(--surface) !important;
        color: var(--primary) !important;
        border: 2px solid var(--primary) !important;
        border-radius: var(--radius);
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        text-decoration: none;
        display: inline-block;
        text-align: center;
        transition: all 0.2s ease;
    }
    a[data-testid="stLinkButton"]:hover {
        background-color: var(--primary) !important;
        color: #FFFFFF !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
    }

    /* INPUTS */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: var(--surface);
        border-radius: 8px;
        border: 1px solid var(--border);
        transition: all 0.2s ease;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, div[data-baseweb="textarea"]:focus-within {
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
    input, textarea {
        color: var(--text-main) !important;
        -webkit-text-fill-color: var(--text-main) !important;
    }

    /* CARDS/METRICS */
    div[data-testid="stMetric"] {
        background-color: var(--surface);
        border: 1px solid var(--border);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
        border-left: 5px solid var(--primary);
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-muted);
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--text-main);
        font-weight: 800;
        font-size: 2.2rem;
    }

    /* DATAFRAME / TABELA */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
    }
    
    /* ABAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 2px solid var(--border);
        padding-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: var(--text-muted);
        font-weight: 600;
        font-size: 1rem;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }

    /* LOGO HEADER CUSTOM */
    .leanttro-header {
        text-align: center;
        padding: 30px 0;
        margin-bottom: 20px;
        background-color: var(--surface);
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid var(--border);
    }
    .leanttro-title {
        font-size: 2.8rem;
        color: var(--text-main);
        margin: 0;
        font-weight: 800;
        letter-spacing: -1px;
    }
    .primary-text { color: var(--primary); }
    .leanttro-sub {
        color: var(--text-muted);
        font-weight: 500;
        font-size: 0.95rem;
        letter-spacing: 0.05em;
        margin-top: 5px;
        text-transform: uppercase;
    }
    
    /* MULTISELECT TAGS */
    span[data-baseweb="tag"] {
        background-color: #EFF6FF !important;
        color: var(--primary) !important;
        border-radius: 6px;
        border: 1px solid #DBEAFE;
    }
    span[data-baseweb="tag"] span {
        color: var(--primary) !important;
        font-weight: 500;
    }
    span[data-baseweb="tag"] svg {
        fill: var(--primary) !important;
    }
    
    /* EXPANDERS */
    .streamlit-expanderHeader {
        background-color: var(--surface);
        border-radius: 8px;
        font-weight: 600;
        color: var(--text-main);
    }

</style>
""", unsafe_allow_html=True)

# --- VARS & CLIENTE GROQ & TRACKING ---
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 

# [!!!] COLOQUE SUA CHAVE DO WEBHOOK DO DIRECTUS AQUI EMBAIXO:
TRACKING_WEBHOOK_KEY = "0deea9a4-ce23-4aee-bb82-d9422bd8e15f"

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Erro ao inicializar Groq: {e}")

# =========================================================
#  FUNÇÕES AUXILIARES
# =========================================================

def render_header():
    st.markdown("""
    <div class="leanttro-header">
        <h1 class="leanttro-title">LEAN<span class="primary-text">TTRO</span>.</h1>
        <div class="leanttro-sub">CRM & INTELLIGENCE HUB</div>
    </div>
    """, unsafe_allow_html=True)

def get_user_table_name(user_id):
    clean_id = str(user_id).replace("-", "_")
    return f"crm_{clean_id}"

def inicializar_crm_usuario(token, user_id):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Tabela CRM
    r = requests.get(f"{base_url}/collections/{table_name}", headers=headers, verify=False)
    if r.status_code != 200:
        schema = {"collection": table_name, "schema": {}, "meta": {"icon": "rocket", "note": "Leanttro CRM Table"}}
        requests.post(f"{base_url}/collections", json=schema, headers=headers, verify=False)
    
    # Lista de campos padrão
    campos = [
        {"field": "nome", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "person"}},
        {"field": "empresa", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "domain"}},
        {"field": "email", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "email"}},
        {"field": "telefone", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "phone"}},
        {"field": "origem", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "map"}},
        {"field": "url", "type": "string", "meta": {"interface": "input", "width": "full", "icon": "link"}},
        {"field": "status", "type": "string", "meta": {"interface": "select-dropdown", "options": {"choices": [{"text": "NOVO", "value": "Novo"}, {"text": "QUENTE", "value": "Quente"}, {"text": "CLIENTE", "value": "Cliente"}, {"text": "ENVIADO EM MASSA", "value": "ENVIADO EM MASSA"}]}}},
        {"field": "obs", "type": "text", "meta": {"interface": "input-multiline"}}
    ]
    
    for campo in campos:
        try:
            requests.post(f"{base_url}/fields/{table_name}", json=campo, headers=headers, verify=False)
        except:
            pass 

    # 2. Tabela SMTP
    r_smtp = requests.get(f"{base_url}/collections/config_smtp", headers=headers, verify=False)
    if r_smtp.status_code != 200:
        schema_smtp = {"collection": "config_smtp", "schema": {}, "meta": {"icon": "email", "note": "SMTP Users Config"}}
        requests.post(f"{base_url}/collections", json=schema_smtp, headers=headers, verify=False)
        campos_smtp = [
            {"field": "smtp_host", "type": "string"},
            {"field": "smtp_port", "type": "integer"},
            {"field": "smtp_user", "type": "string"},
            {"field": "smtp_pass", "type": "string"}
        ]
        for c in campos_smtp: requests.post(f"{base_url}/fields/config_smtp", json=c, headers=headers, verify=False)
        
    return True, "CRM Initialized"

def criar_coluna_dinamica(token, user_id, nome_campo, tipo_interface):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    slug = nome_campo.lower().strip().replace(" ", "_").replace("ç", "c")
    mapa = {"Texto": "string", "Número": "integer", "Data": "date"}
    type_d = mapa.get(tipo_interface, "string")
    
    payload = {
        "field": slug, "type": type_d,
        "meta": {"interface": "input", "width": "full"},
        "schema": {"is_nullable": True}
    }
    r = requests.post(f"{base_url}/fields/{table_name}", json=payload, headers=headers, verify=False)
    return r.status_code == 200

def carregar_dados(token, user_id):
    try:
        table = get_user_table_name(user_id)
        r = requests.get(f"{DIRECTUS_URL}/items/{table}?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if 'id' in df.columns:
                cols_pri = ['id', 'nome', 'empresa', 'email', 'telefone', 'origem', 'status']
                cols_existentes = [c for c in cols_pri if c in df.columns]
                cols_restantes = [c for c in df.columns if c not in cols_existentes]
                return df[cols_existentes + cols_restantes]
    except: pass
    return pd.DataFrame(columns=["nome", "empresa", "email", "status", "telefone"])

def carregar_dados_bot(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/items/clients_bot?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if not df.empty:
                rename_map = {}
                if 'name' in df.columns: rename_map['name'] = 'nome'
                if 'whatsapp' in df.columns: rename_map['whatsapp'] = 'telefone'
                df.rename(columns=rename_map, inplace=True)
            cols_desejadas = ['id', 'nome', 'email', 'telefone', 'dor_principal', 'session_uuid']
            cols_existentes = [c for c in cols_desejadas if c in df.columns]
            return df[cols_existentes]
    except: pass
    return pd.DataFrame()

def atualizar_item(token, user_id, item_id, dados):
    table = get_user_table_name(user_id)
    requests.patch(f"{DIRECTUS_URL}/items/{table}/{item_id}", json=dados, headers={"Authorization": f"Bearer {token}"}, verify=False)

# --- FUNÇÕES SMTP (PERSISTÊNCIA) ---
def carregar_config_smtp(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        r = requests.get(f"{base_url}/items/config_smtp?filter[user_created][_eq]=$CURRENT_USER&limit=1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            data = r.json()['data']
            if data: return data[0]
    except: pass
    return {}

def salvar_config_smtp(token, dados):
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    existente = carregar_config_smtp(token)
    if existente:
        r = requests.patch(f"{base_url}/items/config_smtp/{existente['id']}", json=dados, headers=headers, verify=False)
    else:
        r = requests.post(f"{base_url}/items/config_smtp", json=dados, headers=headers, verify=False)
    return r.status_code == 200

def contar_envios_hoje(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        url = f"{base_url}/items/historico_envios?filter[data_envio][_gte]={hoje_str}&filter[user_created][_eq]=$CURRENT_USER&aggregate[count]=*"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            data = r.json()['data']
            if isinstance(data, list) and len(data) > 0:
                return int(data[0].get('count', 0))
    except: pass
    return 0

def registrar_log_envio(token, destinatario, assunto, status):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        payload = {
            "data_envio": datetime.now().isoformat(),
            "destinatario": destinatario,
            "assunto": assunto,
            "status": status,
            "aberto": False # Campo útil se existir no directus
        }
        r = requests.post(f"{base_url}/items/historico_envios", json=payload, headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code in [200, 201]:
            return r.json()['data']['id'] # Retorna ID para pixel
    except: pass
    return None

def atualizar_status_envio(token, log_id, novo_status, erro_msg=None):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        payload = {"status": novo_status}
        if erro_msg:
            payload["obs"] = erro_msg
        requests.patch(f"{base_url}/items/historico_envios/{log_id}", json=payload, headers={"Authorization": f"Bearer {token}"}, verify=False)
    except: pass

def enviar_email_smtp(smtp_config, to, subject, body, anexo=None, tracking_url=None):
    try:
        to = str(to).strip()
        subject = str(subject).strip()

        # Converte quebras de linha padrão do texto para HTML
        body = str(body).replace('\n', '<br>')

        # --- INJEÇÃO DO PIXEL (COM CACHE BUSTER) ---
        if tracking_url:
            cache_buster = random.randint(1000, 999999)
            url_final = f"{tracking_url}&r={cache_buster}"
            pixel_html = f'<img src="{url_final}" width="1" height="1" style="display:block; width:1px; height:1px; opacity:0.01;" alt="" />'
            
            if "</body>" in body:
                body = body.replace("</body>", f"{pixel_html}</body>")
            else:
                body += pixel_html

        usar_imagem_inline = False
        if anexo is not None and "{{imagem}}" in body.lower():
            if "image" in anexo.type:
                usar_imagem_inline = True

        if usar_imagem_inline:
            msg = MIMEMultipart('related')
            msg['From'] = smtp_config['user']
            msg['To'] = to
            msg['Subject'] = subject
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            cid_id = "imagem_corpo"
            body_atualizado = body.replace("{{imagem}}", f'<br><img src="cid:{cid_id}" style="max-width:100%; height:auto;"><br>')
            msg_alternative.attach(MIMEText(body_atualizado, 'html', 'utf-8'))

            img_data = anexo.getvalue()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<{cid_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=anexo.name)
            msg.attach(image)
        else:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['user']
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            if anexo is not None:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(anexo.getvalue())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{anexo.name}"')
                msg.attach(part)

        server = smtplib.SMTP(smtp_config['host'], int(smtp_config['port']))
        server.starttls()
        server.login(smtp_config['user'], smtp_config['pass'])
        server.sendmail(smtp_config['user'], to, msg.as_string())
        server.quit()
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_copy_ia(ctx, dados_cliente=None):
    if not groq_client: return "Erro", "Configure a GROQ_API_KEY no ambiente"
    
    empresa = ctx.get('empresa', 'Nossa Empresa')
    descricao = ctx.get('descricao', 'Soluções Digitais')
    segmento_alvo = ctx.get('segmento_alvo', '') 
    
    dor_cliente = ""
    if dados_cliente is not None and 'dor_principal' in dados_cliente:
        d = dados_cliente['dor_principal']
        if d and str(d).lower() != 'none':
            dor_cliente = f"A principal dor/necessidade deste cliente é: {d}. Use isso para personalizar o texto."
    
    instrucao_segmento = ""
    if segmento_alvo:
        instrucao_segmento = f"CONTEXTO IMPORTANTE: O público alvo deste disparo são empresas/pessoas do seguinte perfil/segmento: '{segmento_alvo}'. Adapte a linguagem e exemplos para eles."

    prompt = f"""
    Aja como um copywriter profissional B2B.
    Escreva um email curto (max 3 parágrafos) de prospecção fria.
    Minha Empresa: {empresa}
    O que vendemos: {descricao}
    {instrucao_segmento}
    {dor_cliente}
    Tom: Persuasivo, direto e sem enrolação corporativa.
    Foco: Marcar uma reunião ou resolver o problema dele.
    IMPORTANTE: Não coloque Assunto: no corpo, apenas o texto do email.
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        msg_ia = chat_completion.choices[0].message.content
        return "Proposta Personalizada", msg_ia
    except Exception as e:
        return "Erro IA", str(e)

def gerar_whatsapp_ia(ctx, dados_cliente=None):
    if not groq_client: return "Erro: API Key não configurada"
    
    empresa = ctx.get('empresa', 'Leanttro')
    descricao = ctx.get('descricao', 'Landing Pages')
    
    nome = "Doutor(a)"
    dor = ""
    if dados_cliente is not None:
        nome = dados_cliente.get('nome', 'Doutor(a)')
        if 'dor_principal' in dados_cliente:
            dor = f"Foque na dor: {dados_cliente['dor_principal']}"

    prompt = f"""
    Aja como um especialista em vendas B2B via WhatsApp.
    Escreva uma mensagem MUITO CURTA (máximo 2 frases) e direta para abordagem fria.
    Contexto: {empresa} vende {descricao}.
    Cliente: {nome}.
    {dor}
    OBRIGATÓRIO: A mensagem DEVE incluir o link: www.leanttro.com/zenilda-adv
    Tom: Informal, "vizinho", mas profissional. Sem "cara de robô".
    Objetivo: Apenas despertar interesse para clicar no link e ver o exemplo.
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Erro IA: {str(e)}"

def validar_token(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200: return r.json()['data']
    except: pass
    return None

def get_tracking_data(user_id):
    file_path = get_tracking_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        data = {
            "start_date": str(date.today()),
            "last_run_date": str(date.today()),
            "sent_today": 0,
            "last_run_hour": str(datetime.now().strftime("%Y-%m-%d %H")),
            "sent_this_hour": 0
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return data

def extrair_whatsapp(texto):
    padrao = r'(?:(?:\+|00)?55\s?)?(?:\(?([1-9][0-9])\)?\s?)?(?:((?:9\d|[2-9])\d{3})\-?(\d{4}))'
    match = re.search(padrao, str(texto))
    if match:
        ddd, parte1, parte2 = match.groups()
        if not ddd: ddd = "11" 
        return f"55{ddd}{parte1}{parte2}".replace(" ", "").replace("-", "")
    return None

# =========================================================
#  INTERFACE
# =========================================================

# --- 1. PERSISTÊNCIA DE SESSÃO ---
if 'token' not in st.session_state:
    token_url = st.query_params.get("token")
    if token_url:
        user_data = validar_token(token_url)
        if user_data:
            st.session_state['token'] = token_url
            st.session_state['user'] = user_data

# --- TELA DE LOGIN ---
if 'token' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        render_header()
        st.markdown("<p style='text-align:center; color:var(--text-muted)'>Acesso Restrito</p>", unsafe_allow_html=True)
        email = st.text_input("E-MAIL")
        senha = st.text_input("SENHA", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            login_sucesso = False
            try:
                r = requests.post(f"{DIRECTUS_URL}/auth/login", json={"email": email, "password": senha}, verify=False)
                if r.status_code == 200:
                    token = r.json()['data']['access_token']
                    st.session_state['token'] = token
                    u = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
                    st.session_state['user'] = u.json()['data']
                    st.query_params["token"] = token
                    login_sucesso = True
                else:
                    st.error("ACESSO NEGADO")
            except: st.error("ERRO DE CONEXÃO")
            
            if login_sucesso:
                st.rerun()
    st.stop()

token = st.session_state['token']
user = st.session_state['user']
user_id = user['id']

st.query_params["token"] = token

if 'setup_ok' not in st.session_state:
    inicializar_crm_usuario(token, user_id)
    st.session_state['setup_ok'] = True

if 'smtp_loaded' not in st.session_state:
    cfg = carregar_config_smtp(token)
    if cfg:
        st.session_state['smtp'] = {
            'host': cfg.get('smtp_host', 'smtp.gmail.com'),
            'port': cfg.get('smtp_port', 587),
            'user': cfg.get('smtp_user', ''),
            'pass': cfg.get('smtp_pass', '')
        }
        st.session_state['smtp_host_input'] = cfg.get('smtp_host', 'smtp.gmail.com')
        st.session_state['smtp_port_input'] = int(cfg.get('smtp_port', 587))
        st.session_state['smtp_user_input'] = cfg.get('smtp_user', '')
        st.session_state['smtp_pass_input'] = cfg.get('smtp_pass', '')
    st.session_state['smtp_loaded'] = True

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h3 style='color:var(--primary)'>👋 Olá, {user.get('first_name')}</h3>", unsafe_allow_html=True)
    
    if st.button("LOGOUT / SAIR", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    
    st.divider()
    
    with st.expander("🛠️ CONSTRUTOR DE TABELA"):
        nc = st.text_input("NOME COLUNA")
        tc = st.selectbox("TIPO", ["Texto", "Número", "Data"])
        if st.button("CRIAR COLUNA"):
            if criar_coluna_dinamica(token, user_id, nc, tc):
                st.success("CRIADO!")
                time.sleep(1)
                st.rerun()

    with st.expander("🤖 DADOS DA EMPRESA (IA)", expanded=True):
        en = st.text_input("NOME EMPRESA", value="Leanttro (Especialista em Jurídico)")
        ed = st.text_area("O QUE VENDE?", value="Landing Pages de Alta Conversão para Advogados. Produto foco: www.leanttro.com/zenilda-adv. Ajuda a passar autoridade e captar clientes qualificados.")
        if st.button("SALVAR CONTEXTO"):
            st.session_state['ctx'] = {'empresa': en, 'descricao': ed}
            st.success("SALVO")

    with st.expander("📧 SMTP CONFIG", expanded=True):
        h = st.text_input("HOST", key="smtp_host_input")
        p = st.number_input("PORT", key="smtp_port_input")
        u = st.text_input("USER", key="smtp_user_input")
        pw = st.text_input("PASS", type="password", key="smtp_pass_input")
        
        if st.button("SALVAR E CONECTAR"):
            st.session_state['smtp'] = {'host': h, 'port': p, 'user': u, 'pass': pw}
            salvar_config_smtp(token, {'smtp_host': h, 'smtp_port': p, 'smtp_user': u, 'smtp_pass': pw})
            st.toast("Configurações salvas e conectadas!", icon="✅")
            time.sleep(1)

# --- MAIN ---
render_header()
df = carregar_dados(token, user_id)
df_bot = carregar_dados_bot(token)

# --- METRICS & COTA ---
COTA_MAXIMA = 100
envios_realizados = contar_envios_hoje(token)
saldo_envios = COTA_MAXIMA - envios_realizados

k1, k2, k3 = st.columns(3)
k1.metric("TOTAL LEADS (CRM)", len(df))
k2.metric("LEADS BOT", len(df_bot))
k3.metric("SALDO DISPARO", saldo_envios)

if saldo_envios <= 0:
    st.error("⛔ COTA DE ENVIO DIÁRIA ATINGIDA. VOLTE AMANHÃ.")

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["/// BASE DE LEADS & AÇÕES", "/// MODO SNIPER (DISPARO)"])

# --- ABA 1: BASE + WHATSAPP ---
with tab1:
    # 1. ÁREA DE FILTROS & COLUNAS
    with st.expander("🔎 FILTRAR & PERSONALIZAR TABELA", expanded=True):
        f_c1, f_c2 = st.columns([1, 1])
        
        with f_c1:
            st.markdown("##### 👁️ COLUNAS VISÍVEIS (ARRASTE PARA ORDENAR)")
            all_cols = list(df.columns)
            
            if 'cols_visiveis_save' not in st.session_state:
                st.session_state['cols_visiveis_save'] = all_cols
                
            cols_visiveis = st.multiselect("Escolha e ordene as colunas:", all_cols, default=st.session_state['cols_visiveis_save'])
            
            if cols_visiveis != st.session_state['cols_visiveis_save']:
                st.session_state['cols_visiveis_save'] = cols_visiveis
                st.rerun()
        
        with f_c2:
            st.markdown("##### 🌪️ FILTRAR DADOS")
            col_para_filtrar = st.selectbox("Filtrar na coluna:", ["(Sem Filtro)"] + all_cols)
            
            filtro_valores = []
            if col_para_filtrar != "(Sem Filtro)":
                valores_unicos = df[col_para_filtrar].unique().tolist()
                valores_unicos = [str(x) for x in valores_unicos] 
                filtro_valores = st.multiselect(f"Selecione valores de '{col_para_filtrar}':", valores_unicos)

    # Aplica o filtro visualmente
    df_visual = df.copy()
    
    if col_para_filtrar != "(Sem Filtro)" and filtro_valores:
        df_visual = df_visual[df_visual[col_para_filtrar].astype(str).isin(filtro_valores)]

    if cols_visiveis:
        cols_final = [c for c in cols_visiveis]
        if 'id' not in cols_final and 'id' in df_visual.columns:
            cols_final.append('id')
        df_visual = df_visual[cols_final]

    # 2. ÁREA DA TABELA (FULL WIDTH)
    sub_t1, sub_t2 = st.tabs(["📋 TABELA MESTRE", "🤖 TABELA BOT"])
    
    with sub_t1:
        st.caption("💡 **Dica:** Clique no título de qualquer coluna (ex: 'nome' ou 'status') para mudar a ordem dos contatos (A-Z, etc).")
        
        # Oculta a coluna ID
        col_config = {'id': None}

        edited = st.data_editor(
            df_visual, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="editor",
            column_config=col_config,
            hide_index=True # Oculta a numeração lateral (índice do pandas) para ficar limpo
        )
        
        if st.button("💾 SALVAR ALTERAÇÕES NA BASE"):
            chg = st.session_state["editor"]
            
            # 1. PROCESSAR EXCLUSÕES
            deleted_indices = chg.get("deleted_rows", [])
            for idx in deleted_indices:
                try:
                    if not df_visual.empty and idx < len(df_visual):
                        item_id_del = df_visual.iloc[idx]['id']
                        requests.delete(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}/{item_id_del}", headers={"Authorization": f"Bearer {token}"}, verify=False)
                except Exception as e:
                    st.error(f"Erro ao excluir linha: {e}")

            # 2. PROCESSAR EDIÇÕES
            for idx, row in chg["edited_rows"].items():
                try:
                    if int(idx) < len(df_visual):
                        item_id = df_visual.iloc[int(idx)]['id']
                        atualizar_item(token, user_id, item_id, row)
                except: pass
            
            # 3. PROCESSAR ADIÇÕES
            max_id = 0
            df_fresh = carregar_dados(token, user_id)
            if not df_fresh.empty and 'id' in df_fresh.columns:
                try:
                    max_id = pd.to_numeric(df_fresh['id'], errors='coerce').max()
                    if pd.isna(max_id): max_id = 0
                except: max_id = 0
            
            proximo_id = int(max_id) + 1

            for row in chg["added_rows"]:
                if 'id' not in row or not row['id']:
                    row['id'] = proximo_id
                    proximo_id += 1
                requests.post(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}", json=row, headers={"Authorization": f"Bearer {token}"}, verify=False)
            
            # 4. REORGANIZAR
            if deleted_indices:
                try:
                    df_reorg = carregar_dados(token, user_id)
                    if not df_reorg.empty and 'id' in df_reorg.columns:
                        df_reorg['id'] = pd.to_numeric(df_reorg['id'], errors='coerce')
                        df_reorg = df_reorg.sort_values(by='id')
                        novo_contador = 1
                        table_n = get_user_table_name(user_id)
                        headers_api = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                        for i, r_row in df_reorg.iterrows():
                            id_atual = int(r_row['id'])
                            if id_atual != novo_contador:
                                requests.patch(f"{DIRECTUS_URL}/items/{table_n}/{id_atual}", json={"id": novo_contador}, headers=headers_api, verify=False)
                            novo_contador += 1
                except: pass

            st.toast("Dados atualizados e salvos!", icon="✅")
            time.sleep(1)
            st.rerun()
    
    with sub_t2:
        st.markdown("### DADOS CAPTURADOS (READ-ONLY)")
        st.dataframe(df_bot, use_container_width=True, height=400, hide_index=True)

    st.divider()

    # 3. ÁREA DE AÇÕES
    st.markdown("### ⚡ AÇÕES RÁPIDAS (LINHA ÚNICA)")
    
    col_fonte, col_cli, col_vazio = st.columns([1, 2, 3])
    with col_fonte:
        fonte = st.radio("Fonte de Dados:", ["Base Mestre", "Bot Automático"], horizontal=True)
    
    df_ativo = df if fonte == "Base Mestre" else df_bot
    col_nome = 'nome' 
    
    with col_cli:
        nomes = []
        if not df_ativo.empty and col_nome in df_ativo.columns:
            nomes = df_ativo[col_nome].tolist()
        sel_cli = st.selectbox("Selecione o Cliente para Agir:", ["Selecione..."] + nomes)

    if sel_cli != "Selecione..." and not df_ativo.empty:
        dados_cli = df_ativo[df_ativo[col_nome] == sel_cli].iloc[0]
        
        nome_cliente = dados_cli.get(col_nome, '')
        email_cliente = dados_cli.get('email', '')
        tel = str(dados_cli.get('telefone', '')).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if tel == 'nan' or tel == 'None': tel = ""
        
        if 'dor_principal' in dados_cli:
            st.info(f"💡 Dor Identificada: {dados_cli['dor_principal']}")

        act_c1, act_c2 = st.columns(2)
        
        with act_c1:
            st.markdown("#### 💬 WHATSAPP")
            
            if st.session_state.get('last_selected_client') != sel_cli:
                st.session_state['last_selected_client'] = sel_cli
                st.session_state['ai_zap_text'] = None 
                
            default_template = f"Olá Dr(a). {nome_cliente}, tudo bem? Sou vizinho aqui da região do Jabaquara, vi seu perfil e notei uma oportunidade..."
            
            if st.button("✨ GERAR TEXTO ZAP (IA)"):
                gen_text = gerar_whatsapp_ia(st.session_state.get('ctx', {}), dados_cli)
                st.session_state['ai_zap_text'] = gen_text
                st.rerun()
                
            text_to_show = st.session_state.get('ai_zap_text') if st.session_state.get('ai_zap_text') else default_template
            msg_zap = st.text_area("Mensagem:", value=text_to_show, height=100)
            
            raw_tel = str(dados_cli.get('telefone', ''))
            nums = re.sub(r'\D', '', raw_tel) 

            tel_final = ""
            if nums:
                if nums.startswith('55') and len(nums) > 11:
                    tel_final = nums
                else:
                    tel_final = f"55{nums}"

            if tel_final:
                msg_encoded = urllib.parse.quote(msg_zap)
                link_zap = f"https://api.whatsapp.com/send?phone={tel_final}&text={msg_encoded}"
                st.link_button("ENVIAR WHATSAPP", link_zap, use_container_width=True)
            else:
                st.warning("Telefone inválido para envio.")

        with act_c2:
            st.markdown("#### 📧 GMAIL (IA)")
            st.caption("Gera um draft e abre no seu Gmail.")
            if st.button("GERAR TEXTO COM IA"):
                assunto_ia, corpo_ia = gerar_copy_ia(st.session_state.get('ctx', {}), dados_cli)
                corpo_final = corpo_ia.replace("{nome}", nome_cliente)
                
                assunto_safe = urllib.parse.quote(assunto_ia)
                corpo_safe = urllib.parse.quote(corpo_final)
                link_gmail = f"https://mail.google.com/mail/?view=cm&fs=1&to={email_cliente}&su={assunto_safe}&body={corpo_safe}"
                
                st.markdown(f"**Assunto:** {assunto_ia}")
                st.link_button("ABRIR NO GMAIL", link_gmail, use_container_width=True)

# --- ABA 2: MODO SNIPER (INTERNO E EXTERNO) ---
with tab2:
    if saldo_envios <= 0:
        st.warning("BLOQUEADO: COTA ATINGIDA")
        st.stop()

    subtab_int, subtab_ext = st.tabs(["[ 1 ] DISPARO INTERNO", "[ 2 ] IMPORTAR EXCEL"])

    with subtab_int:
        lista_mestre = pd.DataFrame()
        lista_bot_u = pd.DataFrame()

        if not df.empty and 'email' in df.columns:
            lista_mestre = df.copy()
            lista_mestre['origem'] = 'Mestre'
        
        if not df_bot.empty and 'email' in df_bot.columns:
            lista_bot_u = df_bot.copy()
            lista_bot_u['origem'] = 'Bot'

        df_unificado = pd.concat([lista_mestre, lista_bot_u], ignore_index=True)
        if not df_unificado.empty and 'email' in df_unificado.columns:
             df_unificado = df_unificado[df_unificado['email'].astype(str).str.contains("@", na=False)]
        
        with st.expander("🎯 FILTRAGEM INTELIGENTE (SEGMENTAÇÃO)", expanded=True):
            f_s1, f_s2, f_s3 = st.columns([1, 2, 1])
            with f_s1:
                col_sniper = st.selectbox("Filtrar por:", ["(Todos)"] + list(df_unificado.columns), key="col_sniper")
            with f_s2:
                vals_sniper = []
                if col_sniper != "(Todos)":
                    unique_vals = [str(x) for x in df_unificado[col_sniper].unique()]
                    vals_sniper = st.multiselect(f"Valores em '{col_sniper}':", unique_vals, key="vals_sniper")
            with f_s3:
                ocultar_enviados = st.checkbox("Ocultar Status 'ENVIADO EM MASSA'?", value=True)
        
        if col_sniper != "(Todos)" and vals_sniper:
            df_unificado = df_unificado[df_unificado[col_sniper].astype(str).isin(vals_sniper)]

        if ocultar_enviados and 'status' in df_unificado.columns:
             df_unificado = df_unificado[df_unificado['status'] != "ENVIADO EM MASSA"]

        if not df_unificado.empty:
            if 'nome' in df_unificado.columns:
                df_unificado['label'] = df_unificado['nome'] + " (" + df_unificado['origem'] + ")"
            else:
                df_unificado['label'] = df_unificado['email']

        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("### SELEÇÃO (FILTRADA)")
            opcoes = df_unificado['label'].tolist() if not df_unificado.empty else []
            
            if 'status' in df_unificado.columns:
                df_unificado.sort_values(by='status', key=lambda x: x == 'ENVIADO EM MASSA', inplace=True)
                opcoes = df_unificado['label'].tolist()

            sels = st.multiselect("ALVOS", opcoes)
            
            col_lote, col_info = st.columns([1,1])
            with col_lote:
                modo_lote = st.checkbox("⚡ Enviar Lote de 10?", value=False)
            
            alvos_finais = sels
            if modo_lote:
                alvos_finais = sels[:10]
            
            if len(alvos_finais) > 0:
                st.info(f"{len(alvos_finais)} alvos prontos para envio.")
                if modo_lote and len(sels) > 10:
                    st.caption(f"Faltarão {len(sels)-10} leads para o próximo lote.")
            
        with c2:
            st.markdown("### MENSAGEM")
            assunto = st.text_input("ASSUNTO", key="ass_int")
            st.caption("Dica: Use {{imagem}} no texto para inserir a imagem no corpo do email.")
            corpo = st.text_area("CORPO HTML (Use {nome})", height=150, key="body_int")
            file_anexo = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_int")
            
            if st.button("✨ GERAR COM IA (GROQ)"):
                ctx_temp = st.session_state.get('ctx', {}).copy()
                if col_sniper != "(Todos)" and vals_sniper:
                    ctx_temp['segmento_alvo'] = f"{', '.join(vals_sniper)} ({col_sniper})"
                
                sug_a, sug_c = gerar_copy_ia(ctx_temp)
                st.info(f"Assunto: {sug_a}")
                st.code(sug_c)

        if st.button("🚀 DISPARAR NA BASE"):
            if not st.session_state.get('smtp'):
                st.error("CONFIGURE O SMTP NA SIDEBAR")
            elif len(alvos_finais) > saldo_envios:
                st.error(f"SELEÇÃO ({len(alvos_finais)}) MAIOR QUE SALDO ({saldo_envios})")
            else:
                bar = st.progress(0)
                log = st.empty()
                for i, label_sel in enumerate(alvos_finais):
                    if i > 0:
                        wait = random.randint(5, 15) 
                        log.warning(f"⏳ RECARREGANDO... {wait}s")
                        time.sleep(wait)
                    
                    tgt_rows = df_unificado[df_unificado['label'] == label_sel]
                    if tgt_rows.empty: continue
                    tgt = tgt_rows.iloc[0]
                    
                    nome_real = tgt.get('nome', 'Parceiro')
                    email_real = str(tgt['email']).strip()
                    item_id_real = tgt.get('id')
                    
                    if not email_real or email_real.lower() == 'nan':
                        log.warning(f"E-mail inválido para {nome_real}")
                        continue
                    
                    log_id = registrar_log_envio(token, email_real, assunto, "Enviando...")
                    
                    tracking_url = None
                    if log_id and TRACKING_WEBHOOK_KEY != "SUA_CHAVE_AQUI":
                        base_clean = DIRECTUS_URL.rstrip('/')
                        tracking_url = f"{base_clean}/flows/trigger/{TRACKING_WEBHOOK_KEY}?log_id={log_id}"

                    msg_final = corpo.replace("{nome}", nome_real)
                    
                    res, txt = enviar_email_smtp(st.session_state['smtp'], email_real, assunto, msg_final, file_anexo, tracking_url)
                    
                    if log_id:
                        novo_status = "Enviado" if res else f"Erro: {txt}"
                        atualizar_status_envio(token, log_id, novo_status)

                        if res and item_id_real:
                            try:
                                atualizar_item(token, user_id, item_id_real, {"status": "ENVIADO EM MASSA"})
                            except: pass

                    if res: 
                        log.success(f"ENVIADO PARA {nome_real}")
                    else: 
                        log.error(f"ERRO {nome_real}: {txt}")
                    
                    bar.progress((i+1)/len(alvos_finais))
                st.balloons()
                time.sleep(2)
                st.rerun()

    with subtab_ext:
        st.markdown("### 📂 UPLOAD DE LISTA (EXCEL .xlsx)")
        up_file = st.file_uploader("ARQUIVO EXCEL (Colunas: nome, email, origem, url...)", type=["xlsx"])
        
        if up_file:
            try:
                df_ext = pd.read_excel(up_file)
                df_ext.columns = [c.lower() for c in df_ext.columns]
                
                if 'email' in df_ext.columns:
                    df_ext = df_ext[df_ext['email'].astype(str).str.contains("@")]
                    st.dataframe(df_ext.head(), use_container_width=True)
                    st.info(f"{len(df_ext)} LEADS ENCONTRADOS")

                    col_imp_btn, col_imp_info = st.columns([1, 2])
                    with col_imp_btn:
                        if st.button("💾 IMPORTAR LISTA PARA O CRM", type="primary"):
                            progress_text = "Importando leads para o banco de dados..."
                            my_bar = st.progress(0, text=progress_text)
                            
                            table_name = get_user_table_name(user_id)
                            base_url = DIRECTUS_URL.rstrip('/')
                            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                            
                            total_imp = len(df_ext)
                            sucesso_imp = 0
                            
                            for idx, row in df_ext.iterrows():
                                payload = {"status": "Novo"}
                                
                                for col in df_ext.columns:
                                    slug = col.strip().lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a')
                                    val = row[col]
                                    if pd.isna(val): val = ""
                                    payload[slug] = str(val)

                                try:
                                    r_imp = requests.post(f"{base_url}/items/{table_name}", json=payload, headers=headers, verify=False)
                                    if r_imp.status_code in [200, 204]:
                                        sucesso_imp += 1
                                except:
                                    pass
                                
                                my_bar.progress((idx + 1) / total_imp)
                            
                            my_bar.empty()
                            st.success(f"✅ IMPORTAÇÃO CONCLUÍDA! {sucesso_imp} LEADS SALVOS NO CRM.")
                            time.sleep(2)
                            st.rerun()

                    st.markdown("---")

                    assunto_ext = st.text_input("ASSUNTO", key="ass_ext")
                    st.caption("Dica: Use {{imagem}} no texto para inserir a imagem no corpo.")
                    corpo_ext = st.text_area("CORPO HTML (Use {nome})", height=150, key="body_ext")
                    file_anexo_ext = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_ext")
                    
                    if st.button("✨ GERAR COM IA (GROQ) - EXT"):
                        sug_a, sug_c = gerar_copy_ia(st.session_state.get('ctx', {}))
                        st.info(f"Assunto: {sug_a}")
                        st.code(sug_c)
                    
                    if st.button("🚀 DISPARAR LISTA EXTERNA"):
                        if not st.session_state.get('smtp'):
                            st.error("SMTP OFF")
                        elif len(df_ext) > saldo_envios:
                             st.error(f"LISTA ({len(df_ext)}) MAIOR QUE SALDO ({saldo_envios})")
                        else:
                            bar2 = st.progress(0)
                            log2 = st.empty()
                            
                            for i, row in df_ext.iterrows():
                                if i > 0:
                                    wait = random.randint(15, 30)
                                    log2.warning(f"⏳ ANTI-SPAM... {wait}s")
                                    time.sleep(wait)
                                
                                nome_l = row.get('nome', 'Parceiro')
                                email_l = str(row['email']).strip()

                                if not email_l or email_l.lower() == 'nan':
                                    continue
                                
                                log_id = registrar_log_envio(token, email_l, assunto_ext, "Enviando... [EXT]")
                                
                                tracking_url = None
                                if log_id and TRACKING_WEBHOOK_KEY != "SUA_CHAVE_AQUI":
                                    base_clean = DIRECTUS_URL.rstrip('/')
                                    tracking_url = f"{base_clean}/flows/trigger/{TRACKING_WEBHOOK_KEY}?log_id={log_id}"

                                msg_final = corpo_ext.replace("{nome}", str(nome_l))
                                
                                res, txt = enviar_email_smtp(st.session_state['smtp'], email_l, assunto_ext, msg_final, file_anexo_ext, tracking_url)
                                
                                if log_id:
                                    novo_status = "Enviado [EXT]" if res else f"Erro: {txt}"
                                    atualizar_status_envio(token, log_id, novo_status)

                                if res: log2.success(f"ENVIADO: {email_l}")
                                else: log2.error(f"FALHA: {email_l}")
                                
                                bar2.progress((i+1)/len(df_ext))
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                else:
                    st.error("O EXCEL PRECISA TER UMA COLUNA CHAMADA 'email'")
            except Exception as e:
                st.error(f"ERRO AO LER EXCEL: {e}")