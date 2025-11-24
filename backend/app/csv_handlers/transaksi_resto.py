# import pandas as pd
# import re
# from sqlalchemy.orm import Session
# from sqlalchemy.sql import func
# from fastapi import UploadFile, HTTPException
# from app.model.csv import CSVUpload, TransaksiResto, TransaksiRestoProcessed
# from io import StringIO
# from datetime import datetime
# from collections import defaultdict, deque

# class TransaksiRestoHandler:
#     """Handler for transaksi resto CSV files"""

#     def remove_titles(self, name):
#         """Remove titles from guest names"""
#         titles = ['MR', 'MRS', 'MS', 'MISS', 'DR', 'PROF', 'SIR', 'MADAM', 'BPK']
#         name_parts = [part for part in name.split() if part.upper().strip(',') not in titles]
#         return ' '.join(name_parts)
    
#     def reformat_name(self, name):
#         """Reformat guest names from 'Last, First' to 'First Last'"""
#         name = str(name)
#         name = self.remove_titles(name)
#         if ',' in name:
#             parts = [part.strip() for part in name.split(',')]
#             if len(parts) == 2:
#                 name = f"{parts[1]} {parts[0]}"
#         return name.strip()
    
#     def formatting_data(self, df):
#         """Format data types for numeric and currency columns"""
#         df = df.copy()
        
#         # Format date column first (dd/mm/yy format from POS)
#         if 'Date' in df.columns:
#             df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
        
#         # Format integer columns
#         int_cols = ['Table Number', 'Bill Number', 'Article Number', 'Posting ID', 'Reservation Number']
#         for col in int_cols:
#             if col in df.columns:
#                 df[col] = df[col].fillna(0).astype(int)

#         # Format currency columns
#         currency_cols = ['Sales', 'Payment']
#         for col in currency_cols:
#             if col in df.columns:
#                 df[col] = df[col].str.replace(',', '').astype(float)
        
#         return df
    
#     def update_bill_numbers(self, df):
#         """Update bill numbers based on table transfer references using BFS"""
#         df = df.copy()
#         df['Prev Bill Number'] = df['Bill Number'].astype(int)

#         # Pattern to find table transfer references
#         pat = re.compile(r'(?:To|From)\s+Table\s+\d+\s*\*(\d+)')

#         # Build adjacency list for bill connections
#         adj = defaultdict(set)
#         for _, row in df.iterrows():
#             src = int(row['Bill Number'])
#             desc = str(row.get('Description', ''))
#             refs = {int(x) for x in pat.findall(desc)}
#             for dst in refs:
#                 adj[src].add(dst)
#                 adj[dst].add(src)

#         # Ensure all bills are nodes, even without references
#         for b in df['Bill Number'].astype(int).unique():
#             _ = adj[b]

#         # Find connected components & maximum per component using BFS
#         visited = set()
#         comp_max = {}
#         for start in adj.keys():
#             if start in visited:
#                 continue
#             q = deque([start])
#             visited.add(start)
#             comp = []
#             mx = start
#             while q:
#                 u = q.popleft()
#                 comp.append(u)
#                 if u > mx:
#                     mx = u
#                 for v in adj[u]:
#                     if v not in visited:
#                         visited.add(v)
#                         q.append(v)
#             for u in comp:
#                 comp_max[u] = mx
        
#         df['Bill Number'] = df['Bill Number'].astype(int).map(lambda b: comp_max.get(b, b))

#         return df    
    
#     def classify_article(self, article_number, outlet='Restaurant & Bar'):
#         """Classify articles into main categories - Food, Beverages, Others only"""
        
#         if outlet == 'Restaurant & Bar':
#             # Restaurant & Bar: 1-1000=Food, 1001-2999=Beverages, 3000+=Others
#             if 1 <= article_number <= 1000:
#                 return 'Food'
#             elif 1001 <= article_number <= 2299:
#                 return 'Beverages'
#             else:
#                 return 'Others'
                
#         elif outlet == 'Room Service':
#             # Room Service: 1-499=Food, 500-2999=Beverages, 3000+=Others
#             if 1 <= article_number <= 499:
#                 return 'Food'
#             elif 500 <= article_number <= 2999:
#                 return 'Beverages'
#             else:
#                 return 'Others'
                
