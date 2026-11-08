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

# Custom CSS untuk merapikan tata letak dan ukuran pagination di bawah
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }
    h1 {
        font-size: 1.4rem !important;
        margin-bottom: 0px !important;
    }
    .stDataFrame {
        font-size: 15px !important;
    }
    [data-testid="stMetricValue"] {
        color: #C62828 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Payroll & Absensi Mowilex 2026")

# Direktori data
honor_dir = "Mowilex/Honor/2026"
insentif_dir = "Mowilex/Insentif/2026"

# Kumpulkan semua file CSV dari kedua folder
all_files_info = []

if os.path.exists(honor_dir):
    for f in sorted(os.listdir(honor_dir)):
        if f.endswith('.csv'):
            all_files_info.append((f, os.path.join(honor_dir, f)))

if os.path.exists(insentif_dir):
    for f in sorted(os.listdir(insentif_dir)):
        if f.endswith('.csv'):
            all_files_info.append((f, os.path.join(insentif_dir, f)))

if all_files_info:
    def sort_key(item):
        filename = item[0]
        try:
            prefix = filename.split()[0]
            return float(prefix)
        except:
            return 999.0

    all_files_info.sort(key=sort_key)
    csv_files_only = [item[0] for item in all_files_info]
    file_path_map = {item[0]: item[1] for item in all_files_info}

    # Layout sejajar atas (Periode & Pencarian)
    col_filter, col_search = st.columns([1.3, 1])
    
    with col_filter:
        mode_tampilan = st.radio(
            "Mode Tampilan:",
            ["📂 Pilih Per File / Gabung Semua", "📅 Rentang Periode"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with col_search:
        search_query = st.text_input("Cari Karyawan:", placeholder="🔍 Ketik NIP atau Nama...", label_visibility="collapsed").strip()
    
    try:
        if mode_tampilan == "📅 Rentang Periode":
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                start_period = st.selectbox("Dari Periode:", csv_files_only, index=0, label_visibility="collapsed")
            with col_p2:
                end_period = st.selectbox("Sampai Periode:", csv_files_only, index=len(csv_files_only)-1, label_visibility="collapsed")
            
            start_idx = sort_key((start_period, ''))
            end_idx = sort_key((end_period, ''))
            
            selected_files = [f for f in csv_files_only if start_idx <= sort_key((f, '')) <= end_idx]
            if not selected_files:
                selected_files = [start_period]
            
            df_list = []
            for file in selected_files:
                f_path = file_path_map[file]
                temp_df = pd.read_csv(f_path, encoding='latin1')
                temp_df.columns = temp_df.columns.str.strip()
                temp_df['Periode_File'] = file.replace('.csv', '')
                df_list.append(temp_df)
            
            df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        else:
            pilihan_menu = ["📂 Gabungkan SEMUA File (Seluruh Periode)"] + csv_files_only
            selected_option = st.selectbox("Pilih Periode:", pilihan_menu, label_visibility="collapsed")
            
            if selected_option == "📂 Gabungkan SEMUA File (Seluruh Periode)":
                df_list = []
                for file in csv_files_only:
                    f_path = file_path_map[file]
                    temp_df = pd.read_csv(f_path, encoding='latin1')
                    temp_df.columns = temp_df.columns.str.strip()
                    temp_df['Periode_File'] = file.replace('.csv', '')
                    df_list.append(temp_df)
                
                df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
            else:
                f_path = file_path_map[selected_option]
                df = pd.read_csv(f_path, encoding='latin1')
                df.columns = df.columns.str.strip()
                df['Periode_File'] = selected_option.replace('.csv', '')
        
        # --- ATUR POSISI KOLOM KHUSUS INSENTIF SEBELUM 'Biaya ( F - 04 )' ---
        if not df.empty:
            cols = list(df.columns)
            target_col = None
            for c in cols:
                if 'biaya' in c.lower() and ('f-04' in c.lower() or 'f - 04' in c.lower()):
                    target_col = c
                    break
            
            # Deteksi kolom insentif (misal: Insentif Booster Daily Meals, dll)
            kolom_insentif = [c for c in cols if 'insentif' in c.lower() or 'booster' in c.lower()]
            
            if target_col and kolom_insentif:
                for col_ins in kolom_insentif:
                    if col_ins in cols:
                        cols.remove(col_ins)
                target_idx = cols.index(target_col)
                for i, col_ins in enumerate(kolom_insentif):
                    cols.insert(target_idx + i, col_ins)
                df = df[cols]

        if search_query and not df.empty:
            name_col = 'Nama' if 'Nama' in df.columns else ('Nama.1' if 'Nama.1' in df.columns else None)
            if name_col:
                filtered_df = df[
                    df['NIP'].astype(str).str.contains(search_query, case=False, na=False) |
                    df[name_col].astype(str).str.contains(search_query, case=False, na=False)
                ]
            else:
                filtered_df = df[df['NIP'].astype(str).str.contains(search_query, case=False, na=False)]
        else:
            filtered_df = df
        
        # Deteksi otomatis kolom keuangan
        keyword_uang = [
            'gaji', 'honor', 'lembur', 'terima', 'uang', 'pulsa', 'kompensasi', 
            'pph', 'bpjs', 'biaya', 'transp', 'lain', 'total', 'insentif'
        ]
        
        kolom_uang = []
        if not df.empty:
            for col in df.columns:
                col_lower = col.lower()
                if 'status pembayaran' in col_lower:
                    continue
                if any(kw in col_lower for kw in keyword_uang) and col not in ['Periode_File', 'NIP', 'Nama', 'Nama.1', 'Coverage', 'Kota', 'Status', 'Posisi', 'Bank', 'Nomor']:
                    kolom_uang.append(col)
        
        total_terima_filtered = 0
        pph21_filtered = 0
        
        if not filtered_df.empty:
            for col in filtered_df.columns:
                col_lower = col.lower()
                if 'total terima' in col_lower:
                    total_terima_filtered += pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).sum()
                elif 'pph' in col_lower:
                    pph21_filtered += pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).sum()
        
        total_values = {}
        for col in kolom_uang:
            if not filtered_df.empty and col in filtered_df.columns:
                numeric_series = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)
                total_values[col] = numeric_series.sum()
        
        formatted_df = filtered_df.copy() if not filtered_df.empty else pd.DataFrame()
        
        # Konversi tanggal
        kolom_tanggal = ['Masuk', 'Keluar']
        for col in kolom_tanggal:
            if not formatted_df.empty and col in formatted_df.columns:
                numeric_dates = pd.to_numeric(formatted_df[col], errors='coerce')
                valid_dates = numeric_dates.where(numeric_dates > 1, other=pd.NA)
                converted_dates = pd.to_datetime(valid_dates, unit='D', origin='1899-12-30', errors='coerce')
                formatted_df[col] = converted_dates.dt.strftime('%d %b %Y').fillna('')
        
        # Format kolom keuangan
        for col in kolom_uang:
            if not formatted_df.empty and col in formatted_df.columns:
                formatted_df[col] = pd.to_numeric(formatted_df[col], errors='coerce').apply(
                    lambda x: f"{x:,.0f}" if pd.notnull(x) else ""
                )
        
        # Tangani kolom Status Pembayaran
        if not formatted_df.empty:
            for col in formatted_df.columns:
                if 'status pembayaran' in col.lower():
                    formatted_df[col] = formatted_df[col].fillna('-').astype(str)
        
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
        
        # Ringkasan Metrik di Atas
        m1, m2 = st.columns(2)
        m1.metric(label="Grand Total (Total Terima)", value=f"Rp {total_terima_filtered:,.0f}")
        m2.metric(label="Grand Total (PPh 21)", value=f"Rp {pph21_filtered:,.0f}")
        
        # Header Tabel & Tombol Export ke Excel (Sejajar)
        col_title, col_export = st.columns([3, 1])
        with col_title:
            st.markdown("##### 📋 Tabel Data Karyawan & Rekapitulasi")
        with col_export:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                excel_df.to_excel(writer, index=False, sheet_name='Data_Payroll')
            
            st.download_button(
                label="📥 Export ke Excel",
                data=buffer.getvalue(),
                file_name="rekap_payroll_mowilex.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # --- LOGIKA PAGINASI (MAKSIMAL 20 BARIS) ---
        items_per_page = 20
        total_rows = len(formatted_df)
        
        if total_rows > 0:
            total_pages = (total_rows - 1) // items_per_page + 1
            
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = total_pages
            
            start_idx_page = (st.session_state.current_page - 1) * items_per_page
            end_idx_page = start_idx_page + items_per_page
            paginated_df = formatted_df.iloc[start_idx_page:end_idx_page].copy()
            
            if st.session_state.current_page == total_pages and total_values:
                row_total = {col: "" for col in formatted_df.columns}
                first_col = formatted_df.columns[0]
                row_total[first_col] = "TOTAL Keseluruhan"
                
                for col, val in total_values.items():
                    if col in row_total:
                        row_total[col] = f"{val:,.0f}"
                
                df_total_row = pd.DataFrame([row_total])
                paginated_df = pd.concat([paginated_df, df_total_row], ignore_index=True)
            
            # Render Tabel
            st.dataframe(paginated_df, use_container_width=True, height=400, hide_index=True)
            
            # Kontrol Paginasi di Bagian Bawah Tabel
            col_info, col_space, col_nav = st.columns([2, 1, 1.5])
            with col_info:
                st.caption(f"Total Data: {total_rows} | Halaman {st.session_state.current_page} dari {total_pages}")
            with col_nav:
                st.session_state.current_page = st.number_input(
                    "Pilih Halaman:", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=st.session_state.current_page, 
                    step=1, 
                    label_visibility="collapsed"
                )
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
                    height=350
                )
                
                st.altair_chart(chart_altair, use_container_width=True)
            else:
                st.info("Kolom untuk grafik tidak ditemukan.")
        else:
            st.info("Tidak ada data untuk ditampilkan dalam grafik.")
        
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
        
else:
    st.warning("Tidak ada file berformat .csv di dalam folder Honor maupun Insentif.")