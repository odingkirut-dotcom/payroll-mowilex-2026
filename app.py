import streamlit as st
import pandas as pd
import os

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard Payroll & Absensi Mowilex 2026",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Payroll & Absensi Mowilex 2026")
st.write("Aplikasi analisis data karyawan Mowilex secara online dan real-time.")

# Direktori data
data_dir = "2026"

if os.path.exists(data_dir):
    files = os.listdir(data_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if csv_files:
        csv_files.sort()
        selected_file = st.selectbox("📂 Pilih Periode Data CSV:", csv_files)
        
        if selected_file:
            file_path = os.path.join(data_dir, selected_file)
            
            try:
                # Membaca file CSV dengan encoding latin1 (aman dari error karakter)
                df = pd.read_csv(file_path, encoding='latin1')
                
                # Tampilkan informasi ringkas
                st.success(f"Berhasil memuat file: **{selected_file}**")
                st.metric(label="Total Baris Data", value=df.shape[0])
                st.metric(label="Total Kolom", value=df.shape[1])
                
                # Tampilkan tabel data interaktif
                st.subheader("📋 Tabel Data Karyawan")
                st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca file: {e}")
    else:
        st.warning(f"Tidak ada file berformat .csv di dalam folder '{data_dir}'.")
else:
    st.error(f"Folder '{data_dir}' tidak ditemukan di repository GitHub Anda!")