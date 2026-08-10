let allData = [];
let optionsData = { kelompok: [], kegiatan: [], periset: [] };
let filteredData = [];
let currentPage = 1;
const rowsPerPage = 10;

document.addEventListener('DOMContentLoaded', function() {
    loadData();

    document.getElementById('btnSimpan').addEventListener('click', function(e) {
        e.preventDefault();
        saveData();
    });

    document.getElementById('searchInput').addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        filteredData = allData.filter(row => {
            return (row['Periset'] || '').toLowerCase().includes(query) ||
                   (row['Kegiatan_Riset'] || '').toLowerCase().includes(query) ||
                   (row['Kelompok_Riset'] || '').toLowerCase().includes(query);
        });
        currentPage = 1;
        renderTable();
    });

    // Load dropdown options saat modal dibuka
    document.getElementById('modalTambah').addEventListener('show.bs.modal', loadOptions);
    // Reset form saat modal ditutup
    document.getElementById('modalTambah').addEventListener('hidden.bs.modal', resetForm);
});

async function loadData() {
    try {
        const response = await fetch('/api/data');
        allData = await response.json();
        filteredData = [...allData];
        
        let totalKel = new Set();
        let totalKeg = new Set();
        let totalPer = new Set();
        
        allData.forEach(row => {
            const kelompok = row['Kelompok_Riset'] || '-';
            const kegiatan = row['Kegiatan_Riset'] || '-';
            const periset = row['Periset'] || '-';
            if (kelompok !== '-') totalKel.add(kelompok);
            if (kegiatan !== '-') totalKeg.add(kegiatan);
            if (periset !== '-') totalPer.add(periset);
        });
        
        document.getElementById('totalKelompok').innerText = totalKel.size;
        document.getElementById('totalKegiatan').innerText = totalKeg.size;
        document.getElementById('totalPeriset').innerText = totalPer.size;
        
        renderTable();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('isiTabel').innerHTML = '<tr><td colspan="7" class="text-center text-danger">Gagal memuat data. Pastikan server Flask berjalan.</td></tr>';
    }
}

function renderTable() {
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginated = filteredData.slice(start, end);
    
    let html = '';
    paginated.forEach((row, index) => {
        const globalIndex = start + index + 1;
        
        const kegId = row.keg_id;
        const perId = row.per_id;
        const peran = row.Peran || '-';
        const status = row.Status || '-';

        const selKetua = peran.toLowerCase() === 'ketua' ? 'selected' : '';
        const selAnggota = peran.toLowerCase() === 'anggota' ? 'selected' : '';
        
        const selInt = status.toLowerCase().includes('internal prsdi') ? 'selected' : '';
        const selEksPR = status.toLowerCase().includes('eksternal prsdi') ? 'selected' : '';
        const selEksBR = status.toLowerCase().includes('eksternal brin') ? 'selected' : '';

        html += `
            <tr>
                <td>${globalIndex}</td>
                <td>${row['Kelompok_Riset']}</td>
                <td>${row['Kegiatan_Riset']}</td>
                <td>${row['Periset']}</td>
                <td>
                    <select class="form-select form-select-sm border-0 bg-light" onchange="updatePeran('${kegId}', '${perId}', this.value)">
                        <option value="Ketua" ${selKetua}>Ketua</option>
                        <option value="Anggota" ${selAnggota}>Anggota</option>
                    </select>
                </td>
                <td>
                    <select class="form-select form-select-sm border-0 bg-light" onchange="updateStatus('${perId}', this.value)">
                        <option value="Internal PRSDI" ${selInt}>Internal PRSDI</option>
                        <option value="Eksternal PRSDI" ${selEksPR}>Eksternal PRSDI</option>
                        <option value="Eksternal BRIN" ${selEksBR}>Eksternal BRIN</option>
                    </select>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteData('${kegId}', '${perId}')" title="Hapus">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    document.getElementById('isiTabel').innerHTML = html || '<tr><td colspan="7" class="text-center py-4">Tidak ada data ditemukan.</td></tr>';
    
    // Setup pagination info
    document.getElementById('pageInfo').innerText = `Menampilkan ${start + (paginated.length > 0 ? 1 : 0)} - ${start + paginated.length} dari ${filteredData.length} data`;
    
    renderPagination();
}

function renderPagination() {
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    let html = '';
    
    if (totalPages > 1) {
        html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}"><a class="page-link" href="#" onclick="goToPage(${currentPage - 1}); return false;">Prev</a></li>`;
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
                html += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#" onclick="goToPage(${i}); return false;">${i}</a></li>`;
            } else if (i === currentPage - 2 || i === currentPage + 2) {
                html += `<li class="page-item disabled"><a class="page-link" href="#">...</a></li>`;
            }
        }
        html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}"><a class="page-link" href="#" onclick="goToPage(${currentPage + 1}); return false;">Next</a></li>`;
    }
    
    document.getElementById('paginationControls').innerHTML = html;
}

