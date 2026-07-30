"""
main.py
-------
Entry point untuk generate visualisasi jaringan periset BRIN.
Mengeksekusi langkah-langkah:
1. Load data & hitung statistik (data_loader.py)
2. Bangun struktur graph NetworkX (graph_builder.py)
3. Buat PyVis network & tambahkan nodes/edges (visualisasi.py)
4. Rakit HTML akhir dengan layout & JS custom (html_builder.py)
5. Simpan ke file (visualisasi_BRIN.html)
"""

import os
import networkx as nx
from data_loader import load_data, hitung_statistik
from graph_builder import bangun_graph
from visualisasi import tambah_nodes, tambah_edges, buat_network
from html_builder import build_html

def main():
    print("1. Memuat data dari Supabase...")
    df = load_data()

    print("2. Menghitung statistik dan detail keterlibatan...")
    stats = hitung_statistik(df)
    
    print("3. Membangun struktur Graph...")
    G = bangun_graph(df)

    print("3.1 Menghitung Degree Centrality...")
    deg_centrality = nx.degree_centrality(G)
    abs_degree = dict(G.degree())
    centrality_data = {n: {"ratio": deg_centrality[n], "count": abs_degree[n]} for n in G.nodes()}

    print("4. Menginisialisasi PyVis Network...")
    net = buat_network()
    
    print("5. Menambahkan node ke PyVis Network...")
    tambah_nodes(
        net=net,
        G=G,
        jumlah_kegiatan=stats["jumlah_kegiatan"],
        jumlah_periset=stats["jumlah_periset"],
        bobot_periset=stats["bobot_periset"],
        bobot_kelompok=stats["bobot_kelompok"],
        periset_info=stats["periset_info"],
        centrality_data=centrality_data,
        logo_kelompok=stats["logo_kelompok"]
    )

    print("6. Menambahkan edge ke PyVis Network...")
    tambah_edges(net, G)

    print("7. Merakit HTML (Layout + JavaScript)...")
    html_output = build_html(
        net=net, 
        df=df, 
        G=G, 
        jumlah_kegiatan=stats["jumlah_kegiatan"], 
        jumlah_periset=stats["jumlah_periset"],
        bobot_periset=stats["bobot_periset"],
        periset_info=stats["periset_info"],
        centrality_data=centrality_data
    )

    print("8. Menghasilkan output HTML (In-Memory)...")
    return html_output

if __name__ == "__main__":
    main()
