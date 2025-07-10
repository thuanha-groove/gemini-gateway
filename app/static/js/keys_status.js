// Statistical data visualization interaction effects

function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  } else {
    return new Promise((resolve, reject) => {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        const successful = document.execCommand("copy");
        document.body.removeChild(textArea);
        if (successful) {
          resolve();
        } else {
          reject(new Error("Copy failed"));
        }
      } catch (err) {
        document.body.removeChild(textArea);
        reject(err);
      }
    });
  }
}

// API call helper function (similar to the version in error_logs.js)
async function fetchAPI(url, options = {}) {
  try {
    const response = await fetch(url, options);

    if (response.status === 204) {
      return null; // Indicate success with no content for DELETE etc.
    }

    let responseData;
    try {
      // Clone the response to allow reading it multiple times if needed (e.g., for text fallback)
      const clonedResponse = response.clone();
      responseData = await response.json();
    } catch (e) {
      // If JSON parsing fails, try to get text, especially if response wasn't ok
      if (!response.ok) {
        const textResponse = await response.text(); // Use original response for text
        throw new Error(
          textResponse ||
            `HTTP error! status: ${response.status} - ${response.statusText}`
        );
      }
      // If response is ok but not JSON, maybe return raw text or handle differently
      console.warn("Response was not JSON for URL:", url);
      // Consider returning text or null based on expected non-JSON success cases
      return await response.text(); // Example: return text for non-JSON success
    }

    if (!response.ok) {
      // Prefer error message from API response body (already parsed as JSON)
      const message =
        responseData?.detail ||
        responseData?.message ||
        responseData?.error ||
        `HTTP error! status: ${response.status}`;
      throw new Error(message);
    }

    return responseData; // Return parsed JSON data
  } catch (error) {
    console.error(
      "API Call Failed:",
      error.message,
      "URL:",
      url,
      "Options:",
      options
    );
    // Re-throw the error so the calling function knows the operation failed
    // Add more context if possible
    throw new Error(`API request failed: ${error.message}`);
  }
}

// Add animation effects to statistical items
function initStatItemAnimations() {
  const statItems = document.querySelectorAll(".stat-item");
  statItems.forEach((item) => {
    item.addEventListener("mouseenter", () => {
      item.style.transform = "scale(1.05)";
      const icon = item.querySelector(".stat-icon");
      if (icon) {
        icon.style.opacity = "0.2";
        icon.style.transform = "scale(1.1) rotate(0deg)";
      }
    });

    item.addEventListener("mouseleave", () => {
      item.style.transform = "";
      const icon = item.querySelector(".stat-icon");
      if (icon) {
        icon.style.opacity = "";
        icon.style.transform = "";
      }
    });
  });
}

// Get selected keys in the specified type area
function getSelectedKeys(type) {
  const checkboxes = document.querySelectorAll(
    `#${type}Keys .key-checkbox:checked`
  );
  return Array.from(checkboxes).map((cb) => cb.value);
}

// Update the status and count of batch operation buttons in the specified type area
function updateBatchActions(type) {
  const selectedKeys = getSelectedKeys(type);
  const count = selectedKeys.length;
  const batchActionsDiv = document.getElementById(`${type}BatchActions`);
  const selectedCountSpan = document.getElementById(`${type}SelectedCount`);
  const buttons = batchActionsDiv.querySelectorAll("button");

  if (count > 0) {
    batchActionsDiv.classList.remove("hidden");
    selectedCountSpan.textContent = count;
    buttons.forEach((button) => (button.disabled = false));
  } else {
    batchActionsDiv.classList.add("hidden");
    selectedCountSpan.textContent = "0";
    buttons.forEach((button) => (button.disabled = true));
  }

  // Update the select all checkbox state
  const selectAllCheckbox = document.getElementById(
    `selectAll${type.charAt(0).toUpperCase() + type.slice(1)}`
  );
  const allCheckboxes = document.querySelectorAll(`#${type}Keys .key-checkbox`);
  // Only consider the select all state when there are visible keys
  const visibleCheckboxes = document.querySelectorAll(
    `#${type}Keys li:not([style*="display: none"]) .key-checkbox`
  );
  if (selectAllCheckbox && visibleCheckboxes.length > 0) {
    selectAllCheckbox.checked = count === visibleCheckboxes.length;
    selectAllCheckbox.indeterminate =
      count > 0 && count < visibleCheckboxes.length;
  } else if (selectAllCheckbox) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  }
}

// Select all/deselect all keys of the specified type
function toggleSelectAll(type, isChecked) {
  const listElement = document.getElementById(`${type}Keys`);
  // Select checkboxes within LI elements that are NOT styled with display:none
  // This targets currently visible items based on filtering.
  const visibleCheckboxes = listElement.querySelectorAll(
    `li:not([style*="display: none"]) .key-checkbox`
  );

  visibleCheckboxes.forEach((checkbox) => {
    checkbox.checked = isChecked;
    const listItem = checkbox.closest("li[data-key]"); // Get the LI from the current DOM
    if (listItem) {
      listItem.classList.toggle("selected", isChecked);

      // Sync with master array
      const key = listItem.dataset.key;
      const masterList = type === "valid" ? allValidKeys : allInvalidKeys;
      if (masterList) {
        // Ensure masterList is defined
        const masterListItem = masterList.find((li) => li.dataset.key === key);
        if (masterListItem) {
          const masterCheckbox = masterListItem.querySelector(".key-checkbox");
          if (masterCheckbox) {
            masterCheckbox.checked = isChecked;
          }
        }
      }
    }
  });
  updateBatchActions(type);
}

// Copy selected keys
function copySelectedKeys(type) {
  const selectedKeys = getSelectedKeys(type);

  if (selectedKeys.length === 0) {
    showNotification("No keys selected to copy", "warning");
    return;
  }

  const keysText = selectedKeys.join("\n");

  copyToClipboard(keysText)
    .then(() => {
      showNotification(
        `Successfully copied ${selectedKeys.length} selected ${
          type === "valid" ? "valid" : "invalid"
        } keys`
      );
    })
    .catch((err) => {
      console.error("Could not copy text: ", err);
      showNotification("Copy failed, please try again", "error");
    });
}

// Single copy remains unchanged
function copyKey(key) {
  copyToClipboard(key)
    .then(() => {
      showNotification(`Successfully copied key`);
    })
    .catch((err) => {
      console.error("Could not copy text: ", err);
      showNotification("Copy failed, please try again", "error");
    });
}

// The showCopyStatus function is obsolete.

async function verifyKey(key, button) {
  try {
    // Disable the button and display the loading status
    button.disabled = true;
    const originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying';

    try {
      const data = await fetchAPI(`/gemini/v1beta/verify-key/${key}`, {
        method: "POST",
      });

      // Update the UI and display a modal prompt box based on the verification result
      if (data && (data.success || data.status === "valid")) {
        // Verification successful, display success result
        button.style.backgroundColor = "#27ae60";
        // Use the result modal to display a success message
        showResultModal(true, "Key verification successful");
        // The page will automatically refresh when the modal is closed
      } else {
        // Verification failed, display failure result
        const errorMsg = data.error || "Invalid key";
        button.style.backgroundColor = "#e74c3c";
        // Use the result modal to display a failure message, change to true to refresh when closed
        showResultModal(false, "Key verification failed: " + errorMsg, true);
      }
    } catch (apiError) {
      console.error("Key verification API request failed:", apiError);
      showResultModal(false, `Verification request failed: ${apiError.message}`, true);
    } finally {
      // The logic for restoring the original state of the button has been moved to the success/failure branch
      setTimeout(() => {
        if (
          !document.getElementById("resultModal") ||
          document.getElementById("resultModal").classList.contains("hidden")
        ) {
          button.innerHTML = originalHtml;
          button.disabled = false;
          button.style.backgroundColor = "";
        }
      }, 1000);
    }
  } catch (error) {
    console.error("Verification failed:", error);
    // Ensure that the button state is restored when an error is caught (if the page is not refreshed)
    // button.disabled = false; // Handled by finally or not needed due to refresh
    // button.innerHTML = '<i class="fas fa-check-circle"></i> Verify';
    showResultModal(false, "Verification processing failed: " + error.message, true); // Change to true to refresh when closed
  }
}

