"""
data_loader.py
--------------
Modul untuk memuat data dari Excel dan menghitung statistik dasar:
- jumlah_kegiatan : dict {kelompok -> jumlah kegiatan unik}
- jumlah_periset  : dict {kelompok -> jumlah periset unik}
- bobot_periset   : dict {nama periset -> total bobot}
- bobot_kelompok  : dict {kelompok -> total bobot}
- periset_info    : dict {nama periset -> list of dict {kelompok, kegiatan, peran, status}}
"""

import pandas as pd


import os
from supabase import create_client, Client

SUPABASE_URL = "https://ejzmpthmgzfaclpbbtsi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqem1wdGhtZ3pmYWNscGJidHNpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTA3NzQ2NSwiZXhwIjoyMTAwNjUzNDY1fQ.xO-TN_p4NmAuNQ-qCyIpfeJt-zAXTYVYUKlctVFO5HU"

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL", SUPABASE_URL)
    key = os.environ.get("SUPABASE_KEY", SUPABASE_KEY)
    return create_client(url, key)

def load_data(filepath: str = None) -> pd.DataFrame:
    """Memuat data dari Supabase dan mengubahnya menjadi DataFrame."""
    supabase = get_supabase_client()
    response = supabase.table('keanggotaan_riset').select(
        "peran, periset(nama_lengkap, status, foto_url), kegiatan_riset(judul_kegiatan, singkatan, kelompok_riset(nama_kelompok, logo_url))"
    ).execute()
    
    rows = []
    for r in response.data:
        per = r.get("periset") or {}
        keg = r.get("kegiatan_riset") or {}
        kel = keg.get("kelompok_riset") or {}
        
        rows.append({
            "Kelompok_Riset": kel.get("nama_kelompok", "-"),
            "Kegiatan_Riset": keg.get("judul_kegiatan", "-"),
            "Singkatan_Kegiatan": keg.get("singkatan", ""),
            "Periset": per.get("nama_lengkap", "-"),
            "Peran": r.get("peran", "Anggota"),
            "Status": per.get("status", "-"),
            "Foto_URL": per.get("foto_url", ""),
            "Logo_URL": kel.get("logo_url", "")
        })
        
    return pd.DataFrame(rows)


def hitung_statistik(df: pd.DataFrame) -> dict:
    """
    Menghitung semua statistik yang dibutuhkan dari DataFrame.

    Returns:
        dict dengan key:
            - jumlah_kegiatan
            - jumlah_periset
            - bobot_periset
            - bobot_kelompok
            - periset_info
    """
    jumlah_kegiatan = (
        df.groupby("Kelompok_Riset")["Kegiatan_Riset"]
        .nunique()
        .to_dict()
    )

    jumlah_periset = (
        df.groupby("Kelompok_Riset")["Periset"]
        .nunique()
        .to_dict()
    )

    bobot_periset = {}
    bobot_kelompok = {}
    periset_info = {}
    logo_kelompok = {}

    for _, row in df.iterrows():
        nama = row["Periset"]
        peran = row["Peran"].strip()
        peran_lower = peran.lower()
        kelompok = str(row["Kelompok_Riset"])
        kegiatan = row["Kegiatan_Riset"]
        status = row["Status"]

        # 1. Hitung Bobot Periset
        bobot = 3 if peran_lower == "ketua" else 1
        bobot_periset[nama] = bobot_periset.get(nama, 0) + bobot

        # 2. Hitung Bobot Kelompok
        bobot_kelompok[kelompok] = bobot_kelompok.get(kelompok, 0) + bobot

        # 3. Kumpulkan Info Periset (Semua keterlibatannya)
        if nama not in periset_info:
            periset_info[nama] = {
                "status": status,
                "foto_url": row.get("Foto_URL", ""),
                "keterlibatan": []
            }
        
        # 4. Simpan Logo Kelompok
        if kelompok not in logo_kelompok:
            logo_kelompok[kelompok] = row.get("Logo_URL", "")
        
        periset_info[nama]["keterlibatan"].append({
            "kelompok": kelompok,
            "kegiatan": kegiatan,
            "singkatan": row.get("Singkatan_Kegiatan", ""),
            "peran": peran
        })

    return {
        "jumlah_kegiatan": jumlah_kegiatan,
        "jumlah_periset":  jumlah_periset,
        "bobot_periset":   bobot_periset,
        "bobot_kelompok":  bobot_kelompok,
        "periset_info":    periset_info,
        "logo_kelompok":   logo_kelompok,
    }
