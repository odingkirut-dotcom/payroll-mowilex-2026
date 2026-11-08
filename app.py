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
        # Urutkan file secara numerik (1, 2, 3 ... 10, 11)
        def sort_key(filename):
            try:
                return int(filename.split('.')[0])
            except:
                return 999
                
        csv_files.sort(key=sort_key)
        
        # Pilihan menu dropdown
        pilihan_menu = ["📂 Gabungkan SEMUA File (Seluruh Periode)"] + csv_files
        selected_option = st.selectbox("📂 Pilih Periode / Tampilan Data:", pilihan_menu)
        
        try:
            if selected_option == "📂 Gabungkan SEMUA File (Seluruh Periode)":
                df_list = []
                for file in csv_files:
                    f_path = os.path.join(data_dir, file)
                    temp_df = pd.read_csv(f_path, encoding='latin1')
                    temp_df['Periode_File'] = file
                    df_list.append(temp_df)
                
                df = pd.concat(df_list, ignore_index=True)
                st.success("Berhasil menggabungkan seluruh file dari semua periode secara berurutan!")
            else:
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
            
            # Buat salinan untuk diformat
            formatted_df = filtered_df.copy()
            
            # 1. Format Tanggal
            kolom_tanggal = ['Masuk', 'Keluar']
            for col in kolom_tanggal:
                if col in formatted_df.columns:
                    numeric_dates = pd.to_numeric(formatted_df[col], errors='coerce')
                    valid_dates = numeric_dates.where(numeric_dates > 1, other=pd.NA)
                    converted_dates = pd.to_datetime(valid_dates, unit='D', origin='1899-12-30', errors='coerce')
                    formatted_df[col] = converted_dates.dt.strftime('%d %b %Y').fillna('')
            
            # 2. Deteksi otomatis kolom keuangan secara menyeluruh (termasuk kolom 'total')
            keyword_uang = [
                'gaji', 'honor', 'lembur', 'terima', 'uang', 'pulsa', 'kompensasi', 
                'pph', 'bpjs', 'biaya', 'transp', 'lain', 'total'
            ]
            
            kolom_uang = []
            for col in formatted_df.columns:
                col_lower = col.lower()
                # Pastikan kolom teks identitas tidak masuk ke dalam hitungan uang
                if any(kw in col_lower for kw in keyword_uang) and col not in ['Periode_File', 'NIP', 'Nama', 'Coverage', 'Kota', 'Status', 'Posisi', 'Bank', 'Nomor']:
                    kolom_uang.append(col)
            
            # Hitung total (sum) untuk setiap kolom keuangan
            total_values = {}
            for col in kolom_uang:
                numeric_series = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)
                total_values[col] = numeric_series.sum()
            
            # Format angka finansial menjadi ribuan murni tanpa desimal bergaya accounting
            for col in kolom_uang:
                formatted_df[col] = pd.to_numeric(formatted_df[col], errors='coerce').apply(
                    lambda x: f"{x:,.0f}" if pd.notnull(x) else ""
                )
            
            # Tambahkan baris TOTAL di bagian paling bawah tabel
            if not formatted_df.empty and total_values:
                row_total = {col: "" for col in formatted_df.columns}
                first_col = formatted_df.columns[0]
                row_total[first_col] = "TOTAL Keseluruhan"
                
                for col, val in total_values.items():
                    if col in row_total:
                        row_total[col] = f"{val:,.0f}"
                
                df_total_row = pd.DataFrame([row_total])
                formatted_df = pd.concat([formatted_df, df_total_row], ignore_index=True)
            
            # Ringkasan Metrik
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Total Data Ditampilkan", value=filtered_df.shape[0])
            col2.metric(label="Total Seluruh Baris", value=df.shape[0])
            col3.metric(label="Total Kolom", value=df.shape[1])
            
            # Tampilkan tabel data interaktif
            st.subheader("📋 Tabel Data Karyawan & Rekapitulasi Total")
            st.dataframe(formatted_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")
            
    else:
        st.warning(f"Tidak ada file berformat .csv di dalam folder '{data_dir}'.")
else:
    st.error(f"Folder '{data_dir}' tidak ditemukan di repository GitHub Anda!")