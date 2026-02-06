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
  totalProjectPages: 1
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
  const prevBtn = document.getElementById('projects-prev-btn');
  const nextBtn = document.getElementById('projects-next-btn');
  const branchSelector = document.getElementById('branch-selector');

  syncProjectsBtn.addEventListener('click', async () => {
    await syncProjects();
  });

  projectSearch.addEventListener('input', () => {
    renderProjects(appState.projects);
  });

  backToProjectsBtn.addEventListener('click', () => {
    showSection('projects');
  });

  refreshMetricsBtn.addEventListener('click', async () => {
    await refreshMetrics();
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
    showToast('Failed to load connections', 'error');
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
    showToast(error.message || 'Failed to sync projects', 'error');
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
    showToast('Failed to load projects', 'error');
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
    container.innerHTML = `
      <div class="empty-state">
        <p>No projects found. Sync projects to load data.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(project => `
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
  `).join('');
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
    showToast('Failed to load project details', 'error');
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
    showToast('Failed to load metrics', 'error');
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
    showToast(error.message || 'Failed to refresh metrics', 'error');
  } finally {
    hideLoading();
  }
}

function showSection(section) {
  const connectionsSection = document.getElementById('connections-section');
  const projectsSection = document.getElementById('projects-section');
  const projectDetailSection = document.getElementById('project-detail-section');

  connectionsSection.classList.add('hidden');
  projectsSection.classList.add('hidden');
  projectDetailSection.classList.add('hidden');

  if (section === 'connections') {
    connectionsSection.classList.remove('hidden');
  } else if (section === 'projects') {
    projectsSection.classList.remove('hidden');
  } else if (section === 'project-detail') {
    projectDetailSection.classList.remove('hidden');
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
    showToast('Failed to delete connection', 'error');
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

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
