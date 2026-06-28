import streamlit as st
import sqlite3
import time
from datetime import datetime
import pandas as pd  # Naudosime CSV generavimui

# Puslapio konfigūracija
st.set_page_config(page_title="Valandų Seklys", page_icon="⏱️", layout="centered")

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

st.title("⏱️ Valandų Seklys")
st.caption("Jūsų asmeninis laiko optimizavimo įrankis")

# Projekto įvedimas
project_name = st.text_input("Užduoties ar veiklos pavadinimas:", placeholder="Pvz.: Skaitymas, Sportas, Kodavimas")

# Session state laikmačiui
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
        
        # Formatuojame laiką į HH:MM:SS
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

# Jei laikmatis veikia
if st.session_state.running:
    st.info("⏱️ Seklys skaičiuoja laiką... Užsiimkite veikla!")

# --- ISTORIJA IR EKSPORTAS ---
st.subheader("📊 Paskutiniai įrašai")

conn = sqlite3.connect("mobilus_laikas.db")
# Užkrauname duomenis tiesiai į Pandas DataFrame patogesniam valdymui
df = pd.read_sql_query("SELECT projektas AS 'Veikla', data AS 'Data', trukme AS 'Trukmė' FROM laiko_logas ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    # Parodome paskutinius 5 įrašus gražioje Streamlit lentelėje
    st.dataframe(df.head(5), use_container_width=True)
    
    # NAUJA FUNKCIJA: Duomenų atsisiuntimas (Eksportas)
    csv = df.to_csv(index=False).encode('utf-8-sig') # utf-8-sig reikalingas, kad Excel teisingai rodytų lietuviškas raides
    
    st.download_button(
        label="📥 Atsisiųsti visą istoriją (CSV / Excel)",
        data=csv,
        file_name=f"laiko_apskaita_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.write("Įrašų dar nėra. Paleiskite laikmatį!")
