# app/controllers/chat_whatsapp_controller.py
import logging
from typing import List, Tuple, Optional
import pandas as pd
from io import StringIO
from app.model.csv import ChatWhatsappRaw, JKT

logger = logging.getLogger(__name__)

HEADER_TO_MODEL_MAP = {
    "Chats": "phone_number",
    "Type": "message_type",
    "Date": "message_date",
    "Content": "message",
}

def _parse_custom_date(raw_date_series: pd.Series) -> pd.Series:
    parsed_dates = pd.to_datetime(raw_date_series, format='%m-%d-%Y %H.%M.%S', errors='coerce')
    
    failed_mask = pd.isna(parsed_dates)
    if failed_mask.any():
        parsed_dates[failed_mask] = pd.to_datetime(
            raw_date_series[failed_mask], 
            format='%d-%m-%Y %H.%M.%S', 
            errors='coerce'
        )

    failed_mask = pd.isna(parsed_dates)
    if failed_mask.any():
        parsed_dates[failed_mask] = pd.to_datetime(
            raw_date_series[failed_mask], 
            format='%d-%m-%y %H.%M.%S', 
            errors='coerce'
        )

    failed_mask = pd.isna(parsed_dates)
    if failed_mask.any():
        logger.info(f"Failed to parse {failed_mask.sum()} dates with specific formats, trying fallback...")
        parsed_dates[failed_mask] = pd.to_datetime(
            raw_date_series[failed_mask], 
            errors='coerce' 
        )
    return parsed_dates

async def parse_chat_whatsapp_csv(decoded_content: str, upload_id: int) -> Tuple[List[ChatWhatsappRaw], int]:
    rows_to_add: List[ChatWhatsappRaw] = []
    processed_row_count = 0
    df = None

    content_io = StringIO(decoded_content)

    try:
        df = pd.read_csv(content_io) 
        logger.info("Standard parsing successful!")
    except Exception as parse_error:
        logger.info(f"Standard parsing failed: {parse_error}")
        content_io.seek(0)
    finally:
        content_io.close()

    if df is None or df.empty:
        raise ValueError("CSV file is empty or could not be parsed correctly after UTF-8 decoding.")
    
    logger.info(f"Initial data read, {len(df)} rows.")
    
    logger.info("=== CLEANING HEADERS ===")
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    
    logger.info(f"CSV columns found after cleaning: {list(df.columns)}")

    required_columns_cleaned = ['Content', 'Chats']
    missing_cols = [col for col in required_columns_cleaned if col not in df.columns]
    if missing_cols:
        logger.info(f"Missing required columns AFTER cleaning: {missing_cols}. Available: {list(df.columns)}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info("=== RUNNING FILTER TRANSFORMATION LOGIC ===")
    df = df.dropna(subset=['Type'])
    df = df.replace("\t", "", regex=True)
    df = df.replace("", None, regex=True)
    df = df.drop_duplicates()

    group_chat_window = df[~df['Chats'].str.startswith('+', na=False)]

    group_chat_window_names = group_chat_window['Name'].unique(),group_chat_window['Name'].count()

    guest_chat_window = df[~df['Name'].isin(group_chat_window_names[0])]

    df = guest_chat_window[~guest_chat_window['Chats'].isin(group_chat_window_names[0])]

    df = df.copy()

    logger.info("=== CONVERTING DATA TYPES ===")
    if 'Date' in df.columns:
        logger.info("Converting 'Date' column...")
        df.loc[:, 'Date'] = _parse_custom_date(df['Date'])
        failed_dates = df['Date'].isna().sum()

    if failed_dates > 0:
        logger.warning(f"{failed_dates} date values could not be parsed and will be set to NULL.")

    df = df.dropna(subset=['Date']).copy()
    logger.info(f"After filtering invalid dates: {len(df)} rows.")

    logger.info("=== PROCESSING ROWS ===")
    processed_row_count = 0
    for index, row in df.iterrows():
        kwargs ={}
        valid_row = False
        
        for csv_header_orig, model_attr in HEADER_TO_MODEL_MAP.items():
            cleaned_header = ' '.join(csv_header_orig.strip().split())

            if cleaned_header in df.columns and pd.notna(row[cleaned_header]):
                raw_value = row[cleaned_header]
                converted_value = None
                try:
                    if isinstance(raw_value, pd.Timestamp):
                        py_datetime = raw_value.to_pydatetime()
                        
                        if model_attr == 'message_date' and py_datetime.tzinfo is None:
                            converted_value = py_datetime.replace(tzinfo=JKT)
                        else:
                            converted_value = py_datetime
                        
                    else:
                        converted_value = str(raw_value).strip()

                    kwargs[model_attr] = converted_value
                    valid_row = True
                        
                except Exception as e:
                    logger.warning(f"Error converting row {index} for {model_attr}: {e}")
                    converted_value = None

        if valid_row:
            rows_to_add.append(
                ChatWhatsappRaw(
                    csv_upload_id=upload_id,
                    **kwargs
                )
            )
            processed_row_count += 1

    if not rows_to_add:
        raise ValueError("No valid data rows found after parsing and filtering.")

    logger.info(f"Successfully parsed {processed_row_count} rows from chat_whatsapp CSV.")
    return rows_to_add, processed_row_count