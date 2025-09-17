import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import UploadFile, HTTPException
from app.models import CSVUpload, Reservasi, ReservasiProcessed
from io import StringIO

import phonenumbers
import re

class ReservasiHandler:
    """Handler for reservation CSV files"""

    def strip_country_code(self, phone: str):
        if phone.startswith("0"):
            # If starts with 0, assume Indonesia country code 62
            return f"+62{phone[1:]}"
        try:
            num = phonenumbers.parse(phone, None)
            if phonenumbers.is_valid_number(num):
                # Return with country code but without + symbol
                # return f"{num.country_code}{num.national_number}"
                return str(phone)
            else:
                return ''
        except:
            return ''
    
    def clean_phone_number(self, phone: str):
        """Clean phone number using user's proven logic"""
        if pd.isna(phone) or phone == '':
            return ''
        
        phone_str = str(phone).strip()
        # Remove quotes and equals signs
        phone_str = phone_str.replace('"', '').replace('=', '').strip()
        
        # Remove non-digits
        phone_str = ''.join(filter(str.isdigit, phone_str))
        
        # Apply country code stripping
        if phone_str:
            phone_str = self.strip_country_code(phone_str)
        
        return phone_str
    
    def clean_birth_date(self, birth_date):
        """Clean birth date with validation"""
        if pd.isna(birth_date) or birth_date == '':
            return ''
        
        try:
            # Parse date
            parsed_date = pd.to_datetime(birth_date, errors='coerce')
            if pd.notna(parsed_date):
                # Filter out unreasonable dates
                current_year = pd.Timestamp.now().year
                if parsed_date.year > current_year or parsed_date.year < 1900:
                    return ''
                
                return parsed_date.strftime('%Y-%m-%d')
            else:
                return ''
        except:
            return ''
    
    async def process_csv(self, file: UploadFile, db: Session) -> dict:
        """
        Process reservation CSV file based on actual CSV structure
        Expected columns: Number, In House Date, Room Number, Room Type, Guest No, First Name, Last Name, 
        Arrival, Depart, Night, Room Rate, Segment, etc.
        """
        try:
            # Read CSV content with robust parsing and skiprows=5 for reservasi
            content = await file.read()
            
            # Try different CSV parsing strategies with skiprows=5
            try:
                # First attempt: standard parsing with skiprows=5
                df = pd.read_csv(StringIO(content.decode('utf-8')), skiprows=5)
                print("Standard parsing with skiprows=5 successful!")
            except Exception as parse_error:
                print(f"Standard parsing with skiprows=5 failed: {parse_error}")
                
                try:
                    # Second attempt: with error handling and skiprows
                    df = pd.read_csv(
                        StringIO(content.decode('utf-8')),
                        skiprows=5,
                        on_bad_lines='skip',  # Skip bad lines
                        quoting=3,              # QUOTE_NONE - disable quotes
                        sep=None,               # Auto-detect separator
                        engine='python'         # Use Python engine for better error handling
                    )
                    print("Second parsing attempt with skiprows=5 successful!")
                except Exception as second_error:
                    print(f"Second parsing attempt with skiprows=5 failed: {second_error}")
                    
                    # Third attempt: manual parsing with pandas and skiprows
                    df = pd.read_csv(
                        StringIO(content.decode('utf-8')),
                        skiprows=5,
                        engine='python',
                        sep=None,
                        quoting=3,
                        on_bad_lines='skip'  # Skip bad lines
                    )
                    print("Third parsing attempt with skiprows=5 successful!")
            
            # Debug: Log actual CSV columns
            print(f"=== CSV COLUMNS DEBUG ===")
            print(f"DataFrame shape: {df.shape}")
            print(f"Actual columns found: {list(df.columns)}")
            print(f"Expected columns: ['Number', 'In House Date', 'Room Number', 'Room Type', 'Guest No', 'First Name', 'Last Name', 'Arrival', 'Depart', 'Night', 'Room Rate', 'Segment']")
            
            # Show first few rows for debugging
            print(f"First 3 rows:")
            print(df.head(3).to_string())
            
            # Filter out summary section
            print("=== FILTERING OUT SUMMARY SECTION ===")
            print(f"Before filtering summary: {len(df)} records")
            
            # Filter out rows that contain summary data
            if 'Number' in df.columns:
                # Remove rows where Number column is empty or contains summary data
                df = df[df['Number'].notna() & (df['Number'] != '')]
                
                # Additional filter: remove rows that look like summary
                df = df[~df['Number'].str.contains('Summary', case=False, na=False)]
                df = df[~df['Number'].str.contains('Room Type', case=False, na=False)]
                
                print(f"After filtering summary: {len(df)} records")
            
            # Validate required columns (based on actual CSV structure)
            required_columns = ['Arrival', 'Depart', 'Room Number']
            if not all(col in df.columns for col in required_columns):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns. Expected: {required_columns}"
                )
            
            # Create CSV upload record
            csv_upload = CSVUpload(
                filename=file.filename,
                file_type="reservasi",
                status="processing"
            )
            db.add(csv_upload)
            db.commit()
            db.refresh(csv_upload)
            
            # Clean and process data based on user's notes
            print("=== CLEANING RESERVATION DATA ===")

            # [Add] Whole Dataframe Cleaning
            df = (
                df
                .dropna(how='all')
                .fillna('')
                .map(lambda x: str(x).replace("\t", "").strip() if isinstance(x, str) else x)
                .map(
                    lambda x: x.strip('"').strip("'") if isinstance(x, str) else x
                )
            )
            
            # Clean guest names (combine First Name + Last Name) - approach user yang terbukti
            if 'First Name' in df.columns and 'Last Name' in df.columns:
                df['First Name'] = df['First Name'].replace(['', 'NULL', 'NaN', 'nan', None], '')
                df['Last Name'] = df['Last Name'].replace(['', 'NULL', 'NaN', 'nan', None], '')
                
                df['First Name'] = df['First Name'].fillna('')
                df['Last Name'] = df['Last Name'].fillna('')
                
                df['Guest Name'] = (df['First Name'] + ' ' + df['Last Name']).str.strip().str.upper()
                df = df[df['Guest Name'] != '']
                print(f"Guest names cleaned and combined: {len(df)} records")
            
            # [Add] Normalize Birth Date Format
            if 'Birth Date' in df.columns:
                df['Birth Date'] = df['Birth Date'].apply(self.clean_birth_date)

            # Clean room details
            if 'Room Number' in df.columns:
                df['Room Number'] = df['Room Number'].str.strip()
            
            if 'Room Type' in df.columns:
                df['Room Type'] = df['Room Type'].str.strip().str.upper()
            
            # Parse dates - Handle DD/MM/YYYY format with dayfirst=True (approach user yang terbukti)
            date_columns = ['Arrival', 'Depart', 'In House Date', 'Created']
            for col in date_columns:
                if col in df.columns:
                    # Handle DD/MM/YYYY format with dayfirst=True
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                    # Convert to string format for database compatibility
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
            
            # Clean time fields
            time_columns = ['C/I Time', 'C/O Time']
            for col in time_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format='%H:%M', errors='coerce').dt.strftime('%H:%M')
            
            # Clean Mobile Phone
            if 'Mobile Phone' in df.columns:
                df['Mobile Phone'] = df['Mobile Phone'].apply(self.clean_phone_number)

            # Clean email
            if 'Email' in df.columns:
                df['Email'] = df['Email'].str.strip().str.lower()
                df['Email'] = df['Email'].replace(['', 'NULL', 'NaN', 'nan'], '')
            
            # Convert numeric fields
            # Handle currency columns (remove commas before converting)
            currency_columns = ['Room Rate', 'Lodging', 'Breakfast', 'Lunch', 'Dinner', 'Other']
            for col in currency_columns:
                if col in df.columns:
                    # Remove commas (thousand separators), keep dots (decimal separators)
                    df[col] = df[col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
            
            # Handle other numeric columns normally
            other_numeric_columns = ['Age', 'Adult', 'Child', 'Night']
            for col in other_numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Clean other fields
            if 'Segment' in df.columns:
                df['Segment'] = df['Segment'].str.strip().str.upper()
            
            # [Add] Normalize NA in remarks
            if 'remarks' in df.columns:
                df['remarks'] = (
                    df['remarks']
                    .str.strip()
                    .apply(
                        lambda x: "" 
                        if (
                            x.upper() in ["NAN", "NONE", "NULL", "NA", "N A", "N/A"]  # hanya NA
                            or re.fullmatch(r"[\W_]+", x) is not None   # hanya simbol/non-alfanumerik
                        ) else x
                    )
                )
            
            # Group reservation with multiple rows (approach user yang terbukti)
            if 'Guest Name' in df.columns and 'Arrival' in df.columns and 'Depart' in df.columns and 'Room Number' in df.columns:
                print("Applying groupby logic for multi-row reservations...")
                print(f"Before groupby: {len(df)} records")
                
                df = df.groupby(['Guest Name', 'Arrival', 'Depart', 'Room Number'], as_index=False).agg({
                    'In House Date': 'first',
                    'Room Type': 'first',
                    'Arrangement': 'first',
                    'Guest No': 'first',
                    'Age': 'first',
                    'Local Region': 'first',
                    'Room Rate': 'mean',
                    'Lodging': 'mean',
                    'Breakfast': 'mean',
                    'Lunch': 'mean',
                    'Dinner': 'mean',
                    'Other': 'mean',
                    'Bill Number': 'first',
                    'Pay Article': 'first',
                    'Res No': 'first',
                    'Adult': 'first',
                    'Child': 'first',
                    'Nat': 'first',
                    'Company / TA': 'first',
                    'SOB': 'first',
                    'Night': 'first',
                    'C/I Time': 'first',
                    'C/O Time': 'first',
                    'Segment': 'first',
                    'Created': 'first',
                    'By': 'first',
                    'remarks': 'first',
                    'Mobile  Phone': 'first',  # Note: CSV has double space
                    'Email': 'first',
                })
                print(f"After groupby: {len(df)} records")
            
            # Process each row with upsert logic
            rows_processed = 0
            rows_updated = 0
            rows_inserted = 0
            
            for _, row in df.iterrows():
                try:
                    # Get guest name
                    guest_name = str(row.get('Guest Name', ''))
                    if not guest_name:
                        guest_name = f"{str(row.get('First Name', ''))} {str(row.get('Last Name', ''))}".strip()
                    
                    # Get dates - parse as DateTime for Processed table consistency
                    in_house_date = str(row.get('In House Date', ''))
                    arrival_date = pd.to_datetime(row.get('Arrival', ''))
                    depart_date = pd.to_datetime(row.get('Depart', ''))
                    room_number = str(row['Room Number'])
                    
                    # Generate unique guest_id since source system doesn't provide valid Guest No
                    # Use combination of guest_name + room_number + arrival_date to create unique identifier
                    guest_id = str(row.get('Guest No', ''))
                    if guest_id == 'nan' or pd.isna(row.get('Guest No')) or guest_id == '':
                        # Create unique guest_id based on available data
                        if guest_name and room_number:
                            guest_id = f"{guest_name}_{room_number}_{arrival_date.strftime('%Y%m%d')}".replace(' ', '_').replace('-', '_')[:50]
                        elif guest_name:
                            guest_id = f"{guest_name}_{arrival_date.strftime('%Y%m%d')}_{rows_processed}".replace(' ', '_')[:50]
                        else:
                            guest_id = f"GUEST_{csv_upload.id}_{rows_processed}"
                    
                    # Calculate total amount
                    room_rate = float(row.get('Room Rate', 0)) if pd.notna(row.get('Room Rate')) else 0
                    nights = int(row.get('Night', 1)) if pd.notna(row.get('Night')) else 1
                    total_amount = room_rate * nights
                    
                    # Always INSERT into Raw table (Reservasi)
                    reservation_raw = Reservasi(
                        csv_upload_id=csv_upload.id,
                        reservation_id=str(row.get('Res No', '')),
                        guest_id=guest_id,
                        guest_name=guest_name,
                        room_number=room_number,
                        room_type=str(row.get('Room Type', '')),
                        arrangement=str(row.get('Arrangement', '')),
                        in_house_date=in_house_date,
                        arrival_date=arrival_date,
                        depart_date=depart_date,
                        check_in_time=str(row.get('C/I Time', '')),
                        check_out_time=str(row.get('C/O Time', '')),
                        created_date=str(row.get('Created', '')),
                        birth_date=str(row.get('Birth Date', '')),
                        age=int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 0,
                        member_no=str(row.get('Member No', '')),
                        member_type=str(row.get('Member Type', '')),
                        email=str(row.get('Email', '')),
                        mobile_phone=str(row.get('Mobile  Phone', '')),  # Note: CSV has double space
                        vip_status=str(row.get('VIP', '')),
                        room_rate=room_rate,
                        lodging=float(row.get('Lodging', 0)) if pd.notna(row.get('Lodging')) else 0,
                        breakfast=float(row.get('Breakfast', 0)) if pd.notna(row.get('Breakfast')) else 0,
                        lunch=float(row.get('Lunch', 0)) if pd.notna(row.get('Lunch')) else 0,
                        dinner=float(row.get('Dinner', 0)) if pd.notna(row.get('Dinner')) else 0,
                        other_charges=float(row.get('Other', 0)) if pd.notna(row.get('Other')) else 0,
                        total_amount=total_amount,
                        bill_number=str(row.get('Bill Number', '')),
                        pay_article=str(row.get('Pay Article', '')),
                        rate_code=str(row.get('Rate Code', '')),
                        res_no=str(row.get('Res No', '')),
                        adult_count=int(row.get('Adult', 0)) if pd.notna(row.get('Adult')) else 0,
                        child_count=int(row.get('Child', 0)) if pd.notna(row.get('Child')) else 0,
                        compliment=str(row.get('Compliment', '')),
                        nationality=str(row.get('Nat', '')),
                        local_region=str(row.get('Local Region', '')),
                        company_ta=str(row.get('Company / TA', '')),
                        sob=str(row.get('SOB', '')),
                        nights=nights,
                        segment=str(row.get('Segment', '')),
                        created_by=str(row.get('By', '')),
                        k_card=str(row.get('K-Card', '')),
                        remarks=str(row.get('remarks', ''))
                    )
                    db.add(reservation_raw)
                    db.commit()  # Commit raw data immediately
                    rows_inserted += 1
                    print(f"Inserted into Raw: {arrival_date} - {depart_date} - Room {room_number}")
                    
                    # Use proper upsert logic for Processed table
                    # Check if record already exists by unique constraint
                    existing_processed = db.query(ReservasiProcessed).filter(
                        ReservasiProcessed.arrival_date == arrival_date,
                        ReservasiProcessed.depart_date == depart_date,
                        ReservasiProcessed.room_number == room_number
                    ).first()
                    
                    if existing_processed:
                        # UPDATE existing record with latest data
                        existing_processed.reservation_id = str(row.get('Res No', ''))
                        existing_processed.guest_id = guest_id
                        existing_processed.guest_name = guest_name
                        existing_processed.room_number = room_number
                        existing_processed.room_type = str(row.get('Room Type', ''))
                        existing_processed.arrangement = str(row.get('Arrangement', ''))
                        existing_processed.in_house_date = str(row.get('In House Date', ''))
                        existing_processed.arrival_date = arrival_date
                        existing_processed.depart_date = depart_date
                        existing_processed.check_in_time = str(row.get('C/I Time', ''))
                        existing_processed.check_out_time = str(row.get('C/O Time', ''))
                        existing_processed.created_date = str(row.get('Created', ''))
                        existing_processed.birth_date = str(row.get('Birth Date', ''))
                        existing_processed.age = int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 0
                        existing_processed.member_no = str(row.get('Member No', ''))
                        existing_processed.member_type = str(row.get('Member Type', ''))
                        existing_processed.email = str(row.get('Email', ''))
                        existing_processed.mobile_phone = str(row.get('Mobile  Phone', ''))
                        existing_processed.vip_status = str(row.get('VIP', ''))
                        existing_processed.room_rate = room_rate
                        existing_processed.lodging = float(row.get('Lodging', 0)) if pd.notna(row.get('Lodging')) else 0
                        existing_processed.breakfast = float(row.get('Breakfast', 0)) if pd.notna(row.get('Breakfast')) else 0
                        existing_processed.lunch = float(row.get('Lunch', 0)) if pd.notna(row.get('Lunch')) else 0
                        existing_processed.dinner = float(row.get('Dinner', 0)) if pd.notna(row.get('Dinner')) else 0
                        existing_processed.other_charges = float(row.get('Other', 0)) if pd.notna(row.get('Other')) else 0
                        existing_processed.total_amount = total_amount
                        existing_processed.bill_number = str(row.get('Bill Number', ''))
                        existing_processed.pay_article = str(row.get('Pay Article', ''))
                        existing_processed.rate_code = str(row.get('Rate Code', ''))
                        existing_processed.res_no = str(row.get('Res No', ''))
                        existing_processed.adult_count = int(row.get('Adult', 0)) if pd.notna(row.get('Adult')) else 0
                        existing_processed.child_count = int(row.get('Child', 0)) if pd.notna(row.get('Child')) else 0
                        existing_processed.compliment = str(row.get('Compliment', ''))
                        existing_processed.nationality = str(row.get('Nat', ''))
                        existing_processed.local_region = str(row.get('Local Region', ''))
                        existing_processed.company_ta = str(row.get('Company / TA', ''))
                        existing_processed.sob = str(row.get('SOB', ''))
                        existing_processed.nights = nights
                        existing_processed.segment = str(row.get('Segment', ''))
                        existing_processed.created_by = str(row.get('By', ''))
                        existing_processed.k_card = str(row.get('K-Card', ''))
                        existing_processed.remarks = str(row.get('remarks', ''))
                        existing_processed.last_upload_id = csv_upload.id
                        existing_processed.last_updated = func.now()
                        
                        rows_updated += 1
                        print(f"Updated Processed: {arrival_date} - {depart_date} - Room {room_number}")
                        db.commit()  # Commit update immediately
                    else:
                        # INSERT new record (first row of exploded data)
                        reservation_processed = ReservasiProcessed(
                            reservation_id=str(row.get('Res No', '')),
                            guest_id=guest_id,
                            guest_name=guest_name,
                            room_number=room_number,
                            room_type=str(row.get('Room Type', '')),
                            arrangement=str(row.get('Arrangement', '')),
                            in_house_date=str(row.get('In House Date', '')),
                            arrival_date=arrival_date,
                            depart_date=depart_date,
                            check_in_time=str(row.get('C/I Time', '')),
                            check_out_time=str(row.get('C/O Time', '')),
                            created_date=str(row.get('Created', '')),
                            birth_date=str(row.get('Birth Date', '')),
                            age=int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 0,
                            member_no=str(row.get('Member No', '')),
                            member_type=str(row.get('Member Type', '')),
                            email=str(row.get('Email', '')),
                            mobile_phone=str(row.get('Mobile  Phone', '')),
                            vip_status=str(row.get('VIP', '')),
                            room_rate=room_rate,
                            lodging=float(row.get('Lodging', 0)) if pd.notna(row.get('Lodging')) else 0,
                            breakfast=float(row.get('Breakfast', 0)) if pd.notna(row.get('Breakfast')) else 0,
                            lunch=float(row.get('Lunch', 0)) if pd.notna(row.get('Lunch')) else 0,
                            dinner=float(row.get('Dinner', 0)) if pd.notna(row.get('Dinner')) else 0,
                            other_charges=float(row.get('Other', 0)) if pd.notna(row.get('Other')) else 0,
                            total_amount=total_amount,
                            bill_number=str(row.get('Bill Number', '')),
                            pay_article=str(row.get('Pay Article', '')),
                            rate_code=str(row.get('Rate Code', '')),
                            res_no=str(row.get('Res No', '')),
                            adult_count=int(row.get('Adult', 0)) if pd.notna(row.get('Adult')) else 0,
                            child_count=int(row.get('Child', 0)) if pd.notna(row.get('Child')) else 0,
                            compliment=str(row.get('Compliment', '')),
                            nationality=str(row.get('Nat', '')),
                            local_region=str(row.get('Local Region', '')),
                            company_ta=str(row.get('Company / TA', '')),
                            sob=str(row.get('SOB', '')),
                            nights=nights,
                            segment=str(row.get('Segment', '')),
                            created_by=str(row.get('By', '')),
                            k_card=str(row.get('K-Card', '')),
                            remarks=str(row.get('remarks', '')),
                            last_upload_id=csv_upload.id
                        )
                        db.add(reservation_processed)
                        db.commit()  # Commit insert immediately
                        rows_inserted += 1
                        print(f"Inserted into Processed: {arrival_date} - {depart_date} - Room {room_number}")
                    
                    rows_processed += 1
                    
                except Exception as row_error:
                    print(f"Error processing row: {row_error}")
                    print(f"Row data: {row.to_dict()}")
                    db.rollback()  # Rollback on error
                    # Continue with next row instead of failing entire upload
                    continue
            
            # Update upload status
            csv_upload.status = "completed"
            csv_upload.rows_processed = rows_processed
            db.commit()  # Commit status update
            
            print(f"Reservation data processing completed:")
            print(f"- Total records processed: {rows_processed}")
            print(f"- Records updated: {rows_updated}")
            print(f"- Records inserted: {rows_inserted}")
            
            return {
                "upload_id": csv_upload.id,
                "rows_processed": rows_processed,
                "rows_updated": rows_updated,
                "rows_inserted": rows_inserted
            }
            
        except Exception as e:
            # Update upload status to failed
            if 'csv_upload' in locals():
                csv_upload.status = "failed"
                csv_upload.error_message = str(e)
                db.commit()
            
            # Log detailed error
            print(f"=== ERROR DETAILS ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
