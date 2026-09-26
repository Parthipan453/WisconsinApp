

// ==================== GLOBAL VARIABLES ====================
const facultyUuid = '{{ request.resolver_match.kwargs.uuid }}';
let currentPage = 1;
let isFiltering = false;
let searchTimeout = null;
let isFirstLoad = true;

// Store complete data
let allRecordsData = [];
let filteredRecords = [];

// ==================== LOADING FUNCTIONS ====================
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
        overlay.style.opacity = '1';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 200);
    }
}

// ==================== FETCH DATA ====================
function fetchAttendanceData(page = 1) {
    if (isFiltering) return;
    isFiltering = true;
    showLoading();
    
    const year = document.getElementById('yearFilter').value;
    const month = document.getElementById('monthFilter').value;
    const dayOfWeek = document.getElementById('dayOfWeekFilter').value;
    const status = document.getElementById('statusFilter').value;
    const search = document.getElementById('searchInput').value.trim();
    
    // Build URL with parameters
    let url = window.location.pathname + `?ajax=1&page=${page}`;
    if (year) url += `&year=${year}`;
    if (month) url += `&month=${month}`;
    if (dayOfWeek) url += `&day_of_week=${encodeURIComponent(dayOfWeek)}`;
    if (status) url += `&status=${status}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    
    // Update browser URL
    let newUrl = window.location.pathname;
    const params = new URLSearchParams();
    if (year) params.append('year', year);
    if (month) params.append('month', month);
    if (dayOfWeek) params.append('day_of_week', dayOfWeek);
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    const paramString = params.toString();
    if (paramString) {
        newUrl += '?' + paramString;
    }
    
    if (window.history && window.history.pushState) {
        window.history.pushState({ path: newUrl }, '', newUrl);
    }
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Store all records
            allRecordsData = data.all_records || [];
            
            // Store filtered records
            filteredRecords = [...allRecordsData];
            
            // Update the page
            setTimeout(() => {
                updatePage(data);
                hideLoading();
                isFiltering = false;
                isFirstLoad = false;
            }, 150);
        } else {
            throw new Error('Failed to load data');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        isFiltering = false;
        showNotification('Error loading data. Please try again.', 'error');
    });
}

// ==================== FILTER DATA CLIENT-SIDE ====================
function filterRecordsClientSide() {
    const yearFilter = document.getElementById('yearFilter').value;
    const monthFilter = document.getElementById('monthFilter').value;
    const dayOfWeekFilter = document.getElementById('dayOfWeekFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
    
    if (!yearFilter && !monthFilter && !dayOfWeekFilter && !statusFilter && !searchTerm) {
        filteredRecords = [...allRecordsData];
    } else {
        filteredRecords = allRecordsData.filter(record => {
            let matches = true;
            
            // Year filter
            if (yearFilter) {
                const recordYear = record.year || new Date(record.date).getFullYear();
                matches = matches && String(recordYear) === yearFilter;
            }
            
            // Month filter
            if (monthFilter) {
                const recordMonth = record.month || (new Date(record.date).getMonth() + 1);
                matches = matches && String(recordMonth) === monthFilter;
            }
            
            // Day of week filter - EXACT MATCH
            if (dayOfWeekFilter) {
                // Get the day from the record (full day name)
                const recordDay = record.day || '';
                // Compare with the selected day (case insensitive)
                matches = matches && recordDay.toLowerCase() === dayOfWeekFilter.toLowerCase();
            }
            
            // Status filter
            if (statusFilter) {
                matches = matches && record.status === statusFilter;
            }
            
            // Search filter
            if (searchTerm) {
                const searchIn = [
                    record.notes ? record.notes.toLowerCase() : '',
                    record.date || '',
                    record.day ? record.day.toLowerCase() : '',
                    record.status || '',
                    record.status_display ? record.status_display.toLowerCase() : '',
                    record.month ? String(record.month) : '',
                    record.year ? String(record.year) : '',
                    record.login || '',
                    record.logout || ''
                ].join(' ');
                
                matches = matches && searchIn.includes(searchTerm);
            }
            
            return matches;
        });
    }
    
    // Update stats based on filtered data
    updateStatsFromFilteredData();
    
    // Update table with filtered data
    updateTableFromFilteredData(1);
}

function updateStatsFromFilteredData() {
    const total = filteredRecords.length;
    const present = filteredRecords.filter(r => r.status === 'present').length;
    const absent = filteredRecords.filter(r => r.status === 'absent').length;
    const late = filteredRecords.filter(r => r.status === 'late').length;
    const halfDay = filteredRecords.filter(r => r.status === 'half-day').length;
    const leave = filteredRecords.filter(r => r.status === 'leave').length;
    
    // Calculate average hours
    let totalHours = 0;
    let countWithHours = 0;
    filteredRecords.forEach(r => {
        const hours = parseFloat(r.hours) || 0;
        if (hours > 0) {
            totalHours += hours;
            countWithHours++;
        }
    });
    const avgHours = countWithHours > 0 ? (totalHours / countWithHours).toFixed(1) : '0.0';
    
    // Update stats cards with animation
    animateNumber(document.getElementById('statTotalDays'), total);
    animateNumber(document.getElementById('statPresentDays'), present);
    animateNumber(document.getElementById('statAbsentDays'), absent + late + halfDay + leave);
    document.getElementById('statAvgHours').textContent = avgHours + 'h';
    
    // Update quick summary
    animateNumber(document.getElementById('summaryPresent'), present);
    animateNumber(document.getElementById('summaryAbsent'), absent);
    animateNumber(document.getElementById('summaryLate'), late);
    animateNumber(document.getElementById('summaryTotal'), total);
    
    // Update percentages
    const presentPercent = total > 0 ? ((present / total) * 100).toFixed(1) : 0;
    const absentPercent = total > 0 ? ((absent / total) * 100).toFixed(1) : 0;
    const latePercent = total > 0 ? ((late / total) * 100).toFixed(1) : 0;
    const halfDayPercent = total > 0 ? ((halfDay / total) * 100).toFixed(1) : 0;
    
    animateBar('presentBar', presentPercent);
    animateBar('absentBar', absentPercent);
    animateBar('lateBar', latePercent);
    animateBar('halfdayBar', halfDayPercent);
    
    document.getElementById('presentPercent').textContent = presentPercent + '%';
    document.getElementById('absentPercent').textContent = absentPercent + '%';
    document.getElementById('latePercent').textContent = latePercent + '%';
    document.getElementById('halfdayPercent').textContent = halfDayPercent + '%';
}

function updateTableFromFilteredData(page = 1) {
    const itemsPerPage = 10;
    const totalItems = filteredRecords.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    
    // Adjust page if out of range
    if (page > totalPages) page = totalPages;
    if (page < 1) page = 1;
    currentPage = page;
    
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
    const pageItems = filteredRecords.slice(startIndex, endIndex);
    
    // Update table
    const tbody = document.getElementById('attendanceTableBody');
    if (tbody) {
        tbody.style.transition = 'opacity 0.2s';
        tbody.style.opacity = '0';
        
        setTimeout(() => {
            if (pageItems.length > 0) {
                let html = '';
                pageItems.forEach((record, index) => {
                    const serial = startIndex + index + 1;
                    const statusClass = record.status;
                    const statusText = record.status === 'half-day' ? 'Half Day' : record.status.charAt(0).toUpperCase() + record.status.slice(1);
                    html += `
                        <tr>
                            <td>${serial}</td>
                            <td>
                                <span class="date-display">
                                    <i class="ti ti-calendar"></i>
                                    ${record.date || '-'}
                                </span>
                            </td>
                            <td>${record.day || '-'}</td>
                            <td>
                                <span class="time-login">
                                    <i class="ti ti-login"></i>
                                    ${record.login || '-'}
                                </span>
                            </td>
                            <td>
                                <span class="time-logout">
                                    <i class="ti ti-logout"></i>
                                    ${record.logout || '-'}
                                </span>
                            </td>
                            <td>
                                <span class="working-hours">
                                    <i class="ti ti-clock"></i>
                                    ${record.hours || '0'}h
                                </span>
                            </td>
                            <td>
                                <span class="status-badge ${statusClass}">${statusText}</span>
                            </td>
                        </tr>
                    `;
                });

                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="empty-state">
                            <i class="ti ti-calendar-off"></i>
                            <p>No attendance records found</p>
                            <span class="empty-sub">Try adjusting your filters</span>
                        </td>
                    </tr>
                `;
            }
            tbody.style.opacity = '1';
        }, 150);
    }
    
    // Update pagination
    updatePaginationClientSide(totalItems, totalPages, page);
    
    // Update record count
    const recordCount = document.getElementById('recordCount');
    if (recordCount) {
        recordCount.textContent = `Showing ${startIndex + 1} - ${endIndex} of ${totalItems} records`;
    }
    
    const paginationInfo = document.getElementById('paginationInfo');
    if (paginationInfo) {
        paginationInfo.textContent = `Showing ${startIndex + 1} to ${endIndex} of ${totalItems} entries`;
    }
}

