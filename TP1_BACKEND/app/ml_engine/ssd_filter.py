import pandas as pd
import numpy as np


class SSDFilter:
    @staticmethod
    def calculate_absolute_humidity(
        temp: float, rh: float, p: float = 1013.50
    ) -> float:
        if pd.isna(temp) or pd.isna(rh) or pd.isna(p):
            return 0.0
        es = 6.1121 * np.exp((18.678 - temp / 234.5) * (temp / (257.14 + temp)))
        e = (rh / 100.0) * es
        return round(1000.0 * (0.62197 * e / (p - e)), 6)

    @classmethod
    def extract_stationary_minutes(
        cls, df_raw: pd.DataFrame, patience: int = 10, percentile: float = 0.95
    ) -> pd.DataFrame:
        if df_raw.empty or "room_w" not in df_raw.columns:
            return pd.DataFrame()
        df = df_raw.copy().sort_values("ts").reset_index(drop=True)
        df["diff_w"] = df["room_w"].diff().abs()
        df["step_change"] = (df["dryer_power"] != df["dryer_power"].shift()).cumsum()
        diff_w_clean = df["diff_w"].dropna()
        if diff_w_clean.empty:
            return pd.DataFrame()

        # Cálculo estadístico del umbral (Decisión 4 de tu script)
        smooth_diff_global = diff_w_clean.rolling(window=5, min_periods=1).mean()
        stability_threshold = float(smooth_diff_global.quantile(percentile))

        stable_dfs = []
        for _, group in df.groupby("step_change"):
            if len(group) < 20:
                continue
            step_data = group.copy()
            step_data["smooth_diff"] = (
                step_data["diff_w"].rolling(window=5, min_periods=1).mean()
            )
            is_stable = step_data["smooth_diff"] < stability_threshold

            real_stable_idx, counter = None, 0
            for idx in step_data.index:
                counter = counter + 1 if is_stable.loc[idx] else 0
                if counter >= patience:
                    real_stable_idx = idx
                    break

            if real_stable_idx is not None:
                post_data = step_data.loc[real_stable_idx:]
                stable_dfs.append(
                    post_data[post_data["smooth_diff"] < stability_threshold].copy()
                )

        return (
            pd.concat(stable_dfs).reset_index(drop=True)
            if stable_dfs
            else pd.DataFrame()
        )
