/**
 * Share functionality for blog posts
 * Handles social sharing with dropdown UI, Web Share API fallback,
 * copy-to-clipboard, and server-side share tracking.
 */

(function () {
  'use strict';

  // ── Helpers ──────────────────────────────────────
  function getCsrfToken() {
    const cookie = document.cookie
      .split('; ')
      .find(r => r.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  function showToast(message) {
    const toast = document.getElementById('shareToast');
    const text = document.getElementById('shareToastText');
    if (!toast) return;
    if (text) text.textContent = message;
    toast.classList.add('active');
    setTimeout(() => toast.classList.remove('active'), 2500);
  }

  // ── Track share on server ───────────────────────
  async function trackShare(slug, platform) {
    try {
      await fetch(`/blogs/post/${slug}/share/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({ platform }),
      });
      // Update count in UI
      const countEl = document.getElementById('shareCount');
      if (countEl) {
        const current = parseInt(countEl.textContent, 10) || 0;
        countEl.textContent = current + 1;
      }
    } catch (e) {
      console.error('Share tracking error:', e);
    }
  }

  // ── Platform share URLs ─────────────────────────
  const platformUrls = {
    twitter(url, title) {
      return `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
    },
    facebook(url) {
      return `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    },
    linkedin(url) {
      return `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
    },
    telegram(url, title) {
      return `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
    },
    whatsapp(url, title) {
      return `https://wa.me/?text=${encodeURIComponent(title + ' ' + url)}`;
    },
  };

  function openShareWindow(platform, url, title) {
    const buildUrl = platformUrls[platform];
    if (!buildUrl) return false;
    const shareUrl = buildUrl(url, title);
    window.open(shareUrl, '_blank', 'noopener,noreferrer,width=600,height=500');
    return true;
  }

  // Platforms that require copy-link flow (no web share URL)
  const copyOnlyPlatforms = { instagram: 'Instagram', tiktok: 'TikTok' };

  // ── Dropdown controller ─────────────────────────
  function initShareDropdown() {
    const wrapper = document.getElementById('shareWrapper');
    const btn = document.getElementById('shareBtn');
    const dropdown = document.getElementById('shareDropdown');
    const closeBtn = document.getElementById('shareDropdownClose');
    const copyBtn = document.getElementById('shareCopyBtn');
    const copyInput = document.getElementById('shareCopyInput');
    if (!wrapper || !btn || !dropdown) return;

    const slug = btn.dataset.slug;
    const title = btn.dataset.title;
    const url = btn.dataset.url;

    // Toggle dropdown
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      // On mobile, try native Web Share API first
      if (navigator.share && window.innerWidth < 768) {
        navigator.share({ title, url })
          .then(() => trackShare(slug, 'native'))
          .catch(() => {}); // user cancelled
        return;
      }
      dropdown.classList.toggle('active');
    });

    // Close button
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.remove('active');
      });
    }

    // Click outside to close
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        dropdown.classList.remove('active');
      }
    });

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') dropdown.classList.remove('active');
    });

    // Social share buttons
    dropdown.querySelectorAll('.share-option').forEach(option => {
      option.addEventListener('click', () => {
        const platform = option.dataset.platform;

        if (copyOnlyPlatforms[platform]) {
          // Instagram / TikTok: copy link and prompt user
          navigator.clipboard.writeText(url).then(() => {
            showToast(`Havola nusxalandi! ${copyOnlyPlatforms[platform]} ga joylashtiring`);
          }).catch(() => {
            showToast(`Havola nusxalandi!`);
          });
        } else {
          openShareWindow(platform, url, title);
          showToast('Ulashildi!');
        }

        trackShare(slug, platform);
        dropdown.classList.remove('active');
      });
    });

    // Copy link button
    if (copyBtn && copyInput) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(copyInput.value).then(() => {
          copyBtn.classList.add('copied');
          copyBtn.innerHTML = '<i class="bi bi-check-lg"></i>';
          trackShare(slug, 'copy_link');
          showToast('Havola nusxalandi!');
          setTimeout(() => {
            copyBtn.classList.remove('copied');
            copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>';
          }, 2000);
        }).catch(() => {
          // Fallback for older browsers
          copyInput.select();
          document.execCommand('copy');
          trackShare(slug, 'copy_link');
          showToast('Havola nusxalandi!');
        });
      });
    }
  }

  // ── Init ─────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', initShareDropdown);
})();