function goToPage(page) {
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
}

async function updatePeran(kegId, perId, val) {
    try {
        await fetch('/api/data/peran', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({kegiatan_id: kegId, periset_id: perId, peran: val})
        });
        allData.forEach(r => { if(r.keg_id == kegId && r.per_id == perId) r.Peran = val; });
    } catch (e) {
        alert('Gagal update peran');
    }
}

async function updateStatus(perId, val) {
    try {
        await fetch('/api/data/status', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({periset_id: perId, status: val})
        });
        allData.forEach(r => { if(r.per_id == perId) r.Status = val; });
    } catch (e) {
        alert('Gagal update status');
    }
}

async function deleteData(kegId, perId) {
    if (!confirm('Hapus keterlibatan periset ini dari kegiatan?')) return;
    try {
        const res = await fetch(`/api/data?kegiatan_id=${kegId}&periset_id=${perId}`, { method: 'DELETE' });
        const json = await res.json();
        if (json.status === 'success') {
            // Tampilkan info jika ada cascade delete
            if (json.cascade && json.cascade.length > 0) {
                const label = json.cascade.join(', ');
                alert(`✅ Keanggotaan dihapus.\n\n🗑️ Data berikut juga otomatis dihapus karena tidak lagi terkoneksi: ${label}.`);
            }
            loadData();
        } else {
            alert('Gagal hapus: ' + json.message);
        }
    } catch (e) {
        alert('Gagal hapus data');
    }
}

