from flask import Flask, request, jsonify, send_file, Response
import pandas as pd
import os
from supabase import create_client, Client

app = Flask(__name__)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ejzmpthmgzfaclpbbtsi.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqem1wdGhtZ3pmYWNscGJidHNpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTA3NzQ2NSwiZXhwIjoyMTAwNjUzNDY1fQ.xO-TN_p4NmAuNQ-qCyIpfeJt-zAXTYVYUKlctVFO5HU")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cache sederhana agar tidak generate ulang graph setiap request
_html_cache = None

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    global _html_cache
    # Gunakan cache jika sudah ada (reset cache dengan ?refresh=1)
    if _html_cache and request.args.get('refresh') != '1':
        return _html_cache
    import main  # Import di sini agar tidak jalan saat Vercel load module
    html_output = main.main()
    _html_cache = html_output
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

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        response = supabase.table('keanggotaan_riset').select(
            "kegiatan_id, periset_id, peran, periset(nama_lengkap, status), kegiatan_riset(judul_kegiatan, kelompok_riset(nama_kelompok))"
        ).execute()
        
        data = []
        for row in response.data:
            periset = row.get("periset") or {}
            kegiatan = row.get("kegiatan_riset") or {}
            kelompok = kegiatan.get("kelompok_riset") or {}
            
            data.append({
                "keg_id": row.get("kegiatan_id"),
                "per_id": row.get("periset_id"),
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
        periset = request.form.get('periset')
        peran = request.form.get('peran')
        status = request.form.get('status')
        
        # Upload foto ke Supabase Storage (bukan lokal lagi)
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
        kel_id = kel_res.data[0]['id']

        # 2. Upsert Kegiatan Riset (Cari berdasarkan judul dulu karena kita nggak set unique di judul)
        keg_cek = supabase.table("kegiatan_riset").select("id").eq("judul_kegiatan", kegiatan).execute()
        if keg_cek.data and len(keg_cek.data) > 0:
            keg_id = keg_cek.data[0]['id']
        else:
            keg_res = supabase.table("kegiatan_riset").insert({"kelompok_id": kel_id, "judul_kegiatan": kegiatan, "singkatan": ""}).execute()
            keg_id = keg_res.data[0]['id']

        # 3. Upsert Periset
        periset_payload = {"nama_lengkap": periset, "status": status, "total_bobot": 3 if peran.lower() == 'ketua' else 1}
        if foto_url:
            periset_payload["foto_url"] = foto_url
        per_res = supabase.table("periset").upsert(periset_payload, on_conflict="nama_lengkap").execute()
        per_id = per_res.data[0]['id']

        # 4. Upsert Keanggotaan
        supabase.table("keanggotaan_riset").upsert({
            "kegiatan_id": keg_id,
            "periset_id": per_id,
            "peran": peran.capitalize(),
            "bobot": 3 if peran.lower() == 'ketua' else 1
        }, on_conflict="kegiatan_id,periset_id").execute()
        
        global _html_cache
        _html_cache = None  # Reset cache agar dashboard tampil data terbaru
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
            
        supabase.table('keanggotaan_riset').delete().eq('kegiatan_id', keg_id).eq('periset_id', per_id).execute()
        global _html_cache
        _html_cache = None  # Reset cache agar dashboard tampil data terbaru
        return jsonify({'status': 'success', 'message': 'Data berhasil dihapus'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/peran', methods=['PATCH'])
def update_peran():
    try:
        data = request.json
        keg_id = data.get('kegiatan_id')
        per_id = data.get('periset_id')
        peran = data.get('peran')
        
        if not keg_id or not per_id or not peran:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        bobot = 3 if peran.lower() == 'ketua' else 1
        supabase.table('keanggotaan_riset').update({'peran': peran.capitalize(), 'bobot': bobot}).eq('kegiatan_id', keg_id).eq('periset_id', per_id).execute()
        global _html_cache
        _html_cache = None  # Reset cache agar dashboard tampil data terbaru
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/status', methods=['PATCH'])
def update_status():
    try:
        data = request.json
        per_id = data.get('periset_id')
        status = data.get('status')
        
        if not per_id or not status:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
            
        supabase.table('periset').update({'status': status}).eq('id', per_id).execute()
        global _html_cache
        _html_cache = None  # Reset cache agar dashboard tampil data terbaru
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Mulai Server Flask...")
    print("Akses Halaman Admin: http://localhost:5000/admin")
    print("Akses Visualisasi: http://localhost:5000/")
    app.run(debug=True, port=5000)
