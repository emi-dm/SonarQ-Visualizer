/**
 * API Client for backend communication.
 * Handles all HTTP requests to the FastAPI backend with error handling.
 */

const API_BASE_URL = '/api/v1';

/**
 * Base fetch wrapper with error handling
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    // Handle successful responses with no content
    if (response.status === 204) {
      return null;
    }
    
    const data = await response.json();
    
    if (!response.ok) {
      throw {
        status: response.status,
        ...data
      };
    }
    
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

/**
 * API client for connections
 */
const connectionsAPI = {
  /**
   * Create a new connection
   * @param {Object} connectionData - Connection data
   * @returns {Promise<Object>} Created connection
   */
  async create(connectionData) {
    return apiFetch('/connections', {
      method: 'POST',
      body: JSON.stringify(connectionData)
    });
  },
  
  /**
   * Get all connections
   * @returns {Promise<Array>} List of connections
   */
  async getAll() {
    return apiFetch('/connections');
  },
  
  /**
   * Get connection by ID
   * @param {number} id - Connection ID
   * @returns {Promise<Object>} Connection details
   */
  async getById(id) {
    return apiFetch(`/connections/${id}`);
  },
  
  /**
   * Update connection
   * @param {number} id - Connection ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} Updated connection
   */
  async update(id, updates) {
    return apiFetch(`/connections/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  },
  
  /**
   * Delete connection
   * @param {number} id - Connection ID
   * @returns {Promise<void>}
   */
  async delete(id) {
    return apiFetch(`/connections/${id}`, {
      method: 'DELETE'
    });
  },
  
  /**
   * Validate connection
   * @param {number} id - Connection ID
   * @param {string} token - Authentication token
   * @returns {Promise<Object>} Validation result
   */
  async validate(id, token) {
    return apiFetch(`/connections/${id}/validate`, {
      method: 'POST',
      body: JSON.stringify({ token })
    });
  }
};

/**
 * API client for health check
 */
const healthAPI = {
  /**
   * Check API health
   * @returns {Promise<Object>} Health status
   */
  async check() {
    return apiFetch('/health');
  }
};
