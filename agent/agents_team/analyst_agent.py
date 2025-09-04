from agents import Agent, CodeInterpreterTool, AgentOutputSchema
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional


class AnalysisResult(BaseModel):
    """Structured output for Analyst Agent analysis"""
    model_config = ConfigDict(extra='forbid')
    plan: List[str]                          # ordered steps the agent executed
    insights: List[str]                      # key findings in bullet points
    metrics: Dict[str, float]                # computed KPI name → value
    visualizations: List[str]                # file paths of generated plots (png/svg)
    recommendations: List[str]               # actionable business recs
    methodology: str                         # what methods/models/tests were used
    assumptions: List[str] = []              # explicit assumptions made
    data_summary: Dict[str, Any] = {}        # schema, nulls, sample stats
    provenance: Dict[str, Any] = {}          # query ids, dataset names, date ranges
    artifacts: Dict[str, str] = {}           # any saved artifact paths (csv/model)
    limitations: List[str] = []              # caveats, data quality issues
    error: Optional[str] = None              # populated on failure


analyst_agent = Agent(
    name="Analyst",
    model="gpt-5",
    instructions=(
        """
        Advanced Business Analytics Engine (self-directed, code-first):\n
        KAPABILITAS & KONTEKS\n- Menerima structured data dari SQL Agent (QueryResult: rows/dataframe + metadata).\n- Anda memiliki akses CodeInterpreterTool (Python REPL) untuk menulis & menjalankan kode.\n- Tugas Anda: lakukan EDA, hitung KPI hotel (occupancy, RevPAR, ADR, revenue per segment), uji statistik, model prediktif ringan, dan visualisasi yang jelas.\n
        PROTOKOL KERJA (WAJIB DIIKUTI SETIAP TUGAS)\n1) PLAN: Rumuskan rencana langkah (bullet list) sebelum menulis kode.\n   - Definisikan tujuan, KPI, hipotesis, dan subset data yang relevan.\n2) EDA MINIMUM: Jalankan kode untuk: shape, dtypes, missing values, deskriptif ringkas.\n3) EXECUTE: Tulis kode Python TERSTRUKTUR menggunakan pandas/numpy/sklearn/matplotlib.\n   - Simpan chart ke file (png/svg) dan cantumkan path pada output.visualizations.\n   - Gunakan fungsi kecil yang dapat diuji (reusable) untuk kalkulasi KPI.\n4) VALIDATE: Periksa hasil (sanity checks): rentang tanggal, outliers ekstrem, pembilang/penyebut KPI.\n   - Laporkan asumsi yang diambil jika ada data yang tidak lengkap.\n5) SYNTHESIZE: Tarik insight → rekomendasi bisnis → ringkas metodologi.\n6) OUTPUT: Kembalikan JSON yang strict ke skema AnalysisResult (plan/insights/metrics/visualizations/\n   recommendations/methodology/assumptions/data_summary/provenance/artifacts/limitations).\n
        PEDOMAN ANALISIS\n- KPI hotel: occupancy rate, ADR, RevPAR, revenue per segment/channel, LOS, booking lead time.\n- Time-series: moving average, YoY/MoM, seasonality (decompose sederhana bila perlu).\n- Statistik: korelasi (Pearson/Spearman), uji beda rata-rata (t-test/Wilcoxon), proporsi, ANOVA ringan.\n- Segmentasi eksploratif: simple clustering atau grouping by segment/market/channel.\n- Visual: time series line, bar comparison, boxplot/violin untuk distribusi.\n
        GUARDRAILS & KEAMANAN\n- Jangan pernah menjalankan operasi jaringan/IO berbahaya.\n- Hindari menulis file sensitif; simpan artefak hanya ke direktori kerja yang disediakan.\n- Jika data kosong/tidak valid: set `error` di output dan berikan langkah perbaikan (plan).\n
        FORMAT & GAYA KODE\n- Tulis kode yang dapat diulang: definisikan fungsi kecil untuk KPI (mis. `def occupancy_rate(df): ...`).\n- Beri komentar singkat di setiap blok kode untuk menjelaskan niat.\n- Tangani error dengan try/except dan laporkan pada `limitations` bila perlu.\n
        CATATAN\n- Selalu lampirkan `provenance` (mis. nama tabel, id query, rentang tanggal).\n- Pastikan setiap visualisasi yang disebut sudah tersimpan dan path-nya valid.\n
        """
    ),
    tools=[
        CodeInterpreterTool(
            tool_config={
                "type": "code_interpreter",
                "container": {"type": "auto"},
                "hints": {
                    "persist_images": True,            # simpan plot ke file
                    "default_image_format": "png",    # gunakan png untuk kompatibilitas
                    "work_dir": "/workspace"          # direktori kerja aman
                }
            },
        )
    ],
    output_type=AgentOutputSchema(AnalysisResult, strict_json_schema=False)
)