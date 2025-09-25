import pandas as pd
import numpy as np
import re # [Import] Regex
import phonenumbers
from phonenumbers import geocoder
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import UploadFile, HTTPException
from app.model.models import CSVUpload, ProfileTamu, ProfileTamuProcessed
from io import StringIO


class ProfileTamuHandler:
    """Handler for profile tamu CSV files"""
    
    def __init__(self):
        # Occupation mapping from user's research
        self.occupation_mapping = {
            'KARYAWAN BUMD': [
                'KARYAWAN BUMD', 'karyawan bumd', 'KARYAWAN bumd', 'karyawan BUMD',
                'BUMD', 'bumd', 'SLEMAN'
            ],
            'KARYAWAN BUMN': [
                'KARYAWAN BUMN', 'karyawan bumn', 'KARYAWAN bumn', 'karyawan BUMN',
                'BUMN', 'bumn', 'KARYWN BUMN', 'karywn bumn', 'KARYWN bumn', 'karywn BUMN',
                'KARY BUMN', 'kary bumn', 'KARY bumn', 'kary BUMN'
            ],
            'HONORER': [
                'HONORER', 'honorer', 'Honorer',
                'KARYAWAN HONORER', 'karyawan honorer', 'KARYAWAN honorer', 'karyawan HONORER'
            ],
            'IBU RUMAH TANGGA': [
                'IBU RUMAH TANGGA', 'ibu rumah tangga', 'IBU rumah tangga', 'ibu RUMAH TANGGA',
                'IRT', 'irt', 'IRT ', 'irt ',
                'MENGURUS RUMAH TANGGA', 'mengurus rumah tangga', 'MENGURUS rumah tangga', 'mengurus RUMAH TANGGA',
                'MRT', 'mrt', 'RUMAH TANGGA', 'rumah tangga', 'RUMAH tangga', 'rumah TANGGA'
            ],
            'PEDAGANG': [
                'PEDAGANG', 'pedagang', 'Pedagang',
                'PERDAGANGAN', 'perdagangan', 'Perdagangan'
            ],
            'PEGAWAI NEGERI SIPIL': [
                'PEG NEGERI', 'peg negeri', 'PEG negeri', 'peg NEGERI',
                'PEGAWAI NEGERI', 'pegawai negeri', 'PEGAWAI negeri', 'pegawai NEGERI',
                'PEGAWAI NEGERI SIPIL', 'pegawai negeri sipil', 'PEGAWAI negeri sipil', 'pegawai NEGERI SIPIL',
                'PEGAWAI NEGRI', 'pegawai negri', 'PEGAWAI negri', 'pegawai NEGRI',
                'PEGAWAI NEGRI SIPIL', 'pegawai negri sipil', 'PEGAWAI negri sipil', 'pegawai NEGRI SIPIL',
                'PNS', 'pns'
            ],
            'KARYAWAN SWASTA': [
                'KAR SWASTA', 'kar swasta', 'KAR swasta', 'kar SWASTA',
                'KARYAWAN SWASTA', 'karyawan swasta', 'KARYAWAN swasta', 'karyawan SWASTA',
                'KARY SWASTA', 'kary swasta', 'KARY swasta', 'kary SWASTA',
                'KARYAWAB SWASTA', 'karyawab swasta', 'KARYAWAB swasta', 'karyawab SWASTA',
                'KARYAWAN SWATA', 'karyawan swata', 'KARYAWAN swata', 'karyawan SWATA',
                'KARYWAN SWASTA', 'karywan swasta', 'KARYWAN swasta', 'karywan SWASTA',
                'PEG. SWASTA', 'peg. swasta', 'PEG. swasta', 'peg. SWASTA',
                'PEGAWAI SWASTA', 'pegawai swasta', 'PEGAWAI swasta', 'pegawai SWASTA',
                'KARYAWAN', 'karyawan', 'KARYAWAN', 'karyawan',
                'KARYAWATI', 'karyawati', 'KARYAWATI', 'karyawati',
                'SWASTA', 'swasta', "Swasta"
            ],
            'TIDAK BEKERJA': [
                'BELM BEKERJA', 'belm bekerja', 'BELM bekerja', 'belm BEKERJA',
                'BELUM BEKERJA', 'belum bekerja', 'BELUM bekerja', 'belum BEKERJA',
                'BELUM TIDAK BEKERJA', 'belum tidak bekerja', 'BELUM tidak bekerja', 'belum TIDAK BEKERJA',
                'BELUM/TIDAK BEKERJA', 'belum/tidak bekerja', 'BELUM/tidak bekerja', 'belum/TIDAK BEKERJA',
                'TDK BEKERJA', 'tdk bekerja', 'TDK bekerja', 'tdk BEKERJA', 'Tdk bekerja',
                'TIDAK BEKERJA', 'tidak bekerja', 'TIDAK bekerja', 'tidak BEKERJA'
            ],
            'WIRASWASTA': [
                'WIRASWASTA', 'wiraswasta', 'WIRASWASTA', 'wiraswasta',
                'WIRASWATA', 'wiraswata', 'WIRASWATA', 'wiraswata'
            ],
            'PELAJAR MAHASISWA': [
                'pelajar', 'Pelajar', 'PELAJAR', 'PELAJAR ',
                'mahasiswa', 'Mahasiswa', 'MAHASISWA',
                'siswa', 'Siswa', 'SISWA',
                'pelajar mahasiswa', 'PELAJAR MAHASISWA',
                'MAHASISWI', 'PELAJAR / MAHASISWA',
                'PELAJAR/ MAHASISWA', 'PELAJAR/MAHASISWA',
                'PELAJAR/MAHASIWA', 'PELAJAR/MHS',
                'PELAJAR/NAHASISWA'
            ],
            'DOSEN': [
                'DOSEN', 'dosen', 'Dosen'
            ]
        }
    
    def strip_country_code(self, phone: str):
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
    
    def clean_name(self, name):
        """Clean name using user's proven logic"""
        if pd.isna(name) or name == '':
            return ''
        
        name_str = str(name).strip()
        
        # Remove titles
        titles = ['MR', 'MRS', 'MS', 'MISS', 'DR', 'PROF', 'SIR', 'MADAM', 'BPK']
        name_parts = [part for part in name_str.split() if part.upper().strip(',') not in titles]
        name_str = ' '.join(name_parts)
        
        # Handle comma format (Last, First -> First Last)
        if ',' in name_str:
            parts = [part.strip() for part in name_str.split(',')]
            if len(parts) == 2:
                name_str = f"{parts[1]} {parts[0]}"
        
        return name_str.strip()
    
    def clean_occupation(self, occupation):
        """Standardize occupation using user's mapping"""
        if pd.isna(occupation) or occupation == '':
            return ''
        
        occupation_str = str(occupation).strip()
        
        # Apply exact mapping
        for replacement, patterns in self.occupation_mapping.items():
            if occupation_str.upper() in [p.upper() for p in patterns]:
                return replacement
        
        return occupation_str
    
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
        Process profile tamu CSV file using user's proven preprocessing logic
        Expected columns: Name, Guest No, Phone, Mobile No., Email, Address, Birth Date, Occupation, City, Country
        """
        try:
            # Read CSV content with robust parsing
            content = await file.read()
            
            # Try different CSV parsing strategies with skiprows=6 for profile_tamu
            try:
                # First attempt: standard parsing with skiprows=6
                df = pd.read_csv(StringIO(content.decode('utf-8')), dtype=str, skiprows=6)
                print("Standard parsing with skiprows=6 successful!")

            except Exception as parse_error:
                print(f"Standard parsing with skiprows=6 failed: {parse_error}")
                
                try:
                    # Second attempt: with error handling and skiprows
                    df = pd.read_csv(
                        StringIO(content.decode('utf-8')),
                        dtype=str,
                        skiprows=6,
                        on_bad_lines='skip',  # Skip bad lines
                        quoting=3,              # QUOTE_NONE - disable quotes
                        sep=None,               # Auto-detect separator
                        engine='python'         # Use Python engine for better error handling
                    )
                    print("Second parsing attempt with skiprows=6 successful!")
                except Exception as second_error:
                    print(f"Second parsing attempt with skiprows=6 failed: {second_error}")
                    
                    # Third attempt: manual parsing with pandas and skiprows
                    df = pd.read_csv(
                        StringIO(content.decode('utf-8')),
                        dtype=str,
                        skiprows=6,
                        engine='python',
                        sep=None,
                        quoting=3,
                        on_bad_lines='skip'  # Skip bad lines
                    )
                    print("Third parsing attempt with skiprows=6 successful!")
            
            # Debug: Log actual CSV columns
            print(f"=== CSV COLUMNS DEBUG ===")
            print(f"DataFrame shape: {df.shape}")
            print(f"Actual columns found: {list(df.columns)}")
            print(f"Expected columns: {['Name', 'Guest No', 'Phone', 'Mobile No.', 'Email', 'Address', 'Birth Date', 'Occupation', 'City', 'Country', 'Segment', 'Type ID', 'ID No.', 'Sex', 'Zip', 'L-Region', 'Telefax', 'Comments', 'Credit Lim']}")
            print(f"Missing columns: {[col for col in ['Name', 'Guest No', 'Phone', 'Mobile No.', 'Email', 'Address', 'Birth Date', 'Occupation', 'City', 'Country', 'Segment', 'Type ID', 'ID No.', 'Sex', 'Zip', 'L-Region', 'Telefax', 'Comments', 'Credit Lim'] if col not in df.columns]}")
            print(f"Extra columns: {[col for col in df.columns if col not in ['Name', 'Guest No', 'Phone', 'Mobile No.', 'Email', 'Address', 'Birth Date', 'Occupation', 'City', 'Country', 'Segment', 'Type ID', 'ID No.', 'Sex', 'Zip', 'L-Region', 'Telefax', 'Comments', 'Credit Lim']]}")
            
            # Show first few rows for debugging
            print(f"First 3 rows:")
            print(df.head(3).to_string())
            
            # Validate required columns
            required_columns = ['Name']
            if not all(col in df.columns for col in required_columns):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns. Expected: {required_columns}"
                )
            
            # Create CSV upload record
            csv_upload = CSVUpload(
                filename=file.filename,
                file_type="profile_tamu",
                status="processing"
            )
            db.add(csv_upload)
            db.commit()
            db.refresh(csv_upload)
            
            # Clean data using user's proven logic
            print("=== CLEANING GUEST PROFILE DATA ===")
            
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


            # Clean names
            if 'Name' in df.columns:
                df['Name'] = df['Name'].apply(self.clean_name)
                df = df[df['Name'].notna() & (df['Name'] != '')]
                print(f"Names cleaned: {len(df)} records")

            # [Add] clear decimal from Guest Numbers
            # Clean Guest No by removing .0 if present
            if 'Guest No' in df.columns:
                df['Guest No'] = df['Guest No'].apply(
                lambda x: str(x).replace(".0", "") if pd.notna(x) else x
            )
            
            # Clean phone numbers
            if 'Phone' in df.columns:
                df['Phone'] = df['Phone'].apply(self.clean_phone_number)
            
            if 'Mobile No.' in df.columns:
                df['Mobile No.'] = df['Mobile No.'].apply(self.clean_phone_number)
                # Use Phone as fallback if Mobile No. is empty
                df['Mobile No.'] = df['Mobile No.'].fillna(df['Phone'])
            
            # Clean other fields
            # [Add] clean "Nan" to empty string
            if 'Email' in df.columns:
                df['Email'] = (
                    df['Email']
                    .str.strip()
                    .str.lower()
                    .apply(
                        lambda x: "" 
                        if (
                            x.upper() in ["NAN", "NONE", "NULL", "NA", "N A", "N/A"]  # hanya NA
                            or re.fullmatch(r"[\W_]+", x) is not None   # hanya simbol/non-alfanumerik
                        ) else x
                    )
                )
            
            if 'Birth Date' in df.columns:
                df['Birth Date'] = df['Birth Date'].apply(self.clean_birth_date)
            
            if 'Occupation' in df.columns:
                df['Occupation'] = df['Occupation'].apply(self.clean_occupation)
            
            # [Add] Clear and Normalize city null
            if 'City' in df.columns:
                df['City'] = (
                    df['City']
                    .astype(str)
                    .str.strip()
                    .apply(
                        lambda x: "" 
                        if (
                            x.upper() in ["NAN", "NONE", "NULL", "NA", "N A", "N/A"]  # hanya NA
                            or re.fullmatch(r"[\W_]+", x) is not None   # hanya simbol/non-alfanumerik
                        ) else x
                    )
                )
            
            if 'Country' in df.columns:
                df['Country'] = df['Country'].astype(str).str.strip()
            
            # [Add] Turns COMPL into COMP and normalize style with upper()
            if 'Segment' in df.columns:
                df['Segment'] = (
                    df['Segment']
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .replace({
                        "COMPL": "COMP",
                    })
                )
            
            if 'Type ID' in df.columns:
                df['Type ID'] = df['Type ID'].astype(str).str.strip()
            
            if 'ID No.' in df.columns:
                df['ID No.'] = df['ID No.'].astype(str).str.strip()
            
            # [Add] Address Normalization and clearing
            if "Address" in df.columns:
                df["Address"] = (
                    df["Address"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .apply(
                        lambda x: "" 
                        if (
                            x in ["NAN", "NONE", "NULL", "NA", "N A"]  # hanya NA
                            or re.fullmatch(r"[\W_]+", x) is not None   # hanya simbol/non-alfanumerik
                        ) else x
                    )
                )

            # [Add] Clear Telefax from symbols
            if 'Telefax' in df.columns:
                df['Telefax'] = (
                    df['Telefax']
                    .astype(str)
                    .str.replace(r'\D', '', regex=True)
                    .str.strip()
                )

            # [Add] Clear (M, F, U) to UNIDENTIFIED
            if 'Sex' in df.columns:
                df['Sex'] = (
                    df['Sex']
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .replace(['M', 'F', 'U'], 'UNIDENTIFIED')
                )
            
            if 'Zip' in df.columns:
                df['Zip'] = df['Zip'].astype(str).str.strip()
            
            if 'L-Region' in df.columns:
                df['L-Region'] = df['L-Region'].astype(str).str.strip()
            
            if 'Telefax' in df.columns:
                df['Telefax'] = df['Telefax'].astype(str).str.strip()
            
            if 'Comments' in df.columns:
                df['Comments'] = df['Comments'].astype(str).str.strip()
            
            # [Add] Normalize all credit lim nul to 0
            if 'Credit Lim' in df.columns:
                df['Credit Lim'] = (
                    df['Credit Lim']
                    .fillna('0')
                    .astype(str)
                    .str.strip()
                    .replace(r'^\s*$', '0', regex=True)  # if string is empty/only spaces → "0"
                )

            # Process each row with Raw + Processed logic
            rows_processed = 0
            rows_updated = 0
            rows_inserted = 0
            
            for _, row in df.iterrows():
                try:
                    # Get final phone (mobile as primary, phone as fallback)
                    final_phone = str(row.get('Mobile No.', '')) if pd.notna(row.get('Mobile No.', '')) and row.get('Mobile No.', '') != '' else str(row.get('Phone', ''))
                    
                    # Get guest data
                    name = str(row['Name']).strip()
                    phone = final_phone.strip()
                    email = str(row.get('Email', '')).strip()
                    
                    # Step 1: Check for existing guest BEFORE generating guest_id
                    existing_processed = None
                    existing_guest_id = None
                    
                    # Try to find existing guest by name + phone (most reliable)
                    if name and phone:
                        existing_processed = db.query(ProfileTamuProcessed).filter(
                            ProfileTamuProcessed.name == name,
                            ProfileTamuProcessed.phone == phone
                        ).first()
                    
                    # If not found, try name + email
                    if not existing_processed and name and email:
                        existing_processed = db.query(ProfileTamuProcessed).filter(
                            ProfileTamuProcessed.name == name,
                            ProfileTamuProcessed.email == email
                        ).first()
                    
                    # If not found, try exact name match (least reliable, but better than duplicating)
                    if not existing_processed and name:
                        existing_processed = db.query(ProfileTamuProcessed).filter(
                            ProfileTamuProcessed.name == name
                        ).first()
                    
                    # Step 2: Generate guest_id based on existing or new
                    if existing_processed:
                        # Use existing guest_id to maintain consistency
                        guest_id = existing_processed.guest_id
                        existing_guest_id = guest_id
                    else:
                        # Generate new guest_id only for truly new guests
                        if name and phone:
                            guest_id = f"{name}_{phone.replace('+','')}".replace(' ', '_').replace('-', '_')[:50]
                        elif name and email:
                            guest_id = f"{name}_{email}".replace(' ', '_').replace('@', '_').replace('.', '_')[:50]
                        elif name:
                            guest_id = f"{name}_{rows_processed}".replace(' ', '_')[:50]
                        else:
                            guest_id = f"GUEST_{csv_upload.id}_{rows_processed}"
                    
                    # Step 3: Check if Raw record already exists with this guest_id
                    existing_raw = db.query(ProfileTamu).filter(
                        ProfileTamu.guest_id == guest_id,
                        ProfileTamu.csv_upload_id == csv_upload.id
                    ).first()
                    
                    if not existing_raw:
                        # Only INSERT to Raw if not already exists
                        profile_raw = ProfileTamu(
                            csv_upload_id=csv_upload.id,
                            guest_id=guest_id,
                            name=name,
                            email=email,
                            phone=final_phone,
                            address=str(row.get('Address', '')),
                            birth_date=str(row.get('Birth Date', '')),
                            occupation=str(row.get('Occupation', '')),
                            city=str(row.get('City', '')),
                            country=str(row.get('Country', '')),
                            segment=str(row.get('Segment', '')),
                            type_id=str(row.get('Type ID', '')),
                            id_no=str(row.get('ID No.', '')),
                            sex=str(row.get('Sex', '')),
                            zip_code=str(row.get('Zip', '')),
                            local_region=str(row.get('L-Region', '')),
                            telefax=str(row.get('Telefax', '')),
                            mobile_no=str(row.get('Mobile No.', '')),
                            comments=str(row.get('Comments', '')),
                            credit_limit=str(row.get('Credit Lim', '0'))
                        )
                        db.add(profile_raw)
                        db.commit()  # Commit raw data immediately
                        rows_inserted += 1
                        print(f"Inserted into Raw: {guest_id} - {name}")
                    
                    # Step 4: Handle Processed table
                    if existing_processed:
                        # UPDATE existing Processed record with all fields
                        existing_processed.name = name
                        existing_processed.email = email
                        existing_processed.phone = final_phone
                        existing_processed.address = str(row.get('Address', ''))
                        existing_processed.birth_date = str(row.get('Birth Date', ''))
                        existing_processed.occupation = str(row.get('Occupation', ''))
                        existing_processed.city = str(row.get('City', ''))
                        existing_processed.country = str(row.get('Country', ''))
                        existing_processed.segment = str(row.get('Segment', ''))
                        existing_processed.type_id = str(row.get('Type ID', ''))
                        existing_processed.id_no = str(row.get('ID No.', ''))
                        existing_processed.sex = str(row.get('Sex', ''))
                        existing_processed.zip_code = str(row.get('Zip', ''))
                        existing_processed.local_region = str(row.get('L-Region', ''))
                        existing_processed.telefax = str(row.get('Telefax', ''))
                        existing_processed.mobile_no = str(row.get('Mobile No.', ''))
                        existing_processed.comments = str(row.get('Comments', ''))
                        existing_processed.credit_limit = str(row.get('Credit Lim', '0'))
                        existing_processed.last_upload_id = csv_upload.id
                        existing_processed.last_updated = func.now()
                        
                        rows_updated += 1
                        print(f"Updated Processed (deduplicated): {existing_guest_id} - {name}")
                        db.commit()  # Commit update immediately
                    else:
                        # INSERT new Processed record with all fields
                        profile_processed = ProfileTamuProcessed(
                            guest_id=guest_id,
                            name=name,
                            email=email,
                            phone=final_phone,
                            address=str(row.get('Address', '')),
                            birth_date=str(row.get('Birth Date', '')),
                            occupation=str(row.get('Occupation', '')),
                            city=str(row.get('City', '')),
                            country=str(row.get('Country', '')),
                            segment=str(row.get('Segment', '')),
                            type_id=str(row.get('Type ID', '')),
                            id_no=str(row.get('ID No.', '')),
                            sex=str(row.get('Sex', '')),
                            zip_code=str(row.get('Zip', '')),
                            local_region=str(row.get('L-Region', '')),
                            telefax=str(row.get('Telefax', '')),
                            mobile_no=str(row.get('Mobile No.', '')),
                            comments=str(row.get('Comments', '')),
                            credit_limit=str(row.get('Credit Lim', '0')),
                            last_upload_id=csv_upload.id
                        )
                        db.add(profile_processed)
                        db.commit()  # Commit insert immediately
                        rows_inserted += 1
                        print(f"Inserted into Processed: {guest_id} - {name}")
                    
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
            
            print(f"Data processing completed:")
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

"""
Notes dari etl sebelumnya:

