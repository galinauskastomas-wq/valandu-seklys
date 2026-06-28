import streamlit as st
import sqlite3
import time
from datetime import datetime
import pandas as pd

# Puslapio konfigūracija
st.set_page_config(page_title="Valandų Seklys", page_icon="⏱️", layout="centered")

# --- DUOMENŲ BAZĖS VALDYMAS ---
def db_init():
    conn = sqlite3.connect("mobilus_laikas.db")
    cursor = conn.cursor()
    # Pagrindinė logų lentelė
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laiko_logas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projektas TEXT,
            data TEXT,
            trukme TEXT
        )
    """)
    # NAUJA LENTELĖ: Laikmačio būsenos saugojimui tarp sesijų
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laikmacio_busena (
            id INTEGER PRIMARY KEY,
            is_running INTEGER,
            start_time REAL,
            veikla TEXT
        )
    """)
    # Užtikriname, kad būsenos lentelėje būtų bent viena eilutė (ID: 1)
    cursor.execute("INSERT OR IGNORE INTO laikmacio_busena (id, is_running, start_time, veikla) VALUES (1, 0, 0.0, '')")
    conn.commit()
    conn.close()

def gauti_busena():
    conn = sqlite3.connect("mobilus_laikas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_running, start_time, veikla FROM laikmacio_busena WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"is_running": bool(row[0]), "start_time": row[1], "veikla": row[2]}

def issaugoti_busena(is_running, start_time, veikla):
    conn = sqlite3.connect("mobilus_laikas.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE laikmacio_busena SET is_running = ?, start_time = ?, veikla = ? WHERE id = 1", 
                   (1 if is_running else 0, start_time, veikla))
    conn.commit()
    conn.close()

db_init()

# Užkrauname esamą būseną iš DB
busena = gauti_busena()

st.title("⏱️ Valandų Seklys")
st.caption("Nepalaužiamas laiko optimizavimo įrankis (veikia ir išjungus telefoną)")

# Jei laikmatis jau veikia, užfiksuojame tekstą iš DB, kad vartotojas netyčia jo nepakeistų
if busena["is_running"]:
    project_name = st.text_input("Užduoties ar veiklos pavadinimas:", value=busena["veikla"], disabled=True)
else:
    project_name = st.text_input("Užduoties ar veiklos pavadinimas:", placeholder="Pvz.: Skaitymas, Sportas, Kodavimas")

col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ STARTAS", use_container_width=True, disabled=busena["is_running"]):
        proj = project_name.strip() or "Be pavadinimo"
        # Įrašome starto laiką tiesiai į SQLite
        issaugoti_busena(True, time.time(), proj)
        st.rerun()

with col2:
    if st.button("⏹️ STABDYTI", use_container_width=True, disabled=not busena["is_running"]):
        if busena["start_time"] > 0:
            elapsed = time.time() - busena["start_time"]
            hours, rem = divmod(elapsed, 3600)
            minutes, seconds = divmod(rem, 60)
            duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Įrašome rezultatą į istoriją
            conn = sqlite3.connect("mobilus_laikas.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO laiko_logas (projektas, data, trukme) VALUES (?, ?, ?)", (busena["veikla"], current_date, duration_str))
            conn.commit()
            conn.close()
            st.success(f"Išsaugota! Trukmė: {duration_str}")
        
        # Atstatome laikmačio būseną į pradinę
        issaugoti_busena(False, 0.0, "")
        st.rerun()

# Dinaminis pranešimas apie veikiantį laikmatį
if busena["is_running"]:
    praejo_sekundziu = int(time.time() - busena["start_time"])
    p_hours, p_rem = divmod(praejo_sekundziu, 3600)
    p_minutes, p_seconds = divmod(p_rem, 60)
    st.info(f"⏱️ Seklys skaičiuoja laiko tarpą veiklai: **{busena['veikla']}**")
    st.caption(f"Orientacinė trukmė nuo paleidimo: {p_hours:02d}:{p_minutes:02d}:{p_seconds:02d} (atnaujinus puslapį)")

# --- DUOMENŲ APDOROJIMAS IŠ DB ---
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

    # --- ĮRAŠŲ VALDYMAS IR TRYNIMAS ---
    st.subheader("📋 Paskutinių įrašų valdymas")
    paskutiniai_irasae = df.head(5)
    
    for index, row in paskutiniai_irasae.iterrows():
        c_text, c_button = st.columns([3, 1]) # Tekstui duodame daugiau vietos nei mygtukui
        
        with c_text:
            st.markdown(f"**📂 {row['Veikla']}** ({row['Trukmė']})  \n*{row['Data']}*")
            
        with c_button:
            if st.button("❌", key=f"delete_{row['id']}", use_container_width=True):
                conn = sqlite3.connect("mobilus_laikas.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM laiko_logas WHERE id = ?", (int(row['id']),))
                conn.commit()
                conn.close()
                st.toast(f"Ištrinta!")
                time.sleep(0.3)
                st.rerun()
        st.markdown("---")
else:
    st.subheader("📊 Paskutiniai įrašai")
    st.write("Įrašų dar nėra. Paleiskite laikmatį!")
