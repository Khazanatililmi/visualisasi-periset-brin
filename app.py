from flask import Flask, request, jsonify, send_file, Response
import pandas as pd
import os
from supabase import create_client, Client

app = Flask(__name__)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ejzmpthmgzfaclpbbtsi.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqem1wdGhtZ3pmYWNscGJidHNpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTA3NzQ2NSwiZXhwIjoyMTAwNjUzNDY1fQ.xO-TN_p4NmAuNQ-qCyIpfeJt-zAXTYVYUKlctVFO5HU")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Supabase Storage Cache (shared across all Vercel instances) ───────────────
# Menyimpan HTML dashboard di Supabase Storage agar semua instance Vercel
# menggunakan cache yang sama. Ketika data berubah, cache dihapus dari storage
# sehingga instance manapun yang handle request berikutnya akan regenerate.

_CACHE_BUCKET = "foto-periset"
_CACHE_PATH   = "__cache__/dashboard.html"
_mem_cache    = None  # Layer 1: in-memory (cepat, per-instance)

def _get_cached_html():
    """Ambil HTML dari in-memory (cepat) atau Supabase Storage (shared)."""
    global _mem_cache
    if _mem_cache:
        return _mem_cache
    try:
        data = supabase.storage.from_(_CACHE_BUCKET).download(_CACHE_PATH)
        if data:
            html = data.decode("utf-8")
            _mem_cache = html  # Simpan ke memory untuk request berikutnya
            return html
    except Exception:
        pass
    return None

def _save_cached_html(html: str):
    """Simpan HTML ke in-memory dan Supabase Storage."""
    global _mem_cache
    _mem_cache = html
    try:
        supabase.storage.from_(_CACHE_BUCKET).upload(
            _CACHE_PATH,
            html.encode("utf-8"),
            file_options={"content-type": "text/html; charset=utf-8", "upsert": "true"}
        )
    except Exception as e:
        print(f"[Cache] Gagal simpan ke Supabase Storage: {e}")

def _invalidate_cache():
    """Hapus cache dari memory dan Supabase Storage (trigger regenerasi di semua instance)."""
    global _mem_cache
    _mem_cache = None
    try:
        supabase.storage.from_(_CACHE_BUCKET).remove([_CACHE_PATH])
    except Exception:
        pass  # Tidak masalah jika file tidak ada


@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    # Paksa regenerasi jika ada ?refresh=1
    if request.args.get('refresh') != '1':
        cached = _get_cached_html()
        if cached:
            return cached
    import main  # Import di sini agar tidak jalan saat Vercel load module
    html_output = main.main()
    _save_cached_html(html_output)
    return html_output

@app.route('/login_admin')
def login_admin_page():
    return send_file(os.path.join(os.path.dirname(__file__), 'admin', 'login_admin.html'))

@app.route('/admin')
def admin_page():
    return send_file(os.path.join(os.path.dirname(__file__), 'admin', 'admin.html'))

@app.route('/admin.js')
def admin_js():
    return send_file(os.path.join(os.path.dirname(__file__), 'admin', 'admin.js'))

