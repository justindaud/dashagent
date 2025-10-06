import pandas as pd
import re
import phonenumbers
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import UploadFile, HTTPException
from app.model.models import CSVUpload, ChatWhatsapp, ChatWhatsappProcessed
from io import StringIO
from datetime import datetime


class ChatWhatsappHandler:
    """Handler for chat WhatsApp CSV files"""
    
    def __init__(self):
        pass
    
    def is_phone(self, number: str) -> bool:
        """Check if string is a valid phone number"""
        if not isinstance(number, str):
            return False
        return re.match(r"^\+?\d+$", number) is not None
    
    def strip_country_code(self, phone: str):
        if phone == 0:
            return ''

        if phone.startswith("0"):
            return phone[1:]
        try:
            num = phonenumbers.parse(phone, None)
            if phonenumbers.is_valid_number(num):
                return str(phone)
            else:
                return ''
        except:
            return ''
    
    async def process_csv(self, file: UploadFile, db: Session, user_id: str) -> dict:
        """
        Process WhatsApp chat CSV file based on actual CSV structure
        Expected columns: Chats,Type,Date,Name,Content
        """
        try:
            # Read CSV content
            content = await file.read()
            df = pd.read_csv(StringIO(content.decode('utf-8')))
            
            # Validate required columns
            required_columns = ['Chats', 'Content']
            if not all(col in df.columns for col in required_columns):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns. Expected: {required_columns}"
                )
            
            # Create CSV upload record with explicit transaction
            try:
                csv_upload = CSVUpload(
                    filename=file.filename,
                    file_type="chat_whatsapp",
                    status="processing",
                    uploaded_by=user_id
                )
                db.add(csv_upload)
                db.commit()
                db.refresh(csv_upload)
            except Exception as upload_error:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error creating upload record: {str(upload_error)}")

            # Clean and process data based on user's research notes
            print("=== CLEANING WHATSAPP CHAT DATA ===")
            
            df = df.dropna(subset=['Type'])
            df = df.replace("\t", "", regex=True)
            df = df.drop_duplicates()

            # Define groups you want to exclude
            groups_to_exclude = ["Team Pulang", "PULANG - BM"]

            # Filter out rows where Chats is one of the excluded groups
            group_chat_window = df[df['Chats'].isin(groups_to_exclude)]

            # Find 'Name' inside the group chat window
            group_chat_window_names = group_chat_window['Name'].unique(),group_chat_window['Name'].count()

            # filter df Chat with group_chat_window to get guest_chat_window
            df = df[~df['Chats'].isin(group_chat_window_names[0])]


            # Filter out group chats and staff (approach user yang terbukti)
            if 'Chats' in df.columns:
                # Remove rows where Chats is not a valid phone number
                df = df[df['Chats'].apply(self.is_phone)]
                print(f"Valid phone numbers after filtering: {len(df)} records")
            
            # Clean phone numbers using user's proven logic
            if 'Chats' in df.columns:
                # [Remove] make sure number can be processed
                df['Chats'] = df['Chats'].apply(self.strip_country_code)
                df = df.dropna(subset=['Chats'])
                df = df[df['Chats'] != '']
                print(f"Phone numbers cleaned: {len(df)} records")
            
            # Clean messages
            if 'Content' in df.columns:
                df['Content'] = df['Content'].fillna('').astype(str).str.strip()
                df = df[df['Content'] != '']
                print(f"Valid messages: {len(df)} records")
            
            # Parse dates
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%Y %H.%M.%S', errors='coerce')
                df = df[df['Date'].notna()]
                print(f"Valid dates: {len(df)} records")

            df.drop_duplicates(subset=['Chats', 'Date', 'Content'], inplace=True)
            
            # Process and insert data with Raw + Processed logic
            rows_processed = 0
            rows_updated = 0
            rows_inserted = 0
            
            for index, row in df.iterrows():
                phone_number = str(row['Chats'])
                message_date = row['Date']
                message_content = str(row.get('Content', ''))

                existing_raw = db.query(ChatWhatsapp).filter(
                    ChatWhatsapp.phone_number == phone_number,
                    ChatWhatsapp.message_date == message_date,
                    ChatWhatsapp.message == message_content
                ).first()

                if existing_raw:
                    continue  # Skip duplicates in Raw table
                else:
                    chat_raw = ChatWhatsapp(
                        csv_upload_id=csv_upload.id,
                        phone_number=phone_number,
                        message_type=str(row['Type']),
                        message_date=message_date,
                        message=message_content,
                    )
                    db.add(chat_raw)
                    rows_inserted += 1
                    print(f"Inserted into Raw: {phone_number} - {message_date} - {message_content[:50]}...")
                
                # Check if record already exists in Processed table
                existing_processed = db.query(ChatWhatsappProcessed).filter(
                    ChatWhatsappProcessed.phone_number == phone_number,
                    ChatWhatsappProcessed.message_date == message_date,
                    ChatWhatsappProcessed.message == message_content
                ).first()
                
                if existing_processed:
                    # UPDATE existing Processed record
                    existing_processed.message_type = str(row['Type'])
                    existing_processed.last_upload_id = csv_upload.id
                    
                    rows_updated += 1
                    print(f"Updated Processed: {phone_number} - {message_date} - {message_content[:50]}...")
                else:
                    # INSERT new Processed record
                    chat_processed = ChatWhatsappProcessed(
                        phone_number=phone_number,
                        message_type=str(row['Type']),
                        message_date=message_date,
                        message=message_content,
                        last_upload_id=csv_upload.id
                    )
                    db.add(chat_processed)
                    print(f"Inserted into Processed: {phone_number} - {message_date} - {message_content[:50]}...")
                
                rows_processed += 1
            
            # Update upload status
            csv_upload.status = "completed"
            csv_upload.rows_processed = rows_processed
            db.commit()
            
            print(f"WhatsApp chat data processing completed:")
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
            db.rollback()
            if 'csv_upload' in locals():
                try:
                    csv_upload.status = "failed"
                    csv_upload.error_message = str(e)
                    db.commit()
                except:
                    db.rollback()
            print(e) # Debug log
            raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")