async function resetKeyFailCount(key, button) {
  try {
    // Disable the button and display the loading status
    button.disabled = true;
    const originalHtml = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting';

    const data = await fetchAPI(`/gemini/v1beta/reset-fail-count/${key}`, {
      method: "POST",
    });

    // Update the UI based on the reset result
    if (data.success) {
      showNotification("Failure count reset successfully");
      // Keep the green background for a while on success
      button.style.backgroundColor = "#27ae60";
      // Refresh the page later
      setTimeout(() => location.reload(), 1000);
    } else {
      const errorMsg = data.message || "Reset failed";
      showNotification("Reset failed: " + errorMsg, "error");
      // Keep the red background for a while on failure
      button.style.backgroundColor = "#e74c3c";
      // If it fails, restore the button after 1 second
      setTimeout(() => {
        button.innerHTML = originalHtml;
        button.disabled = false;
        button.style.backgroundColor = "";
      }, 1000);
    }

    // The logic for restoring the button state has been moved to the success/failure branch
  } catch (apiError) {
    console.error("Reset failed:", apiError);
    showNotification(`Reset request failed: ${apiError.message}`, "error");
    // Ensure that the button state is restored when an error is caught
    button.disabled = false;
    button.innerHTML = '<i class="fas fa-redo-alt"></i> Reset'; // Restore original icon and text
    button.style.backgroundColor = ""; // Clear any background color that may have been set
  }
}

// Show reset confirmation modal (based on selected keys)
function showResetModal(type) {
  const modalElement = document.getElementById("resetModal");
  const titleElement = document.getElementById("resetModalTitle");
  const messageElement = document.getElementById("resetModalMessage");
  const confirmButton = document.getElementById("confirmResetBtn");

  const selectedKeys = getSelectedKeys(type);
  const count = selectedKeys.length;

  // Set title and message
  titleElement.textContent = "Batch Reset Failure Count";
  if (count > 0) {
    messageElement.textContent = `Are you sure you want to batch reset the failure count for ${count} selected ${
      type === "valid" ? "valid" : "invalid"
    } keys?`;
    confirmButton.disabled = false; // Make sure the button is available
  } else {
    // This should not happen in theory, because the button is disabled when not selected
    messageElement.textContent = `Please select the ${
      type === "valid" ? "valid" : "invalid"
    } keys to reset first.`;
    confirmButton.disabled = true;
  }

  // Set confirm button event
  confirmButton.onclick = () => executeResetAll(type);

  // Show modal
  modalElement.classList.remove("hidden");
}

function closeResetModal() {
  document.getElementById("resetModal").classList.add("hidden");
}

// Trigger show modal
function resetAllKeysFailCount(type, event) {
  // Prevent event bubbling
  if (event) {
    event.stopPropagation();
  }

  // Show modal confirmation box
  showResetModal(type);
}

// Close the modal and decide whether to refresh the page based on the parameters
function closeResultModal(reload = true) {
  document.getElementById("resultModal").classList.add("hidden");
  if (reload) {
    location.reload(); // Refresh the page after the operation is complete
  }
}

// Show operation result modal (general version)
function showResultModal(success, message, autoReload = true) {
  const modalElement = document.getElementById("resultModal");
  const titleElement = document.getElementById("resultModalTitle");
  const messageElement = document.getElementById("resultModalMessage");
  const iconElement = document.getElementById("resultIcon");
  const confirmButton = document.getElementById("resultModalConfirmBtn");

  // Set title
  titleElement.textContent = success ? "Operation Successful" : "Operation Failed";

  // Set icon
  if (success) {
    iconElement.innerHTML =
      '<i class="fas fa-check-circle text-success-500"></i>';
    iconElement.className = "text-6xl mb-3 text-success-500"; // Slightly increase the icon size
  } else {
    iconElement.innerHTML =
      '<i class="fas fa-times-circle text-danger-500"></i>';
    iconElement.className = "text-6xl mb-3 text-danger-500"; // Slightly increase the icon size
  }

  // Clear existing content and set a new message
  messageElement.innerHTML = ""; // Clear
  if (typeof message === "string") {
    // For normal string messages, keep the original logic
    const messageDiv = document.createElement("div");
    messageDiv.innerText = message; // Use innerText to prevent XSS
    messageElement.appendChild(messageDiv);
  } else if (message instanceof Node) {
    // If a DOM node is passed in, add it directly
    messageElement.appendChild(message);
  } else {
    // Convert other types to strings
    const messageDiv = document.createElement("div");
    messageDiv.innerText = String(message);
    messageElement.appendChild(messageDiv);
  }

  // Set confirm button click event
  confirmButton.onclick = () => closeResultModal(autoReload);

  // Show modal
  modalElement.classList.remove("hidden");
}

