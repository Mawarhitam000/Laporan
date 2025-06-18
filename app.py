from flask import Flask, render_template, request, redirect
import pandas as pd
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Daftar awal jenis hewan
hewan_list_awal = [
    'burung terkukur', 'babi', 'kadal', 'kambing',
    'sapi', 'ular', 'burung elang', 'burung merpati'
]

# Nama file Excel
excel_file = 'laporan_hewan.xlsx'

def kirim_ke_google_apps_script(data):
    url = 'https://script.google.com/macros/s/AKfycbxgfZlUe3QM6qVmsIYZzEoG5Wkt_I3OH9ZEFLUOxSr1LszZauNaP8K7unzVkMZUQqMj/exec'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=data)
        print("Status:", response.status_code)
        print("Respon:", response.text)
        return response.status_code == 200
    except Exception as e:
        print("Gagal mengirim ke Google Apps Script:", e)
        return False


@app.route('/', methods=['GET', 'POST'])
def laporan():
    # Cek apakah file sudah ada
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        zona_kolom = [col for col in df.columns if col.startswith('zona')]
    else:
        zona_kolom = ['zona 1', 'zona 2', 'zona 3', 'zona 4', 'zona 5']
        df = pd.DataFrame({
            'jenis hewan': hewan_list_awal,
            **{z: [0]*len(hewan_list_awal) for z in zona_kolom},
            'hari': ['']*len(hewan_list_awal),
            'tanggal': ['']*len(hewan_list_awal),
            'waktu': ['']*len(hewan_list_awal),
            'total': [0]*len(hewan_list_awal)
        })

    if request.method == 'POST':
        nama_hewan = request.form['nama_hewan'].strip().lower()
        zona = request.form['zona'].strip().lower()
        jumlah = int(request.form['jumlah'])

        now = datetime.now()
        hari = now.strftime('%A')
        tanggal = now.strftime('%Y-%m-%d')
        waktu = now.strftime('%H:%M:%S')

        # Hilangkan baris TOTAL jika ada
        df = df[df['jenis hewan'].str.lower() != 'total']

        # Tambah zona baru jika belum ada
        if zona not in df.columns:
            df.insert(len(zona_kolom) + 1, zona, [0]*len(df))
            zona_kolom.append(zona)

        # Tambah hewan baru jika belum ada
        if nama_hewan not in df['jenis hewan'].str.lower().values:
            new_row = {
                'jenis hewan': nama_hewan,
                **{z: 0 for z in zona_kolom},
                'hari': '',
                'tanggal': '',
                'waktu': '',
                'total': 0
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Update data
        idx = df[df['jenis hewan'].str.lower() == nama_hewan].index[0]
        df.at[idx, zona] += jumlah
        df.at[idx, 'hari'] = hari
        df.at[idx, 'tanggal'] = tanggal
        df.at[idx, 'waktu'] = waktu
        df.at[idx, 'total'] = df.loc[idx, zona_kolom].sum()

        # Hitung ulang baris TOTAL
        total_zona = {z: df[z].sum() for z in zona_kolom}
        total_semua = df['total'].sum()
        total_row = {
            'jenis hewan': 'TOTAL',
            **total_zona,
            'hari': '',
            'tanggal': '',
            'waktu': '',
            'total': total_semua
        }

        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        df.to_excel(excel_file, index=False)
        
        # Kirim data ke Google Apps Script
        kirim_ke_google_apps_script({
        "jenis_hewan": nama_hewan,
        "zona": zona,
        "jumlah": jumlah,
        "hari": hari,
        "tanggal": tanggal,
        "waktu": waktu
})


        return redirect('/')

    # Tampilkan hewan untuk form (tanpa "total")
    hewan_list = df[df['jenis hewan'].str.lower() != 'total']['jenis hewan'].tolist()

    return render_template('form.html', hewan_list=hewan_list, zona_list=zona_kolom)

if __name__ == '__main__':
    app.run(debug=True)