async function cleanupOrphans() {
    const konfirmasi = confirm(
        '🧹 Bersihkan Data Orphan?\n\n' +
        'Ini akan menghapus PERMANEN semua:\n' +
        '• Periset yang tidak terlibat di kegiatan manapun\n' +
        '• Kegiatan yang tidak punya anggota apapun\n' +
        '• Kelompok Riset yang tidak punya kegiatan apapun\n\n' +
        'Lanjutkan?'
    );
    if (!konfirmasi) return;

    const btn = document.querySelector('button[onclick="cleanupOrphans()"]');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Membersihkan...';

    try {
        const res = await fetch('/api/cleanup-orphans', { method: 'DELETE' });
        const json = await res.json();
        if (json.status === 'success') {
            const d = json.deleted;
            const total = d.periset + d.kegiatan + d.kelompok;
            if (total === 0) {
                alert('✅ Database sudah bersih! Tidak ada data orphan ditemukan.');
            } else {
                alert(
                    `✅ Pembersihan selesai!\n\n` +
                    `🗑️ Dihapus:\n` +
                    `• ${d.periset} periset\n` +
                    `• ${d.kegiatan} kegiatan\n` +
                    `• ${d.kelompok} kelompok riset`
                );
                loadData();
            }
        } else {
            alert('Gagal membersihkan: ' + json.message);
        }
    } catch (e) {
        alert('Terjadi kesalahan saat membersihkan data.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ─── Cascading Dropdown Functions ────────────────────────────────────────────

async function loadOptions() {
    try {
        const res = await fetch('/api/options');
        optionsData = await res.json();
        populateKelompok();
        populatePeriset();
    } catch (e) {
        console.error('Gagal memuat opsi dropdown:', e);
    }
}

function populateKelompok() {
    const sel = document.getElementById('kelompok');
    sel.innerHTML = '<option value="">— Pilih Kelompok Riset —</option>';
    optionsData.kelompok.forEach(k => {
        sel.innerHTML += `<option value="${k.id}" data-nama="${k.nama_kelompok}">${k.nama_kelompok}</option>`;
    });
    sel.innerHTML += '<option value="__new__">➕ Buat Kelompok Baru</option>';
    document.getElementById('kelompokBaru').classList.add('d-none');
    resetKegiatan();
}

function resetKegiatan() {
    const sel = document.getElementById('kegiatan');
    sel.innerHTML = '<option value="">— Pilih kelompok dulu —</option><option value="__new__">➕ Buat Kegiatan Baru</option>';
    document.getElementById('kegiatanBaru').classList.add('d-none');
    document.getElementById('kegiatanBaru').value = '';
}

function populatePeriset() {
    const sel = document.getElementById('periset');
    sel.innerHTML = '<option value="">— Pilih Periset —</option>';
    optionsData.periset.forEach(p => {
        sel.innerHTML += `<option value="${p.id}" data-nama="${p.nama_lengkap}" data-status="${p.status || ''}">${p.nama_lengkap}</option>`;
    });
    sel.innerHTML += '<option value="__new__">➕ Tambah Periset Baru</option>';
    document.getElementById('perisetBaruDiv').classList.add('d-none');
    document.getElementById('perisetExistingInfo').classList.add('d-none');
}

function onKelompokChange() {
    const sel = document.getElementById('kelompok');
    const val = sel.value;
    const newInput = document.getElementById('kelompokBaru');

    if (val === '__new__') {
        newInput.classList.remove('d-none');
        // Tampilkan semua kegiatan jika kelompok baru
        const kegSel = document.getElementById('kegiatan');
        kegSel.innerHTML = '<option value="">— Isi nama kelompok dulu —</option><option value="__new__">➕ Buat Kegiatan Baru</option>';
        document.getElementById('kegiatanBaru').classList.add('d-none');
    } else {
        newInput.classList.add('d-none');
        newInput.value = '';
        // Filter kegiatan berdasar kelompok terpilih
        const kegSel = document.getElementById('kegiatan');
        kegSel.innerHTML = '<option value="">— Pilih Kegiatan Riset —</option>';
        const filtered = val
            ? optionsData.kegiatan.filter(k => String(k.kelompok_id) === String(val))
            : optionsData.kegiatan;
        filtered.forEach(k => {
            kegSel.innerHTML += `<option value="${k.id}" data-judul="${k.judul_kegiatan}">${k.judul_kegiatan}</option>`;
        });
        kegSel.innerHTML += '<option value="__new__">➕ Buat Kegiatan Baru</option>';
        document.getElementById('kegiatanBaru').classList.add('d-none');
        document.getElementById('kegiatanBaru').value = '';
    }
}

function onKegiatanChange() {
    const val = document.getElementById('kegiatan').value;
    const newInput = document.getElementById('kegiatanBaru');
    if (val === '__new__') {
        newInput.classList.remove('d-none');
    } else {
        newInput.classList.add('d-none');
        newInput.value = '';
    }
}

function onPerisetChange() {
    const sel = document.getElementById('periset');
    const val = sel.value;
    const newDiv = document.getElementById('perisetBaruDiv');
    const existingInfo = document.getElementById('perisetExistingInfo');

    if (val === '__new__') {
        newDiv.classList.remove('d-none');
        existingInfo.classList.add('d-none');
    } else if (val) {
        newDiv.classList.add('d-none');
        existingInfo.classList.remove('d-none');
        // Auto-fill status dari data existing
        const dataStatus = sel.options[sel.selectedIndex].getAttribute('data-status') || '';
        const statusSel = document.getElementById('status');
        for (let opt of statusSel.options) {
            if (opt.value.toLowerCase() === dataStatus.toLowerCase()) {
                opt.selected = true;
                break;
            }
        }
    } else {
        newDiv.classList.add('d-none');
        existingInfo.classList.add('d-none');
    }
}

function resetForm() {
    document.getElementById('formData').reset();
    document.getElementById('kelompokBaru').classList.add('d-none');
    document.getElementById('kegiatanBaru').classList.add('d-none');
    document.getElementById('perisetBaruDiv').classList.add('d-none');
    document.getElementById('perisetExistingInfo').classList.add('d-none');
    resetKegiatan();
}

// ─── Save Data ────────────────────────────────────────────────────────────────

async function saveData() {
    const btn = document.getElementById('btnSimpan');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Menyimpan...';

    // Resolve nilai kelompok
    const kelSel = document.getElementById('kelompok');
    const kelVal = kelSel.value === '__new__'
        ? document.getElementById('kelompokBaru').value.trim()
        : (kelSel.options[kelSel.selectedIndex]?.getAttribute('data-nama') || '');

    // Resolve nilai kegiatan
    const kegSel = document.getElementById('kegiatan');
    const kegVal = kegSel.value === '__new__'
        ? document.getElementById('kegiatanBaru').value.trim()
        : (kegSel.options[kegSel.selectedIndex]?.getAttribute('data-judul') || '');

    // Resolve nilai periset
    const perSel = document.getElementById('periset');
    const perVal = perSel.value === '__new__'
        ? document.getElementById('perisetBaru').value.trim()
        : (perSel.options[perSel.selectedIndex]?.getAttribute('data-nama') || '');

    // Validasi
    if (!kelVal || !kegVal || !perVal) {
        alert('Harap lengkapi semua field yang wajib diisi (*).');
        btn.disabled = false;
        btn.innerHTML = 'Simpan';
        return;
    }

    const formData = new FormData();
    formData.append('kelompok', kelVal);
    formData.append('kegiatan', kegVal);
    formData.append('periset', perVal);
    formData.append('peran', document.getElementById('peran').value);
    formData.append('status', document.getElementById('status').value);

    // Foto hanya jika periset baru
    if (perSel.value === '__new__') {
        const fotoFile = document.getElementById('foto').files[0];
        if (fotoFile) formData.append('foto', fotoFile);
    }

    try {
        const response = await fetch('/api/data', { method: 'POST', body: formData });
        const result = await response.json();

        if (result.status === 'success') {
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalTambah'));
            modal.hide();
            loadData();
        } else {
            alert('Gagal menyimpan: ' + result.message);
        }
    } catch (error) {
        console.error('Error saving data:', error);
        alert('Terjadi kesalahan saat menyimpan data.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Simpan';
    }
}
