from sqlalchemy.orm import Session
from app.models.energy_pricing import EnergyPricing


class EnergyPricingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_tariff(self) -> EnergyPricing | None:
        return (
            self.db.query(EnergyPricing)
            .filter(EnergyPricing.is_active == True)
            .order_by(EnergyPricing.effective_from.desc())
            .first()
        )

    def create_tariff(self, cost: float, currency: str = "USD") -> EnergyPricing:
        # Desactivamos tarifas anteriores
        self.db.query(EnergyPricing).filter(EnergyPricing.is_active == True).update(
            {"is_active": False}
        )

        new_tariff = EnergyPricing(kwh_cost=cost, currency=currency, is_active=True)
        self.db.add(new_tariff)
        self.db.commit()
        self.db.refresh(new_tariff)
        return new_tariff
