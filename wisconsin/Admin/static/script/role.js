(() => {
    'use strict';

    if (window.AOS) {
        AOS.init({
            once: true,
            duration: 500,
            easing: 'ease-out-cubic',
            offset: 40,
            disable: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        });
    }

    const configEl = document.getElementById('roleConfig');
    const CSRF_TOKEN          = configEl ? configEl.dataset.csrf : '';
    const ASSIGNMENTS_URL     = configEl ? configEl.dataset.assignmentsUrl : '';
    const CREATE_ROLE_URL     = configEl ? configEl.dataset.createRoleUrl : '';
    const UNASSIGN_URL_TPL    = configEl ? configEl.dataset.unassignUrlTemplate : '';
    const EDIT_URL_TPL        = configEl ? configEl.dataset.editUrlTemplate : '';

    const buildUnassignUrl = id => UNASSIGN_URL_TPL.replace('999999', id);
    // const buildEditUrl     = id => EDIT_URL_TPL.replace('999999', id);
    const buildEditUrl = uuid =>
    EDIT_URL_TPL.replace('__UUID__', uuid);
 
    const AVATAR_COLORS = [
        ['#c5050c', '#fff'],
        ['#2563eb', '#fff'],
        ['#7c3aed', '#fff'],
        ['#059669', '#fff'],
        ['#d97706', '#fff'],
        ['#0891b2', '#fff'],
        ['#be185d', '#fff'],
    ];

    const ROWS_PER_PAGE = 10;

    let currentPage     = 1;
    let totalPagesCount = 1;
    let filterRole      = '';
    let searchQuery      = '';
    let pendingDeleteId   = null;
    let pendingDeleteRole = null;
    let pendingDeleteName = null;
    let searchDebounce    = null;


    const tableBody      = document.getElementById('rolesTableBody');
    const mobileCards    = document.getElementById('rolesMobileCards');
    const tableCount     = document.getElementById('tableCount');
    const prevBtn        = document.getElementById('prevPage');
    const nextBtn        = document.getElementById('nextPage');
    const pageNumbers    = document.getElementById('pageNumbers');
    const roleFilter     = document.getElementById('roleFilter');
    const tableSearch    = document.getElementById('tableSearch');

    const roleModal      = document.getElementById('roleModal');
    const openAddRole    = document.getElementById('openAddRoleModal');
    const closeRole      = document.getElementById('closeRoleModal');
    const cancelRole     = document.getElementById('cancelRoleModal');
    const saveRoleBtn    = document.getElementById('saveRole');
    const roleModalTitle = document.getElementById('roleModalTitle');
    const roleNameInput  = document.getElementById('roleName');
    const roleDescInput  = document.getElementById('roleDesc');
    const roleUserTypeInput = document.getElementById('roleUserType');
    const roleNameHint   = roleModal ? roleModal.querySelector('.field-hint') : null;
    const roleNameHintDefault = roleNameHint ? roleNameHint.textContent : '';

    const deleteModal    = document.getElementById('deleteModal');
    const closeDeleteBtn = document.getElementById('closeDeleteModal');
    const cancelDelete   = document.getElementById('cancelDeleteModal');
    const confirmDelete  = document.getElementById('confirmDelete');

    const toastEl        = document.getElementById('roleToast');
    const toastMsg       = document.getElementById('toastMsg');

    const rolePillsWrap     = document.getElementById('rolePills');
    const totalRolesValueEl = document.getElementById('totalRolesValue');
    const unassignedValueEl = document.getElementById('unassignedUsersValue');


    function getInitials(name) {
        const parts = name.trim().split(/\s+/);
        if (parts.length === 1) return parts[0][0].toUpperCase();
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }

    function avatarColor(id) {
        return AVATAR_COLORS[id % AVATAR_COLORS.length];
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr + 'T00:00:00');
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function roleBadgeHTML(role, color) {
        return `<span class="role-badge role-badge--${color}">
                    <span class="role-badge__dot"></span>${role}
                </span>`;
    }

    function statusBadgeHTML(status) {
        const label = status.charAt(0).toUpperCase() + status.slice(1);
        return `<span class="status-badge status-badge--${status}">
                    <span class="status-dot"></span>${label}
                </span>`;
    }

    function avatarHTML(row, size = 34) {
        const [bg, fg] = avatarColor(row.id);
        return `<div class="user-avatar user-avatar--initials"
                     style="width:${size}px;height:${size}px;background:${bg};color:${fg};font-size:${Math.round(size*0.3)}px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;"
                     aria-label="${row.name}">${getInitials(row.name)}</div>`;
    }



    function fetchAssignments(page = 1) {
        if (!ASSIGNMENTS_URL) return;

        const params = new URLSearchParams({ page: String(page), page_size: String(ROWS_PER_PAGE) });
        if (filterRole)  params.set('role', filterRole);
        if (searchQuery) params.set('search', searchQuery);

        fetch(`${ASSIGNMENTS_URL}?${params.toString()}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(r => r.json())
            .then(data => renderTable(data))
            .catch(err => {
                console.error('Failed to load role assignments', err);
                if (tableBody) {
                    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--gray-400);font-size:.85rem;">Couldn't load users. Please refresh.</td></tr>`;
                }
            });
    }

    function applyFilters() {
        fetchAssignments(1);
    }

    if (roleFilter) {
        roleFilter.addEventListener('change', () => {
            filterRole = roleFilter.value;
            applyFilters();
        });
    }
    if (tableSearch) {
        tableSearch.addEventListener('input', () => {
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(() => {
                searchQuery = tableSearch.value.toLowerCase().trim();
                applyFilters();
            }, 300);
        });
    }


    function renderTable(data) {
        const results   = data.results || [];
        const total     = data.total || 0;
        const page      = data.page || 1;
        const pageSize  = data.page_size || ROWS_PER_PAGE;
        currentPage     = page;
        totalPagesCount = data.total_pages || 1;

        const start = (page - 1) * pageSize;

        if (tableCount) {
            tableCount.textContent = total === 0
                ? 'No users found'
                : `Showing ${start + 1}–${Math.min(start + pageSize, total)} of ${total} users`;
        }

        renderTableRows(results, start);
        renderMobileCards(results, start);
        renderPagination(page, totalPagesCount);
        lucide.createIcons();
    }

    function renderTableRows(slice, start) {
        if (!tableBody) return;
        if (slice.length === 0) {
            tableBody.innerHTML = `<tr class="empty-row">
                <td colspan="7">
                    <svg class="empty-icon" data-lucide="inbox"></svg>
                    <p style="margin:0;font-size:.85rem;color:var(--gray-400)">No users match your filters.</p>
                </td>
            </tr>`;
            return;
        }

        tableBody.innerHTML = slice.map((row, idx) => `
            <tr data-id="${row.id}">
                <td class="col-no" style="color:var(--gray-400);font-size:.8rem;">${start + idx + 1}</td>
                <td class="col-user">
                    <div class="user-cell">
                        ${avatarHTML(row)}
                        <div class="user-info">
                            <span class="user-info__name">${row.name}</span>
                            <span class="user-info__email">${row.email}</span>
                        </div>
                    </div>
                </td>
                <td class="col-uid" style="font-size:.8rem;color:var(--gray-500);font-weight:500;">${row.uid}</td>
                <td class="col-role">${roleBadgeHTML(row.role, row.role_color)}</td>
                <td class="col-status">${statusBadgeHTML(row.status)}</td>
                <td class="col-assigned" style="font-size:.8rem;color:var(--gray-500);">${formatDate(row.assigned)}</td>
                
            </tr>
        `).join('');

        // tableBody.querySelectorAll('.action-btn--edit').forEach(btn => {
        //     btn.addEventListener('click', () => {
        //         window.location.href = buildEditUrl(+btn.dataset.uuid);
        //     });
        // });
        tableBody.querySelectorAll('.action-btn--edit').forEach(btn => {
            btn.addEventListener('click', () => {
                window.location.href = buildEditUrl(btn.dataset.id);
            });
        });
                tableBody.querySelectorAll('.action-btn--delete').forEach(btn => {
            btn.addEventListener('click', () => {
                const id  = +btn.dataset.id;
                const row = slice.find(r => r.id === id);
                if (row) openDeleteModal(row);
            });
        });
    }

    function renderMobileCards(slice, start) {
        if (!mobileCards) return;
        if (slice.length === 0) {
            mobileCards.innerHTML = `<div style="padding:32px 16px;text-align:center;color:var(--gray-400);font-size:.85rem;">No users match your filters.</div>`;
            return;
        }

        mobileCards.innerHTML = slice.map((row, idx) => `
            <div class="role-card" data-id="${row.id}">
                <div class="role-card__top">
                    <span style="font-size:.72rem;color:var(--gray-400);min-width:22px;">${start + idx + 1}</span>
                    ${avatarHTML(row, 38)}
                    <div class="role-card__meta">
                        <div class="role-card__name">${row.name}</div>
                        <div class="role-card__email">${row.email}</div>
                    </div>
                   
                </div>
                <div class="role-card__bottom">
                    <span class="role-card__uid">${row.uid}</span>
                    ${roleBadgeHTML(row.role, row.role_color)}
                    ${statusBadgeHTML(row.status)}
                    <span class="role-card__date">${formatDate(row.assigned)}</span>
                </div>
            </div>
        `).join('');

        mobileCards.querySelectorAll('.action-btn--edit').forEach(btn => {
            btn.addEventListener('click', () => {
                window.location.href = buildEditUrl(+btn.dataset.uuid);
            });
        });
        // mobileCards.querySelectorAll('.action-btn--delete').forEach(btn => {
        //     btn.addEventListener('click', () => {
        //         const id  = +btn.dataset.id;
        //         const row = slice.find(r => r.id === id);
        //         if (row) openDeleteModal(row);
        //     });
        // });
        mobileCards.querySelectorAll('.action-btn--edit').forEach(btn => {
            btn.addEventListener('click', () => {
                window.location.href = buildEditUrl(btn.dataset.id);
            });
        });
    }


    function renderPagination(page, totalPages) {
        if (!pageNumbers) return;

        if (prevBtn) prevBtn.disabled = page === 1;
        if (nextBtn) nextBtn.disabled = page === totalPages;

        const pages = [];
        const delta = 2;
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= page - delta && i <= page + delta)) {
                pages.push(i);
            }
        }

        const withEllipsis = [];
        let prev = null;
        for (const p of pages) {
            if (prev !== null && p - prev > 1) {
                withEllipsis.push('…');
            }
            withEllipsis.push(p);
            prev = p;
        }

        pageNumbers.innerHTML = withEllipsis.map(p =>
            p === '…'
                ? `<span style="display:flex;align-items:center;padding:0 4px;color:var(--gray-400);font-size:.8rem;">…</span>`
                : `<button class="page-num ${p === page ? 'active' : ''}" data-page="${p}" aria-label="Page ${p}" ${p === page ? 'aria-current="page"' : ''}>${p}</button>`
        ).join('');

        pageNumbers.querySelectorAll('.page-num').forEach(btn => {
            btn.addEventListener('click', () => {
                fetchAssignments(+btn.dataset.page);
                scrollToTable();
            });
        });
    }

    if (prevBtn) prevBtn.addEventListener('click', () => { fetchAssignments(currentPage - 1); scrollToTable(); });
    if (nextBtn) nextBtn.addEventListener('click', () => { fetchAssignments(currentPage + 1); scrollToTable(); });

    function scrollToTable() {
        const section = document.querySelector('.roles-table-section');
        if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }



    function openAddModal() {
        roleModalTitle.textContent = 'Add New Role';
        roleNameInput.value = '';
        roleDescInput.value = '';
        if (roleUserTypeInput) roleUserTypeInput.value = '';
        clearRoleNameError();
        showModal(roleModal);
    }

    function clearRoleNameError() {
        roleNameInput.style.borderColor = '';
        if (roleNameHint) {
            roleNameHint.textContent = roleNameHintDefault;
            roleNameHint.style.color = '';
        }
    }

    function showRoleNameError(msg) {
        roleNameInput.style.borderColor = 'var(--red-500)';
        roleNameInput.focus();
        if (roleNameHint) {
            roleNameHint.textContent = msg;
            roleNameHint.style.color = 'var(--red-600)';
        }
    }

    if (openAddRole) openAddRole.addEventListener('click', openAddModal);
    if (closeRole)   closeRole.addEventListener('click',   () => hideModal(roleModal));
    if (cancelRole)  cancelRole.addEventListener('click',  () => hideModal(roleModal));














    if (saveRoleBtn) {
    saveRoleBtn.addEventListener('click', () => {
        const name = roleNameInput.value.trim();
        const description = roleDescInput.value.trim();
        const userType = roleUserTypeInput ? roleUserTypeInput.value.trim() : '';

        if (!name) {
            showRoleNameError('Role name is required.');
            return;
        }

        clearRoleNameError();
        saveRoleBtn.disabled = true;

        fetch(CREATE_ROLE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                role_name: name,
                description,
                user_type: userType
            }).toString(),
        })
        .then(r => r.json().then(data => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
            saveRoleBtn.disabled = false;


            if (!ok || !data.ok) {
                showRoleNameError('Could not save this role.');
                return;
            }

            addRoleToUI(data.role);
            hideModal(roleModal);
            showToast(
                `Role "${data.role.name}" created successfully.`,
                'success'
            );


        })
        .catch(() => {
            saveRoleBtn.disabled = false;
            showRoleNameError('Something went wrong.');
        });
    });
}

    function addRoleToUI(role) {
        const placeholder = document.getElementById('noRolePill');
        if (placeholder) placeholder.remove();

        if (rolePillsWrap) {
            const pill = document.createElement('div');
            pill.className = 'role-pill';
            pill.dataset.roleId = role.id;
            pill.innerHTML = `
                <span class="role-pill__dot role-pill__dot--gray"></span>
                <span class="role-pill__name">${role.name}</span>
                <span class="role-pill__badge">${role.count}</span>
            `;
            rolePillsWrap.appendChild(pill);
            lucide.createIcons();
        }

        if (roleFilter) {
            const opt = document.createElement('option');
            opt.value = role.id;
            opt.textContent = role.name;
            roleFilter.appendChild(opt);
        }

        if (totalRolesValueEl) {
            const current = parseInt(totalRolesValueEl.textContent.replace(/,/g, ''), 10) || 0;
            totalRolesValueEl.textContent = current + 1;
        }
    }



    function openDeleteModal(row) {
        pendingDeleteId   = row.id;
        pendingDeleteRole = row.role_id;
        pendingDeleteName = row.name;
        showModal(deleteModal);
    }

    if (closeDeleteBtn) closeDeleteBtn.addEventListener('click', () => hideModal(deleteModal));
    if (cancelDelete)   cancelDelete.addEventListener('click',   () => hideModal(deleteModal));

    if (confirmDelete) {
        confirmDelete.addEventListener('click', () => {
            if (!pendingDeleteId) return;

            confirmDelete.disabled = true;

            fetch(buildUnassignUrl(pendingDeleteId), {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
            })
                .then(r => r.json())
                .then(data => {
                    confirmDelete.disabled = false;
                    hideModal(deleteModal);

                    if (!data.ok) {
                        showToast('Could not remove this role assignment.');
                        return;
                    }

                    if (pendingDeleteRole && rolePillsWrap) {
                        const pill = rolePillsWrap.querySelector(`[data-role-id="${pendingDeleteRole}"] .role-pill__badge`);
                        if (pill) pill.textContent = Math.max(0, (parseInt(pill.textContent, 10) || 1) - 1);
                    }
                    if (unassignedValueEl) {
                        const current = parseInt(unassignedValueEl.textContent.replace(/,/g, ''), 10) || 0;
                        unassignedValueEl.textContent = current + 1;
                    }

                    showToast(`Role assignment for "${pendingDeleteName}" removed.`);
                    fetchAssignments(currentPage);
                    pendingDeleteId = null;
                    pendingDeleteRole = null;
                    pendingDeleteName = null;
                })
                .catch(() => {
                    confirmDelete.disabled = false;
                    hideModal(deleteModal);
                    showToast('Could not remove this role assignment.');
                });
        });
    }


    function showModal(modal) {
        document.body.classList.add('modal-open');
        modal.hidden = false;
        // setTimeout(() => {
        //     const first = modal.querySelector('input, textarea, select, button:not(.roles-modal__close)');
        //     if (first) first.focus();
        // }, 50);
    }

    function hideModal(modal) {
        document.body.classList.remove('modal-open');
        modal.hidden = true;
    }

    [roleModal, deleteModal].forEach(modal => {
        if (!modal) return;
        modal.addEventListener('click', e => {
            if (e.target === modal) hideModal(modal);
        });
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            if (roleModal   && !roleModal.hidden)   hideModal(roleModal);
            if (deleteModal && !deleteModal.hidden) hideModal(deleteModal);
        }
    });


    let toastTimer = null;

    const container = document.getElementById('global-toast-container');
    container.appendChild(roleToast);

    const toastIconWrap = document.getElementById('toastIconWrap');
    const toastIcon     = document.getElementById('toastIcon');
    const toastTitle    = document.getElementById('toastTitle');
    const toastClose    = document.getElementById('toastClose');

    if (toastClose) {
        toastClose.addEventListener('click', () => {
            toastEl.classList.add('hiding');
            setTimeout(() => { toastEl.hidden = true; toastEl.classList.remove('hiding'); }, 260);
            clearTimeout(toastTimer);
        });
    }

    function showToast(msg, type = 'error', title = null, duration = 3000) {
        if (!toastEl) return;

        const isError  = type === 'error';
        const autoTitle = title || (isError ? 'Error' : 'Success');

        if (toastTitle)    toastTitle.textContent = autoTitle;
        if (toastMsg)      toastMsg.textContent   = msg;

        if (toastIcon)     toastIcon.setAttribute('data-lucide', isError ? 'x-circle' : 'check-circle');
       

        if (toastIconWrap) {
            toastIconWrap.innerHTML = isError
                ? '<i data-lucide="x-circle"></i>'
                : '<i data-lucide="check-circle"></i>';

            lucide.createIcons();
        }

        toastIconWrap.className =
                'role-toast__icon-wrap' +
                (isError ? '' : ' role-toast__icon-wrap--success');

        toastEl.classList.remove('hiding');
        toastEl.hidden = false;
        lucide.createIcons();

        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toastEl.classList.add('hiding');
            setTimeout(() => { toastEl.hidden = true; toastEl.classList.remove('hiding'); }, 260);
        }, duration);
    }


    fetchAssignments(1);


    document.addEventListener('DOMContentLoaded', function () {

        const userType = document.getElementById('id_user_type');
        const roleSelect = document.getElementById('id_role');

        const rolesData = JSON.parse(
            document.getElementById('allRolesData').textContent
        );

        userType.addEventListener('change', function () {

            const selectedType = this.value;

            roleSelect.innerHTML =
                '<option value="">Select Role</option>';

            const filteredRoles = rolesData.filter(
                role => role.type === selectedType
            );

            filteredRoles.forEach(role => {
                const option = document.createElement('option');
                option.value = role.id;
                option.textContent = role.name;
                roleSelect.appendChild(option);
            });
        });

    });



    
