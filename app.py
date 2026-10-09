import io, re, unicodedata
from datetime import datetime, timezone
import pandas as pd
import requests
import streamlit as st
import plotly.express as px

st.set_page_config(page_title='Observatorio Agroalimentario | Fuentes oficiales',layout='wide')
st.title('Observatorio Agroalimentario · Fuentes oficiales')
st.caption('Prototipo de consulta directa. Datos oficiales disponibles en el origen; no se fabrican registros ni se utilizan datos simulados.')

URL_DGSIAP = 'https://nube.agricultura.gob.mx/index.php?ANIO={year}&view=10AE434F-A2158368-A120BC5A-EDF4AFAA'
CONAGUA = {
    'Estadísticas agrícolas de distritos de riego': 'https://datos.conagua.gob.mx/docs/DatosAbiertos/Estadisticas_Agricolas_Distritos_de_Riego.csv',
    'Precipitación diaria': 'https://datos.conagua.gob.mx/docs/DatosAbiertos/PRECIPITACION_DIA.csv',
    'Temperatura diaria': 'https://datos.conagua.gob.mx/docs/DatosAbiertos/TEMPAIRE_DIA.csv',
}

def norm(x):
    return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKD',str(x)).encode('ascii','ignore').decode().lower())

@st.cache_data(ttl=6*3600,show_spinner='Descargando información oficial...')
def load_csv(url):
    r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (compatible; ObservatorioAgro/0.1)'},timeout=65)
    r.raise_for_status()
    if len(r.content)>95_000_000:
        raise ValueError('Archivo mayor a 95 MB; utilice el proceso de carga programada.')
    errors=[]
    for encoding in ('utf-8-sig','latin1','cp1252'):
        for sep in (None,',',';','\t','|'):
            try:
                df=pd.read_csv(io.BytesIO(r.content),encoding=encoding,sep=sep,engine='python' if sep is None else 'c',low_memory=False if sep is not None else True)
                if len(df.columns)>1 and len(df)>0:
                    return df,datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
            except (UnicodeError,pd.errors.ParserError,ValueError) as e:
                errors.append(str(e))
    raise ValueError('No fue posible identificar estructura del CSV de origen.')

def findcol(df,aliases):
    columns={norm(c):c for c in df.columns}
    for alias in aliases:
        if norm(alias) in columns:return columns[norm(alias)]
    for alias in aliases:
        for k,v in columns.items():
            if norm(alias) in k:return v
    return None

ALIASES={
'estado':['nomestado','estado','entidad','nomentidad','entidadfederativa'],
'municipio':['nommunicipio','municipio'],
'cultivo':['nomcultivo','cultivo','producto','nomproducto'],
'anio':['anio','ano','year'],
'sembrada':['sembrada','superficiesembrada','supsembrada','supsem'],
'cosechada':['cosechada','superficiecosechada','supcosechada','supcos'],
'siniestrada':['siniestrada','superficiesiniestrada','supsiniestrada','supsin'],
'produccion':['volumenproduccion','volumen','produccion','produccionobtenida'],
'rendimiento':['rendimiento','rendimientootenido','rendimientobtenido'],
'pmr':['precio','preciomediorural','pmr'],
'valor':['valorproduccion','valor','valordelaproduccion']}

def number(series):
    if pd.api.types.is_numeric_dtype(series):return pd.to_numeric(series,errors='coerce')
    s=series.astype(str).str.replace(',','',regex=False).str.replace(' ','',regex=False)
    return pd.to_numeric(s,errors='coerce')

def fmt(x,unit=''):
    if pd.isna(x):return 'Sin dato'
    return f'{x:,.2f} {unit}'

with st.sidebar:
    st.header('Fuente y actualización')
    source=st.radio('Conjunto de datos',['DGSIAP · Cierre agrícola','CONAGUA · Datos abiertos'])
    if source.startswith('DGSIAP'):
        year=st.selectbox('Año del cierre',list(range(2025,2002,-1)))
        url=URL_DGSIAP.format(year=year)
    else:
        dataset=st.selectbox('Conjunto CONAGUA',list(CONAGUA))
        url=CONAGUA[dataset]
    st.markdown(f'[Abrir archivo original]({url})')
    if st.button('Actualizar desde origen'):
        load_csv.clear()
        st.rerun()

try:
    df,consulted=load_csv(url)
except Exception as exc:
    st.error(f'No se logró obtener el archivo oficial: {exc}')
    st.info('La disponibilidad depende del servidor de origen. No se reemplazan datos faltantes por cifras ficticias. Puede reintentar o utilizar el enlace oficial.')
    st.stop()
st.success(f'Archivo consultado · {len(df):,} registros · {consulted} · fuente: {source}')
st.caption('Fecha de consulta no equivale a la fecha oficial de publicación o corte del conjunto de datos.')

if source.startswith('CONAGUA'):
    st.subheader('Explorador de información hidrológica / climática')
    st.info('Conector de lectura directa. La homologación automática por municipio y periodo con la producción agrícola requiere normalizar primero este conjunto de datos.')
    st.dataframe(df.head(500),use_container_width=True)
    st.write('Columnas:',', '.join(map(str,df.columns)))
    st.download_button('Exportar vista (CSV)',df.head(500).to_csv(index=False).encode('utf-8-sig'),'conagua_vista.csv','text/csv')
    st.stop()