@app.route('/api/options', methods=['GET'])
def get_options():
    """Return existing data for cascading dropdowns in admin form."""
    try:
        kel = supabase.table('kelompok_riset').select('id, nama_kelompok').order('nama_kelompok').execute()
        keg = supabase.table('kegiatan_riset').select('id, judul_kegiatan, kelompok_id').order('judul_kegiatan').execute()
        per = supabase.table('periset').select('id, nama_lengkap, status').order('nama_lengkap').execute()
        return jsonify({'kelompok': kel.data, 'kegiatan': keg.data, 'periset': per.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        response = supabase.table('keanggotaan_riset').select(
            "kegiatan_id, periset_id, peran, periset(nama_lengkap, status), kegiatan_riset(judul_kegiatan, kelompok_riset(id, nama_kelompok))"
        ).execute()
        
        data = []
        for row in response.data:
            periset  = row.get("periset") or {}
            kegiatan = row.get("kegiatan_riset") or {}
            kelompok = kegiatan.get("kelompok_riset") or {}
            
            data.append({
                "keg_id": row.get("kegiatan_id"),
                "per_id": row.get("periset_id"),
                "kel_id": kelompok.get("id"),
                "Kelompok_Riset": kelompok.get("nama_kelompok", "-"),
                "Kegiatan_Riset": kegiatan.get("judul_kegiatan", "-"),
                "Periset": periset.get("nama_lengkap", "-"),
                "Peran": row.get("peran", "-"),
                "Status": periset.get("status", "-")
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['POST'])
def add_data():
    try:
        kelompok = request.form.get('kelompok')
        kegiatan = request.form.get('kegiatan')
        periset  = request.form.get('periset')
        peran    = request.form.get('peran')
        status   = request.form.get('status')
        
        # Upload foto ke Supabase Storage
        foto_url = None
        foto = request.files.get('foto')
        if foto and foto.filename:
            ext = os.path.splitext(foto.filename)[1]
            foto_filename = f"{periset.replace(' ', '_').lower()}{ext}"
            file_bytes = foto.read()
            content_type = "image/png" if ext.lower() == ".png" else "image/jpeg"
            try:
                supabase.storage.from_("foto-periset").upload(foto_filename, file_bytes, file_options={"content-type": content_type, "upsert": "true"})
                foto_url = supabase.storage.from_("foto-periset").get_public_url(foto_filename)
            except Exception as e:
                print(f"Gagal upload foto: {e}")
        
        # 1. Upsert Kelompok Riset
        kel_res = supabase.table("kelompok_riset").upsert({"nama_kelompok": kelompok, "deskripsi": f"Kelompok Riset {kelompok}"}, on_conflict="nama_kelompok").execute()
        kel_id  = kel_res.data[0]['id']

        # 2. Cari / buat Kegiatan Riset
        keg_cek = supabase.table("kegiatan_riset").select("id").eq("judul_kegiatan", kegiatan).execute()
        if keg_cek.data and len(keg_cek.data) > 0:
            keg_id = keg_cek.data[0]['id']
        else:
            keg_res = supabase.table("kegiatan_riset").insert({"kelompok_id": kel_id, "judul_kegiatan": kegiatan, "singkatan": ""}).execute()
            keg_id  = keg_res.data[0]['id']

        # 3. Upsert Periset
        periset_payload = {"nama_lengkap": periset, "status": status, "total_bobot": 3 if peran.lower() == 'ketua' else 1}
        if foto_url:
            periset_payload["foto_url"] = foto_url
        per_res = supabase.table("periset").upsert(periset_payload, on_conflict="nama_lengkap").execute()
        per_id  = per_res.data[0]['id']

        # 4. Upsert Keanggotaan
        supabase.table("keanggotaan_riset").upsert({
            "kegiatan_id": keg_id,
            "periset_id":  per_id,
            "peran":       peran.capitalize(),
            "bobot":       3 if peran.lower() == 'ketua' else 1
        }, on_conflict="kegiatan_id,periset_id").execute()
        
        _invalidate_cache()
        return jsonify({'status': 'success', 'message': 'Data berhasil ditambahkan ke Supabase!'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data', methods=['DELETE'])
def delete_data():
    try:
        keg_id = request.args.get('kegiatan_id')
        per_id = request.args.get('periset_id')
        if not keg_id or not per_id:
            return jsonify({'status': 'error', 'message': 'Missing IDs'}), 400

        # 1. Hapus keanggotaan
        supabase.table('keanggotaan_riset').delete().eq('kegiatan_id', keg_id).eq('periset_id', per_id).execute()
        cascade_info = []

        # 2. Cek apakah periset masih punya keanggotaan lain
        sisa_per = supabase.table('keanggotaan_riset').select('id').eq('periset_id', per_id).execute()
        if len(sisa_per.data) == 0:
            supabase.table('periset').delete().eq('id', per_id).execute()
            cascade_info.append('periset')

        # 3. Cek apakah kegiatan masih punya anggota lain
        sisa_keg = supabase.table('keanggotaan_riset').select('id').eq('kegiatan_id', keg_id).execute()
        if len(sisa_keg.data) == 0:
            keg_data = supabase.table('kegiatan_riset').select('kelompok_id').eq('id', keg_id).execute()
            if keg_data.data:
                kel_id = keg_data.data[0]['kelompok_id']
                supabase.table('kegiatan_riset').delete().eq('id', keg_id).execute()
                cascade_info.append('kegiatan')
                # 4. Cek apakah kelompok masih punya kegiatan lain
                sisa_kel = supabase.table('kegiatan_riset').select('id').eq('kelompok_id', kel_id).execute()
                if len(sisa_kel.data) == 0:
                    supabase.table('kelompok_riset').delete().eq('id', kel_id).execute()
                    cascade_info.append('kelompok')

        _invalidate_cache()
        msg = 'Data berhasil dihapus'
        if cascade_info:
            msg += f'. Otomatis dihapus juga: {", ".join(cascade_info)} yang tidak lagi terkoneksi.'
        return jsonify({'status': 'success', 'message': msg, 'cascade': cascade_info})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/cleanup-orphans', methods=['DELETE'])
def cleanup_orphans():
    """Scan dan hapus semua record periset, kegiatan, kelompok yang tidak punya koneksi apapun."""
    try:
        deleted = {'periset': 0, 'kegiatan': 0, 'kelompok': 0}

        # 1. Hapus periset orphan (tidak ada di keanggotaan_riset)
        all_per  = supabase.table('periset').select('id').execute()
        used_per = {r['periset_id'] for r in supabase.table('keanggotaan_riset').select('periset_id').execute().data}
        for p in all_per.data:
            if p['id'] not in used_per:
                supabase.table('periset').delete().eq('id', p['id']).execute()
                deleted['periset'] += 1

        # 2. Hapus kegiatan orphan (tidak ada di keanggotaan_riset)
        all_keg  = supabase.table('kegiatan_riset').select('id, kelompok_id').execute()
        used_keg = {r['kegiatan_id'] for r in supabase.table('keanggotaan_riset').select('kegiatan_id').execute().data}
        for k in all_keg.data:
            if k['id'] not in used_keg:
                supabase.table('kegiatan_riset').delete().eq('id', k['id']).execute()
                deleted['kegiatan'] += 1

        # 3. Hapus kelompok orphan (tidak punya kegiatan apapun)
        all_kel  = supabase.table('kelompok_riset').select('id').execute()
        used_kel = {r['kelompok_id'] for r in supabase.table('kegiatan_riset').select('kelompok_id').execute().data}
        for k in all_kel.data:
            if k['id'] not in used_kel:
                supabase.table('kelompok_riset').delete().eq('id', k['id']).execute()
                deleted['kelompok'] += 1

        _invalidate_cache()
        return jsonify({'status': 'success', 'deleted': deleted})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/peran', methods=['PATCH'])
def update_peran():
    try:
        data   = request.json
        keg_id = data.get('kegiatan_id')
        per_id = data.get('periset_id')
        peran  = data.get('peran')
        
        if not keg_id or not per_id or not peran:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        bobot = 3 if peran.lower() == 'ketua' else 1
        supabase.table('keanggotaan_riset').update({'peran': peran.capitalize(), 'bobot': bobot}).eq('kegiatan_id', keg_id).eq('periset_id', per_id).execute()
        _invalidate_cache()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/status', methods=['PATCH'])
def update_status():
    try:
        data   = request.json
        per_id = data.get('periset_id')
        status = data.get('status')
        
        if not per_id or not status:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        supabase.table('periset').update({'status': status}).eq('id', per_id).execute()
        _invalidate_cache()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/master/periset', methods=['PUT'])
def edit_master_periset():
    try:
        per_id = request.form.get('id')
        nama   = request.form.get('nama_lengkap')
        status = request.form.get('status')
        
        if not per_id or not nama:
            return jsonify({'status': 'error', 'message': 'Missing ID or Nama'}), 400
            
        payload = {"nama_lengkap": nama, "status": status}
        
        foto = request.files.get('foto')
        if foto and foto.filename:
            ext = os.path.splitext(foto.filename)[1]
            foto_filename = f"{nama.replace(' ', '_').lower()}{ext}"
            file_bytes = foto.read()
            content_type = "image/png" if ext.lower() == ".png" else "image/jpeg"
            try:
                supabase.storage.from_("foto-periset").upload(foto_filename, file_bytes, file_options={"content-type": content_type, "upsert": "true"})
                payload["foto_url"] = supabase.storage.from_("foto-periset").get_public_url(foto_filename)
            except Exception as e:
                print(f"Gagal upload foto: {e}")
                
        supabase.table('periset').update(payload).eq('id', per_id).execute()
        _invalidate_cache()
        return jsonify({'status': 'success', 'message': 'Data Periset berhasil diupdate'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/master/kegiatan', methods=['PUT'])
def edit_master_kegiatan():
    try:
        data = request.json
        keg_id = data.get('id')
        judul = data.get('judul_kegiatan')
        
        if not keg_id or not judul:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        supabase.table('kegiatan_riset').update({'judul_kegiatan': judul}).eq('id', keg_id).execute()
        _invalidate_cache()
        return jsonify({'status': 'success', 'message': 'Judul Kegiatan berhasil diupdate'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/master/kelompok', methods=['PUT'])
def edit_master_kelompok():
    try:
        data = request.json
        kel_id = data.get('id')
        nama = data.get('nama_kelompok')
        
        if not kel_id or not nama:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        supabase.table('kelompok_riset').update({
            'nama_kelompok': nama,
            'deskripsi': f"Kelompok Riset {nama}"
        }).eq('id', kel_id).execute()
        
        _invalidate_cache()
        return jsonify({'status': 'success', 'message': 'Nama Kelompok berhasil diupdate'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Mulai Server Flask...")
    print("Akses Halaman Admin: http://localhost:5000/admin")
    print("Akses Visualisasi: http://localhost:5000/")
    app.run(debug=True, port=5000)
