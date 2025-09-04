Data Dictionary untuk database `dashagent` (PostgreSQL)

Ringkasan singkat
- Lokasi database: PostgreSQL dengan connection string dari environment variable DATABASE_URL
- Tabel utama: `reservasi_processed`, `profile_tamu_processed`, `chat_whatsapp_processed`
- Tujuan: memberi AI agent konteks skema, kolom penting, contoh nilai, dan aturan penghubung antar tabel.

Catatan umum
- Tipe kolom mengikuti PostgreSQL (TEXT, INTEGER, REAL, TIMESTAMP, BOOLEAN).
- Database menggunakan dual-layer architecture: raw CSV tables + processed tables.
- Semua analytics queries menggunakan processed tables sebagai single source of truth.

Tabel: reservasi_processed
- Primary key: `id` (INTEGER)
- Deskripsi: data reservasi yang sudah diproses dan dibersihkan (single source of truth).
- Kolom utama:
	- id (INTEGER, PK) — id internal.
	- reservation_id (TEXT) — kode reservasi dari sistem.
	- guest_id (TEXT) — kode tamu.
	- guest_name (TEXT) — nama tamu seperti tercatat pada reservasi.
	- arrival_date (TIMESTAMP) — tanggal check-in.
	- depart_date (TIMESTAMP) — tanggal check-out.
	- room_number (TEXT)
	- room_type (TEXT)
	- arrangement (TEXT) — jenis reservasi (Without breakfast atau with breakfast).
	- age (INTEGER)
	- local_region (TEXT)
	- room_rate (REAL)
	- lodging, breakfast, lunch, dinner, other_charges (REAL)
	- bill_number (TEXT)
	- pay_article (TEXT)
	- res_no (TEXT)
	- adult_count (INTEGER), child_count (INTEGER)
	- nationality (TEXT)
	- company_ta (TEXT) — nama perusahaan / travel agent.
	- sob (TEXT)
	- nights (INTEGER) — lama menginap.
	- check_in_time (TEXT), check_out_time (TEXT)
	- segment (TEXT) — sumber/segment (mis. OTA, COR, RO dll).
	- created_date (TEXT), created_by (TEXT)
	- remarks (TEXT)
	- mobile_phone (TEXT) — nomor telepon pada reservasi.
	- email (TEXT) — email kontak pada reservasi.
	- compliment (TEXT) — status compliment/house use.
	- last_updated (TIMESTAMP), last_upload_id (INTEGER)



Tabel: profile_tamu_processed
- Primary key: `id` (INTEGER)
- Deskripsi: master data tamu yang sudah diproses dan dibersihkan.
- Kolom utama:
	- id (INTEGER, PK)
	- guest_id (TEXT, UNIQUE)
	- name (TEXT)
	- segment (TEXT)
	- type_id (TEXT) — jenis identitas (KTP, SIM, dll)
	- id_no (TEXT)
	- address, zip_code, city, local_region (TEXT)
	- nationality, country (TEXT)
	- phone (TEXT) — telepon utama
	- telefax (TEXT)
	- sex (TEXT)
	- birth_date (TEXT)
	- email (TEXT)
	- comments (TEXT)
	- mobile_no (TEXT) — nomor ponsel
	- occupation (TEXT)
	- credit_limit (TEXT)
	- last_updated (TIMESTAMP), last_upload_id (INTEGER)

Tabel: chat_whatsapp_processed
- Primary key: `id` (INTEGER)
- Deskripsi: log pesan WhatsApp yang sudah diproses.
- Kolom utama:
	- id (INTEGER, PK)
	- phone_number (TEXT)
	- message_type (TEXT) — 'Received', 'Sent', dll.
	- message_date (TIMESTAMP)
	- message (TEXT) — isi pesan.
	- last_updated (TIMESTAMP), last_upload_id (INTEGER)

Relasi dan kolom kunci rekomendasi
- Cocokkan kontak antara tabel menggunakan:
	- nomor ponsel: `chat_whatsapp_processed.phone_number` ↔ `profile_tamu_processed.mobile_no`
	- guest_id: `reservasi_processed.guest_id` ↔ `profile_tamu_processed.guest_id`
	- nama: `reservasi_processed.guest_name` ↔ `profile_tamu_processed.name` (fallback)
