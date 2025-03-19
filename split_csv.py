import csv

# Define the input and output file names
input_file = "HealthManager Pro Export - 01.01.2019 - 19.03.2025.csv"
gewicht_output_file = "HealthManager_Gewicht.csv"
blutdruck_output_file = "HealthManager_Blutdruck.csv"

# Read the content of the input file
with open(input_file, "r", encoding="utf-8") as file:
    lines = file.readlines()


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

# Write the extracted data to the respective output files
with open(gewicht_output_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=";")
    for row in gewicht_data:
        writer.writerow(row.split(";"))

with open(blutdruck_output_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=";")
    for row in blutdruck_data:
        writer.writerow(row.split(";"))

print("CSV files have been created successfully.")
