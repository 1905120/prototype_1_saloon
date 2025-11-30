

import os, json, csv, requests

def write_to_csv(val1, val2, val3, val4):
    """
    Appends 3 values to a CSV file.
    If the file doesn't exist, it creates it with a header.
    """

    file_path = f'{os.path.dirname(os.path.abspath(__file__))}\\output.csv'

    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header if file is new
        # if not file_exists:
        #     writer.writerow(["Column1", "Column2", "Column3", "Column3"])

        # Append values
        writer.writerow([val1, val2, val3, val4])

script_dir = os.path.dirname(os.path.abspath(__file__))

base_url = "http://127.0.0.1:8000/api/v1/getcustomerbookingmapping/salon"

with open(f'{script_dir}\\get_cust_suggestion_100.json', 'r') as f:
    all_payloads = json.load(f)
keys = list(all_payloads.keys())

# write_to_csv("location_time", 
#     "location_without_time", 
#     "time_without_location", 
#     "without_time_without_location")

write_to_csv("location_time", "location_without_time", "time_without_location", "without_time_without_location")
for count in range(100):

    location_time_end_point = f'{base_url}/{all_payloads[keys[0]][count]["end_point"]}'
    location_time_payload = all_payloads[keys[0]][count]["payload"]

    location_without_time_end_point = f'{base_url}/{all_payloads[keys[1]][count]["end_point"]}'
    location_without_time_payload = all_payloads[keys[1]][count]["payload"]

    time_without_location_end_point = f'{base_url}/{all_payloads[keys[2]][count]["end_point"]}'
    time_without_location_payload = all_payloads[keys[2]][count]["payload"]

    without_time_without_location_end_point = f'{base_url}/{all_payloads[keys[3]][count]["end_point"]}'
    without_time_without_location_payload = all_payloads[keys[3]][count]["payload"]

    res1 = requests.post(location_time_end_point, json=location_time_payload)
    res2 = requests.post(location_without_time_end_point, json=location_without_time_payload)
    res3 = requests.post(time_without_location_end_point, json=time_without_location_payload)
    res4 = requests.post(without_time_without_location_end_point, json=without_time_without_location_payload)
    
    write_to_csv(res1.json()["err_details"]["err_msg"], 
    res2.json()["err_details"]["err_msg"], 
    res3.json()["err_details"]["err_msg"], 
    res4.json()["err_details"]["err_msg"])

