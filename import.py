#!/usr/bin/env python3
import csv
import json
import requests

JIRA_BASE_URL = "https://jira.fint.vn"   # đổi thành URL Jira của bạn
AUTH = ("sontt", "Fallen5944@@") # tài khoản admin Jira

CSV_FILE = "users.csv"
DEFAULT_PASSWORD = "TempPassw0rd!"          # mật khẩu mặc định

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Làm sạch dữ liệu
        def clean(s): 
            return (s or "").replace("\r", "").replace("\n", " ").strip()

        name = clean(row.get("name"))
        displayName = clean(row.get("displayName"))
        emailAddress = clean(row.get("emailAddress"))

        if not (name and emailAddress and displayName):
            print(f"⚠️ Bỏ qua dòng thiếu dữ liệu: {row}")
            continue

        # JSON payload
        data = {
            "name": name,
            "displayName": displayName,
            "emailAddress": emailAddress,
            "password": DEFAULT_PASSWORD,
            "notification": False   # không gửi email thông báo
        }

        print("Tạo user:", json.dumps(data, ensure_ascii=False))

        r = requests.post(
            f"{JIRA_BASE_URL}/rest/api/2/user",
            auth=AUTH,
            headers={"Accept": "application/json",
                     "Content-Type": "application/json"},
            json=data,
            timeout=15
        )

        if r.status_code == 201:
            print(f"✅ Thành công: {name}")
        else:
            print(f"❌ Lỗi ({r.status_code}): {r.text}")
