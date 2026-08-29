import logging
from app.repositories.simulation_repository import SimulationRepository
from app.services.gmp_service import GmpService
from app.services.llm_service import LlmService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class SimulationService:
    # 🎯 INYECCIÓN DE SERVICIOS: Recibimos los servicios hermanos, no sus repositorios
    def __init__(
        self,
        sim_repo: SimulationRepository,
        gmp_service: GmpService,
        llm_service: LlmService,
        audit_service: AuditService,
        simulator_engine,
    ):
        self.sim_repo = sim_repo
        self.gmp_service = gmp_service
        self.llm_service = llm_service
        self.audit_service = audit_service
        self.simulator_engine = simulator_engine

    def predict_optimal_power(self, sim_input: dict) -> dict:
        """Ejecuta la inferencia matemática en RAM y la explicación con IA."""
        current_pwr = float(sim_input.get("current_power", 0.0))
        ideal_pwr = current_pwr
        savings_pct = 0.0
        is_gmp_alert = False
        
        room_temp = sim_input.get("room_temp")
        injection_pressure = sim_input.get("injection_pressure")
        if room_temp is None or injection_pressure is None:
            raise ValueError(
                "Faltan campos obligatorios para la inferencia: 'room_temp' y/o 'injection_pressure'. "
                "El modelo no puede calcular el objetivo higrométrico sin ellos."
            )

        # 1. Consultar umbrales vigentes al SERVICIO de GMP con blindaje contra None
        min_limit, max_limit = 40.0, 55.0
        try:
            gmp_config = self.gmp_service.get_active_config()
            if gmp_config is not None:
                min_limit = gmp_config.min_hum_limit
                max_limit = gmp_config.max_hum_limit
        except Exception as e:
            logger.warning(f"⚠️ Usando límites GMP por defecto debido a excepción: {e}")

        # 2. Inferencia en XGBoost
        try:
            ideal_pwr, is_gmp_alert = self.simulator_engine.recomendar_potencia(
                current_power=current_pwr,
                room_temp=room_temp,  # ya no "temp_sala=temp_sala"
                target_setpoint=sim_input.get("target_setpoint", 50.0),
                outdoor_temp=sim_input.get("outdoor_temp", 20.0),
                outdoor_rh=sim_input.get("outdoor_rh", 50.0),
                ahu_temp=sim_input.get("ahu_temp", 20.0),
                ahu_rh=sim_input.get("ahu_rh", 50.0),
                injection_pressure=injection_pressure,
                min_gmp_rh_limit=min_limit,
                max_gmp_rh_limit=max_limit,
            )
            if current_pwr > ideal_pwr:
                savings_pct = round(((current_pwr - ideal_pwr) / current_pwr) * 100, 1)
        except Exception as e:
            logger.error(f"❌ Fallo en XGBoost: {e}. Se mantiene potencia actual.")

        # 3. Delegar justificación al SERVICIO de LLM
        llm_explanation = self.llm_service.generate_engineering_justification(
            current_pwr=current_pwr,
            ideal_pwr=ideal_pwr,
            setpoint=sim_input.get("target_setpoint", 50.0),
            gmp_alert=is_gmp_alert,
            savings_pct=savings_pct,
        )

        return {
            "potencia_recomendada": ideal_pwr,
            "ahorro_estimado_pct": savings_pct,
            "alerta_gmp": is_gmp_alert,
            "explicacion_gemini": llm_explanation,
        }

    def register_operator_decision(self, user_id: int, sim_data: dict) -> dict:
        """Guarda la simulación en BD y emite la pista de auditoría GxP inmutable."""
        # 1. Guardar en tabla de simulaciones mediante su repositorio propio
        self.sim_repo.create(user_id=user_id, sim_data=sim_data)

        # 2. Delegar la auditoría inmutable al SERVICIO de Auditoría (Estandarizado en inglés técnico)
        action_type = sim_data.get("action", "RECOMMENDATION_APPLIED")
        applied = sim_data.get("applied_power", 0.0)
        recommended = sim_data.get("recommended_power", 0.0)

        if action_type == "RECOMMENDATION_APPLIED":
            detail = f"Operator APPLIED Digital Twin recommended power: {applied}%."
        else:
            justification = sim_data.get("justification", "No justification provided")
            detail = f"Operator OVERRODE AI recommendation ({recommended}%) and applied {applied}%. Reason: {justification}"

        self.audit_service.record_action(
            user_id=user_id,
            action=action_type,
            resource="HVAC_SIMULATOR",
            detail=detail,
        )

        return {
            "status": "success",
            "message": "Simulación guardada y auditoría GxP generada exitosamente.",
        }
