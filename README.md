# Observatorio Agroalimentario | Prototipo con fuentes oficiales

## Alcance
- Descarga y consulta directa del cierre agrícola municipal DGSIAP (años 2003–2025 mediante dirección oficial identificada en octubre de 2026).
- Presenta filtros, tablas, cifras agregadas, gráficas y preguntas de lenguaje natural **por reglas**, sin LLM.
- Descarga y explora archivos oficiales CONAGUA de distritos de riego, precipitación o temperatura; todavía NO ejecuta una unión analítica con los cierres DGSIAP.
- Las cifras se obtienen directamente del archivo oficial: si falla el servidor, muestra un error y no crea valores ficticios.
- INEGI y SNIIM se documentan como futuras fuentes; no se afirma que estén integradas.

## Desplegar gratuitamente
1. Crear un repositorio de GitHub con `app.py` y `requirements.txt`.
2. Iniciar sesión en https://share.streamlit.io/ usando GitHub.
3. Crear una app y seleccionar el repositorio, rama principal y `app.py`.
4. Publicar. Se requiere conectividad saliente hacia las fuentes oficiales.

## Ejecutar localmente
```
python -m venv .venv
pip install -r requirements.txt
streamlit run app.py
```

## Fuentes
- DGSIAP: https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php
- CONAGUA: https://datos.conagua.gob.mx/views/index_datos_abiertos.html
- INEGI API (requiere token): https://www.inegi.org.mx/servicios/api_indicadores.html
- SNIIM: https://www.economia-sniim.gob.mx/analisis/Precios.asp

## Advertencias analíticas
- Un cierre anual no equivale al avance mensual ni a una fuente de datos en tiempo real.
- Rendimiento agregado = producción / superficie cosechada; no sumar rendimientos.
- PMR nacional/estatal requiere ponderación correcta con el valor de producción y sus unidades; no promediar PMR simples ni inferir desde un valor cuya unidad no se haya verificado.
- El precio SNIIM es al mayoreo, no PMR.
- Para un análisis clima-producción es necesario alinear municipio, periodo agrícola, cobertura espacial y escala temporal; el prototipo aún no lo hace.
- Para uso institucional, implementar caché persistente, control de errores, diccionario de campos, auditoría y pruebas con datos oficiales.
