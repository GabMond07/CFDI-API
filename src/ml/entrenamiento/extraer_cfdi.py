import pandas as pd
import asyncio
from prisma import Prisma
from dotenv import load_dotenv
load_dotenv()

async def obtener_cfdis():
    db = Prisma()
    await db.connect()
    cfdis = await db.cfdi.find_many()
    await db.disconnect()

    df = pd.DataFrame([
        {
            "uuid": c.uuid,
            "total": c.total,
            "payment_method": c.payment_method or "N/A",
            "issue_date": c.issue_date,
            "day_of_week": c.issue_date.weekday(),  # 0 = lunes, 6 = domingo
        }
        for c in cfdis
    ])
    return df


if __name__ == "__main__":
    df = asyncio.run(obtener_cfdis())
    df.to_csv("cfdis_para_entrenar.csv", index=False)
