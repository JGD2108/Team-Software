from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Equipment, FailureMode, ProductionLine, Shift, User


DEFAULT_FAILURE_MODES = [
    "DA\u00d1O BANDA",
    "FALLA MEC\u00c1NICA",
    "FALLA EL\u00c9CTRICA",
    "TIEMPO A CORREGIR",
    "FALLA NEUM\u00c1TICA",
    "FALLA POR CODIFICADORA",
    "FALLA DE AUTOMATIZACI\u00d3N",
]


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
    for shift in ["1", "2", "3"]:
        if not db.query(Shift).filter(Shift.name == shift).first():
            db.add(Shift(name=shift, is_active=True))
    db.query(Shift).filter(Shift.name.notin_(["1", "2", "3"])).update({"is_active": False}, synchronize_session=False)
    for mode_name in DEFAULT_FAILURE_MODES:
        if not db.query(FailureMode).filter(FailureMode.name == mode_name).first():
            db.add(FailureMode(name=mode_name, is_active=True))
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
