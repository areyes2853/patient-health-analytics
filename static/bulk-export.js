// Bulk Epic FHIR Export - JavaScript

let currentData = null;
let genderChart = null;
let ageChart = null;

// ===== LOAD BULK DATA FROM EPIC =====
function loadBulkData() {
  document.getElementById('loading').style.display = 'block';
  document.getElementById('exportBtn').disabled = true;

  fetch('/api/epic/bulk-export')
    .then((res) => res.json())
    .then((data) => {
      currentData = data;
      displayStats(data);
      displayCharts(data);
      displayTable(data);

      document.getElementById('loading').style.display = 'none';
      document.getElementById('stats-container').style.display = 'block';
      document.getElementById('charts-section').style.display = 'block';
      document.getElementById('table-section').style.display = 'block';
      document.getElementById('exportBtn').disabled = false;
    })
    .catch((err) => {
      alert('Error: ' + err.message);
      document.getElementById('loading').style.display = 'none';
      document.getElementById('exportBtn').disabled = false;
    });
}

// ===== DISPLAY STATISTICS =====
function displayStats(data) {
  document.getElementById('total-patients').textContent =
    data.stats.total_patients;
  document.getElementById('male-count').textContent =
    data.stats.gender_counts.male;
  document.getElementById('female-count').textContent =
    data.stats.gender_counts.female;
  document.getElementById('avg-age').textContent = data.stats.average_age
    ? Math.round(data.stats.average_age)
    : 'N/A';
}

// ===== DISPLAY CHARTS =====
function displayCharts(data) {
  // Gender Chart
  const genderCtx = document.getElementById('genderChart').getContext('2d');
  if (genderChart) genderChart.destroy();
  genderChart = new Chart(genderCtx, {
    type: 'doughnut',
    data: {
      labels: ['Male', 'Female', 'Other'],
      datasets: [
        {
          data: [
            data.stats.gender_counts.male,
            data.stats.gender_counts.female,
            data.stats.gender_counts.other,
          ],
          backgroundColor: ['#007bff', '#ff69b4', '#6c757d'],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
    },
  });

  // Age Chart
  const ageCtx = document.getElementById('ageChart').getContext('2d');
  if (ageChart) ageChart.destroy();

  // Create age bins
  const ages = data.data.map((p) => p.age).filter((a) => a !== null);
  const ageBins = {
    '0-20': 0,
    '21-40': 0,
    '41-60': 0,
    '61-80': 0,
    '80+': 0,
  };

  ages.forEach((age) => {
    if (age <= 20) ageBins['0-20']++;
    else if (age <= 40) ageBins['21-40']++;
    else if (age <= 60) ageBins['41-60']++;
    else if (age <= 80) ageBins['61-80']++;
    else ageBins['80+']++;
  });

  ageChart = new Chart(ageCtx, {
    type: 'bar',
    data: {
      labels: Object.keys(ageBins),
      datasets: [
        {
          label: 'Number of Patients',
          data: Object.values(ageBins),
          backgroundColor: '#28a745',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

// ===== DISPLAY TABLE =====
function displayTable(data) {
  document.getElementById('table-container').innerHTML = data.table_html;
}

// ===== DOWNLOAD AS CSV =====
function downloadCSV() {
  if (!currentData) return;

  let csv = 'ID,First Name,Last Name,DOB,Age,Gender\n';
  currentData.data.forEach((patient) => {
    csv += `${patient.id},"${patient.first_name}","${patient.last_name}",${patient.dob},${patient.age},${patient.gender}\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `bulk-export-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
}

// ===== SAVE TO DATABASE =====
function saveToDB() {
  alert('Save to database feature coming soon!');
}
