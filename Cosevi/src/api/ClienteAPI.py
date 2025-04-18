from datetime import datetime

import requests
from src.basedatos.GestorBaseDatos import actualizar_ubicaciones
from src.basedatos.GestorBaseDatos import insertar_lluvia
from src.helpers.Utilidades import dividir_en_chunks
from tqdm import tqdm
import locale
from unidecode import unidecode
from collections import defaultdict


def buscar_lugar_api(provincia, canton, distrito):
    try:
        # Construir la consulta con los campos separados
        query = f"{distrito}, {canton}, {provincia}, Costa Rica"

        # Parámetros para Nominatim
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': 1
        }
        headers = {
            "User-Agent": "Analisis/1.0"  # Pon tu email real si es posible
        }

        response = requests.get('https://nominatim.openstreetmap.org/search', params=params,headers=headers, timeout=10)

        # Comprobar si la respuesta fue exitosa
        response.raise_for_status()

        data = response.json()

        if not data:
            return {
                'success': False,
                'message': 'No se encontraron resultados para la ubicación proporcionada.'
            }

        lugar = data[0]
        return {
            'success': True,
            'nombre': lugar['display_name'],
            'latitud': lugar['lat'],
            'longitud': lugar['lon'],
            'detalles': lugar['address']
        }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'La solicitud a la API tardó demasiado tiempo y fue cancelada.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'Error de red o solicitud: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Ocurrió un error inesperado: {str(e)}'
        }

def consultar_lluvia_api(lat, lon, start_date="2023-10-01", end_date="2023-12-31"):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "precipitation",
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    registros = []
    # Mapeo de días en inglés a español sin tildes
    dias_es = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miercoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sabado",
        "Sunday": "Domingo"
    }
    # Diccionario para agrupar: (anio, mes, dia_semana, hora) -> lista de precipitaciones
    lluvia_agrupada = defaultdict(list)
    # Agrupar precipitaciones por año, mes, día de la semana y hora
    for i, time in enumerate(data["hourly"]["time"]):
        dt = datetime.fromisoformat(time)
        anio = dt.year
        mes = dt.month
        dia_en = dt.strftime("%A")  # Ej: 'Monday'
        dia_semana = dias_es[dia_en]  # Convertido a español sin tilde
        hora = dt.strftime("%H:%M")
        precipitacion = data["hourly"]["precipitation"][i]

        clave = (anio, mes, dia_semana, hora)
        lluvia_agrupada[clave].append(precipitacion)

    for (anio, mes, dia_semana, hora), lista_lluvia in lluvia_agrupada.items():
        promedio = sum(lista_lluvia) / len(lista_lluvia)
        registros.append({
            "anio": anio,
            "mes": mes,
            "dia_semana": dia_semana,
            "hora": hora,
            "lluvia_acumulada": round(promedio,2)
        })

    # Ordenar por día de la semana en español y hora
    dias_orden = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    registros.sort(key=lambda x: (x["anio"], x["mes"], dias_orden.index(x["dia_semana"]), x["hora"]))

    return registros

def cargar_lat_lon(df, chunk_size=1000):
    if not df.empty:
        print("Iniciando actualización de ubicaciones...")

        # Dividir el DataFrame en chunks
        chunks = list(dividir_en_chunks(df, chunk_size))

        # Barra de progreso para la actualización
        for chunk in tqdm(chunks, desc="Actualizando registros", ncols=100):
            for _, row in chunk.iterrows():
                resultado = buscar_lugar_api(row['provincia'], row['canton'], row['distrito'])
                print(resultado)
                if resultado['success']:
                    actualizar_ubicaciones(row['id'], resultado['longitud'], resultado['latitud'])
    else:
        print("⚠️ DataFrame vacío, no se puede procesar.")

def carga_precipitacion(df, chunk_size=1000):
    if not df.empty:
        print("Iniciando insercion de precipitaciones...")

        # Dividir el DataFrame en chunks
        chunks = list(dividir_en_chunks(df, chunk_size))

        # Barra de progreso para la actualización
        for chunk in tqdm(chunks, desc="Insertando registros", ncols=100):
            for _, row in chunk.iterrows():
              try:
                  provincia = row['provincia']
                  canton = row['canton']
                  distrito = row['distrito']
                  lat = row['latitud']
                  lon = row['longitud']

                  datos_lluvia = consultar_lluvia_api(lat, lon)
                  print(datos_lluvia)
                  for registro in datos_lluvia:
                      print(registro)
                      insertar_lluvia(provincia, canton, distrito, registro['dia_semana'], registro['mes'], registro['anio'], registro['hora'], registro['lluvia_acumulada'])
              except Exception as e:
                print(f"⚠️ Error inesperado al insertar: {e}")
    else:
        print("⚠️ DataFrame vacío, no se puede procesar.")