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
                # Membaca file CSV dengan encoding latin1
                df = pd.read_csv(file_path, encoding='latin1')
                
                # Tambahkan fitur pencarian berdasarkan NIP atau Nama
                st.markdown("---")
                search_query = st.text_input("🔍 Cari Karyawan (ketik NIP atau Nama):", "").strip()
                
                # Filter data jika pengguna mengetik sesuatu di kotak pencarian
                if search_query:
                    # Cek kolom NIP dan Nama (pastikan huruf besar/kecil aman)
                    filtered_df = df[
                        df['NIP'].astype(str).str.contains(search_query, case=False, na=False) |
                        df['Nama'].astype(str).str.contains(search_query, case=False, na=False)
                    ]
                else:
                    filtered_df = df
                
                # Tampilkan informasi ringkas
                col1, col2, col3 = st.columns(3)
                col1.metric(label="Total Data Ditampilkan", value=filtered_df.shape[0])
                col2.metric(label="Total Seluruh Karyawan", value=df.shape[0])
                col3.metric(label="Total Kolom", value=df.shape[1])
                
                # Tampilkan tabel data interaktif
                st.subheader("📋 Tabel Data Karyawan")
                st.dataframe(filtered_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca file: {e}")
    else:
        st.warning(f"Tidak ada file berformat .csv di dalam folder '{data_dir}'.")
else:
    st.error(f"Folder '{data_dir}' tidak ditemukan di repository GitHub Anda!")