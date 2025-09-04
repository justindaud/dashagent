from agents import Agent, FileSearchTool
import os


VS_ID = os.getenv("GOVERNANCE_VS_ID")


governance_agent = Agent(
    name="Governance",
    model="gpt-4o-mini",
    instructions=(
        "Kamu sumber pengetahuan. Kamu bisa mengakses buku profile perusahaan,"
        "melihat informasi atau eksplanasi field data, dan informasi antartabel data."
        "Arti kolom dari data_dictionary.md, contoh query dari dataset_manifest.md. "
        "Selalu sertakan sitasi judul dokumen."
    ),
    tools=[FileSearchTool(vector_store_ids=[VS_ID], max_num_results=4)],
)