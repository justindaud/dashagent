# app/controllers/transaction_resto_controller.py
import logging
from typing import List, Tuple
import pandas as pd
from io import StringIO
import re
from collections import defaultdict, deque
from datetime import datetime

from app.model.csv import JKT, TransactionRestoRaw

logger = logging.getLogger(__name__)

HEADER_TO_MODEL_MAP = {
    "Bill Number": "bill_number",
    "Article Number": "article_number",
    "Guest Name": "guest_name",
    "Description": "item_name",
    "Quantity": "quantity",
    "Sales": "sales",
    "Payment": "payment",
    "Outlet": "outlet",
    "Table Number": "table_number",
    "Posting ID": "posting_id",
    "Reservation Number": "reservation_number",
    "Travel Agent / Reserve Name": "travel_agent_name",
    "Date": "transaction_date",
    "Start Time": "start_time",
    "Close Time": "close_time",
    "Time": "time",
}

def remove_titles(name: str) -> str:
    if not isinstance(name, str):
        name = str(name or "")
    titles = ['MR', 'MRS', 'MS', 'MISS', 'DR', 'PROF', 'SIR', 'MADAM', 'BPK']
    name_parts = [part for part in name.split() if part.upper().strip(',') not in titles]
    return ' '.join(name_parts)


def reformat_name(name: str) -> str:
    name = str(name or "")
    name = remove_titles(name)
    if ',' in name:
        parts = [part.strip() for part in name.split(',')]
        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"
    return name.strip()


def formatting_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce')

    int_cols = ['Table Number', 'Bill Number', 'Article Number', 'Posting ID', 'Reservation Number']
    for col in int_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    currency_cols = ['Sales', 'Payment']
    for col in currency_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(',', '', regex=False)
                .replace('', '0')
            )
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    return df

def update_bill_numbers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Prev Bill Number'] = pd.to_numeric(df['Bill Number'], errors='coerce').fillna(0).astype(int)

    pat = re.compile(r'(?:To|From)\s+Table\s+\d+\s*\*(\d+)')

    adj = defaultdict(set)
    for _, row in df.iterrows():
        src = int(row['Bill Number'])
        desc = str(row.get('Description', ''))
        refs = {int(x) for x in pat.findall(desc)}
        for dst in refs:
            adj[src].add(dst)
            adj[dst].add(src)

    for b in df['Bill Number'].astype(int).unique():
        _ = adj[b]

    visited = set()
    comp_max = {}
    for start in adj.keys():
        if start in visited:
            continue
        q = deque([start])
        visited.add(start)
        comp = []
        mx = start
        while q:
            u = q.popleft()
            comp.append(u)
            if u > mx:
                mx = u
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        for u in comp:
            comp_max[u] = mx

    df['Bill Number'] = df['Bill Number'].astype(int).map(lambda b: comp_max.get(b, b))

    return df


def classify_article(article_number: int, outlet: str = 'Restaurant & Bar') -> str:
    outlet = (outlet or '').strip()

    if outlet == 'Restaurant & Bar':
        if 1 <= article_number <= 1000:
            return 'Food'
        elif 1001 <= article_number <= 2299:
            return 'Beverages'
        else:
            return 'Others'

    elif outlet == 'Room Service':
        if 1 <= article_number <= 499:
            return 'Food'
        elif 500 <= article_number <= 2999:
            return 'Beverages'
        else:
            return 'Others'

    elif outlet == 'Banquet':
        return 'Others'

    else:
        if 1 <= article_number <= 1000:
            return 'Food'
        elif 1001 <= article_number <= 2999:
            return 'Beverages'
        else:
            return 'Others'


