/**
 * Main application logic for SonarQube Report Visualizer.
 * Handles UI interactions, state management, and API communication.
 */

// Application state
const appState = {
  connections: [],
  currentConnection: null,
  currentProject: null
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
  
  // Load connections
  await loadConnections();
  
  showLoading();
  hideLoading();
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
  
  showLoading();
  
  try {
    if (editId) {
      // Update existing connection
      const connection = await connectionsAPI.update(parseInt(editId), {
        name: name,
        server_url: serverUrl
      });
      
      // Update token in storage
      setInStorage(`connection_token_${connection.id}`, token);
      
      showToast('Connection updated successfully', 'success');
    } else {
      // Create new connection
      const connection = await connectionsAPI.create({
        name: name,
        server_url: serverUrl,
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
        ${conn.server_version ? `<p class="text-small">Version: ${escapeHtml(conn.server_version)}</p>` : ''}
        ${conn.last_validated_at ? `<p class="text-small">Last validated: ${formatDate(conn.last_validated_at)}</p>` : '<p class="text-small text-warning">Not validated</p>'}
      </div>
      <div class="card-actions">
        <button class="btn btn-secondary" onclick="validateConnection(${conn.id})">Validate</button>
        <button class="btn btn-text" onclick="editConnection(${conn.id})">Edit</button>
        <button class="btn btn-text text-error" onclick="deleteConnection(${conn.id})">Delete</button>
      </div>
    </div>
  `).join('');
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