#         elif outlet == 'Banquet':
#             # Banquet: Semua=Others (sesuai permintaan user)
#             return 'Others'
                
#         else:
#             # Default classification for unknown outlets
#             if 1 <= article_number <= 1000:
#                 return 'Food'
#             elif 1001 <= article_number <= 2999:
#                 return 'Beverages'
#             else:
#                 return 'Others'
    
#     def classify_subarticle(self, article_number, outlet='Restaurant & Bar'):
#         """Classify articles into sub-categories based on outlet-specific patterns"""
        
#         if outlet == 'Restaurant & Bar':
#             # Restaurant & Bar detailed classification
#             article_str = str(article_number)
            
#             # Food categories (1-1000)
#             if 1 <= article_number <= 1000:
#                 if 1 <= article_number <= 40:
#                     return 'Breakfast'
#                 elif 41 <= article_number <= 80:
#                     return 'Appetizer'
#                 elif 81 <= article_number <= 120:
#                     return 'Dessert'
#                 elif 121 <= article_number <= 160:
#                     return 'Pasta'
#                 elif 161 <= article_number <= 200:
#                     return 'Extra For Pasta'
#                 elif 201 <= article_number <= 240:
#                     return 'Pizza'
#                 elif 241 <= article_number <= 280:
#                     return 'Easy Bite'
#                 else:  # 281-1000
#                     return 'Main Course'
            
#             # Beverages (1001-2999) - Combined Non-Alcohol + Alcohol
#             elif 1001 <= article_number <= 2999:
#                 if article_str.startswith('100'):  # 1001-1099
#                     return 'Coffee'
#                 elif article_str.startswith('104'):  # 1041-1049
#                     return 'Tea'
#                 elif article_str.startswith('108'):  # 1081-1089
#                     return 'Softdrink'
#                 elif article_str.startswith('112'):  # 1120-1129
#                     return 'Mineral Water'
#                 elif article_str.startswith('114'):  # 1141-1149
#                     return 'Juice'
#                 elif article_str.startswith('118'):  # 1181-1189
#                     return 'Mocktail'
#                 elif article_str.startswith('122'):  # 1221-1229
#                     return 'Mixer'
#                 elif article_str.startswith('200'):  # 2001-2099
#                     return 'Beer'
#                 elif article_str.startswith('204') or article_str.startswith('205') or \
#                      article_str.startswith('206') or article_str.startswith('207') or article_str.startswith('208'):
#                     return 'Cocktail'
#                 elif article_str.startswith('210') or article_str.startswith('211') or \
#                      article_str.startswith('212') or article_str.startswith('213') or \
#                      article_str.startswith('214') or article_str.startswith('215'):
#                     return 'Shoot'
#                 elif article_str.startswith('22'):  # 2201-2299
#                     return 'Bottle'
#                 else:
#                     return 'Beverages'  # Default for unknown beverage
            
#             # Others (3000+)
#             elif article_number >= 2300:
#                 if article_str.startswith('23'):  # 2301-2399
#                     return 'Promo'
#                 elif article_str.startswith('30'):  # 3001-3099
#                     return 'Cigarette'
#                 elif article_str.startswith('31'):  # 3101-3199
#                     return 'Miscellaneous'
#                 elif article_str.startswith('35') and article_number not in [3514, 3515, 3516]:  # 3501-3599 excluding specific items
#                     return 'Merchandise'
#                 elif article_str.startswith('40'):  # 4001-4099
#                     return 'Soju'
#                 elif article_str.startswith('69'):  # 6901-6999
#                     return 'Compliment Cake'
#                 elif article_str.startswith('891'):  # Discount pattern
#                     return 'Discount'
#                 elif article_str.startswith('98'):  # 9801-9899
#                     return 'Compliment'
#                 elif article_str.startswith('990'):  # 9901-9909
#                     return 'Cash'
#                 elif article_str.startswith('991'):  # 9911-9919
#                     return 'Voucher'
#                 elif article_str.startswith('993'):  # 9931-9939
#                     return 'Credit Card'
#                 elif article_str.startswith('995'):  # 9951-9959
#                     return 'City Ledger'
#                 else:
#                     return 'Others'  # Default for unknown others
                
