# app/controllers/profile_guest_controller.py
import logging
from typing import List, Tuple, Optional
import pandas as pd
from io import StringIO
import re
import phonenumbers

from app.model.csv import ProfileGuestRaw

logger = logging.getLogger(__name__)

HEADER_TO_MODEL_MAP = {
    "Guest No": "guest_id",
    "Name": "name",
    "Email": "email",
    "Phone": "phone",
    "Address": "address",
    "Birth Date": "birth_date",
    "Occupation": "occupation",
    "City": "city",
    "Country": "country",
    "Segment": "segment",
    "Type ID": "type_id",
    "ID No.": "id_no",
    "Sex": "sex",
    "Zip": "zip_code",
    "L-Region": "local_region",
    "Telefax": "telefax",
    "Mobile No.": "mobile_no",
    "Comments": "comments",
    "Credit Lim": "credit_limit",
}

def strip_country_code(phone: str):
    if phone == '0':
        return ''
    
    if not(re.match(r"^\+?\d+$", phone)):
        return ''

    if phone.startswith("0"):
        return f"+62{phone[1:]}"
    
    if phone.startswith("8"):
        return f"+62{phone}"
    try:
        num = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(num):
            return str(phone) 
        else:
            return ''
    except:
        return ''

def clean_phone_number(phone: str):
    if pd.isna(phone) or phone == '':
        return ''
    
    phone_str = str(phone).strip()
    phone_str = phone_str.replace('"', '').replace('=', '').strip()
    
    phone_str = ''.join(filter(str.isdigit, phone_str))
    
    if phone_str:
        phone_str = strip_country_code(phone_str)
    
    return phone_str

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

def _to_str_or_none(raw: str) -> Optional[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    return s if s != "" else None

STRING_DATE_FIELDS = {"birth_date"}

async def parse_profile_guest_csv(decoded_content: str, upload_id: int) -> Tuple[List[ProfileGuestRaw], int]:
    rows_to_add: List[ProfileGuestRaw] = []
    processed_row_count = 0
    df = None

    content_io = StringIO(decoded_content)

    try:
        df = pd.read_csv(content_io, skiprows=6) 
        logger.info("Standard parsing with skiprows=6 successful!")
    except Exception as parse_error:
        logger.info(f"Standard parsing with skiprows=6 failed: {parse_error}")
        content_io.seek(0)
        try:
            df = pd.read_csv(
                content_io,
                skiprows=6,
                on_bad_lines='skip',
                quoting=3,
                sep=None,
                engine='python'
            )
            logger.info("Second parsing attempt with skiprows=6 successful!")
        except Exception as second_error:
            logger.info(f"Second parsing attempt with skiprows=6 failed: {second_error}")
    finally:
        content_io.close()

    if df is None or df.empty:
        raise ValueError("CSV file is empty or could not be parsed correctly after UTF-8 decoding.")

    logger.info("=== CSV COLUMNS DEBUG ===")
    logger.info(f"DataFrame shape: {df.shape}")
    actual_columns_before_clean = list(df.columns)
    logger.info(f"Actual columns found BEFORE cleaning: {actual_columns_before_clean}")

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

    logger.info("=== CLEANING GUEST PROFILE DATA ===")
    logger.info(f"Before dataframe cleaning: {len(df)} records")
    df = (
        df
        .dropna(how='all')
        .fillna('')
        .map(lambda x: str(x).replace("\t", "").strip() if isinstance(x, str) else x)
        .map(
            lambda x: x.strip('"').strip("'") if isinstance(x, str) else x
        )
    )
    logger.info(f"After dataframe cleaning: {len(df)} records")

    required_columns_cleaned = ['Name']
    missing_cols = [col for col in required_columns_cleaned if col not in df.columns]
    if missing_cols:
        logger.info(f"Missing required columns AFTER cleaning: {missing_cols}. Available: {list(df.columns)}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info("=== CLEANING PHONE NUMBERS (Vectorized) ===")
    
    if 'Phone' in df.columns:
        logger.info("Cleaning 'Phone' column...")
        df['Phone'] = df['Phone'].apply(clean_phone_number)
    
    if 'Mobile No.' in df.columns:
        logger.info("Cleaning 'Mobile No.' column...")
        df['Mobile No.'] = df['Mobile No.'].apply(clean_phone_number)
        
        if 'Phone' in df.columns:
            logger.info("Applying 'Phone' as fallback to 'Mobile No.'...")
            df['Mobile No.'] = df['Mobile No.'].fillna(df['Phone'])

    processed_row_count = 0
    for index, row in df.iterrows():
        kwargs = {}
        valid_row = False

        for csv_header_orig, model_attr in HEADER_TO_MODEL_MAP.items():
            cleaned_header = ' '.join(csv_header_orig.strip().split())

            if cleaned_header in df.columns and cleaned_header in row and pd.notna(row[cleaned_header]):
                raw_value = row[cleaned_header]
                converted_value = None

                try:
                    if model_attr in STRING_DATE_FIELDS:
                        converted_value = _to_iso_yyyy_mm_dd_str(raw_value)
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
                ProfileGuestRaw(
                    csv_upload_id=upload_id,
                    **kwargs
                )
            )
            processed_row_count += 1

    if not rows_to_add:
         raise ValueError("No valid data rows found after parsing and filtering.")

    logger.info(f"Successfully parsed {processed_row_count} rows from profile_guest CSV.")
    return rows_to_add, processed_row_count