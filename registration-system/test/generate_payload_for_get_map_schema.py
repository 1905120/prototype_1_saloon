import json
import random
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(f'{script_dir}\\customers_100.json', 'r') as f:
    rec = json.load(f)

with open(f'{script_dir}\\request_times.json', 'r') as f:
    time_stamp = json.load(f)


def random_lat_lon():
    latitude = round(random.uniform(-90, 90), 6)    # 6 decimal places for precision
    longitude = round(random.uniform(-180, 180), 6) # 6 decimal places for precision
    return latitude, longitude

service = [
  "hair-cutting",
  "hair-coloring",
  "hair-styling",
  "facial-treatment",
  "manicure",
  "pedicure",
  "massage-therapy",
  "waxing"
]

payload = {
    "location_time": [],
    "location_without_time" : [],
    "time_without_location" : [],
    "without_time_without_location" : []
}


for each_cust in rec:
    requires_service = random.choice(service)
    phone = each_cust["phone"]
    end_point = f'{requires_service}/{phone}'
    latitude, longitude = random_lat_lon()
    request_payload1 = {
        "request_time" : random.choice(time_stamp),
        "location" : {
            "latitude" : latitude,
            "longitude" : longitude
        }
    }
    request_payload2 = {
        "location" : {
            "latitude" : latitude,
            "longitude" : longitude
        }
    }
    request_payload3 = {
        "request_time" : random.choice(time_stamp)
    }
    request_payload4 = {}

    payload["location_time"].append({"end_point": end_point, "payload" : request_payload1})
    payload["location_without_time"].append({"end_point": end_point, "payload" : request_payload2})
    payload["time_without_location"].append({"end_point": end_point, "payload" : request_payload3})
    payload["without_time_without_location"].append({"end_point": end_point, "payload" : request_payload4})


with open(f'{script_dir}\\get_cust_suggestion_100.json', 'w') as f:
    json.dump(payload, f)
