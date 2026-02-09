from flask import Flask, render_template, request, jsonify
import pymongo
from datetime import datetime, timedelta
import base64, os, uuid

# ================= APP =================
app = Flask(__name__)

# ================= DATABASE =================
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["campus_parking"]

# ================= STORAGE FOTO =================
FACE_DIR = "static/faces"
os.makedirs(FACE_DIR, exist_ok=True)

# ================= HELPER =================
def utc_to_wib(t):
    return t + timedelta(hours=7)

def parse_qr(raw):
    try:
        if raw.startswith("{") and "|" in raw:
            p = raw.replace("{", "").replace("}", "").split("|")
            return {
                "npm_display": p[1],
                "nama": p[2]
            }
    except:
        pass
    return {
        "npm_display": raw,
        "nama": "Mahasiswa"
    }

def save_base64_image(data):
    try:
        header, encoded = data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        filename = f"{uuid.uuid4().hex}.jpg"
        path = os.path.join(FACE_DIR, filename)
        with open(path, "wb") as f:
            f.write(img_bytes)
        return f"/static/faces/{filename}"
    except:
        return None

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")

# ================= SCAN =================
@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    raw = data.get("npm", "").strip()
    foto_base64 = data.get("foto")

    info = parse_qr(raw)
    now = datetime.utcnow()

    foto_path = save_base64_image(foto_base64) if foto_base64 else None

    active = db.parking_logs.find_one({
        "npm_raw": raw,
        "status": "MASUK"
    })

    # ====== KELUAR ======
    if active:
        diff = now - active["timestamp"]
        total = int(diff.total_seconds())
        durasi = f"{total//3600}j {(total%3600)//60}m"

        db.parking_logs.update_one(
            {"_id": active["_id"]},
            {"$set": {
                "status": "KELUAR",
                "out_time": now,
                "duration": durasi
            }}
        )

        db.parking_slots.update_one(
            {"slot_id": active["slot_id"]},
            {"$set": {
                "status": "KOSONG",
                "npm_raw": None
            }}
        )

        return jsonify({
            "type": "KELUAR",
            "nama": info["nama"],
            "slot": active["slot_id"]
        })

    # ====== MASUK ======
    slot = db.parking_slots.find_one({"status": "KOSONG"})
    if not slot:
        return jsonify({
            "type": "FULL",
            "nama": "Parkiran Penuh"
        })

    db.parking_slots.update_one(
        {"_id": slot["_id"]},
        {"$set": {
            "status": "TERISI",
            "npm_raw": raw
        }}
    )

    db.parking_logs.insert_one({
        "npm_raw": raw,
        "npm_display": info["npm_display"],
        "nama": info["nama"],
        "slot_id": slot["slot_id"],
        "status": "MASUK",
        "timestamp": now,
        "out_time": None,
        "duration": "-",
        "foto": foto_path
    })

    return jsonify({
        "type": "MASUK",
        "nama": info["nama"],
        "slot": slot["slot_id"]
    })

# ================= LOGS =================
@app.route("/get_logs")
def get_logs():
    logs = list(
        db.parking_logs.find()
        .sort("timestamp", -1)
        .limit(10)
    )

    data = []
    for l in logs:
        data.append({
            "nama": l["nama"],
            "npm_display": l["npm_display"],
            "slot": l["slot_id"],
            "waktu_masuk": utc_to_wib(l["timestamp"]).strftime("%H:%M:%S"),
            "waktu_keluar": "-" if not l["out_time"]
                else utc_to_wib(l["out_time"]).strftime("%H:%M:%S"),
            "duration": l["duration"],
            "status": l["status"],
            "foto": l.get("foto")
        })

    return jsonify(data)

# ================= SLOT =================
@app.route("/api/slots")
def slots():
    return jsonify([
        {
            "slot": s["slot_id"],
            "status": s["status"]
        }
        for s in db.parking_slots.find().sort("slot_id", 1)
    ])

# ================= RESET =================
@app.route("/reset", methods=["POST"])
def reset_system():
    # hapus semua log
    db.parking_logs.delete_many({})

    # reset semua slot
    db.parking_slots.update_many(
        {},
        {"$set": {
            "status": "KOSONG",
            "npm_raw": None
        }}
    )

    # hapus semua foto
    for f in os.listdir(FACE_DIR):
        try:
            os.remove(os.path.join(FACE_DIR, f))
        except:
            pass

    return jsonify({
        "status": "ok",
        "message": "Sistem berhasil direset"
    })

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
