# DashAgent Analytics Plan

## Overview
Dokumen ini berisi rencana analisis data yang akan diimplementasikan pada dashboard DashAgent. Setiap analisis akan menentukan pendekatan teknis yang paling sesuai (backend vs frontend vs hybrid).

### Date-Picker
Dashboard akan memiliki datepicker untuk menentukan periode cut-off analisis.

### Metrik
Dashboard akan memuat metrik revenue, occupancy rate, dan average room rate

### Dimensi
Dimensi dapat dipilih untuk menganalisis metrik lebih dalam, berupa room type, segment, age, city, nationality

### Compare
Dasboard memiliki semacam compare mode dimana user dapat memilih 2 rentang periode yang berbeda untuk analisis head-to-head metrik-metrik yang sama

### Metric Definitions (final)
- Revenue: sum(room_rate × nights), dengan nights = (depart_date − arrival_date) atau field nights bila tersedia di processed data. Perhitungan selalu mengikuti filter aktif (mis. exclude house_use/compliment, include room_type=Deluxe, dsb.).
- Occupancy Rate: occupied_room_nights ÷ (total_rooms_input_user × days_in_period). Backend mengembalikan occupied_room_nights dan days_in_period; nilai total_rooms ditentukan di frontend per panel.
- Average Room Rate (ARR/ADR): rata-rata sederhana dari room_rate pada data terfilter. Contoh: jika filter room_type=Deluxe, maka ARR dihitung hanya dari rate kamar Deluxe.

### API Contract (draft minimal)
- Endpoint: /analytics/aggregate
- Query params (per panel):
  - start, end (YYYY-MM-DD)
  - group_by: segment | room_type | city | nationality | age_group | none
  - filters: include/exclude (mis. filters[segment__not_in]=house_use,compliment; filters[room_type__in]=Deluxe)
  - top_n (opsional) + include_other=true (untuk pie ringkas)
- Response:
  - period: { start, end, days }
  - totals: { revenue_sum, occupied_room_nights, arr_simple, bookings_count }
  - breakdown: [ { key, revenue_sum, occupied_room_nights, arr_simple, bookings_count } ]

Catatan:
- Occupancy rate dihitung di frontend: occupancy = occupied_room_nights / (user_total_rooms × days).
- arr_simple adalah rata-rata sederhana room_rate (post-filter), bukan weighted ADR.
- Pie chart menggunakan breakdown sesuai group_by. Untuk dua dimensi, gunakan drilldown atau small multiples.

### Compare Mode
- Dua panel berdampingan (A dan B). Masing-masing panel dapat memiliki: periode berbeda, filters berbeda (opsional), dan user_total_rooms berbeda.
- Default: panel B mewarisi filters dari panel A, user dapat override bila diperlukan.

### Compute & Storage Decisions
- Backend (FastAPI + SQL/ORM):
  - Hitung aggregate utama dari `reservasi_processed`:
    - revenue_sum = SUM(room_rate × nights)
    - occupied_room_nights = SUM(nights)
    - arr_simple = AVG(room_rate)
    - bookings_count = COUNT(*)
  - Dukung group_by: `segment`, `room_type`, `local_region` (alias city), `nationality`, `age_group` (dibentuk dari kolom `age`).
  - Dukung filters include/exclude pada kolom: `segment`, `room_type`, `local_region`, `nationality`; serta pengecualian `compliment`, `house_use` via kolom `compliment`/`segment` sesuai data.
  - Kembalikan `days_in_period` (date diff inclusive) untuk perhitungan occupancy di frontend.
- Frontend (Next.js):
  - Menetapkan `user_total_rooms` per panel dan menghitung occupancy_rate = occupied_room_nights / (user_total_rooms × days_in_period).
  - Orkestrasi compare mode (dua panel) dan rendering pie/small multiples.
  - Mengirim parameter filter/group_by/top_n ke backend.
- Database storage:
  - Tahap awal: tanpa tabel agregat. Query on-demand + cache di backend (TTL 1–5 menit).
  - Opsi lanjutan: pre-aggregation harian (mis. `analytics_daily`) berisi date, segment, room_type, local_region, nationality, revenue_sum, room_nights_sum, arr_simple, bookings_count.
  
Penamaan kolom (sinkron dengan `reservasi_processed`):
- Tanggal: `arrival_date` (DateTime), `depart_date` (DateTime)
- Lama inap: `nights`
- Tarif kamar: `room_rate`
- Dimensi kota: gunakan `local_region` (ditampilkan sebagai "city")
- Kewarganegaraan: `nationality`
- Usia: `age` (dibucket menjadi `age_group` di backend saat group_by=age_group)

## Build Plan

### Milestone 1 — MVP (end-to-end)
1) Backend API
- Tambah router `analytics` dengan endpoint `GET /analytics/aggregate`.
- Validasi params: `start,end,group_by,filters,top_n`.
- Base filter periode: record yang overlap dengan window (arrival_date < end && depart_date > start).
- Aggregates:
  - revenue_sum = SUM(room_rate × nights)
  - occupied_room_nights = SUM(nights)
  - arr_simple = AVG(room_rate)
  - bookings_count = COUNT(*)
- Group by dinamis: `segment|room_type|local_region|nationality|age_group`.
- Top N + Other di backend (opsional; boleh FE).
- Response sesuai kontrak di atas. Cache 1–5 menit.

2) Frontend UI
- Panel kontrol global: date-picker, group_by, filter include/exclude (multiselect), input `total_rooms` per panel, toggle Compare.
- Header metrics: Revenue, Occupancy (FE = nights / (total_rooms × days)), ARR.
- Chart: Pie by `group_by` (+ drilldown/small multiples untuk 2D eksplorasi).
- Compare: dua panel berdampingan; panel B mewarisi filter dari A dengan opsi override.

3) Data hygiene
- Pastikan `reservasi_processed.nights` terisi benar saat ETL; `room_rate` tipe numerik.
- Indeks yang disarankan: `(arrival_date, depart_date)`, `segment`, `room_type`, `local_region`, `nationality`, `age`.

### Milestone 2 — Akurasi & UX
- Perbaiki perhitungan nights overlap (pro-rate): gunakan `overlap_nights = max(0, min(depart,end) - max(arrival,start))` (unit hari).
- Saved views (persist filter & layout per user).
- Top N server-side dengan kolom “Other”.
- Tooltips/legenda rinci (numerator/denominator untuk ARR & occupancy).

### Milestone 3 — Performa & Ekstensi
- Pre-aggregation tabel harian `analytics_daily` (date, segment, room_type, local_region, nationality, revenue_sum, room_nights_sum, arr_simple, bookings_count).
- Job terjadwal nightly untuk refresh (opsional incremental per upload).
- Metric tambahan (opsional): repeat guest rate (distinct guest_id dengan count > 1 dalam window/12m).