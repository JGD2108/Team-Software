from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "plant_user"


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    role: str | None = None
    is_active: bool | None = None


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
    code: str | None = None
    is_active: bool = True


class LineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None = None
    is_active: bool


class EquipmentIn(BaseModel):
    name: str
    production_line_id: int
    code: str | None = None
    is_active: bool = True


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    production_line_id: int | None
    code: str | None = None
    parent_code: str | None = None
    hierarchy_level: int | None = None
    plant_code: str | None = None
    plant_name: str | None = None
    area_code: str | None = None
    area_name: str | None = None
    process_code: str | None = None
    process_name: str | None = None
    is_reportable: bool
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    location: str | None = None
    qr_code: str | None = None
    criticality: str | None = None
    specialty: str | None = None
    grouping: str | None = None
    analysis_group: str | None = None
    pdt_group: str | None = None
    source_status: str | None = None
    financial_code: str | None = None
    cost_center: str | None = None
    is_active: bool


class FailureModeIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    is_active: bool = True


class FailureModeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool


class DailyReportIn(BaseModel):
    event_date: date
    production_line_id: int
    shift_id: int
    equipment_id: int
    failure_mode_id: int
    damage_description: str = Field(min_length=3, max_length=500)
    reason_description: str = Field(min_length=3, max_length=500)
    downtime_minutes: float = Field(gt=0, le=1440)
    frequency: int = Field(ge=1, le=1000)


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
    damage_description: str | None = None
    reason_description: str | None = None
    downtime_minutes: float | None = None
    frequency: float | None = None
    event_date: date | None = None


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
