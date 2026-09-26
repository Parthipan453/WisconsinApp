// /* kali's  code  */

document.addEventListener('DOMContentLoaded', function () {


    if (window.lucide) {
        lucide.createIcons();
    }


    if (window.AOS) {
        AOS.init({
            duration: 700,
            easing: 'ease-out-cubic',
            once: true,
            offset: 40
        });
    }


    var rootStyles = getComputedStyle(document.documentElement);

    function cssVar(name, fallback) {
        var value = rootStyles.getPropertyValue(name).trim();
        return value || fallback;
    }

    function formatK(value) {

    if (value < 1000) {
        return value;
    }

    if (value < 1000000) {
        return (value / 1000).toFixed(value % 1000 === 0 ? 0 : 1) + "k";
    }

    return (value / 1000000).toFixed(value % 1000000 === 0 ? 0 : 1) + "M";
}
    var colors = {
        red: cssVar('--db-red', '#e0455c'),
        blue: cssVar('--db-blue', '#4d82f3'),
        black: cssVar('--db-black', '#1f2024'),
        green: cssVar('--db-green', '#1cb35c'),
        orange: cssVar('--db-orange', '#f5a623'),
        purple: cssVar('--db-purple', '#8b7cf6'),
        suspended: cssVar('--db-suspended', '#b3261e'),
        inactive: cssVar('--db-inactive', '#9aa0ab'),
        grid: '#f1eef0',
        muted: cssVar('--db-text-muted', '#98989f')
    };

    if (typeof Chart === 'undefined') {
        return;
    }

    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = colors.muted;

    var dashboardData = {};
    var dataEl = document.getElementById('dashboard-chart-data');
    if (dataEl) {
        try {
            dashboardData = JSON.parse(dataEl.textContent);
        } catch (e) {
            dashboardData = {};
        }
    }

    var userGrowth = dashboardData.userGrowth || { labels: [], students: [], faculty: [], administrators: [] };
    var userDistribution = dashboardData.userDistribution || { students: 0, faculty: 0, administrators: 0 };
    var accountStatus = dashboardData.accountStatus || { active: 0, pending: 0, suspended: 0, inactive: 0 };

   function niceMax(values) {

    const max = Math.max(...values, 0);

    if (max <= 5) {
        return 5;
    }

    if (max <= 10) {
        return 10;
    }

    if (max <= 20) {
        return 20;
    }

    if (max <= 50) {
        return 50;
    }

    if (max <= 100) {
        return 100;
    }

    return Math.ceil(max / 100) * 100;
}

    var userGrowthEl = document.getElementById('userGrowthChart');
    if (userGrowthEl) {
        var growthMax = niceMax([].concat(userGrowth.students, userGrowth.faculty, userGrowth.administrators));
        new Chart(userGrowthEl, {
            type: 'line',
            data: {
                labels: userGrowth.labels,
                datasets: [
                    {
                        label: 'Students',
                        data: userGrowth.students,
                        borderColor: colors.red,
                        backgroundColor: colors.red,
                        pointBackgroundColor: colors.red,
                        pointBorderColor: '#fff',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Faculty',
                        data: userGrowth.faculty,
                        borderColor: colors.blue,
                        backgroundColor: colors.blue,
                        pointBackgroundColor: colors.blue,
                        pointBorderColor: '#fff',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Administrators',
                        data: userGrowth.administrators,
                        borderColor: colors.black,
                        backgroundColor: colors.black,
                        pointBackgroundColor: colors.black,
                        pointBorderColor: '#fff',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ctx.dataset.label + ': ' + formatK(ctx.raw);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: growthMax,
                       ticks: {
                            stepSize: growthMax <= 10 ? 1 : Math.ceil(growthMax / 5),
                            callback: formatK
                        },
                        grid: { color: colors.grid },
                        border: { display: false }
                    },
                    x: {
                        grid: { display: false },
                        border: { display: false }
                    }
                }
            }
        });
    }

    var userDistributionEl = document.getElementById('userDistributionChart');
    if (userDistributionEl) {
        new Chart(userDistributionEl, {
            type: 'doughnut',
            data: {
                labels: ['Students', 'Faculty', 'Administrators'],
                datasets: [{
                    data: [
                        userDistribution.students || 0,
                        userDistribution.faculty || 0,
                        userDistribution.administrators || 0
                    ],
                    backgroundColor: [colors.red, colors.blue, colors.black],
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }


    var accountStatusEl = document.getElementById('accountStatusChart');
    if (accountStatusEl) {
        var statusValues = [
            accountStatus.active || 0,
            accountStatus.pending || 0,
            accountStatus.suspended || 0,
            accountStatus.inactive || 0
        ];
        var statusMax = niceMax(statusValues);
        new Chart(accountStatusEl, {
            type: 'bar',
            data: {
                labels: ['Active', 'Pending', 'Suspended', 'Inactive'],
                datasets: [{
                    data: statusValues,
                    backgroundColor: [colors.green, colors.orange, colors.suspended, colors.inactive],
                    borderRadius: 6,
                    maxBarThickness: 48
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        min: 0,
                        max: statusMax,
                       ticks: {
                            stepSize: statusMax <= 10 ? 1 : Math.ceil(statusMax / 5),
                            callback: formatK
                        },
                        grid: { color: colors.grid },
                        border: { display: false }
                    },
                    x: {
                        grid: { display: false },
                        border: { display: false }
                    }
                }
            }
        });
    }

});