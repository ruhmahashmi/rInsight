console.log("rInsight Dashboard loaded");

let charts = {};

function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  if (!tabs.length) {
    console.error("No tabs found");
    return;
  }
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      const tabContent = document.getElementById(tab.dataset.tab);
      if (tabContent) {
        tabContent.classList.add('active');
        if (tab.dataset.tab === 'keywords') {
          fetchKeywords().then(renderKeywords);
        } else if (tab.dataset.tab === 'resources') {
          fetchRecommendations().then(renderRecommendations);
        } else {
          fetchData(tab.dataset.tab);
        }
      } else {
        showError(`Content for ${tab.dataset.tab} not found`);
      }
    });
  });
}

async function fetchStressScores(startDate, endDate) {
  showLoading(true);
  hideError();
  try {
    const url = `/api/stress-scores?start_date=${startDate}&end_date=${endDate}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const data = await response.json();
    return data;
  } catch (e) {
    showError(`Failed to load stress scores: ${e.message}`);
    return {};
  } finally {
    showLoading(false);
  }
}

async function fetchKeywords() {
  showLoading(true);
  hideError();
  try {
    const response = await fetch('/api/keywords');
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    return await response.json();
  } catch (e) {
    showError(`Failed to load keywords: ${e.message}`);
    return [];
  } finally {
    showLoading(false);
  }
}

async function fetchRecommendations() {
  showLoading(true);
  hideError();
  try {
    const response = await fetch('/api/recommendations');
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    return await response.json();
  } catch (e) {
    showError(`Failed to load recommendations: ${e.message}`);
    return [];
  } finally {
    showLoading(false);
  }
}

async function reloadCSV() {
  showLoading(true);
  hideError();
  try {
    const response = await fetch('/api/reload-csv');
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const result = await response.json();
    showError(result.message, result.status === 'success' ? 'info' : 'error');
    const activeTab = document.querySelector('.tab.active')?.dataset.tab;
    if (activeTab) {
      if (activeTab === 'keywords') {
        fetchKeywords().then(renderKeywords);
      } else if (activeTab === 'resources') {
        fetchRecommendations().then(renderRecommendations);
      } else {
        fetchData(activeTab);
      }
    }
  } catch (e) {
    showError(`Failed to reload CSV: ${e.message}`);
  } finally {
    showLoading(false);
  }
}

function showLoading(show) {
  const loading = document.getElementById('loading');
  if (loading) loading.classList.toggle('hidden', !show);
}

function showError(message, type = 'error') {
  const alert = document.getElementById('error-alert');
  const messageEl = document.getElementById('error-message');
  if (alert && messageEl) {
    messageEl.textContent = message;
    alert.className = `p-4 rounded-lg mb-6 ${
      type === 'info' ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' :
      'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
    }`;
    alert.classList.remove('hidden');
  }
}

function hideError() {
  const alert = document.getElementById('error-alert');
  if (alert) alert.classList.add('hidden');
}

function updateProgressBar(id, score, color) {
  const bar = document.getElementById(id);
  if (bar) {
    bar.style.width = `${score}%`;
    bar.style.backgroundColor = color;
  }
}

function updateScoreBadge(id, status, score) {
  const badge = document.getElementById(id);
  if (badge) {
    badge.textContent = status;
    badge.className = `px-3 py-1 rounded-full text-sm ${
      status === 'Low' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' :
      status === 'Moderate' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
      status === 'Critical' ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' :
      'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
    }`;
  }
}

function setupDatePicker(category) {
  const startInput = document.getElementById(`${category}-date-start`);
  const endInput = document.getElementById(`${category}-date-end`);
  if (startInput && endInput) {
    const handler = () => {
      if (startInput.value && endInput.value && startInput.value <= endInput.value) {
        fetchData(category);
      } else {
        showError('Invalid date range. Start date must be before end date.');
      }
    };
    startInput.addEventListener('change', handler);
    endInput.addEventListener('change', handler);
  }
}

function setupButtons() {
  const retryButton = document.getElementById('retry-data');
  if (retryButton) {
    retryButton.addEventListener('click', () => {
      const activeTab = document.querySelector('.tab.active')?.dataset.tab;
      if (activeTab) {
        if (activeTab === 'keywords') {
          fetchKeywords().then(renderKeywords);
        } else if (activeTab === 'resources') {
          fetchRecommendations().then(renderRecommendations);
        } else {
          fetchData(activeTab);
        }
      }
    });
  }
  const reloadButton = document.getElementById('reload-csv');
  if (reloadButton) reloadButton.addEventListener('click', reloadCSV);

  document.querySelectorAll('#download-report').forEach(btn => {
    btn.addEventListener('click', () => {
      const category = btn.closest('.tab-content').id;
      generateReport(category);
    });
  });
}

function generateReport(category) {
  const score = document.getElementById(`${category}-score`)?.textContent || '0';
  const explanation = document.getElementById(`${category}-explanation`)?.textContent || 'No data';
  const recommendation = document.getElementById(`${category}-recommendation`)?.textContent || 'No recommendation';
  const report = `
    rInsight Stress Report: ${category.charAt(0).toUpperCase() + category.slice(1)}
    Date: ${new Date().toLocaleDateString()}
    Score: ${score}
    Explanation: ${explanation}
    Recommendation: ${recommendation}
  `;
  const blob = new Blob([report], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${category}_stress_report.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

async function fetchData(category) {
  const startDate = document.getElementById(`${category}-date-start`)?.value || '2025-04-13';
  const endDate = document.getElementById(`${category}-date-end`)?.value || '2025-04-20';
  const scores = await fetchStressScores(startDate, endDate);

  const categories = category === 'all' ? ['academic', 'financial', 'health', 'housing', 'social'] : [category];
  for (const cat of categories) {
    const scoreEl = document.getElementById(`${cat}-score`);
    const explanationEl = document.getElementById(`${cat}-explanation`);
    const recommendationEl = document.getElementById(`${cat}-recommendation`);
    if (!scoreEl || !explanationEl || !recommendationEl) continue;

    if (scores[cat]?.score > 0) {
      scoreEl.textContent = scores[cat].score;
      updateScoreBadge(`${cat}-badge`, scores[cat].status, scores[cat].score);
      explanationEl.textContent = scores[cat].explanation;
      recommendationEl.textContent = `Recommendation: ${scores[cat].recommendation}`;
      updateProgressBar(`${cat}-progress`, scores[cat].score, scores[cat].color);
      const canvas = document.getElementById(`${cat}-trend`);
      if (canvas) {
        if (charts[cat]) charts[cat].destroy();
        charts[cat] = new Chart(canvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: scores[cat].trend_labels,
            datasets: [{
              label: cat.charAt(0).toUpperCase() + cat.slice(1),
              data: scores[cat].trend_data,
              borderColor: scores[cat].color,
              backgroundColor: createGradient(canvas, scores[cat].color),
              fill: true,
              tension: 0.4
            }]
          },
          options: {
            responsive: true,
            animation: { duration: 1000 },
            scales: { y: { beginAtZero: true, max: 100 } },
            plugins: { tooltip: { mode: 'index', intersect: false } }
          }
        });
      }
    } else {
      scoreEl.textContent = '0';
      explanationEl.textContent = `Explanation: No ${cat} posts found`;
      recommendationEl.textContent = 'Recommendation: Monitor subreddit for new posts';
      updateScoreBadge(`${cat}-badge`, 'No Data', 0);
      updateProgressBar(`${cat}-progress`, 0, '#6B7280');
    }

    const refreshButton = document.getElementById(`refresh-${cat}`);
    if (refreshButton) {
      refreshButton.removeEventListener('click', fetchData);
      refreshButton.addEventListener('click', () => fetchData(cat));
    }
    setupDatePicker(cat);
  }

  if (category === 'all' && Object.keys(scores).length) {
    const highestStress = document.getElementById('highest-stress');
    const topKeyword = document.getElementById('top-keyword');
    const criticalAlerts = document.getElementById('critical-alerts');
    const allSummary = document.getElementById('all-summary');
    const allRecommendation = document.getElementById('all-recommendation');
    if (highestStress && topKeyword && criticalAlerts && allSummary && allRecommendation) {
      highestStress.textContent = scores.highest_stress || 'None (Score: 0)';
      topKeyword.textContent = scores.top_keyword || 'None (Frequency: 0)';
      criticalAlerts.textContent = scores.critical_alerts || '0 categories';
      allSummary.textContent = scores.summary || 'Summary: No data available';
      allRecommendation.textContent = `Recommendation: ${scores.recommendation || 'No recommendation available'}`;
      const radarCanvas = document.getElementById('radar-chart');
      if (radarCanvas) {
        if (charts.radar) charts.radar.destroy();
        charts.radar = new Chart(radarCanvas.getContext('2d'), {
          type: 'radar',
          data: {
            labels: ['Academic', 'Financial', 'Health', 'Housing', 'Social'],
            datasets: [{
              label: 'Stress Scores',
              data: [
                scores.academic?.score || 0,
                scores.financial?.score || 0,
                scores.health?.score || 0,
                scores.housing?.score || 0,
                scores.social?.score || 0
              ],
              backgroundColor: 'rgba(59, 130, 246, 0.2)',
              borderColor: '#3B82F6',
              pointBackgroundColor: '#3B82F6'
            }]
          },
          options: {
            responsive: true,
            animation: { duration: 1500 },
            scales: { r: { beginAtZero: true, max: 100 } }
          }
        });
      }
    }
    const liveAlerts = document.getElementById('live-alerts');
    const alertMessage = document.getElementById('alert-message');
    if (liveAlerts && alertMessage && scores.critical_alerts.includes('categories need urgent attention')) {
      const criticalCount = parseInt(scores.critical_alerts) || 0;
      alertMessage.textContent = criticalCount > 0
        ? `Critical Alert: ${criticalCount} categories require immediate attention!`
        : 'No critical alerts at this time.';
      liveAlerts.classList.toggle('hidden', criticalCount === 0);
    }
  }
}

function createGradient(canvas, color) {
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, `${color}80`);
  gradient.addColorStop(1, `${color}10`);
  return gradient;
}

async function renderKeywords(keywords) {
  const table = document.getElementById('keyword-table').querySelector('tbody');
  if (!table) return;
  table.innerHTML = '';
  if (keywords?.length) {
    let filteredKeywords = [...keywords];
    const searchInput = document.getElementById('keyword-search');
    const categoryFilter = document.getElementById('keyword-filter');
    const sortButton = document.getElementById('sort-frequency');

    function renderKeywordTable(kws) {
      table.innerHTML = '';
      kws.forEach(kw => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td class="p-3">${kw.keyword}</td>
          <td class="p-3">${kw.frequency}</td>
          <td class="p-3">${kw.category.charAt(0).toUpperCase() + kw.category.slice(1)}</td>
          <td class="p-3">${(kw.confidence * 100).toFixed(1)}%</td>
          <td class="p-3">${kw.sample}</td>
        `;
        table.appendChild(row);
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', () => {
        filteredKeywords = keywords.filter(kw => kw.keyword.toLowerCase().includes(searchInput.value.toLowerCase()));
        if (categoryFilter?.value !== 'all') {
          filteredKeywords = filteredKeywords.filter(kw => kw.category === categoryFilter.value);
        }
        renderKeywordTable(filteredKeywords);
      });
    }

    if (categoryFilter) {
      categoryFilter.addEventListener('change', (e) => {
        filteredKeywords = e.target.value === 'all' ? keywords : keywords.filter(kw => kw.category === e.target.value);
        if (searchInput?.value) {
          filteredKeywords = filteredKeywords.filter(kw => kw.keyword.toLowerCase().includes(searchInput.value.toLowerCase()));
        }
        renderKeywordTable(filteredKeywords);
      });
    }

    if (sortButton) {
      sortButton.addEventListener('click', () => {
        filteredKeywords.sort((a, b) => b.frequency - a.frequency);
        renderKeywordTable(filteredKeywords);
      });
    }

    renderKeywordTable(filteredKeywords);

    const keywordCanvas = document.getElementById('keyword-chart');
    if (keywordCanvas) {
      if (charts.keyword) charts.keyword.destroy();
      charts.keyword = new Chart(keywordCanvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels: keywords.slice(0, 5).map(kw => kw.keyword),
          datasets: [{
            label: 'Frequency',
            data: keywords.slice(0, 5).map(kw => kw.frequency),
            backgroundColor: '#3B82F6',
            borderColor: '#3B82F6',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          scales: { y: { beginAtZero: true } },
          animation: { duration: 1000 }
        }
      });
    }
  } else {
    table.innerHTML = '<tr><td colspan="5" class="text-center p-4">No keywords available</td></tr>';
  }
}

async function renderRecommendations(recommendations) {
  const list = document.getElementById('gemini-recommendations');
  const alert = document.getElementById('resources-alert');
  if (!list || !alert) return;
  list.innerHTML = '';
  if (recommendations?.length) {
    recommendations.forEach(rec => {
      const li = document.createElement('li');
      li.className = 'py-2';
      li.innerHTML = `<strong class="text-blue-600 dark:text-blue-400">${rec.keyword}</strong> (${rec.severity}): ${rec.suggestion}`;
      list.appendChild(li);
    });
    alert.textContent = `Alert: ${recommendations.length} actionable recommendations generated`;
    alert.className = 'text-yellow-600 dark:text-yellow-400 mb-4 font-semibold';
  } else {
    list.innerHTML = '<li class="py-2 text-gray-600 dark:text-gray-400">No recommendations available</li>';
    alert.textContent = 'Alert: No recommendations generated';
    alert.className = 'text-red-600 dark:text-red-400 mb-4 font-semibold';
  }
}

function setupThemeToggle() {
  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('dark');
      localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    });
    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('dark');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupButtons();
  setupThemeToggle();
  fetchData('academic');
});