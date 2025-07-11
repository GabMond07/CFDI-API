from prisma import Prisma
import pandas as pd
import traceback
import joblib
from src.ml.schemas.cfdi_input import CFDISospechosoInput

modelo_data = joblib.load("src/ml/modelo_sospechoso.pkl")
modelo = modelo_data["modelo"]
columnas_requeridas = modelo_data["columnas"]

async def clasificar_todos_cfdis_service():
    try:
        db = Prisma()
        await db.connect()
        cfdis = await db.cfdi.find_many()
        await db.disconnect()

        df = pd.DataFrame([{
            "uuid": c.uuid,
            "total": c.total,
            "payment_method": c.payment_method or "N/A",
            "day_of_week": c.issue_date.weekday(),
        } for c in cfdis])

        df = pd.get_dummies(df, columns=["payment_method"], drop_first=True)

        for col in columnas_requeridas:
            if col not in df.columns:
                df[col] = 0

        X = df[columnas_requeridas]

        predicciones = modelo.predict(X)
        resultado = [{"uuid": uuid, "sospechoso": bool(pred)} for uuid, pred in zip(df["uuid"], predicciones)]

        return resultado

    except Exception as e:
        print("Error al clasificar CFDIs:", str(e))
        traceback.print_exc()
        raise e
