// Error Logs Page JavaScript (Updated for new structure, no Bootstrap)

// Page scrolling functions
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function scrollToBottom() {
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

// API call helper function
async function fetchAPI(url, options = {}) {
  try {
    const response = await fetch(url, options);

    // Handle cases where response might be empty but still ok (e.g., 204 No Content for DELETE)
    if (response.status === 204) {
      return null; // Indicate success with no content
    }

    let responseData;
    try {
      responseData = await response.json();
    } catch (e) {
      // Handle non-JSON responses if necessary, or assume error if JSON expected
      if (!response.ok) {
        // If response is not ok and not JSON, use statusText
        throw new Error(
          `HTTP error! status: ${response.status} - ${response.statusText}`
        );
      }
      // If response is ok but not JSON, maybe return raw text or handle differently
      // For now, let's assume successful non-JSON is not expected or handled later
      console.warn("Response was not JSON for URL:", url);
      return await response.text(); // Or handle as needed
    }

    if (!response.ok) {
      // Prefer error message from API response body if available
      const message =
        responseData?.detail ||
        `HTTP error! status: ${response.status} - ${response.statusText}`;
      throw new Error(message);
    }

    return responseData; // Return parsed JSON data for successful responses
  } catch (error) {
    // Catch network errors or errors thrown from above
    console.error(
      "API Call Failed:",
      error.message,
      "URL:",
      url,
      "Options:",
      options
    );
    // Re-throw the error so the calling function knows the operation failed
    throw error;
  }
}

// Refresh function removed as the buttons are gone.
// If refresh functionality is needed elsewhere, it can be triggered directly by calling loadErrorLogs().

// Global state management
let errorLogState = {
  currentPage: 1,
  pageSize: 10,
  logs: [], // Store retrieved logs
  sort: {
    field: "id", // Default sort by ID
    order: "desc", // Default descending order
  },
  search: {
    key: "",
    error: "",
    errorCode: "",
    startDate: "",
    endDate: "",
  },
};

// DOM Elements Cache
let pageSizeSelector;
// let refreshBtn; // Removed, as the button is deleted
let tableBody;
let paginationElement;
let loadingIndicator;
let noDataMessage;
let errorMessage;
let logDetailModal;
let modalCloseBtns; // Collection of close buttons for the modal
let keySearchInput;
let errorSearchInput;
let errorCodeSearchInput; // Added error code input
let startDateInput;
let endDateInput;
let searchBtn;
let pageInput;
let goToPageBtn;
let selectAllCheckbox; // Added: Select all checkbox
let copySelectedKeysBtn; // Added: Copy selected button
let deleteSelectedBtn; // Added: Bulk delete button
let sortByIdHeader; // Added: ID sort header
let sortIcon; // Added: Sort icon
let selectedCountSpan; // Added: Selected count display
let deleteConfirmModal; // Added: Delete confirmation modal
let closeDeleteConfirmModalBtn; // Added: Close delete modal button
let cancelDeleteBtn; // Added: Cancel delete button
let confirmDeleteBtn; // Added: Confirm delete button
let deleteConfirmMessage; // Added: Delete confirmation message element
let idsToDeleteGlobally = []; // Added: Store IDs to be deleted
let currentConfirmCallback = null; // Added: Store the current confirmation callback
let deleteAllLogsBtn; // Added: Clear all button

// Helper functions for initialization
function cacheDOMElements() {
  pageSizeSelector = document.getElementById("pageSize");
  tableBody = document.getElementById("errorLogsTable");
  paginationElement = document.getElementById("pagination");
  loadingIndicator = document.getElementById("loadingIndicator");
  noDataMessage = document.getElementById("noDataMessage");
  errorMessage = document.getElementById("errorMessage");
  logDetailModal = document.getElementById("logDetailModal");
  modalCloseBtns = document.querySelectorAll(
    "#closeLogDetailModalBtn, #closeModalFooterBtn"
  );
  keySearchInput = document.getElementById("keySearch");
  errorSearchInput = document.getElementById("errorSearch");
  errorCodeSearchInput = document.getElementById("errorCodeSearch");
  startDateInput = document.getElementById("startDate");
  endDateInput = document.getElementById("endDate");
  searchBtn = document.getElementById("searchBtn");
  pageInput = document.getElementById("pageInput");
  goToPageBtn = document.getElementById("goToPageBtn");
  selectAllCheckbox = document.getElementById("selectAllCheckbox");
  copySelectedKeysBtn = document.getElementById("copySelectedKeysBtn");
  deleteSelectedBtn = document.getElementById("deleteSelectedBtn");
  sortByIdHeader = document.getElementById("sortById");
  if (sortByIdHeader) {
    sortIcon = sortByIdHeader.querySelector("i");
  }
  selectedCountSpan = document.getElementById("selectedCount");
  deleteConfirmModal = document.getElementById("deleteConfirmModal");
  closeDeleteConfirmModalBtn = document.getElementById(
    "closeDeleteConfirmModalBtn"
  );
  cancelDeleteBtn = document.getElementById("cancelDeleteBtn");
  confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
  deleteConfirmMessage = document.getElementById("deleteConfirmMessage");
  deleteAllLogsBtn = document.getElementById("deleteAllLogsBtn"); // Cache clear all button
 }
  
 function initializePageSizeControls() {
  if (pageSizeSelector) {
    pageSizeSelector.value = errorLogState.pageSize;
    pageSizeSelector.addEventListener("change", function () {
      errorLogState.pageSize = parseInt(this.value);
      errorLogState.currentPage = 1; // Reset to first page
      loadErrorLogs();
    });
  }
}

function initializeSearchControls() {
  if (searchBtn) {
    searchBtn.addEventListener("click", function () {
      errorLogState.search.key = keySearchInput
        ? keySearchInput.value.trim()
        : "";
      errorLogState.search.error = errorSearchInput
        ? errorSearchInput.value.trim()
        : "";
      errorLogState.search.errorCode = errorCodeSearchInput
        ? errorCodeSearchInput.value.trim()
        : "";
      errorLogState.search.startDate = startDateInput
        ? startDateInput.value
        : "";
      errorLogState.search.endDate = endDateInput ? endDateInput.value : "";
      errorLogState.currentPage = 1; // Reset to first page on new search
      loadErrorLogs();
    });
  }
}

function initializeModalControls() {
  // Log Detail Modal
  if (logDetailModal && modalCloseBtns) {
    modalCloseBtns.forEach((btn) => {
      btn.addEventListener("click", closeLogDetailModal);
    });
    logDetailModal.addEventListener("click", function (event) {
      if (event.target === logDetailModal) {
        closeLogDetailModal();
      }
    });
  }

  // Delete Confirm Modal
  if (closeDeleteConfirmModalBtn) {
    closeDeleteConfirmModalBtn.addEventListener(
      "click",
      hideDeleteConfirmModal
    );
  }
  if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener("click", hideDeleteConfirmModal);
  }
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", handleConfirmDelete);
  }
  if (deleteConfirmModal) {
    deleteConfirmModal.addEventListener("click", function (event) {
      if (event.target === deleteConfirmModal) {
        hideDeleteConfirmModal();
      }
    });
  }
}