#         elif outlet == 'Room Service':
#             # Room Service detailed classification based on actual data
#             # Food (1-499)
#             if 1 <= article_number <= 10:
#                 return 'Dessert'
#             elif 40 <= article_number <= 49:
#                 return 'Pasta'
#             elif 121 <= article_number <= 129:
#                 return 'Pizza'
#             elif 160 <= article_number <= 199:
#                 return 'Snack'
#             elif 200 <= article_number <= 499:
#                 return 'Main Course'
            
#             # Beverages (500-2999)
#             elif 500 <= article_number <= 599:
#                 return 'Beer'
#             elif 600 <= article_number <= 699:
#                 return 'Cocktail'
#             elif 700 <= article_number <= 799:
#                 return 'Canned'
#             elif 800 <= article_number <= 899:
#                 return 'Water'
#             elif 900 <= article_number <= 999:
#                 return 'Coffee'
#             elif 1000 <= article_number <= 1099:
#                 return 'Mocktail'
#             elif 1100 <= article_number <= 1199:
#                 return 'Tea'
#             elif 1200 <= article_number <= 1299:
#                 return 'Juice'
#             elif 2000 <= article_number <= 2999:
#                 return 'Bottle'
            
#             # Others (3000+)
#             elif 3000 <= article_number <= 3099:
#                 return 'Promo'
#             else:
#                 return 'Others'
                
#         elif outlet == 'Banquet':
#             if article_number == 3:
#                 return 'Room Rental'
#             elif article_number == 4:
#                 return 'Coffee Break'
#             elif article_number == 5:
#                 return 'Lunch'
#             elif article_number == 6:
#                 return 'Dinner'
#             else:
#                 return 'Other'
        
#         else:
#             return 'Unknown'
            
#     def process_outlet_data(self, df, outlet_name):
#         """Process data for a specific outlet following trial.ipynb pipeline"""
#         if df.empty:
#             return df
            
#         print(f"🔧 Processing {outlet_name} outlet...")
        
#         # Step 1: Name reformatting
#         if 'Guest Name' in df.columns:
#             df['Guest Name'] = df['Guest Name'].apply(self.reformat_name)

#         # Step 2: Data formatting
#         df = self.formatting_data(df)

#         # Step 3: Bill number consolidation (per outlet)
#         df = self.update_bill_numbers(df)

#         # Step 4: Group by Bill Number and Article Number
#         grouped_df = df.groupby(['Bill Number', 'Article Number'], as_index=False).agg({
#             'Description': 'first',
#             'Date': 'last',
#             'Table Number': 'last',
#             'Quantity': 'sum',
#             'Sales': 'sum',
#             'Payment': 'sum',
#             'Outlet': 'first',
#             'Posting ID': 'first',
#             'Start Time': 'first',
#             'Close Time': 'last',
#             'Time': 'max',
#             'Guest Name': 'first',
#             'Travel Agent / Reserve Name': 'first',
#             'Reservation Number': 'first',
#             'Prev Bill Number': 'first',
#         })

#         # Step 5: Handle discounts and compliments
#         disc = grouped_df[grouped_df['Article Number'].astype(str).str.startswith('891')]
#         comp = grouped_df[(grouped_df['Article Number'] > 9800) & (grouped_df['Article Number'] < 9900)]

#         disc_per_bill = disc.groupby('Bill Number')['Sales'].sum()
#         comp_per_bill = comp.groupby('Bill Number')['Payment'].sum()
#         grouped_df['Bill Discount'] = grouped_df['Bill Number'].map(disc_per_bill).fillna(0)
#         grouped_df['Bill Compliment'] = grouped_df['Bill Number'].map(comp_per_bill).fillna(0)
#         grouped_df['Total Deduction'] = grouped_df['Bill Discount'] + grouped_df['Bill Compliment']

#         # Remove discount and compliment rows
#         if not disc.empty:
#             grouped_df = grouped_df.drop(disc.index)
#         if not comp.empty:
#             grouped_df = grouped_df.drop(comp.index)

