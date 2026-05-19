/**
 * Engagement functionality for blog posts (like/dislike)
 * Handles AJAX requests for like/dislike actions with UI updates
 */

// Get CSRF token from Django template
function getCsrfToken() {
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
  return cookieValue || '';
}

// Handle like/dislike action
async function handleEngagement(action, slug) {
  const url = `/blogs/post/${slug}/${action}/`;
  const csrfToken = getCsrfToken();

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
    });

    if (response.status === 429) {
      // Rate limit exceeded
      const data = await response.json();
      showError(data.error || 'Rate limit exceeded. Please try again later.');
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    updateUI(action, data);
  } catch (error) {
    console.error('Error:', error);
    showError('An error occurred. Please try again.');
  }
}

// Update UI with new counts and button states
function updateUI(action, data) {
  const likeBtn = document.getElementById('likeBtn');
  const dislikeBtn = document.getElementById('dislikeBtn');
  const likeCount = document.getElementById('likeCount');
  const dislikeCount = document.getElementById('dislikeCount');

  // Update counts
  if (likeCount) {
    likeCount.textContent = `(${data.likes})`;
  }
  if (dislikeCount) {
    dislikeCount.textContent = `(${data.dislikes})`;
  }

  // Update button states based on action
  if (action === 'like') {
    if (data.action === 'added') {
      // Like was added
      likeBtn.classList.remove('btn-outline-primary');
      likeBtn.classList.add('btn-primary');
      // Remove dislike state if present
      dislikeBtn.classList.remove('btn-danger');
      dislikeBtn.classList.add('btn-outline-danger');
    } else {
      // Like was removed
      likeBtn.classList.remove('btn-primary');
      likeBtn.classList.add('btn-outline-primary');
    }
  } else if (action === 'dislike') {
    if (data.action === 'added') {
      // Dislike was added
      dislikeBtn.classList.remove('btn-outline-danger');
      dislikeBtn.classList.add('btn-danger');
      // Remove like state if present
      likeBtn.classList.remove('btn-primary');
      likeBtn.classList.add('btn-outline-primary');
    } else {
      // Dislike was removed
      dislikeBtn.classList.remove('btn-danger');
      dislikeBtn.classList.add('btn-outline-danger');
    }
  }
}

// Show error message to user
function showError(message) {
  // Create error message element
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4';
  errorDiv.setAttribute('role', 'alert');
  errorDiv.innerHTML = `
    <strong class="font-bold">Error: </strong>
    <span class="block sm:inline">${message}</span>
  `;

  // Insert error message before engagement buttons
  const engagementDiv = document.querySelector('.mt-6.flex.items-center.space-x-4');
  if (engagementDiv) {
    engagementDiv.parentNode.insertBefore(errorDiv, engagementDiv);
    
    // Remove error message after 5 seconds
    setTimeout(() => {
      errorDiv.remove();
    }, 5000);
  }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const likeBtn = document.getElementById('likeBtn');
  const dislikeBtn = document.getElementById('dislikeBtn');

  if (likeBtn) {
    likeBtn.addEventListener('click', () => {
      const slug = likeBtn.getAttribute('data-slug');
      handleEngagement('like', slug);
    });
  }

  if (dislikeBtn) {
    dislikeBtn.addEventListener('click', () => {
      const slug = dislikeBtn.getAttribute('data-slug');
      handleEngagement('dislike', slug);
    });
  }
});
