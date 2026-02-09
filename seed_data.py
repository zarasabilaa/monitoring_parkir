import pymongo
from datetime import datetime

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["campus_parking"]

db.parking_logs.drop()
db.parking_slots.drop()

slots = []
for row in ["A", "B"]:
    for i in range(1, 6):
        slots.append({
            "slot_id": f"{row}{i}",
            "status": "KOSONG",
            "npm_raw": None,
            "last_update": datetime.utcnow()
        })

db.parking_slots.insert_many(slots)

print("✅ Database bersih")
print("✅ Slot parkir siap")