def classify_subarticle(article_number: int, outlet: str = 'Restaurant & Bar') -> str:
    outlet = (outlet or '').strip()
    article_str = str(article_number)

    if outlet == 'Restaurant & Bar':
        if 1 <= article_number <= 1000:
            if 1 <= article_number <= 40:
                return 'Breakfast'
            elif 41 <= article_number <= 80:
                return 'Appetizer'
            elif 81 <= article_number <= 120:
                return 'Dessert'
            elif 121 <= article_number <= 160:
                return 'Pasta'
            elif 161 <= article_number <= 200:
                return 'Extra For Pasta'
            elif 201 <= article_number <= 240:
                return 'Pizza'
            elif 241 <= article_number <= 280:
                return 'Easy Bite'
            else:
                return 'Main Course'

        elif 1001 <= article_number <= 2999:
            if article_str.startswith('100'):
                return 'Coffee'
            elif article_str.startswith('104'):
                return 'Tea'
            elif article_str.startswith('108'):
                return 'Softdrink'
            elif article_str.startswith('112'):
                return 'Mineral Water'
            elif article_str.startswith('114'):
                return 'Juice'
            elif article_str.startswith('118'):
                return 'Mocktail'
            elif article_str.startswith('122'):
                return 'Mixer'
            elif article_str.startswith('200'):
                return 'Beer'
            elif article_str.startswith(('204', '205', '206', '207', '208')):
                return 'Cocktail'
            elif article_str.startswith(('210', '211', '212', '213', '214', '215')):
                return 'Shoot'
            elif article_str.startswith('22'):
                return 'Bottle'
            else:
                return 'Beverages'

        elif article_number >= 2300:
            if article_str.startswith('23'):
                return 'Promo'
            elif article_str.startswith('30'):
                return 'Cigarette'
            elif article_str.startswith('31'):
                return 'Miscellaneous'
            elif article_str.startswith('35') and article_number not in [3514, 3515, 3516]:
                return 'Merchandise'
            elif article_str.startswith('40'):
                return 'Soju'
            elif article_str.startswith('69'):
                return 'Compliment Cake'
            elif article_str.startswith('891'):
                return 'Discount'
            elif article_str.startswith('98'):
                return 'Compliment'
            elif article_str.startswith('990'):
                return 'Cash'
            elif article_str.startswith('991'):
                return 'Voucher'
            elif article_str.startswith('993'):
                return 'Credit Card'
            elif article_str.startswith('995'):
                return 'City Ledger'
            else:
                return 'Others'

    elif outlet == 'Room Service':
        if 1 <= article_number <= 10:
            return 'Dessert'
        elif 40 <= article_number <= 49:
            return 'Pasta'
        elif 121 <= article_number <= 129:
            return 'Pizza'
        elif 160 <= article_number <= 199:
            return 'Snack'
        elif 200 <= article_number <= 499:
            return 'Main Course'
        elif 500 <= article_number <= 599:
            return 'Beer'
        elif 600 <= article_number <= 699:
            return 'Cocktail'
        elif 700 <= article_number <= 799:
            return 'Canned'
        elif 800 <= article_number <= 899:
            return 'Water'
        elif 900 <= article_number <= 999:
            return 'Coffee'
        elif 1000 <= article_number <= 1099:
            return 'Mocktail'
        elif 1100 <= article_number <= 1199:
            return 'Tea'
        elif 1200 <= article_number <= 1299:
            return 'Juice'
        elif 2000 <= article_number <= 2999:
            return 'Bottle'
        elif 3000 <= article_number <= 3099:
            return 'Promo'
        else:
            return 'Others'

    elif outlet == 'Banquet':
        if article_number == 3:
            return 'Room Rental'
        elif article_number == 4:
            return 'Coffee Break'
        elif article_number == 5:
            return 'Lunch'
        elif article_number == 6:
            return 'Dinner'
        else:
            return 'Other'

    return 'Unknown'

def _to_str_or_none(val):
    if val is None:
        return None
    s = str(val).strip()
    return s if s != "" else None