function initializePaginationJumpControls() {
  if (goToPageBtn && pageInput) {
    goToPageBtn.addEventListener("click", function () {
      const targetPage = parseInt(pageInput.value);
      if (!isNaN(targetPage) && targetPage >= 1) {
        errorLogState.currentPage = targetPage;
        loadErrorLogs();
        pageInput.value = "";
      } else {
        showNotification("Please enter a valid page number", "error", 2000);
        pageInput.value = "";
      }
    });
    pageInput.addEventListener("keypress", function (event) {
      if (event.key === "Enter") {
        goToPageBtn.click();
      }
    });
  }
}

function initializeActionControls() {
  if (deleteSelectedBtn) {
    deleteSelectedBtn.addEventListener("click", handleDeleteSelected);
  }
  if (sortByIdHeader) {
    sortByIdHeader.addEventListener("click", handleSortById);
  }
  // Bulk selection listeners are closely related to actions
  setupBulkSelectionListeners();
  
   // Add event listener for "Clear All" button
   if (deleteAllLogsBtn) {
     deleteAllLogsBtn.addEventListener("click", function() {
       const message = "Are you sure you want to clear all error logs? This action cannot be undone!";
       showDeleteConfirmModal(message, handleDeleteAllLogs); // Pass callback
     });
   }
 }
  
 // Added: Function to handle "Clear All" logic
 async function handleDeleteAllLogs() {
   const url = "/api/logs/errors/all";
   const options = {
     method: "DELETE",
   };
 
   try {
     await fetchAPI(url, options);
     showNotification("Successfully cleared all error logs", "success");
     if (selectAllCheckbox) selectAllCheckbox.checked = false; // Deselect all
     loadErrorLogs(); // Reload logs
   } catch (error) {
     console.error("Failed to clear all error logs:", error);
     showNotification(`Failed to clear: ${error.message}`, "error", 5000);
   }
 }
  
 // Execute when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  cacheDOMElements();
  initializePageSizeControls();
  initializeSearchControls();
  initializeModalControls();
  initializePaginationJumpControls();
  initializeActionControls();

  // Initial load of error logs
  loadErrorLogs();

  // Add event listeners for copy buttons inside the modal and table
  // This needs to be called after initial render and potentially after each render if content is dynamic
  setupCopyButtons();
});

