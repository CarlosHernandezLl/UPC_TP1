# TP1_MACHINE/ssd_service.py
import pandas as pd
import numpy as np

class SSDService:
    @staticmethod
    def calculate_optimal_threshold(df: pd.DataFrame, percentile: float = 0.90) -> float:
        """Calcula el umbral del percentil 90 basado en la derivada de humedad"""
        if len(df) < 5: return 0.005
        diff_w = df['w_sala'].diff().abs().dropna()
        smooth_diff = diff_w.rolling(window=5, min_periods=1).mean()
        return float(smooth_diff.quantile(percentile))

    @classmethod
    def extraer_todos_los_minutos_estacionarios(cls, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        ESTA ES TU FUNCIÓN ORIGINAL DEL NOTEBOOK.
        Filtra los datos para quedarse solo con el equilibrio térmico.
        """
        df = df_raw.copy().sort_values('ts').reset_index(drop=True)
        df['diff_w'] = df['w_sala'].diff().abs()
        df['cambio_escalon'] = (df['potencia_secador'] != df['potencia_secador'].shift()).cumsum()
        
        umbral = cls.calculate_optimal_threshold(df, 0.90)
        bloques_estables = []
        
        for _, group in df.groupby('cambio_escalon'):
            if len(group) < 20: continue
            data_step = group.copy()
            data_step['smooth_diff'] = data_step['diff_w'].rolling(window=5, min_periods=1).mean()
            is_stable = data_step['smooth_diff'] < umbral
            bloques_estables.append(data_step[is_stable])
            
        if not bloques_estables: return pd.DataFrame()
        return pd.concat(bloques_estables).reset_index(drop=True)