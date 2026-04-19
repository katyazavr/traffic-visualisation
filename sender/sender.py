import pandas as pd
import time
import requests

url = 'http://127.0.0.1:5000/packet'

df = pd.read_csv('sender/ip_addresses.csv')
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df.sort_values(by='timestamp')
print(1)
last_timestamp = df.loc[0, 'timestamp']
for row in df.itertuples():
    current_timestamp = row.timestamp
    packet = {
        "ip": row.ip_address,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "timestamp": current_timestamp,
        "s_mark": row.suspicious
    }
    if last_timestamp == current_timestamp:
        response = requests.post(url, json=packet)
        print(response.status_code)
    else:
        time.sleep(current_timestamp - last_timestamp)
        response = requests.post(url, json=packet)
        print(response.status_code)
    last_timestamp = current_timestamp