#         # Drop rows where quantity & sales & payment are 0 simultaneously
#         drop_indices = grouped_df[(grouped_df['Quantity'] == 0) & (grouped_df['Sales'] == 0) & (grouped_df['Payment'] == 0)].index
#         if not drop_indices.empty:
#             grouped_df = grouped_df.drop(drop_indices)

#         # Step 6: Article classification (outlet-specific)
#         grouped_df['Article Number'] = grouped_df['Article Number'].replace('', 0).astype(int)
        
#         # Get outlet name for this batch
#         outlet_name = grouped_df['Outlet'].iloc[0] if not grouped_df.empty else 'Restaurant & Bar'
        
#         # Apply outlet-specific classification
#         grouped_df['Article'] = grouped_df['Article Number'].apply(lambda x: self.classify_article(x, outlet_name))
#         grouped_df['Subarticle'] = grouped_df['Article Number'].apply(lambda x: self.classify_subarticle(x, outlet_name))

#         # Reorder columns
#         cols = grouped_df.columns.tolist()
#         if 'Article' in cols and 'Article Number' in cols:
#             cols.insert(cols.index('Article Number') + 1, cols.pop(cols.index('Article')))
#         if 'Subarticle' in cols and 'Article' in cols:
#             cols.insert(cols.index('Article') + 1, cols.pop(cols.index('Subarticle')))
#         grouped_df = grouped_df[cols]
        
#         print(f"   - {outlet_name} processed: {grouped_df.shape[0]} records")
#         return grouped_df

#     async def process_csv(self, file: UploadFile, db: Session) -> dict:
#         """
#         Process restaurant transaction CSV following trial.ipynb simplified pipeline
#         Expected columns from POS system: Date, Bill Number, Article Number, Description, 
#         Sales, Payment, Quantity, Guest Name, Table Number, Outlet, etc.
#         """
#         try:
#             # Read CSV content
#             content = await file.read()
#             df = pd.read_csv(StringIO(content.decode('utf-8')), skiprows=2)

#             if 'Outlet' in df.columns:
#                 resto = df[df['Outlet'] == 'Restaurant & Bar']
#                 roomservice = df[df['Outlet'] == 'Room Service'] 
#                 banquet = df[df['Outlet'] == 'Banquet']
                
#                 print(f"📊 Data split by outlet:")
#                 print(f"   - Restaurant & Bar: {resto.shape[0]} records")
#                 print(f"   - Room Service: {roomservice.shape[0]} records") 
#                 print(f"   - Banquet: {banquet.shape[0]} records")
#             else:
#                 # Fallback if no Outlet column
#                 resto = df[df['Date'].notna()]
#                 roomservice = pd.DataFrame()
#                 banquet = pd.DataFrame()
            
#             # Validate required columns
#             required_columns = ['Date', 'Table Number', 'Bill Number', 'Article Number', 'Description', 'Quantity', 'Sales', 'Payment', 'Outlet', 'Posting ID', 'Start Time', 'Close Time', 'Time', 'Guest Name', 'Travel Agent / Reserve Name', 'Reservation Number']
#             missing_columns = [col for col in required_columns if col not in df.columns]
#             if missing_columns:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Missing required columns. Expected: {missing_columns}"
#                 )
            
#             # Create CSV upload record
#             csv_upload = CSVUpload(
#                 filename=file.filename,
#                 file_type="transaksi_resto",
#                 status="processing"
#             )
#             db.add(csv_upload)
#             db.commit()
#             db.refresh(csv_upload)

#             print(f"📂 Starting ETL processing for {file.filename}")
#             print(f"📊 Initial data shape: {df.shape}")

#             processed_dfs = []
            
#             # Process each outlet separately to handle Bill Number uniqueness per outlet
#             if not resto.empty:
#                 resto_processed = self.process_outlet_data(resto, "Restaurant & Bar")
#                 if not resto_processed.empty:
#                     processed_dfs.append(resto_processed)
                    
#             if not roomservice.empty:
#                 roomservice_processed = self.process_outlet_data(roomservice, "Room Service")
#                 if not roomservice_processed.empty:
#                     processed_dfs.append(roomservice_processed)
                    
#             if not banquet.empty:
#                 banquet_processed = self.process_outlet_data(banquet, "Banquet")
#                 if not banquet_processed.empty:
#                     processed_dfs.append(banquet_processed)
            