// Show dedicated modal for batch verification results
function showVerificationResultModal(data) {
  const modalElement = document.getElementById("resultModal");
  const titleElement = document.getElementById("resultModalTitle");
  const messageElement = document.getElementById("resultModalMessage");
  const iconElement = document.getElementById("resultIcon");
  const confirmButton = document.getElementById("resultModalConfirmBtn");

  const successfulKeys = data.successful_keys || [];
  const failedKeys = data.failed_keys || {};
  const validCount = data.valid_count || 0;
  const invalidCount = data.invalid_count || 0;

  // Set title and icon
  titleElement.textContent = "Batch Verification Results";
  if (invalidCount === 0 && validCount > 0) {
    iconElement.innerHTML =
      '<i class="fas fa-check-double text-success-500"></i>';
    iconElement.className = "text-6xl mb-3 text-success-500";
  } else if (invalidCount > 0 && validCount > 0) {
    iconElement.innerHTML =
      '<i class="fas fa-exclamation-triangle text-warning-500"></i>';
    iconElement.className = "text-6xl mb-3 text-warning-500";
  } else if (invalidCount > 0 && validCount === 0) {
    iconElement.innerHTML =
      '<i class="fas fa-times-circle text-danger-500"></i>';
    iconElement.className = "text-6xl mb-3 text-danger-500";
  } else {
    // All are 0 or other cases
    iconElement.innerHTML = '<i class="fas fa-info-circle text-gray-500"></i>';
    iconElement.className = "text-6xl mb-3 text-gray-500";
  }

  // Build detailed content
  messageElement.innerHTML = ""; // Clear

  const summaryDiv = document.createElement("div");
  summaryDiv.className = "text-center mb-4 text-lg";
  summaryDiv.innerHTML = `Verification complete: <span class="font-semibold text-success-600">${validCount}</span> successful, <span class="font-semibold text-danger-600">${invalidCount}</span> failed.`;
  messageElement.appendChild(summaryDiv);

  // Success list
  if (successfulKeys.length > 0) {
    const successDiv = document.createElement("div");
    successDiv.className = "mb-3";
    const successHeader = document.createElement("div");
    successHeader.className = "flex justify-between items-center mb-1";
    successHeader.innerHTML = `<h4 class="font-semibold text-success-700">Successful Keys (${successfulKeys.length}):</h4>`;

    const copySuccessBtn = document.createElement("button");
    copySuccessBtn.className =
      "px-2 py-0.5 bg-green-100 hover:bg-green-200 text-green-700 text-xs rounded transition-colors";
    copySuccessBtn.innerHTML = '<i class="fas fa-copy mr-1"></i>Copy All';
    copySuccessBtn.onclick = (e) => {
      e.stopPropagation();
      copyToClipboard(successfulKeys.join("\n"))
        .then(() =>
          showNotification(
            `Copied ${successfulKeys.length} successful keys`,
            "success"
          )
        )
        .catch(() => showNotification("Copy failed", "error"));
    };
    successHeader.appendChild(copySuccessBtn);
    successDiv.appendChild(successHeader);

    const successList = document.createElement("ul");
    successList.className =
      "list-disc list-inside text-sm text-gray-600 max-h-20 overflow-y-auto bg-gray-50 p-2 rounded border border-gray-200";
    successfulKeys.forEach((key) => {
      const li = document.createElement("li");
      li.className = "font-mono";
      // Store full key in dataset for potential future use, display masked
      li.dataset.fullKey = key;
      li.textContent =
        key.substring(0, 4) + "..." + key.substring(key.length - 4);
      successList.appendChild(li);
    });
    successDiv.appendChild(successList);
    messageElement.appendChild(successDiv);
  }

  // Failure list
  if (Object.keys(failedKeys).length > 0) {
    const failDiv = document.createElement("div");
    failDiv.className = "mb-1"; // Reduce bottom margin
    const failHeader = document.createElement("div");
    failHeader.className = "flex justify-between items-center mb-1";
    failHeader.innerHTML = `<h4 class="font-semibold text-danger-700">Failed Keys (${
      Object.keys(failedKeys).length
    }):</h4>`;

    const copyFailBtn = document.createElement("button");
    copyFailBtn.className =
      "px-2 py-0.5 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded transition-colors";
    copyFailBtn.innerHTML = '<i class="fas fa-copy mr-1"></i>Copy All';
    const failedKeysArray = Object.keys(failedKeys); // Get array of failed keys
    copyFailBtn.onclick = (e) => {
      e.stopPropagation();
      copyToClipboard(failedKeysArray.join("\n"))
        .then(() =>
          showNotification(
            `Copied ${failedKeysArray.length} failed keys`,
            "success"
          )
        )
        .catch(() => showNotification("Copy failed", "error"));
    };
    failHeader.appendChild(copyFailBtn);
    failDiv.appendChild(failHeader);

    const failList = document.createElement("ul");
    failList.className =
      "text-sm text-gray-600 max-h-32 overflow-y-auto bg-red-50 p-2 rounded border border-red-200 space-y-1"; // Increase max height and spacing
    Object.entries(failedKeys).forEach(([key, error]) => {
      const li = document.createElement("li");
      // li.className = 'flex justify-between items-center'; // Restore original layout
      li.className = "flex flex-col items-start"; // Start with vertical layout

      const keySpanContainer = document.createElement("div");
      keySpanContainer.className = "flex justify-between items-center w-full"; // Ensure key and button are on the same line initially

      const keySpan = document.createElement("span");
      keySpan.className = "font-mono";
      // Store full key in dataset, display masked
      keySpan.dataset.fullKey = key;
      keySpan.textContent =
        key.substring(0, 4) + "..." + key.substring(key.length - 4);

      const detailsButton = document.createElement("button");
      detailsButton.className =
        "ml-2 px-2 py-0.5 bg-red-200 hover:bg-red-300 text-red-700 text-xs rounded transition-colors";
      detailsButton.innerHTML = '<i class="fas fa-info-circle mr-1"></i>Details';
      detailsButton.dataset.error = error; // Store the error message in the data attribute
      detailsButton.onclick = (e) => {
        e.stopPropagation(); // Prevent modal close
        const button = e.currentTarget;
        const listItem = button.closest("li");
        const errorMsg = button.dataset.error;
        const errorDetailsId = `error-details-${key.replace(
          /[^a-zA-Z0-9]/g,
          ""
        )}`; // Create unique ID
        let errorDiv = listItem.querySelector(`#${errorDetailsId}`);

        if (errorDiv) {
          // Collapse: Remove error div and reset li layout
          errorDiv.remove();
          // listItem.className = 'flex justify-between items-center'; // Restore original layout
          listItem.className = "flex flex-col items-start"; // Keep vertical layout
          button.innerHTML = '<i class="fas fa-info-circle mr-1"></i>Details'; // Restore button text
        } else {
          // Expand: Create and append error div, change li layout
          errorDiv = document.createElement("div");
          errorDiv.id = errorDetailsId;
          errorDiv.className =
            "w-full mt-1 pl-0 text-xs text-red-600 bg-red-50 p-1 rounded border border-red-100 whitespace-pre-wrap break-words"; // Adjusted padding
          errorDiv.textContent = errorMsg;
          listItem.appendChild(errorDiv);
          listItem.className = "flex flex-col items-start"; // Change layout to vertical
          button.innerHTML = '<i class="fas fa-chevron-up mr-1"></i>Collapse'; // Change button text
          // Move button to be alongside the keySpan for vertical layout (already done)
        }
      };

      keySpanContainer.appendChild(keySpan); // Add keySpan to container
      keySpanContainer.appendChild(detailsButton); // Add button to container
      li.appendChild(keySpanContainer); // Add container to list item
      failList.appendChild(li);
    });
    failDiv.appendChild(failList);
    messageElement.appendChild(failDiv);
  }

  // Set confirm button click event - always refresh automatically
  confirmButton.onclick = () => closeResultModal(true); // Always reload

  // Show modal
  modalElement.classList.remove("hidden");
}

