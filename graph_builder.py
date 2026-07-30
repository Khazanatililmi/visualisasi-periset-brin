"""
graph_builder.py
----------------
Modul untuk membangun NetworkX Graph dari DataFrame.
Setiap baris DataFrame menghasilkan node Kelompok_Riset, Kegiatan_Riset,
dan Periset beserta edge antar ketiganya.
"""

import networkx as nx
import pandas as pd


def bangun_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Membuat dan mengembalikan NetworkX Graph berdasarkan data periset.

    Node:
        - Kelompok_Riset  : kategori='Kelompok_Riset'
        - Kegiatan_Riset  : kategori='Kegiatan_Riset', kelompok=...
        - Periset         : kategori='periset', status=...

    Edge:
        - Kelompok_Riset <-> Kegiatan_Riset  : weight=0
        - Kegiatan_Riset <-> Periset         : weight=3 (ketua) | 1 (anggota)
    """
    G = nx.Graph()

    for _, row in df.iterrows():
        kelompok_riset  = str(row["Kelompok_Riset"])
        kegiatan_riset  = row["Kegiatan_Riset"]
        periset         = row["Periset"]
        status          = row["Status"]
        peran           = row["Peran"]

        # Node Kelompok_Riset
        G.add_node(kelompok_riset, kategori="Kelompok_Riset")

        # Node Kegiatan_Riset
        G.add_node(
            kegiatan_riset,
            kategori="Kegiatan_Riset",
            kelompok=kelompok_riset,
        )

        # Node Periset (status kita ambil dari yang pertama ditemui atau biarkan overwrite karena biasanya status orang itu sama)
        G.add_node(
            periset,
            kategori="periset",
            status=status,
        )

        # Edge Kelompok_Riset -> Kegiatan_Riset
        G.add_edge(kelompok_riset, kegiatan_riset, weight=0)

        # Edge Kegiatan_Riset -> Periset (berbobot berdasarkan peran)
        bobot = 3 if peran.strip().lower() == "ketua" else 1
        G.add_edge(kegiatan_riset, periset, weight=bobot)

    return G
