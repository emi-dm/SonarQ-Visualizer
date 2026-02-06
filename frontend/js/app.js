/**
 * Main application logic for SonarQube Report Visualizer.
 * Handles UI interactions, state management, and API communication.
 */

// Application state
const appState = {
  connections: [],
  currentConnection: null,
  currentProject: null,
  projects: [],
  projectPage: 1,
  projectPageSize: 20,
  totalProjectPages: 1,
  virtualScrollHandler: null,
  virtualItemHeight: 190
};

/**
 * Initialize application
 */
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

/**
 * Setup event listeners and load initial data
 */
async function initializeApp() {
  // Setup modal event listeners
  setupModalListeners();
  setupProjectListeners();
  setupNavigationListeners();
  setupDashboardListeners();
  
  // Load connections
  await loadConnections();
  showSection('connections');
  
  showLoading();
  hideLoading();
}

function setupProjectListeners() {
  const syncProjectsBtn = document.getElementById('sync-projects-btn');
  const projectSearch = document.getElementById('project-search');
  const backToProjectsBtn = document.getElementById('back-to-projects-btn');
  const refreshMetricsBtn = document.getElementById('refresh-metrics-btn');
  const exportJsonBtn = document.getElementById('export-json-btn');
  const exportCsvBtn = document.getElementById('export-csv-btn');
  const prevBtn = document.getElementById('projects-prev-btn');
  const nextBtn = document.getElementById('projects-next-btn');
  const branchSelector = document.getElementById('branch-selector');

  syncProjectsBtn.addEventListener('click', async () => {
    await syncProjects();
  });

  const debouncedSearch = debounce(() => {
    renderProjects(appState.projects);
  }, 300);

  projectSearch.addEventListener('input', debouncedSearch);

  backToProjectsBtn.addEventListener('click', () => {
    showSection('projects');
  });

  refreshMetricsBtn.addEventListener('click', async () => {
    await refreshMetrics();
  });

  exportJsonBtn.addEventListener('click', async () => {
    await exportLatestMetrics('json');
  });

  exportCsvBtn.addEventListener('click', async () => {
    await exportLatestMetrics('csv');
  });

  prevBtn.addEventListener('click', async () => {
    if (appState.projectPage > 1) {
      await loadProjects(appState.currentConnection.id, appState.projectPage - 1);
    }
  });

  nextBtn.addEventListener('click', async () => {
    if (appState.projectPage < appState.totalProjectPages) {
      await loadProjects(appState.currentConnection.id, appState.projectPage + 1);
    }
  });

  branchSelector.addEventListener('change', async () => {
    if (appState.currentProject) {
      await loadProjectMetrics(appState.currentProject.id, branchSelector.value);
    }
  });
}

/**
 * Setup modal and button event listeners
 */
function setupModalListeners() {
  const addConnectionBtn = document.getElementById('add-connection-btn');
  const closeModalBtn = document.getElementById('close-modal-btn');
  const connectionForm = document.getElementById('connection-form');
  const testConnectionBtn = document.getElementById('test-connection-btn');
  const modal = document.getElementById('connection-modal');
  
  // Open modal
  addConnectionBtn.addEventListener('click', () => {
    openConnectionModal();
  });
  
  // Close modal
  closeModalBtn.addEventListener('click', () => {
    closeConnectionModal();
  });
  
  // Close modal on outside click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeConnectionModal();
    }
  });
  
  // Test connection
  testConnectionBtn.addEventListener('click', async () => {
    await testConnection();
  });
  
  // Submit form
  connectionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveConnection();
  });
}

/**
 * Open connection modal
 */
