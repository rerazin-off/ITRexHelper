document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-modal-open]').forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            var modal = document.getElementById(trigger.getAttribute('data-modal-open'));
            if (modal) modal.classList.add('open');
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            var modal = trigger.closest('.modal-overlay');
            if (modal) modal.classList.remove('open');
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
        overlay.addEventListener('click', function (event) {
            if (event.target === overlay) overlay.classList.remove('open');
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
            if (supportWidget) supportWidget.classList.remove('open');
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
            var statusEl = document.getElementById('detailStatus');
            statusEl.textContent = btn.dataset.status || '';
            statusEl.className = 'status-badge ' + (btn.dataset.statusClass || 'status-new');

            var contractLink = document.getElementById('detailContractDownload');
            var footer = modal.querySelector('.modal__footer');
            if (footer) {
                if (!contractLink) {
                    contractLink = document.createElement('a');
                    contractLink.id = 'detailContractDownload';
                    contractLink.className = 'btn btn-outline btn-sm';
                    contractLink.textContent = 'Скачать договор';
                    footer.insertBefore(contractLink, footer.firstChild);
                }
                if (btn.dataset.statusCode === 'CLOSED' && btn.dataset.ticketId) {
                    contractLink.href = '/tickets/' + btn.dataset.ticketId + '/contract/download/';
                    contractLink.style.display = 'inline-flex';
                } else {
                    contractLink.style.display = 'none';
                    contractLink.href = '#';
                }
            }

            modal.classList.add('open');
        });
    });

    function setAdminTicketReadonly(readonly) {
        var fields = ['adminContactInput', 'adminDescriptionInput', 'adminStatusSelect', 'adminPrioritySelect'];
        fields.forEach(function (id) {
            var el = document.getElementById(id);
            if (el) el.disabled = readonly;
        });
        var saveBtn = document.getElementById('adminTicketSave');
        if (saveBtn) saveBtn.style.display = readonly ? 'none' : 'inline-flex';
        var notice = document.getElementById('adminReadonlyNotice');
        if (notice) notice.style.display = readonly ? 'block' : 'none';
    }

    document.querySelectorAll('[data-admin-ticket-open]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var modal = document.getElementById('adminTicketModal');
            if (!modal) return;
            document.getElementById('adminTicketForm').action = btn.dataset.action || '#';
            document.getElementById('adminTicketNext').value = btn.dataset.next || '';
            document.getElementById('adminCompany').textContent = btn.dataset.company || 'Не указано';
            document.getElementById('adminClient').textContent = btn.dataset.client || '';
            document.getElementById('adminContactInput').value = btn.dataset.contact || '';
            document.getElementById('adminDate').textContent = btn.dataset.date || '';
            document.getElementById('adminDescriptionInput').value = btn.dataset.description || '';
            if (btn.dataset.statusValue) document.getElementById('adminStatusSelect').value = btn.dataset.statusValue;
            if (btn.dataset.priorityValue) document.getElementById('adminPrioritySelect').value = btn.dataset.priorityValue;
            setAdminTicketReadonly(btn.dataset.readonly === '1');
            modal.classList.add('open');
        });
    });
});