// Added: Show delete confirmation modal
function showDeleteConfirmModal(message, confirmCallback) {
  if (deleteConfirmModal && deleteConfirmMessage) {
    deleteConfirmMessage.textContent = message;
    currentConfirmCallback = confirmCallback; // Store callback
    deleteConfirmModal.classList.add("show");
    document.body.style.overflow = "hidden"; // Prevent body scrolling
  }
}
 
// Added: Hide delete confirmation modal
function hideDeleteConfirmModal() {
  if (deleteConfirmModal) {
    deleteConfirmModal.classList.remove("show");
    document.body.style.overflow = ""; // Restore body scrolling
    idsToDeleteGlobally = []; // Clear IDs to be deleted
    currentConfirmCallback = null; // Clear callback
  }
}
 
// Added: Handle confirm delete button click
function handleConfirmDelete() {
  if (typeof currentConfirmCallback === 'function') {
    currentConfirmCallback(); // Call stored callback
  }
  hideDeleteConfirmModal(); // Close modal
}
 
// Fallback copy function using document.execCommand
function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;

  // Avoid scrolling to bottom
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.position = "fixed";

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  let successful = false;
  try {
    successful = document.execCommand("copy");
  } catch (err) {
    console.error("Fallback copy failed:", err);
    successful = false;
  }

  document.body.removeChild(textArea);
  return successful;
}

// Helper function to handle feedback after copy attempt (both modern and fallback)
function handleCopyResult(buttonElement, success) {
  const originalIcon = buttonElement.querySelector("i").className; // Store original icon class
  const iconElement = buttonElement.querySelector("i");
  if (success) {
    iconElement.className = "fas fa-check text-success-500"; // Use checkmark icon class
    showNotification("Successfully copied to clipboard", "success", 2000);
  } else {
    iconElement.className = "fas fa-times text-danger-500"; // Use error icon class
    showNotification("Copy failed", "error", 3000);
  }
  setTimeout(
    () => {
      iconElement.className = originalIcon;
    },
    success ? 2000 : 3000
  ); // Restore original icon class
}

// New internal helper function to encapsulate the actual copy operation and feedback
function _performCopy(text, buttonElement) {
  let copySuccess = false;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        if (buttonElement) {
          handleCopyResult(buttonElement, true);
        } else {
          showNotification("Successfully copied to clipboard", "success");
        }
      })
      .catch((err) => {
        console.error("Clipboard API failed, attempting fallback:", err);
        copySuccess = fallbackCopyTextToClipboard(text);
        if (buttonElement) {
          handleCopyResult(buttonElement, copySuccess);
        } else {
          showNotification(
            copySuccess ? "Successfully copied to clipboard" : "Copy failed",
            copySuccess ? "success" : "error"
          );
        }
      });
  } else {
    console.warn(
      "Clipboard API not available or context insecure. Using fallback copy method."
    );
    copySuccess = fallbackCopyTextToClipboard(text);
    if (buttonElement) {
      handleCopyResult(buttonElement, copySuccess);
    } else {
      showNotification(
        copySuccess ? "Successfully copied to clipboard" : "Copy failed",
        copySuccess ? "success" : "error"
      );
    }
  }
}

// Function to set up copy button listeners (using modern API with fallback) - Updated to handle table copy buttons
function setupCopyButtons(containerSelector = "body") {
  // Find buttons within the specified container (defaults to body)
  const container = document.querySelector(containerSelector);
  if (!container) return;

  const copyButtons = container.querySelectorAll(".copy-btn");
  copyButtons.forEach((button) => {
    // Remove existing listener to prevent duplicates if called multiple times
    button.removeEventListener("click", handleCopyButtonClick);
    // Add the listener
    button.addEventListener("click", handleCopyButtonClick);
  });
}

// Extracted click handler logic for reusability and removing listeners
function handleCopyButtonClick() {
  const button = this; // 'this' refers to the button clicked
  const targetId = button.getAttribute("data-target");
  const textToCopyDirect = button.getAttribute("data-copy-text"); // For direct text copy (e.g., table key)
  let textToCopy = "";

  if (textToCopyDirect) {
    textToCopy = textToCopyDirect;
  } else if (targetId) {
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      textToCopy = targetElement.textContent;
    } else {
      console.error("Target element not found:", targetId);
      showNotification("Copy error: Target element not found", "error");
      return; // Exit if target element not found
    }
  } else {
    console.error(
      "No data-target or data-copy-text attribute found on button:",
      button
    );
    showNotification("Copy error: Source not specified", "error");
    return; // Exit if no source specified
  }

  if (textToCopy) {
    _performCopy(textToCopy, button); // Use the new helper function
  } else {
    console.warn(
      "No text found to copy for target:",
      targetId || "direct text"
    );
    showNotification("No content to copy", "warning");
  }
}

