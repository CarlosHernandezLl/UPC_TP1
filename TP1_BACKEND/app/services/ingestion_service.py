"""
Módulo de ingestión de datos para HU-01.
Carga, limpia y fusiona datos de los 3 dataloggers.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rutas base
BASE_DIR = Path(__file__).parent.parent  # app/ -> TP1_BACKEND
DATA_DIR = BASE_DIR / "data"


def load_dataloger_rotronic(file_path: str) -> pd.DataFrame:
    """
    Carga el archivo del dataloger Rotronic (formato personalizado).
    
    El archivo tiene un formato especial con secciones:
    - [#I] Descripción equipo
    - [#S] Versión y serie
    - [#1] Configuración Humedad
    - [#2] Configuración Temperatura
    - [#H] Encabezado de columnas
    - [#D] Datos
    
    Args:
        file_path: Ruta al archivo dataloger.xls
        
    Returns:
        DataFrame con columnas: timestamp, humedad, temperatura
    """
    logger.info(f"Cargando dataloger Rotronic: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Buscar inicio de datos después de [#D]Medidas
    data_start = None
    data_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Buscar la línea "Medidas" que indica el inicio real de datos
        if 'Medidas' in stripped and '[#D]' in stripped:
            data_start = i + 1
        elif data_start and stripped.startswith('[#'):
            # Encontramos otra sección, terminamos datos
            break
        elif data_start and stripped:
            data_lines.append(stripped)
    
    if not data_lines:
        raise ValueError(f"No se encontraron datos en {file_path}")
    
    # Parsear datos (formato: fecha\thora\thumedad\ttemperatura)
    parsed_data = []
    for line in data_lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            try:
                fecha = parts[0].strip()
                hora = parts[1].strip()
                humedad = float(parts[2].strip())
                temperatura = float(parts[3].strip())
                timestamp = pd.to_datetime(f"{fecha} {hora}", format="%d/%m/%Y %H:%M:%S")
                parsed_data.append({
                    'timestamp': timestamp,
                    'humedad': humedad,
                    'temperatura': temperatura
                })
            except (ValueError, IndexError) as e:
                logger.warning(f"Fila ignorada por error: {line} - {e}")
                continue
    
    df = pd.DataFrame(parsed_data)
    logger.info(f"Dataloger cargado: {len(df)} registros")
    return df


def load_externo_csv(file_path: str) -> pd.DataFrame:
    """
    Carga el archivo externo.csv con datos climáticos externos.
    
    Args:
        file_path: Ruta al archivo externo.csv
        
    Returns:
        DataFrame con columnas: timestamp, temp_ext, hum_ext
    """
    logger.info(f"Cargando externo.csv: {file_path}")
    
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    logger.info(f"Externo cargado: {len(df)} registros")
    return df


def load_umaf209_csv(file_path: str) -> pd.DataFrame:
    """
    Carga el archivo umaf209.csv con datos de la máquina UMAF209.
    
    Args:
        file_path: Ruta al archivo umaf209.csv
        
    Returns:
        DataFrame con columnas: timestamp, f20911t, f20911h, f20910p, f209potsecador
    """
    logger.info(f"Cargando umaf209.csv: {file_path}")
    
    df = pd.read_csv(file_path)
    # Renombrar columna 'fecha' a 'timestamp'
    df['timestamp'] = pd.to_datetime(df['fecha'])
    # Eliminar columnas innecesarias
    df = df.drop(columns=['id', 'fecha'], errors='ignore')
    
    logger.info(f"UMAF209 cargado: {len(df)} registros")
    return df


def clean_dataloger_noise(df: pd.DataFrame, 
                          start_rows_to_remove: int = 5, 
                          end_rows_to_remove: int = 5) -> pd.DataFrame:
    """
    Limpia el ruido del dataloger eliminando filas de inicio y fin.
    
    Los dataloggers suelen tener registros al inicio y fin que pueden
    contener valores atípicos o incompletos debido al arranque/parada.
    
    Args:
        df: DataFrame con columna 'timestamp'
        start_rows_to_remove: Número de filas a eliminar del inicio
        end_rows_to_remove: Número de filas a eliminar del fin
        
    Returns:
        DataFrame limpio
    """
    logger.info(f"Limpiando ruido: {start_rows_to_remove} filas inicio, {end_rows_to_remove} filas fin")
    
    original_len = len(df)
    
    # Eliminar filas del inicio
    if start_rows_to_remove > 0:
        df = df.iloc[start_rows_to_remove:]
    
    # Eliminar filas del fin
    if end_rows_to_remove > 0:
        df = df.iloc[:-end_rows_to_remove]
    
    logger.info(f"Ruido eliminado: {original_len - len(df)} filas removidas")
    return df


def merge_dataloggers(dataloger: pd.DataFrame, 
                      externo: pd.DataFrame, 
                      umaf209: pd.DataFrame,
                      tolerance_minutes: int = 5) -> pd.DataFrame:
    """
    Fusiona los 3 dataloggers usando la columna timestamp.
    
    Utiliza merge_asof para hacer un merge aproximativo (nearest),
    permitiendo una tolerancia configurable para sincronizar timestamps.
    
    Args:
        dataloger: DataFrame del dataloger Rotronic
        externo: DataFrame del archivo externo
        umaf209: DataFrame del archivo umaf209
        tolerance_minutes: Tolerancia en minutos para el merge
        
    Returns:
        DataFrame fusionado con todos los datos
    """
    logger.info(f"Fusionando dataloggers (tolerancia: {tolerance_minutes} min)")
    
    # Ordenar todos los DataFrames por timestamp
    dataloger = dataloger.sort_values('timestamp').reset_index(drop=True)
    externo = externo.sort_values('timestamp').reset_index(drop=True)
    umaf209 = umaf209.sort_values('timestamp').reset_index(drop=True)
    
    # Merge aproximativo con tolerancia mayor
    # Usamos merge_asof que hace nearest join dentro de la tolerancia
    df_merged = pd.merge_asof(
        dataloger,
        externo,
        on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta(minutes=tolerance_minutes)
    )
    
    df_merged = pd.merge_asof(
        df_merged,
        umaf209,
        on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta(minutes=tolerance_minutes)
    )
    
    # Eliminar filas donde no hubo match (todos los valores de externo/umaf son NaN)
    # Esto indica que no había datos close enough en esos archivos
    initial_count = len(df_merged)
    df_merged = df_merged.dropna(subset=['temp_ext', 'f20911t'], how='all')
    dropped = initial_count - len(df_merged)
    
    if dropped > 0:
        logger.warning(f"Se eliminaron {dropped} registros sin datos coincidentes")
    
    logger.info(f"Merge completado: {len(df_merged)} registros")
    return df_merged


def load_and_merge_all(data_dir: Optional[str] = None,
                       clean_start: int = 5,
                       clean_end: int = 5,
                       tolerance: int = 5) -> pd.DataFrame:
    """
    Función principal: carga los 3 archivos, limpia ruido y fusiona.
    
    Args:
        data_dir: Directorio con los archivos de datos. 
                  Si es None, usa el directorio por defecto.
        clean_start: Filas a eliminar del inicio de cada dataloger
        clean_end: Filas a eliminar del fin de cada dataloger
        tolerance: Tolerancia en minutos para el merge
        
    Returns:
        DataFrame fusionado con todos los datos
    """
    if data_dir is None:
        data_dir = DATA_DIR
    
    # Cargar los 3 archivos
    dataloger = load_dataloger_rotronic(str(Path(data_dir) / "dataloger.xls"))
    externo = load_externo_csv(str(Path(data_dir) / "externo.csv"))
    umaf209 = load_umaf209_csv(str(Path(data_dir) / "umaf209.csv"))
    
    # Limpiar ruido de cada dataloger
    dataloger = clean_dataloger_noise(dataloger, clean_start, clean_end)
    externo = clean_dataloger_noise(externo, clean_start, clean_end)
    umaf209 = clean_dataloger_noise(umaf209, clean_start, clean_end)
    
    # Fusionar los 3 dataloggers
    df_final = merge_dataloggers(dataloger, externo, umaf209, tolerance)
    
    return df_final


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Genera un resumen estadístico del DataFrame fusionado.
    
    Args:
        df: DataFrame con datos fusionados
        
    Returns:
        Diccionario con estadísticas
    """
    return {
        'total_registros': len(df),
        'fecha_inicio': df['timestamp'].min(),
        'fecha_fin': df['timestamp'].max(),
        'columnas': df.columns.tolist(),
        'valores_nulos': df.isnull().sum().to_dict(),
        'estadisticas': df.describe().to_dict()
    }


# Ejemplo de uso
if __name__ == "__main__":
    # Cargar y fusionar todos los datos
    df = load_and_merge_all()
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN DE DATOS FUSIONADOS")
    print("="*60)
    summary = get_data_summary(df)
    print(f"Total registros: {summary['total_registros']}")
    print(f"Fecha inicio: {summary['fecha_inicio']}")
    print(f"Fecha fin: {summary['fecha_fin']}")
    print(f"Columnas: {summary['columnas']}")
    print(f"\nPrimeras 5 filas:")
    print(df.head())
    print(f"\nValores nulos por columna:")
    print(df.isnull().sum())