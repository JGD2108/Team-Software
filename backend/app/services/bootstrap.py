from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Equipment, ProductionLine, Shift, User


def seed_initial_data(db: Session) -> None:
    if not db.query(User).filter(User.email == "admin@mantenimiento.local").first():
        db.add(
            User(
                name="Administrador MVP",
                email="admin@mantenimiento.local",
                password_hash=hash_password("Admin123!"),
                role="admin",
                is_active=True,
            )
        )
    if not db.query(User).filter(User.email == "planta@mantenimiento.local").first():
        db.add(
            User(
                name="Usuario Planta",
                email="planta@mantenimiento.local",
                password_hash=hash_password("Planta123!"),
                role="plant_user",
                is_active=True,
            )
        )
    for shift in ["Turno A", "Turno B", "Turno C", "Sin turno"]:
        if not db.query(Shift).filter(Shift.name == shift).first():
            db.add(Shift(name=shift, is_active=True))
    db.flush()
    if not db.query(ProductionLine).first():
        line_a = ProductionLine(name="Linea 1", is_active=True)
        line_b = ProductionLine(name="Linea 2", is_active=True)
        db.add_all([line_a, line_b])
        db.flush()
        db.add_all(
            [
                Equipment(name="Bomba principal", production_line_id=line_a.id, is_active=True),
                Equipment(name="Compresor 1", production_line_id=line_a.id, is_active=True),
                Equipment(name="Transportador A", production_line_id=line_b.id, is_active=True),
                Equipment(name="Empacadora", production_line_id=line_b.id, is_active=True),
            ]
        )
    db.commit()
