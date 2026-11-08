import streamlit as st
import pandas as pd
import os

st.title("📊 Dashboard Payroll & Absensi Mowilex 2026")

# Contoh membaca folder data 2026
data_dir = "2026"
if os.path.exists(data_dir):
    files = os.listdir(data_dir)
    st.write("File data yang tersedia:", files)
    
    # Pilih file CSV jika ada
    csv_files = [f for f in files if f.endswith('.csv')]
    if csv_files:
        selected_file = st.selectbox("Pilih file data:", csv_files)
        df = pd.read_csv(os.path.join(data_dir, selected_file))
        st.dataframe(df)
    else:
        st.warning("Tidak ada file CSV di dalam folder 2026.")
else:
    st.error("Folder 2026 tidak ditemukan!")