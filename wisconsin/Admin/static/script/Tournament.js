// kali code 

(() => {
    'use strict';


    const TOURNAMENT_TYPE_LABELS = {
        INTER_COLLEGE: 'Inter College',
        INTRA_COLLEGE: 'Intra College',
        INTER_DEPARTMENT: 'Inter Department',
        INTRA_DEPARTMENT: 'Intra Department',
        OPEN: 'Open Tournament'
    };

    const STATUS_LABELS = {
        CREATED: 'Created',
        INVITATION_SENT: 'Invitation Sent',
        REGISTRATION_OPEN: 'Registration Open',
        REGISTRATION_CLOSED: 'Registration Closed',
        VERIFICATION: 'Verification',
        APPROVED: 'Approved',
        FIXTURES_READY: 'Fixtures Ready',
        ONGOING: 'Ongoing',
        COMPLETED: 'Completed',
        ARCHIVED: 'Archived'
    };

    const APPLICATION_STATUS_LABELS = {
        INVITED: 'Invited',
        APPLIED: 'Applied',
        APPROVED: 'Approved',
        REJECTED: 'Rejected'
    };

    const RESULT_LABELS = {
        PARTICIPATED: 'Participated',
        WINNER: 'Winner',
        RUNNER_UP: 'Runner Up',
        THIRD_PLACE: 'Third Place'
    };

    const DASHBOARD_DATA = JSON.parse(
        document.getElementById('tournament-dashboard-data').textContent
    );

    const tournaments = DASHBOARD_DATA.tournaments;
    const invitations = DASHBOARD_DATA.invitations;
    const participants = DASHBOARD_DATA.participants;


  

const ROWS_PER_PAGE = 5;

const tablePages = {
    tournaments: 1,
    invitations: 1,
    participants: 1
};


function renderPagination(containerId, currentPage, totalItems, onPageChange) {

    const container = document.getElementById(containerId);

    if (!container) return;

    const totalPages = Math.ceil(totalItems / ROWS_PER_PAGE);

    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';

    const startItem =
        totalItems === 0
            ? 0
            : ((currentPage - 1) * ROWS_PER_PAGE) + 1;

    const endItem =
        Math.min(currentPage * ROWS_PER_PAGE, totalItems);

    html += `
        <span class="trn-pagination__info">
            Showing ${startItem}–${endItem} of ${totalItems}
        </span>
    `;

    html += `
        <button
            type="button"
            ${currentPage === 1 ? 'disabled' : ''}
            data-page="${currentPage - 1}">
            <i data-lucide="chevron-left"></i>
        </button>
    `;

    for (let page = 1; page <= totalPages; page++) {

        html += `
            <button
                type="button"
                class="${page === currentPage ? 'active' : ''}"
                data-page="${page}">
                ${page}
            </button>
        `;
    }

    html += `
        <button
            type="button"
            ${currentPage === totalPages ? 'disabled' : ''}
            data-page="${currentPage + 1}">
            <i data-lucide="chevron-right"></i>
        </button>
    `;

    container.innerHTML = html;

    container.querySelectorAll('button[data-page]').forEach(button => {

        button.addEventListener('click', () => {

            if (button.disabled) return;

            const page = parseInt(button.dataset.page, 10);

            if (!page || page < 1 || page > totalPages) return;

            onPageChange(page);
        });

    });

    if (window.lucide) {
        lucide.createIcons();
    }
}

   
    

    function formatDate(d) {
        if (!d) return '—';
        return new Date(d + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    function badge(value, labelMap) {
        const key = value.toLowerCase();
        const label = labelMap[value] || value;
        return `<span class="trn-badge trn-badge--${key}">${label}</span>`;
    }

   

    function animateCounters() {
        document.querySelectorAll('.trn-counter').forEach(el => {
            const target = parseInt(el.dataset.count, 10) || 0;
            let current = 0;
            const step = Math.max(1, Math.ceil(target / 60));
            const timer = setInterval(() => {
                current += step;
                if (current >= target) { current = target; clearInterval(timer); }
                el.textContent = current.toLocaleString();
            }, 20);
        });
    }


    function tournamentNameCellHtml(t) {
        const isCompleted = t.status === 'COMPLETED';
        return `${t.tournament_name}${isCompleted ? '<span class="trn-completed-badge">Completed</span>' : ''}`;
    }

    function tournamentActionsCell(t) {
        const isCompleted = t.status === 'COMPLETED';
        return `
            <div class="trn-actions">

                <button
                    type="button"
                    class="trn-action-btn trn-action-btn--view"
                    data-trn-action="view"
                    data-uuid="${t.tournament_uuid}"
                    title="View Tournament">
                    <i data-lucide="eye"></i>
                </button>

                ${isCompleted ? '' : `
                <button
                    type="button"
                    class="trn-action-btn trn-action-btn--complete"
                    data-trn-action="complete"
                    data-uuid="${t.tournament_uuid}"
                    title="Complete Tournament">
                    <i data-lucide="check-circle-2"></i>
                </button>
                `}

            </div>
        `;
    }


    function renderTournamentsTable() {

    const tBody = document.getElementById('tournamentsTableBody');

    if (!tBody) return;

    tBody.innerHTML = '';

    const currentPage = tablePages.tournaments;

    const start =
        (currentPage - 1) * ROWS_PER_PAGE;

    const end =
        start + ROWS_PER_PAGE;

    const pageData =
        tournaments.slice(start, end);

    pageData.forEach(t => {

        const pct = t.maximum_participants
            ? Math.round(
                (t.registered_participants / t.maximum_participants) * 100
            )
            : 0;

        const row = document.createElement('tr');

        row.dataset.uuid = t.tournament_uuid;

        row.innerHTML = `
             <td>
                <span class="trn-cell-primary trn-tournament-name-cell">
                    ${tournamentNameCellHtml(t)}
                </span>
                <br>
                <span class="trn-cell-muted">
                    ${t.tournament_code}
                </span>
            </td>

            <td>${t.sport}</td>

            <td>
                ${TOURNAMENT_TYPE_LABELS[t.tournament_type] || t.tournament_type}
            </td>

            <td>
                ${t.participation_type === 'TEAM'
                    ? 'Team'
                    : 'Individual'}
            </td>

            <td>${t.venue}</td>

            <td>${formatDate(t.start_date)}</td>

            <td>${formatDate(t.end_date)}</td>

            <td class="trn-tournament-actions-cell">
                ${tournamentActionsCell(t)}
            </td>
        `;

        tBody.appendChild(row);
    });

    const countEl = document.getElementById('tournamentsCount');

    if (countEl) {
        const totalPages = Math.ceil(
            tournaments.length / ROWS_PER_PAGE
        );

        countEl.textContent =
            totalPages > 1
                ? `Showing page ${currentPage} of ${totalPages}`
                : `Showing ${tournaments.length} tournaments`;
    }

    renderPagination(
        'tournamentsPagination',
        currentPage,
        tournaments.length,
        page => {
            tablePages.tournaments = page;
            renderTournamentsTable();
        }
    );

    if (window.lucide) {
        lucide.createIcons();
    }
}





    function invitationActionsCell(inv) {

    const canTakeAction = inv.application_status === 'APPLIED';

    return `
         <div class="trn-actions">

            <!-- View -->
            <button type="button"
                    class="trn-action-btn trn-action-btn--view"
                    title="View"
                    data-inv-action="view"
                    data-uuid="${inv.invitation_uuid}">
                <i data-lucide="eye"></i>
            </button>

            ${window.canUpdateInvitation ? `
            <!-- Accept -->
            <button type="button"
                    class="trn-action-btn trn-action-btn--accept"
                    title="Accept"
                    data-inv-action="accept"
                    data-uuid="${inv.invitation_uuid}"
                    ${canTakeAction ? '' : 'disabled'}>
                <i data-lucide="check"></i>
            </button>

            <!-- Reject -->
            <button type="button"
                    class="trn-action-btn trn-action-btn--reject"
                    title="Reject"
                    data-inv-action="reject"
                    data-uuid="${inv.invitation_uuid}"
                    ${canTakeAction ? '' : 'disabled'}>
                <i data-lucide="x"></i>
            </button>
            ` : ''}

        </div>
    `;
}




        function renderInvitationsTable() {

    const iBody =
        document.getElementById('invitationsTableBody');

    if (!iBody) return;

    iBody.innerHTML = '';

    const currentPage = tablePages.invitations;

    const start =
        (currentPage - 1) * ROWS_PER_PAGE;

    const end =
        start + ROWS_PER_PAGE;

    const pageData =
        invitations.slice(start, end);

    pageData.forEach(inv => {

        const row = document.createElement('tr');

        row.dataset.uuid = inv.invitation_uuid;

        row.innerHTML = `
            <td class="trn-cell-primary">
                ${inv.tournament}
            </td>

            <td>${inv.college_name}</td>

            <td>${inv.department_name}</td>

            <td>${inv.contact_person}</td>

            <td class="trn-cell-muted">
                ${inv.email}
            </td>

            <td class="trn-invitation-status-cell">
                ${badge(
                    inv.application_status,
                    APPLICATION_STATUS_LABELS
                )}
            </td>

            <td>
                ${formatDate(inv.invitation_sent_at)}
            </td>

            <td>
                ${invitationActionsCell(inv)}
            </td>
        `;

        iBody.appendChild(row);
    });

    const countEl =
        document.getElementById('invitationsCount');

    if (countEl) {

        const totalPages = Math.ceil(
            invitations.length / ROWS_PER_PAGE
        );

        countEl.textContent =
            totalPages > 1
                ? `Showing page ${currentPage} of ${totalPages}`
                : `Showing ${invitations.length} invitations`;
    }

    renderPagination(
        'invitationsPagination',
        currentPage,
        invitations.length,
        page => {

            tablePages.invitations = page;

            renderInvitationsTable();

            // Re-render icons after changing page
            if (window.lucide) {
                lucide.createIcons();
            }
        }
    );

    if (window.lucide) {
        lucide.createIcons();
    }
}




    function getCookie(name) {
        const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return match ? decodeURIComponent(match.pop()) : '';
    }


    document.getElementById('trnToastClose')?.addEventListener('click', () => {
        const toast = document.getElementById('trnRoleToast');
        if (!toast) return;
        clearTimeout(toast._hideTimer);
        toast.classList.add('hiding');
        setTimeout(() => { toast.hidden = true; }, 250);
    });
   
   

  function showToast(message, type, title) {
    const toast = document.getElementById('trnRoleToast');
    if (!toast) return;

    const iconWrap = document.getElementById('trnToastIconWrap');
    const icon = document.getElementById('trnToastIcon');
    const titleEl = document.getElementById('trnToastTitle');
    const msg = document.getElementById('trnToastMsg');
    const isSuccess = type === 'success';

    titleEl.textContent = title || (isSuccess ? 'Success' : 'Error');
    msg.textContent = message;
    iconWrap.classList.toggle('trn-role-toast__icon-wrap--success', isSuccess);
    // icon.setAttribute('data-lucide', isSuccess ? 'check-circle' : 'x-circle');
    iconWrap.innerHTML = `<i data-lucide="${isSuccess ? 'check-circle' : 'x-circle'}" id="trnToastIcon"></i>`;


    toast.hidden = false;
    toast.classList.remove('hiding');
    if (window.lucide) lucide.createIcons();

    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => { toast.hidden = true; }, 250);
    }, 3200);
}
 

    function renderPlayersList(app, participationType) {
    if (!app || !app.players || app.players.length === 0) {
        return `
            <div class="trn-insight-empty">
                No participant details submitted.
            </div>
        `;
    }

    return `
        <div class="trn-modal-row trn-players-title">
            <span>Players</span>
            <strong>${app.players.length}</strong>
        </div>

        <div class="trn-modal-players-list">
            ${app.players.map((player, index) => {

                

                let name = '';

                if (typeof player === 'string') {
                    name = player;
                } else if (player && typeof player === 'object') {
                    name = player.name || player.player_name || '—';
                }

                return `
                    <div class="trn-modal-player">
                        <span class="trn-modal-player__number">
                            ${index + 1}.
                        </span>
                        <span class="trn-modal-player__name">
                            ${name || '—'}
                        </span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

    function openInvitationModal(uuid) {
        const overlay = document.getElementById('invitationModalOverlay');
        const body = document.getElementById('invitationModalBody');
        const acceptBtn = document.getElementById('invitationModalAccept');
        const rejectBtn = document.getElementById('invitationModalReject');
        if (!overlay || !body) return;

        // body.innerHTML = `<div class="trn-insight-empty">Loading…</div>`;
        // overlay.classList.add('is-open');
        // acceptBtn.dataset.uuid = uuid;
        // rejectBtn.dataset.uuid = uuid;
        // acceptBtn.disabled = true;
        // rejectBtn.disabled = true;

        body.innerHTML = `<div class="trn-insight-empty">Loading…</div>`;
        overlay.classList.add('is-open');
        if (acceptBtn) { acceptBtn.dataset.uuid = uuid; acceptBtn.disabled = true; }
        if (rejectBtn) { rejectBtn.dataset.uuid = uuid; rejectBtn.disabled = true; }

        fetch(`/dashboard/tournaments/invitation/${uuid}/`)
            .then(res => res.json())
            .then(data => {
                const app = data.application;
                 
                const canTakeAction = data.application_status === 'APPLIED';

                // acceptBtn.disabled = !canTakeAction;
                // rejectBtn.disabled = !canTakeAction;

                if (acceptBtn) acceptBtn.disabled = !canTakeAction;
                if (rejectBtn) rejectBtn.disabled = !canTakeAction;
 
                body.innerHTML = `
                    <div class="trn-modal-section">
                        <div class="trn-modal-row"><span>Tournament</span><strong>${data.tournament}</strong></div>
                        <div class="trn-modal-row"><span>contact Person</span><strong>${data.contact_person}</strong></div>
                        <div class="trn-modal-row"><span>Email</span><strong>${data.email}</strong></div>
                        <div class="trn-modal-row"><span>Applied On</span><strong>${formatDate(app ? app.applied_at : null)}</strong></div>
                        <div class="trn-modal-row"><span>Status</span>${badge(data.application_status, APPLICATION_STATUS_LABELS)}</div>
                    </div>
                    <div class="trn-modal-section">
                        <h4 class="trn-modal-section__title">${data.participation_type === 'TEAM' ? 'Team Details' : 'Participant Details'}</h4>
                        <div class="trn-modal-row">
                            <span>${data.participation_type === 'TEAM' ? 'Team Name' : 'Participant Name'}</span>
                            <strong>${
                                app
                                    ? (data.participation_type === 'TEAM'
                                        ? (app.team_name || '—')
                                        : (app.entry_name || '—'))
                                    : '—'
                            }</strong>
                        </div>
                        <div class="trn-modal-row"><span>Contact Person</span><strong>${app ? app.contact_person : '—'}</strong></div>
                        <div class="trn-modal-row"><span>Contact Mobile</span><strong>${app ? app.contact_mobile : '—'}</strong></div>
                        ${data.participation_type === 'TEAM' ? `
                        <div class="trn-modal-row"><span>Coach</span><strong>${app ? app.coach_name : '—'}</strong></div>
                        <div class="trn-modal-row"><span>Players Count</span><strong>${app ? app.players_count : '—'}</strong></div>
                        ${renderPlayersList(app, data.participation_type)}
                        ` : ''}
                        <div class="trn-modal-row"><span>Faculty Remarks</span><strong>${app && app.faculty_remarks ? app.faculty_remarks : '—'}</strong></div>
                    </div>
                `;
                if (window.lucide) lucide.createIcons();
            })
            .catch(() => { body.innerHTML = `<div class="trn-insight-empty">Failed to load application details.</div>`; });
    }

    function closeInvitationModal() {
        const overlay = document.getElementById('invitationModalOverlay');
        if (overlay) overlay.classList.remove('is-open');
    }

    function submitInvitationAction(uuid, action) {
        return fetch(`/dashboard/tournaments/invitation/${uuid}/action/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `action=${action}`
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }

            const inv = invitations.find(i => i.invitation_uuid === uuid);
            if (inv) inv.application_status = data.application_status;

            const row = document.querySelector(`#invitationsTableBody tr[data-uuid="${uuid}"]`);
            if (row) {
                row.querySelector('.trn-invitation-status-cell').innerHTML = badge(data.application_status, APPLICATION_STATUS_LABELS);
                row.querySelectorAll('[data-inv-action="accept"], [data-inv-action="reject"]').forEach(btn => btn.disabled = true);
            }
            closeInvitationModal();

            // const message = action === 'accept'
            //     ? 'Tournament application accepted successfully.'
            //     : 'Tournament application rejected successfully.';
            // showToast(message, 'success');
            const message = action === 'accept'
                ? 'Tournament application accepted successfully.'
                : 'Tournament application rejected successfully.';
            const toastTitle = action === 'accept'
                ? 'Invitation Accepted'
                : 'Invitation Rejected';
            showToast(message, 'success', toastTitle);
           
            // setTimeout(() => window.location.reload(), 1100);
        })
        .catch(() => showToast('Something went wrong. Please try again.', 'error'));
    }


        function applyInvitationStatusUpdate(payload) {
        const inv = invitations.find(i => i.invitation_uuid === payload.invitation_uuid);
        if (inv) {
            Object.assign(inv, payload);
        }

        const row = document.querySelector(`#invitationsTableBody tr[data-uuid="${payload.invitation_uuid}"]`);
        if (!row) return; 

        const statusCell = row.querySelector('.trn-invitation-status-cell');
        if (statusCell) {
            statusCell.innerHTML = badge(payload.application_status, APPLICATION_STATUS_LABELS);
        }

        const canTakeAction = payload.application_status === 'APPLIED';
        row.querySelectorAll('[data-inv-action="accept"], [data-inv-action="reject"]').forEach(btn => {
            btn.disabled = !canTakeAction;
        });

        if (window.lucide) lucide.createIcons();
    }

    function applyParticipantAdded(payload) {
        const alreadyExists = participants.some(
            p => p.invitation_uuid && p.invitation_uuid === payload.invitation_uuid
        );
        if (alreadyExists) return;

        participants.unshift(payload);
        tablePages.participants = 1;
        renderParticipantsTable();
    }

    function initInvitationSocket() {
        const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const socket = new WebSocket(`${scheme}://${window.location.host}/ws/tournaments/dashboard/`);

        socket.addEventListener('message', event => {
            let msg;
            try {
                msg = JSON.parse(event.data);
            } catch {
                return;
            }
            if (msg.type === 'invitation_status_update' && msg.invitation) {
                applyInvitationStatusUpdate(msg.invitation);
            } else if (msg.type === 'participant_added' && msg.participant) {
                applyParticipantAdded(msg.participant);
            }
        });

        socket.addEventListener('close', () => {
            setTimeout(initInvitationSocket, 3000);
        });
    }





    function openCompleteTournamentModal(uuid) {
        const overlay = document.getElementById('completeTournamentModalOverlay');
        const confirmBtn = document.getElementById('completeTournamentModalConfirm');
        if (confirmBtn) {
            confirmBtn.dataset.uuid = uuid;
            confirmBtn.disabled = false;
        }
        if (overlay) overlay.classList.add('is-open');
        if (window.lucide) lucide.createIcons();
    }

    function closeCompleteTournamentModal() {
        const overlay = document.getElementById('completeTournamentModalOverlay');
        if (overlay) overlay.classList.remove('is-open');
    }

    function submitCompleteTournament(uuid) {
        const confirmBtn = document.getElementById('completeTournamentModalConfirm');
        if (confirmBtn) confirmBtn.disabled = true;

        fetch(`/dashboard/tournaments/${uuid}/complete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: ''
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }

            const t = tournaments.find(x => x.tournament_uuid === uuid);
            if (t) t.status = data.status;

            const row = document.querySelector(`#tournamentsTableBody tr[data-uuid="${uuid}"]`);
            if (row && t) {
                const nameCell = row.querySelector('.trn-tournament-name-cell');
                if (nameCell) nameCell.innerHTML = tournamentNameCellHtml(t);

                const actionsCell = row.querySelector('.trn-tournament-actions-cell');
                if (actionsCell) actionsCell.innerHTML = tournamentActionsCell(t);
            }

            closeCompleteTournamentModal();
            showToast('Tournament marked as completed successfully.', 'success', 'Tournament Completed');
            if (window.lucide) lucide.createIcons();
        })
        .catch(() => showToast('Something went wrong. Please try again.', 'error'))
        .finally(() => {
            if (confirmBtn) confirmBtn.disabled = false;
        });
    }

    function wireTournamentActions() {
        const tBody = document.getElementById('tournamentsTableBody');
        if (tBody) {
            tBody.addEventListener('click', e => {
                const btn = e.target.closest('[data-trn-action]');
                if (!btn) return;
                const uuid = btn.dataset.uuid;
                const action = btn.dataset.trnAction;
                if (action === 'view') {
                    window.location.href = `/dashboard/tournaments/${uuid}/view/`;
                } else if (action === 'complete') {
                    openCompleteTournamentModal(uuid);
                }
            });
        }

        const overlay = document.getElementById('completeTournamentModalOverlay');
        const closeBtn = document.getElementById('completeTournamentModalClose');
        const cancelBtn = document.getElementById('completeTournamentModalCancel');
        const confirmBtn = document.getElementById('completeTournamentModalConfirm');

        if (closeBtn) closeBtn.addEventListener('click', closeCompleteTournamentModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeCompleteTournamentModal);
        if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeCompleteTournamentModal(); });
        if (confirmBtn) confirmBtn.addEventListener('click', () => {
            if (confirmBtn.disabled) return;
            submitCompleteTournament(confirmBtn.dataset.uuid);
        });
    }

    function wireInvitationActions() {
        const iBody = document.getElementById('invitationsTableBody');
        if (iBody) {
            iBody.addEventListener('click', e => {
                const btn = e.target.closest('[data-inv-action]');
                if (!btn) return;
                const uuid = btn.dataset.uuid;
                const action = btn.dataset.invAction;
                if (action === 'view') openInvitationModal(uuid);
                else submitInvitationAction(uuid, action);
            });
        }

        const overlay = document.getElementById('invitationModalOverlay');
        const closeBtn = document.getElementById('invitationModalClose');
        const acceptBtn = document.getElementById('invitationModalAccept');
        const rejectBtn = document.getElementById('invitationModalReject');

        if (closeBtn) closeBtn.addEventListener('click', closeInvitationModal);
        if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeInvitationModal(); });
        if (acceptBtn) acceptBtn.addEventListener('click', () => { if (!acceptBtn.disabled) submitInvitationAction(acceptBtn.dataset.uuid, 'accept'); });
        if (rejectBtn) rejectBtn.addEventListener('click', () => { if (!rejectBtn.disabled) submitInvitationAction(rejectBtn.dataset.uuid, 'reject'); });
    }

    function playersCell(p, idx) {
        if (p.participation_type !== 'TEAM') return '—';
        const count = p.players_count ?? (p.players ? p.players.length : 0);
        return `
            <button type="button" class="trn-players-btn" data-players-idx="${idx}" title="View players">
                <i data-lucide="eye"></i> ${count}
            </button>`;
    }


    function renderParticipantsTable() {

    const pBody =
        document.getElementById('participantsTableBody');

    if (!pBody) return;

    pBody.innerHTML = '';

    const currentPage = tablePages.participants;

    const start =
        (currentPage - 1) * ROWS_PER_PAGE;

    const end =
        start + ROWS_PER_PAGE;

    const pageData =
        participants.slice(start, end);

    pageData.forEach((p, localIndex) => {

        const originalIndex = start + localIndex;

        const isTeam =
            p.participation_type === 'TEAM';

        const name =
            isTeam
                ? (
                    p.team_name &&
                    p.team_name !== '—'
                        ? p.team_name
                        : p.participant_name
                )
                : p.participant_name;

        const participantType =
            p.participation_type === 'TEAM'
                ? 'Team'
                : p.participation_type === 'INDIVIDUAL'
                    ? 'Individual'
                    : '—';

        const row =
            document.createElement('tr');

        row.innerHTML = `
            <td>
                ${p.tournament}
            </td>

            <td>
                ${participantType}
            </td>

            <td class="trn-cell-primary">
                ${name}
            </td>

            <td>
                ${p.college_name}
            </td>

            <td>
                ${p.coach_name}
            </td>

            <td>
                ${playersCell(p, originalIndex)}
            </td>

            <td>
                ${formatDate(p.registered_at)}
            </td>
        `;

        pBody.appendChild(row);
    });

    const countEl =
        document.getElementById('participantsCount');

    if (countEl) {

        const totalPages = Math.ceil(
            participants.length / ROWS_PER_PAGE
        );

        countEl.textContent =
            totalPages > 1
                ? `Showing page ${currentPage} of ${totalPages}`
                : `Showing ${participants.length} participants`;
    }

    renderPagination(
        'participantsPagination',
        currentPage,
        participants.length,
        page => {

            tablePages.participants = page;

            renderParticipantsTable();

            if (window.lucide) {
                lucide.createIcons();
            }
        }
    );

    if (window.lucide) {
        lucide.createIcons();
    }
}

    function openPlayersModal(idx) {
        const overlay = document.getElementById('playersModalOverlay');
        const body = document.getElementById('playersModalBody');
        const title = document.getElementById('playersModalTitle');
        if (!overlay || !body) return;

        const p = participants[idx];
        if (!p) return;

        const displayName = (p.team_name && p.team_name !== '—') ? p.team_name : p.participant_name;
        title.textContent = `Players — ${displayName}`;

        const players = p.players || [];
        body.innerHTML = players.length
            ? players.map(pl => {
                
                    const pname = typeof pl === 'string'
                   ? pl
                    : (pl && (pl.name || pl.player_name)) || '—';
                 return `<div class="trn-modal-player"><span class="trn-modal-player__name">${pname}</span></div>`;
                return `<div class="trn-modal-player"><span class="trn-modal-player__name">${pname}</span></div>`;
            }).join('')
            : `<div class="trn-insight-empty">No player details submitted.</div>`;

        overlay.classList.add('is-open');
        if (window.lucide) lucide.createIcons();
    }

    function closePlayersModal() {
        const overlay = document.getElementById('playersModalOverlay');
        if (overlay) overlay.classList.remove('is-open');
    }

    function wireParticipantsActions() {
        const pBody = document.getElementById('participantsTableBody');
        if (pBody) {
            pBody.addEventListener('click', e => {
                const btn = e.target.closest('[data-players-idx]');
                if (!btn) return;
                openPlayersModal(parseInt(btn.dataset.playersIdx, 10));
            });
        }

        const overlay = document.getElementById('playersModalOverlay');
        const closeBtn = document.getElementById('playersModalClose');
        if (closeBtn) closeBtn.addEventListener('click', closePlayersModal);
        if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closePlayersModal(); });
    }

   

    function insightItem(icon, title, meta) {
        return `
            <div class="trn-insight-item">
                <span class="trn-insight-item__icon"><i data-lucide="${icon}"></i></span>
                <div class="trn-insight-item__body">
                    <div class="trn-insight-item__title">${title}</div>
                    <div class="trn-insight-item__meta">${meta}</div>
                </div>
            </div>`;
    }

    function renderInsights() {
        const upcomingEl = document.getElementById('insightUpcoming');
        if (upcomingEl) {
            upcomingEl.innerHTML = tournaments
                .filter(t => ['CREATED', 'INVITATION_SENT', 'REGISTRATION_OPEN', 'FIXTURES_READY'].includes(t.status))
                .slice(0, 4)
                .map(t => insightItem('calendar', t.tournament_name, formatDate(t.start_date)))
                .join('') || `<div class="trn-insight-empty">No upcoming tournaments</div>`;
        }

        const deadlinesEl = document.getElementById('insightDeadlines');
      
        if (deadlinesEl) {

    const today = new Date();
    const todayString =
        today.getFullYear() +
        '-' +
        String(today.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(today.getDate()).padStart(2, '0'); 

    deadlinesEl.innerHTML = tournaments
        .filter(t =>
            t.registration_deadline &&
            t.registration_deadline > todayString
        )
        .sort((a, b) =>
            a.registration_deadline.localeCompare(b.registration_deadline)
        )
        .slice(0, 5)
        .map(t =>
            insightItem(
                'alarm-clock',
                t.tournament_name,
                `Closes ${formatDate(t.registration_deadline)}`
            )
        )
        .join('') ||
        `<div class="trn-insight-empty">No upcoming registration deadlines</div>`;
}

        const pendingEl = document.getElementById('insightPending');
        if (pendingEl) {
            pendingEl.innerHTML = invitations
                .filter(inv => inv.application_status === 'APPLIED')
                .map(inv => insightItem('user-round-check', inv.contact_person, `${inv.tournament} · ${inv.college_name}`))
                .join('') || `<div class="trn-insight-empty">No pending approvals</div>`;
        }

        const completedEl = document.getElementById('insightCompleted');
        if (completedEl) {
            completedEl.innerHTML = tournaments
                .filter(t => t.status === 'COMPLETED')
                .map(t => insightItem('flag-triangle-right', t.tournament_name, formatDate(t.end_date)))
                .join('') || `<div class="trn-insight-empty">No recently completed tournaments</div>`;
        }

        const winnersEl = document.getElementById('insightWinners');
        if (winnersEl) {
            winnersEl.innerHTML = participants
                .filter(p => p.result === 'WINNER')
                .map(p => insightItem('crown', p.participant_name, p.tournament))
                .join('') || `<div class="trn-insight-empty">No winners recorded yet</div>`;
        }

        const notificationsEl = document.getElementById('insightNotifications');
        if (notificationsEl) {
            notificationsEl.innerHTML = `
                <div class="trn-notify-item trn-notify-item--warn"><i data-lucide="triangle-alert"></i><span>5 tournaments have registration closing within 48 hours.</span></div>
                <div class="trn-notify-item trn-notify-item--danger"><i data-lucide="circle-x"></i><span>1 invitation was rejected and needs follow-up.</span></div>
                <div class="trn-notify-item trn-notify-item--info"><i data-lucide="info"></i><span>Fixtures are ready for review on 1 tournament.</span></div>
            `;
        }
    }

    

    function renderCharts() {
        if (!window.Chart) return;

        Chart.defaults.font = { family: "'Encode Sans', sans-serif", size: 11 };
        Chart.defaults.color = '#6c757d';

        const statusEl = document.getElementById('statusDistributionChart');
        if (statusEl) {
            new Chart(statusEl, {
                type: 'doughnut',
                data: {
                    labels: DASHBOARD_DATA.charts.status_distribution.labels,
                    datasets: [{
                        data: DASHBOARD_DATA.charts.status_distribution.data,
                        backgroundColor: ['#198754', '#c5050c', '#0d6efd', '#4338ca', '#f4b400', '#6c757d'],
                        borderWidth: 0,
                        hoverOffset: 8
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 12 } } }
                }
            });
        }

        const typeEl = document.getElementById('typeDistributionChart');
        if (typeEl) {
            new Chart(typeEl, {
                type: 'polarArea',
                data: {
                    // labels: ['Inter College', 'Intra College', 'Inter Department', 'Intra Department', 'Open'],
                    labels: DASHBOARD_DATA.charts.type_distribution.labels,
                    datasets: [{
                        // data: [26, 18, 15, 12, 15],
                        data: DASHBOARD_DATA.charts.type_distribution.data,
                        backgroundColor: ['rgba(197,5,12,.75)', 'rgba(13,110,253,.75)', 'rgba(25,135,84,.75)', 'rgba(244,180,0,.75)', 'rgba(111,66,193,.75)']
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 12 } } },
                    scales: { r: { ticks: { display: false }, grid: { color: '#e9ecef' } } }
                }
            });
        }

        const monthlyEl = document.getElementById('monthlyCreationChart');
        if (monthlyEl) {
            new Chart(monthlyEl, {
                type: 'bar',
                data: {
                    labels: DASHBOARD_DATA.charts.monthly_creation.labels,
                    datasets: [{
                        label: 'Tournaments Created',
                        data: DASHBOARD_DATA.charts.monthly_creation.data,
                        backgroundColor: '#c5050c',
                        borderRadius: 6,
                        maxBarThickness: 28
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, grid: { color: '#e9ecef' } }
                    }
                }
            });
        }

        const invEl = document.getElementById('invitationStatusChart');
        if (invEl) {
            new Chart(invEl, {
                type: 'pie',
                data: {
                    labels: DASHBOARD_DATA.charts.invitation_status.labels,
                    datasets: [{
                        data: DASHBOARD_DATA.charts.invitation_status.data,
                        backgroundColor: ['#6c757d', '#f4b400', '#0aa2a2', '#c5050c'],
                        borderWidth: 0
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 12 } } }
                }
            });
        }

        const growthEl = document.getElementById('participantGrowthChart');
        if (growthEl) {
            new Chart(growthEl, {
                type: 'line',
                data: {
                    labels: DASHBOARD_DATA.charts.participant_growth.labels,
                    datasets: [{
                        label: 'Registered Participants',
                        data: DASHBOARD_DATA.charts.participant_growth.data,
                        borderColor: '#c5050c',
                        backgroundColor: 'rgba(197,5,12,.12)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#c5050c'
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, grid: { color: '#e9ecef' } }
                    }
                }
            });
        }
    }

   

    function init() {
        animateCounters();
        renderTournamentsTable();
        renderInvitationsTable();
        renderParticipantsTable();
        renderInsights();
        renderCharts();
        wireInvitationActions();
        wireParticipantsActions();
        wireTournamentActions();
        initInvitationSocket(); 

        if (window.lucide) lucide.createIcons();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();