function updatePaginationClientSide(totalItems, totalPages, currentPage) {
    const controls = document.getElementById('paginationControls');
    if (!controls) return;
    
    let html = '';
    
    if (currentPage > 1) {
        html += `<a href="#" data-page="1" class="page-link pagination-link">&laquo;</a>`;
        html += `<a href="#" data-page="${currentPage - 1}" class="page-link pagination-link">&lsaquo;</a>`;
    } else {
        html += `<span class="page-link disabled">&laquo;</span>`;
        html += `<span class="page-link disabled">&lsaquo;</span>`;
    }
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<span class="page-link">...</span>`;
    }
    
    for (let num = startPage; num <= endPage; num++) {
        if (currentPage === num) {
            html += `<span class="page-link active" data-page="${num}">${num}</span>`;
        } else {
            html += `<a href="#" data-page="${num}" class="page-link pagination-link">${num}</a>`;
        }
    }
    
    if (endPage < totalPages) {
        html += `<span class="page-link">...</span>`;
    }
    
    if (currentPage < totalPages) {
        html += `<a href="#" data-page="${currentPage + 1}" class="page-link pagination-link">&rsaquo;</a>`;
        html += `<a href="#" data-page="${totalPages}" class="page-link pagination-link">&raquo;</a>`;
    } else {
        html += `<span class="page-link disabled">&rsaquo;</span>`;
        html += `<span class="page-link disabled">&raquo;</span>`;
    }
    
    controls.innerHTML = html;
    
    // Add event listeners
    document.querySelectorAll('.pagination-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = parseInt(this.dataset.page);
            if (page && page !== currentPage) {
                const tableCard = document.querySelector('.table-card');
                if (tableCard) {
                    tableCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                updateTableFromFilteredData(page);
            }
        });
    });
}

// ==================== UPDATE PAGE ====================

function updatePage(data) {
    // Show OVERALL statistics (all time - no filters applied)
    // These values come from the base queryset without any filters
    animateNumber(document.getElementById('statTotalDays'), data.overall_total_days || 0);
    animateNumber(document.getElementById('statPresentDays'), data.overall_present_days || 0);
    animateNumber(document.getElementById('statAbsentDays'), data.overall_absent_days || 0);
    document.getElementById('statAvgHours').textContent = (data.overall_avg_hours || '0.0') + 'h';
    
    // Update today's status
    document.getElementById('todayLogin').textContent = data.today_login || '-';
    document.getElementById('todayLogout').textContent = data.today_logout || '-';
    document.getElementById('todayHours').textContent = data.today_hours || '0h';
    
    const statusBadge = document.getElementById('todayStatus');
    if (statusBadge) {
        statusBadge.style.transition = 'opacity 0.2s';
        statusBadge.style.opacity = '0';
        
        setTimeout(() => {
            const statusText = data.today_status ? data.today_status.charAt(0).toUpperCase() + data.today_status.slice(1) : 'Absent';
            statusBadge.textContent = statusText;
            statusBadge.className = 'status-badge ' + (data.today_status || 'absent');
            statusBadge.style.opacity = '1';
        }, 150);
    }
    
    // Update table
    const tbody = document.getElementById('attendanceTableBody');
    if (tbody) {
        tbody.style.transition = 'opacity 0.2s';
        tbody.style.opacity = '0';
        
        setTimeout(() => {
            if (data.attendance_list && data.attendance_list.length > 0) {
                let html = '';
                data.attendance_list.forEach((record, index) => {
                    const serial = (data.page_obj.start_index + index);
                    const statusClass = record.status;
                    const statusText = record.status === 'half-day' ? 'Half Day' : record.status.charAt(0).toUpperCase() + record.status.slice(1);
                    html += `
                        <tr>
                            <td>${serial}</td>
                            <td>
                                <span class="date-display">
                                    <i class="ti ti-calendar"></i>
                                    ${record.date || '-'}
                                </span>
                            </td>
                            <td>${record.day || '-'}</td>
                            <td>
                                <span class="time-login">
                                    <i class="ti ti-login"></i>
                                    ${record.login || '-'}
                                </span>
                            </td>
                            <td>
                                <span class="time-logout">
                                    <i class="ti ti-logout"></i>
                                    ${record.logout || '-'}
                                </span>
                            </td>
                            <td>
                                <span class="working-hours">
                                    <i class="ti ti-clock"></i>
                                    ${record.hours || '0'}h
                                </span>
                            </td>
                            <td>
                                <span class="status-badge ${statusClass}">${statusText}</span>
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="empty-state">
                            <i class="ti ti-calendar-off"></i>
                            <p>No attendance records found</p>
                            <span class="empty-sub">Try adjusting your filters</span>
                        </td>
                    </tr>
                `;
            }
            tbody.style.opacity = '1';
        }, 150);
    }
    
    // Update record count
    const recordCount = document.getElementById('recordCount');
    if (recordCount && data.page_obj) {
        recordCount.textContent = `Showing ${data.page_obj.start_index} - ${data.page_obj.end_index} of ${data.page_obj.total_records} records`;
    }
    
    // Update pagination info
    const paginationInfo = document.getElementById('paginationInfo');
    if (paginationInfo && data.page_obj) {
        paginationInfo.textContent = `Showing ${data.page_obj.start_index} to ${data.page_obj.end_index} of ${data.page_obj.total_records} entries`;
    }
    
    // Update pagination controls
    if (data.page_obj) {
        updatePagination(data.page_obj);
    }
    
    // Update monthly stats with animation (these use filtered data)
    animateBar('presentBar', data.present_percentage || 0);
    animateBar('absentBar', data.absent_percentage || 0);
    animateBar('lateBar', data.late_percentage || 0);
    animateBar('halfdayBar', data.halfday_percentage || 0);
    
    document.getElementById('presentPercent').textContent = (data.present_percentage || 0) + '%';
    document.getElementById('absentPercent').textContent = (data.absent_percentage || 0) + '%';
    document.getElementById('latePercent').textContent = (data.late_percentage || 0) + '%';
    document.getElementById('halfdayPercent').textContent = (data.halfday_percentage || 0) + '%';
    
    // Update quick summary (these use filtered data)
    animateNumber(document.getElementById('summaryPresent'), data.present_days || 0);
    animateNumber(document.getElementById('summaryAbsent'), data.absent_days || 0);
    animateNumber(document.getElementById('summaryLate'), data.late_days || 0);
    animateNumber(document.getElementById('summaryTotal'), data.total_days || 0);
    
    // Update weekly bars
    if (data.weekly_data) {
        updateWeeklyBars(data.weekly_data);
    }
    
    // Update month label
    if (data.current_month_name) {
        document.getElementById('currentMonthLabel').textContent = data.current_month_name;
    }
    if (data.week_label) {
        document.getElementById('currentWeekLabel').textContent = data.week_label;
    }
}

// ==================== ANIMATION HELPERS ====================
function animateNumber(element, targetValue) {
    if (!element) return;
    
    const currentValue = parseInt(element.textContent) || 0;
    if (currentValue === targetValue) return;
    
    const duration = 300;
    const startTime = performance.now();
    const startValue = currentValue;
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        
        const current = Math.round(startValue + (targetValue - startValue) * eased);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        } else {
            element.textContent = targetValue;
        }
    }
    
    requestAnimationFrame(updateNumber);
}

function animateBar(elementId, targetPercentage) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const currentWidth = parseFloat(element.style.width) || 0;
    if (Math.abs(currentWidth - targetPercentage) < 0.1) return;
    
    const duration = 400;
    const startTime = performance.now();
    const startWidth = currentWidth;
    
    function updateBar(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        
        const current = startWidth + (targetPercentage - startWidth) * eased;
        element.style.width = current + '%';
        
        if (progress < 1) {
            requestAnimationFrame(updateBar);
        } else {
            element.style.width = targetPercentage + '%';
        }
    }
    
    requestAnimationFrame(updateBar);
}

// ==================== UPDATE PAGINATION ====================
function updatePagination(pageObj) {
    const controls = document.getElementById('paginationControls');
    if (!controls) return;
    
    let html = '';
    
    if (pageObj.has_previous) {
        html += `<a href="#" data-page="1" class="page-link pagination-link">&laquo;</a>`;
        html += `<a href="#" data-page="${pageObj.previous_page_number}" class="page-link pagination-link">&lsaquo;</a>`;
    } else {
        html += `<span class="page-link disabled">&laquo;</span>`;
        html += `<span class="page-link disabled">&lsaquo;</span>`;
    }
    
    const startPage = Math.max(1, pageObj.current_page - 2);
    const endPage = Math.min(pageObj.total_pages, pageObj.current_page + 2);
    
    if (startPage > 1) {
        html += `<span class="page-link">...</span>`;
    }
    
    for (let num = startPage; num <= endPage; num++) {
        if (pageObj.current_page === num) {
            html += `<span class="page-link active" data-page="${num}">${num}</span>`;
        } else {
            html += `<a href="#" data-page="${num}" class="page-link pagination-link">${num}</a>`;
        }
    }
    
    if (endPage < pageObj.total_pages) {
        html += `<span class="page-link">...</span>`;
    }
    
    if (pageObj.has_next) {
        html += `<a href="#" data-page="${pageObj.next_page_number}" class="page-link pagination-link">&rsaquo;</a>`;
        html += `<a href="#" data-page="${pageObj.total_pages}" class="page-link pagination-link">&raquo;</a>`;
    } else {
        html += `<span class="page-link disabled">&rsaquo;</span>`;
        html += `<span class="page-link disabled">&raquo;</span>`;
    }
    
    controls.innerHTML = html;
    
    document.querySelectorAll('.pagination-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            if (page) {
                currentPage = parseInt(page);
                const tableCard = document.querySelector('.table-card');
                if (tableCard) {
                    tableCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                fetchAttendanceData(currentPage);
            }
        });
    });
}

// ==================== UPDATE WEEKLY BARS ====================
function updateWeeklyBars(weeklyData) {
    const container = document.getElementById('weeklyBars');
    if (!container) return;
    
    let html = '';
    weeklyData.forEach(day => {
        const hoursDisplay = day.hours > 0 ? day.hours.toFixed(1) + 'h' : '-';
        const statusClass = day.status || 'absent';
        const dateDisplay = day.date || '';
        html += `
            <div class="weekly-item">
                <div class="weekly-bar-wrapper">
                    <div class="weekly-bar ${statusClass}" style="height: 0%;">
                        <span class="weekly-hours">${hoursDisplay}</span>
                    </div>
                </div>
                <span class="weekly-day">${day.day}</span>
                <span class="weekly-date">${dateDisplay}</span>
            </div>
        `;
    });
    container.innerHTML = html;
    
    setTimeout(() => {
        const bars = container.querySelectorAll('.weekly-bar');
        weeklyData.forEach((day, index) => {
            if (bars[index]) {
                setTimeout(() => {
                    bars[index].style.transition = 'height 0.5s ease';
                    bars[index].style.height = day.percentage + '%';
                }, index * 50);
            }
        });
    }, 100);
}

// ==================== NOTIFICATION ====================
function showNotification(message, type = 'info') {
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }
    
    const colors = {
        error: '#ff4444',
        success: '#4CAF50',
        info: '#2196F3',
        warning: '#ff9800'
    };
    
    const notification = document.createElement('div');
    notification.style.cssText = `
        pointer-events: auto;
        background: white;
        padding: 16px 24px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-left: 4px solid ${colors[type] || colors.info};
        animation: slideIn 0.3s ease;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    `;
    
    notification.innerHTML = `
        <span style="color: ${colors[type] || colors.info}; font-weight: bold;">
            ${type.toUpperCase()}
        </span>
        <span style="flex: 1;">${message}</span>
        <button onclick="this.parentElement.remove()" 
                style="background: none; border: none; cursor: pointer; font-size: 18px; padding: 0 4px;">
            ×
        </button>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// ==================== FILTER FUNCTIONS ====================
function applyFilters() {
    currentPage = 1;
    fetchAttendanceData(currentPage);
}

function applySearch() {
    clearTimeout(searchTimeout);
    filterRecordsClientSide();
}

function resetFilters() {
    document.getElementById('yearFilter').value = '';
    document.getElementById('monthFilter').value = '';
    document.getElementById('dayOfWeekFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('searchInput').value = '';
    currentPage = 1;
    fetchAttendanceData(currentPage);
}

function refreshData() {
    fetchAttendanceData(currentPage);
}

function exportData(type) {
    const year = document.getElementById('yearFilter').value;
    const month = document.getElementById('monthFilter').value;
    const dayOfWeek = document.getElementById('dayOfWeekFilter').value;
    const status = document.getElementById('statusFilter').value;
    const search = document.getElementById('searchInput').value.trim();
    
    let url = window.location.pathname + `?export=${type}`;
    if (year) url += `&year=${year}`;
    if (month) url += `&month=${month}`;
    if (dayOfWeek) url += `&day_of_week=${encodeURIComponent(dayOfWeek)}`;
    if (status) url += `&status=${status}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    
    window.location.href = url;
}

// ==================== EVENT LISTENERS ====================
document.addEventListener('DOMContentLoaded', function() {


    // Auto-apply filters on change with debounce
    let debounceTimer;
    const filterInputs = ['yearFilter', 'monthFilter', 'dayOfWeekFilter', 'statusFilter'];
    filterInputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    currentPage = 1;
                    fetchAttendanceData(currentPage);
                }, 300);
            });
        }
    });
    
    // Search input with client-side filtering
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterRecordsClientSide();
            }, 300);
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                filterRecordsClientSide();
            }
        });
    }
    
    // Restore filter state from URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('year')) {
        document.getElementById('yearFilter').value = urlParams.get('year');
    }
    if (urlParams.has('month')) {
        document.getElementById('monthFilter').value = urlParams.get('month');
    }
    if (urlParams.has('day_of_week')) {
        document.getElementById('dayOfWeekFilter').value = urlParams.get('day_of_week');
    }
    if (urlParams.has('status')) {
        document.getElementById('statusFilter').value = urlParams.get('status');
    }
    if (urlParams.has('search')) {
        document.getElementById('searchInput').value = urlParams.get('search');
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        if (e.key === 'Escape' && !e.target.matches('input, select, textarea')) {
            resetFilters();
        }
    });
    
    // Initial load
    fetchAttendanceData(1);
    
    // Handle browser back/forward
    window.addEventListener('popstate', function() {
        const params = new URLSearchParams(window.location.search);
        if (params.has('year')) {
            document.getElementById('yearFilter').value = params.get('year');
        }
        if (params.has('month')) {
            document.getElementById('monthFilter').value = params.get('month');
        }
        if (params.has('day_of_week')) {
            document.getElementById('dayOfWeekFilter').value = params.get('day_of_week');
        }
        if (params.has('status')) {
            document.getElementById('statusFilter').value = params.get('status');
        }
        if (params.has('search')) {
            document.getElementById('searchInput').value = params.get('search');
        }
        fetchAttendanceData(1);
    });

    document.querySelectorAll('.filter-input').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
    });
});