// Added: Set up event listeners for bulk selection
function setupBulkSelectionListeners() {
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener("change", handleSelectAllChange);
  }

  if (tableBody) {
    // Use event delegation to handle row checkbox clicks
    tableBody.addEventListener("change", handleRowCheckboxChange);
  }

  if (copySelectedKeysBtn) {
    copySelectedKeysBtn.addEventListener("click", handleCopySelectedKeys);
  }

  // Added: Add event listener for bulk delete button (if not already added)
  // Usually added once in DOMContentLoaded
  // if (deleteSelectedBtn && !deleteSelectedBtn.hasListener) {
  //     deleteSelectedBtn.addEventListener('click', handleDeleteSelected);
  //     deleteSelectedBtn.hasListener = true; // Mark as added
  // }
}

// Added: Function to handle "Select All" checkbox changes
function handleSelectAllChange() {
  const isChecked = selectAllCheckbox.checked;
  const rowCheckboxes = tableBody.querySelectorAll(".row-checkbox");
  rowCheckboxes.forEach((checkbox) => {
    checkbox.checked = isChecked;
  });
  updateSelectedState();
}

// Added: Function to handle row checkbox changes (event delegation)
function handleRowCheckboxChange(event) {
  if (event.target.classList.contains("row-checkbox")) {
    updateSelectedState();
  }
}

// Added: Update selection state (count, button state, select all checkbox state)
function updateSelectedState() {
  const rowCheckboxes = tableBody.querySelectorAll(".row-checkbox");
  const selectedCheckboxes = tableBody.querySelectorAll(
    ".row-checkbox:checked"
  );
  const selectedCount = selectedCheckboxes.length;

  // Removed number display, no longer updating selectedCountSpan
  // Still update the disabled state of the copy button
  if (copySelectedKeysBtn) {
    copySelectedKeysBtn.disabled = selectedCount === 0;

    // Optional: Update button title attribute based on the number of selected items
    copySelectedKeysBtn.setAttribute("title", `Copy ${selectedCount} selected key(s)`);
  }
  // Added: Update the disabled state of the bulk delete button
  if (deleteSelectedBtn) {
    deleteSelectedBtn.disabled = selectedCount === 0;
    deleteSelectedBtn.setAttribute("title", `Delete ${selectedCount} selected log(s)`);
  }

  // Update the state of the "Select All" checkbox
  if (selectAllCheckbox) {
    if (rowCheckboxes.length > 0 && selectedCount === rowCheckboxes.length) {
      selectAllCheckbox.checked = true;
      selectAllCheckbox.indeterminate = false;
    } else if (selectedCount > 0) {
      selectAllCheckbox.checked = false;
      selectAllCheckbox.indeterminate = true; // Indeterminate state
    } else {
      selectAllCheckbox.checked = false;
      selectAllCheckbox.indeterminate = false;
    }
  }
}

// Added: Function to handle "Copy Selected Keys" button click
function handleCopySelectedKeys() {
  const selectedCheckboxes = tableBody.querySelectorAll(
    ".row-checkbox:checked"
  );
  const keysToCopy = [];
  selectedCheckboxes.forEach((checkbox) => {
    const key = checkbox.getAttribute("data-key");
    if (key) {
      keysToCopy.push(key);
    }
  });

  if (keysToCopy.length > 0) {
    const textToCopy = keysToCopy.join("\n"); // One key per line
    _performCopy(textToCopy, copySelectedKeysBtn); // Use the new helper function
  } else {
    showNotification("No selected keys to copy", "warning");
  }
}

// Modified: Function to handle bulk delete button click - changed to show modal
function handleDeleteSelected() {
  const selectedCheckboxes = tableBody.querySelectorAll(
    ".row-checkbox:checked"
  );
  const logIdsToDelete = [];
  selectedCheckboxes.forEach((checkbox) => {
    const logId = checkbox.getAttribute("data-log-id"); // Need to add data-log-id during rendering
    if (logId) {
      logIdsToDelete.push(parseInt(logId));
    }
  });

  if (logIdsToDelete.length === 0) {
    showNotification("No selected logs to delete", "warning");
    return;
  }

  if (logIdsToDelete.length === 0) {
    showNotification("No selected logs to delete", "warning");
    return;
  }

  // Store IDs to be deleted and show modal
  idsToDeleteGlobally = logIdsToDelete; // Still need to set, because performActualDelete will use it
  const message = `Are you sure you want to delete the ${logIdsToDelete.length} selected logs? This action cannot be undone!`;
  showDeleteConfirmModal(message, function() { // Pass anonymous callback
    performActualDelete(idsToDeleteGlobally);
  });
}
 