const ROLE_DETAILS_URL_TPL   = configEl ? configEl.dataset.roleDetailsUrlTemplate   : '';
const ROLE_AVAILABLE_URL_TPL = configEl ? configEl.dataset.roleAvailableUrlTemplate : '';
const ROLE_ASSIGN_URL_TPL    = configEl ? configEl.dataset.roleAssignUrlTemplate    : '';
const ROLE_REVOKE_URL_TPL    = configEl ? configEl.dataset.roleRevokeUrlTemplate    : '';
const ROLE_UPDATE_URL_TPL    = configEl ? configEl.dataset.roleUpdateUrlTemplate    : '';
const ROLE_CONVERT_URL_TPL   = configEl ? configEl.dataset.roleConvertUrlTemplate   : '';
 
const buildRoleDetailsUrl   = id => ROLE_DETAILS_URL_TPL.replace('999999',   id);
const buildAvailableUrl     = id => ROLE_AVAILABLE_URL_TPL.replace('999999', id);
const buildAssignUrl        = id => ROLE_ASSIGN_URL_TPL.replace('999999',    id);
const buildRevokeUrl        = id => ROLE_REVOKE_URL_TPL.replace('999999',    id);
const buildRoleUpdateUrl    = id => ROLE_UPDATE_URL_TPL.replace('999999',    id);
const buildRoleConvertUrl   = id => ROLE_CONVERT_URL_TPL.replace('999999',   id);
 
