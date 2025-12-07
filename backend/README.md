python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 4400 --workers 2