#             # Combine all processed outlet data
#             if processed_dfs:
#                 grouped_df = pd.concat(processed_dfs, ignore_index=True)
#                 print(f"📊 Combined processed data shape: {grouped_df.shape}")
#             else:
#                 grouped_df = pd.DataFrame()
#                 print("⚠️ No data to process after outlet separation")

#             # Step 7: Database Storage
#             print("🔧 Step 7: Storing processed data...")
            
#             # Process each row
#             rows_processed = 0
#             rows_inserted = 0
#             rows_updated = 0

#             if not grouped_df.empty:
#                 for _, row in grouped_df.iterrows():
#                     # Convert to database format
#                     bill_number = str(row['Bill Number'])
#                     article_number = str(row['Article Number'])
#                     description = str(row['Description'])
#                     quantity = int(row['Quantity']) if row['Quantity'] else 0
                    
#                     # Convert to cents for currency fields
#                     sales = int(float(row['Sales']) * 100) if row['Sales'] else 0
                    
#                     # Date sudah di-parse di formatting_data(), tinggal ambil nilai
#                     timestamp = row.get('Date', datetime.now())

#                     # CHECK if Raw record already exists to prevent duplicate constraint violation
#                     existing_raw = db.query(TransaksiResto).filter(
#                         TransaksiResto.bill_number == bill_number,
#                         TransaksiResto.article_number == article_number,
#                         TransaksiResto.guest_name == str(row.get('Guest Name', '')),
#                         TransaksiResto.transaction_date == timestamp.date() if timestamp else None
#                     ).first()

#                     if existing_raw:
#                         # UPDATE existing raw record with latest data
#                         existing_raw.item_name = description
#                         existing_raw.quantity = quantity
#                         existing_raw.sales = sales
#                         existing_raw.payment = sales
#                         existing_raw.outlet = str(row.get('Outlet', ''))
#                         existing_raw.table_number = int(row.get('Table Number', 0))
#                         existing_raw.posting_id = str(row.get('Posting ID', ''))
#                         existing_raw.reservation_number = str(row.get('Reservation Number', ''))
#                         existing_raw.travel_agent_name = str(row.get('Travel Agent / Reserve Name', ''))
#                         existing_raw.transaction_date = timestamp
#                         existing_raw.start_time = str(row.get('Start Time', ''))
#                         existing_raw.close_time = str(row.get('Close Time', ''))
#                         existing_raw.time = str(row.get('Time', ''))
#                         existing_raw.timestamp = timestamp
#                         existing_raw.csv_upload_id = csv_upload.id  # Update to latest upload
#                     else:
#                         # Only INSERT into Raw table if record doesn't exist
#                         transaksi_raw = TransaksiResto(
#                             csv_upload_id=csv_upload.id,
#                             bill_number=bill_number,
#                             article_number=article_number,
#                             guest_name=str(row.get('Guest Name', '')),
#                             item_name=description,
#                             quantity=quantity,
#                             sales=sales,
#                             payment=sales,  # Using sales as payment for now
#                             outlet=str(row.get('Outlet', '')),
#                             table_number=int(row.get('Table Number', 0)),
#                             posting_id=str(row.get('Posting ID', '')),
#                             reservation_number=str(row.get('Reservation Number', '')),
#                             travel_agent_name=str(row.get('Travel Agent / Reserve Name', '')),
#                             transaction_date=timestamp,
#                             start_time=str(row.get('Start Time', '')),
#                             close_time=str(row.get('Close Time', '')),
#                             time=str(row.get('Time', '')),
#                             timestamp=timestamp
#                         )
#                         db.add(transaksi_raw)
#                         rows_inserted += 1

#                     # Check if record exists in Processed table
#                     existing_processed = db.query(TransaksiRestoProcessed).filter(
#                         TransaksiRestoProcessed.bill_number == bill_number,
#                         TransaksiRestoProcessed.article_number == article_number,
#                         TransaksiRestoProcessed.guest_name == str(row.get('Guest Name', '')),
#                         TransaksiRestoProcessed.transaction_date == timestamp.date() if timestamp else None
#                     ).first()