cols={k:findcol(df,v) for k,v in ALIASES.items()}
with st.expander('Estructura identificada / trazabilidad'):
    st.json(cols)
    st.write('Columnas originales:',list(df.columns))

for item in ('estado','municipio','cultivo'):
    col=cols[item]
    if col:
        values=sorted(df[col].dropna().astype(str).unique().tolist())
        if item=='estado':
            choice=st.selectbox('Entidad federativa',['Todas']+values)
        elif item=='cultivo':
            choice=st.selectbox('Cultivo',['Todos']+values)
        else:
            choice=st.selectbox('Municipio',['Todos']+values)
        if choice not in ('Todas','Todos'):
            df=df[df[col].astype(str)==choice]

numeric={}
for key in ('sembrada','cosechada','siniestrada','produccion','rendimiento','pmr','valor'):
    if cols[key] is not None:
        numeric[key]=number(df[cols[key]])

st.subheader('Indicadores del cierre agrícola')
metric_def=[('sembrada','Superficie sembrada','ha'),('cosechada','Superficie cosechada','ha'),('siniestrada','Superficie siniestrada','ha'),('produccion','Producción','t'),('pmr','PMR ponderado','$/t'),('rendimiento','Rendimiento agregado','t/ha')]
metrics={}
for key,label,unit in metric_def:
    if key in numeric and key not in ('pmr','rendimiento'):
        metrics[key]=numeric[key].sum(min_count=1)
if 'produccion' in metrics and 'cosechada' in metrics and metrics['cosechada']>0:
    metrics['rendimiento']=metrics['produccion']/metrics['cosechada']
if 'valor' in numeric and 'produccion' in metrics and metrics['produccion']>0:
    # Precio derivado: solo válido si valor monetario está expresado en miles de pesos, como en diversos cierres DGSIAP.
    st.caption('El PMR debe calcularse según la unidad del campo valor de producción indicada en el diccionario oficial; por seguridad no se estima automáticamente.')
cs=st.columns(3)
for i,(key,label,unit) in enumerate(metric_def):
    cs[i%3].metric(label,fmt(metrics.get(key,float('nan')),unit) if key!='pmr' else 'Ver detalle de datos')
if 'sembrada' in metrics and 'siniestrada' in metrics and metrics['sembrada']>0:
    st.metric('Tasa de superficie siniestrada',f"{100*metrics['siniestrada']/metrics['sembrada']:.2f}%")

available=[(key,label) for key,label,unit in metric_def if key in numeric and key not in ('pmr','rendimiento')]
if available:
    metric=st.selectbox('Variable para comparar',available,format_func=lambda x:x[1])[0]
    by=st.selectbox('Agrupar por',[k for k in ('estado','municipio','cultivo') if cols[k]])
    tmp=df[[cols[by]]].copy()
    tmp['valor']=numeric[metric]
    graph=tmp.groupby(cols[by],dropna=False,as_index=False)['valor'].sum().sort_values('valor',ascending=False).head(20)
    fig=px.bar(graph,x='valor',y=cols[by],orientation='h',title=f'Top 20 · {metric}')
    fig.update_layout(yaxis={'categoryorder':'total ascending'},height=560)
    st.plotly_chart(fig,use_container_width=True)
    st.download_button('Descargar resultado agregado',graph.to_csv(index=False).encode('utf-8-sig'),'resultado_agregado.csv','text/csv')
st.subheader('Preguntas para el observatorio')
question=st.text_input('Escribe una pregunta',placeholder='¿Qué municipios registran más superficie siniestrada?')
if question:
    q=norm(question)
    match='siniestrada' if 'siniestr' in q else 'produccion' if 'producc' in q else 'cosechada' if 'cosech' in q else 'sembrada' if 'sembr' in q else None
    gran='municipio' if 'municip' in q else 'estado' if ('estado' in q or 'entidad' in q) else 'cultivo' if 'cultiv' in q else 'municipio'
    if match in numeric and cols.get(gran):
        frame=df[[cols[gran]]].copy()
        frame['dato']=numeric[match]
        res=frame.groupby(cols[gran],dropna=False)['dato'].sum().sort_values(ascending=False).head(10).reset_index()
        st.write(f'Los 10 mayores registros por {gran} para {match}, en el filtro actual:')
        st.dataframe(res,use_container_width=True)
        st.caption('Consulta determinística (reglas), todavía no utiliza un modelo de lenguaje. No interpreta causas ni atribuciones.')
    else:
        st.warning('Esta pregunta no está cubierta por el intérprete inicial. Consulta las visualizaciones o amplía el agente con una herramienta LLM segura.')
st.subheader('Registros oficiales consultados')
st.dataframe(df.head(1000),use_container_width=True)
st.caption('Para preservar recursos gratuitos se visualizan hasta 1,000 filas; las agregaciones usan todas las filas tras aplicar filtros.')
