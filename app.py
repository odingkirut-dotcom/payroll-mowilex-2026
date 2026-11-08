import streamlit as st
import pandas as pd
import os
import altair as alt
import io

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
        # Urutkan file secara numerik (1, 2, 3 ... 10, 11) berdasarkan angka depan
        def sort_key(filename):
            try:
                return int(filename.split('.')[0])
            except:
                return 999
                
        csv_files.sort(key=sort_key)
        
        # Opsi Pilihan Tampilan Langsung di Halaman Utama
        st.markdown("---")
        st.subheader("⚙️ Pengaturan Periode & Tampilan Data")
        
        mode_tampilan = st.radio(
            "Pilih Mode Tampilan:",
            ["📂 Pilih Per File / Gabung Semua", "📅 Rentang Periode (Dari - Sampai)"],
            horizontal=True
        )
        
        try:
            if mode_tampilan == "📅 Rentang Periode (Dari - Sampai)":
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    start_period = st.selectbox("Dari Periode:", csv_files, index=0)
                with col_p2:
                    end_period = st.selectbox("Sampai Periode:", csv_files, index=len(csv_files)-1)
                
                start_idx = sort_key(start_period)
                end_idx = sort_key(end_period)
                
                selected_files = [f for f in csv_files if start_idx <= sort_key(f) <= end_idx]
                if not selected_files:
                    selected_files = [start_period]
                
                df_list = []
                for file in selected_files:
                    f_path = os.path.join(data_dir, file)
                    temp_df = pd.read_csv(f_path, encoding='latin1')
                    temp_df['Periode_File'] = file
                    df_list.append(temp_df)
                
                df = pd.concat(df_list, ignore_index=True)
            else:
                pilihan_menu = ["📂 Gabungkan SEMUA File (Seluruh Periode)"] + csv_files
                selected_option = st.selectbox("📂 Pilih Periode / Tampilan Data:", pilihan_menu)
                
                if selected_option == "📂 Gabungkan SEMUA File (Seluruh Periode)":
                    df_list = []
                    for file in csv_files:
                        f_path = os.path.join(data_dir, file)
                        temp_df = pd.read_csv(f_path, encoding='latin1')
                        temp_df['Periode_File'] = file
                        df_list.append(temp_df)
                    
                    df = pd.concat(df_list, ignore_index=True)
                else:
                    file_path = os.path.join(data_dir, selected_option)
                    df = pd.read_csv(file_path, encoding='latin1')
                    df['Periode_File'] = selected_option
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
            
            # Deteksi otomatis kolom keuangan secara menyeluruh
            keyword_uang = [
                'gaji', 'honor', 'lembur', 'terima', 'uang', 'pulsa', 'kompensasi', 
                'pph', 'bpjs', 'biaya', 'transp', 'lain', 'total'
            ]
            
            kolom_uang = []
            for col in df.columns:
                col_lower = col.lower()
                if any(kw in col_lower for kw in keyword_uang) and col not in ['Periode_File', 'NIP', 'Nama', 'Coverage', 'Kota', 'Status', 'Posisi', 'Bank', 'Nomor']:
                    kolom_uang.append(col)
            
            # Hitung nilai Grand Total untuk 'Total Terima' dan 'PPh21'
            total_terima_filtered = 0
            pph21_filtered = 0
            
            for col in filtered_df.columns:
                col_lower = col.lower()
                if 'total terima' in col_lower:
                    total_terima_filtered = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).sum()
                elif 'pph' in col_lower:
                    pph21_filtered = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).sum()
            
            # Hitung total (sum) untuk seluruh kolom keuangan di baris bawah tabel
            total_values = {}
            for col in kolom_uang:
                numeric_series = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)
                total_values[col] = numeric_series.sum()
            
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
            
            # 2. Format angka finansial menjadi ribuan murni tanpa desimal bergaya accounting
            for col in kolom_uang:
                if col in formatted_df.columns:
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
            
            # Ringkasan Metrik di Atas Tabel
            col1, col2 = st.columns(2)
            col1.metric(label="Grand Total (Total Terima)", value=f"Rp {total_terima_filtered:,.0f}")
            col2.metric(label="Grand Total (PPh 21)", value=f"Rp {pph21_filtered:,.0f}")
            
            # Header Tabel & Tombol Export ke Excel
            st.markdown("---")
            col_title, col_export = st.columns([3, 1])
            with col_title:
                st.subheader("📋 Tabel Data Karyawan & Rekapitulasi Total")
            with col_export:
                # Konversi DataFrame yang ditampilkan menjadi file Excel (in-memory buffer)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    formatted_df.to_excel(writer, index=False, sheet_name='Data_Payroll')
                
                st.download_button(
                    label="📥 Export ke Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name="rekap_payroll_mowilex.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Tampilkan tabel data interaktif
            st.dataframe(formatted_df, use_container_width=True)
            
            # --- BAGIAN DIAGRAM BATANG NORMALISASI PERSENTASE (MERAH) ---
            st.markdown("---")
            st.subheader("📊 Diagram Batang Persentase Kontribusi Periode")
            
            if 'Periode_File' in filtered_df.columns and not filtered_df.empty:
                target_grafik = None
                for c in ['Total Terima', 'Total']:
                    if c in filtered_df.columns:
                        target_grafik = c
                        break
                
                if target_grafik:
                    df_chart = filtered_df.copy()
                    df_chart[target_grafik] = pd.to_numeric(df_chart[target_grafik], errors='coerce').fillna(0)
                    
                    chart_data = df_chart.groupby('Periode_File')[target_grafik].sum().reset_index()
                    chart_data['Sort_ID'] = chart_data['Periode_File'].apply(sort_key)
                    chart_data = chart_data.sort_values('Sort_ID')
                    
                    # Normalisasi nilai ke bentuk persentase (total semua periode = 100%)
                    sum_all = chart_data[target_grafik].sum()
                    if sum_all > 0:
                        chart_data['Persentase'] = (chart_data[target_grafik] / sum_all) * 100
                    else:
                        chart_data['Persentase'] = 0.0
                        
                    chart_data['Formatted_Pct'] = chart_data['Persentase'].apply(lambda x: f"{x:.2f}%")
                    
                    chart_altair = alt.Chart(chart_data).mark_bar(color='#E53935').encode(
                        x=alt.X('Periode_File:N', sort=list(chart_data['Periode_File']), title='Periode File'),
                        y=alt.Y('Persentase:Q', title='Kontribusi (%)', axis=alt.Axis(format='.1f')),
                        tooltip=[
                            alt.Tooltip('Periode_File:N', title='Periode'),
                            alt.Tooltip('Formatted_Pct:N', title='Kontribusi')
                        ]
                    ).properties(
                        height=400
                    )
                    
                    st.altair_chart(chart_altair, use_container_width=True)
                else:
                    st.info("Kolom untuk grafik tidak ditemukan.")
            else:
                st.info("Tidak ada data untuk ditampilkan dalam grafik.")
            
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")
            
    else:
        st.warning(f"Tidak ada file berformat .csv di dalam folder '{data_dir}'.")
else:
    st.error(f"Folder '{data_dir}' tidak ditemukan di repository GitHub Anda!")