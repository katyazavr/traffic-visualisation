import json
import queue
import threading
from collections import deque

from flask import Blueprint, Response, jsonify, request

from geo import region_for_packet

bp = Blueprint("routes", __name__)

MAX_PACKETS = 5000
RECENT_WINDOW = 10

packets = deque(maxlen=MAX_PACKETS)
stream_subscribers = []
storage_lock = threading.Lock()


def _broadcast(packet):
    dead_queues = []
    for subscriber in stream_subscribers:
        try:
            subscriber.put_nowait(packet)
        except queue.Full:
            dead_queues.append(subscriber)
    for subscriber in dead_queues:
        if subscriber in stream_subscribers:
            stream_subscribers.remove(subscriber)


@bp.route("/")
def index():
    return jsonify({"status": "ok", "message": "Traffic backend is running"})


@bp.route("/packet", methods=["POST"])
def packet():
    data = request.get_json(silent=True) or {}
    required_keys = {"ip", "latitude", "longitude", "timestamp", "s_mark"}
    if not required_keys.issubset(data):
        return jsonify({"error": "Invalid packet payload"}), 400

    lat = float(data["latitude"])
    lng = float(data["longitude"])
    normalized_packet = {
        "ip": str(data["ip"]),
        "latitude": lat,
        "longitude": lng,
        "timestamp": int(float(data["timestamp"])),
        "s_mark": int(float(data["s_mark"])),
        "region": region_for_packet(lat, lng),
    }

    with storage_lock:
        packets.append(normalized_packet)
    _broadcast(normalized_packet)
    return jsonify({"status": "received"}), 201


@bp.route("/packet", methods=["GET"])
def get_packets():
    limit = min(int(request.args.get("limit", 100)), 500)
    with storage_lock:
        items = list(packets)[-limit:]
    return jsonify(items)


@bp.route("/stats", methods=["GET"])
def stats():
    with storage_lock:
        snapshot = list(packets)

    region_counts = {}
    suspicious = 0
    for item in snapshot:
        key = item.get("region") or "Unknown"
        region_counts[key] = region_counts.get(key, 0) + 1
        suspicious += 1 if item["s_mark"] == 1 else 0

    top_regions = sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify(
        {
            "total_packets": len(snapshot),
            "suspicious_packets": suspicious,
            "top_regions": [{"region": loc, "count": count} for loc, count in top_regions],
            "recent_window_seconds": RECENT_WINDOW,
        }
    )


@bp.route("/stream", methods=["GET"])
def stream():
    def event_stream():
        subscriber = queue.Queue(maxsize=1000)
        stream_subscribers.append(subscriber)
        try:
            while True:
                item = subscriber.get()
                yield f"data: {json.dumps(item)}\n\n"
        except GeneratorExit:
            if subscriber in stream_subscribers:
                stream_subscribers.remove(subscriber)

    return Response(event_stream(), mimetype="text/event-stream")