def process_outlet_data(df: pd.DataFrame, outlet_name: str) -> pd.DataFrame:
    if df.empty:
        return df

    logger.info(f"🔧 Processing {outlet_name} outlet...")

    df = df.copy()

    if 'Guest Name' in df.columns:
        df['Guest Name'] = df['Guest Name'].apply(reformat_name)

    df = formatting_data(df)

    df = update_bill_numbers(df)

    grouped_df = df.groupby(['Bill Number', 'Article Number'], as_index=False).agg({
        'Description': 'first',
        'Date': 'last',
        'Table Number': 'last',
        'Quantity': 'sum',
        'Sales': 'sum',
        'Payment': 'sum',
        'Outlet': 'first',
        'Posting ID': 'first',
        'Start Time': 'first',
        'Close Time': 'last',
        'Time': 'max',
        'Guest Name': 'first',
        'Travel Agent / Reserve Name': 'first',
        'Reservation Number': 'first',
        'Prev Bill Number': 'first',
    })

    disc = grouped_df[grouped_df['Article Number'].astype(str).str.startswith('891')]
    comp = grouped_df[(grouped_df['Article Number'] > 9800) & (grouped_df['Article Number'] < 9900)]

    disc_per_bill = disc.groupby('Bill Number')['Sales'].sum()
    comp_per_bill = comp.groupby('Bill Number')['Payment'].sum()

    grouped_df['Bill Discount'] = grouped_df['Bill Number'].map(disc_per_bill).fillna(0.0)
    grouped_df['Bill Compliment'] = grouped_df['Bill Number'].map(comp_per_bill).fillna(0.0)
    grouped_df['Total Deduction'] = grouped_df['Bill Discount'] + grouped_df['Bill Compliment']

    if not disc.empty:
        grouped_df = grouped_df.drop(disc.index)
    if not comp.empty:
        grouped_df = grouped_df.drop(comp.index)

    drop_idx = grouped_df[
        (grouped_df['Quantity'] == 0) &
        (grouped_df['Sales'] == 0) &
        (grouped_df['Payment'] == 0)
    ].index
    if not drop_idx.empty:
        grouped_df = grouped_df.drop(drop_idx)

    grouped_df['Article Number'] = grouped_df['Article Number'].replace('', 0).astype(int)

    outlet_name_effective = grouped_df['Outlet'].iloc[0] if not grouped_df.empty else outlet_name

    grouped_df['Article'] = grouped_df['Article Number'].apply(
        lambda x: classify_article(x, outlet_name_effective)
    )
    grouped_df['Subarticle'] = grouped_df['Article Number'].apply(
        lambda x: classify_subarticle(x, outlet_name_effective)
    )

    logger.info(f"   - {outlet_name} processed: {grouped_df.shape[0]} records")
    return grouped_df


