import streamlit as st
import sqlite3
import time
from datetime import datetime

# Puslapio konfigūracija (pritaikyta telefonams)
st.set_page_config(page_title="Laiko Trackeris", page_icon="⏱️", layout="centered")

# Duomenų bazės paruošimas
def db_init():
    conn = sqlite3.connect("mobilus_laikas.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laiko_logas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projektas TEXT,
            data TEXT,
            trukme TEXT
        )
    """)
    conn.commit()
    conn.close()

db_init()

st.title("⏱️ Darbo Valandų Apskaita")
st.caption("Tobula Python programėlė jūsų telefonui")

# Projekto įvedimas
project_name = st.text_input("Projekto arba užduoties pavadinimas:", placeholder="Pvz.: Programavimas, Skaitymas")

# Naudojame Streamlit session_state laiko sekimui
if "running" not in st.session_state:
    st.session_state.running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ STARTAS", use_container_width=True, disabled=st.session_state.running):
        st.session_state.running = True
        st.session_state.start_time = time.time()
        st.rerun()

with col2:
    if st.button("⏹️ STABDYTI", use_container_width=True, disabled=not st.session_state.running):
        st.session_state.running = False
        elapsed = time.time() - st.session_state.start_time
        
        # Formatuojame laiką
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Įrašome į SQLite
        proj = project_name.strip() or "Be pavadinimo"
        conn = sqlite3.connect("mobilus_laikas.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO laiko_logas (projektas, data, trukme) VALUES (?, ?, ?)", (proj, current_date, duration_str))
        conn.commit()
        conn.close()
        
        st.success(f"Išsaugota! Trukmė: {duration_str}")
        st.rerun()

# Jei laikmatis veikia, parodome statusą
if st.session_state.running:
    st.info("⏱️ Laikmatis veikia... Paspauskite STABDYTI, kai baigsite.")

# Istorijos rodymas
st.subheader("📊 Paskutiniai įrašai")
conn = sqlite3.connect("mobilus_laikas.db")
cursor = conn.cursor()
cursor.execute("SELECT projektas, data, trukme FROM laiko_logas ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()
conn.close()

if rows:
    for row in rows:
        with st.container(border=True):
            st.markdown(f"**📂 {row[0]}**")
            st.markdown(f"📅 {row[1]} | ⏱️ {row[2]}")
else:
    st.write("Įrašų dar nėra. Paleiskite laikmatį!")
