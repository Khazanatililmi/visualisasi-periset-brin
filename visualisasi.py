"""
visualisasi.py
--------------
Modul untuk mengisi PyVis Network dengan node dan edge
yang sudah dibangun oleh graph_builder.py.

Fungsi utama:
    - nama_pendek()    : Menghasilkan nama pertama (tanpa gelar akademik)
    - tambah_nodes()   : Menambahkan semua node ke PyVis Network
    - tambah_edges()   : Menambahkan semua edge ke PyVis Network
    - buat_network()   : Membuat dan mengkonfigurasi PyVis Network
"""

import os
import networkx as nx
from pyvis.network import Network


# ---------------------------------------------------------------------------
# Helper: Nama pendek periset (tanpa gelar)
# ---------------------------------------------------------------------------

def nama_pendek(nama: str) -> str:
    """Mengembalikan kata pertama yang bukan gelar akademik."""
    kata = nama.replace(",", "").split()

    abaikan = [
        "Dr.", "Dr", "Dra.", "Dra", "Drs", "Drs. ", "Drs ", " Drs. ", " Drs", "dr.",
        "Prof.", "Prof", "Prof.", "Prof. ",
        "Ir.", "Ir", "Ir.", "Ir ", " Ir. ", " Ir.",
        "Eng.", "Eng",
        "Dr.Eng.", "Dr.Eng",
        "S.T.", "S.T", "S.Si.", "S.Si",
        "S.Kom.", "S.Kom",
        "M.T.", "M.T",
        "M.Sc.", "M.Sc",
        "M.Kom.", "M.Kom",
        "M.Eng.", "M.Eng", "M.Eng. ",
        "Ph.D", "Ph.D.",
        "M", "M. ", "M.", "dr.",
        "Dipl. Ing. (FH)", "Dipl. Ing. ", "(", ")", "Dr. Dipl. Ing (FH)",
        "Dr. Eng.", "Dr.dr", "Prof. Dr.", "Drs.", "Dipl.", "Ing", "(FH)",
    ]

    for k in kata:
        if k not in abaikan:
            return k

    return nama


# ---------------------------------------------------------------------------
# Tambah Node
# ---------------------------------------------------------------------------

