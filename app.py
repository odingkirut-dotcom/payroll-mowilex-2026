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
        
        # Tambahkan opsi untuk menggabungkan seluruh file di awal list
         pilihan_menu = ["📂 Gabungkan SEMUA File (Seluruh Periode)"] + csv_files
        selected_option = st.selectbox("📂 Pilih Periode / Tampilan Data:", pilihan_menu)
        
        try:
            if selected_option == "📂 Gabungkan SEMUA File (Seluruh Periode)":
                # Gabungkan semua file CSV yang ada di folder 2026
                df_list = []
                for file in csv_files:
                    f_path = os.path.join(data_dir, file)
                    temp_df = pd.read_csv(f_path, encoding='latin1')
                    temp_df['Periode_File'] = file # Menandai asal file
                    df_list.append(temp_df)
                
                df = pd.concat(df_list, ignore_index=True)
                st.success("Berhasil menggabungkan seluruh file dari semua periode!")
            else:
                # Membaca satu file yang dipilih
                file_path = os.path.join(data_dir, selected_option)
                df = pd.read_csv(file_path, encoding='latin1')
                st.success(f"Berhasil memuat file: **{selected_option}**")
            
            # Fitur Pencarian Berdasarkan NIP atau Nama
            st.markdown("---")
            search_query = st.text_input("🔍 Cari Karyawan (ketik NIP atau Nama):", "").strip()
            
            if search_query:
                filtered_df = df[
                    df['NIP'].astype(str).str.contains(search_query, case=False, na=False) |
                    df['Nama'].astype(str).str.contains(search_query, case=False, na=False)
                ]
            else:
                filtered_df = df
            
            # Ringkasan Metrik
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Total Data Ditampilkan", value=filtered_df.shape[0])
            col2.metric(label="Total Seluruh Baris", value=df.shape[0])
            col3.metric(label="Total Kolom", value=df.shape[1])
            
            # Tampilkan tabel data interaktif
            st.subheader("📋 Tabel Data Karyawan")
            st.dataframe(filtered_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")
            
    else:
        st.warning(f"Tidak ada file berformat .csv di dalam folder '{data_dir}'.")
else:
    st.error(f"Folder '{data_dir}' tidak ditemukan di repository GitHub Anda!")