async function executeResetAll(type) {
  try {
    // Close confirmation modal
    closeResetModal();

    // Find the corresponding reset button to display the loading status
    const resetButton = document.querySelector(
      `button[data-reset-type="${type}"]`
    );
    if (!resetButton) {
      showResultModal(
        false,
        `Could not find the batch reset button for the ${type === "valid" ? "valid" : "invalid"} keys area.`,
        false
      ); // Don't reload if button not found
      return;
    }

    // Get selected keys
    const keysToReset = getSelectedKeys(type);

    if (keysToReset.length === 0) {
      showNotification(
        `No selected ${type === "valid" ? "valid" : "invalid"} keys to reset.`,
        "warning"
      );
      return;
    }

    // Disable the button and display the loading status
    resetButton.disabled = true;
    const originalHtml = resetButton.innerHTML;
    resetButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting';

    try {
      const options = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys: keysToReset, key_type: type }),
      };
      const data = await fetchAPI(
        `/gemini/v1beta/reset-selected-fail-counts`,
        options
      );

      // Show modal based on reset result
      if (data.success) {
        const message =
          data.reset_count !== undefined
            ? `Successfully reset failure count for ${data.reset_count} selected ${
                type === "valid" ? "valid" : "invalid"
              } keys.`
            : `Successfully reset ${keysToReset.length} selected keys.`;
        showResultModal(true, message); // Refresh the page on success
      } else {
        const errorMsg = data.message || "Batch reset failed";
        // Do not automatically refresh the page after failure, so that the user can see the error message
        showResultModal(false, "Batch reset failed: " + errorMsg, false);
      }
    } catch (apiError) {
      console.error("Batch reset API request failed:", apiError);
      showResultModal(false, `Batch reset request failed: ${apiError.message}`, false);
    } finally {
      // Restore button state (only when not refreshing)
      if (
        !document.getElementById("resultModal") ||
        document.getElementById("resultModal").classList.contains("hidden") ||
        document.getElementById("resultModalTitle").textContent.includes("Failed")
      ) {
        resetButton.innerHTML = originalHtml;
        resetButton.disabled = false;
      }
    }
  } catch (error) {
    console.error("Batch reset processing failed:", error);
    showResultModal(false, "Batch reset processing failed: " + error.message, false); // Do not automatically refresh on failure
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function scrollToBottom() {
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

// Remove this function as it may be interfering with the display of the button
// The scroll button is already set to flex display in HTML, no additional JavaScript control is needed
// function updateScrollButtons() {
//     // Do nothing
// }

function refreshPage(button) {
  button.classList.add("loading"); // Maybe add a loading class for visual feedback
  button.disabled = true;
  const icon = button.querySelector("i");
  if (icon) icon.classList.add("fa-spin"); // Add spin animation

  setTimeout(() => {
    window.location.reload();
    // No need to remove loading/spin as page reloads
  }, 300);
}

// Function to expand/collapse block content with smooth animation effect.
// @param {HTMLElement} header - The clicked block header element.
// @param {string} sectionId - (Currently unused, but can be used for more precise targeting) The ID of the associated content block.
function toggleSection(header, sectionId) {
  const toggleIcon = header.querySelector(".toggle-icon");
  // The content element is the .key-content div inside the card
  const card = header.closest(".stats-card");
  const content = card ? card.querySelector(".key-content") : null;

  // Batch operation bar and pagination controls may also affect the animation height calculation of the content area
  const batchActions = card ? card.querySelector('[id$="BatchActions"]') : null;
  const pagination = card
    ? card.querySelector('[id$="PaginationControls"]')
    : null;

  if (!toggleIcon || !content) {
    console.error(
      "Toggle section failed: Icon or content element not found. Header:",
      header,
      "SectionId:",
      sectionId
    );
    return;
  }

  const isCollapsed = content.classList.contains("collapsed");
  toggleIcon.classList.toggle("collapsed", !isCollapsed); // Update arrow icon direction

  if (isCollapsed) {
    // --- Prepare for expansion animation ---
    content.classList.remove("collapsed"); // Remove collapsed class to apply expanded styles

    // Step 1: Reset inline styles to let CSS control the initial "hidden" state (usually maxHeight: 0, opacity: 0).
    //         At the same time, make sure overflow is hidden before the animation starts.
    content.style.maxHeight = ""; // Clear any existing inline maxHeight
    content.style.opacity = ""; // Clear any existing inline opacity
    content.style.paddingTop = ""; // Clear inline padding
    content.style.paddingBottom = "";
    content.style.overflow = "hidden"; // Hide overflowing content during animation

    // Step 2: Use requestAnimationFrame (rAF) to ensure that the browser calculates scrollHeight before
    //         the style reset from the previous step has been applied (especially if there are transition effects in CSS).
    requestAnimationFrame(() => {
      // Step 3: Calculate the target height of the content area.
      //         This includes the scrollHeight of the content itself, as well as the height of any visible batch operation bars and pagination controls.
      let targetHeight = content.scrollHeight;

      if (batchActions && !batchActions.classList.contains("hidden")) {
        targetHeight += batchActions.offsetHeight;
      }
      if (pagination && pagination.offsetHeight > 0) {
        // Try to get the margin-top of the pagination control to get a more accurate height
        const paginationStyle = getComputedStyle(pagination);
        const paginationMarginTop = parseFloat(paginationStyle.marginTop) || 0;
        targetHeight += pagination.offsetHeight + paginationMarginTop;
      }

      // Step 4: Set maxHeight and opacity to trigger the CSS transition to the expanded state.
      content.style.maxHeight = targetHeight + "px";
      content.style.opacity = "1";
      // Assume the padding after expansion is 1rem (p-4 in Tailwind). Adjust according to the actual situation.
      content.style.paddingTop = "1rem";
      content.style.paddingBottom = "1rem";

      // Step 5: Listen for the transitionend event. After the animation ends, remove maxHeight to allow the content to adjust dynamically,
      //         and set overflow to visible to prevent the content from being cropped after changes.
      content.addEventListener(
        "transitionend",
        function onExpansionEnd() {
          content.removeEventListener("transitionend", onExpansionEnd); // Clean up listener
          // Double check to make sure it is in the expanded state (to avoid errors when clicking quickly in succession)
          if (!content.classList.contains("collapsed")) {
            content.style.maxHeight = ""; // Allow content to adapt to height
            content.style.overflow = "visible"; // Allow content to overflow (if needed)
          }
        },
        { once: true }
      ); // Make sure the listener only executes once
    });
  } else {
    // --- Prepare for collapse animation ---
    // Step 1: Get the visible height of the current content area.
    //         This is necessary for a smooth transition from the current rendering height to 0.
    let currentVisibleHeight = content.scrollHeight; // scrollHeight should already be the internal height including padding
    if (batchActions && !batchActions.classList.contains("hidden")) {
      currentVisibleHeight += batchActions.offsetHeight;
    }
    if (pagination && pagination.offsetHeight > 0) {
      const paginationStyle = getComputedStyle(pagination);
      const paginationMarginTop = parseFloat(paginationStyle.marginTop) || 0;
      currentVisibleHeight += pagination.offsetHeight + paginationMarginTop;
    }

    // Step 2: Set maxHeight to the currently calculated visible height to ensure that the transition starts from the current height.
    //         At the same time, make sure overflow is hidden before the animation starts.
    content.style.maxHeight = currentVisibleHeight + "px";
    content.style.overflow = "hidden";

    // Step 3: Use requestAnimationFrame (rAF) to ensure that the browser has applied the above maxHeight.
    requestAnimationFrame(() => {
      // Step 4: Transition to the target state (collapsed): maxHeight and padding are set to 0, opacity is set to 0.
      content.style.maxHeight = "0px";
      content.style.opacity = "0";
      content.style.paddingTop = "0";
      content.style.paddingBottom = "0";
      // Add the collapsed class after the animation starts (or is about to start) so that CSS can apply the final collapsed style.
      content.classList.add("collapsed");
    });
  }
}

// Filter valid keys (based on failure count threshold) and update batch operation status
function filterValidKeys() {
  const thresholdInput = document.getElementById("failCountThreshold");
  const validKeysList = document.getElementById("validKeys"); // Get the UL element
  if (!validKeysList) return; // Exit if the list doesn't exist

  const validKeyItems = validKeysList.querySelectorAll("li[data-key]"); // Select li elements within the list
  // Read the threshold, if the input is invalid or empty, it defaults to 0 (no filtering)
  const threshold = parseInt(thresholdInput.value, 10);
  const filterThreshold = isNaN(threshold) || threshold < 0 ? 0 : threshold;
  let hasVisibleItems = false;

  validKeyItems.forEach((item) => {
    // Make sure to only process li elements that contain data-fail-count
    if (item.dataset.failCount !== undefined) {
      const failCount = parseInt(item.dataset.failCount, 10);
      // If the number of failures is greater than or equal to the threshold, it will be displayed, otherwise it will be hidden
      if (failCount >= filterThreshold) {
        item.style.display = "flex"; // Use flex because li is now a flex container
        hasVisibleItems = true;
      } else {
        item.style.display = "none"; // Hide
        // If an item is hidden, deselect it
        const checkbox = item.querySelector(".key-checkbox");
        if (checkbox && checkbox.checked) {
          checkbox.checked = false;
        }
      }
    }
  });

  // Update the batch operation status and select all checkbox of valid keys
  updateBatchActions("valid");

  // Handle "No valid keys" message
  const noMatchMsgId = "no-valid-keys-msg";
  let noMatchMsg = validKeysList.querySelector(`#${noMatchMsgId}`);
  const initialKeyCount = validKeysList.querySelectorAll("li[data-key]").length; // Get the initial number of keys

  if (!hasVisibleItems && initialKeyCount > 0) {
    // Only show when there are initial keys but they are all invisible now
    if (!noMatchMsg) {
      noMatchMsg = document.createElement("li");
      noMatchMsg.id = noMatchMsgId;
      noMatchMsg.className = "text-center text-gray-500 py-4 col-span-full";
      noMatchMsg.textContent = "No matching valid keys found";
      validKeysList.appendChild(noMatchMsg);
    }
    noMatchMsg.style.display = "";
  } else if (noMatchMsg) {
    noMatchMsg.style.display = "none";
  }
}

// --- Initialization Helper Functions ---
function initializePageAnimationsAndEffects() {
  initStatItemAnimations(); // Already an external function

  const animateCounters = () => {
    const statValues = document.querySelectorAll(".stat-value");
    statValues.forEach((valueElement) => {
      const finalValue = parseInt(valueElement.textContent, 10);
      if (!isNaN(finalValue)) {
        if (!valueElement.dataset.originalValue) {
          valueElement.dataset.originalValue = valueElement.textContent;
        }
        let startValue = 0;
        const duration = 1500;
        const startTime = performance.now();
        const updateCounter = (currentTime) => {
          const elapsedTime = currentTime - startTime;
          if (elapsedTime < duration) {
            const progress = elapsedTime / duration;
            const easeOutValue = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.floor(easeOutValue * finalValue);
            valueElement.textContent = currentValue;
            requestAnimationFrame(updateCounter);
          } else {
            valueElement.textContent = valueElement.dataset.originalValue;
          }
        };
        requestAnimationFrame(updateCounter);
      }
    });
  };
  setTimeout(animateCounters, 300);

  document.querySelectorAll(".stats-card").forEach((card) => {
    card.addEventListener("mouseenter", () => {
      card.classList.add("shadow-lg");
      card.style.transform = "translateY(-2px)";
    });
    card.addEventListener("mouseleave", () => {
      card.classList.remove("shadow-lg");
      card.style.transform = "";
    });
  });
}

function initializeSectionToggleListeners() {
  document.querySelectorAll(".stats-card-header").forEach((header) => {
    if (header.querySelector(".toggle-icon")) {
      header.addEventListener("click", (event) => {
        if (event.target.closest("input, label, button, select")) {
          return;
        }
        const card = header.closest(".stats-card");
        const content = card ? card.querySelector(".key-content") : null;
        const sectionId = content ? content.id : null;
        if (sectionId) {
          toggleSection(header, sectionId);
        } else {
          console.warn("Could not determine sectionId for toggle.");
        }
      });
    }
  });
}

function initializeKeyFilterControls() {
  const thresholdInput = document.getElementById("failCountThreshold");
  if (thresholdInput) {
    thresholdInput.addEventListener("input", filterValidKeys);
  }
}

function initializeGlobalBatchVerificationHandlers() {
  window.showVerifyModal = function (type, event) {
    if (event) {
      event.stopPropagation();
    }
    const modalElement = document.getElementById("verifyModal");
    const titleElement = document.getElementById("verifyModalTitle");
    const messageElement = document.getElementById("verifyModalMessage");
    const confirmButton = document.getElementById("confirmVerifyBtn");
    const selectedKeys = getSelectedKeys(type);
    const count = selectedKeys.length;
    titleElement.textContent = "Batch Verify Keys";
    if (count > 0) {
      messageElement.textContent = `Are you sure you want to batch verify ${count} selected ${
        type === "valid" ? "valid" : "invalid"
      } keys? This may take some time.`;
      confirmButton.disabled = false;
    } else {
      messageElement.textContent = `Please select the ${
        type === "valid" ? "valid" : "invalid"
      } keys to verify first.`;
      confirmButton.disabled = true;
    }
    confirmButton.onclick = () => executeVerifyAll(type);
    modalElement.classList.remove("hidden");
  };

  window.closeVerifyModal = function () {
    document.getElementById("verifyModal").classList.add("hidden");
  };

  // executeVerifyAll becomes a local function of initializeGlobalBatchVerificationHandlers
  async function executeVerifyAll(type) {
    // Removed window.
    try {
      window.closeVerifyModal(); // Calls the global close function, which is fine.
      const verifyButton = document.querySelector(
        `#${type}BatchActions button:nth-child(1)`
      ); // Assuming verify is the first button
      let originalVerifyHtml = "";
      if (verifyButton) {
        originalVerifyHtml = verifyButton.innerHTML;
        verifyButton.disabled = true;
        verifyButton.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Verifying';
      }
      const keysToVerify = getSelectedKeys(type);
      if (keysToVerify.length === 0) {
        showNotification(
          `No selected ${type === "valid" ? "valid" : "invalid"} keys to verify.`,
          "warning"
        );
        if (verifyButton) {
          // Restore button if no keys selected
          verifyButton.innerHTML = originalVerifyHtml;
        }
        return;
      }
      showNotification("Starting batch verification, please wait...", "info");
      const options = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys: keysToVerify }),
      };
      const data = await fetchAPI(
        `/gemini/v1beta/verify-selected-keys`,
        options
      );
      if (data) {
        showVerificationResultModal(data);
      } else {
        throw new Error("API did not return verification data.");
      }
    } catch (apiError) {
      console.error("Batch verification processing failed:", apiError);
      showResultModal(false, `Batch verification processing failed: ${apiError.message}`, true);
    } finally {
      console.log("Batch verification process completed.");
      // Button state will be reset on page reload or by updateBatchActions
    }
  }
  // The confirmButton.onclick in showVerifyModal (defined earlier in initializeGlobalBatchVerificationHandlers)
  // will correctly reference this local executeVerifyAll due to closure.
}