function openConnectionModal(connection = null) {
  const modal = document.getElementById('connection-modal');
  const form = document.getElementById('connection-form');
  const title = document.getElementById('modal-title');
  const errorDiv = document.getElementById('form-error');
  
  // Reset form
  form.reset();
  errorDiv.classList.add('hidden');
  
  if (connection) {
    // Edit mode
    title.textContent = 'Edit Connection';
    document.getElementById('connection-name').value = connection.name;
    document.getElementById('connection-url').value = connection.server_url;
    document.getElementById('connection-organization').value = connection.organization || '';
    form.dataset.editId = connection.id;
    
    // Get token from storage
    const token = getFromStorage(`connection_token_${connection.id}`);
    if (token) {
      document.getElementById('connection-token').value = token;
    }
  } else {
    // Create mode
    title.textContent = 'Add Connection';
    delete form.dataset.editId;
  }
  
  modal.classList.remove('hidden');
}

/**
 * Close connection modal
 */
function closeConnectionModal() {
  const modal = document.getElementById('connection-modal');
  modal.classList.add('hidden');
}

/**
 * Test connection without saving
 */
async function testConnection() {
  const name = document.getElementById('connection-name').value.trim();
  const serverUrl = document.getElementById('connection-url').value.trim();
  const token = document.getElementById('connection-token').value.trim();
  const errorDiv = document.getElementById('form-error');
  const organization = document.getElementById('connection-organization').value.trim();
  
  if (!name || !serverUrl || !token) {
    showError('Please fill in all fields', errorDiv);
    return;
  }
  
  showLoading();
  
  try {
    // Create temporary connection to test
    const response = await connectionsAPI.create({
      name: `${name}_test_${Date.now()}`,
      server_url: serverUrl,
      organization: organization || null,
      token: token,
      validate: true
    });
    
    // Delete the temporary connection
    await connectionsAPI.delete(response.id);
    
    hideLoading();
    showToast('Connection test successful!', 'success');
    errorDiv.classList.add('hidden');
    
  } catch (error) {
    hideLoading();
    const message = error.message || error.error || 'Connection test failed';
    showError(message, errorDiv);
    showToast('Connection test failed', 'error');
  }
}

/**
 * Save connection (create or update)
 */