const roleDetailsModal    = document.getElementById('roleDetailsModal');
const closeRoleDetails    = document.getElementById('closeRoleDetailsModal');
const rdModalTitle        = document.getElementById('rdModalTitle');
const rdUserCount         = document.getElementById('rdUserCount');
const rdDescription       = document.getElementById('rdDescription');
const rdTabAssigned       = document.getElementById('rdTabAssigned');
const rdTabAdd            = document.getElementById('rdTabAdd');
const rdTabSettings       = document.getElementById('rdTabSettings');
const rdPanelAssigned     = document.getElementById('rdPanelAssigned');
const rdPanelAdd          = document.getElementById('rdPanelAdd');
const rdPanelSettings     = document.getElementById('rdPanelSettings');
const rsRoleNameInput     = document.getElementById('rsRoleNameInput');
const rsRoleNameHint      = document.getElementById('rsRoleNameHint');
const rsRoleNameHintDefault = rsRoleNameHint ? rsRoleNameHint.textContent : '';
const rsUpdateNameBtn     = document.getElementById('rsUpdateNameBtn');
const rsCurrentRoleInput  = document.getElementById('rsCurrentRoleInput');
const rsTargetRoleSelect  = document.getElementById('rsTargetRoleSelect');
const rsConvertBtn        = document.getElementById('rsConvertBtn');
const convertUsersConfirmModal  = document.getElementById('convertUsersConfirmModal');
const closeConvertUsersModal    = document.getElementById('closeConvertUsersModal');
const cancelConvertUsersModal   = document.getElementById('cancelConvertUsersModal');
const confirmConvertUsersBtn    = document.getElementById('confirmConvertUsersBtn');
const convertUsersConfirmText   = document.getElementById('convertUsersConfirmText');
const rdAssignedSearch    = document.getElementById('rdAssignedSearch');
const rdAssignedList      = document.getElementById('rdAssignedList');
const rdAvailableSearch   = document.getElementById('rdAvailableSearch');
const rdAutocomplete      = document.getElementById('rdAutocomplete');
const rdChips             = document.getElementById('rdChips');
const rdAssignBtn         = document.getElementById('rdAssignBtn');
const rdAddHint           = document.getElementById('rdAddHint');
const revokeConfirmModal  = document.getElementById('revokeConfirmModal');
const closeRevokeModal    = document.getElementById('closeRevokeModal');
const cancelRevokeModal   = document.getElementById('cancelRevokeModal');
const confirmRevokeBtn    = document.getElementById('confirmRevokeBtn');
const revokeConfirmText   = document.getElementById('revokeConfirmText');
 
