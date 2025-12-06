let currentFloorFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('floor-select');
    if (select) {
        select.addEventListener('change', (e) => {
            currentFloorFilter = e.target.value;
            updateMonitor();
        });
    }
});

function updateMonitor() {
    fetch('/api/rooms/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('monitor-container');
            container.innerHTML = '';
            
            // Group rooms by floor
            const floors = {};
            data.rooms.forEach(room => {
                const floor = Math.floor(parseInt(room.room_id) / 100);
                if (!floors[floor]) floors[floor] = [];
                floors[floor].push(room);
            });

            // Sort floors
            const sortedFloors = Object.keys(floors).sort();

            // Populate select dynamically
            const select = document.getElementById('floor-select');
            if (select) {
                // Keep track of current selection to restore if needed (though we only append)
                // Check which floors are already in the dropdown
                const existingOptions = new Set();
                for (let i = 0; i < select.options.length; i++) {
                    existingOptions.add(select.options[i].value);
                }

                sortedFloors.forEach(f => {
                    const floorStr = f.toString();
                    if (!existingOptions.has(floorStr)) {
                        const opt = document.createElement('option');
                        opt.value = floorStr;
                        opt.textContent = `Floor ${floorStr}`;
                        select.appendChild(opt);
                    }
                });
            }

            sortedFloors.forEach(floor => {
                if (currentFloorFilter !== 'all' && currentFloorFilter !== floor) return;

                // Create Floor Section
                const floorSection = document.createElement('div');
                floorSection.className = 'mb-5';
                floorSection.innerHTML = `<h5 class="border-bottom pb-2 mb-3 text-muted">Floor ${floor}</h5>`;
                
                const row = document.createElement('div');
                row.className = 'row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 row-cols-xl-5 g-4';
                
                // Sort rooms in floor
                floors[floor].sort((a, b) => a.room_id.localeCompare(b.room_id));

                floors[floor].forEach(room => {
                    let statusClass = 'status-off';
                    let statusText = '关机';
                    
                    if (room.is_on) {
                        if (room.status === 'SERVING') { statusClass = 'status-serving'; statusText = '送风中'; }
                        else if (room.status === 'WAITING') { statusClass = 'status-waiting'; statusText = '等待中'; }
                        else { statusClass = 'status-idle'; statusText = '待机'; }
                    }

                    const occupancyText = room.occupancy_status === 'OCCUPIED' ? 
                        '<span class="badge bg-danger rounded-pill badge-small">OCCUPIED</span>' : 
                        '<span class="badge bg-success rounded-pill badge-small">VACANT</span>';

                    const html = `
                        <div class="col">
                            <div class="card h-100 border-0 shadow-sm room-card ${statusClass}">
                                <div class="card-body p-4">
                                    <div class="d-flex justify-content-between align-items-start mb-3">
                                        <h5 class="fw-bold mb-0">${room.room_id}</h5>
                                        ${occupancyText}
                                    </div>
                                    
                                    <div class="mb-3">
                                        <h2 class="display-6 fw-bold mb-0">${room.current_temp.toFixed(1)}°</h2>
                                        <small class="text-muted text-uppercase fw-bold status-text">${statusText}</small>
                                    </div>

                                    <div class="d-flex justify-content-between align-items-end border-top pt-3 mt-3">
                                        <div>
                                            <div class="small text-muted info-text">Target: <strong>${room.target_temp.toFixed(1)}°</strong></div>
                                            <div class="small text-muted info-text">Fan: <strong>${room.fan_speed}</strong></div>
                                        </div>
                                        <div class="fw-bold text-dark">¥${room.fee.toFixed(2)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    row.innerHTML += html;
                });
                
                floorSection.appendChild(row);
                container.appendChild(floorSection);
            });
        });
}

setInterval(updateMonitor, 1000);
updateMonitor();