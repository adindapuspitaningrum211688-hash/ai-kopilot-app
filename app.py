import streamlit as st
import json
import os
from kaggle.api.kaggle_api_extended import KaggleApi

# ==========================================
# 1. KONFIGURASI TAMPILAN & CSS KUSTOM
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
    
    /* Hapus Latar Putih Kompleks: Buat Semua Input & Box Hanya Outline Garis Pinggir Putih */
    div[data-baseweb="input"], 
    div[data-baseweb="base-input"],
    textarea,
    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div {
        background-color: transparent !important;
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }

    /* Hilangkan background putih pada popover, dialog, dan expander */
    div[data-testid="stPopover"] > button,
    .stButton > button {
        background-color: transparent !important;
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    
    .stButton > button:hover, div[data-testid="stPopover"] > button:hover {
        border-color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Style Header Selamat Datang di Tengah & Spasi Antar Kata */
    .welcome-container {
        text-align: center;
        width: 100%;
        margin: 0 auto 20px auto;
    }
    .welcome-title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .word-group {
        display: inline-flex;
        gap: 6px;
        margin: 0 14px; /* Memberikan Spasi Nyata Antar Kata */
    }
    .letter-box {
        border: 1.5px solid rgba(255, 255, 255, 0.85);
        background: transparent !important;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 17px;
        font-weight: bold;
        color: #FFFFFF;
        display: inline-block;
    }
    
    /* Area Catatan Utama Transparan */
    .main-editor-card {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Kotak Jawaban AI Transparan */
    .ai-box {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-left: 4px solid #d8b4fe;
        border-radius: 8px;
        padding: 14px;
        margin: 10px 0;
    }
    
    /* Sidebar Transparan Tanpa Icon Bug */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 5, 25, 0.5) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Sembunyikan teks sistem ekspander yang rusak */
    summary div p {
        display: inline-block;
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
# 4. SIDEBAR NAVIGASI RAPI & BERSIH
# ==========================================
with st.sidebar:
    st.subheader("Navigasi")
    
    # Mode Pilihan Menu Utama
    menu_choice = st.radio("Menu Utama", ["Obrolan", "Diary", "Project"], index=0)
    
    st.divider()

    if menu_choice == "Obrolan":
        if st.button("➕ Obrolan Baru", use_container_width=True):
            new_id = f"chat_{len(st.session_state.chats)+1}"
            st.session_state.chats[new_id] = {"title": f"Obrolan {len(st.session_state.chats)+1}", "messages": [], "memory": [], "media": []}
            st.session_state.active_id = new_id
            st.session_state.current_view = "obrolan"
            st.rerun()
            
        for cid, cdata in list(st.session_state.chats.items()):
            if st.button(f"💬 {cdata['title']}", key=f"btn_{cid}", use_container_width=True):
                st.session_state.active_id = cid
                st.session_state.current_view = "obrolan"
                st.rerun()

    elif menu_choice == "Diary":
        if st.button("➕ Diary Baru", use_container_width=True):
            new_id = f"diary_{len(st.session_state.diaries)+1}"
            st.session_state.diaries[new_id] = {"title": f"Diary {len(st.session_state.diaries)+1}", "content": "", "messages": [], "memory": [], "media": []}
            st.session_state.active_id = new_id
            st.session_state.current_view = "diary"
            st.rerun()
            
        for did, ddata in list(st.session_state.diaries.items()):
            if st.button(f"📖 {ddata['title']}", key=f"btn_{did}", use_container_width=True):
                st.session_state.active_id = did
                st.session_state.current_view = "diary"
                st.rerun()

    else:
        if st.button("➕ Project Baru", use_container_width=True):
            new_id = f"proj_{len(st.session_state.projects)+1}"
            st.session_state.projects[new_id] = {"title": f"Proyek {len(st.session_state.projects)+1}", "content": "", "messages": [], "memory": [], "memory": [], "media": []}
            st.session_state.active_id = new_id
            st.session_state.current_view = "project"
            st.rerun()
            
        for pid, pdata in list(st.session_state.projects.items()):
            if st.button(f"🚀 {pdata['title']}", key=f"btn_{pid}", use_container_width=True):
                st.session_state.active_id = pid
                st.session_state.current_view = "project"
                st.rerun()

    st.divider()

    # --- CARI DALAM SEMUA ---
    with st.popover("🔍 Cari Dalam Semua"):
        search_query = st.text_input("Cari kata kunci...", key="global_search")
        if search_query:
            st.caption(f"Hasil pencarian untuk: **{search_query}**")
            for cid, c in st.session_state.chats.items():
                if any(search_query.lower() in m["content"].lower() for m in c["messages"]):
                    st.write(f"• [Obrolan] {c['title']}")
            for did, d in st.session_state.diaries.items():
                if search_query.lower() in d["content"].lower():
                    st.write(f"• [Diary] {d['title']}")

    # --- GLOSARIUM ISTILAH ---
    with st.popover("📚 Glosarium Istilah"):
        g_search = st.text_input("Cari Istilah...", key="g_search")
        for k, v in st.session_state.glosarium.items():
            if not g_search or g_search.lower() in k.lower() or g_search.lower() in v.lower():
                st.markdown(f"**{k}**")
                st.caption(v)

    # --- KINERJA AI ---
    with st.popover("⚡ Kinerja AI"):
        st.caption(status_sys)
        st.metric("Total Master Tools", len(manifest_tools))
        st.metric("Latensi Sistem", "12 ms")
        st.metric("Status GPU", "Tesla T4 Ready")

# ==========================================
# 5. SAPAAN UTAMA (PRESISI TENGAH & SPASI KATA)
# ==========================================
st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
st.markdown('<div class="welcome-title">Selamat datang!</div>', unsafe_allow_html=True)

# Pembagian Tepat Kata dengan Spasi Nyata Antar Kelompok Kata
dear_words = ["D", "e", "a", "r"]
affectionate_words = ["A", "f", "f", "e", "c", "t", "i", "o", "n", "a", "t", "e"]
fairmindedness_word = "Fairmindedness"

html_content = '<div style="text-align: center;">'

# Kelompok Kata 1: Dear
html_content += '<div class="word-group">'
for w in dear_words:
    html_content += f'<div class="letter-box">{w}</div>'
html_content += '</div>'

# Kelompok Kata 2: Affectionate
html_content += '<div class="word-group">'
for w in affectionate_words:
    html_content += f'<div class="letter-box">{w}</div>'
html_content += '</div>'

# Kelompok Kata 3: Fairmindedness
html_content += '<div class="word-group">'
html_content += f'<div class="letter-box">{fairmindedness_word}</div>'
html_content += '</div>'

html_content += '</div>'

st.markdown(html_content, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# Get Active Item Data
current_view = st.session_state.current_view
active_id = st.session_state.active_id

if current_view == "obrolan":
    active_data = st.session_state.chats.get(active_id, st.session_state.chats["default"])
elif current_view == "diary":
    active_data = st.session_state.diaries.get(active_id, list(st.session_state.diaries.values())[0])
else:
    active_data = st.session_state.projects.get(active_id, list(st.session_state.projects.values())[0])

# ==========================================
# 6. HEADER UTAMA: RENAME, MEMORY & MEDIA
# ==========================================
col_h1, col_h2, col_h3 = st.columns([0.5, 0.25, 0.25])

with col_h1:
    new_title = st.text_input("Judul Sesi", value=active_data["title"], key=f"title_{active_id}")
    active_data["title"] = new_title

with col_h2:
    with st.popover("🧠 Editable Memory"):
        st.subheader("Memori Sesi Ini")
        mem_text = st.text_area("Kelola fakta & preferensi memori:", value="\n".join(active_data["memory"]))
        if st.button("Simpan Memori"):
            active_data["memory"] = [m.strip() for m in mem_text.split("\n") if m.strip()]
            st.success("Memori diperbarui!")

with col_h3:
    with st.popover("📁 Media Library"):
        st.subheader("Pustaka Media & File")
        uploaded = st.file_uploader("Unggah berkas", accept_multiple_files=True)
        if uploaded:
            for f in uploaded:
                active_data["media"].append(f.name)
            st.success("File ditambahkan ke pustaka!")
        if active_data["media"]:
            for m in active_data["media"]:
                st.caption(f"📄 {m}")

# ==========================================
# 7. TAMPILAN UTAMA DIARY & PROJECT
# ==========================================
if current_view in ["diary", "project"]:
    st.markdown('<div class="main-editor-card">', unsafe_allow_html=True)
    st.subheader(f"Lembar Tulis {current_view.capitalize()}")
    
    content_input = st.text_area(
        "Isi Catatan:",
        value=active_data.get("content", ""),
        height=350,
        key=f"editor_{active_id}"
    )
    active_data["content"] = content_input
    st.markdown('</div>', unsafe_allow_html=True)

    with st.popover("🤖 Perintah & Riwayat Asisten AI"):
        st.info("Ajukan perintah ke AI untuk membantu mengedit, merangkum, atau menganalisis catatan di atas.")

# ==========================================
# 8. PANEL INPUT PERINTAH & MODE EKSPLORASI
# ==========================================
col_mode, col_add = st.columns([0.7, 0.3])
with col_mode:
    mode = st.radio(
        "Mode Eksplorasi:",
        ["Kerja 💼", "Diskusi 💬", "Opini 💡", "Kehidupan 🌿", "Detektif 🔍"],
        horizontal=True
    )

for msg in active_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt := st.chat_input("Kirim perintah atau pertanyaan ke AI Kopilot..."):
    active_data["messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        st.write(f"*(Mode: {mode})* Memproses instruksi dengan 352 Master Tools...")
        
        with st.container():
            st.markdown('<div class="ai-box">', unsafe_allow_html=True)
            st.markdown("**Opsi 1: Jawaban Langsung & Praktis**")
            st.write(f"Berikut adalah ringkasan solusi untuk: *{user_prompt}*")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="ai-box">', unsafe_allow_html=True)
            st.markdown("**Opsi 2: Analisis Sistemik & Mendalam**")
            st.write(f"Menganalisis keterkaitan elemen-elemen dari perspektif *{mode}*.")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="ai-box">', unsafe_allow_html=True)
            st.markdown("**Opsi 3: Metodologi & Tindakan Lanjutan**")
            st.write("Langkah-langkah strategis berbasis kerangka kerja dan registri tool.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        full_response = f"[Respon Terstruktur Tiga Opsi untuk: {user_prompt}]"
        active_data["messages"].append({"role": "assistant", "content": full_response})
