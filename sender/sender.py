import os
import time
from pathlib import Path

import pandas as pd
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5000/packet")
DATASET_PATH = Path(__file__).resolve().parent / "ip_addresses.csv"
REQUEST_TIMEOUT = 5


def send_packets():
    dataframe = pd.read_csv(DATASET_PATH)
    dataframe.columns = dataframe.columns.str.strip().str.lower().str.replace(" ", "_")
    dataframe = dataframe.sort_values(by="timestamp").reset_index(drop=True)

    if dataframe.empty:
        print("No rows in CSV file")
        return

    # Give backend time to start in compose setups.
    time.sleep(2)

    last_timestamp = int(dataframe.loc[0, "timestamp"])
    sent_count = 0
    for row in dataframe.itertuples():
        current_timestamp = int(row.timestamp)
        sleep_seconds = max(0, current_timestamp - last_timestamp)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

        packet = {
            "ip": row.ip_address,
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "timestamp": current_timestamp,
            "s_mark": int(float(row.suspicious)),
        }

        try:
            response = requests.post(BACKEND_URL, json=packet, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            sent_count += 1
        except requests.RequestException as exc:
            print(f"Failed to send packet {packet['ip']}: {exc}")

        last_timestamp = current_timestamp
        if sent_count % 100 == 0:
            print(f"Sent {sent_count} packets")

    print(f"Finished sending {sent_count} packets")


if __name__ == "__main__":
    send_packets()
