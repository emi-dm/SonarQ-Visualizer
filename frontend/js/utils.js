/**
 * Utility functions for DOM manipulation, date formatting, and localStorage operations.
 */

/**
 * Format date to human-readable string
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
  if (!date) {
    return 'N/A';
  }
  
  const d = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(d.getTime())) {
    return 'Invalid date';
  }
  
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format date to ISO string for API requests
 * @param {Date} date - Date to format
 * @returns {string} ISO formatted date string
 */
function formatDateISO(date) {
  return date.toISOString();
}

/**
 * Calculate human-readable staleness indicator
 * @param {string|Date} fetchTimestamp - When data was last fetched
 * @returns {string} Human-readable staleness (e.g., "2 hours ago")
 */
function calculateStaleness(fetchTimestamp) {
  if (!fetchTimestamp) {
    return 'Never';
  }
  
  const now = new Date();
  const fetched = typeof fetchTimestamp === 'string' ? new Date(fetchTimestamp) : fetchTimestamp;
  const diffMs = now - fetched;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) {
    return 'Just now';
  }
  if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  }
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  }
  return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
}

/**
 * Check if data is stale (older than 24 hours)
 * @param {string|Date} fetchTimestamp - When data was last fetched
 * @returns {boolean} True if data is stale
 */
function isStale(fetchTimestamp) {
  if (!fetchTimestamp) {
    return true;
  }
  
  const now = new Date();
  const fetched = typeof fetchTimestamp === 'string' ? new Date(fetchTimestamp) : fetchTimestamp;
  const diffHours = (now - fetched) / (1000 * 60 * 60);
  
  return diffHours > 24;
}

/**
 * Show loading overlay
 */
function showLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
  }
}

/**
 * Hide loading overlay
 */
function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.add('hidden');
  }
}

/**
 * Show error message in a container
 * @param {string} message - Error message to display
 * @param {HTMLElement} container - Container element to show error in
 */
function showError(message, container) {
  if (!container) {
    return;
  }
  container.textContent = message;
  container.classList.remove('hidden');
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) {
    return;
  }

  const toastColorByType = {
    error: '#DE350B',
    success: '#00875A',
    warning: '#FF8B00',
    info: '#0747A6'
  };
  const backgroundColor = toastColorByType[type] || toastColorByType.info;
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    padding: 1rem 1.5rem;
    background-color: ${backgroundColor};
    color: white;
    border-radius: 6px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    animation: slideIn 0.3s ease;
    cursor: pointer;
  `;
  
  container.appendChild(toast);
  
  // Remove toast on click
  toast.addEventListener('click', () => {
    toast.remove();
  });
  
  // Auto remove after duration
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        toast.remove();
      }, 300);
    }
  }, duration);
}

/**
 * Get item from localStorage
 * @param {string} key - Storage key
 * @returns {any} Parsed value or null
 */
function getFromStorage(key) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : null;
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return null;
  }
}

/**
 * Set item in localStorage
 * @param {string} key - Storage key
 * @param {any} value - Value to store (will be JSON stringified)
 */
function setInStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error writing to localStorage:', error);
  }
}

/**
 * Remove item from localStorage
 * @param {string} key - Storage key
 */
function removeFromStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing from localStorage:', error);
  }
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Create DOM element with attributes and children
 * @param {string} tag - HTML tag name
 * @param {Object} attrs - Attributes object
 * @param {Array|string} children - Child elements or text content
 * @returns {HTMLElement} Created element
 */
function createElement(tag, attrs = {}, children = []) {
  const element = document.createElement(tag);
  
  Object.entries(attrs).forEach(([key, value]) => {
    if (key === 'className') {
      element.className = value;
    } else if (key === 'dataset') {
      Object.entries(value).forEach(([dataKey, dataValue]) => {
        element.dataset[dataKey] = dataValue;
      });
    } else {
      element.setAttribute(key, value);
    }
  });
  
  if (typeof children === 'string') {
    element.textContent = children;
  } else if (Array.isArray(children)) {
    children.forEach(child => {
      if (typeof child === 'string') {
        element.appendChild(document.createTextNode(child));
      } else if (child instanceof HTMLElement) {
        element.appendChild(child);
      }
    });
  }
  
  return element;
}

/**
 * Format number with thousand separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
  if (num === null || num === undefined) {
    return 'N/A';
  }
  return num.toLocaleString('en-US');
}

/**
 * Format percentage
 * @param {number} pct - Percentage value
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted percentage
 */
function formatPercentage(pct, decimals = 2) {
  if (pct === null || pct === undefined) {
    return 'N/A';
  }
  return `${pct.toFixed(decimals)}%`;
}
