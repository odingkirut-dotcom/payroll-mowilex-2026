import os
import pandas as pd
import streamlit as st

# Konfigurasi halaman agar tetap rapi seperti semula
st.set_page_config(
    page_title="Dashboard Payroll & Absensi Mowilex 2026", layout="wide"
)

# Direktori data utama honor
data_dir = "Mowilex/Honor/2026"
insentif_dir = "Mowilex/Insentif/2026"

# Cek apakah folder utama ada
if not os.path.exists(data_dir):
    st.error(
        f"Folder direktori '{data_dir}' tidak ditemukan di repository GitHub!"
    )
    st.stop()

# List file CSV honor
files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
files.sort()

st.title("📊 Dashboard Payroll & Absensi Mowilex 2026")

# --- Bagian Filter / Pilihan File (Sesuai aslinya) ---
# (Pastikan bagian pemilih file Anda tetap dipanggil di sini, misal selected_option)
# Contoh placeholder pemilihan file:
selected_option = st.selectbox("Pilih Periode File CSV", ["Gabungkan SEMUA File (Seluruh Periode)"] + files)

# Fungsi untuk memuat dan menggabungkan data
@st.cache_data
def load_data(selected_file):
    if selected_file == "Gabungkan SEMUA File (Seluruh Periode)":
        df_list = []
        for f in files:
            f_path = os.path.join(data_dir, f)
            temp_df = pd.read_csv(f_path, encoding="latin1")
            temp_df.columns = temp_df.columns.str.strip()
            df_list.append(temp_df)
        df_honor = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        
        # Gabungkan seluruh file insentif jika mode gabung semua
        df_insentif_list = []
        if os.path.exists(insentif_dir):
            for f_ins in os.listdir(insentif_dir):
                if f_ins.endswith(".csv"):
                    f_ins_path = os.path.join(insentif_dir, f_ins)
                    temp_ins = pd.read_csv(f_ins_path, encoding="latin1")
                    temp_ins.columns = temp_ins.columns.str.strip()
                    df_insentif_list.append(temp_ins)
        df_insentif = pd.concat(df_insentif_list, ignore_index=True) if df_insentif_list else pd.DataFrame()
        
    else:
        # Load file honor per periode
        f_path = os.path.join(data_dir, selected_file)
        df_honor = pd.read_csv(f_path, encoding="latin1")
        df_honor.columns = df_honor.columns.str.strip()
        
        # Load file insentif yang sesuai dengan nama filenya
        # Misal nama file insentif disesuaikan (misal: "1. Insentif Januari 2026.csv")
        insentif_filename = selected_file.replace("1. 16 Desember", "1. Insentif 16 Desember") # sesuaikan polanya jika perlu
        # Atau cari file insentif yang mengandung teks serupa
        matched_ins_files = [f for f in os.listdir(insentif_dir) if f.endswith(".csv")] if os.path.exists(insentif_dir) else []
        
        df_insentif = pd.DataFrame()
        for f_ins in matched_ins_files:
            # Pencocokan sederhana berdasarkan nomor/bulan file
            if selected_file.split(" ")[0] in f_ins:
                f_ins_path = os.path.join(insentif_dir, f_ins)
                df_insentif = pd.read_csv(f_ins_path, encoding="latin1")
                df_insentif.columns = df_insentif.columns.str.strip()
                break

    # --- PROSES GABUNG (MERGE) BERDASARKAN NIP ---
    if not df_honor.empty and not df_insentif.empty and 'NIP' in df_honor.columns and 'NIP' in df_insentif.columns:
        # Hapus kolom duplikat dari insentif agar tidak kembar (kecuali NIP)
        kolom_dup = ['Nama', 'NPWP', 'Posisi', 'Coverage', 'Kota', 'Status', 'Masuk', 'Keluar', 'Biaya Transfer', 'PPh21']
        df_insentif_clean = df_insentif.drop(columns=[col for col in kolom_dup if col in df_insentif.columns], errors='ignore')
        
        # Left join agar data honor utama tetap aman
        df_honor = pd.merge(df_honor, df_insentif_clean, on='NIP', how='left', suffixes=('', '_insentif'))
        
        # Posisikan kolom insentif baru tepat setelah 'Total Terima'
        cols = list(df_honor.columns)
        kolom_insentif_baru = [c for c in df_insentif_clean.columns if c != 'NIP' and c not in cols[:cols.index('Total Terima')]]
        
        for col_ins in kolom_insentif_baru:
            if col_ins in cols:
                cols.remove(col_ins)
            if 'Total Terima' in cols:
                idx_total = cols.index('Total Terima')
                cols.insert(idx_total + 1, col_ins)
        df_honor = df_honor[cols]

    return df_honor

# Memuat dataframe utama
df = load_data(selected_option)

# --- Bagian Metrik / Angka Atas (Grand Total) ---
# (Pastikan perhitungan metrik Total Terima dan PPh 21 Anda tetap berjalan di sini)
col1, col2 = st.columns(2)
if 'Total Terima' in df.columns:
    total_terima = df['Total Terima'].sum()
    col1.metric("Grand Total (Total Terima)", f"Rp {total_terima:,.0f}")

if 'PPh21' in df.columns:
    total_pph = df['PPh21'].sum()
    col2.metric("Grand Total (PPh 21)", f"Rp {total_pph:,.0f}")

# --- Tabel Data Karyawan & Rekapitulasi ---
st.subheader("📋 Tabel Data Karyawan & Rekapitulasi")
st.dataframe(df, use_container_width=True)