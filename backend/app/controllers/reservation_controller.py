# app/controllers/reservation_controller.py
import logging
from typing import List, Tuple, Optional
import pandas as pd
from io import StringIO
import re
from datetime import date, datetime

from app.model.csv import ReservationRaw
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
JKT = ZoneInfo("Asia/Jakarta")

HEADER_TO_MODEL_MAP = {
    "Res No": "reservation_id",
    "Guest No": "guest_id",
    "First Name": "first_name",
    "Last Name": "last_name",
    "Room Number": "room_number",
    "Room Type": "room_type",
    "Arrangement": "arrangement",
    "In House Date": "in_house_date",
    "Arrival": "arrival_date",
    "Depart": "depart_date",
    "C/I Time": "check_in_time",
    "C/O Time": "check_out_time",
    "Created": "created_date",
    "Birth Date": "birth_date",
    "Age": "age",
    "Member No": "member_no",
    "Member Type": "member_type",
    "Email": "email",
    "Mobile Phone": "mobile_phone",
    "Mobile  Phone": "mobile_phone",
    "VIP": "vip_status",
    "Room Rate": "room_rate",
    "Lodging": "lodging",
    "Breakfast": "breakfast",
    "Lunch": "lunch",
    "Dinner": "dinner",
    "Other": "other_charges",
    "Bill Number": "bill_number",
    "Pay Article": "pay_article",
    "Rate Code": "rate_code",
    "Adult": "adult_count",
    "Child": "child_count",
    "Compliment": "compliment",
    "Nat": "nationality",
    "Local Region": "local_region",
    "Company / TA": "company_ta",
    "SOB": "sob",
    "Night": "nights",
    "Segment": "segment",
    "By": "created_by",
    "K-Card": "k_card",
    "remarks": "remarks",
}

def _to_int_or_none(raw: str) -> Optional[int]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    s = s.replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^\d\.\-]+", "", s)
    if s in ("", "-", ".", "-."):
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def _to_float_or_none(raw: str) -> Optional[float]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "").replace(" ", "")
    s = re.sub(r"[^\d.\-]+", "", s)
    if s in ("", "-", ".", "-.",):
        return None
    try:
        val = float(s)
        return -val if neg else val
    except Exception:
        return None

def _to_iso_yyyy_mm_dd_str(raw: str) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None

    s = str(raw).strip()
    if not s:
        return None

    s = re.sub(r"\b00:00(:00)?\b", "", s).strip()
    s = s.replace("/", "-")

    dt = None

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
                "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%m-%d-%Y %H:%M:%S"):
        try:
            dt = pd.to_datetime(s, format=fmt, errors="raise", utc=False)
            break
        except ValueError:
            dt = None

    if dt is None or pd.isna(dt):
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True, utc=False)
    if dt is None or pd.isna(dt):
        dt = pd.to_datetime(s, errors="coerce", dayfirst=False, utc=False)

    if dt is None or pd.isna(dt):
        return None

    py_dt = dt.to_pydatetime()
    return f"{py_dt.year:04d}-{py_dt.month:02d}-{py_dt.day:02d}"

def _to_local_midnight_dt(raw: str) -> Optional[datetime]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s:
        return None

    s = re.sub(r"\b00:00(:00)?\b", "", s).strip()

    dt = None
    
    try:
        dt = pd.to_datetime(s, format="%Y-%m-%d", errors="raise", utc=False)
    except ValueError:
        dt = None

    if pd.isna(dt):
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True, utc=False)

    if pd.isna(dt):
        dt = pd.to_datetime(s, errors="coerce", dayfirst=False, utc=False)

    if pd.isna(dt):
        return None

    d = dt.date()
    local_midnight = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=JKT)
    return local_midnight

def _to_str_or_none(raw: str) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    return s if s != "" else None

INT_FIELDS = {
    "reservation_id", "age", "adult_count", "child_count", "nights",
}

FLOAT_FIELDS = {
    "room_rate", "lodging", "breakfast", "lunch", "dinner", "other_charges"
}

STRING_DATE_FIELDS = {"in_house_date", "created_date", "birth_date"}

LOCAL_DATETIME_FIELDS = {"arrival_date", "depart_date"}

