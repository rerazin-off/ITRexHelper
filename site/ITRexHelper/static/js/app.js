document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-modal-open]').forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            var modalId = trigger.getAttribute('data-modal-open');
            var modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('open');
            }
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            var modal = trigger.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('open');
            }
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
        overlay.addEventListener('click', function (event) {
            if (event.target === overlay) {
                overlay.classList.remove('open');
            }
        });
    });

    var supportFab = document.getElementById('supportFab');
    var supportWidget = document.getElementById('supportWidget');
    if (supportFab && supportWidget) {
        supportFab.addEventListener('click', function () {
            supportWidget.classList.toggle('open');
        });
    }

    document.querySelectorAll('[data-support-close]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (supportWidget) {
                supportWidget.classList.remove('open');
            }
        });
    });

    document.querySelectorAll('.password-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = btn.parentElement.querySelector('input');
            if (!input) return;
            input.type = input.type === 'password' ? 'text' : 'password';
        });
    });

    document.querySelectorAll('[data-ticket-open]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var modal = document.getElementById('ticketDetailModal');
            if (!modal) return;
            document.getElementById('detailDate').textContent = btn.dataset.date || '';
            document.getElementById('detailDescription').textContent = btn.dataset.description || '';
            document.getElementById('detailStatus').textContent = btn.dataset.status || '';
            document.getElementById('detailStatus').className = 'status-badge ' + (btn.dataset.statusClass || 'status-new');
            modal.classList.add('open');
        });
    });

    document.querySelectorAll('[data-admin-ticket-open]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var modal = document.getElementById('adminTicketModal');
            if (!modal) return;
            document.getElementById('adminTicketForm').action = btn.dataset.action || '#';
            document.getElementById('adminCompany').textContent = btn.dataset.company || 'Не указано';
            document.getElementById('adminClient').textContent = btn.dataset.client || '';
            document.getElementById('adminContact').textContent = btn.dataset.contact || '';
            document.getElementById('adminDate').textContent = btn.dataset.date || '';
            document.getElementById('adminDeadline').textContent = btn.dataset.deadline || 'Не указана';
            document.getElementById('adminDescription').textContent = btn.dataset.description || '';
            var statusEl = document.getElementById('adminStatus');
            statusEl.textContent = btn.dataset.status || '';
            statusEl.className = 'status-badge ' + (btn.dataset.statusClass || 'status-new');
            var statusSelect = document.getElementById('adminStatusSelect');
            if (statusSelect && btn.dataset.statusValue) {
                statusSelect.value = btn.dataset.statusValue;
            }
            modal.classList.add('open');
        });
    });
});
