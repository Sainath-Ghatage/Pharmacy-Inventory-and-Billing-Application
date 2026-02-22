# Create a CSV file with the specified columns and some sample data

import pandas as pd

data = [
    ["Paracetamol 500mg", "BATCH001", 50, "2024-01-15", "2026-01-14"],
    ["Amoxicillin 250mg", "BATCH002", 30, "2023-11-10", "2025-11-09"],
    ["Ibuprofen 400mg", "BATCH003", 40, "2024-03-05", "2026-03-04"],
    ["Cetirizine 10mg", "BATCH004", 25, "2024-02-20", "2026-02-19"],
    ["Azithromycin 500mg", "BATCH005", 20, "2023-12-01", "2025-11-30"],
    ["Metformin 500mg", "BATCH006", 60, "2024-04-12", "2026-04-11"],
    ["Pantoprazole 40mg", "BATCH007", 35, "2024-01-28", "2026-01-27"],
    ["Atorvastatin 10mg", "BATCH008", 45, "2023-10-18", "2025-10-17"],
    ["Amlodipine 5mg", "BATCH009", 55, "2024-05-02", "2026-05-01"],
    ["Omeprazole 20mg", "BATCH010", 28, "2024-03-22", "2026-03-21"],
]

df = pd.DataFrame(data, columns=["Medicine Name", "Batch Number", "Qty", "Mfg Date", "Exp Date"])

file_path = "/mnt/data/medicine_inventory.csv"
df.to_csv(file_path, index=False)

file_path
