import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv("cfdis_etiquetados.csv")

# Preprocesamiento
df = pd.get_dummies(df, columns=["payment_method"], drop_first=True)

X = df[["total", "day_of_week"] + [col for col in df.columns if col.startswith("payment_method_")]]
y = df["sospechoso"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

modelo = RandomForestClassifier()
modelo.fit(X_train, y_train)

print("Precisión:", modelo.score(X_test, y_test))

# Guardar el modelo junto con las columnas
joblib.dump({
    "modelo": modelo,
    "columnas": X.columns.tolist()
}, "../modelo_sospechoso.pkl")
