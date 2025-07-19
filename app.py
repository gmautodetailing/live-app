from flask import Flask, render_template, request, redirect
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("GM_Bookings").sheet1

SERVICES = {
    "Exterior Detail": 90,
    "Full Detail": 150,
    "Standard Membership": 90,
    "Premium Membership": 150
}

def get_availability(service):
    booked_slots = sheet.get_all_records()
    duration = SERVICES[service]
    today = datetime.date.today()
    dates = [(today + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    slots_per_day = []

    for date in dates:
        day_slots = []
        start_hour = 9
        end_hour = 20
        step = 30
        for hour in range(start_hour * 60, end_hour * 60, step):
            start = datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(minutes=hour)
            end = start + datetime.timedelta(minutes=duration)
            overlap = any(
                datetime.datetime.strptime(b["Date"], "%Y-%m-%d") == start.date() and
                int(b["Start"].split(":")[0]) * 60 + int(b["Start"].split(":")[1]) <= hour < 
                int(b["End"].split(":")[0]) * 60 + int(b["End"].split(":")[1])
                for b in booked_slots
            )
            if not overlap:
                day_slots.append(start.strftime("%H:%M"))
        slots_per_day.append((date, day_slots))
    return slots_per_day

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        postcode = request.form["postcode"]
        service = request.form["service"]
        return redirect(f"/book?name={name}&phone={phone}&postcode={postcode}&service={service}")
    return render_template("index.html")

@app.route("/book")
def book():
    name = request.args.get("name")
    phone = request.args.get("phone")
    postcode = request.args.get("postcode")
    service = request.args.get("service")
    slots = get_availability(service)
    return render_template("calendar.html", name=name, phone=phone, postcode=postcode, service=service, slots=slots)

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    phone = request.form["phone"]
    postcode = request.form["postcode"]
    service = request.form["service"]
    date = request.form["date"]
    time = request.form["time"]
    duration = SERVICES[service]
    end = datetime.datetime.strptime(time, "%H:%M") + datetime.timedelta(minutes=duration)
    sheet.append_row([name, phone, postcode, service, date, time, end.strftime("%H:%M")])
    return "Booking confirmed!"

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Required for Render
    app.run(host="0.0.0.0", port=port)
