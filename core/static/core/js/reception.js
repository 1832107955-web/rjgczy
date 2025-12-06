document.addEventListener('DOMContentLoaded', function() {
    const btnCheckin = document.getElementById('btn-checkin');
    if (btnCheckin) {
        btnCheckin.addEventListener('click', checkIn);
    }

    const btnCheckout = document.getElementById('btn-checkout');
    if (btnCheckout) {
        btnCheckout.addEventListener('click', checkOut);
    }
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

function checkIn() {
    const roomId = document.getElementById('checkin-room').value;
    const guestId = document.getElementById('guest-id').value;
    
    fetch('/api/checkin/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ room_id: roomId, guest_id: guestId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            alert('入住办理成功');
            location.reload();
        } else {
            alert('入住失败: ' + data.message);
        }
    });
}

function checkOut() {
    const roomId = document.getElementById('checkout-room').value;
    if (!confirm(`确定为房间 ${roomId} 退房吗?`)) return;

    fetch('/api/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ room_id: roomId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            document.getElementById('bill-area').classList.remove('d-none');
            
            // Summary
            document.getElementById('bill-rate').innerText = '¥' + data.bill.daily_rate.toFixed(2) + '/night';
            document.getElementById('bill-days').innerText = data.bill.days;
            document.getElementById('bill-accom').innerText = '¥' + data.bill.accommodation_fee.toFixed(2);
            document.getElementById('bill-ac').innerText = '¥' + data.bill.ac_fee.toFixed(2);
            document.getElementById('bill-total').innerText = '¥' + data.bill.total.toFixed(2);
            
            // AC Details
            const tbody = document.getElementById('ac-details-body');
            tbody.innerHTML = '';
            if (data.bill.ac_details && data.bill.ac_details.length > 0) {
                data.bill.ac_details.forEach(session => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${session.start}</td>
                        <td>${session.end}</td>
                        <td>${session.mode === 'cool' ? '制冷' : '制热'}</td>
                        <td>${session.fan}</td>
                        <td>¥${session.fee.toFixed(2)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No AC usage recorded</td></tr>';
            }
            
        } else {
            alert('退房失败: ' + (data.message || 'Unknown error'));
        }
    });
}