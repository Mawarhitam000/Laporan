from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

CSV_FILE = 'laporan.csv'

# Inisialisasi file jika belum ada
def initialize_csv():
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame({
            'jenis hewan': [
                'burung terkukur', 'babi', 'kadal', 'kambing',
                'sapi', 'ular', 'burung elang', 'burung merpati'
            ],
            'zona 1': [0]*8,
            'zona 2': [0]*8,
            'zona 3': [0]*8,
            'zona 4': [0]*8,
            'zona 5': [0]*8,
            'hari': ['']*8,
            'tanggal': ['']*8,
            'waktu': ['']*8,
            'total': [0]*8
        })
        df.loc[len(df.index)] = [None]*9 + [0]  # Baris kosong untuk tanggal terakhir
        df.loc[len(df.index)] = ['TOTAL'] + [0]*8 + [0]  # Baris total
        df.to_csv(CSV_FILE, index=False)

@app.route('/', methods=['GET', 'POST'])
def laporan():
    initialize_csv()
    df = pd.read_csv(CSV_FILE)

    zona_cols = [col for col in df.columns if col.startswith('zona')]
    hewan_list = df['jenis hewan'].dropna()
    hewan_list = hewan_list[~hewan_list.str.upper().isin(['TOTAL'])].unique().tolist()

    if request.method == 'POST':
        nama_hewan = request.form['nama_hewan'].strip()
        zona = request.form['zona'].strip()
        jumlah = int(request.form['jumlah'])

        if zona not in df.columns:
            df[zona] = 0
            zona_cols.append(zona)

        now = datetime.now()
        hari = now.strftime('%A')
        tanggal = now.strftime('%Y-%m-%d')
        waktu = now.strftime('%H:%M:%S')

        if nama_hewan in df['jenis hewan'].values:
            idx = df[df['jenis hewan'] == nama_hewan].index[0]
        else:
            idx = len(df) - 1  # sebelum baris TOTAL
            df.loc[idx+1:] = df.loc[idx:].shift(1)
            df.loc[idx] = [nama_hewan] + [0]*(len(df.columns)-1)

        df.at[idx, zona] = df.at[idx, zona] + jumlah
        df.at[idx, 'hari'] = hari
        df.at[idx, 'tanggal'] = tanggal
        df.at[idx, 'waktu'] = waktu
        df.at[idx, 'total'] = df.loc[idx, zona_cols].sum()

        # Update total keseluruhan
        df.loc[df['jenis hewan'] == 'TOTAL', zona] = df.loc[df['jenis hewan'] != 'TOTAL', zona].sum()
        df.loc[df['jenis hewan'] == 'TOTAL', 'total'] = df.loc[df['jenis hewan'] != 'TOTAL', zona_cols].sum().sum()

        df.to_csv(CSV_FILE, index=False)

    return render_template('form.html', hewan_list=hewan_list, zona_list=zona_cols)

if __name__ == '__main__':
    app.run(debug=True)
