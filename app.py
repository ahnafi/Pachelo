from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import pandas as pd
import pickle
import re
from tensorflow.keras.models import load_model
import os
import numpy as np
from sklearn.preprocessing import LabelEncoder


app = Flask(__name__)


# Fungsi untuk parsing log
def parse_apache_log_line(line):
    log_pattern = re.compile(
        r'(?P<ip>\S+) (?P<dash1>\S+) (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" (?P<status>\d{3}) (?P<size>\d+) "(?P<referrer>[^\"]+)" "(?P<user_agent>[^\"]+)"')
    match = log_pattern.match(line)
    return match.groupdict() if match else None


def convert_log_to_csv(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()
    log_data = [parse_apache_log_line(line) for line in lines]
    log_data = [entry for entry in log_data if entry]
    df = pd.DataFrame(log_data)
    csv_file = log_file.replace('.log', '.csv')
    df.to_csv(csv_file, index=False)
    remove_file(log_file)
    return csv_file


def remove_file(name_file):
    if os.path.isfile(name_file):
        os.remove(name_file)


# Load model, encoder, and scaler



@app.route('/')
def upload_file():
    if request.args.get('up'):
        remove_file(request.args.get('up'))
        remove_file(request.args.get('res'))
    return render_template('upload.html')


@app.route('/predict', methods=['POST'])
# def predict():
#     os.makedirs('./uploads', exist_ok=True)
#     os.makedirs('./results', exist_ok=True)

#     if 'file' not in request.files:
#         return render_template('notfound.html')
#     file = request.files['file']
#     if file.filename == '':
#         return render_template('notfound.html')

#     filepath = './uploads/' + file.filename
#     file.save(filepath)

#     if file.filename.endswith('.log'):
#         filepath = convert_log_to_csv(filepath)

#     model = load_model('ids.keras')
#     with open('label_encoders.pkl', 'rb') as f:
#         label_encoders = pickle.load(f)
#     with open('scaler.pkl', 'rb') as f:
#         scaler = pickle.load(f)

#     new_data = pd.read_csv(filepath)
#     features = ['status', 'user_agent']
#     if not all(feature in new_data.columns for feature in features):
#         return render_template('notfound.html')

#     X_new = new_data[features]

#     # Terapkan Label Encoding
#     for col in features:
#         if col in label_encoders:
#             X_new[col] = label_encoders[col].transform(X_new[col].astype(str))

#     # Standarisasi data baru
#     X_new_scaled = scaler.transform(X_new)

#     # Prediksi menggunakan model yang dimuat
#     predictions = (model.predict(X_new_scaled) > 0.5).astype("int32").flatten()
#     new_data['is_anomaly'] = predictions

#     # Simpan hasil ke file baru
#     output_path = "./results/hasilScan-" + file.filename.removesuffix('.log') + ".csv"
#     new_data.to_csv(output_path, index=False)

#     # Hitung jumlah anomali per IP
#     anomaly_counts = new_data[new_data['is_anomaly'] == 1].groupby('ip').size().sort_values(ascending=False).head(10)
#     top_anomalies = anomaly_counts.reset_index(name='anomali_counter')

#     # Mengubah DataFrame menjadi list of dictionaries
#     top_anomalies_list = top_anomalies.to_dict(orient='records')

#     model.save('ids.keras')
#     with open('label_encoders.pkl', 'wb') as f:
#         pickle.dump(label_encoders,f)
#     with open('scaler.pkl', 'wb') as f:
#         pickle.dump(scaler,f)

#     return render_template('result.html', top_anomalies=top_anomalies_list, result=output_path,upload=filepath)
def predict():
    os.makedirs('./uploads', exist_ok=True)
    os.makedirs('./results', exist_ok=True)

    if 'file' not in request.files:
        return render_template('notfound.html')
    file = request.files['file']
    if file.filename == '':
        return render_template('notfound.html')

    filepath = './uploads/' + file.filename
    file.save(filepath)

    if file.filename.endswith('.log'):
        filepath = convert_log_to_csv(filepath)

    model = load_model('newModelvv.keras')
    with open('newLabelEncoders.pkl', 'rb') as f:
        label_encoders = pickle.load(f)
    with open('newScalervv.pkl', 'rb') as f:
        scaler = pickle.load(f)

    new_data = pd.read_csv(filepath)
    features = ['user_agent', 'status']

    if not all(feature in new_data.columns for feature in features):
        return render_template('notfound.html')

    # Urutkan fitur sesuai dengan urutan pelatihan
    X_new = new_data[features]

    # Terapkan Label Encoding dengan Incremental dan Unknown Handling
    for col in features:
        if col in label_encoders:  # Jika encoder untuk kolom ini sudah ada
            le = label_encoders[col]
            # Tambahkan label baru ke encoder
            new_classes = set(X_new[col].unique()) - set(le.classes_)
            if new_classes:
                print(f"Menambahkan label baru untuk '{col}': {new_classes}")
                le.classes_ = np.concatenate([le.classes_, np.array(list(new_classes), dtype=object)])  # Update classes_

            # Transform data
            X_new[col] = X_new[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        else:
            # Jika encoder baru, buat dan simpan
            le = LabelEncoder()
            X_new[col] = le.fit_transform(X_new[col].astype(str))
            label_encoders[col] = le

    # Standarisasi data baru
    X_new_scaled = scaler.transform(X_new)

    # Prediksi menggunakan model yang dimuat
    predictions = (model.predict(X_new_scaled) > 0.5).astype("int32").flatten()
    new_data['is_anomaly'] = predictions

    # Simpan hasil ke file baru
    output_path = "./results/hasilScan-" + file.filename.removesuffix('.log') + ".csv"
    new_data.to_csv(output_path, index=False)

    # Hitung jumlah anomali per IP
    anomaly_counts = new_data[new_data['is_anomaly'] == 1].groupby('ip').size().sort_values(ascending=False).head(10)
    top_anomalies = anomaly_counts.reset_index(name='anomali_counter')
    print(top_anomalies)

    # Mengubah DataFrame menjadi list of dictionaries
    top_anomalies_list = top_anomalies.to_dict(orient='records')

    model.save('newModelvv.keras')
    with open('newLabelEncoders.pkl', 'wb') as f:
        pickle.dump(label_encoders, f)
    with open('newScalervv.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    return render_template('result.html', top_anomalies=top_anomalies_list, result=output_path, upload=filepath)


@app.route('/download')
def download_file():
    filename = request.args.get('filename')
    return send_from_directory(directory='.', path=filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