let activeRoleId        = null;
let activeRoleName      = null;
let allAssignedUsers    = [];
let selectedUserIds     = [];
let pendingRevokeUserId = null;
let pendingRevokeUserName = null;
let pendingTargetRoleId = null;
let pendingTargetRoleName = null;
let rdSearchDebounce    = null;
let rdAvailDebounce     = null;
 
if (rolePillsWrap) {
    rolePillsWrap.addEventListener('click', e => {
        const pill = e.target.closest('.role-pill[data-role-id]');
        if (!pill) return;
 
        rolePillsWrap.querySelectorAll('.role-pill').forEach(p => p.classList.remove('role-pill--active'));
        pill.classList.add('role-pill--active');
 
        activeRoleId   = pill.dataset.roleId;
        activeRoleName = pill.querySelector('.role-pill__name').textContent.trim();
 
        openRoleDetailsModal(activeRoleId, activeRoleName);
    });
}
 
// function openRoleDetailsModal(roleId, roleName) {
//     selectedUserIds = [];
//     allAssignedUsers = [];
//     rdChips.innerHTML = '';
//     rdAssignBtn.disabled = true;
//     rdAddHint.textContent = 'Select users above to assign.';
//     rdAvailableSearch.value = '';
//     rdAutocomplete.hidden = true;
//     rdAssignedSearch.value = '';

