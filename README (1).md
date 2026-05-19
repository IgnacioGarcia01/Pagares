# Pagaré USD — Rosental S.A.

Aplicación Streamlit para la operatoria de compra de Pagaré en Dólares.

## Correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Community Cloud

1. Subir a GitHub  
2. Ir a https://share.streamlit.io  
3. New app → conectar repo → `app.py` → Deploy

## Funcionalidades

- Toggle Garantizado / No Garantizado (oculta columnas y parámetros SGR)
- Parámetros editables en tiempo real
- Instrumentos ilimitados con nombre personalizable
- Inputs con separador de miles y número en letras
- Tabla de resultados con columnas grises y fila totales destacada
- Borrar instrumento individual o todos

## Fórmulas (Excel → Python)

| Col | Nombre            | Fórmula                                        |
|-----|-------------------|------------------------------------------------|
| E   | Días              | `fechaPago - fechaLiq`                         |
| H   | VN Pesos          | `F × G`                                        |
| J   | Importe Bruto     | `H / (1 + I×E/365)`                            |
| K   | Descuento         | `H − J`                                        |
| L   | Der. Mercado      | `IF(E>90, J×tasa, J×tasa/90×E)`               |
| M   | Arancel Rosental  | `MAX(BoletoMin, H×com/365×E)`                  |
| N   | IVA Gastos        | `(L+M) × 21%`                                  |
| O   | Total Gastos      | `L+M+N`                                        |
| P   | Total Boleto      | `H−K−O`                                        |
| Q   | Comisión SGR      | `H × 2% × (E−2)/365`                           |
| R   | Caja Valores SGR  | `H × 0,2% × 1,21`                              |
| S   | Total SGR         | `Q+R`                                          |
| T   | NETO A COBRAR     | `H−K−O−S` (garantizado) / `H−K−O` (no grt.)  |
