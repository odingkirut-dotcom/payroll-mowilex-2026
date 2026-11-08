import glob
import os
import pandas as pd
import gradio as gr

# ==========================================
# BACA LANGSUNG DARI FOLDER LOKAL PROJECT './2026/'
# ==========================================
folder_path = './2026/'

# Cari semua file .csv di dalam folder 2026
all_files = glob.glob(os.path.join(folder_path, '*.csv'))
print(f'Ditemukan {len(all_files)} file CSV di folder.')


# Fungsi pintar untuk mengurutkan file secara numerik berdasarkan angka di awal nama file
def ambil_nomor_urut(path_file):
  nama_file = os.path.basename(path_file)
  import re

  match = re.match(r'(\d+)', nama_file)
  return int(match.group(1)) if match else 999


if len(all_files) == 0:
  print('⚠️ Peringatan: Tidak ada file CSV ditemukan di folder ./2026/.')
  df_master = pd.DataFrame()
else:
  sorted_files = sorted(all_files, key=ambil_nomor_urut)

  df_list = []
  for file in sorted_files:
    try:
      df_temp = pd.read_csv(file, encoding='utf-8')
    except UnicodeDecodeError:
      df_temp = pd.read_csv(file, encoding='latin-1')

    nama_file_asli = os.path.basename(file).replace('.csv', '')
    df_temp['Periode_File'] = nama_file_asli
    df_list.append(df_temp)

  df_master = pd.concat(df_list, ignore_index=True)
  print(f'✅ Berhasil memuat total baris: {len(df_master):,}')


def ambil_nomor_urut_str(nama_periode):
  import re

  match = re.match(r'(\d+)', str(nama_periode))
  return int(match.group(1)) if match else 999


# Temukan kolom total terima & pph 21 secara otomatis
col_total_terima = None
for col in df_master.columns:
  if 'total' in col.lower() and 'terima' in col.lower():
    col_total_terima = col
    break
if not col_total_terima:
  col_total_terima = (
      df_master.columns[-1] if not df_master.empty else 'Total Terima'
  )

col_pph21 = None
for col in df_master.columns:
  col_l = col.lower()
  if 'pph' in col_l and (
      '21' in col_l or 'pribadi' in col_l or 'karyawan' in col_l
  ):
    col_pph21 = col
    break