function openRoleDetailsModal(roleId, roleName) {
    selectedUserIds = [];
    allAssignedUsers = [];
    if (rdChips) rdChips.innerHTML = '';
    if (rdAssignBtn) rdAssignBtn.disabled = true;
    if (rdAddHint) rdAddHint.textContent = 'Select users above to assign.';
    if (rdAvailableSearch) rdAvailableSearch.value = '';
    if (rdAutocomplete) rdAutocomplete.hidden = true;
    if (rdAssignedSearch) rdAssignedSearch.value = '';

    if (rsRoleNameInput) rsRoleNameInput.value = '';
    if (rsRoleNameHint)  { rsRoleNameHint.textContent = rsRoleNameHintDefault; rsRoleNameHint.style.color = ''; }
    if (rsCurrentRoleInput) rsCurrentRoleInput.value = roleName;
    if (rsTargetRoleSelect) rsTargetRoleSelect.innerHTML = '<option value="">Select target role</option>';
    if (rsConvertBtn) rsConvertBtn.disabled = true;

    switchRdTab('assigned');
 
    rdModalTitle.textContent = roleName;
    rdUserCount.textContent  = '…';
    rdDescription.textContent = '';
 
    showModal(roleDetailsModal);
    loadRoleDetails(roleId);
}
 
function loadRoleDetails(roleId) {
    rdAssignedList.innerHTML = `<div class="rd-empty"><div class="rd-spinner"></div></div>`;
 
    fetch(buildRoleDetailsUrl(roleId), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            rdUserCount.textContent  = data.total_users || 0;
            rdDescription.textContent = data.description || '';
            allAssignedUsers = data.users || [];
            renderAssignedUsers(allAssignedUsers);
            lucide.createIcons();
        })
        .catch(() => {
            rdAssignedList.innerHTML = `<div class="rd-empty"><i data-lucide="alert-circle"></i><span>Failed to load users.</span></div>`;
            lucide.createIcons();
        });
}
 
function renderAssignedUsers(users) {
    if (!rdAssignedList) return;
    if (users.length === 0) {
        rdAssignedList.innerHTML = `<div class="rd-empty">
            <i data-lucide="users"></i>
            <span>No users found under this role.</span>
        </div>`;
        lucide.createIcons();
        return;
    }
 
    rdAssignedList.innerHTML = users.map(u => {
        const [bg, fg] = avatarColor(u.id);
        const initials = getInitials(u.name || u.username || 'U');
        return `
          <div class="rd-user-row" data-id="${u.id}">
            <div style="width:34px;height:34px;border-radius:50%;background:${bg};color:${fg};
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:11px;flex-shrink:0;">${initials}</div>
            <div class="rd-user-row__info">
                <span class="rd-user-row__name">${u.name}</span>
                <span class="rd-user-row__email">${u.email || ''}</span>
            </div>
            <span class="rd-user-row__uid">${u.uid || '—'}</span>
            <span class="rd-user-row__status">${statusBadgeHTML(u.status || 'active')}</span>
            ${window.CAN_UPDATE_USERROLE ? `
            <button class="rd-revoke-btn" data-id="${u.id}" data-name="${u.name}"
                    aria-label="Revoke role from ${u.name}" title="Revoke role">
                <i data-lucide="user-minus"></i>
            </button>` : ''}
        </div>`;
    }).join('');
 
    rdAssignedList.querySelectorAll('.rd-revoke-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            pendingRevokeUserId   = +btn.dataset.id;
            pendingRevokeUserName = btn.dataset.name;
            if (revokeConfirmText) {
                revokeConfirmText.textContent =
                    `Remove this role from "${pendingRevokeUserName}"? They will become unassigned.`;
            }
            showModal(revokeConfirmModal);
        });
    });
    lucide.createIcons();
}
 
