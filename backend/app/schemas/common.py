from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LoginIn(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "plant_user"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LineIn(BaseModel):
    name: str
    is_active: bool = True


class LineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool


class EquipmentIn(BaseModel):
    name: str
    production_line_id: int
    is_active: bool = True


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    production_line_id: int
    is_active: bool


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_hash: str
    uploaded_at: datetime
    status: str
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int


class CorrectionIn(BaseModel):
    production_line_id: int | None = None
    equipment_id: int | None = None
    shift_name: str | None = None


class DashboardFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    year: int | None = None
    month: int | None = None
    production_line_id: int | None = None
    equipment_id: int | None = None
    shift_id: int | None = None


class ReportRequest(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    production_line_id: int | None = None
    equipment_id: int | None = None
    shift_id: int | None = None
