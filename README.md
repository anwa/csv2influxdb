# HealthManager Pro Data Conversion Script

This Python script processes CSV files exported from beurer HealthManager Pro, extracts relevant data for weight and blood pressure, and converts it into a format suitable for InfluxDB. The script identifies the latest CSV file based on the date in the filename, processes the data, and outputs it to a new CSV file in the InfluxDB line protocol format.

## Features

- Automatically identifies the latest CSV file based on the date in the filename.
- Extracts and processes weight and blood pressure data.
- Converts date and time to Unix timestamps.
- Outputs the processed data in InfluxDB line protocol format.
- Deletes the processed CSV files after conversion.

## Prerequisites

- Python 3.x

## Usage

1. Place the script in the directory containing the HealthManager Pro CSV files.
2. Ensure the CSV files follow the naming pattern: `HealthManager Pro Export - DD.MM.YYYY - DD.MM.YYYY.csv`.
3. Run the script:

```bash
python csv2influxdb.py
```

The script will create an output file named `influxdb-import.csv` in the same directory.

## Script Details

### Importing Required Libraries

```python
import sys
import os
import io
import csv
import re
from datetime import datetime
```

### Defining Input and Output Files

```python
influxdb_output_file = "influxdb-import.csv"
directory = "./"
pattern = r"HealthManager Pro Export - \d{2}\.\d{2}\.\d{4} - (\d{2}\.\d{2}\.\d{4})\.csv"
files = os.listdir(directory)
matching_files = [f for f in files if re.match(pattern, f)]
```

### Extracting Date from Filename

```python
def extract_date(filename):
    match = re.search(pattern, filename)
    if match:
        return datetime.strptime(match.group(1), "%d.%m.%Y")
    return None

newest_file = max(matching_files, key=extract_date)
input_file = os.path.join(directory, newest_file)
```

### Converting Date and Time to Unix Timestamp

```python
def datetime_to_unix(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    return int(dt.timestamp())
```

### Reading the Input File

```python
try:
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
except Exception as e:
    print(f"Error reading file '{input_file}': {e}")
    sys.exit()
```

### Extracting Data for Weight and Blood Pressure

```python
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

gewicht_data = extract_gewicht_data(lines)
blutdruck_data = extract_blutdruck_data(lines)
gewicht_data_str = "\n".join(gewicht_data)
blutdruck_data_str = "\n".join(blutdruck_data)
gewicht_data_io = io.StringIO(gewicht_data_str)
blutdruck_data_io = io.StringIO(blutdruck_data_str)
```

### Processing and Converting Data

```python
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
            print(f"Error converting date and time: {date} {time_of_day} - {e}")
            continue
        influxdb_line = (
            f"andreas,entity_id=weight,friendly_name=Gewicht "
            f"weight={weight},BMI={bmi},fat={fat},water={water},muscles={muscles},bones={bones} {timestamp}\n"
        )
        outfile.write(influxdb_line)

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
            print(f"Error converting date and time: {date} {time_of_day} - {e}")
            continue
        influxdb_line = (
            f"andreas,entity_id=blood_pressure,friendly_name=Blutdruck "
            f"sys={sys},dia={dia},pulse={pulse},MAD={mad} {timestamp}\n"
        )
        outfile.write(influxdb_line)
```

### Creating the Output File

```python
with open(influxdb_output_file, "w", encoding="utf-8", newline="\n") as outfile:
    reader = csv.DictReader(gewicht_data_io, delimiter=";")
    process_gewicht_data(reader, outfile)
    reader = csv.DictReader(blutdruck_data_io, delimiter=";")
    process_blutdruck_data(reader, outfile)
```

### Deleting Processed Files

```python
for file in matching_files:
    os.remove(os.path.join(directory, file))

print("CSV file has been created and converted to InfluxDB format successfully.")
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- HealthManager Pro for providing the data export functionality.
- The Python community for the libraries and tools used in this script.
