/**
 * Chart rendering module using Chart.js v4
 * 
 * Provides functions for rendering:
 * - Line charts (trends)
 * - Pie charts (severity distribution)
 * - Gauge charts (coverage with color thresholds)
 */

// Chart instances storage (for cleanup and updates)
const chartInstances = {};

/**
 * Color schemes for different metrics
 */
const COLORS = {
    bugs: '#d32f2f',
    vulnerabilities: '#f57c00',
    codeSmells: '#fdd835',
    coverage: {
        high: '#4caf50',    // >80%
        medium: '#ff9800',  // 50-80%
        low: '#f44336'      // <50%
    },
    qualityGate: {
        OK: '#4caf50',
        WARN: '#ff9800',
        ERROR: '#f44336'
    },
    severity: {
        BLOCKER: '#d32f2f',
        CRITICAL: '#f57c00',
        MAJOR: '#ff9800',
        MINOR: '#fdd835',
        INFO: '#2196f3'
    }
};

/**
 * Get coverage color based on percentage
 */
function getCoverageColor(percentage) {
    if (percentage === null || percentage === undefined) return COLORS.coverage.low;
    if (percentage >= 80) return COLORS.coverage.high;
    if (percentage >= 50) return COLORS.coverage.medium;
    return COLORS.coverage.low;
}

/**
 * Destroy existing chart instance if it exists
 */
function destroyChart(canvasId) {
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
        delete chartInstances[canvasId];
    }
}

/**
 * Render a line chart for trend analysis
 * @param {string} canvasId - Canvas element ID
 * @param {Array} data - Array of {date, bugs, vulnerabilities, coverage}
 * @param {Object} options - Chart options
 */
function renderTrendChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    
    // Prepare datasets
    const labels = data.map(item => formatDate(item.analysis_date || item.date));
    
    const datasets = [];
    
    // Add bugs dataset if present
    if (data.some(item => 'bugs_count' in item || 'bugs' in item)) {
        datasets.push({
            label: 'Bugs',
            data: data.map(item => (item.bugs_count ?? item.bugs)),
            borderColor: COLORS.bugs,
            backgroundColor: COLORS.bugs + '33',
            tension: 0.4,
            yAxisID: 'y'
        });
    }
    
    // Add vulnerabilities dataset if present
    if (data.some(item => 'vulnerabilities_count' in item || 'vulnerabilities' in item)) {
        datasets.push({
            label: 'Vulnerabilities',
            data: data.map(item => (item.vulnerabilities_count ?? item.vulnerabilities)),
            borderColor: COLORS.vulnerabilities,
            backgroundColor: COLORS.vulnerabilities + '33',
            tension: 0.4,
            yAxisID: 'y'
        });
    }
    
    // Add coverage dataset if present
    if (data.some(item => 'coverage_pct' in item || 'coverage' in item)) {
        datasets.push({
            label: 'Coverage (%)',
            data: data.map(item => (item.coverage_pct ?? item.coverage)),
            borderColor: COLORS.coverage.high,
            backgroundColor: COLORS.coverage.high + '33',
            tension: 0.4,
            yAxisID: 'y1'
        });
    }
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: options.title || 'Metrics Trend',
                    font: { size: 16 }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            const value = context.parsed.y;
                            if (context.dataset.yAxisID === 'y1') {
                                label += value === null || value === undefined ? 'N/A' : value.toFixed(2) + '%';
                            } else {
                                label += value === null || value === undefined ? 'N/A' : value;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Count'
                    },
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: datasets.length > 2,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Coverage (%)'
                    },
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
    
    chartInstances[canvasId] = chart;
    return chart;
}

/**
 * Render a pie chart for severity distribution
 * @param {string} canvasId - Canvas element ID
 * @param {Object} severityData - Object with {BLOCKER, CRITICAL, MAJOR, MINOR, INFO}
 * @param {Object} options - Chart options
 */
function renderSeverityPieChart(canvasId, severityData, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    
    const labels = Object.keys(severityData);
    const values = Object.values(severityData);
    const colors = labels.map(severity => COLORS.severity[severity] || '#999999 ');
    
    const chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: options.title || 'Severity Distribution',
                    font: { size: 16 }
                },
                legend: {
                    display: true,
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    chartInstances[canvasId] = chart;
    return chart;
}

/**
 * Render a doughnut chart with gauge-like appearance for coverage
 * @param {string} canvasId - Canvas element ID
 * @param {number} coveragePercent - Coverage percentage (0-100)
 * @param {Object} options - Chart options
 */
function renderCoverageGauge(canvasId, coveragePercent, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    
    const value = coveragePercent ?? 0;
    const remaining = 100 - value;
    const color = getCoverageColor(value);
    
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Coverage', 'Remaining'],
            datasets: [{
                data: [value, remaining],
                backgroundColor: [color, '#e0e0e0'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: options.title || 'Code Coverage',
                    font: { size: 16 }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        },
        plugins: [{
            id: 'centerText',
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                ctx.save();
                const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                
                ctx.font = 'bold 32px sans-serif';
                ctx.fillStyle = color;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${value.toFixed(1)}%`, centerX, centerY);
                ctx.restore();
            }
        }]
    });
    
    chartInstances[canvasId] = chart;
    return chart;
}

/**
 * Render a bar chart for project comparison
 * @param {string} canvasId - Canvas element ID
 * @param {Array} projects - Array of {name, bugs, vulnerabilities, coverage}
 * @param {Object} options - Chart options
 */
function renderProjectComparisonChart(canvasId, projects, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    destroyChart(canvasId);

    const ctx = canvas.getContext('2d');
    
    const labels = projects.map(p => (p.name ?? p.project_name));
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Bugs',
                    data: projects.map(p => (p.bugs_count ?? p.bugs)),
                    backgroundColor: COLORS.bugs,
                    yAxisID: 'y'
                },
                {
                    label: 'Vulnerabilities',
                    data: projects.map(p => (p.vulnerabilities_count ?? p.vulnerabilities)),
                    backgroundColor: COLORS.vulnerabilities,
                    yAxisID: 'y'
                },
                {
                    label: 'Coverage (%)',
                    data: projects.map(p => (p.coverage_pct ?? p.coverage)),
                    backgroundColor: COLORS.coverage.high,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: options.title || 'Project Comparison',
                    font: { size: 16 }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Count'
                    },
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Coverage (%)'
                    },
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
    
    chartInstances[canvasId] = chart;
    return chart;
}

/**
 * Cleanup all charts
  */
function destroyAllCharts() {
    Object.keys(chartInstances).forEach(canvasId => {
        destroyChart(canvasId);
    });
}

console.log('Charts module loaded - Chart.js v4 rendering functions available');