async def parse_transaction_resto_csv(decoded_content: str, upload_id: int) -> Tuple[List[TransactionRestoRaw], int]:
    rows_to_add: List[TransactionRestoRaw] = []
    processed_row_count = 0
    df = None

    content_io = StringIO(decoded_content)

    try:
        df = pd.read_csv(content_io, skiprows=2)
        logger.info("Standard parsing with skiprows=2 successful!")
    except Exception as parse_error:
        logger.info(f"Standard parsing with skiprows=2 failed: {parse_error}")
        content_io.seek(0)
        try:
            df = pd.read_csv(
                content_io,
                skiprows=2,
                on_bad_lines='skip',
                quoting=3,
                sep=None,
                engine='python'
            )
            logger.info("Second parsing attempt with skiprows=2 successful!")
        except Exception as second_error:
            logger.info(f"Second parsing attempt with skiprows=2 failed: {second_error}")
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

    if 'Outlet' in df.columns:
        resto = df[df['Outlet'] == 'Restaurant & Bar']
        roomservice = df[df['Outlet'] == 'Room Service']
        banquet = df[df['Outlet'] == 'Banquet']

        logger.info("📊 Data split by outlet:")
        logger.info(f"   - Restaurant & Bar: {resto.shape[0]} records")
        logger.info(f"   - Room Service: {roomservice.shape[0]} records")
        logger.info(f"   - Banquet: {banquet.shape[0]} records")
    else:
        resto = df[df['Date'].notna()]
        roomservice = pd.DataFrame()
        banquet = pd.DataFrame()

    df.dropna(how='all', inplace=True)
    logger.info(f"After dropna(how='all'): {len(df)} records")

    required_columns_cleaned = [
        'Date', 'Table Number', 'Bill Number', 'Article Number', 'Description',
        'Quantity', 'Sales', 'Payment', 'Outlet', 'Posting ID',
        'Start Time', 'Close Time', 'Time',
        'Guest Name', 'Travel Agent / Reserve Name', 'Reservation Number'
    ]
    missing_cols = [col for col in required_columns_cleaned if col not in df.columns]
    if missing_cols:
        logger.info(f"Missing required columns AFTER cleaning: {missing_cols}. Available: {list(df.columns)}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    processed_dfs = []

    if not resto.empty:
        resto_processed = process_outlet_data(resto, "Restaurant & Bar")
        if not resto_processed.empty:
            processed_dfs.append(resto_processed)

    if not roomservice.empty:
        roomservice_processed = process_outlet_data(roomservice, "Room Service")
        if not roomservice_processed.empty:
            processed_dfs.append(roomservice_processed)

    if not banquet.empty:
        banquet_processed = process_outlet_data(banquet, "Banquet")
        if not banquet_processed.empty:
            processed_dfs.append(banquet_processed)

    if processed_dfs:
        grouped_df = pd.concat(processed_dfs, ignore_index=True)
        logger.info(f"📊 Combined processed data shape: {grouped_df.shape}")
    else:
        grouped_df = pd.DataFrame()
        logger.warning("⚠️ No data to process after outlet separation")

    if grouped_df.empty:
        raise ValueError("No valid data rows found after processing transaction resto CSV.")

    for index, row in grouped_df.iterrows():
        try:
            ts = row.get('Date')
            if isinstance(ts, pd.Timestamp):
                py_dt = ts.to_pydatetime()
            elif ts is None or (isinstance(ts, float) and pd.isna(ts)):
                py_dt = None
            else:
                py_dt = pd.to_datetime(ts, errors='coerce')
                if isinstance(py_dt, pd.Timestamp):
                    py_dt = py_dt.to_pydatetime()
                else:
                    py_dt = None

            if py_dt is not None and py_dt.tzinfo is None:
                py_dt = py_dt.replace(tzinfo=JKT)

            bill_number = _to_str_or_none(row.get('Bill Number'))
            article_number = _to_str_or_none(row.get('Article Number'))
            guest_name = _to_str_or_none(row.get('Guest Name'))
            item_name = _to_str_or_none(row.get('Description'))

            quantity = int(row.get('Quantity', 0) or 0)
            sales_val = float(row.get('Sales', 0) or 0)
            sales = int(round(sales_val * 100))

            article_category = _to_str_or_none(row.get('Article', ''))
            article_subcategory = _to_str_or_none(row.get('Subarticle', ''))

            outlet = _to_str_or_none(row.get('Outlet', ''))
            table_number = int(row.get('Table Number', 0) or 0)
            posting_id = _to_str_or_none(row.get('Posting ID', ''))
            reservation_number = _to_str_or_none(row.get('Reservation Number', ''))
            travel_agent_name = _to_str_or_none(row.get('Travel Agent / Reserve Name', ''))
            prev_bill_number = _to_str_or_none(row.get('Prev Bill Number', ''))

            bill_discount = float(row.get('Bill Discount', 0) or 0)
            bill_compliment = float(row.get('Bill Compliment', 0) or 0)
            total_deduction = float(row.get('Total Deduction', 0) or 0)

            start_time = _to_str_or_none(row.get('Start Time', ''))
            close_time = _to_str_or_none(row.get('Close Time', ''))
            time_str = _to_str_or_none(row.get('Time', ''))

            tr = TransactionRestoRaw(
                csv_upload_id=upload_id,
                bill_number=bill_number,
                article_number=article_number,
                guest_name=guest_name,
                item_name=item_name,
                quantity=quantity,
                sales=sales,
                payment=sales,
                outlet=outlet,
                table_number=table_number,
                posting_id=posting_id,
                reservation_number=reservation_number,
                travel_agent_name=travel_agent_name,
                prev_bill_number=prev_bill_number,
                transaction_date=py_dt,
                start_time=start_time,
                close_time=close_time,
                time=time_str,
                bill_discount=bill_discount,
                bill_compliment=bill_compliment,
                total_deduction=total_deduction,
                article_category=article_category,
                article_subcategory=article_subcategory,
            )

            rows_to_add.append(tr)
            processed_row_count += 1

        except Exception as e:
            logger.warning(
                f"Row {index + 2}: error building TransactionRestoRaw, skipped. Error: {e}"
            )
            continue

    if not rows_to_add:
        raise ValueError("No valid data rows found after parsing and filtering.")

    logger.info(f"Successfully parsed {processed_row_count} rows from transaction_resto CSV.")
    return rows_to_add, processed_row_count