# Cleaning phone number from guest profile
import phonenumbers
from phonenumbers import geocoder

# Strip number country code or 0
def strip_country_code(phone: str):
    if phone.startswith("0"):
        return phone[1:]
    try:
        num = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(num):
            no_code_number = num.national_number
            return no_code_number
        else:
            "Unkown"
    except:
        return phone

df["Phone"] = (
    df["Phone"]
    .astype(str)
    .str.replace(r"\\D", "", regex=True)
    
    .apply(strip_country_code)
)

df["Mobile No."] = (
    df["Mobile No."]
    .astype(str)
    .str.replace(r"\\D", "", regex=True)       # remove non-digits
    .apply(strip_country_code)
)
df['Mobile No.'] = df['Mobile No.'].fillna(df['Phone'])

print("\nTotal rows: ", clean_guest_df.shape[0])
print("\n", clean_guest_df.head())

### Cleaning name from guest profile
def clean_name(self, name):
        if pd.isna(name) or name == '':
            return np.nan
        
        # Remove titles (approach user)
        titles = ['MR', 'MRS', 'MS', 'MISS', 'DR', 'PROF', 'SIR', 'MADAM', 'BPK']
        name_parts = [part for part in str(name).split() if part.upper().strip(',') not in titles]
        name = ' '.join(name_parts)
        
        # Handle comma format (approach user)
        if ',' in name:
            parts = [part.strip() for part in name.split(',')]
            if len(parts) == 2:
                name = f"{parts[1]} {parts[0]}"
        
        return name.strip()


"""