function initializeKeySelectionListeners() {
  const setupEventListenersForList = (listId, keyType) => {
    const listElement = document.getElementById(listId);
    if (!listElement) return;

    // Event delegation for clicks on list items to toggle checkbox
    listElement.addEventListener("click", (event) => {
      const listItem = event.target.closest("li[data-key]");
      if (!listItem) return;

      // Do not toggle if a button, a link, or any element explicitly designed for interaction within the li was clicked
      if (
        event.target.closest(
          "button, a, input[type='button'], input[type='submit']"
        )
      ) {
        let currentTarget = event.target;
        let isInteractiveElementClick = false;
        while (currentTarget && currentTarget !== listItem) {
          if (
            currentTarget.tagName === "BUTTON" ||
            currentTarget.tagName === "A" ||
            (currentTarget.tagName === "INPUT" &&
              ["button", "submit"].includes(currentTarget.type))
          ) {
            isInteractiveElementClick = true;
            break;
          }
          currentTarget = currentTarget.parentElement;
        }
        if (isInteractiveElementClick) return;
      }

      const checkbox = listItem.querySelector(".key-checkbox");
      if (checkbox) {
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });

    // Event delegation for 'change' event on checkboxes within the list
    listElement.addEventListener("change", (event) => {
      if (event.target.classList.contains("key-checkbox")) {
        const checkbox = event.target; // This is the checkbox in the DOM
        const listItem = checkbox.closest("li[data-key]"); // This is the LI in the DOM

        if (listItem) {
          listItem.classList.toggle("selected", checkbox.checked);

          // Sync with master array
          const key = listItem.dataset.key;
          const masterList =
            keyType === "valid" ? allValidKeys : allInvalidKeys;
          if (masterList) {
            // Ensure masterList is defined
            const masterListItem = masterList.find(
              (li) => li.dataset.key === key
            );
            if (masterListItem) {
              const masterCheckbox =
                masterListItem.querySelector(".key-checkbox");
              if (masterCheckbox) {
                masterCheckbox.checked = checkbox.checked;
              }
            }
          }
        }
        updateBatchActions(keyType);
      }
    });
  };

  setupEventListenersForList("validKeys", "valid");
  setupEventListenersForList("invalidKeys", "invalid");
}

function initializeAutoRefreshControls() {
  const autoRefreshToggle = document.getElementById("autoRefreshToggle");
  const autoRefreshIntervalTime = 60000; // 60 seconds
  let autoRefreshTimer = null;

  function startAutoRefresh() {
    if (autoRefreshTimer) return;
    console.log("Starting auto-refresh...");
    showNotification("Auto-refresh enabled", "info", 2000);
    autoRefreshTimer = setInterval(() => {
      console.log("Auto-refreshing keys_status page...");
      location.reload();
    }, autoRefreshIntervalTime);
  }

  function stopAutoRefresh() {
    if (autoRefreshTimer) {
      console.log("Stopping auto-refresh...");
      showNotification("Auto-refresh disabled", "info", 2000);
      clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
  }

  if (autoRefreshToggle) {
    const isAutoRefreshEnabled =
      localStorage.getItem("autoRefreshEnabled") === "true";
    autoRefreshToggle.checked = isAutoRefreshEnabled;
    if (isAutoRefreshEnabled) {
      startAutoRefresh();
    }
    autoRefreshToggle.addEventListener("change", () => {
      if (autoRefreshToggle.checked) {
        localStorage.setItem("autoRefreshEnabled", "true");
        startAutoRefresh();
      } else {
        localStorage.setItem("autoRefreshEnabled", "false");
        stopAutoRefresh();
      }
    });
  }
}

// These variables are used by pagination and search, define them in a scope accessible by initializeKeyPaginationAndSearch
let allValidKeys = [];
let allInvalidKeys = [];
let filteredValidKeys = [];
let itemsPerPage = 10; // Default
let validCurrentPage = 1; // Also used by displayPage
let invalidCurrentPage = 1; // Also used by displayPage

function initializeKeyPaginationAndSearch() {
  const validKeysListElement = document.getElementById("validKeys");
  const invalidKeysListElement = document.getElementById("invalidKeys");
  const searchInput = document.getElementById("keySearchInput");
  const itemsPerPageSelect = document.getElementById("itemsPerPageSelect");
  const thresholdInput = document.getElementById("failCountThreshold"); // Already used by initializeKeyFilterControls

  if (validKeysListElement) {
    allValidKeys = Array.from(
      validKeysListElement.querySelectorAll("li[data-key]")
    );
    allValidKeys.forEach((li) => {
      const keyTextSpan = li.querySelector(".key-text");
      if (keyTextSpan && keyTextSpan.dataset.fullKey) {
        li.dataset.key = keyTextSpan.dataset.fullKey;
      }
    });
    filteredValidKeys = [...allValidKeys];
  }
  if (invalidKeysListElement) {
    allInvalidKeys = Array.from(
      invalidKeysListElement.querySelectorAll("li[data-key]")
    );
    allInvalidKeys.forEach((li) => {
      const keyTextSpan = li.querySelector(".key-text");
      if (keyTextSpan && keyTextSpan.dataset.fullKey) {
        li.dataset.key = keyTextSpan.dataset.fullKey;
      }
    });
  }

  if (itemsPerPageSelect) {
    itemsPerPage = parseInt(itemsPerPageSelect.value, 10); // Initialize itemsPerPage
    itemsPerPageSelect.addEventListener("change", () => {
      itemsPerPage = parseInt(itemsPerPageSelect.value, 10);
      filterAndSearchValidKeys(); // Re-filter and display page 1 for valid keys
      displayPage("invalid", 1, allInvalidKeys); // Reset invalid keys to page 1
    });
  }

  // Initial display calls
  filterAndSearchValidKeys();
  displayPage("invalid", 1, allInvalidKeys);

  // Event listeners for search and filter (thresholdInput listener is in initializeKeyFilterControls)
  if (searchInput) {
    searchInput.addEventListener("input", filterAndSearchValidKeys);
  }
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/static/service-worker.js")
        .then((registration) => {
          console.log("ServiceWorker registration successful:", registration.scope);
        })
        .catch((error) => {
          console.log("ServiceWorker registration failed:", error);
        });
    });
  }
}

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initializePageAnimationsAndEffects();
  initializeSectionToggleListeners();
  initializeKeyFilterControls();
  initializeGlobalBatchVerificationHandlers();
  initializeKeySelectionListeners();
  initializeAutoRefreshControls();
  initializeKeyPaginationAndSearch(); // This will also handle initial display
  registerServiceWorker();

  // Initial batch actions update might be needed if not covered by displayPage
  // updateBatchActions('valid');
  // updateBatchActions('invalid');
});

