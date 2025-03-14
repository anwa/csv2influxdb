import csv
import time
from datetime import datetime


# Funktion zum Konvertieren von Datum und Uhrzeit in Unix-Zeitstempel
def datetime_to_unix(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    return int(dt.timestamp())


# Einlesen der CSV-Datei
input_file = "./HealthManager_Gewicht.csv"
output_file = "./influxdb-import.csv"

with open(input_file, "r", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    # Erstellen der neuen CSV-Datei
    with open(output_file, "w", encoding="utf-8", newline="\n") as outfile:
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

            # Formatieren der Zeile für InfluxDB
            influxdb_line = (
                f"andreas,entity_id=weight,friendly_name=Gewicht "
                f"weight={weight},BMI={bmi},fat={fat},water={water},muscles={muscles},bones={bones} {timestamp}\n"
            )
            outfile.write(influxdb_line)

# Einlesen der CSV-Datei
input_file = "./HealthManager_Blutdruck.csv"

with open(input_file, "r", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")

    # Erstellen der neuen CSV-Datei
    with open(output_file, "a", encoding="utf-8", newline="\n") as outfile:
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

            # Formatieren der Zeile für InfluxDB
            influxdb_line = (
                f"andreas,entity_id=blood_pressure,friendly_name=Blutdruck "
                f"sys={sys},dia={dia},pulse={pulse},MAD={mad} {timestamp}\n"
            )
            outfile.write(influxdb_line)

print(f"Die Datei {output_file} wurde erfolgreich erstellt.")
