import sys
import os
import io
import csv
import re
from datetime import datetime

# Define the input and output file names
# input_file = "HealthManager Pro Export.csv"
influxdb_output_file = "influxdb-import.csv"

# Verzeichnis, in dem die Dateien gespeichert sind
directory = "./"

# Muster für den Dateinamen
pattern = r"HealthManager Pro Export - \d{2}\.\d{2}\.\d{4} - (\d{2}\.\d{2}\.\d{4})\.csv"

# Liste aller Dateien im Verzeichnis
files = os.listdir(directory)

# Filtere die Dateien, die dem Muster entsprechen
matching_files = [f for f in files if re.match(pattern, f)]


# Funktion zum Extrahieren des Datums aus dem Dateinamen
def extract_date(filename):
    match = re.search(pattern, filename)
    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")
    return None


# Finde die neueste Datei
newest_file = max(matching_files, key=extract_date)

# Pfad zur neuesten Datei
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
    print(f"Fehler beim Lesen der Datei '{input_file}': {e}")
    sys.exit()


# Function to extract relevant data for Gewicht
def extract_gewicht_data(lines):
    gewicht_data = []
    start_collecting = False
    for line in lines:
        if "Gewicht" in line:
            start_collecting = True
            continue
        if start_collecting:
            if line.strip() == "":
                break
            if "Körperfett" in line or (line.strip() and line.split(";")[4].strip()):
                gewicht_data.append(line.strip())
    return gewicht_data


# Function to extract relevant data for Blutdruck
def extract_blutdruck_data(lines):
    blutdruck_data = []
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
            blutdruck_data.append(line.strip())
    return blutdruck_data


# Extract data for Gewicht and Blutdruck
gewicht_data = extract_gewicht_data(lines)
blutdruck_data = extract_blutdruck_data(lines)

# Convert the list of lines to a string
gewicht_data_str = "\n".join(gewicht_data)
blutdruck_data_str = "\n".join(blutdruck_data)

# Use io.StringIO to create a file-like object from the string
gewicht_data_io = io.StringIO(gewicht_data_str)
blutdruck_data_io = io.StringIO(blutdruck_data_str)


# Function to extract and convert relevant data for Gewicht
def process_gewicht_data(reader, outfile):
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
            print(
                f"Fehler beim Konvertieren von Datum und Uhrzeit: {date} {time_of_day} - {e}"
            )
            continue
        influxdb_line = (
            f"andreas,entity_id=weight,friendly_name=Gewicht "
            f"weight={weight},BMI={bmi},fat={fat},water={water},muscles={muscles},bones={bones} {timestamp}\n"
        )
        outfile.write(influxdb_line)


# Function to extract and convert relevant data for Blutdruck
def process_blutdruck_data(reader, outfile):
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
            print(
                f"Fehler beim Konvertieren von Datum und Uhrzeit: {date} {time_of_day} - {e}"
            )
            continue
        influxdb_line = (
            f"andreas,entity_id=blood_pressure,friendly_name=Blutdruck "
            f"sys={sys},dia={dia},pulse={pulse},MAD={mad} {timestamp}\n"
        )
        outfile.write(influxdb_line)


# Create the InfluxDB output file and process the data
with open(influxdb_output_file, "w", encoding="utf-8", newline="\n") as outfile:
    reader = csv.DictReader(gewicht_data_io, delimiter=";")
    process_gewicht_data(reader, outfile)
    reader = csv.DictReader(blutdruck_data_io, delimiter=";")
    process_blutdruck_data(reader, outfile)

# Löschen aller Dateien, die dem Muster entsprechen
for file in matching_files:
    os.remove(os.path.join(directory, file))

print("CSV file has been created and converted to InfluxDB format successfully.")