// --- New: Delete key related functions ---

// New version: Show single key deletion confirmation modal
function showSingleKeyDeleteConfirmModal(key, button) {
  const modalElement = document.getElementById("singleKeyDeleteConfirmModal");
  const titleElement = document.getElementById(
    "singleKeyDeleteConfirmModalTitle"
  );
  const messageElement = document.getElementById(
    "singleKeyDeleteConfirmModalMessage"
  );
  const confirmButton = document.getElementById("confirmSingleKeyDeleteBtn");

  const keyDisplay =
    key.substring(0, 4) + "..." + key.substring(key.length - 4);
  titleElement.textContent = "Confirm Key Deletion";
  messageElement.innerHTML = `Are you sure you want to delete the key <span class="font-mono text-amber-300 font-semibold">${keyDisplay}</span>?<br>This action cannot be undone.`;

  // Remove the old listener and re-attach it to ensure that the key and button parameters are up-to-date
  const newConfirmButton = confirmButton.cloneNode(true);
  confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);

  newConfirmButton.onclick = () => executeSingleKeyDelete(key, button);

  modalElement.classList.remove("hidden");
}

// New version: Close single key deletion confirmation modal
function closeSingleKeyDeleteConfirmModal() {
  document
    .getElementById("singleKeyDeleteConfirmModal")
    .classList.add("hidden");
}

// New version: Execute single key deletion
async function executeSingleKeyDelete(key, button) {
  closeSingleKeyDeleteConfirmModal();

  button.disabled = true;
  const originalHtml = button.innerHTML;
  // Use font icons to ensure consistency
  button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Deleting';

  try {
    const response = await fetchAPI(`/api/config/keys/${key}`, {
      method: "DELETE",
    });

    if (response.success) {
      // Use resultModal and ensure refresh
      showResultModal(true, response.message || "Key deleted successfully", true);
    } else {
      // Use resultModal, do not refresh on failure, so that the user can see the error message
      showResultModal(false, response.message || "Key deletion failed", false);
      button.innerHTML = originalHtml;
      button.disabled = false;
    }
  } catch (error) {
    console.error("Delete key API request failed:", error);
    showResultModal(false, `Delete key request failed: ${error.message}`, false);
    button.innerHTML = originalHtml;
    button.disabled = false;
  }
}

// Show batch delete confirmation modal
function showDeleteConfirmationModal(type, event) {
  if (event) {
    event.stopPropagation();
  }
  const modalElement = document.getElementById("deleteConfirmModal");
  const titleElement = document.getElementById("deleteConfirmModalTitle");
  const messageElement = document.getElementById("deleteConfirmModalMessage");
  const confirmButton = document.getElementById("confirmDeleteBtn");

  const selectedKeys = getSelectedKeys(type);
  const count = selectedKeys.length;

  titleElement.textContent = "Confirm Batch Deletion";
  if (count > 0) {
    messageElement.textContent = `Are you sure you want to delete ${count} selected ${
      type === "valid" ? "valid" : "invalid"
    } keys? This action cannot be undone.`;
    confirmButton.disabled = false;
  } else {
    // This should not happen in theory, because the batch delete button is disabled when not selected
    messageElement.textContent = `Please select the ${
      type === "valid" ? "valid" : "invalid"
    } keys to delete first.`;
    confirmButton.disabled = true;
  }

  confirmButton.onclick = () => executeDeleteSelectedKeys(type);
  modalElement.classList.remove("hidden");
}

// Close batch delete confirmation modal
function closeDeleteConfirmationModal() {
  document.getElementById("deleteConfirmModal").classList.add("hidden");
}

// Execute batch delete
async function executeDeleteSelectedKeys(type) {
  closeDeleteConfirmationModal();

  const selectedKeys = getSelectedKeys(type);
  if (selectedKeys.length === 0) {
    showNotification("No keys selected to delete", "warning");
    return;
  }

  // Find the batch delete button and display the loading status (assuming it is the last button in the corresponding type of batchActions)
  const batchActionsDiv = document.getElementById(`${type}BatchActions`);
  const deleteButton = batchActionsDiv
    ? batchActionsDiv.querySelector("button.bg-red-600")
    : null;

  let originalDeleteBtnHtml = "";
  if (deleteButton) {
    originalDeleteBtnHtml = deleteButton.innerHTML;
    deleteButton.disabled = true;
    deleteButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting';
  }

  try {
    const response = await fetchAPI("/api/config/keys/delete-selected", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keys: selectedKeys }),
    });

    if (response.success) {
      // Use resultModal to display more detailed results
      const message =
        response.message ||
        `Successfully deleted ${response.deleted_count || selectedKeys.length} keys.`;
      showResultModal(true, message, true); // true means success, message, true means refresh after closing
    } else {
      showResultModal(false, response.message || "Batch key deletion failed", true); // false means failure, message, true means refresh after closing
    }
  } catch (error) {
    console.error("Batch delete API request failed:", error);
    showResultModal(false, `Batch delete API request failed: ${error.message}`, true);
  } finally {
    // The page will be refreshed when resultModal is closed, so there is usually no need to restore the button state here.
    // If you do not refresh, you need to restore the button state:
    // if (deleteButton && (!document.getElementById("resultModal") || document.getElementById("resultModal").classList.contains("hidden") || document.getElementById("resultModalTitle").textContent.includes("Failed"))) {
    //   deleteButton.innerHTML = originalDeleteBtnHtml;
    //   // The disabled state of the button will be handled in updateBatchActions, or reset due to page refresh
    // }
  }
}

// --- End: Delete key related functions ---