#                     if existing_processed:
#                         # UPDATE existing record with all fields
#                         existing_processed.item_name = description
#                         existing_processed.quantity = quantity
#                         existing_processed.sales = sales
#                         existing_processed.payment = sales  # Using sales as payment for now
#                         existing_processed.outlet = str(row.get('Outlet', ''))
#                         existing_processed.article_category = str(row.get('Article', ''))
#                         existing_processed.article_subcategory = str(row.get('Subarticle', ''))
#                         existing_processed.table_number = int(row.get('Table Number', 0))
#                         existing_processed.posting_id = str(row.get('Posting ID', ''))
#                         existing_processed.reservation_number = str(row.get('Reservation Number', ''))
#                         existing_processed.travel_agent_name = str(row.get('Travel Agent / Reserve Name', ''))
#                         existing_processed.prev_bill_number = str(row.get('Prev Bill Number', ''))
#                         existing_processed.transaction_date = timestamp
#                         existing_processed.start_time = str(row.get('Start Time', ''))
#                         existing_processed.close_time = str(row.get('Close Time', ''))
#                         existing_processed.time = str(row.get('Time', ''))
#                         existing_processed.bill_discount = float(row.get('Bill Discount', 0))
#                         existing_processed.bill_compliment = float(row.get('Bill Compliment', 0))
#                         existing_processed.total_deduction = float(row.get('Total Deduction', 0))
#                         existing_processed.last_upload_id = csv_upload.id
#                         existing_processed.last_updated = func.now()
#                         rows_updated += 1
#                     else:
#                         # INSERT new record with all classification and detail data (following pattern from other 3 ETLs)
#                         transaksi_processed = TransaksiRestoProcessed(
#                             bill_number=bill_number,
#                             article_number=article_number,
#                             guest_name=str(row.get('Guest Name', '')),
#                             item_name=description,
#                             quantity=quantity,
#                             sales=sales,
#                             payment=sales,  # Using sales as payment for now
#                             outlet=str(row.get('Outlet', '')),
#                             article_category=str(row.get('Article', '')),
#                             article_subcategory=str(row.get('Subarticle', '')),
#                             table_number=int(row.get('Table Number', 0)),
#                             posting_id=str(row.get('Posting ID', '')),
#                             reservation_number=str(row.get('Reservation Number', '')),
#                             travel_agent_name=str(row.get('Travel Agent / Reserve Name', '')),
#                             prev_bill_number=str(row.get('Prev Bill Number', '')),
#                             transaction_date=timestamp,
#                             start_time=str(row.get('Start Time', '')),
#                             close_time=str(row.get('Close Time', '')),
#                             time=str(row.get('Time', '')),
#                             timestamp=timestamp,  # Keep for compatibility
#                             bill_discount=float(row.get('Bill Discount', 0)),
#                             bill_compliment=float(row.get('Bill Compliment', 0)),
#                             total_deduction=float(row.get('Total Deduction', 0)),
#                             last_upload_id=csv_upload.id
#                         )
#                         db.add(transaksi_processed)

#                     rows_processed += 1
#             else:
#                 print("⚠️ No data to store after processing")

#             # Update upload status
#             csv_upload.status = "completed"
#             csv_upload.rows_processed = rows_processed
#             db.commit()

#             print(f"✅ ETL processing completed:")
#             print(f"   - Total records processed: {rows_processed}")
#             print(f"   - Records inserted (raw): {rows_inserted}")
#             print(f"   - Records updated (processed): {rows_updated}")

#             return {
#                 "upload_id": csv_upload.id,
#                 "rows_processed": rows_processed,
#                 "rows_inserted": rows_inserted,
#                 "rows_updated": rows_updated,
#                 "final_data_shape": grouped_df.shape,
#                 "outlets_processed": len(processed_dfs),
#                 "processing_approach": "multi_outlet_with_bill_consolidation"
#             }

#         except Exception as e:
#             # Update upload status to failed
#             if 'csv_upload' in locals():
#                 csv_upload.status = "failed"
#                 csv_upload.error_message = str(e)
#                 db.commit()
#             raise HTTPException(status_code=500, detail=f"ETL Error: {str(e)}")