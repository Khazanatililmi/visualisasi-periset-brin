let allData = [];
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
            loadData(); // reload all data to update analytics
        } else {
            alert('Gagal hapus: ' + json.message);
        }
    } catch (e) {
        alert('Gagal hapus data');
    }
}

async function saveData() {
    const btn = document.getElementById('btnSimpan');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Menyimpan...';

    const form = document.getElementById('formData');
    const formData = new FormData();
    
    formData.append('kelompok', document.getElementById('kelompok').value);
    formData.append('kegiatan', document.getElementById('kegiatan').value);
    formData.append('periset', document.getElementById('periset').value);
    formData.append('peran', document.getElementById('peran').value);
    formData.append('status', document.getElementById('status').value);
    
    const fotoFile = document.getElementById('foto').files[0];
    if (fotoFile) {
        formData.append('foto', fotoFile);
    }

    try {
        const response = await fetch('/api/data', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Tutup modal
            const modalEl = document.getElementById('modalTambah');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
            
            form.reset();
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
