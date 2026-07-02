import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# ========================================================
# 🔒 GERBANG KEAMANAN TINGKAT TINGGI (PASSWORD GATE)
# ========================================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("### 🔑 Dashboard Terkunci")
    password_input = st.text_input("Masukkan PIN Akses Dashboard:", type="password")
    if st.button("Buka Kunci"):
        if password_input == st.secrets["APP_PASSWORD"]: 
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ PIN Salah! Akses ditolak.")
    return False

if not check_password():
    st.stop()
# ========================================================

st.set_page_config(page_title="Dashboard Gudang", page_icon="📊", layout="wide")
st.title("📊 Dashboard Gudang (Versi Cloud Database ☁️)")

# ========================================================
# ☁️ BACA BENSIN DARI CLOUD DATABASE (SUPABASE)
# ========================================================
try:
    # 1. Nyalain mesin kurir pakai alamat dari secrets.toml
    engine = create_engine(st.secrets["SUPABASE_URL"])
    
    # 2. Tarik data pakai query SQL langsung dari Supabase!
    df_stok = pd.read_sql("SELECT * FROM tabel_stok_akhir", engine)
    
    st.success("⚡ Data berhasil ditarik instan dari Cloud Database Supabase!")
    
    # ----------------------------------------------------
    # KARTU RINGKASAN METRIK (SUMMARY CARDS)
    # ----------------------------------------------------
    st.markdown("### 📋 Ikhtisar Gudang Hari Ini")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_kategori = len(df_stok)
        st.metric(label="📦 Total Jenis Item", value=f"{total_kategori} Item")
        
    with col2:
        total_stok_fisik = df_stok['sisa_stok'].sum()
        st.metric(label="🔢 Total Unit Stok", value=f"{total_stok_fisik} Pcs")
        
    with col3:
        total_minus = len(df_stok[df_stok['sisa_stok'] < 0])
        st.metric(label="⚠️ Item Selisih / Minus", value=f"{total_minus} Item", delta="- Perlu Audit" if total_minus > 0 else "Aman")

    st.markdown("---")

    # TAMPILAN TABEL DATA
    st.markdown("### 📦 Rekap Sisa Stok Detail")
    st.dataframe(df_stok, use_container_width=True, hide_index=True)

    # TAMPILAN GRAFIK
    st.markdown("---")
    st.markdown("### 📈 Visualisasi Total Stok Gudang")

    df_chart = df_stok.groupby('nama_barang')['sisa_stok'].sum().reset_index()

    fig = px.bar(
        df_chart, 
        x="nama_barang", 
        y="sisa_stok", 
        title="Total Keseluruhan Stok Per Barang",
        text_auto=True,  
        template="plotly_white"
    )
    fig.update_layout(xaxis_title="Nama Barang", yaxis_title="Total Sisa Stok")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Gagal narik data dari database: {e}")
