import streamlit as st
import json
import os
from kaggle.api.kaggle_api_extended import KaggleApi

# ==========================================
# 1. KONFIGURASI TAMPILAN & CSS PURE OUTLINE
# ==========================================
st.set_page_config(page_title="AI Kopilot", page_icon="🔮", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Alice&display=swap');
    
    /* Background Utama Bertema Pemandangan Laut & Langit Magenta */
    .stApp {
        background: linear-gradient(180deg, #4a154b 0%, #2b1055 40%, #75225b 70%, #1a0826 100%);
        background-attachment: fixed;
        font-family: 'Alice', serif !important;
        color: #FFFFFF !important;
    }
    
    /* Font Alice untuk Seluruh Teks */
    h1, h2, h3, h4, h5, h6, p, div, span, label, input, textarea, button {
        font-family: 'Alice', serif !important;
        color: #FFFFFF !important;
    }

    /* Paksa Semua Input, Textarea, & Container Transparan Tanpa Latar Belakang Putih */
    div[data-baseweb="input"], 
    div[data-baseweb="base-input"],
    textarea,
    .stTextInput input,
    .stTextArea textarea {
        background-color: transparent !important;
        background: transparent !important;
        border: 1.5px solid rgba(255, 255, 255, 0.7) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
    }

    /* --------------------------------------------------------------------- */
    /* PERBAIKAN: OVERRIDE KHUSUS ST.CHAT_INPUT & ELEMEN BAWAAN STREAMLIT    */
    /* --------------------------------------------------------------------- */
    
    /* Area Container Utama Chat Input */
    div[data-testid="stChatInput"] {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* Inner Wrapper Chat Input */
    div[data-testid="stChatInput"] > div {
        background-color: transparent !important;
        background: transparent !important;
        border: 1.5px solid rgba(255, 255, 255, 0.7) !important;
        border-radius: 12px !important;
    }

    /* Textarea di Dalam Chat Input */
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        background: transparent !important;
        color: #FFFFFF !important;
        border: none !important; /* Mengikuti border container outer */
    }

    /* Tombol Kirim pada Chat Input */
    div[data-testid="stChatInput"] button {
        background-color: transparent !important;
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    div[data-testid="stChatInput"] button:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: #FFFFFF !important;
    }

    /* Bubble Obrolan (User & Assistant) */
    div[data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        margin-bottom: 10px;
    }

    /* --------------------------------------------------------------------- */

    /* Paksa Semua Tombol Bertipe Outline Transparan Murni */
    .stButton > button {
        background-color: transparent !important;
        background: transparent !important;
        border: 1.5px solid rgba(255, 255, 255, 0.7) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        backdrop-filter: none !important;
        box-shadow: none !important;
    }
    
    .stButton > button:hover {
        border-color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Style Header Sapaan & Kotak Huruf Konsisten */
    .welcome-container {
        text-align: center;
        width: 100%;
        margin: 0 auto 25px auto;
    }
    .welcome-title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
    }
    .word-group {
        display: inline-flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin: 8px 12px;
    }
    .letter-box {
        border: 1.5px solid rgba(255, 255, 255, 0.85);
        background: transparent !important;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 17px !important;
        font-weight: bold;
        color: #FFFFFF;
        display: inline-block;
    }

    /* Lembar Tulis & Panel Transparan */
    .main-editor-card {
        background: transparent !important;
        border: 1.5px solid rgba(255, 255, 255, 0.5);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .ai-box {
        background: transparent !important;
        border: 1.5px solid rgba(255, 255, 255, 0.4);
        border-left: 4px solid #d8b4fe !important;
        border-radius: 8px;
        padding: 14px;
        margin: 10px 0;
    }

    /* Sidebar Transparan Clean */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 5, 25, 0.5) !important;
        border-right: 1.5px solid rgba(255, 255, 255, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INISIALISASI SESSION STATE
# ==========================================
if "current_view" not in st.session_state:
    st.session_state.current_view = "obrolan"

if "active_id" not in st.session_state:
    st.session_state.active_id = "default"

if "active_panel" not in st.session_state:
    st.session_state.active_panel = None  # None, 'memory', 'media', 'search', 'glosarium', 'kinerja', 'ai'

if "chats" not in st.session_state:
    st.session_state.chats = {"default": {"title": "Obrolan Utama", "messages": [], "memory": [], "media": []}}

if "diaries" not in st.session_state:
    st.session_state.diaries = {"d1": {"title": "Catatan Diary 1", "content": "Tuliskan diary kamu di sini...", "messages": [], "memory": [], "media": []}}

if "projects" not in st.session_state:
    st.session_state.projects = {"p1": {"title": "Proyek R&D AI", "content": "Dokumentasi dan perencanaan proyek...", "messages": [], "memory": [], "media": []}}

if "glosarium" not in st.session_state:
    st.session_state.glosarium = {
        "Kebijaksanaan Sains": "Integrasi pemikiran sistemik, argumentasi ilmiah, dan integritas intelektual.",
        "Fairmindedness": "Sikap memperlakukan semua sudut pandang secara adil tanpa prasangka.",
        "Quantization": "Teknik kompresi model AI agar efisien dijalankan di perangkat terbatas.",
        "ZeroGPU": "Alokasi dinamis GPU A100/H100 gratis dari Hugging Face untuk tugas inferensi."
    }

# ==========================================
# 3. KONEKSI REGISTRI MASTER KAGGLE
# ==========================================
@st.cache_resource
def load_kaggle_manifest():
    try:
        os.environ['KAGGLE_USERNAME'] = st.secrets["KAGGLE_USERNAME"]
        os.environ['KAGGLE_KEY'] = st.secrets["KAGGLE_KEY"]
        api = KaggleApi()
        api.authenticate()
        dataset_target = f"{st.secrets['KAGGLE_USERNAME']}/ai-kopilot-registry-full-all-tools"
        local_dir = "./registry_data"
        os.makedirs(local_dir, exist_ok=True)
        api.dataset_download_file(dataset_target, file_name="registry_manifest.json", path=local_dir)
        manifest_path = os.path.join(local_dir, "registry_manifest.json")
        data = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                data.append(json.loads(line.strip()))
        return data, "✔ Terhubung ke Kaggle Master Registry"
    except Exception as e:
        return [], f"⚠ Standalone Mode: {str(e)}"

manifest_tools, status_sys = load_kaggle_manifest()

# ==========================================
# 4. SIDEBAR NAVIGASI
# ==========================================
with st.sidebar:
    st.subheader("Menu Utama")
    
    menu_choice = st.radio("Pilih Tampilan", ["Obrolan", "Diary", "Project"], index=0, label_visibility="collapsed")
    st.divider()

    if menu_choice == "Obrolan":
        if st.button("➕ Obrolan Baru", use_container_width=True):