def tambah_nodes(
    net: Network,
    G: nx.Graph,
    jumlah_kegiatan: dict,
    jumlah_periset: dict,
    bobot_periset: dict,
    bobot_kelompok: dict,
    periset_info: dict,
    centrality_data: dict,
    logo_kelompok: dict = None,
) -> None:
    """Menambahkan semua node dari Graph ke PyVis Network."""

    for node, attr in G.nodes(data=True):
        kategori = attr["kategori"]

        if kategori == "Kelompok_Riset":
            logo = logo_kelompok.get(node) if logo_kelompok else None

            judul_kelompok = f"""
    Kelompok Riset
    {node}

    Jumlah Kegiatan : {jumlah_kegiatan.get(node, 0)}
    Jumlah Periset : {jumlah_periset.get(node, 0)}
    Total Bobot : {bobot_kelompok.get(node, 0)}
    Total Koneksi (Degree): {centrality_data[node]['count']}
    """
            if logo:
                net.add_node(
                    node,
                    group="kelompok",
                    shape="image",
                    image=logo,
                    size=65,
                    label=" ",
                    font={"size": 0},
                    title=judul_kelompok,
                )
            else:
                net.add_node(
                    node,
                    group="kelompok",
                    shape="circularImage",
                    image="",
                    size=70,
                    label="",
                    title=judul_kelompok,
                )

        # ── Kegiatan Riset ──────────────────────────────────────────────────
        elif kategori == "Kegiatan_Riset":
            label_riset = ""
            for kata in node.split():
                if kata.lower() in ["dan", "di", "dalam", "dengan", "pada", "untuk", "ke", "dari", "the", "of"]:
                    continue
                label_riset += kata[0].upper()

            net.add_node(
                node,
                kelompok=attr["kelompok"],
                group="kegiatan",
                label=label_riset,
                color="#03a9f4",
                size=35,
                shape="diamond",
                font={"size": 35, "color": "white", "face": "arial"},
                title=f"""
    Kegiatan Riset
    {node}
    
    Kelompok: {attr["kelompok"]}
    Total Koneksi (Degree): {centrality_data[node]['count']}
    """,
            )

        # ── Periset ─────────────────────────────────────────────────────────
        else:
            status       = attr["status"]
            status_lower = status.lower()

            if "internal prsdi" in status_lower:
                warna = "#cc2e2e"
            elif "eksternal prsdi" in status_lower:
                warna = "#d512f3"
            elif "eksternal brin" in status_lower:
                warna = "#b4e73c"
            else:
                warna = "#346edb"

            ukuran = 12 + (bobot_periset[node] * 2)

            # Tentukan gambar dari periset_info
            foto = periset_info.get(node, {}).get("foto_url")
            if not foto and "eksternal prsdi" in status_lower:
                foto = "https://ejzmpthmgzfaclpbbtsi.supabase.co/storage/v1/object/public/foto-periset/logo.png"

            # Build Tooltip string with detailed activities and roles
            judul = f"""{node}\nStatus : {status}\nTotal Bobot : {bobot_periset[node]}\nTotal Koneksi (Degree): {centrality_data[node]['count']}\n\nKeterlibatan:\n"""
            
            keterlibatan = periset_info.get(node, {}).get("keterlibatan", [])
            for ket in keterlibatan:
                kegiatan_str = ket['kegiatan']
                if len(kegiatan_str) > 50:
                    kegiatan_str = kegiatan_str[:47] + "..."
                judul += f"- [{ket['peran']}] {kegiatan_str} (Kel: {ket['kelompok']})\n"

            if foto:
                net.add_node(
                    node,
                    status=status_lower,
                    group=status_lower,
                    shape="circularImage",
                    image=foto,
                    size=ukuran,
                    borderWidth=max(5, ukuran // 7),
                    borderWidthSelected=max(7, ukuran // 6),
                    color={
                        "border": warna,
                        "background": "#ffffff",
                        "highlight": {"border": warna, "background": "#ffffff"},
                    },
                    label=nama_pendek(node),
                    font={"size": 15},
                    title=judul,
                )
            else:
                net.add_node(
                    node,
                    group=status_lower,
                    color=warna,
                    size=ukuran,
                    label=nama_pendek(node),
                    font={"size": 15},
                    title=judul,
                )


# ---------------------------------------------------------------------------
# Tambah Edge
# ---------------------------------------------------------------------------

def tambah_edges(net: Network, G: nx.Graph) -> None:
    """Menambahkan semua edge dari Graph ke PyVis Network."""

    for source, target, data in G.edges(data=True):
        bobot = data.get("weight", 0)

        if bobot == 0:          # Kelompok_Riset -> Kegiatan_Riset
            warna = "#21B4F3"
            tebal = 3
            label = ""
        elif bobot == 3:        # Ketua
            warna = "#D8BA10"
            tebal = 4
            label = "3"
        else:                   # Anggota
            warna = "#9E9E9EA9"
            tebal = 1
            label = ""

        net.add_edge(
            source,
            target,
            width=tebal,
            color=warna,
            label=label,
            font={"size": 22, "color": "black", "strokeWidth": 2},
        )


# ---------------------------------------------------------------------------
# Buat dan konfigurasi PyVis Network
# ---------------------------------------------------------------------------

def buat_network() -> Network:
    """Membuat PyVis Network dengan konfigurasi physics dan interaksi default."""

    net = Network(
        height="715px",
        width="100%",
        bgcolor="white",
        font_color="black",
        neighborhood_highlight=False,
        cdn_resources="remote",
    )

    net.set_options("""
var options = {
  "physics": {
    "enabled": true,
    "forceAtlas2Based": {
      "gravitationalConstant": -120,
      "centralGravity": 0.01,
      "springLength": 250,
      "springConstant": 0.06,
      "damping": 0.6,
      "avoidOverlap": 1
    },
    "solver": "forceAtlas2Based",
    "stabilization": {
      "enabled": true,
      "iterations": 300
    }
  },

  "layout": {
    "improvedLayout": false
  },

  "interaction": {
    "hover": true,
    "hoverConnectedEdges": true,
    "selectConnectedEdges": true,
    "navigationButtons": true
  },

  "edges": {
    "smooth": false
  }
}
""")

    return net
