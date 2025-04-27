console.log("Script.js loaded");

// Tab Switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
});

// Week Selector
document.getElementById('week-select').addEventListener('change', (e) => {
  const week = e.target.value;
  console.log(`Week selected: ${week}`);
  fetchData(week);
});

// Fetch Data from Flask
async function fetchStressScores(week = 'all') {
  try {
    const response = await fetch(`/api/stress-scores/${week}`);
    const data = await response.json();
    console.log('Stress scores:', data);
    return data;
  } catch (e) {
    console.error('Error fetching stress scores:', e);
    return {};
  }
}

async function fetchKeywords(week = 'all') {
  try {
    const response = await fetch(`/api/keywords/${week}`);
    const data = await response.json();
    console.log('Keywords:', data);
    return data;
  } catch (e) {
    console.error('Error fetching keywords:', e);
    return [];
  }
}

async function fetchRecommendations(week = 'all') {
  try {
    const response = await fetch(`/api/recommendations/${week}`);
    const data = await response.json();
    console.log('Recommendations:', data);
    return data;
  } catch (e) {
    console.error('Error fetching recommendations:', e);
    return [];
  }
}

// Render Gauges
function drawGauge(ctx, score, color) {
  ctx.beginPath();
  ctx.arc(75, 75, 60, 0, 2 * Math.PI);
  ctx.strokeStyle = '#4B5563';
  ctx.lineWidth = 10;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(75, 75, 60, -Math.PI / 2, (-Math.PI / 2) + (score / 100) * 2 * Math.PI);
  ctx.strokeStyle = color;
  ctx.lineWidth = 10;
  ctx.stroke();
  ctx.font = '20px Poppins';
  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.fillText(score, 75, 80);
}

