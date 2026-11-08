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

# Custom CSS untuk memadatkan padding atas secara maksimal dan mempercantik tampilan
st.markdown("""
    <style>
    /* Pangkas ruang kosong/padding atas bawaan Streamlit secara agresif */
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Perbesar font keseluruhan agar lebih nyaman di mata */
    html, body, [class*="css"] {
        font-size: 16px;
    }
    
    /* Perbesar ukuran teks pada metrik */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #C62828 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        font-weight: 600;
    }
    
    /* Kustomisasi Header & Subheader beraksen merah */
    h1, h2, h3 {
        color: #B71C1C;
    }
    
    /* Memperbesar teks isi tabel data */
    .stDataFrame {
        font-size: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

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
        
        st.markdown("---")
        
        # Membuat layout sejajar (2 Kolom: Kiri untuk Periode, Kanan untuk Pencarian)
        col_filter, col_search = st.columns([1.2, 1])
        
        with col_filter:
            st.markdown("##### ⚙️ Pengaturan Periode")
            mode_tampilan = st.radio(
                "Pilih Mode Tampilan:",
                ["📂 Pilih Per File / Gabung Semua", "📅 Rentang Periode"],
                horizontal=True,
                label_visibility="collapsed"
            )
        
        with col_search:
            st.markdown("##### 🔍 Pencarian Karyawan")
            search_query = st.text_input("Cari Karyawan:", placeholder="Ketik NIP atau Nama...", label_visibility="collapsed").strip()
        
        try:
            # Logika Pemilihan Periode
            if mode_tampilan == "📅 Rentang Periode":
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
                selected_option = st.selectbox("📂 Pilih Periode / Tampilan Data:", pilihan_menu, label_visibility="collapsed")
                
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
            
            # Terapkan Filter Pencarian NIP atau Nama
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
            
            # Buat salinan lengkap dengan baris total untuk keperluan Excel
            excel_df = formatted_df.copy()
            if not excel_df.empty and total_values:
                row_total = {col: "" for col in excel_df.columns}
                first_col = excel_df.columns[0]
                row_total[first_col] = "TOTAL Keseluruhan"
                
                for col, val in total_values.items():
                    if col in row_total:
                        row_total[col] = f"{val:,.0f}"
                
                df_total_row = pd.DataFrame([row_total])
                excel_df = pd.concat([excel_df, df_total_row], ignore_index=True)
            
            # Ringkasan Metrik di Atas Tabel
            st.markdown("---")
            col1, col2 = st.columns(2)
            col1.metric(label="Grand Total (Total Terima)", value=f"Rp {total_terima_filtered:,.0f}")
            col2.metric(label="Grand Total (PPh 21)", value=f"Rp {pph21_filtered:,.0f}")
            
            # Header Tabel & Tombol Export ke Excel
            st.markdown("---")
            col_title, col_export = st.columns([3, 1])
            with col_title:
                st.subheader("📋 Tabel Data Karyawan & Rekapitulasi Total")
            with col_export:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    excel_df.to_excel(writer, index=False, sheet_name='Data_Payroll')
                
                st.download_button(
                    label="📥 Export ke Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name="rekap_payroll_mowilex.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # --- SISTEM PAGINASI (MAKSIMAL 20 BARIS PER HALAMAN) ---
            items_per_page = 20
            total_rows = len(formatted_df)
            
            if total_rows > 0:
                total_pages = (total_rows - 1) // items_per_page + 1
                
                # Kontrol navigasi halaman di atas tabel sebelah kanan
                col_pag_info, col_pag_select = st.columns([2, 1])
                with col_pag_info:
                    st.caption(f"Menampilkan total {total_rows} data karyawan (Maks. {items_per_page} baris per halaman)")
                with col_pag_select:
                    current_page = st.number_input("Halaman:", min_value=1, max_value=total_pages, value=1, step=1)
                
                # Potong data sesuai halaman aktif
                start_idx_page = (current_page - 1) * items_per_page
                end_idx_page = start_idx_page + items_per_page
                paginated_df = formatted_df.iloc[start_idx_page:end_idx_page].copy()
                
                # Jika ini halaman terakhir, sisipkan baris rekapitulasi total di bagian bawah tabel
                if current_page == total_pages and total_values:
                    row_total = {col: "" for col in formatted_df.columns}
                    first_col = formatted_df.columns[0]
                    row_total[first_col] = "TOTAL Keseluruhan"
                    
                    for col, val in total_values.items():
                        if col in row_total:
                            row_total[col] = f"{val:,.0f}"
                    
                    df_total_row = pd.DataFrame([row_total])
                    paginated_df = pd.concat([paginated_df, df_total_row], ignore_index=True)
                
                # Tampilkan tabel data interaktif per halaman
                st.dataframe(paginated_df, use_container_width=True, height=450, hide_index=True)
            else:
                st.info("Tidak ada data karyawan yang ditemukan.")
            
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