async function saveConnection() {
  const form = document.getElementById('connection-form');
  const name = document.getElementById('connection-name').value.trim();
  const serverUrl = document.getElementById('connection-url').value.trim();
  const token = document.getElementById('connection-token').value.trim();
  const errorDiv = document.getElementById('form-error');
  const editId = form.dataset.editId;
  
  const organization = document.getElementById('connection-organization').value.trim();
  showLoading();
  
  try {
    if (editId) {
      // Update existing connection
      const connection = await connectionsAPI.update(parseInt(editId), {
        name: name,
        server_url: serverUrl,
        organization: organization || null
      });
      // Update token in storage
      setInStorage(`connection_token_${connection.id}`, token);
      
      showToast('Connection updated successfully', 'success');
    } else {
      // Create new connection
      const connection = await connectionsAPI.create({
        name: name,
        server_url: serverUrl,
        organization: organization || null,
        token: token,
        validate: false  // Don't validate on create, user can test first
      });
      
      // Store token in localStorage
      setInStorage(`connection_token_${connection.id}`, token);
      
      showToast('Connection created successfully', 'success');
    }
    
    // Reload connections list
    await loadConnections();
    
    // Close modal
    closeConnectionModal();
    
  } catch (error) {
    let message = 'Failed to save connection';
    
    if (error.status === 409) {
      message = 'A connection with this name already exists';
    } else if (error.message) {
      message = error.message;
    } else if (error.error) {
      message = error.error;
    }
    
    showError(message, errorDiv);
    showToast(message, 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Load and display connections
 */
async function loadConnections() {
  showLoading();
  
  try {
    const connections = await connectionsAPI.getAll();
    appState.connections = connections;
    
    renderConnections(connections);
    
  } catch (error) {
    console.error('Failed to load connections', {error});
    showToast(getErrorMessage(error, 'Failed to load connections'), 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Render connections list
 */
function renderConnections(connections) {
  const container = document.getElementById('connections-list');
  
  if (connections.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No connections yet. Click "Add Connection" to get started.</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = connections.map(conn => `
    <div class="card" data-connection-id="${conn.id}">
      <div class="card-header">
        <h3>${escapeHtml(conn.name)}</h3>
        <span class="badge badge-${conn.is_active ? 'success' : 'inactive'}">
          ${conn.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>
      <div class="card-body">
        <p class="text-secondary">${escapeHtml(conn.server_url)}</p>
        ${conn.organization ? `<p class="text-small">Org: ${escapeHtml(conn.organization)}</p>` : ''}
        ${conn.server_version ? `<p class="text-small">Version: ${escapeHtml(conn.server_version)}</p>` : ''}
        ${conn.last_validated_at ? `<p class="text-small">Last validated: ${formatDate(conn.last_validated_at)}</p>` : '<p class="text-small text-warning">Not validated</p>'}
      </div>
      <div class="card-actions">
        <button class="btn btn-primary" onclick="openProjects(${conn.id})">Projects</button>
        <button class="btn btn-secondary" onclick="validateConnection(${conn.id})">Validate</button>
        <button class="btn btn-text" onclick="editConnection(${conn.id})">Edit</button>
        <button class="btn btn-text text-error" onclick="deleteConnection(${conn.id})">Delete</button>
      </div>
    </div>
  `).join('');
}

async function openProjects(connectionId) {
  const connection = appState.connections.find(conn => conn.id === connectionId);
  if (!connection) {
    showToast('Connection not found', 'error');
    return;
  }
  appState.currentConnection = connection;
  appState.projectPage = 1;
  await loadProjects(connectionId, 1);
  showSection('projects');
}

async function syncProjects() {
  if (!appState.currentConnection) {
    showToast('Select a connection first', 'error');
    return;
  }

  const token = getFromStorage(`connection_token_${appState.currentConnection.id}`);
  if (!token) {
    showToast('No token found for this connection', 'error');
    return;
  }

  showLoading();
  try {
    const result = await projectsAPI.sync(appState.currentConnection.id, token);
    const message = result.failed_count > 0
      ? `Synced with ${result.failed_count} failed projects`
      : 'Projects synced successfully';
    showToast(message, result.failed_count > 0 ? 'warning' : 'success');
    await loadProjects(appState.currentConnection.id, appState.projectPage);
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to sync projects'), 'error');
  } finally {
    hideLoading();
  }
}

async function loadProjects(connectionId, page = 1) {
  showLoading();
  try {
    const response = await projectsAPI.list(connectionId, {
      page,
      page_size: appState.projectPageSize,
      include_metrics: false
    });

    appState.projects = response.projects;
    appState.projectPage = response.pagination.page;
    appState.totalProjectPages = response.pagination.total_pages;

    document.getElementById('projects-page-info').textContent =
      `Page ${response.pagination.page} of ${response.pagination.total_pages}`;

    renderProjects(response.projects);
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to load projects'), 'error');
  } finally {
    hideLoading();
  }
}

function renderProjects(projects) {
  const container = document.getElementById('projects-list');
  const searchValue = document.getElementById('project-search').value.toLowerCase();

  const filtered = projects.filter(project => {
    const name = project.name.toLowerCase();
    const key = project.project_key.toLowerCase();
    return name.includes(searchValue) || key.includes(searchValue);
  });

  if (filtered.length === 0) {
    disableVirtualProjectList(container);
    container.innerHTML = `
      <div class="empty-state">
        <p>No projects found. Sync projects to load data.</p>
      </div>
    `;
    return;
  }

  if (filtered.length > 100) {
    renderProjectsVirtualized(container, filtered);
    return;
  }

  disableVirtualProjectList(container);

  container.innerHTML = filtered.map(project => buildProjectCardHtml(project)).join('');
}

function buildProjectCardHtml(project) {
  return `
    <div class="card" data-project-id="${project.id}">
      <div class="card-header">
        <h3>${escapeHtml(project.name)}</h3>
      </div>
      <div class="card-body">
        <p class="text-secondary">${escapeHtml(project.project_key)}</p>
        ${project.description ? `<p class="text-small">${escapeHtml(project.description)}</p>` : ''}
        ${project.last_analysis_date ? `<p class="text-small">Last analysis: ${formatDate(project.last_analysis_date)}</p>` : '<p class="text-small text-warning">No analysis data</p>'}
      </div>
      <div class="card-actions">
        <button class="btn btn-secondary" onclick="openProjectDetail(${project.id})">View Metrics</button>
      </div>
    </div>
  `;
}

function renderProjectsVirtualized(container, projects) {
  disableVirtualProjectList(container);
  container.classList.add('virtual-list');
  container.dataset.virtualized = 'true';
  container.scrollTop = 0;

  const spacer = document.createElement('div');
  spacer.className = 'virtual-spacer';
  spacer.style.height = `${projects.length * appState.virtualItemHeight}px`;

  const itemsContainer = document.createElement('div');
  itemsContainer.className = 'virtual-items';

  container.innerHTML = '';
  container.appendChild(spacer);
  container.appendChild(itemsContainer);

  const renderVisible = () => {
    const scrollTop = container.scrollTop;
    const viewportHeight = container.clientHeight;
    const buffer = 6;
    const startIndex = Math.max(0, Math.floor(scrollTop / appState.virtualItemHeight) - buffer);
    const endIndex = Math.min(
      projects.length,
      Math.ceil((scrollTop + viewportHeight) / appState.virtualItemHeight) + buffer
    );

    itemsContainer.innerHTML = '';

    for (let index = startIndex; index < endIndex; index += 1) {
      const wrapper = document.createElement('div');
      wrapper.className = 'virtual-item';
      wrapper.style.top = `${index * appState.virtualItemHeight}px`;
      wrapper.innerHTML = buildProjectCardHtml(projects[index]);
      itemsContainer.appendChild(wrapper);
    }
  };

  appState.virtualScrollHandler = renderVisible;
  container.addEventListener('scroll', renderVisible);
  renderVisible();
}

function disableVirtualProjectList(container) {
  if (appState.virtualScrollHandler) {
    container.removeEventListener('scroll', appState.virtualScrollHandler);
    appState.virtualScrollHandler = null;
  }
  container.classList.remove('virtual-list');
  delete container.dataset.virtualized;
}

async function openProjectDetail(projectId) {
  showLoading();
  try {
    const project = await projectsAPI.getById(projectId, true);
    appState.currentProject = project;

    document.getElementById('project-detail-title').textContent = project.name;
    updateBranchSelector(project.branches || ['main']);
    await loadProjectMetrics(projectId, document.getElementById('branch-selector').value);
    showSection('project-detail');
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to load project details'), 'error');
  } finally {
    hideLoading();
  }
}

function updateBranchSelector(branches) {
  const selector = document.getElementById('branch-selector');
  const safeBranches = branches.length ? branches : ['main'];
  selector.innerHTML = safeBranches.map(branch => `<option value="${branch}">${branch}</option>`).join('');
}

async function loadProjectMetrics(projectId, branch = 'main') {
  showLoading();
  try {
    const response = await metricsAPI.getMetrics(projectId, branch, 30);
    const snapshots = response.snapshots;

    renderMetricsTable(snapshots);
    updateStaleness(snapshots[0]);
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to load metrics'), 'error');
  } finally {
    hideLoading();
  }
}

function renderMetricsTable(snapshots) {
  const container = document.getElementById('project-metrics');
  if (!snapshots || snapshots.length === 0) {
    container.innerHTML = '<p class="text-secondary">No metrics snapshots yet.</p>';
    return;
  }

  const latest = snapshots[0];
  container.innerHTML = `
    <table class="metrics-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Bugs</td><td>${latest.bugs_count}</td></tr>
        <tr><td>Vulnerabilities</td><td>${latest.vulnerabilities_count}</td></tr>
        <tr><td>Code Smells</td><td>${latest.code_smells_count}</td></tr>
        <tr><td>Coverage</td><td>${latest.coverage_pct ?? 'N/A'}%</td></tr>
        <tr><td>Duplications</td><td>${latest.duplications_pct ?? 'N/A'}%</td></tr>
        <tr><td>Quality Gate</td><td>${latest.quality_gate_status}</td></tr>
        <tr><td>NCLOC</td><td>${latest.ncloc ?? 'N/A'}</td></tr>
      </tbody>
    </table>
  `;
}

function updateStaleness(latestSnapshot) {
  const stalenessDiv = document.getElementById('project-staleness');
  if (!latestSnapshot) {
    stalenessDiv.textContent = '';
    return;
  }
  const fetchTime = new Date(latestSnapshot.fetch_timestamp);
  const diffHours = Math.floor((Date.now() - fetchTime.getTime()) / (1000 * 60 * 60));
  if (diffHours >= 24) {
    stalenessDiv.innerHTML = `<span class="staleness-badge">Stale: ${diffHours}h ago</span>`;
  } else {
    stalenessDiv.textContent = `Last refreshed ${diffHours}h ago`;
  }
}

async function refreshMetrics() {
  if (!appState.currentProject || !appState.currentConnection) {
    showToast('Select a project first', 'error');
    return;
  }
  const token = getFromStorage(`connection_token_${appState.currentConnection.id}`);
  if (!token) {
    showToast('No token found for this connection', 'error');
    return;
  }

  const branch = document.getElementById('branch-selector').value;
  showLoading();
  try {
    await metricsAPI.refresh(appState.currentProject.id, token, branch);
    showToast('Metrics refreshed', 'success');
    await loadProjectMetrics(appState.currentProject.id, branch);
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to refresh metrics'), 'error');
  } finally {
    hideLoading();
  }
}

async function exportLatestMetrics(format) {
  if (!appState.currentProject) {
    showToast('Select a project first', 'error');
    return;
  }

  const branch = document.getElementById('branch-selector').value || 'main';
  const url = `${API_BASE_URL}/projects/${appState.currentProject.id}/metrics/export?format=${encodeURIComponent(format)}&branch=${encodeURIComponent(branch)}`;

  showLoading();
  try {
    const response = await fetch(url);

    if (!response.ok) {
      let errorPayload = null;
      try {
        errorPayload = await response.json();
      } catch (parseError) {
        errorPayload = null;
      }
      const message = getErrorMessage(errorPayload, 'Failed to export metrics');
      showToast(message, 'error');
      return;
    }

    const blob = await response.blob();
    const filename = getFilenameFromDisposition(
      response.headers.get('content-disposition'),
      `project_${appState.currentProject.id}_${branch}_latest_metrics.${format}`
    );
    triggerDownload(blob, filename);
    showToast('Export ready', 'success');
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to export metrics'), 'error');
  } finally {
    hideLoading();
  }
}

function showSection(section) {
  const connectionsSection = document.getElementById('connections-section');
  const projectsSection = document.getElementById('projects-section');
  const projectDetailSection = document.getElementById('project-detail-section');
  const dashboardSection = document.getElementById('dashboard-section');

  connectionsSection.classList.add('hidden');
  projectsSection.classList.add('hidden');
  projectDetailSection.classList.add('hidden');
  if (dashboardSection) dashboardSection.classList.add('hidden');

  if (section === 'connections') {
    connectionsSection.classList.remove('hidden');
  } else if (section === 'projects') {
    projectsSection.classList.remove('hidden');
  } else if (section === 'project-detail') {
    projectDetailSection.classList.remove('hidden');
  } else if (section === 'dashboard') {
    if (dashboardSection) dashboardSection.classList.remove('hidden');
  }
}

/**
 * Validate a connection
 */
async function validateConnection(connectionId) {
  const token = getFromStorage(`connection_token_${connectionId}`);
  
  if (!token) {
    showToast('No token found. Please edit connection and provide token.', 'error');
    return;
  }
  
  showLoading();
  
  try {
    const result = await connectionsAPI.validate(connectionId, token);
    
    showToast(`Connection validated! Server version: ${result.server_version}`, 'success');
    
    // Reload connections to show updated validation timestamp
    await loadConnections();
    
  } catch (error) {
    let message = 'Validation failed';
    
    if (error.status === 401) {
      message = 'Authentication failed. Token may be invalid or expired.';
    } else if (error.status === 503) {
      message = 'Cannot reach SonarQube server';
    } else if (error.message) {
      message = error.message;
    }
    
    showToast(message, 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Edit a connection
 */
async function editConnection(connectionId) {
  showLoading();
  
  try {
    const connection = await connectionsAPI.getById(connectionId);
    openConnectionModal(connection);
  } catch (error) {
    showToast('Failed to load connection details', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Delete a connection
 */
async function deleteConnection(connectionId) {
  if (!confirm('Are you sure you want to delete this connection?')) {
    return;
  }
  
  showLoading();
  
  try {
    await connectionsAPI.delete(connectionId);
    
    // Remove token from storage
    removeFromStorage(`connection_token_${connectionId}`);
    
    showToast('Connection deleted successfully', 'success');
    
    // Reload connections
    await loadConnections();
    
  } catch (error) {
    showToast(getErrorMessage(error, 'Failed to delete connection'), 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Show error in form
 */
function showError(message, errorDiv) {
  errorDiv.textContent = message;
  errorDiv.classList.remove('hidden');
}

function getErrorMessage(error, fallback) {
  if (!error) {
    return fallback;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error.message) {
    return error.message;
  }
  if (error.error) {
    return error.error;
  }
  if (error.details && error.details.message) {
    return error.details.message;
  }
  return fallback;
}

function getFilenameFromDisposition(disposition, fallback) {
  if (!disposition) {
    return fallback;
  }
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : fallback;
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Setup navigation listeners
 */
function setupNavigationListeners() {
  const navConnectionsBtn = document.getElementById('nav-connections-btn');
  const navProjectsBtn = document.getElementById('nav-projects-btn');
  const navDashboardBtn = document.getElementById('nav-dashboard-btn');
  
  if (navConnectionsBtn) {
    navConnectionsBtn.addEventListener('click', () => showSection('connections'));
  }
  
  if (navProjectsBtn) {
    navProjectsBtn.addEventListener('click', () => {
      if (appState.currentConnection) {
        showSection('projects');
        loadProjects(appState.currentConnection.id);
      } else {
        showToast('Please select a connection first', 'warning');
      }
    });
  }
  
  if (navDashboardBtn) {
    navDashboardBtn.addEventListener('click', async () => {
      showSection('dashboard');
      await loadDashboard();
    });
  }
}

/**
 * Setup dashboard event listeners
 */
function setupDashboardListeners() {
  const refreshDashboardBtn = document.getElementById('refresh-dashboard-btn');
  const connectionFilter = document.getElementById('dashboard-connection-filter');
  const timeRangeFilter = document.getElementById('dashboard-time-range');
  const filterCheckboxes = [
    'filter-bugs',
    'filter-vulnerabilities',
    'filter-code-smells',
    'filter-coverage',
    'filter-duplications'
  ];
  
  if (refreshDashboardBtn) {
    refreshDashboardBtn.addEventListener('click', async () => {
      await loadDashboard();
    });
  }
  
  if (connectionFilter) {
    connectionFilter.addEventListener('change', async () => {
      await loadDashboard();
    });
  }
  
  if (timeRangeFilter) {
    timeRangeFilter.addEventListener('change', async () => {
      await loadDashboard();
    });
  }
  
  // Setup filter checkboxes
  filterCheckboxes.forEach(id => {
    const checkbox = document.getElementById(id);
    if (checkbox) {
      checkbox.addEventListener('change', async () => {
        await loadDashboard();
      });
    }
  });
}

/**
 * Load dashboard data and render visualizations
 */
async function loadDashboard() {
  showLoading();
  
  try {
    // Build query parameters
    const connectionFilter = document.getElementById('dashboard-connection-filter');
    const params = {};
    
    if (connectionFilter && connectionFilter.value) {
      params.connection_id = connectionFilter.value;
    }
    
    // Fetch dashboard data
    const dashboardData = await api.get('/dashboard', params);
    
    // Render aggregate statistics
    renderDashboardAggregates(dashboardData.aggregates);
    
    // Render charts
    renderDashboardCharts(dashboardData.projects);
    
    // Render project cards
    renderDashboardProjectCards(dashboardData.projects);
    
    showToast('Dashboard loaded successfully', 'success');
    
  } catch (error) {
    console.error('Error loading dashboard:', error);
    showToast('Failed to load dashboard data', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Render dashboard aggregate statistics
 */
function renderDashboardAggregates(aggregates) {
  document.getElementById('stat-total-projects').textContent = aggregates.total_projects || '0';
  document.getElementById('stat-total-bugs').textContent = aggregates.total_bugs || '0';
  document.getElementById('stat-total-vulnerabilities').textContent = aggregates.total_vulnerabilities || '0';
  
  const avgCoverage = aggregates.avg_coverage !== null && aggregates.avg_coverage !== undefined
    ? `${aggregates.avg_coverage.toFixed(1)}%`
    : 'N/A';
  document.getElementById('stat-avg-coverage').textContent = avgCoverage;
  
  const qgPassRate = aggregates.quality_gate_pass_rate !== null && aggregates.quality_gate_pass_rate !== undefined
    ? `${aggregates.quality_gate_pass_rate.toFixed(1)}%`
    : 'N/A';
  document.getElementById('stat-qg-pass-rate').textContent = qgPassRate;
}

/**
 * Render dashboard charts
 */
function renderDashboardCharts(projects) {
  if (!projects || projects.length === 0) {
    return;
  }
  
  // Wait for Chart.js to be available
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded yet, retrying...');
    setTimeout(() => renderDashboardCharts(projects), 100);
    return;
  }
  
  // Prepare data for charts
  const projectsWithMetrics = projects
    .filter(p => p.latest_metrics)
    .map(p => ({
      name: p.project_name,
      project_name: p.project_name,
      bugs_count: p.latest_metrics.bugs_count,
      vulnerabilities_count: p.latest_metrics.vulnerabilities_count,
      code_smells_count: p.latest_metrics.code_smells_count,
      coverage_pct: p.latest_metrics.coverage_pct,
      duplications_pct: p.latest_metrics.duplications_pct,
      quality_gate_status: p.latest_metrics.quality_gate_status
    }));
  
  // Render project comparison chart
  if (typeof renderProjectComparisonChart === 'function') {
    renderProjectComparisonChart('dashboard-comparison-chart', projectsWithMetrics, {
      title: 'Project Metrics Comparison'
    });
  }
  
  // Render coverage chart (showing coverage for each project)
  if (typeof renderProjectComparisonChart === 'function') {
    const coverageData = projectsWithMetrics.map(p => ({
      name: p.name,
      project_name: p.name,
      coverage_pct: p.coverage_pct,
      bugs_count: 0,
      vulnerabilities_count: 0
    }));
    
    renderProjectComparisonChart('dashboard-coverage-chart', coverageData, {
      title: 'Code Coverage by Project'
    });
  }
  
  // Render quality gate chart (pie chart of statuses)
  if (typeof renderSeverityPieChart === 'function') {
    const qgCounts = {
      'OK': 0,
      'WARN': 0,
      'ERROR': 0
    };
    
    projectsWithMetrics.forEach(p => {
      const status = p.quality_gate_status || 'ERROR';
      if (qgCounts.hasOwnProperty(status)) {
        qgCounts[status]++;
      }
    });
    
    renderSeverityPieChart('dashboard-quality-gate-chart', qgCounts, {
      title: 'Quality Gate Status Distribution'
    });
  }
}

/**
 * Render dashboard project cards
 */
function renderDashboardProjectCards(projects) {
  const container = document.getElementById('dashboard-projects-grid');
  
  if (!projects || projects.length === 0) {
    container.innerHTML = '<p class="text-secondary">No projects available</p>';
    return;
  }
  
  container.innerHTML = projects
    .map(project => {
      const metrics = project.latest_metrics;
      
      if (!metrics) {
        return `
          <div class="project-card">
            <h4>${escapeHtml(project.project_name)}</h4>
            <p class="text-secondary">No metrics available</p>
          </div>
        `;
      }
      
      const qgClass = metrics.quality_gate_status === 'OK' ? 'badge-success' :
                      metrics.quality_gate_status === 'WARN' ? 'badge-warning' : 'badge-error';
      
      const stalenessHours = project.staleness_hours || 0;
      const stalenessClass = stalenessHours > 24 ? 'text-warning' : 'text-secondary';
      
      return `
        <div class="project-card" data-project-id="${project.project_id}">
          <div class="project-card-header">
            <h4>${escapeHtml(project.project_name)}</h4>
            <span class="badge ${qgClass}">${metrics.quality_gate_status}</span>
          </div>
          
          <div class="metrics-grid">
            <div class="metric-item">
              <span class="metric-label">Bugs</span>
              <span class="metric-value">${metrics.bugs_count || 0}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Vulnerabilities</span>
              <span class="metric-value">${metrics.vulnerabilities_count || 0}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Code Smells</span>
              <span class="metric-value">${metrics.code_smells_count || 0}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Coverage</span>
              <span class="metric-value">
                ${metrics.coverage_pct !== null ? metrics.coverage_pct.toFixed(1) + '%' : 'N/A'}
              </span>
            </div>
          </div>
          
          <div class="project-card-footer">
            <span class="${stalenessClass} text-small">
              Updated ${formatRelativeTime(stalenessHours)} ago
            </span>
          </div>
        </div>
      `;
    })
    .join('');
    
  // Add click listeners to project cards
  container.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('click', () => {
      const projectId = parseInt(card.dataset.projectId);
      const project = appState.projects.find(p => p.id === projectId);
      
      if (project) {
        appState.currentProject = project;
        showSection('project-detail');
        loadProjectMetrics(projectId);
      }
    });
  });
}

/**
 * Format relative time from hours
 */
function formatRelativeTime(hours) {
  if (hours < 1) {
    return `${Math.floor(hours * 60)} min`;
  } else if (hours < 24) {
    return `${Math.floor(hours)} hour${hours >= 2 ? 's' : ''}`;
  } else {
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? 's' : ''}`;
  }
}

/**
 * Load preferences from API
 */
async function loadPreferences() {
  try {
    const preferences = await api.get('/preferences');
    return preferences || {};
  } catch (error) {
    console.error('Error loading preferences:', error);
    return getDefaultPreferences();
  }
}

/**
 * Save preferences to API
 */
async function savePreferences(preferences) {
  try {
    await api.put('/preferences', preferences);
  } catch (error) {
    console.error('Error saving preferences:', error);
    showToast('Failed to save preferences', 'error');
  }
}

/**
 * Get default preferences
 */
function getDefaultPreferences() {
  return {
    theme: 'light',
    chart_type: 'line',
    time_range: '30d',
    page_size: 20,
    show_trends: true,
    dashboard_columns: 3
  };
}

