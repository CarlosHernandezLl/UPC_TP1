import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import r2_score, mean_squared_error

from app.ml_engine.ssd_filter import SSDFilter
from app.services.data_service import DataService
from app.services.ml_model_service import MlModelService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class MLTrainingService:
    """Servicio orquestador del ciclo de vida de IA farmacéutica (MLOps & 21 CFR Part 11)."""

    def __init__(
        self,
        data_service: DataService,
        model_service: MlModelService,
        audit_service: AuditService,
        sim_engine,
    ):
        self.data_service = data_service
        self.model_service = model_service
        self.audit_service = audit_service
        self.sim_engine = sim_engine

        # 🚀 CORRECCIÓN: Volvemos a las 6 variables estructurales puras (Sin inercias)
        self.feature_cols = [
            "dryer_power",
            "outdoor_temp",
            "outdoor_w",
            "ahu_temp",
            "ahu_w",
            "injection_pressure",
        ]

    def get_active_model_metrics(self) -> dict:
        """Obtiene las métricas reales y el linaje del modelo activo en producción."""
        active_model = self.model_service.get_active_model_version()
        if active_model is not None:
            return {
                "version_tag": active_model.version_tag,
                "r2_score": active_model.r2_score,
                "rmse": active_model.rmse,
                "batch_id": (
                    str(active_model.batch_id) if active_model.batch_id else None
                ),
                "trained_at": active_model.trained_at,
                "status": "ACTIVE_DATABASE_REGISTRY",
            }

        if (
            hasattr(self.sim_engine, "r2_score")
            and self.sim_engine.r2_score is not None
        ):
            return {
                "version_tag": "v1.0.0-in-memory",
                "r2_score": self.sim_engine.r2_score,
                "rmse": getattr(self.sim_engine, "rmse", 0.0),
                "status": "ACTIVE_IN_MEMORY_ONLY",
            }

        return {
            "version_tag": "NONE",
            "r2_score": 0.0,
            "rmse": 0.0,
            "status": "UNTRAINED_OR_EMPTY",
        }

    
    def execute_retraining_pipeline(self, user_id: int) -> dict:
        """Orquesta la extracción, filtrado SSD y Quality Gate GxP (Modelo 6 Variables con LOSO CV)."""
        logger.info(
            f"⚙️ [MLOps] Operador ID={user_id} inició pipeline de reentrenamiento estricto LOSO."
        )

        batch_id, db_records = self.data_service.get_latest_training_batch()
        if not db_records or len(db_records) < 100:
            msg = "El último lote tiene datos insuficientes (<100 filas) para un entrenamiento científico."
            self.audit_service.record_action(
                user_id=user_id, action="ML_RETRAIN_FAILED", resource="MLOPS_PIPELINE", detail=msg
            )
            return {"status": "error", "message": msg}

        df_raw = pd.DataFrame([
            {
                "ts": r.timestamp,
                "dryer_power": float(r.dryer_power),
                "outdoor_temp": float(r.outdoor_temp),
                "outdoor_w": float(r.outdoor_w),
                "ahu_temp": float(r.ahu_temp),
                "ahu_w": float(r.ahu_w),
                "injection_pressure": float(r.injection_pressure),
                "room_w": float(r.room_w),
            }
            for r in db_records
        ])

        # 1. Filtrado de Estado Estacionario (SSD) directo sobre datos crudos
        df_gold = SSDFilter.extract_stationary_minutes(df_raw, patience=10, percentile=0.95)
        
        if df_gold.empty or len(df_gold) < 20:
            msg = "No se encontraron ventanas estables bajo el algoritmo SSD en el lote seleccionado."
            self.audit_service.record_action(
                user_id=user_id, action="ML_RETRAIN_FAILED", resource="MLOPS_PIPELINE", detail=msg
            )
            return {"status": "error", "message": msg}

        # 2. Mapeo de 6 variables
        X = df_gold[self.feature_cols]
        y = df_gold["room_w"]
        grupos = sorted(df_gold["step_change"].unique())

        todas_preds = []
        todas_reales = []
        monotone_constraints = (-1, 0, 1, -1, 1, 0)

        # 3. 🚀 VALIDACIÓN ESTRICTA: Leave-One-Step-Out (LOSO) Pooled Metrics
        logger.info("[MLOps] Ejecutando validación cruzada LOSO...")
        for g in grupos:
            test_mask = df_gold["step_change"] == g
            X_tr, y_tr = X.loc[~test_mask], y.loc[~test_mask]
            X_te, y_te = X.loc[test_mask], y.loc[test_mask]

            modelo_fold = xgb.XGBRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                reg_lambda=1.0,
                reg_alpha=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                monotone_constraints=monotone_constraints,
                random_state=42,
            )
            modelo_fold.fit(X_tr, y_tr)
            preds = modelo_fold.predict(X_te)

            todas_preds.extend(preds)
            todas_reales.extend(y_te.values)

        # Cálculo de las métricas agrupadas fuera de muestra
        r2_real = float(r2_score(todas_reales, todas_preds) * 100.0)
        rmse_real = float(np.sqrt(mean_squared_error(todas_reales, todas_preds)))

        # 4. GxP Quality Gate
        if r2_real < 70.0:
            reason = f"Reentrenamiento rechazado: R² validado fuera de muestra ({r2_real:.2f}%) inferior al estándar GxP (70.0%)."
            logger.warning(f"⚠️ {reason}")
            self.audit_service.record_action(
                user_id=user_id,
                action="ML_MODEL_REJECTED",
                resource="MLOPS_PIPELINE",
                detail=f"Challenger failed LOSO quality gate. R²={r2_real:.2f}%, RMSE={rmse_real:.6f}. Batch UUID: {batch_id}",
            )
            return {"status": "rejected", "reason": reason}

        # 5. 🚀 ENTRENAMIENTO DE PRODUCCIÓN: 100% de la Data de Oro
        logger.info("[MLOps] Quality Gate superado. Entrenando modelo de producción con 100% de la data de oro...")
        model_final = xgb.XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            reg_lambda=1.0,
            reg_alpha=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            monotone_constraints=monotone_constraints,
            random_state=42,
        )
        model_final.fit(X, y)

        # 6. Almacenamiento en Disco y Registro Relacional
        base_path = os.path.dirname(__file__)
        model_dir = os.path.abspath(os.path.join(base_path, "..", "ml_engine", "saved_models"))
        os.makedirs(model_dir, exist_ok=True)

        version_tag = datetime.now(ZoneInfo("America/Lima")).strftime("v1.%m%d.%H%M%S")
        model_file_path = os.path.join(model_dir, f"xgboost_hvac_{version_tag}.json")
        model_final.save_model(model_file_path)

        # Persistencia en BD
        self.model_service.register_new_version(
            version_tag=version_tag,
            model_path=model_file_path,
            r2_score=round(r2_real, 2),
            rmse=round(rmse_real, 6),
            batch_id=batch_id,
            status="ACTIVE",
        )

        # 7. Actualización en caliente en memoria RAM
        self.sim_engine.r2_score = round(r2_real, 2)
        self.sim_engine.rmse = round(rmse_real, 6)
        if hasattr(self.sim_engine, "reload_model_in_memory"):
            self.sim_engine.reload_model_in_memory(model_path=model_file_path)

        success_msg = f"Modelo Challenger {version_tag} validado (LOSO) con R²={r2_real:.2f}%. Pesos actualizados en RAM."
        self.audit_service.record_action(
            user_id=user_id,
            action="ML_MODEL_PROMOTED",
            resource="MLOPS_PIPELINE",
            detail=f"New champion model promoted. LOSO R²={r2_real:.2f}%, RMSE={rmse_real:.6f}. Trained on Batch UUID: {batch_id}",
        )

        return {"status": "success", "message": success_msg, "version_tag": version_tag}
    
    # def execute_retraining_pipeline(self, user_id: int) -> dict:
    #     """Orquesta la extracción, filtrado SSD y Quality Gate GxP (Modelo 6 Variables)."""
    #     logger.info(
    #         f"⚙️ [MLOps] Operador ID={user_id} inició pipeline de reentrenamiento."
    #     )

    #     batch_id, db_records = self.data_service.get_latest_training_batch()
    #     if not db_records or len(db_records) < 100:
    #         msg = "El último lote tiene datos insuficientes (<100 filas) para un entrenamiento científico."
    #         self.audit_service.record_action(
    #             user_id=user_id,
    #             action="ML_RETRAIN_FAILED",
    #             resource="MLOPS_PIPELINE",
    #             detail=msg,
    #         )
    #         return {"status": "error", "message": msg}

    #     # Extracción limpia de la base de datos a Pandas
    #     df_raw = pd.DataFrame(
    #         [
    #             {
    #                 "ts": r.timestamp,
    #                 "dryer_power": float(r.dryer_power),
    #                 "outdoor_temp": float(r.outdoor_temp),
    #                 "outdoor_w": float(r.outdoor_w),
    #                 "ahu_temp": float(r.ahu_temp),
    #                 "ahu_w": float(r.ahu_w),
    #                 "injection_pressure": float(
    #                     getattr(r, "injection_pressure", 1013.25)
    #                 ),
    #                 "room_w": float(r.room_w),
    #             }
    #             for r in db_records
    #         ]
    #     )

    #     # 1. 🚀 CORRECCIÓN: Filtrado de Estado Estacionario (SSD) directo sobre datos crudos
    #     df_gold = SSDFilter.extract_stationary_minutes(
    #         df_raw, patience=10, percentile=0.95
    #     )

    #     if df_gold.empty or len(df_gold) < 20:
    #         msg = "No se encontraron ventanas estables bajo el algoritmo SSD en el lote seleccionado."
    #         self.audit_service.record_action(
    #             user_id=user_id,
    #             action="ML_RETRAIN_FAILED",
    #             resource="MLOPS_PIPELINE",
    #             detail=msg,
    #         )
    #         return {"status": "error", "message": msg}

    #     # 2. 🚀 CORRECCIÓN: Asignación directa (Eliminamos augmentación sintética)
    #     X = df_gold[self.feature_cols]
    #     y = df_gold["room_w"]

    #     # 3. División Cronológica por Escalones sin Data Leakage
    #     gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    #     train_idx, test_idx = next(gss.split(X, y, groups=df_gold["step_change"]))

    #     X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    #     X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

    #     # 4. 🚀 CORRECCIÓN: Nuevos hiperparámetros y 6 Restricciones Monótonas
    #     monotone_constraints = (-1, 0, 1, -1, 1, 0)
    #     model = xgb.XGBRegressor(
    #         n_estimators=50,
    #         max_depth=3,
    #         learning_rate=0.1,
    #         reg_lambda=1.0,
    #         reg_alpha=0.1,
    #         subsample=0.8,
    #         colsample_bytree=0.8,
    #         monotone_constraints=monotone_constraints,
    #         random_state=42,
    #     )
    #     model.fit(X_train, y_train)

    #     preds = model.predict(X_test)
    #     r2_real = float(r2_score(y_test, preds) * 100.0)
    #     mse_real = float(mean_squared_error(y_test, preds))
    #     rmse_real = float(np.sqrt(mse_real))

    #     # 5. GxP Quality Gate
    #     if r2_real < 70.0:
    #         reason = f"Reentrenamiento rechazado: R² del nuevo lote ({r2_real:.2f}%) inferior al estándar GxP (70.0%)."
    #         logger.warning(f"⚠️ {reason}")
    #         self.audit_service.record_action(
    #             user_id=user_id,
    #             action="ML_MODEL_REJECTED",
    #             resource="MLOPS_PIPELINE",
    #             detail=f"Challenger model failed quality gate. R²={r2_real:.2f}%, RMSE={rmse_real:.6f}. Batch UUID: {batch_id}",
    #         )
    #         return {"status": "rejected", "reason": reason}

    #     # 6. Almacenamiento en Disco y Registro Relacional
    #     base_path = os.path.dirname(__file__)
    #     model_dir = os.path.abspath(
    #         os.path.join(base_path, "..", "ml_engine", "saved_models")
    #     )
    #     os.makedirs(model_dir, exist_ok=True)

    #     # Generación de tag único con milisegundos
    #     version_tag = datetime.now(ZoneInfo("America/Lima")).strftime("v1.%m%d.%H%M%S")

    #     model_file_path = os.path.join(model_dir, f"xgboost_hvac_{version_tag}.json")
    #     model.save_model(model_file_path)

    #     # Persistencia en BD
    #     self.model_service.register_new_version(
    #         version_tag=version_tag,
    #         model_path=model_file_path,
    #         r2_score=round(r2_real, 2),
    #         rmse=round(rmse_real, 6),
    #         batch_id=batch_id,
    #         status="ACTIVE",
    #     )

    #     # 7. Actualización en caliente en memoria RAM
    #     self.sim_engine.r2_score = round(r2_real, 2)
    #     self.sim_engine.mse = round(mse_real, 6)
    #     if hasattr(self.sim_engine, "reload_model_in_memory"):
    #         self.sim_engine.reload_model_in_memory(model_path=model_file_path)

    #     success_msg = f"Modelo Challenger {version_tag} validado con R²={r2_real:.2f}%. Pesos actualizados en RAM."
    #     self.audit_service.record_action(
    #         user_id=user_id,
    #         action="ML_MODEL_PROMOTED",
    #         resource="MLOPS_PIPELINE",
    #         detail=f"New champion model promoted. R²={r2_real:.2f}%, RMSE={rmse_real:.6f}. Trained on Batch UUID: {batch_id}",
    #     )

    #     return {"status": "success", "message": success_msg, "version_tag": version_tag}
