import logging
from app.core.config import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class LlmService:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.client = None
        self.model_name = "gemini-2.5-flash-lite"
        self.system_instruction = (
            "Eres un ingeniero experto en psicrometría y automatización de sistemas HVAC en plantas farmacéuticas GxP. "
            "El sistema utiliza un modelo XGBoost entrenado mediante respuesta al escalón en estado estacionario. "
            "Las variables exteriores tienen un peso despreciable debido al pre-acondicionamiento térmico de la UMA principal. "
            "Tu tarea es justificar técnicamente la modulación del secador basándote en la carga latente local y el setpoint. "
            "Da una explicación concisa de máximo 2 líneas en español, usando términos como: régimen permanente, ganancia estática o estabilidad del lote."
        )

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("✨ [LlmService] Cliente de Google Gemini configurado.")
            except Exception as e:
                logger.error(f"⚠️ [LlmService] Fallo al inicializar Gemini: {e}")

    def generate_engineering_justification(
        self,
        current_pwr: float,
        ideal_pwr: float,
        setpoint: float,
        gmp_alert: bool,
        savings_pct: float,
    ) -> str:
        """Genera una explicación dinámica o activa el plan de contingencia si no hay red."""
        fallback_text = "Ajuste basado en equilibrio psicrométrico estándar (Modo de Contingencia Local)."

        if gmp_alert:
            fallback_text = "Ajuste preventivo forzado para contener de manera inmediata una potencial excursión fuera de los umbrales regulatorios."
        elif savings_pct > 0:
            fallback_text = "Optimización del trabajo mecánico del deshumidificador conservando la estabilidad de la carga latente."

        if not self.client:
            return fallback_text

        try:
            prompt = (
                f"Contexto Operacional Estacionario:\n"
                f"- Setpoint de Seguridad: {setpoint}% HR.\n"
                f"- Ajuste Predictivo: Cambiar potencia del {current_pwr}% al {ideal_pwr}%.\n"
                f"- Alerta Higrométrica GxP: {'CRÍTICA' if gmp_alert else 'NORMAL'}.\n\n"
                f"Explica resumidamente al operador cómo este ajuste estabiliza el lazo cerrado respecto al setpoint objetivo."
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    max_output_tokens=120,
                    temperature=0.15,
                ),
            )
            return (
                response.text.strip().replace('"', "")
                if response.text
                else fallback_text
            )
        except Exception as e:
            logger.error(f"⚠️ [LlmService] Timeout o error en API de Gemini: {e}")
            return fallback_text
