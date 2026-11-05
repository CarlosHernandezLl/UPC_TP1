"""Genera los archivos de prueba (válidos y alterados) a partir de docs/Entrenamiento Mayo."""
import csv, json, os, shutil
import openpyxl

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "..", "..", "docs", "Entrenamiento Mayo")
OUT = os.path.join(ROOT, "fixtures")
os.makedirs(OUT, exist_ok=True)


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f, delimiter=";"))


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(rows)


def write_xlsx(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    wb.save(path)


plc = read(os.path.join(SRC, "DATOS_PLC.csv"))
ext = read(os.path.join(SRC, "EXTERIOR.csv"))
shutil.copy(os.path.join(SRC, "DATOS_PLC.csv"), os.path.join(OUT, "DATOS_PLC.csv"))
shutil.copy(os.path.join(SRC, "EXTERIOR.csv"), os.path.join(OUT, "EXTERIOR.csv"))
shutil.copy(os.path.join(SRC, "DATALOGGER.xls"), os.path.join(OUT, "DATALOGGER.xls"))

# Variantes .xlsx (HU0001-1: CSV/XLSX)
write_xlsx(os.path.join(OUT, "DATOS_PLC.xlsx"), plc)
write_xlsx(os.path.join(OUT, "EXTERIOR.xlsx"), ext)

# CP002: columna obligatoria eliminada (f209potsecador)
head = plc[0]
drop = head.index("f209potsecador")
write_csv(os.path.join(OUT, "COPIA_DATOS_PLC_sin_columna.csv"), [[c for i, c in enumerate(r) if i != drop] for r in plc])

# CP003: sin encabezado y con formato de fecha inválido
write_csv(os.path.join(OUT, "COPIA_DATOS_PLC_sin_encabezado.csv"), plc[1:])
bad = [plc[0]] + [r[:-1] + ["fecha-invalida"] for r in plc[1:]]
write_csv(os.path.join(OUT, "COPIA_DATOS_PLC_fecha_invalida.csv"), bad)

# Rango de fechas del dataset (para CP004)
first, last = plc[1][-1], plc[-1][-1]
json.dump({"first": first, "last": last}, open(os.path.join(OUT, "rango.json"), "w"))
print("fixtures listos:", sorted(os.listdir(OUT)))