function toggleKeyVisibility(button) {
  const keyContainer = button.closest(".flex.items-center.gap-1");
  const keyTextSpan = keyContainer.querySelector(".key-text");
  const eyeIcon = button.querySelector("i");
  const fullKey = keyTextSpan.dataset.fullKey;
  const maskedKey =
    fullKey.substring(0, 4) + "..." + fullKey.substring(fullKey.length - 4);

  if (keyTextSpan.textContent === maskedKey) {
    keyTextSpan.textContent = fullKey;
    eyeIcon.classList.remove("fa-eye");
    eyeIcon.classList.add("fa-eye-slash");
    button.title = "Hide key";
  } else {
    keyTextSpan.textContent = maskedKey;
    eyeIcon.classList.remove("fa-eye-slash");
    eyeIcon.classList.add("fa-eye");
    button.title = "Show key";
  }
}

// --- API call details modal logic ---

// Show API call details modal
async function showApiCallDetails(
  period,
  totalCalls,
  successCalls,
  failureCalls
) {
  const modal = document.getElementById("apiCallDetailsModal");
  const contentArea = document.getElementById("apiCallDetailsContent");
  const titleElement = document.getElementById("apiCallDetailsModalTitle");

  if (!modal || !contentArea || !titleElement) {
    console.error("Could not find API call details modal elements");
    showNotification("Cannot display details, page elements are missing", "error");
    return;
  }

  // Set title
  let periodText = "";
  switch (period) {
    case "1m":
      periodText = "Last 1 Minute";
      break;
    case "1h":
      periodText = "Last 1 Hour";
      break;
    case "24h":
      periodText = "Last 24 Hours";
      break;
    default:
      periodText = "Specified Period";
  }
  titleElement.textContent = `${periodText} API Call Details`;

  // Show modal and set loading status
  modal.classList.remove("hidden");
  contentArea.innerHTML = `
        <div class="text-center py-10">
             <i class="fas fa-spinner fa-spin text-primary-600 text-3xl"></i>
             <p class="text-gray-500 mt-2">Loading...</p>
        </div>`;

  try {
    const data = await fetchAPI(`/api/stats/details?period=${period}`);
    if (data) {
      renderApiCallDetails(
        data,
        contentArea,
        totalCalls,
        successCalls,
        failureCalls
      );
    } else {
      renderApiCallDetails(
        [],
        contentArea,
        totalCalls,
        successCalls,
        failureCalls
      ); // Show empty state if no data
    }
  } catch (apiError) {
    console.error("Failed to get API call details:", apiError);
    contentArea.innerHTML = `
            <div class="text-center py-10 text-danger-500">
                <i class="fas fa-exclamation-triangle text-3xl"></i>
                <p class="mt-2">Failed to load: ${apiError.message}</p>
            </div>`;
  }
}

