import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import UploadFile, HTTPException
from app.model.models import CSVUpload, TransaksiResto, TransaksiRestoProcessed
from io import StringIO
from datetime import datetime


class TransaksiRestoHandler:
    """Handler for transaksi resto CSV files"""
    
    async def process_csv(self, file: UploadFile, db: Session, user_id: str) -> dict:
        """
        Process transaksi resto CSV file
        Expected columns: transaction_id, guest_id, item_name, quantity, price, total_amount, timestamp
        """
        try:
            # Read CSV content
            content = await file.read()
            df = pd.read_csv(StringIO(content.decode('utf-8')))
            
            # Validate required columns
            required_columns = ['transaction_id', 'guest_id', 'item_name', 'quantity', 'price', 'total_amount', 'timestamp']
            if not all(col in df.columns for col in required_columns):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns. Expected: {required_columns}"
                )
            
            # Create CSV upload record
            csv_upload = CSVUpload(
                filename=file.filename,
                file_type="transaksi_resto",
                status="processing"
            )
            db.add(csv_upload)
            db.commit()
            db.refresh(csv_upload)
            
            # Process each row
            rows_processed = 0
            rows_inserted = 0
            rows_updated = 0
            
            for _, row in df.iterrows():
                # Convert timestamp string to datetime
                try:
                    timestamp = pd.to_datetime(row['timestamp'])
                except:
                    raise HTTPException(status_code=400, detail="Invalid timestamp format")
                
                # Convert price and total_amount to cents
                price = int(float(row['price']) * 100) if row['price'] else 0
                total_amount = int(float(row['total_amount']) * 100) if row['total_amount'] else 0
                
                # Always INSERT into Raw table (TransaksiResto)
                transaksi_raw = TransaksiResto(
                    csv_upload_id=csv_upload.id,
                    transaction_id=str(row['transaction_id']),
                    guest_id=str(row['guest_id']),
                    item_name=str(row['item_name']),
                    quantity=int(row['quantity']) if row['quantity'] else 0,
                    price=price,
                    total_amount=total_amount,
                    timestamp=timestamp
                )
                db.add(transaksi_raw)
                rows_inserted += 1
                print(f"Inserted into Raw: {row['transaction_id']} - {row['guest_id']}")
                
                # Check if record already exists in Processed table
                existing_processed = db.query(TransaksiRestoProcessed).filter(
                    TransaksiRestoProcessed.transaction_id == str(row['transaction_id']),
                    TransaksiRestoProcessed.guest_id == str(row['guest_id']),
                    TransaksiRestoProcessed.timestamp == timestamp
                ).first()
                
                if existing_processed:
                    # UPDATE existing Processed record with all fields
                    existing_processed.item_name = str(row['item_name'])
                    existing_processed.quantity = int(row['quantity']) if row['quantity'] else 0
                    existing_processed.price = price
                    existing_processed.total_amount = total_amount
                    existing_processed.last_upload_id = csv_upload.id
                    existing_processed.last_updated = func.now()
                    
                    rows_updated += 1
                    print(f"Updated Processed: {row['transaction_id']} - {row['guest_id']}")
                else:
                    # INSERT new Processed record with all fields
                    transaksi_processed = TransaksiRestoProcessed(
                        transaction_id=str(row['transaction_id']),
                        guest_id=str(row['guest_id']),
                        item_name=str(row['item_name']),
                        quantity=int(row['quantity']) if row['quantity'] else 0,
                        price=price,
                        total_amount=total_amount,
                        timestamp=timestamp,
                        last_upload_id=csv_upload.id
                    )
                    db.add(transaksi_processed)
                    print(f"Inserted into Processed: {row['transaction_id']} - {row['guest_id']}")
                
                rows_processed += 1
            
            # Update upload status
            csv_upload.status = "completed"
            csv_upload.rows_processed = rows_processed
            db.commit()
            
            print(f"Restaurant transaction data processing completed:")
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
            raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
