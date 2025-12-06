let currentState = {};
let roomId = null;

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('main-container');
    if (container) {
        roomId = container.dataset.roomId;
    }

    if (roomId) {
        fetchStatus();
        setInterval(fetchStatus, 1000);
    }

    const powerBtn = document.getElementById('power-btn');
    if (powerBtn) {
        powerBtn.addEventListener('click', togglePower);
    }

    const btnMinus = document.getElementById('btn-temp-minus');
    if (btnMinus) {
        btnMinus.addEventListener('click', () => changeTemp(-1));
    }

    const btnPlus = document.getElementById('btn-temp-plus');
    if (btnPlus) {
        btnPlus.addEventListener('click', () => changeTemp(1));
    }

    const modeInputs = document.querySelectorAll('input[name="mode"]');
    modeInputs.forEach(input => {
        input.addEventListener('change', updateSettings);
    });

    const fanInputs = document.querySelectorAll('input[name="fan"]');
    fanInputs.forEach(input => {
        input.addEventListener('change', updateSettings);
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function fetchStatus() {
    if (!roomId) return;
    fetch(`/api/room/${roomId}/`)
        .then(res => res.json())
        .then(data => {
            currentState = data;
            render();
        });
}

function render() {
    document.getElementById('current-temp').innerText = currentState.current_temp.toFixed(1) + "°C";
    document.getElementById('fee').innerText = "¥" + currentState.fee.toFixed(2);
    document.getElementById('target-temp-display').innerText = currentState.target_temp.toFixed(1);
    
    // Status Badge
    const badge = document.getElementById('status-badge');
    if (!currentState.is_on) {
        badge.className = "badge rounded-pill bg-secondary px-3 py-2";
        badge.innerText = "关机";
    } else {
        if (currentState.status === 'SERVING') {
            badge.className = "badge rounded-pill bg-success px-3 py-2";
            badge.innerText = "送风中";
        } else if (currentState.status === 'WAITING') {
            badge.className = "badge rounded-pill bg-warning text-dark px-3 py-2";
            badge.innerText = "等待中";
        } else {
            badge.className = "badge rounded-pill bg-info text-dark px-3 py-2";
            badge.innerText = "待机";
        }
    }

    // Power Button
    const pwrBtn = document.getElementById('power-btn');
    const controls = document.getElementById('controls');
    if (currentState.is_on) {
        pwrBtn.innerText = "关机";
        pwrBtn.className = "btn btn-success w-100 py-3 mb-4 fw-bold shadow-sm";
        controls.classList.remove('controls-disabled');
    } else {
        pwrBtn.innerText = "开机";
        pwrBtn.className = "btn btn-secondary w-100 py-3 mb-4 fw-bold shadow-sm";
        controls.classList.add('controls-disabled');
    }

    // Sync Inputs
    const modeInput = document.getElementById(`mode-${currentState.mode.toLowerCase()}`);
    if (modeInput) modeInput.checked = true;
    
    const fanInput = document.getElementById(`fan-${currentState.fan_speed.toLowerCase()}`);
    if (fanInput) fanInput.checked = true;
}

function togglePower() {
    const newState = !currentState.is_on;
    postUpdate({ is_on: newState });
}

function changeTemp(delta) {
    let newTemp = currentState.target_temp + delta;
    postUpdate({ target_temp: newTemp });
}

function updateSettings() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const fan = document.querySelector('input[name="fan"]:checked').value;
    postUpdate({ mode: mode, fan_speed: fan });
}

function postUpdate(data) {
    if (!roomId) return;
    fetch(`/api/control/${roomId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    }).then(() => fetchStatus());
}