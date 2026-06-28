import streamlit as st
import sqlite3
import time
from datetime import datetime
import pandas as pd

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
        
        if st.session_state.start_time is not None:
            elapsed = time.time() - st.session_state.start_time
            hours, rem = divmod(elapsed, 3600)
            minutes, seconds = divmod(rem, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            proj = project_name.strip() or "Be pavadinimo"
            conn = sqlite3.connect("mobilus_laikas.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO laiko_logas (projektas, data, trukme) VALUES (?, ?, ?)", (proj, current_date, duration_str))
            conn.commit()
            conn.close()
            
            st.success(f"Išsaugota! Trukmė: {duration_str}")
        else:
            st.error("Įvyko klaida: Laikmatis nebuvo teisingai paleistas.")
            
        st.session_state.start_time = None
        st.rerun()

if st.session_state.running:
    st.info("⏱️ Seklys skaičiuoja laiką... Užsiimkite veikla!")

# --- DUOMENŲ APDOROJIMAS ---
conn = sqlite3.connect("mobilus_laikas.db")
df = pd.read_sql_query("SELECT id, projektas AS 'Veikla', data AS 'Data', trukme AS 'Trukmė' FROM laiko_logas ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    # --- EKSPORTAS ---
    st.subheader("📊 Duomenų eksportas")
    csv = df[['Veikla', 'Data', 'Trukmė']].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Atsisiųsti visą istoriją (CSV / Excel)",
        data=csv,
        file_name=f"laiko_apskaita_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # --- NAUJA FUNKCIJA: ĮRAŠŲ VALDYMAS IR TRYNIMAS ---
    st.subheader("📋 Paskutinių įrašų valdymas")
    
    # Rodome paskutinius 5 įrašus su trynimo mygtukais šalia
    paskutiniai_irasae = df.head(5)
    
    for index, row in paskutiniai_irasae.iterrows():
        # Sukuriame stulpelius: tekstui ir trynimo mygtukui
        c_text, c_button = st.columns([4, 1])
        
        with c_text:
            st.markdown(f"**📂 {row['Veikla']}** ({row['Trukmė']})  \n*{row['Data']}*")
            
        with c_button:
            # Kiekvienas mygtukas turi unikalų raktą (key) pagal įrašo ID bazėje
            if st.button("❌ Trinti", key=f"delete_{row['id']}", use_container_width=True):
                conn = sqlite3.connect("mobilus_laikas.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM laiko_logas WHERE id = ?", (int(row['id']),))
                conn.commit()
                conn.close()
                st.toast(f"Įrašas '{row['Veikla']}' ištrintas!")
                time.sleep(0.5) # Trumpa pauzė sklandžiam persikrovimui
                st.rerun()
        st.markdown("---") # Atskyrimo linija tarp įrašų
else:
    st.subheader("📊 Paskutiniai įrašai")
    st.write("Įrašų dar nėra. Paleiskite laikmatį!")