# ==========================================
# APLIKASI WEB INTERAKTIF GRADIO
# ==========================================
def filter_data(periode_awal, periode_akhir, keyword_pencarian):
  if df_master.empty:
    return (
        pd.DataFrame(),
        '### ⚠️ Tidak ada data yang dimuat.',
        None,
        pd.DataFrame(),
    )

  filtered_df = df_master.copy()

  if 'Periode_File' in filtered_df.columns:
    semua_periode = sorted(
        list(filtered_df['Periode_File'].unique()), key=ambil_nomor_urut_str
    )

    if periode_awal in semua_periode and periode_akhir in semua_periode:
      idx_awal = semua_periode.index(periode_awal)
      idx_akhir = semua_periode.index(periode_akhir)

      if idx_awal > idx_akhir:
        idx_awal, idx_akhir = idx_akhir, idx_awal

      periode_terpilih = semua_periode[idx_awal : idx_akhir + 1]
      filtered_df = filtered_df[
          filtered_df['Periode_File'].isin(periode_terpilih)
      ]

  if keyword_pencarian and keyword_pencarian.strip() != '':
    keyword = keyword_pencarian.strip().lower()
    kolom_cocok = [
        col
        for col in filtered_df.columns
        if any(k in col.lower() for k in ['nip', 'nama', 'name', 'nik', 'id'])
    ]

    if kolom_cocok:
      kondisi = False
      for col in kolom_cocok:
        kondisi = kondisi | filtered_df[col].astype(str).str.lower().str.contains(
            keyword, na=False
        )
      filtered_df = filtered_df[kondisi]
    else:
      kondisi = False
      for col in filtered_df.select_dtypes(include=['object', 'string']).columns:
        kondisi = kondisi | filtered_df[col].astype(str).str.lower().str.contains(
            keyword, na=False
        )
      filtered_df = filtered_df[kondisi]

  # Data untuk Grafik Batang (%)
  if not filtered_df.empty and col_total_terima in filtered_df.columns:
    df_chart = (
        filtered_df.groupby('Periode_File')[col_total_terima]
        .sum()
        .reset_index()
    )
    df_chart['Urut'] = df_chart['Periode_File'].apply(ambil_nomor_urut_str)
    df_chart = df_chart.sort_values('Urut')

    total_keseluruhan = df_chart[col_total_terima].sum()
    if total_keseluruhan > 0:
      df_chart['Persentase'] = (
          df_chart[col_total_terima] / total_keseluruhan
      ) * 100
      df_chart['Persentase'] = df_chart['Persentase'].round(2)
    else:
      df_chart['Persentase'] = 0

    def persingkat_label(nama):
      import re

      m = re.match(r'(\d+)\.', str(nama))
      if m:
        num = int(m.group(1))
        return f'P-{num:02d}'
      return str(nama)

    df_chart['Periode'] = df_chart['Periode_File'].apply(persingkat_label)
    df_chart = df_chart.sort_values('Urut')
    df_chart = df_chart[['Periode', 'Persentase']]
  else:
    df_chart = pd.DataFrame(columns=['Periode', 'Persentase'])

  # Formatting Tabel & Baris Total
  if not filtered_df.empty:
    df_display = filtered_df.copy()

    for col in df_display.columns:
      col_lower = col.lower()
      if 'masuk' in col_lower or 'keluar' in col_lower:

        def konversi_tanggal(val):
          if pd.isna(val) or val == 0 or str(val).strip() in ['0', '']:
            return ''
          try:
            num_val = float(val)
            if 30000 < num_val < 60000:
              return (
                  pd.to_datetime('1899-12-30')
                  + pd.to_timedelta(num_val, unit='D')
              ).strftime('%d %b %Y')
          except ValueError:
            pass
          dt = pd.to_datetime(val, errors='coerce')
          if pd.notnull(dt):
            return dt.strftime('%d %b %Y')
          return str(val)

        df_display[col] = df_display[col].apply(konversi_tanggal)

    cols_list = df_display.columns.tolist()
    mulai_format = False
    for col in cols_list:
      col_l = col.lower()
      if 'gaji' in col_l or 'pokok' in col_l:
        mulai_format = True
      if mulai_format:
        if pd.api.types.is_numeric_dtype(df_display[col]):
          df_display[col] = df_display[col].apply(
              lambda x: f'{int(x):,}'
              .replace(',', '.')
              if pd.notnull(x) and not pd.isna(x)
              else ''
          )

    row_total = {col: '' for col in df_display.columns}
    kolom_teks = df_display.select_dtypes(
        include=['object', 'string']
    ).columns.tolist()
    if kolom_teks:
      row_total[kolom_teks[0]] = 'TOTAL KESELURUHAN'
    else:
      row_total[df_display.columns[0]] = 'TOTAL KESELURUHAN'

    kolom_dikecualikan = ['npwp', 'tahun', 'masuk', 'periode_file']
    for col in filtered_df.select_dtypes(include=['number']).columns:
      col_lower = col.lower()
      is_gaji_dasar = (
          'gaji' in col_lower
          and 'terima' not in col_lower
          and 'total' not in col_lower
      )
      is_harian_dasar = (
          'harian' in col_lower
          and 'total' not in col_lower
          and 'terima' not in col_lower
      )
      is_dikecualikan = any(exc in col_lower for exc in kolom_dikecualikan)

      if not (is_gaji_dasar or is_harian_dasar or is_dikecualikan):
        val_sum = filtered_df[col].sum()
        row_total[col] = f'{int(val_sum):,}'.replace(',', '.')

    df_display = pd.concat(
        [df_display, pd.DataFrame([row_total])], ignore_index=True
    )
  else:
    df_display = filtered_df

  path_output_excel = '/tmp/data_payroll_mowilex.xlsx'
  with pd.ExcelWriter(path_output_excel, engine='openpyxl') as writer:
    df_display.to_excel(writer, index=False, sheet_name='Payroll_Mowilex')
    worksheet = writer.sheets['Payroll_Mowilex']
    for col in worksheet.columns:
      max_len = 0
      col_letter = col[0].column_letter
      for cell in col:
        if cell.value is not None:
          max_len = max(max_len, len(str(cell.value)))
      worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

  total_baris = len(filtered_df)
  grand_total_terima_str = '0'
  if not filtered_df.empty and col_total_terima in filtered_df.columns:
    total_val = filtered_df[col_total_terima].sum()
    grand_total_terima_str = f'{int(total_val):,}'.replace(',', '.')

  grand_total_pph21_str = '0'
  if not filtered_df.empty and col_pph21 and col_pph21 in filtered_df.columns:
    pph_val = filtered_df[col_pph21].sum()
    grand_total_pph21_str = f'{int(pph_val):,}'.replace(',', '.')

  info_teks = (
      f'### 📊 Ringkasan Data\n'
      f'- **Total Baris Ditemukan:** `{total_baris:,}` baris\n'
      f'- **Grand Total Terima:** `Rp {grand_total_terima_str}`\n'
      f'- **Grand Total PPh 21:** `Rp {grand_total_pph21_str}`'
  )
  return df_display, info_teks, path_output_excel, df_chart