// Fetch and Render Data
async function fetchData(week) {
  const scores = await fetchStressScores(week);
  const keywords = await fetchKeywords(week);
  const recommendations = await fetchRecommendations(week);

  // Academic
  if (scores.academic) {
    document.getElementById('academic-score').textContent = scores.academic.score;
    document.getElementById('academic-trend-text').textContent = `Trend: ${scores.academic.trend} in Week ${week === 'all' ? 'All' : week}`;
    document.getElementById('academic-recommendation').textContent = `Recommendation: ${scores.academic.recommendation}`;
    drawGauge(document.getElementById('academic-gauge').getContext('2d'), scores.academic.score, scores.academic.color);
    new Chart(document.getElementById('academic-trend').getContext('2d'), {
      type: 'line',
      data: {
        labels: scores.academic.trend_labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{ label: 'Academic', data: scores.academic.trend_data || [60, 55, 50, 42], borderColor: scores.academic.color, fill: false }]
      },
      options: { responsive: true, animation: { duration: 1000 } }
    });
  } else {
    console.warn('No academic data available');
  }

  // Financial
  if (scores.financial) {
    document.getElementById('financial-score').textContent = scores.financial.score;
    document.getElementById('financial-trend-text').textContent = `Trend: ${scores.financial.trend} in Week ${week === 'all' ? 'All' : week}`;
    document.getElementById('financial-recommendation').textContent = `Recommendation: ${scores.financial.recommendation}`;
    drawGauge(document.getElementById('financial-gauge').getContext('2d'), scores.financial.score, scores.financial.color);
    new Chart(document.getElementById('financial-trend').getContext('2d'), {
      type: 'line',
      data: {
        labels: scores.financial.trend_labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{ label: 'Financial', data: scores.financial.trend_data || [65, 60, 55, 50], borderColor: scores.financial.color, fill: false }]
      },
      options: { responsive: true, animation: { duration: 1000 } }
    });
  } else {
    console.warn('No financial data available');
  }

  // Health
  if (scores.health) {
    document.getElementById('health-score').textContent = scores.health.score;
    document.getElementById('health-trend-text').textContent = `Trend: ${scores.health.trend} in Week ${week === 'all' ? 'All' : week}`;
    document.getElementById('health-recommendation').textContent = `Recommendation: ${scores.health.recommendation}`;
    drawGauge(document.getElementById('health-gauge').getContext('2d'), scores.health.score, scores.health.color);
    new Chart(document.getElementById('health-trend').getContext('2d'), {
      type: 'line',
      data: {
        labels: scores.health.trend_labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{ label: 'Health', data: scores.health.trend_data || [70, 65, 60, 55], borderColor: scores.health.color, fill: false }]
      },
      options: { responsive: true, animation: { duration: 1000 } }
    });
  } else {
    console.warn('No health data available');
  }

  // Housing
  if (scores.housing) {
    document.getElementById('housing-score').textContent = scores.housing.score;
    document.getElementById('housing-trend-text').textContent = `Trend: ${scores.housing.trend} in Week ${week === 'all' ? 'All' : week}`;
    document.getElementById('housing-recommendation').textContent = `Recommendation: ${scores.housing.recommendation}`;
    drawGauge(document.getElementById('housing-gauge').getContext('2d'), scores.housing.score, scores.housing.color);
    new Chart(document.getElementById('housing-trend').getContext('2d'), {
      type: 'line',
      data: {
        labels: scores.housing.trend_labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{ label: 'Housing', data: scores.housing.trend_data || [68, 63, 58, 53], borderColor: scores.housing.color, fill: false }]
      },
      options: { responsive: true, animation: { duration: 1000 } }
    });
  } else {
    console.warn('No housing data available');
  }

  // Social
  if (scores.social) {
    document.getElementById('social-score').textContent = scores.social.score;
    document.getElementById('social-trend-text').textContent = `Trend: ${scores.social.trend} in Week ${week === 'all' ? 'All' : week}`;
    document.getElementById('social-recommendation').textContent = `Recommendation: ${scores.social.recommendation}`;
    drawGauge(document.getElementById('social-gauge').getContext('2d'), scores.social.score, scores.social.color);
    new Chart(document.getElementById('social-trend').getContext('2d'), {
      type: 'line',
      data: {
        labels: scores.social.trend_labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [{ label: 'Social', data: scores.social.trend_data || [75, 70, 65, 60], borderColor: scores.social.color, fill: false }]
      },
      options: { responsive: true, animation: { duration: 1000 } }
    });
  } else {
    console.warn('No social data available');
  }

  // Radar Chart
  if (Object.keys(scores).length) {
    new Chart(document.getElementById('radar-chart').getContext('2d'), {
      type: 'radar',
      data: {
        labels: ['Academic', 'Financial', 'Health', 'Housing', 'Social'],
        datasets: [{
          label: `Stress Scores (Week ${week === 'all' ? 'All' : week})`,
          data: [
            scores.academic?.score || 0,
            scores.financial?.score || 0,
            scores.health?.score || 0,
            scores.housing?.score || 0,
            scores.social?.score || 0
          ],
          backgroundColor: 'rgba(147, 51, 234, 0.2)',
          borderColor: '#9333EA',
          pointBackgroundColor: '#9333EA'
        }]
      },
      options: { responsive: true, animation: { duration: 1500 } }
    });
    document.getElementById('all-summary').textContent = scores.summary || 'Summary: No data available';
    document.getElementById('all-recommendation').textContent = `Recommendation: ${scores.recommendation || 'No recommendation available'}`;
  }

  // Keywords
  if (keywords.length) {
    const cloud = document.getElementById('keyword-cloud');
    cloud.innerHTML = '';
    keywords.forEach((kw, i) => {
      const span = document.createElement('span');
      span.className = 'keyword';
      span.style.left = `${Math.random() * (cloud.offsetWidth - 100)}px`;
      span.style.top = `${Math.random() * (cloud.offsetHeight - 50)}px`;
      span.style.fontSize = `${10 + kw.frequency * 5}px`;
      span.textContent = kw.keyword;
      const tooltip = document.createElement('span');
      tooltip.className = 'keyword-tooltip';
      tooltip.textContent = `Category: ${kw.category}, Sample: ${kw.sample}`;
      span.appendChild(tooltip);
      cloud.appendChild(span);
    });

    const table = document.getElementById('keyword-table');
    table.innerHTML = '<tr class="border-b border-gray-700"><th>Keyword</th><th>Frequency</th><th>Category</th><th>Sample Post</th></tr>';
    keywords.forEach(kw => {
      const row = document.createElement('tr');
      row.innerHTML = `<td>${kw.keyword}</td><td>${kw.frequency}</td><td>${kw.category}</td><td>${kw.sample}</td>`;
      table.appendChild(row);
    });
  }

  // Recommendations
  if (recommendations.length) {
    const list = document.getElementById('gemini-recommendations');
    list.innerHTML = '';
    recommendations.forEach(rec => {
      const li = document.createElement('li');
      li.className = 'py-2';
      li.textContent = `For "${rec.keyword}": ${rec.suggestion} (Generated by Gemini)`;
      list.appendChild(li);
    });
    document.getElementById('resources-alert').textContent = `Alert: ${recommendations.length} recommendations generated`;
  }
}

// Initial Fetch
fetchData('4');