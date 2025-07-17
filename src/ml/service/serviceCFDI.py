from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from prisma import Prisma
import pandas as pd

async def obtener_datos_cfdi():
    db = Prisma()
    await db.connect()

    cfdis = await db.cfdi.find_many(take=500)

    await db.disconnect()

    # Filtra en Python si hay campos nulos
    filtrados = [
        c for c in cfdis
        if c.type and c.payment_form and c.currency and c.cfdi_use
    ]

    data = pd.DataFrame([{
        "subtotal": c.subtotal,
        "currency": c.currency,
        "payment_form": c.payment_form,
        "cfdi_use": c.cfdi_use,
        "export_status": c.export_status or "N/A",
        "issuer_id": c.issuer_id,
        "receiver_id": str(c.receiver_id),
        "type": c.type
    } for c in filtrados])

    return data


async def clasificar_tipo_cfdi():
    data = await obtener_datos_cfdi()

    # Eliminar registros vacíos
    data.dropna(inplace=True)

    # Codificar variables categóricas
    le_currency = LabelEncoder()
    le_payment_form = LabelEncoder()
    le_cfdi_use = LabelEncoder()
    le_export_status = LabelEncoder()
    le_issuer = LabelEncoder()
    le_receiver = LabelEncoder()
    le_type = LabelEncoder()  # Lo que queremos predecir

    data["currency_encoded"] = le_currency.fit_transform(data["currency"])
    data["payment_form_encoded"] = le_payment_form.fit_transform(data["payment_form"])
    data["cfdi_use_encoded"] = le_cfdi_use.fit_transform(data["cfdi_use"])
    data["export_status_encoded"] = le_export_status.fit_transform(data["export_status"].fillna("N/A"))
    data["issuer_encoded"] = le_issuer.fit_transform(data["issuer_id"])
    data["receiver_encoded"] = le_receiver.fit_transform(data["receiver_id"].astype(str))
    data["type_encoded"] = le_type.fit_transform(data["type"])

    # Variables de entrada (X) y etiqueta (y)
    X = data[[
        "subtotal",
        "currency_encoded",
        "payment_form_encoded",
        "cfdi_use_encoded",
        "export_status_encoded",
        "issuer_encoded",
        "receiver_encoded"
    ]]
    y = data["type_encoded"]

    # División en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Entrenar el modelo
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Evaluar el modelo
    predictions = model.predict(X_test)

    resultados = []
    for i in range(len(X_test)):
        resultados.append({
            "entrada": X_test.iloc[i].to_dict(),
            "prediccion": le_type.inverse_transform([predictions[i]])[0],
            "esperado": le_type.inverse_transform([y_test.iloc[i]])[0]
        })

    return resultados