daftar_periode = (
    sorted(list(df_master['Periode_File'].unique()), key=ambil_nomor_urut_str)
    if 'Periode_File' in df_master.columns
    else []
)
default_awal = daftar_periode[0] if daftar_periode else None
default_akhir = daftar_periode[-1] if daftar_periode else None

initial_df, initial_info, initial_file, initial_chart = filter_data(
    default_awal, default_akhir, ''
)

custom_theme = gr.themes.Soft(primary_hue='red', secondary_hue='rose')

with gr.Blocks() as demo:
  with gr.Row():
    with gr.Column(scale=3):
      gr.Markdown('# 📊 Dashboard & Pencarian Data Payroll Mowilex 2026')
      gr.Markdown(
          'Aplikasi web interaktif untuk data payroll dan absensi karyawan.'
      )
    with gr.Column(scale=2):
      chart_view = gr.BarPlot(
          value=initial_chart,
          x='Periode',
          y='Persentase',
          title='Kontribusi Total Terima per Periode (%)',
          x_title='Periode',
          y_title='Persentase (%)',
          height=180,
          y_lim=[0, None],
      )

  output_info = gr.Markdown(value=initial_info)

  with gr.Row():
    dropdown_awal = gr.Dropdown(
        choices=daftar_periode, value=default_awal, label='Dari Periode'
    )
    dropdown_akhir = gr.Dropdown(
        choices=daftar_periode, value=default_akhir, label='Sampai Periode'
    )
    input_pencarian = gr.Textbox(
        label='Cari NIP atau Nama',
        placeholder='Ketik NIP atau Nama yang ingin dicari...',
    )

  tabel_view = gr.DataFrame(value=initial_df, max_height=500, interactive=False)

  with gr.Row():
    btn_download = gr.File(
        label=(
            '📥 Download Data Excel (.xlsx) - Lebar Kolom Otomatis Rapih'
        ),
        value=initial_file,
    )

  inputs_list = [dropdown_awal, dropdown_akhir, input_pencarian]
  outputs_list = [tabel_view, output_info, btn_download, chart_view]

  dropdown_awal.change(fn=filter_data, inputs=inputs_list, outputs=outputs_list)
  dropdown_akhir.change(fn=filter_data, inputs=inputs_list, outputs=outputs_list)
  input_pencarian.input(
      fn=filter_data, inputs=inputs_list, outputs=outputs_list
  )

# Khusus untuk Hugging Face, jalankan dengan demo.launch() saja tanpa share=True
demo.launch()