import sys
import os
import io
import csv
import re
import logging
from datetime import datetime

# Define the user name and output file name
user_name = "andreas"
influxdb_output_file = "influxdb-import.csv"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Directory where the files are stored
directory = "./"

# Pattern for the filename
pattern = r"HealthManager Pro Export - \d{2}\.\d{2}\.\d{4} - (\d{2}\.\d{2}\.\d{4})\.csv"

# List all files in the directory
files = os.listdir(directory)

# Filter the files that match the pattern
matching_files = [f for f in files if re.match(pattern, f)]


# Function to extract the date from the filename
def extract_date(filename):
    match = re.search(pattern, filename)
    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")
    return None


# Find the newest file
try:
    newest_file = max(matching_files, key=extract_date)
except ValueError:
    logging.error("No files matching the pattern were found.")
    sys.exit(1)

# Path to the newest file
input_file = os.path.join(directory, newest_file)


# Function to convert date and time to Unix timestamp
def datetime_to_unix(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    return int(dt.timestamp())


# Read the content of the input file
try:
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
except Exception as e:
    logging.error(f"Error reading file '{input_file}': {e}")
    sys.exit(1)


# Function to extract relevant data for weight
def extract_weight_data(lines):
    weight_data = []
    start_collecting = False
    for line in lines:
        if "Gewicht" in line:
            start_collecting = True
            continue
        if start_collecting:
            if line.strip() == "":
                break
            if "Körperfett" in line or (line.strip() and line.split(";")[4].strip()):
                weight_data.append(line.strip())
    return weight_data


# Function to extract relevant data for blood pressure
def extract_blood_pressure_data(lines):
    blood_pressure_data = []
    start_collecting = False
    for line in lines:
        if "Blutdruck" in line:
            start_collecting = True
            continue
        if start_collecting:
            if line.strip() == "" or not line.split(";")[0].strip():
                break
            if "MAD =" in line or "Ø =" in line:
                continue
            blood_pressure_data.append(line.strip())
    return blood_pressure_data


# Extract data for weight and blood pressure
weight_data = extract_weight_data(lines)
blood_pressure_data = extract_blood_pressure_data(lines)

# Convert the list of lines to a string
weight_data_str = "\n".join(weight_data)
blood_pressure_data_str = "\n".join(blood_pressure_data)

# Use io.StringIO to create a file-like object from the string
weight_data_io = io.StringIO(weight_data_str)
blood_pressure_data_io = io.StringIO(blood_pressure_data_str)


# Function to extract and convert relevant data for weight
def process_weight_data(reader, outfile):
    for row in reader:
        date = row["Datum"]
        time_of_day = row["Uhrzeit"]
        weight = row["kg"]
        bmi = row["BMI"]
        fat = row["Körperfett"]
        water = row["Wasser"]
        muscles = row["Muskeln"]
        bones = row["Knochen"]
        try:
            timestamp = datetime_to_unix(date, time_of_day)
        except ValueError as e:
            logging.error(f"Error converting date and time: {date} {time_of_day} - {e}")
            continue
        influxdb_line = (
            f"{user_name},entity_id=weight,friendly_name=Gewicht "
            f"weight={weight},BMI={bmi},fat={fat},water={water},muscles={muscles},bones={bones} {timestamp}\n"
        )
        outfile.write(influxdb_line)


# Function to extract and convert relevant data for blood pressure
def process_blood_pressure_data(reader, outfile):
    for row in reader:
        date = row["Datum"]
        time_of_day = row["Uhrzeit"]
        sys = row["Sys"]
        dia = row["Dia"]
        pulse = row["Puls"]
        mad = row["MAD"]
        try:
            timestamp = datetime_to_unix(date, time_of_day)
        except ValueError as e:
            logging.error(f"Error converting date and time: {date} {time_of_day} - {e}")
            continue
        influxdb_line = (
            f"{user_name},entity_id=blood_pressure,friendly_name=Blutdruck "
            f"sys={sys},dia={dia},pulse={pulse},MAD={mad} {timestamp}\n"
        )
        outfile.write(influxdb_line)


# Create the InfluxDB output file and process the data
with open(influxdb_output_file, "w", encoding="utf-8", newline="\n") as outfile:
    reader = csv.DictReader(weight_data_io, delimiter=";")
    process_weight_data(reader, outfile)
    reader = csv.DictReader(blood_pressure_data_io, delimiter=";")
    process_blood_pressure_data(reader, outfile)

# Delete all files that match the pattern
for file in matching_files:
    os.remove(os.path.join(directory, file))

print("CSV file has been created and converted to InfluxDB format successfully.")