// Added: Perform the actual delete operation (extracted from the original handleDeleteSelected and handleDeleteLogRow)
async function performActualDelete(logIds) {
  if (!logIds || logIds.length === 0) return;

  const isSingleDelete = logIds.length === 1;
  const url = isSingleDelete
    ? `/api/logs/errors/${logIds[0]}`
    : "/api/logs/errors";
  const method = "DELETE";
  const body = isSingleDelete ? null : JSON.stringify({ ids: logIds });
  const headers = isSingleDelete ? {} : { "Content-Type": "application/json" };
  const options = {
    method: method,
    headers: headers,
    body: body, // fetchAPI handles null body correctly
  };

  try {
    // Use fetchAPI for the delete request
    await fetchAPI(url, options); // fetchAPI returns null for 204 No Content

    // If fetchAPI doesn't throw, the request was successful
    const successMessage = isSingleDelete
      ? `Successfully deleted the log`
      : `Successfully deleted ${logIds.length} logs`;
    showNotification(successMessage, "success");
    // Deselect all
    if (selectAllCheckbox) selectAllCheckbox.checked = false;
    // Reload current page data
    loadErrorLogs();
  } catch (error) {
    console.error("Failed to bulk delete error logs:", error);
    showNotification(`Bulk delete failed: ${error.message}`, "error", 5000);
  }
}

// Modified: Function to handle single row delete button click - changed to show modal
function handleDeleteLogRow(logId) {
  if (!logId) return;

  // Store ID to be deleted and show modal
  idsToDeleteGlobally = [parseInt(logId)]; // Store as an array // Still need to set, because performActualDelete will use it
  // Use a generic confirmation message without showing the specific ID
  const message = `Are you sure you want to delete this log? This action cannot be undone!`;
  showDeleteConfirmModal(message, function() { // Pass anonymous callback
    performActualDelete([parseInt(logId)]); // Make sure to pass an array
  });
}
 
// Added: Function to handle ID sort click
function handleSortById() {
  if (errorLogState.sort.field === "id") {
    // If currently sorting by ID, switch order
    errorLogState.sort.order =
      errorLogState.sort.order === "asc" ? "desc" : "asc";
  } else {
    // If not currently sorting by ID, switch to sorting by ID, default to descending
    errorLogState.sort.field = "id";
    errorLogState.sort.order = "desc";
  }
  // Update icon
  updateSortIcon();
  // Reload first page data
  errorLogState.currentPage = 1;
  loadErrorLogs();
}

// Added: Function to update sort icon
function updateSortIcon() {
  if (!sortIcon) return;
  // Remove all possible sort classes
  sortIcon.classList.remove(
    "fa-sort",
    "fa-sort-up",
    "fa-sort-down",
    "text-gray-400",
    "text-primary-600"
  );

  if (errorLogState.sort.field === "id") {
    sortIcon.classList.add(
      errorLogState.sort.order === "asc" ? "fa-sort-up" : "fa-sort-down"
    );
    sortIcon.classList.add("text-primary-600"); // Highlight
  } else {
    // If not sorting by ID, show default icon
    sortIcon.classList.add("fa-sort", "text-gray-400");
  }
}

// Load error log data
async function loadErrorLogs() {
  // Reset selection state
  if (selectAllCheckbox) selectAllCheckbox.checked = false;
  if (selectAllCheckbox) selectAllCheckbox.indeterminate = false;
  updateSelectedState(); // Update button states and counts

  showLoading(true);
  showError(false);
  showNoData(false);

  const offset = (errorLogState.currentPage - 1) * errorLogState.pageSize;

  try {
    // Construct the API URL with search and sort parameters
    let apiUrl = `/api/logs/errors?limit=${errorLogState.pageSize}&offset=${offset}`;
    // Add sort parameters
    apiUrl += `&sort_by=${errorLogState.sort.field}&sort_order=${errorLogState.sort.order}`;

    // Add search parameters
    if (errorLogState.search.key) {
      apiUrl += `&key_search=${encodeURIComponent(errorLogState.search.key)}`;
    }
    if (errorLogState.search.error) {
      apiUrl += `&error_search=${encodeURIComponent(
        errorLogState.search.error
      )}`;
    }
    if (errorLogState.search.errorCode) {
      // Add error code to API request
      apiUrl += `&error_code_search=${encodeURIComponent(
        errorLogState.search.errorCode
      )}`;
    }
    if (errorLogState.search.startDate) {
      apiUrl += `&start_date=${encodeURIComponent(
        errorLogState.search.startDate
      )}`;
    }
    if (errorLogState.search.endDate) {
      apiUrl += `&end_date=${encodeURIComponent(errorLogState.search.endDate)}`;
    }

    // Use fetchAPI to get logs
    const data = await fetchAPI(apiUrl);

    // API now returns { logs: [], total: count }
    // fetchAPI already parsed JSON
    if (data && Array.isArray(data.logs)) {
      errorLogState.logs = data.logs; // Store the list data (contains error_code)
      renderErrorLogs(errorLogState.logs);
      updatePagination(errorLogState.logs.length, data.total || -1); // Use total from response
    } else {
      // Handle unexpected data format even after successful fetch
      console.error("Unexpected API response format:", data);
      throw new Error("Unrecognized API response format");
    }

    showLoading(false);

    if (errorLogState.logs.length === 0) {
      showNoData(true);
    }
  } catch (error) {
    console.error("Failed to get error logs:", error);
    showLoading(false);
    showError(true, error.message); // Show specific error message
  }
}

