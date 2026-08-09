"""
html_builder.py
---------------
Modul ini bertugas menggabungkan hasil HTML dari PyVis dengan
layout kustom (Header, Statistik, Filter, Info Panel) dan logika
JavaScript untuk merender Dashboard Periset yang interaktif.
"""

import json

def clean_str(s):
    """Bersihkan newline dan karakter berbahaya dari string agar aman di JS."""
    if not isinstance(s, str):
        s = str(s)
    return s.replace("\n", " ").replace("\r", " ").replace("`", "'").strip()

def build_html(net, df, G, jumlah_kegiatan, jumlah_periset, bobot_periset, periset_info, centrality_data):
    """
    Menghasilkan HTML akhir berupa string.
    Menggunakan data Graph dan periset_info untuk membangun data filter JSON.
    """
    html = net.generate_html()

    # Siapkan data untuk JS
    data_filter = []
    for node, attr in G.nodes(data=True):
        kategori = attr.get("kategori", "")
        
        node_data = {
            "id": clean_str(node),
            "kategori": kategori,
            "centrality": centrality_data[node]["count"]
        }
        
        if kategori == "Kelompok_Riset":
            node_data["jml_kegiatan"] = jumlah_kegiatan.get(node, 0)
            node_data["jml_periset"] = jumlah_periset.get(node, 0)
        elif kategori == "Kegiatan_Riset":
            node_data["kelompok"] = clean_str(attr.get("kelompok", ""))
        elif kategori == "periset":
            node_data["status"] = clean_str(attr.get("status", ""))
            node_data["bobot"] = bobot_periset.get(node, 0)
            # Tambahkan keterlibatan penuh
            keterlibatan = periset_info.get(node, {}).get("keterlibatan", [])
            node_data["keterlibatan"] = keterlibatan
            
        data_filter.append(node_data)

    from collections import defaultdict
    filter_hierarki = defaultdict(lambda: defaultdict(list))

    for _, row in df.iterrows():
        kelompok = clean_str(row["Kelompok_Riset"])
        kegiatan = clean_str(row["Kegiatan_Riset"])
        periset  = clean_str(row["Periset"])

        if kegiatan not in filter_hierarki[kelompok]:
            filter_hierarki[kelompok][kegiatan] = []
        if periset not in filter_hierarki[kelompok][kegiatan]:
            filter_hierarki[kelompok][kegiatan].append(periset)

    json_filter   = json.dumps(data_filter, ensure_ascii=False)
    json_hierarki = json.dumps({k: dict(v) for k, v in filter_hierarki.items()}, ensure_ascii=False)

    # ---------------------------------------------------------
    # Injeksi CSS & External JS (Choices.js)
    # ---------------------------------------------------------
    html = html.replace(
        "</head>",
        """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/choices.js/public/assets/styles/choices.min.css">
<script src="https://cdn.jsdelivr.net/npm/choices.js/public/assets/scripts/choices.min.js"></script>
</head>
"""
    )

    header = """
<div style="width:100%;background:#0B4F6C;padding:25px;text-align:center;color:white;font-family:Segoe UI;box-shadow:0px 3px 8px rgba(0,0,0,.2);position:relative;">
    <h1 style="margin:0;font-size:36px;">DASHBOARD PERISET</h1>
    <p style="margin-top:8px;font-size:18px;">PR Sains Data dan Informasi</p>
    <p style="margin-top:3px;font-size:15px;">Badan Riset dan Inovasi Nasional</p>
    <a href="/admin" style="
        position:absolute;
        right:24px;
        top:50%;
        transform:translateY(-50%);
        background:white;
        color:#0B4F6C;
        border:none;
        padding:10px 20px;
        border-radius:8px;
        font-size:14px;
        font-weight:600;
        font-family:Segoe UI;
        text-decoration:none;
        display:inline-flex;
        align-items:center;
        gap:7px;
        box-shadow:0 2px 8px rgba(0,0,0,0.15);
        transition:all 0.2s ease;
    " onmouseover="this.style.background='#f0f4f8';this.style.boxShadow='0 4px 14px rgba(0,0,0,0.2)'"
       onmouseout="this.style.background='white';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.15)'">
        &#9881; Admin
    </a>
</div>
"""

    statistik = f"""
<style>
.stat-card{{background:white;width:220px;padding:20px;border-radius:15px;box-shadow:0 3px 12px rgba(0,0,0,.15);text-align:center;font-family:Segoe UI;transition:transform .2s,box-shadow .2s;}}
.stat-card:hover{{transform:translateY(-4px);box-shadow:0 6px 20px rgba(0,0,0,.18);}}
.stat-card h3{{margin:0 0 6px;font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1px;}}
.stat-card .num{{font-size:44px;font-weight:700;color:#0B4F6C;line-height:1;}}
.stat-card small{{color:#aaa;font-size:12px;}}
.stat-card.filter-active{{border:2px solid #e74c3c;}}
#loadingBar {{ display: none !important; }}
#infoPanel{{position:fixed;right:-400px;top:0;width:390px;height:100vh;background:#fff;box-shadow:-4px 0 24px rgba(0,0,0,.18);z-index:9999;transition:right .35s cubic-bezier(.4,0,.2,1);overflow-y:auto;font-family:Segoe UI;}}
#infoPanel.open{{right:0;}}
#infoPanelHeader{{background:#0B4F6C;color:white;padding:18px 20px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:1;}}
#infoPanelHeader h3{{margin:0;font-size:16px;}}
#infoPanelClose{{background:none;border:none;color:white;font-size:22px;cursor:pointer;padding:0 4px;line-height:1;}}
#infoPanelBody{{padding:20px;}}
.info-badge{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:12px;}}
.info-row{{margin:10px 0;font-size:14px;color:#444;border-bottom:1px solid #f0f0f0;padding-bottom:8px;}}
.info-row span{{font-weight:600;color:#0B4F6C;}}
.badge-aktif{{display:inline-block;background:#e74c3c;color:white;border-radius:12px;font-size:11px;padding:2px 8px;margin-left:6px;vertical-align:middle;font-weight:bold;animation:pulse .6s ease;}}
@keyframes pulse{{0%{{transform:scale(0);}}70%{{transform:scale(1.2);}}100%{{transform:scale(1);}}}}
.toast{{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(60px);background:#0B4F6C;color:white;padding:12px 28px;border-radius:30px;font-family:Segoe UI;font-size:14px;opacity:0;transition:all .4s;z-index:99999;pointer-events:none;white-space:nowrap;box-shadow:0 4px 15px rgba(0,0,0,.2);}}
.toast.show{{opacity:1;transform:translateX(-50%) translateY(0);}}
#btnFilter, #btnReset {{ transition: all 0.2s ease-in-out; box-shadow: 0px 2px 6px rgba(0,0,0,.15); }}
#btnFilter:hover{{background:#083c52 !important;transform:translateY(-2px);box-shadow: 0px 6px 15px rgba(11, 79, 108, .35);}}
#btnFilter:active{{transform:translateY(0);box-shadow: 0px 2px 5px rgba(0,0,0,.2);}}
#btnReset:hover{{background:#c0392b !important;transform:translateY(-2px);box-shadow: 0px 6px 15px rgba(231, 76, 60, .35);}}
#btnReset:active{{transform:translateY(0);box-shadow: 0px 2px 5px rgba(0,0,0,.2);}}
#infoPanelClose:hover{{color: #ddd; transform: scale(1.1);}}
.role-badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 5px; color: white; }}
.role-ketua {{ background: #D8BA10; }}
.role-anggota {{ background: #9E9E9EA9; color: #333; }}
</style>

<div style="display:flex;justify-content:center;gap:25px;margin:30px;flex-wrap:wrap;">
    <div class="stat-card" id="cardPeriset">
        <h3>Total Periset</h3>
        <div class="num" id="statPeriset">{len(df['Periset'].unique())}</div>
        <small id="statPerisetSub">&nbsp;</small>
    </div>
    <div class="stat-card" id="cardKegiatan">
        <h3>Total Kegiatan</h3>
        <div class="num" id="statKegiatan">{len(df['Kegiatan_Riset'].unique())}</div>
        <small id="statKegiatanSub">&nbsp;</small>
    </div>
    <div class="stat-card" id="cardKelompok">
        <h3>Kelompok Riset</h3>
        <div class="num" id="statKelompok">{len(df['Kelompok_Riset'].unique())}</div>
        <small id="statKelompokSub">&nbsp;</small>
    </div>
</div>

<div id="infoPanel">
  <div id="infoPanelHeader">
    <h3 id="infoPanelTitle">Detail Node</h3>
    <button id="infoPanelClose">&#10005;</button>
  </div>
  <div id="infoPanelBody">
    <p style="color:#aaa;text-align:center;margin-top:40px;">Klik node pada graph<br>untuk melihat detail.</p>
  </div>
</div>
<div id="toastMsg" class="toast"></div>
"""

    filter_panel = """
<div style="width:90%;margin:auto;margin-top:25px;margin-bottom:25px;background:white;padding:25px;border-radius:15px;box-shadow:0px 4px 15px rgba(0,0,0,.15);font-family:Segoe UI;">
    <h2 style="margin-top:0;color:#0E5A77;">🔎 Filter Data (Multi-Select)</h2>
    <p style="color:gray;margin-bottom:25px;">Pilih beberapa kelompok, kegiatan, atau periset sekaligus. Data akan menyesuaikan secara dinamis.</p>
    <div style="display:flex;gap:20px;flex-wrap:wrap;">
        <div style="flex:1;min-width:260px;">
            <label style="font-weight:bold;color:#0E5A77;" id="labelKelompok">Kelompok Riset</label>
            <select id="filterKelompok" multiple style="width:100%;margin-top:8px;padding:12px;border-radius:10px;border:1px solid #ccc;font-size:15px;"></select>
        </div>
        <div style="flex:1;min-width:260px;">
            <label style="font-weight:bold;color:#0E5A77;" id="labelKegiatan">Kegiatan Riset</label>
            <select id="filterKegiatan" multiple style="width:100%;margin-top:8px;padding:12px;border-radius:10px;border:1px solid #ccc;font-size:15px;"></select>
        </div>
        <div style="flex:1;min-width:260px;">
            <label style="font-weight:bold;color:#0E5A77;" id="labelPeriset">Periset</label>
            <select id="filterPeriset" multiple style="width:100%;margin-top:8px;padding:12px;border-radius:10px;border:1px solid #ccc;font-size:15px;"></select>
        </div>
    </div>
    <div style="display:flex;gap:12px;margin-top:20px;">
        <button id="btnFilter" style="padding:12px 30px;background:#0B4F6C;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;">🔍 Terapkan Filter</button>
        <button id="btnReset" style="padding:12px 24px;background:#e74c3c;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;">✕ Reset</button>
    </div>
</div>
"""

    script = """
<script>
const dataNode = JSON.parse(document.getElementById('data-filter').textContent);
const hierarki = JSON.parse(document.getElementById('data-hierarki').textContent);

const TOTAL_PERISET  = dataNode.filter(function(d){return d.kategori==='periset';}).length;
const TOTAL_KEGIATAN = dataNode.filter(function(d){return d.kategori==='Kegiatan_Riset';}).length;
const TOTAL_KELOMPOK = dataNode.filter(function(d){return d.kategori==='Kelompok_Riset';}).length;

function showToast(msg){
    var t = document.getElementById('toastMsg');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, 3000);
}

document.getElementById('infoPanelClose').addEventListener('click', function(){
    document.getElementById('infoPanel').classList.remove('open');
});

function tampilkanInfoPanel(nodeId){
    var info = null;
    for(var i=0;i<dataNode.length;i++){
        if(dataNode[i].id === nodeId){ info = dataNode[i]; break; }
    }
    if(!info) return;

    var panel = document.getElementById('infoPanel');
    var body  = document.getElementById('infoPanelBody');
    var title = document.getElementById('infoPanelTitle');

    var html = '';
    if(info.kategori === 'Kelompok_Riset'){
        title.textContent = 'Kelompok Riset';
        html  = '<span class="info-badge" style="background:#0B4F6C;color:white;">Kelompok Riset</span>';
        html += '<div class="info-row"><span>Nama:</span><br>'+nodeId+'</div>';
        html += '<div class="info-row"><span>Koneksi:</span> '+info.centrality+'</div>';
        html += '<div class="info-row"><span>Jumlah Kegiatan:</span> '+info.jml_kegiatan+'</div>';
        html += '<div class="info-row"><span>Jumlah Periset:</span> '+info.jml_periset+'</div>';
        html += '<hr style="margin:16px 0;border:none;border-top:1px solid #eee;">';
        html += '<p style="font-size:13px;color:#666;font-weight:600;">Daftar Kegiatan:</p>';
        Object.keys(hierarki[nodeId]||{}).sort().forEach(function(kg){
            html += '<div style="font-size:13px;padding:6px 0;border-bottom:1px solid #f5f5f5;color:#333;">• '+kg+'</div>';
        });
    } else if(info.kategori === 'Kegiatan_Riset'){
        title.textContent = 'Kegiatan Riset';
        var perisetList = (hierarki[info.kelompok]||{})[nodeId] || [];
        html  = '<span class="info-badge" style="background:#03a9f4;color:white;">Kegiatan Riset</span>';
        html += '<div class="info-row"><span>Judul:</span><br>'+nodeId+'</div>';
        html += '<div class="info-row"><span>Kelompok:</span> '+info.kelompok+'</div>';
        html += '<div class="info-row"><span>Koneksi:</span> '+info.centrality+'</div>';
        html += '<div class="info-row"><span>Jumlah Periset:</span> '+perisetList.length+'</div>';
        html += '<hr style="margin:16px 0;border:none;border-top:1px solid #eee;">';
        html += '<p style="font-size:13px;color:#666;font-weight:600;">Daftar Periset:</p>';
        var perisetDetails = perisetList.map(function(p) {
            var peran = "Anggota";
            var pNode = dataNode.find(x => x.id === p);
            if(pNode && pNode.keterlibatan){
               var kt = pNode.keterlibatan.find(x => x.kegiatan === nodeId);
               if(kt) peran = kt.peran;
            }
            return { nama: p, peran: peran };
        });
        perisetDetails.sort(function(a, b) {
            if (a.peran.toLowerCase() === 'ketua' && b.peran.toLowerCase() !== 'ketua') return -1;
            if (a.peran.toLowerCase() !== 'ketua' && b.peran.toLowerCase() === 'ketua') return 1;
            return a.nama.localeCompare(b.nama);
        });
        perisetDetails.forEach(function(item){
            var roleClass = item.peran.toLowerCase() === 'ketua' ? 'role-ketua' : 'role-anggota';
            html += '<div style="font-size:13px;padding:6px 0;border-bottom:1px solid #f5f5f5;color:#333;"><span class="role-badge '+roleClass+'">'+item.peran+'</span> '+item.nama+'</div>';
        });
    } else {
        title.textContent = 'Periset';
        var statusLabel = info.status || '-';
        var badgeColor = '#346edb';
        var status_lower = statusLabel.toLowerCase();
        if(status_lower.indexOf('internal prsdi')>=0) badgeColor='#cc2e2e';
        else if(status_lower.indexOf('eksternal prsdi')>=0) badgeColor='#d512f3';
        else if(status_lower.indexOf('eksternal brin')>=0) badgeColor='#b4e73c';
        
        html  = '<span class="info-badge" style="background:'+badgeColor+';color:white;">'+statusLabel+'</span>';
        html += '<div class="info-row"><span>Nama:</span><br>'+nodeId+'</div>';
        html += '<div class="info-row"><span>Total Bobot:</span> '+info.bobot+'</div>';
        html += '<div class="info-row"><span>Koneksi:</span> '+info.centrality+'</div>';
        
        if (info.keterlibatan && info.keterlibatan.length > 0) {
            var sortedKet = info.keterlibatan.slice().sort(function(a, b) {
                if (a.peran.toLowerCase() === 'ketua' && b.peran.toLowerCase() !== 'ketua') return -1;
                if (a.peran.toLowerCase() !== 'ketua' && b.peran.toLowerCase() === 'ketua') return 1;
                return 0;
            });
            html += '<hr style="margin:16px 0;border:none;border-top:1px solid #eee;">';
            html += '<p style="font-size:13px;color:#666;font-weight:600;">Keterlibatan Kegiatan:</p>';
            sortedKet.forEach(function(ket){
                var roleClass = ket.peran.toLowerCase() === 'ketua' ? 'role-ketua' : 'role-anggota';
                html += '<div style="font-size:13px;padding:8px 0;border-bottom:1px solid #f5f5f5;color:#333;line-height:1.4;">';
                html += '<span class="role-badge '+roleClass+'">'+ket.peran+'</span> <b>'+ket.kegiatan+'</b><br>';
                html += '<small style="color:#777;margin-left:5px;">Kel: '+ket.kelompok+'</small>';
                html += '</div>';
            });
        }
    }
    body.innerHTML = html;
    panel.classList.add('open');
}

// Interaksi Network - dibungkus agar dipanggil setelah drawGraph() selesai
function initCustomEvents() {
    if (typeof network === 'undefined' || !network) {
        setTimeout(initCustomEvents, 100);
        return;
    }

    network.on("click", function(params){
        if(params.nodes.length == 0){
            document.getElementById('infoPanel').classList.remove('open');
            return;
        }
        var dipilih = params.nodes[0];
        tampilkanInfoPanel(dipilih);
        nodes.forEach(function(n){ nodes.update({id:n.id, hidden:true}); });
        edges.forEach(function(e){ edges.update({id:e.id, hidden:true}); });
        nodes.update({id:dipilih, hidden:false});
        network.getConnectedEdges(dipilih).forEach(function(edgeId){
            var edge = edges.get(edgeId);
            var tujuan1 = (edge.from == dipilih) ? edge.to : edge.from;
            nodes.update({id:tujuan1, hidden:false});
            edges.update({id:edgeId, hidden:false});
            network.getConnectedEdges(tujuan1).forEach(function(edgeId2){
                var edge2 = edges.get(edgeId2);
                var tujuan2 = (edge2.from == tujuan1) ? edge2.to : edge2.from;
                nodes.update({id:tujuan2, hidden:false});
                edges.update({id:edgeId2, hidden:false});
            });
        });
    });

    network.on("doubleClick", function(){ resetSemua(); });
}

function updateStatistik(visibleIds){
    if(!visibleIds){
        document.getElementById('statPeriset').textContent  = TOTAL_PERISET;
        document.getElementById('statKegiatan').textContent = TOTAL_KEGIATAN;
        document.getElementById('statKelompok').textContent = TOTAL_KELOMPOK;
        document.getElementById('statPerisetSub').innerHTML  = '&nbsp;';
        document.getElementById('statKegiatanSub').innerHTML = '&nbsp;';
        document.getElementById('statKelompokSub').innerHTML = '&nbsp;';
        ['cardPeriset','cardKegiatan','cardKelompok'].forEach(function(id){
            document.getElementById(id).classList.remove('filter-active');
        });
        return;
    }
    var cP=0, cK=0, cG=0;
    dataNode.forEach(function(item){
        if(!visibleIds[item.id]) return;
        if(item.kategori==='periset')        cP++;
        if(item.kategori==='Kegiatan_Riset') cK++;
        if(item.kategori==='Kelompok_Riset') cG++;
    });
    document.getElementById('statPeriset').textContent  = cP;
    document.getElementById('statKegiatan').textContent = cK;
    document.getElementById('statKelompok').textContent = cG;
    document.getElementById('statPerisetSub').textContent  = 'dari '+TOTAL_PERISET+' total';
    document.getElementById('statKegiatanSub').textContent = 'dari '+TOTAL_KEGIATAN+' total';
    document.getElementById('statKelompokSub').textContent = 'dari '+TOTAL_KELOMPOK+' total';
    document.getElementById('cardPeriset').classList.toggle('filter-active', cP < TOTAL_PERISET);
    document.getElementById('cardKegiatan').classList.toggle('filter-active', cK < TOTAL_KEGIATAN);
    document.getElementById('cardKelompok').classList.toggle('filter-active', cG < TOTAL_KELOMPOK);
}

function updateBadge(elId, value){
    var el = document.getElementById(elId);
    var old = el.querySelector('.badge-aktif');
    if(old) old.remove();
    if(value && value.length > 0){
        var b = document.createElement('span');
        b.className = 'badge-aktif';
        b.textContent = value.length + ' Dipilih';
        el.appendChild(b);
    }
}

function tampilkanSemua(){
    nodes.forEach(function(n){ nodes.update({id:n.id, hidden:false}); });
    edges.forEach(function(e){ edges.update({id:e.id, hidden:false}); });
    updateStatistik(null);
}

function buatPilihan(arr){
    var hasil = [];
    arr.forEach(function(v){ hasil.push({value:v, label:v}); });
    return hasil;
}

var allKelompok = Object.keys(hierarki).sort();
var allKegiatan = [];
var kegiatanSet = {};
allKelompok.forEach(function(k){
    Object.keys(hierarki[k]).forEach(function(kg){
        if(!kegiatanSet[kg]){ kegiatanSet[kg]=true; allKegiatan.push(kg); }
    });
});
allKegiatan.sort();

var allPeriset = [];
var perisetSet = {};
allKelompok.forEach(function(k){
    Object.keys(hierarki[k]).forEach(function(kg){
        hierarki[k][kg].forEach(function(p){
            if(!perisetSet[p]){ perisetSet[p]=true; allPeriset.push(p); }
        });
    });
});
allPeriset.sort();

var choiceOpt = {
    searchEnabled:true, 
    shouldSort:false, 
    removeItemButton:true, 
    searchResultLimit:100, 
    itemSelectText:""
};

var choiceKelompok = new Choices("#filterKelompok", Object.assign({}, choiceOpt, {placeholderValue:"Pilih Kelompok Riset..."}));
var choiceKegiatan = new Choices("#filterKegiatan", Object.assign({}, choiceOpt, {placeholderValue:"Pilih Kegiatan Riset..."}));
var choicePeriset  = new Choices("#filterPeriset", Object.assign({}, choiceOpt, {searchResultLimit:200, placeholderValue:"Pilih Periset..."}));

choiceKelompok.setChoices(buatPilihan(allKelompok), "value", "label", true);
choiceKegiatan.setChoices(buatPilihan(allKegiatan), "value", "label", true);
choicePeriset.setChoices(buatPilihan(allPeriset), "value", "label", true);

function updateKegiatan(kelompoks){
    var list = [];
    if(!kelompoks || kelompoks.length === 0){
        list = allKegiatan;
    } else {
        kelompoks.forEach(k => {
            Object.keys(hierarki[k]||{}).forEach(kg => { if(list.indexOf(kg)===-1) list.push(kg); });
        });
        list.sort();
    }
    choiceKegiatan.removeActiveItems();
    choiceKegiatan.clearChoices();
    choiceKegiatan.setChoices(buatPilihan(list), "value", "label", true);
}

function updatePeriset(kelompoks, kegiatans){
    var list=[], seen={};
    var hasKel = kelompoks && kelompoks.length > 0;
    var hasKeg = kegiatans && kegiatans.length > 0;
    
    if(!hasKel && !hasKeg){
        list = allPeriset;
    } else {
        var kelsToScan = hasKel ? kelompoks : allKelompok;
        kelsToScan.forEach(k => {
            var kegsToScan = hasKeg ? kegiatans : Object.keys(hierarki[k]||{});
            kegsToScan.forEach(kg => {
                if(hierarki[k] && hierarki[k][kg]){
                    hierarki[k][kg].forEach(p => {
                        if(!seen[p]){ seen[p]=true; list.push(p); }
                    });
                }
            });
        });
        list.sort();
    }
    choicePeriset.removeActiveItems();
    choicePeriset.clearChoices();
    choicePeriset.setChoices(buatPilihan(list), "value", "label", true);
}

document.getElementById("filterKelompok").addEventListener("change", function(){
    var vals = choiceKelompok.getValue(true);
    updateKegiatan(vals);
    updatePeriset(vals, []);
    updateBadge('labelKelompok', vals);
});
document.getElementById("filterKegiatan").addEventListener("change", function(){
    var kelVals = choiceKelompok.getValue(true);
    var kegVals = choiceKegiatan.getValue(true);
    updatePeriset(kelVals, kegVals);
    updateBadge('labelKegiatan', kegVals);
});
document.getElementById("filterPeriset").addEventListener("change", function(){
    updateBadge('labelPeriset', choicePeriset.getValue(true));
});

document.getElementById("btnFilter").addEventListener("click", terapkanFilter);

function resetSemua(){
    choiceKelompok.removeActiveItems();
    choiceKegiatan.removeActiveItems();
    choicePeriset.removeActiveItems();
    choiceKegiatan.clearChoices();
    choiceKegiatan.setChoices(buatPilihan(allKegiatan),"value","label",true);
    choicePeriset.clearChoices();
    choicePeriset.setChoices(buatPilihan(allPeriset),"value","label",true);
    ['labelKelompok','labelKegiatan','labelPeriset'].forEach(function(id){ updateBadge(id, null); });
    tampilkanSemua();
    setTimeout(function(){ network.fit({animation:{duration:600,easingFunction:"easeInOutQuad"}}); }, 100);
    showToast('🔄 Filter direset — menampilkan semua data');
}
document.getElementById("btnReset").addEventListener("click", resetSemua);

function terapkanFilter(){
    var kel = choiceKelompok.getValue(true);
    var keg = choiceKegiatan.getValue(true);
    var per = choicePeriset.getValue(true);
    
    // Fallback if they are not arrays (sometimes choices JS returns string if single item, but with multiple it should be array)
    if(typeof kel === 'string' && kel !== '') kel = [kel];
    if(typeof keg === 'string' && keg !== '') keg = [keg];
    if(typeof per === 'string' && per !== '') per = [per];

    var hasKel = kel && kel.length > 0;
    var hasKeg = keg && keg.length > 0;
    var hasPer = per && per.length > 0;

    if(!hasKel && !hasKeg && !hasPer){
        resetSemua();
        return;
    }

    var visible = {};

    dataNode.forEach(function(item){
        var match = false;

        // Jika user memilih Periset (Level terendah/terspesifik)
        if(hasPer){
            if(item.kategori === 'periset' && per.includes(item.id)) match = true;
            if(item.kategori === 'Kegiatan_Riset'){
                // Cek apakah ada periset terpilih yang ikut kegiatan ini
                var connectedPer = dataNode.filter(d => d.kategori==='periset' && per.includes(d.id));
                if(connectedPer.some(p => p.keterlibatan && p.keterlibatan.some(kt => kt.kegiatan === item.id))) match = true;
            }
            if(item.kategori === 'Kelompok_Riset'){
                var connectedPer2 = dataNode.filter(d => d.kategori==='periset' && per.includes(d.id));
                if(connectedPer2.some(p => p.keterlibatan && p.keterlibatan.some(kt => kt.kelompok === item.id))) match = true;
            }
        }
        // Jika user memilih Kegiatan (Level menengah)
        else if(hasKeg){
            if(item.kategori === 'Kegiatan_Riset' && keg.includes(item.id)) match = true;
            if(item.kategori === 'Kelompok_Riset'){
                var connectedKeg = dataNode.filter(d => d.kategori==='Kegiatan_Riset' && keg.includes(d.id));
                if(connectedKeg.some(k => k.kelompok === item.id)) match = true;
            }
            if(item.kategori === 'periset'){
                if(item.keterlibatan && item.keterlibatan.some(kt => keg.includes(kt.kegiatan))) match = true;
            }
        }
        // Jika user memilih Kelompok (Level tertinggi)
        else if(hasKel){
            if(item.kategori === 'Kelompok_Riset' && kel.includes(item.id)) match = true;
            if(item.kategori === 'Kegiatan_Riset' && kel.includes(item.kelompok)) match = true;
            if(item.kategori === 'periset' && item.keterlibatan && item.keterlibatan.some(kt => kel.includes(kt.kelompok))) match = true;
        }

        if(match) visible[item.id] = true;
    });

    nodes.forEach(function(n){ nodes.update({id:n.id, hidden:!visible[n.id]}); });
    edges.forEach(function(e){ edges.update({id:e.id, hidden:!(visible[e.from]&&visible[e.to])}); });

    updateStatistik(visible);

    var cP = Object.keys(visible).filter(function(id){
        var d = dataNode.find(function(x){return x.id===id;});
        return d && d.kategori==='periset';
    }).length;

    var msg = '✅ Filter Diterapkan  |  '+cP+' periset ditampilkan';
    showToast(msg);

    setTimeout(function(){ network.fit({animation:{duration:700,easingFunction:"easeInOutQuad"}}); }, 150);
}

// Mulai inisialisasi event klik setelah semua fungsi didefinisikan
initCustomEvents();
</script>
"""

    html = html.replace('<script src="lib/bindings/utils.js"></script>', '')
    html = html.replace('<body>', '<body>' + header + statistik + filter_panel)

    # JANGAN patch drawGraph() — initCustomEvents belum terdefinisi saat itu
    # initCustomEvents() dipanggil di akhir custom script block setelah didefinisikan

    json_scripts = f'''
<script id="data-filter" type="application/json">
{json_filter}
</script>
<script id="data-hierarki" type="application/json">
{json_hierarki}
</script>
'''
    html = html.replace("</body>", json_scripts + script + "</body>")

    return html
