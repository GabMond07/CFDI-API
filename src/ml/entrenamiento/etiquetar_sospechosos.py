import pandas as pd

df = pd.read_csv("cfdis_para_entrenar.csv")

# Reglas:
# - total > 1,000,000
# - metodo de pago raro (no "PUE" ni "PPD")
# - día fin de semana (5=sábado, 6=domingo)

def es_sospechoso(row):
    pago_raro = row["payment_method"] not in ("PUE", "PPD")
    es_finde = row["day_of_week"] in (5, 6)
    return int(row["total"] > 1_000_000 or pago_raro or es_finde)

df["sospechoso"] = df.apply(es_sospechoso, axis=1)
df.to_csv("cfdis_etiquetados.csv", index=False)