if (rdAssignedSearch) {
    rdAssignedSearch.addEventListener('input', () => {
        clearTimeout(rdSearchDebounce);
        rdSearchDebounce = setTimeout(() => {
            const q = rdAssignedSearch.value.toLowerCase().trim();
            if (!q) {
                renderAssignedUsers(allAssignedUsers);
                return;
            }
            const filtered = allAssignedUsers.filter(u =>
                (u.name  || '').toLowerCase().includes(q) ||
                (u.email || '').toLowerCase().includes(q) ||
                (u.uid   || '').toLowerCase().includes(q)
            );
            renderAssignedUsers(filtered);
        }, 250);
    });
}
 
function loadRoleSettings() {
    if (rsRoleNameInput) rsRoleNameInput.value = activeRoleName || '';
    if (rsRoleNameHint)  { rsRoleNameHint.textContent = rsRoleNameHintDefault; rsRoleNameHint.style.color = ''; }
    if (rsCurrentRoleInput) rsCurrentRoleInput.value = activeRoleName || '';
    populateTargetRoleSelect();
}

function populateTargetRoleSelect() {
    if (!rsTargetRoleSelect || !roleFilter) return;

    rsTargetRoleSelect.innerHTML = '<option value="">Select target role</option>';

    roleFilter.querySelectorAll('option').forEach(opt => {
        if (!opt.value) return;                 // skip "All Roles"
        if (String(opt.value) === String(activeRoleId)) return; // exclude current role

        const o = document.createElement('option');
        o.value = opt.value;
        o.textContent = opt.textContent;
        rsTargetRoleSelect.appendChild(o);
    });

    rsConvertBtn.disabled = true;
}

if (rsTargetRoleSelect) {
    rsTargetRoleSelect.addEventListener('change', () => {
        rsConvertBtn.disabled = !rsTargetRoleSelect.value;
    });
}

function showRsRoleNameError(msg) {
    if (!rsRoleNameHint) return;
    rsRoleNameHint.textContent = msg;
    rsRoleNameHint.style.color = 'var(--red-500)';
}

if (rsUpdateNameBtn) {
    rsUpdateNameBtn.addEventListener('click', () => {
        if (!activeRoleId) return;
        const newName = (rsRoleNameInput.value || '').trim();

        if (!newName) {
            showRsRoleNameError('Role name cannot be empty.');
            return;
        }

        rsUpdateNameBtn.disabled = true;
        const originalHTML = rsUpdateNameBtn.innerHTML;
        rsUpdateNameBtn.innerHTML = '<div class="rd-spinner" style="width:16px;height:16px;"></div>';

        fetch(buildRoleUpdateUrl(activeRoleId), {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ role_name: newName }),
        })
        .then(r => r.json().then(data => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
            rsUpdateNameBtn.disabled = false;
            rsUpdateNameBtn.innerHTML = originalHTML;
            lucide.createIcons();

            if (!ok || !data.ok) {
                showRsRoleNameError(data.error || 'Could not update role name.');
                return;
            }

            const oldName = activeRoleName;
            activeRoleName = data.role_name;

            // Update modal title + settings panel
            rdModalTitle.textContent = activeRoleName;
            rsRoleNameHint.textContent = rsRoleNameHintDefault;
            rsRoleNameHint.style.color = '';
            if (rsCurrentRoleInput) rsCurrentRoleInput.value = activeRoleName;

            // Update role pill name
            if (rolePillsWrap) {
                const nameEl = rolePillsWrap.querySelector(
                    `[data-role-id="${activeRoleId}"] .role-pill__name`
                );
                if (nameEl) nameEl.textContent = activeRoleName;
            }

            // Update role filter dropdown + target role dropdown options
            if (roleFilter) {
                const opt = roleFilter.querySelector(`option[value="${activeRoleId}"]`);
                if (opt) opt.textContent = activeRoleName;
            }
            populateTargetRoleSelect();

            // Refresh table data so role badges reflect the new name
            fetchAssignments(currentPage);

            showToast(`Role renamed to "${activeRoleName}".`, 'success');
        })
        .catch(() => {
            rsUpdateNameBtn.disabled = false;
            rsUpdateNameBtn.innerHTML = originalHTML;
            lucide.createIcons();
            showRsRoleNameError('Something went wrong. Please try again.');
        });
    });
}

if (rsConvertBtn) {
    rsConvertBtn.addEventListener('click', () => {
        if (!activeRoleId || !rsTargetRoleSelect.value) return;

        pendingTargetRoleId   = rsTargetRoleSelect.value;
        pendingTargetRoleName = rsTargetRoleSelect.options[rsTargetRoleSelect.selectedIndex].textContent;

        if (convertUsersConfirmText) {
            convertUsersConfirmText.textContent =
                `Are you sure you want to move all users from "${activeRoleName}" to "${pendingTargetRoleName}"?`;
        }
        showModal(convertUsersConfirmModal);
    });
}

if (closeConvertUsersModal)  closeConvertUsersModal.addEventListener('click',  () => hideModal(convertUsersConfirmModal));
if (cancelConvertUsersModal) cancelConvertUsersModal.addEventListener('click', () => hideModal(convertUsersConfirmModal));

