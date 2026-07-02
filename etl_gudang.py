import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from sqlalchemy import create_engine

def run_etl():
    print("🚀 Memulai proses ETL Gudang (Target: Supabase Cloud)...")
    
    # ==========================================
    # 1. FASE EXTRACT (Menarik Data Mentah)
    # ==========================================
    print("📥 [Extract] Menghubungkan ke Google Sheets...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client_gs = gspread.authorize(creds)
    
    sheet = client_gs.open("Database Gudang").sheet1
    data_mentah = sheet.get_all_records()
    
    df = pd.DataFrame(data_mentah)
    print(f"✅ [Extract] Berhasil menarik {len(df)} baris data.")

    # ==========================================
    # 2. FASE TRANSFORM (Membersihkan & Mengolah Data)
    # ==========================================
    print("⚙️ [Transform] Memproses data...")
    df = df.fillna("")
    df['nama_barang'] = df['nama_barang'].astype(str).str.lower().str.strip()
    df['varian'] = df['varian'].astype(str).str.lower().str.strip()
    df['kondisi'] = df['kondisi'].astype(str).str.lower().str.strip()
    df['jumlah'] = pd.to_numeric(df['jumlah'], errors='coerce').fillna(0).astype(int)
    
    # Kalkulasi Sisa Stok
    print("🧮 [Transform] Menghitung sisa stok akhir...")
    df['jumlah_kalkulasi'] = df.apply(
        lambda row: row['jumlah'] if row['status_transaksi'].lower() == 'masuk' else -row['jumlah'], 
        axis=1
    )
    df_stok_akhir = df.groupby(['nama_barang', 'varian', 'kondisi'])['jumlah_kalkulasi'].sum().reset_index()
    df_stok_akhir.rename(columns={'jumlah_kalkulasi': 'sisa_stok'}, inplace=True)
    print(f"✅ [Transform] Kalkulasi selesai. Ditemukan {len(df_stok_akhir)} item unik.")

    # ==========================================
    # 3. FASE LOAD CLOUD (Simpan ke Supabase PostgreSQL)
    # ==========================================
    print("🌐 [Load] Menghubungkan ke database Supabase...")
    
    # Menyalakan mesin SQLAlchemy pakai alamat dari secrets.toml
    engine = create_engine(st.secrets["SUPABASE_URL"])
    
    try:
        # Menyuntikkan data langsung jadi tabel SQL
        # if_exists='replace' artinya tiap kali ETL jalan, tabel lama dihapus, diganti data paling fresh
        print("💾 [Load] Menyuntikkan log_transaksi ke database...")
        df.to_sql('log_transaksi', engine, if_exists='replace', index=False)
        
        print("💾 [Load] Menyuntikkan tabel_stok_akhir ke database...")
        df_stok_akhir.to_sql('tabel_stok_akhir', engine, if_exists='replace', index=False)
        
        print("🎉 Proses ETL ke Cloud Database SELESAI dengan sukses!")
    except Exception as e:
        print(f"❌ [Error] Gagal mengirim data ke Supabase: {e}")

if __name__ == "__main__":
    run_etl()