// Close API call details modal
function closeApiCallDetailsModal() {
  const modal = document.getElementById("apiCallDetailsModal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

// Render API call details to modal
function renderApiCallDetails(
  data,
  container,
  totalCalls,
  successCalls,
  failureCalls
) {
  let summaryHtml = "";
  // Only show the overview when these statistics are provided
  if (
    totalCalls !== undefined &&
    successCalls !== undefined &&
    failureCalls !== undefined
  ) {
    summaryHtml = `
        <div class="mb-4 p-3 bg-white dark:bg-gray-700 rounded-lg"> 
            <h4 class="font-semibold text-gray-700 dark:text-gray-200 mb-2 text-md border-b pb-1.5 dark:border-gray-600">Period Call Overview:</h4>
            <div class="grid grid-cols-3 gap-2 text-center">
                <div>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Total</p>
                    <p class="text-lg font-bold text-primary-600 dark:text-primary-400">${totalCalls}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Success</p>
                    <p class="text-lg font-bold text-success-600 dark:text-success-400">${successCalls}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Failure</p>
                    <p class="text-lg font-bold text-danger-600 dark:text-danger-400">${failureCalls}</p>
                </div>
            </div>
        </div>
    `;
  }

  if (!data || data.length === 0) {
    container.innerHTML =
      summaryHtml +
      `
            <div class="text-center py-10 text-gray-500 dark:text-gray-400">
                <i class="fas fa-info-circle text-3xl"></i>
                <p class="mt-2">No API call records in this period.</p>
            </div>`;
    return;
  }

  // Create table
  let tableHtml = `
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Time</th>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Key (Partial)</th>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Model</th>
                    <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
    `;

  // Fill table rows
  data.forEach((call) => {
    const timestamp = new Date(call.timestamp).toLocaleString();
    const keyDisplay = call.key
      ? `${call.key.substring(0, 4)}...${call.key.substring(
          call.key.length - 4
        )}`
      : "N/A";
    const statusClass =
      call.status === "success"
        ? "text-success-600 dark:text-success-400"
        : "text-danger-600 dark:text-danger-400";
    const statusIcon =
      call.status === "success" ? "fa-check-circle" : "fa-times-circle";

    tableHtml += `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">${timestamp}</td>
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 font-mono">${keyDisplay}</td>
                <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${
                  call.model || "N/A"
                }</td>
                <td class="px-4 py-2 whitespace-nowrap text-sm ${statusClass}">
                    <i class="fas ${statusIcon} mr-1"></i>
                    ${call.status}
                </td>
            </tr>
        `;
  });

  tableHtml += `
            </tbody>
        </table>
    `;

  container.innerHTML = summaryHtml + tableHtml; // Prepend summary
}

// --- Key usage details modal logic ---

// Show key usage details modal
window.showKeyUsageDetails = async function (key) {
  const modal = document.getElementById("keyUsageDetailsModal");
  const contentArea = document.getElementById("keyUsageDetailsContent");
  const titleElement = document.getElementById("keyUsageDetailsModalTitle");
  const keyDisplay =
    key.substring(0, 4) + "..." + key.substring(key.length - 4);

  if (!modal || !contentArea || !titleElement) {
    console.error("Could not find key usage details modal elements");
    showNotification("Cannot display details, page elements are missing", "error");
    return;
  }

  // renderKeyUsageDetails becomes a local function of showKeyUsageDetails
  function renderKeyUsageDetails(data, container) {
    if (!data || Object.keys(data).length === 0) {
      container.innerHTML = `
                <div class="text-center py-10 text-gray-500">
                    <i class="fas fa-info-circle text-3xl"></i>
                    <p class="mt-2">This key has no call records in the past 24 hours.</p>
                </div>`;
      return;
    }
    let tableHtml = `
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model Name</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Call Count (24h)</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">`;
    const sortedModels = Object.entries(data).sort(
      ([, countA], [, countB]) => countB - countA
    );
    sortedModels.forEach(([model, count]) => {
      tableHtml += `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${model}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${count}</td>
                </tr>`;
    });
    tableHtml += `
                </tbody>
            </table>`;
    container.innerHTML = tableHtml;
  }

  // Set title
  titleElement.textContent = `Key ${keyDisplay} - Request Details (Last 24 Hours)`;

  // Show modal and set loading status
  modal.classList.remove("hidden");
  contentArea.innerHTML = `
        <div class="text-center py-10">
             <i class="fas fa-spinner fa-spin text-primary-600 text-3xl"></i>
             <p class="text-gray-500 mt-2">Loading...</p>
        </div>`;

  try {
    const data = await fetchAPI(`/api/key-usage-details/${key}`);
    if (data) {
      renderKeyUsageDetails(data, contentArea);
    } else {
      renderKeyUsageDetails({}, contentArea); // Show empty state if no data
    }
  } catch (apiError) {
    console.error("Failed to get key usage details:", apiError);
    contentArea.innerHTML = `
            <div class="text-center py-10 text-danger-500">
                <i class="fas fa-exclamation-triangle text-3xl"></i>
                <p class="mt-2">Failed to load: ${apiError.message}</p>
            </div>`;
  }
};

// Close key usage details modal
window.closeKeyUsageDetailsModal = function () {
  const modal = document.getElementById("keyUsageDetailsModal");
  if (modal) {
    modal.classList.add("hidden");
  }
};

// The window.renderKeyUsageDetails function has been moved inside showKeyUsageDetails, and the remaining code here has been deleted.

// --- Key List Display & Pagination ---

/**
 * Displays key list items for a specific type and page.
 * @param {string} type 'valid' or 'invalid'
 * @param {number} page Page number (1-based)
 * @param {Array} keyItemsArray The array of li elements to paginate (e.g., filteredValidKeys, allInvalidKeys)
 */
function displayPage(type, page, keyItemsArray) {
  const listElement = document.getElementById(`${type}Keys`);
  const paginationControls = document.getElementById(
    `${type}PaginationControls`
  );
  if (!listElement || !paginationControls) return;

  // Update current page based on type
  if (type === "valid") {
    validCurrentPage = page;
    // Read itemsPerPage from the select specifically for valid keys
    const itemsPerPageSelect = document.getElementById("itemsPerPageSelect");
    itemsPerPage = itemsPerPageSelect
      ? parseInt(itemsPerPageSelect.value, 10)
      : 10;
  } else {
    invalidCurrentPage = page;
    // For invalid keys, use a fixed itemsPerPage or the same global one
    // itemsPerPage = 10; // Or read from a different select if needed
  }

  const totalItems = keyItemsArray.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  page = Math.max(1, Math.min(page, totalPages || 1)); // Ensure page is valid

  // Update current page variable again after validation
  if (type === "valid") {
    validCurrentPage = page;
  } else {
    invalidCurrentPage = page;
  }

  const startIndex = (page - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;

  listElement.innerHTML = ""; // Clear current list content

  const pageItems = keyItemsArray.slice(startIndex, endIndex);

  if (pageItems.length > 0) {
    pageItems.forEach((originalMasterItem) => {
      const listItemClone = originalMasterItem.cloneNode(true);
      // The checkbox's 'checked' state is cloned from the master item.
      // Now, ensure the 'selected' class on the clone matches this cloned checkbox state.
      const checkboxInClone = listItemClone.querySelector(".key-checkbox");
      if (checkboxInClone) {
        listItemClone.classList.toggle("selected", checkboxInClone.checked);
      }
      listElement.appendChild(listItemClone);
    });
  } else if (
    totalItems === 0 &&
    type === "valid" &&
    (document.getElementById("failCountThreshold").value !== "0" ||
      document.getElementById("keySearchInput").value !== "")
  ) {
    // Handle empty state after filtering/searching for valid keys
    const noMatchMsgId = "no-valid-keys-msg";
    let noMatchMsg = listElement.querySelector(`#${noMatchMsgId}`);
    if (!noMatchMsg) {
      noMatchMsg = document.createElement("li");
      noMatchMsg.id = noMatchMsgId;
      noMatchMsg.className = "text-center text-gray-500 py-4 col-span-full";
      noMatchMsg.textContent = "No matching valid keys found";
      listElement.appendChild(noMatchMsg);
    }
    noMatchMsg.style.display = "";
  } else if (totalItems === 0) {
    // Handle empty state for initially empty lists
    const emptyMsg = document.createElement("li");
    emptyMsg.className = "text-center text-gray-500 py-4 col-span-full";
    emptyMsg.textContent = `No ${type === "valid" ? "valid" : "invalid"} keys`;
    listElement.appendChild(emptyMsg);
  }

  setupPaginationControls(type, page, totalPages, keyItemsArray);
  updateBatchActions(type); // Update batch actions based on the currently displayed page
  // Re-attach event listeners for buttons inside the newly added list items if needed (using event delegation is better)
}

/**
 * Sets up pagination controls.
 * @param {string} type 'valid' or 'invalid'
 * @param {number} currentPage Current page number
 * @param {number} totalPages Total number of pages
 * @param {Array} keyItemsArray The array of li elements being paginated
 */
function setupPaginationControls(type, currentPage, totalPages, keyItemsArray) {
  const controlsContainer = document.getElementById(
    `${type}PaginationControls`
  );
  if (!controlsContainer) return;

  controlsContainer.innerHTML = "";

  if (totalPages <= 1) {
    return; // No controls needed for single/no page
  }

  // Base classes for all buttons (Tailwind for layout, custom for consistent styling)
  const baseButtonClasses =
    "pagination-button px-3 py-1 rounded text-sm transition-colors duration-150 ease-in-out";
  // Define hover classes that work with the custom background by adjusting opacity or a border effect.
  // Since .pagination-button defines a background, a hover effect might be a subtle border change or brightness.
  // For simplicity, we can rely on CSS for hover effects on .pagination-button:hover
  // const hoverClasses = "hover:border-purple-400"; // Example if you want JS to add specific hover behavior

  // Previous Button
  const prevButton = document.createElement("button");
  prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
  prevButton.className = `${baseButtonClasses} disabled:opacity-50 disabled:cursor-not-allowed`;
  prevButton.disabled = currentPage === 1;
  prevButton.onclick = () => displayPage(type, currentPage - 1, keyItemsArray);
  controlsContainer.appendChild(prevButton);

  // Page Number Buttons (Logic for ellipsis)
  const maxPageButtons = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxPageButtons - 1);

  if (endPage - startPage + 1 < maxPageButtons) {
    startPage = Math.max(1, endPage - maxPageButtons + 1);
  }

  // First Page Button & Ellipsis
  if (startPage > 1) {
    const firstPageButton = document.createElement("button");
    firstPageButton.textContent = "1";
    firstPageButton.className = `${baseButtonClasses}`;
    firstPageButton.onclick = () => displayPage(type, 1, keyItemsArray);
    controlsContainer.appendChild(firstPageButton);
    if (startPage > 2) {
      const ellipsis = document.createElement("span");
      ellipsis.textContent = "...";
      ellipsis.className = "px-3 py-1 text-gray-300 text-sm"; // Adjusted color for dark theme
      controlsContainer.appendChild(ellipsis);
    }
  }

  // Middle Page Buttons
  for (let i = startPage; i <= endPage; i++) {
    const pageButton = document.createElement("button");
    pageButton.textContent = i;
    pageButton.className = `${baseButtonClasses} ${
      i === currentPage
        ? "active font-semibold" // Relies on .pagination-button.active CSS for styling
        : "" // Non-active buttons just use .pagination-button style
    }`;
    pageButton.onclick = () => displayPage(type, i, keyItemsArray);
    controlsContainer.appendChild(pageButton);
  }

  // Ellipsis & Last Page Button
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      const ellipsis = document.createElement("span");
      ellipsis.textContent = "...";
      ellipsis.className = "px-3 py-1 text-gray-300 text-sm"; // Adjusted color
      controlsContainer.appendChild(ellipsis);
    }
    const lastPageButton = document.createElement("button");
    lastPageButton.textContent = totalPages;
    lastPageButton.className = `${baseButtonClasses}`;
    lastPageButton.onclick = () => displayPage(type, totalPages, keyItemsArray);
    controlsContainer.appendChild(lastPageButton);
  }

  // Next Button
  const nextButton = document.createElement("button");
  nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
  nextButton.className = `${baseButtonClasses} disabled:opacity-50 disabled:cursor-not-allowed`;
  nextButton.disabled = currentPage === totalPages;
  nextButton.onclick = () => displayPage(type, currentPage + 1, keyItemsArray);
  controlsContainer.appendChild(nextButton);
}

// --- Filtering & Searching (Valid Keys Only) ---

/**
 * Filters and searches the valid keys based on threshold and search term.
 * Updates the `filteredValidKeys` array and redisplays the first page.
 */
function filterAndSearchValidKeys() {
  const thresholdInput = document.getElementById("failCountThreshold");
  const searchInput = document.getElementById("keySearchInput");

  const threshold = parseInt(thresholdInput.value, 10);
  const filterThreshold = isNaN(threshold) || threshold < 0 ? 0 : threshold;
  const searchTerm = searchInput.value.trim().toLowerCase();

  // Filter from the original full list (allValidKeys)
  filteredValidKeys = allValidKeys.filter((item) => {
    const failCount = parseInt(item.dataset.failCount, 10);
    const fullKey = item.dataset.key || ""; // Use data-key which should hold the full key

    const failCountMatch = failCount >= filterThreshold;
    const searchMatch =
      searchTerm === "" || fullKey.toLowerCase().includes(searchTerm);

    return failCountMatch && searchMatch;
  });

  // Reset to the first page after filtering/searching
  validCurrentPage = 1;
  displayPage("valid", validCurrentPage, filteredValidKeys);
}