if (confirmConvertUsersBtn) {
    confirmConvertUsersBtn.addEventListener('click', () => {
        if (!activeRoleId || !pendingTargetRoleId) return;
        confirmConvertUsersBtn.disabled = true;

        fetch(buildRoleConvertUrl(activeRoleId), {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ target_role_id: pendingTargetRoleId }),
        })
        .then(r => r.json())
        .then(data => {
            confirmConvertUsersBtn.disabled = false;
            hideModal(convertUsersConfirmModal);

            if (!data.ok) {
                showToast(data.error || 'Could not convert users.', 'error');
                return;
            }

            // Refresh role pill counts for both source and target roles
            updatePillCount(data.source_role.id, data.source_role.count);
            updatePillCount(data.target_role.id, data.target_role.count);

            // Refresh Assigned Users tab + total counter in modal header
            allAssignedUsers = [];
            renderAssignedUsers(allAssignedUsers);
            rdUserCount.textContent = data.source_role.count;

            // Refresh table data and stat cards
            fetchAssignments(currentPage);

            showToast(
                `${data.moved_count} user(s) moved from "${data.source_role.name}" to "${data.target_role.name}".`,
                'success'
            );

            rsTargetRoleSelect.value = '';
            rsConvertBtn.disabled = true;
            pendingTargetRoleId = null;
            pendingTargetRoleName = null;
        })
        .catch(() => {
            confirmConvertUsersBtn.disabled = false;
            hideModal(convertUsersConfirmModal);
            showToast('Could not convert users.', 'error');
        });
    });
}

function switchRdTab(tab) {
    const isAssigned = tab === 'assigned';
    const isAdd      = tab === 'add';
    const isSettings = tab === 'settings';

    rdTabAssigned.classList.toggle('rd-tab--active', isAssigned);
    // rdTabAdd.classList.toggle('rd-tab--active', isAdd);
    // rdTabSettings.classList.toggle('rd-tab--active', isSettings);
        if (rdTabAdd) rdTabAdd.classList.toggle('rd-tab--active', isAdd);
    if (rdTabSettings) rdTabSettings.classList.toggle('rd-tab--active', isSettings);

    rdTabAssigned.setAttribute('aria-selected', isAssigned ? 'true' : 'false');
    // rdTabAdd.setAttribute('aria-selected',      isAdd ? 'true' : 'false');
    // rdTabSettings.setAttribute('aria-selected', isSettings ? 'true' : 'false');
        if (rdTabAdd) rdTabAdd.setAttribute('aria-selected',      isAdd ? 'true' : 'false');
    if (rdTabSettings) rdTabSettings.setAttribute('aria-selected', isSettings ? 'true' : 'false');


    rdPanelAssigned.classList.toggle('rd-panel--hidden', !isAssigned);
    // rdPanelAdd.classList.toggle('rd-panel--hidden',       !isAdd);
    // rdPanelSettings.classList.toggle('rd-panel--hidden',  !isSettings);
    if (rdPanelAdd) rdPanelAdd.classList.toggle('rd-panel--hidden',       !isAdd);
    if (rdPanelSettings) rdPanelSettings.classList.toggle('rd-panel--hidden',  !isSettings);

    if (isSettings) loadRoleSettings();
}
 
if (rdTabAssigned) rdTabAssigned.addEventListener('click', () => switchRdTab('assigned'));
if (rdTabAdd)      rdTabAdd.addEventListener('click',      () => switchRdTab('add'));
if (rdTabSettings) rdTabSettings.addEventListener('click', () => switchRdTab('settings'));
 
if (rdAvailableSearch) {
    rdAvailableSearch.addEventListener('input', () => {
        clearTimeout(rdAvailDebounce);
        const q = rdAvailableSearch.value.trim();
        if (q.length < 1) { rdAutocomplete.hidden = true; return; }
 
        rdAvailDebounce = setTimeout(() => {
            const url = `${buildAvailableUrl(activeRoleId)}?search=${encodeURIComponent(q)}`;
            fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(r => r.json())
                .then(data => renderAutocomplete(data.users || []))
                .catch(() => { rdAutocomplete.hidden = true; });
        }, 280);
    });
 
    rdAvailableSearch.addEventListener('keydown', e => {
        if (e.key === 'Escape') rdAutocomplete.hidden = true;
    });
}
 
function renderAutocomplete(users) {
    if (!rdAutocomplete) return;
    const filtered = users.filter(u => !selectedUserIds.includes(u.id));
    if (filtered.length === 0) {
        rdAutocomplete.innerHTML = `<div class="rd-ac-item" style="color:var(--gray-400);cursor:default;">No users found.</div>`;
        rdAutocomplete.hidden = false;
        return;
    }
    rdAutocomplete.innerHTML = filtered.map(u => `
        <div class="rd-ac-item" tabindex="0" data-id="${u.id}" data-name="${u.name}">
            <div style="width:28px;height:28px;border-radius:50%;background:${avatarColor(u.id)[0]};
                        color:${avatarColor(u.id)[1]};display:flex;align-items:center;
                        justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;">
                ${getInitials(u.name || 'U')}
            </div>
            <div class="rd-ac-item__info">
                <span class="rd-ac-item__name">${u.name}</span>
                <span class="rd-ac-item__sub">${u.email || ''} ${u.uid ? '· ' + u.uid : ''}</span>
            </div>
        </div>
    `).join('');
    rdAutocomplete.hidden = false;
 
    rdAutocomplete.querySelectorAll('.rd-ac-item[data-id]').forEach(item => {
        item.addEventListener('click', () => selectUser(+item.dataset.id, item.dataset.name));
        item.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') selectUser(+item.dataset.id, item.dataset.name);
        });
    });
}
 
document.addEventListener('click', e => {
    if (rdAutocomplete && !rdAutocomplete.contains(e.target) && e.target !== rdAvailableSearch) {
        rdAutocomplete.hidden = true;
    }
});
 
function selectUser(id, name) {
    if (selectedUserIds.includes(id)) return;
    selectedUserIds.push(id);
    rdAvailableSearch.value = '';
    rdAutocomplete.hidden = true;
    renderChips();
}
 