async def parse_reservation_csv(decoded_content: str, upload_id: int) -> Tuple[List[ReservationRaw], int]:
    rows_to_add: List[ReservationRaw] = []
    processed_row_count = 0
    df = None

    content_io = StringIO(decoded_content)

    try:
        df = pd.read_csv(content_io, skiprows=5)
        logger.info("Standard parsing with skiprows=5 successful!")
    except Exception as parse_error:
        logger.info(f"Standard parsing with skiprows=5 failed: {parse_error}")
        content_io.seek(0)
        try:
            df = pd.read_csv(
                content_io,
                skiprows=5,
                on_bad_lines='skip',
                quoting=3,
                sep=None,
                engine='python'
            )
            logger.info("Second parsing attempt with skiprows=5 successful!")
        except Exception as second_error:
            logger.info(f"Second parsing attempt with skiprows=5 failed: {second_error}")
    finally:
        content_io.close()

    if df is None or df.empty:
        raise ValueError("CSV file is empty or could not be parsed correctly after UTF-8 decoding.")

    logger.info("=== CSV COLUMNS DEBUG ===")
    logger.info(f"DataFrame shape: {df.shape}")
    actual_columns_before_clean = list(df.columns)
    logger.info(f"Actual columns found BEFORE cleaning: {actual_columns_before_clean}")

    logger.info("First 3 rows BEFORE cleaning:")
    logger.info(f"\n{df.head(3).to_string()}")

    logger.info("=== CLEANING HEADERS ===")
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    actual_columns_after_clean = list(df.columns)
    logger.info(f"Cleaned columns: {actual_columns_after_clean}")

    expected_cols_debug = list(HEADER_TO_MODEL_MAP.keys())
    logger.info(f"Expected columns (from map): {expected_cols_debug}")

    logger.info("=== FILTERING OUT SUMMARY SECTION ===")
    logger.info(f"Before filtering summary: {len(df)} records")
    df.dropna(how='all', inplace=True)
    logger.info(f"After dropna: {len(df)} records")

    cleaned_number_col = 'Number'
    if cleaned_number_col in df.columns:
        df['Number_numeric'] = pd.to_numeric(df[cleaned_number_col], errors='coerce')
        df = df[df['Number_numeric'].notna()].drop(columns=['Number_numeric'])
        logger.info(f"After filtering summary based on 'Number': {len(df)} records")
    else:
        logger.info(f"Column '{cleaned_number_col}' not found for summary filtering.")

    required_columns_cleaned = ['Arrival', 'Depart', 'Room Number']
    missing_cols = [col for col in required_columns_cleaned if col not in df.columns]
    if missing_cols:
        logger.info(f"Missing required columns AFTER cleaning: {missing_cols}. Available: {list(df.columns)}")
        raise ValueError(f"Missing required columns AFTER cleaning: {missing_cols}")

    processed_row_count = 0
    for index, row in df.iterrows():
        kwargs = {}
        valid_row = False

        for csv_header_orig, model_attr in HEADER_TO_MODEL_MAP.items():
            cleaned_header = ' '.join(csv_header_orig.strip().split())

            if cleaned_header == "Mobile Phone" and cleaned_header not in df.columns:
                cleaned_header_fallback = ' '.join("Mobile  Phone".strip().split())
                if cleaned_header_fallback in df.columns:
                    cleaned_header = cleaned_header_fallback

            if cleaned_header in df.columns and cleaned_header in row and pd.notna(row[cleaned_header]):
                raw_value = row[cleaned_header]

                try:
                    if model_attr in INT_FIELDS:
                        converted_value = _to_int_or_none(raw_value)
                    elif model_attr in FLOAT_FIELDS:
                        converted_value = _to_float_or_none(raw_value)
                    elif model_attr in STRING_DATE_FIELDS:
                        converted_value = _to_iso_yyyy_mm_dd_str(raw_value)
                    elif model_attr in LOCAL_DATETIME_FIELDS:
                        converted_value = _to_local_midnight_dt(raw_value)
                    else:
                        converted_value = _to_str_or_none(raw_value)

                except Exception as e:
                    logger.warning(
                        f"Row {index+6}: Error converting '{raw_value}' for '{cleaned_header}' -> {model_attr}. Set None. Error: {e}"
                    )
                    converted_value = None

                kwargs[model_attr] = converted_value
                valid_row = True

        if valid_row:
            rows_to_add.append(
                ReservationRaw(
                    csv_upload_id=upload_id,
                    **kwargs
                )
            )
            processed_row_count += 1

    if not rows_to_add:
        raise ValueError("No valid data rows found after parsing and filtering.")

    logger.info(f"Successfully parsed {processed_row_count} rows with type-safe conversion (int/float/date).")
    return rows_to_add, processed_row_count
