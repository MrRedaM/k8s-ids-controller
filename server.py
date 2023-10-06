from fastapi import FastAPI, UploadFile
import shutil
import os
import csv
import requests
import uvicorn


app = FastAPI()

ip_address = "192.168.56.5"
port = "30400"
result_file_path = '/nfs/classification/classification.csv'


def send_post_request(ip, p, data):
    url = f"http://{ip}:{p}"  # Construct the URL with the IP address and port
    response = requests.post(url, data=str(data))
    return response


def read_csv(file_path):
    data = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data


def write_to_csv(file_path, row):
    file_exists = os.path.exists(file_path)

    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if file_exists:
            # Check if the first column exists in the CSV file
            with open(file_path, 'r', newline='') as read_file:
                reader = csv.reader(read_file)
                for existing_row in reader:
                    if existing_row and existing_row[0] == row[0]:
                        # Update the value in the second column
                        existing_row[1] = row[1]
                        return
        # If the CSV file doesn't exist, create a new one and write the row
        writer.writerow(row)


@app.post("/analyse-csv/")
async def upload_pcap(file: UploadFile):
    # Check if the uploaded file is a PCAP file
    if file.filename.endswith('.csv'):
        # Save the uploaded PCAP file to a temporary directory
        base_filename = os.path.splitext(file.filename)[0]
        with open(f"{base_filename}.csv", "wb") as csv_file:
            shutil.copyfileobj(file.file, csv_file)
            csv_data = read_csv(csv_file)
            response = send_post_request(ip_address, port, csv_data)
            result_value = response.text if response.status_code == 200 else '0'
            write_to_csv(result_file_path, [base_filename, result_value])




        if response.status_code == 200:
            return {"message": "CSV file uploaded, analyzed, and result updated successfully."}
        else:
            return {"message": "Failed to send CSV file to the target server."}
    else:
        return {"message": "Invalid file format. Please upload a CSV file."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