function renderChips() {
    if (!rdChips) return;
    if (selectedUserIds.length === 0) {
        rdChips.innerHTML = '';
        rdAssignBtn.disabled = true;
        rdAddHint.textContent = 'Select users above to assign.';
        return;
    }
 
    if (!window._rdSelectedNames) window._rdSelectedNames = {};
 
    rdChips.innerHTML = selectedUserIds.map(id => {
        const name = window._rdSelectedNames[id] || `User #${id}`;
        return `<span class="rd-chip" data-id="${id}">
            ${name}
            <button class="rd-chip__remove" data-id="${id}" aria-label="Remove ${name}">
                <i data-lucide="x"></i>
            </button>
        </span>`;
    }).join('');
 
    rdChips.querySelectorAll('.rd-chip__remove').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = +btn.dataset.id;
            selectedUserIds = selectedUserIds.filter(x => x !== id);
            renderChips();
        });
    });
 
    rdAssignBtn.disabled = false;
    rdAddHint.textContent = `${selectedUserIds.length} user(s) selected.`;
    lucide.createIcons();
}
 
function selectUser(id, name) {
    if (selectedUserIds.includes(id)) return;
    if (!window._rdSelectedNames) window._rdSelectedNames = {};
    window._rdSelectedNames[id] = name;
    selectedUserIds.push(id);
    rdAvailableSearch.value = '';
    rdAutocomplete.hidden = true;
    renderChips();
}
 
if (rdAssignBtn) {
    rdAssignBtn.addEventListener('click', () => {
        if (!activeRoleId || selectedUserIds.length === 0) return;
        rdAssignBtn.disabled = true;
        rdAssignBtn.innerHTML = '<div class="rd-spinner" style="width:16px;height:16px;"></div>';
 
        fetch(buildAssignUrl(activeRoleId), {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_ids: selectedUserIds }),
        })
        .then(r => r.json())
        .then(data => {
            rdAssignBtn.innerHTML = '<i data-lucide="user-plus"></i> Assign Users';
            lucide.createIcons();
 
            if (!data.ok) {
                showToast(data.error || 'Could not assign users.', 'error');
                rdAssignBtn.disabled = false;
                return;
            }
 
            const count = selectedUserIds.length;
            selectedUserIds = [];
            window._rdSelectedNames = {};
            renderChips();
 
            updatePillCount(activeRoleId, data.total_users);
 
            loadRoleDetails(activeRoleId);
            switchRdTab('assigned');
 
            fetchAssignments(currentPage);
            showToast(`${count} user(s) assigned to "${activeRoleName}".`, 'success');
        })
        .catch(() => {
            rdAssignBtn.innerHTML = '<i data-lucide="user-plus"></i> Assign Users';
            lucide.createIcons();
            rdAssignBtn.disabled = false;
            showToast('Could not assign users.', 'error');
        });
    });
}
 
if (closeRevokeModal)  closeRevokeModal.addEventListener('click',  () => hideModal(revokeConfirmModal));
if (cancelRevokeModal) cancelRevokeModal.addEventListener('click', () => hideModal(revokeConfirmModal));
 
if (confirmRevokeBtn) {
    confirmRevokeBtn.addEventListener('click', () => {
        if (!pendingRevokeUserId || !activeRoleId) return;
        confirmRevokeBtn.disabled = true;
 
        fetch(buildRevokeUrl(activeRoleId), {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: pendingRevokeUserId }),
        })
        .then(r => r.json())
        .then(data => {
            confirmRevokeBtn.disabled = false;
            hideModal(revokeConfirmModal);
 
            if (!data.ok) {
                showToast(data.error || 'Could not revoke role.', 'error');
                return;
            }
 
            allAssignedUsers = allAssignedUsers.filter(u => u.id !== pendingRevokeUserId);
            renderAssignedUsers(allAssignedUsers);
 
            const newCount = allAssignedUsers.length;
            rdUserCount.textContent = newCount;
            updatePillCount(activeRoleId, newCount);
 
            if (unassignedValueEl) {
                const cur = parseInt(unassignedValueEl.textContent.replace(/,/g, ''), 10) || 0;
                unassignedValueEl.textContent = cur + 1;
            }
 
            showToast(`Role revoked from "${pendingRevokeUserName}".`, 'success');
            fetchAssignments(currentPage);
            pendingRevokeUserId = null;
            pendingRevokeUserName = null;
        })
        .catch(() => {
            confirmRevokeBtn.disabled = false;
            hideModal(revokeConfirmModal);
            showToast('Could not revoke role.', 'error');
        });
    });
}
 
function updatePillCount(roleId, count) {
    if (!rolePillsWrap) return;
    const badge = rolePillsWrap.querySelector(`[data-role-id="${roleId}"] .role-pill__badge`);
    if (badge) badge.textContent = count;
}
 
if (closeRoleDetails) {
    closeRoleDetails.addEventListener('click', () => {
        hideModal(roleDetailsModal);
        rolePillsWrap && rolePillsWrap.querySelectorAll('.role-pill').forEach(p => p.classList.remove('role-pill--active'));
    });
}
if (roleDetailsModal) {
    roleDetailsModal.addEventListener('click', e => {
        if (e.target === roleDetailsModal) {
            hideModal(roleDetailsModal);
            rolePillsWrap && rolePillsWrap.querySelectorAll('.role-pill').forEach(p => p.classList.remove('role-pill--active'));
        }
    });
}
 
if (convertUsersConfirmModal) {
    convertUsersConfirmModal.addEventListener('click', e => {
        if (e.target === convertUsersConfirmModal) hideModal(convertUsersConfirmModal);
    });
}
 
document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (revokeConfirmModal && !revokeConfirmModal.hidden) { hideModal(revokeConfirmModal); return; }
    if (convertUsersConfirmModal && !convertUsersConfirmModal.hidden) { hideModal(convertUsersConfirmModal); return; }
    if (roleDetailsModal   && !roleDetailsModal.hidden)   { hideModal(roleDetailsModal);   return; }
});
 

})();