// Helper function to create HTML for a single log row
function _createLogRowHtml(log, sequentialId) {
  // Format date
  let formattedTime = "N/A";
  try {
    const requestTime = new Date(log.request_time);
    if (!isNaN(requestTime)) {
      formattedTime = requestTime.toLocaleString("en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      });
    }
  } catch (e) {
    console.error("Error formatting date:", e);
  }

  const errorCodeContent = log.error_code || "None";

  const maskKey = (key) => {
    if (!key || key.length < 8) return key || "None";
    return `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
  };
  const maskedKey = maskKey(log.gemini_key);
  const fullKey = log.gemini_key || "";

  return `
        <td class="text-center px-3 py-3 text-gray-700">
            <input type="checkbox" class="row-checkbox form-checkbox h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" data-key="${fullKey}" data-log-id="${
    log.id
  }">
        </td>
        <td class="text-gray-700">${sequentialId}</td>
        <td class="relative group text-gray-700" title="${fullKey}">
            ${maskedKey}
            <button class="copy-btn absolute top-1/2 right-2 transform -translate-y-1/2 bg-gray-200 hover:bg-gray-300 text-gray-600 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity text-xs" data-copy-text="${fullKey}" title="Copy full key">
                <i class="far fa-copy"></i>
            </button>
        </td>
        <td class="text-gray-700">${log.error_type || "Unknown"}</td>
        <td class="error-code-content text-gray-700" title="${
          log.error_code || ""
        }">${errorCodeContent}</td>
        <td class="text-gray-700">${log.model_name || "Unknown"}</td>
        <td class="text-gray-700">${formattedTime}</td>
        <td>
            <button class="btn-view-details mr-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-all duration-200" data-log-id="${log.id}">
                <i class="fas fa-eye mr-1"></i>Details
            </button>
            <button class="btn-delete-row bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-sm transition-all duration-200" data-log-id="${
              log.id
            }" title="Delete this log">
                <i class="fas fa-trash-alt"></i>
            </button>
        </td>
    `;
}

// Render error log table
function renderErrorLogs(logs) {
  if (!tableBody) return;
  tableBody.innerHTML = ""; // Clear previous entries

  // Reset the state of the select all checkbox (after clearing the table)
  if (selectAllCheckbox) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  }

  if (!logs || logs.length === 0) {
    // Handled by showNoData
    return;
  }

  const startIndex = (errorLogState.currentPage - 1) * errorLogState.pageSize;

  logs.forEach((log, index) => {
    const sequentialId = startIndex + index + 1;
    const row = document.createElement("tr");
    row.innerHTML = _createLogRowHtml(log, sequentialId);
    tableBody.appendChild(row);
  });

  // Add event listeners to new 'View Details' buttons
  document.querySelectorAll(".btn-view-details").forEach((button) => {
    button.addEventListener("click", function () {
      const logId = parseInt(this.getAttribute("data-log-id"));
      showLogDetails(logId);
    });
  });

  // Added: Add event listener for newly rendered delete buttons
  document.querySelectorAll(".btn-delete-row").forEach((button) => {
    button.addEventListener("click", function () {
      const logId = this.getAttribute("data-log-id");
      handleDeleteLogRow(logId);
    });
  });

  // Re-initialize copy buttons specifically for the newly rendered table rows
  setupCopyButtons("#errorLogsTable");
  // Update selected state after rendering
  updateSelectedState();
}

// Show error log details (get from API)
async function showLogDetails(logId) {
  if (!logDetailModal) return;

  // Show loading state in modal (optional)
  // Clear previous content and show a spinner or message
  document.getElementById("modalGeminiKey").textContent = "Loading...";
  document.getElementById("modalErrorType").textContent = "Loading...";
  document.getElementById("modalErrorLog").textContent = "Loading...";
  document.getElementById("modalRequestMsg").textContent = "Loading...";
  document.getElementById("modalModelName").textContent = "Loading...";
  document.getElementById("modalRequestTime").textContent = "Loading...";

  logDetailModal.classList.add("show");
  document.body.style.overflow = "hidden"; // Prevent body scrolling

  try {
    // Use fetchAPI to get log details
    const logDetails = await fetchAPI(`/api/logs/errors/${logId}/details`);

    // fetchAPI handles response.ok check and JSON parsing
    if (!logDetails) {
      // Handle case where API returns success but no data (if possible)
      throw new Error("Log details not found");
    }

    // Format date
    let formattedTime = "N/A";
    try {
      const requestTime = new Date(logDetails.request_time);
      if (!isNaN(requestTime)) {
        formattedTime = requestTime.toLocaleString("en-US", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        });
      }
    } catch (e) {
      console.error("Error formatting date:", e);
    }

    // Format request message (handle potential JSON)
    let formattedRequestMsg = "None";
    if (logDetails.request_msg) {
      try {
        if (
          typeof logDetails.request_msg === "object" &&
          logDetails.request_msg !== null
        ) {
          formattedRequestMsg = JSON.stringify(logDetails.request_msg, null, 2);
        } else if (typeof logDetails.request_msg === "string") {
          // Try parsing if it looks like JSON, otherwise display as string
          const trimmedMsg = logDetails.request_msg.trim();
          if (trimmedMsg.startsWith("{") || trimmedMsg.startsWith("[")) {
            formattedRequestMsg = JSON.stringify(
              JSON.parse(logDetails.request_msg),
              null,
              2
            );
          } else {
            formattedRequestMsg = logDetails.request_msg;
          }
        } else {
          formattedRequestMsg = String(logDetails.request_msg);
        }
      } catch (e) {
        formattedRequestMsg = String(logDetails.request_msg); // Fallback
        console.warn("Could not parse request_msg as JSON:", e);
      }
    }

    // Populate modal content with fetched details
    document.getElementById("modalGeminiKey").textContent =
      logDetails.gemini_key || "None";
    document.getElementById("modalErrorType").textContent =
      logDetails.error_type || "Unknown";
    document.getElementById("modalErrorLog").textContent =
      logDetails.error_log || "None"; // Full error log
    document.getElementById("modalRequestMsg").textContent =
      formattedRequestMsg; // Full request message
    document.getElementById("modalModelName").textContent =
      logDetails.model_name || "Unknown";
    document.getElementById("modalRequestTime").textContent = formattedTime;

    // Re-initialize copy buttons specifically for the modal after content is loaded
    setupCopyButtons("#logDetailModal");
  } catch (error) {
    console.error("Failed to get log details:", error);
    // Show error in modal
    document.getElementById("modalGeminiKey").textContent = "Error";
    document.getElementById("modalErrorType").textContent = "Error";
    document.getElementById(
      "modalErrorLog"
    ).textContent = `Loading failed: ${error.message}`;
    document.getElementById("modalRequestMsg").textContent = "Error";
    document.getElementById("modalModelName").textContent = "Error";
    document.getElementById("modalRequestTime").textContent = "Error";
    // Optionally show a notification
    showNotification(`Failed to load log details: ${error.message}`, "error", 5000);
  }
}

// Close Log Detail Modal
function closeLogDetailModal() {
  if (logDetailModal) {
    logDetailModal.classList.remove("show");
    // Optional: Restore body scrolling
    document.body.style.overflow = "";
  }
}

// Update pagination controls
function updatePagination(currentItemCount, totalItems) {
  if (!paginationElement) return;
  paginationElement.innerHTML = ""; // Clear existing pagination

  // Calculate total pages only if totalItems is known and valid
  let totalPages = 1;
  if (totalItems >= 0) {
    totalPages = Math.max(1, Math.ceil(totalItems / errorLogState.pageSize));
  } else if (
    currentItemCount < errorLogState.pageSize &&
    errorLogState.currentPage === 1
  ) {
    // If less items than page size fetched on page 1, assume it's the only page
    totalPages = 1;
  } else {
    // If total is unknown and more items might exist, we can't build full pagination
    // We can show Prev/Next based on current page and if items were returned
    console.warn("Total item count unknown, pagination will be limited.");
    // Basic Prev/Next for unknown total
    addPaginationLink(
      paginationElement,
      "«",
      errorLogState.currentPage > 1,
      () => {
        errorLogState.currentPage--;
        loadErrorLogs();
      }
    );
    addPaginationLink(
      paginationElement,
      errorLogState.currentPage.toString(),
      true,
      null,
      true
    ); // Current page number (non-clickable)
    addPaginationLink(
      paginationElement,
      "»",
      currentItemCount === errorLogState.pageSize,
      () => {
        errorLogState.currentPage++;
        loadErrorLogs();
      }
    ); // Next enabled if full page was returned
    return; // Exit here for limited pagination
  }

  const maxPagesToShow = 5; // Max number of page links to show
  let startPage = Math.max(
    1,
    errorLogState.currentPage - Math.floor(maxPagesToShow / 2)
  );
  let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

  // Adjust startPage if endPage reaches the limit first
  if (endPage === totalPages) {
    startPage = Math.max(1, endPage - maxPagesToShow + 1);
  }

  // Previous Button
  addPaginationLink(
    paginationElement,
    "«",
    errorLogState.currentPage > 1,
    () => {
      errorLogState.currentPage--;
      loadErrorLogs();
    }
  );

  // First Page Button
  if (startPage > 1) {
    addPaginationLink(paginationElement, "1", true, () => {
      errorLogState.currentPage = 1;
      loadErrorLogs();
    });
    if (startPage > 2) {
      addPaginationLink(paginationElement, "...", false); // Ellipsis
    }
  }

  // Page Number Buttons
  for (let i = startPage; i <= endPage; i++) {
    addPaginationLink(
      paginationElement,
      i.toString(),
      true,
      () => {
        errorLogState.currentPage = i;
        loadErrorLogs();
      },
      i === errorLogState.currentPage
    );
  }

  // Last Page Button
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      addPaginationLink(paginationElement, "...", false); // Ellipsis
    }
    addPaginationLink(paginationElement, totalPages.toString(), true, () => {
      errorLogState.currentPage = totalPages;
      loadErrorLogs();
    });
  }

  // Next Button
  addPaginationLink(
    paginationElement,
    "»",
    errorLogState.currentPage < totalPages,
    () => {
      errorLogState.currentPage++;
      loadErrorLogs();
    }
  );
}

// Helper function to add pagination links
function addPaginationLink(
  parentElement,
  text,
  enabled,
  clickHandler,
  isActive = false
) {
  // const pageItem = document.createElement('li'); // We are not using <li> anymore

  const pageLink = document.createElement("a");

  // Base Tailwind classes for layout, size, and transition. Colors/borders will come from CSS.
  let baseClasses =
    "px-3 py-1 rounded-md text-sm transition duration-150 ease-in-out"; // Common classes

  if (isActive) {
    pageLink.className = `${baseClasses} active`; // Add 'active' class for CSS
  } else if (enabled) {
    pageLink.className = baseClasses; // Just base classes, CSS handles the rest
  } else {
    // Disabled link (e.g., '...' or unavailable prev/next)
    pageLink.className = `${baseClasses} disabled`; // Add 'disabled' class for CSS
  }

  pageLink.href = "#"; // Prevent page jump
  pageLink.innerHTML = text;

  if (enabled && clickHandler) {
    pageLink.addEventListener("click", function (e) {
      e.preventDefault();
      clickHandler();
    });
  } else {
    // Handles !enabled (includes isActive as clickHandler is null for it, and '...' which has no clickHandler)
    pageLink.addEventListener("click", (e) => e.preventDefault());
  }

  parentElement.appendChild(pageLink); // Directly append <a> to the <ul>
}

// Show/hide status indicator (using 'active' class)
function showLoading(show) {
  if (loadingIndicator)
    loadingIndicator.style.display = show ? "block" : "none";
}

function showNoData(show) {
  if (noDataMessage) noDataMessage.style.display = show ? "block" : "none";
}

function showError(show, message = "Failed to load error logs, please try again later.") {
  if (errorMessage) {
    errorMessage.style.display = show ? "block" : "none";
    if (show) {
      // Update the error message content
      const p = errorMessage.querySelector("p");
      if (p) p.textContent = message;
    }
  }
}

// Function to show temporary status notifications (like copy success)
function showNotification(message, type = "success", duration = 3000) {
  const notificationElement = document.getElementById("notification"); // Use the correct ID from base.html
  if (!notificationElement) {
    console.error("Notification element with ID 'notification' not found.");
    return;
  }

  // Set message and type class
  notificationElement.textContent = message;
  // Remove previous type classes before adding the new one
  notificationElement.classList.remove("success", "error", "warning", "info");
  notificationElement.classList.add(type); // Add the type class for styling
  notificationElement.className = `notification ${type} show`; // Add 'show' class

  // Hide after duration
  setTimeout(() => {
    notificationElement.classList.remove("show");
  }, duration);
}

// Example Usage (if copy functionality is added later):
// showNotification('Key copied!', 'success');
// showNotification('Copy failed!', 'error');