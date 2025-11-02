// Patient Health Analytics Dashboard - Main JavaScript

const API_BASE = '/api';

// ===== PATIENT COUNT =====
fetch(`${API_BASE}/patients/count`)
  .then((res) => res.json())
  .then((data) => {
    document.getElementById('count-data').textContent = data.data;
    document.getElementById('count-desc').textContent = data.description;
    document.getElementById('count-query').textContent = data.query;
    document.getElementById('count-time').textContent = `Updated: ${new Date(
      data.timestamp
    ).toLocaleString()}`;
  })
  .catch((err) => {
    document.getElementById(
      'count-data'
    ).innerHTML = `<div class="error">Error: ${err.message}</div>`;
  });

// ===== ALL PATIENTS =====
fetch(`${API_BASE}/patients`)
  .then((res) => res.json())
  .then((data) => {
    document.getElementById('patients-desc').textContent = data.description;
    document.getElementById('patients-query').textContent = data.query;
    document.getElementById('patients-time').textContent = `Updated: ${new Date(
      data.timestamp
    ).toLocaleString()}`;

    let html = `<table>
            <tr>
                <th>ID</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Date of Birth</th>
                <th>Email</th>
            </tr>`;

    data.data.forEach((patient) => {
      html += `<tr>
                <td>${patient.id}</td>
                <td>${patient.first_name}</td>
                <td>${patient.last_name}</td>
                <td>${patient.date_of_birth}</td>
                <td>${patient.email}</td>
            </tr>`;
    });

    html += '</table>';
    document.getElementById('patients-data').innerHTML = html;
  })
  .catch((err) => {
    document.getElementById(
      'patients-data'
    ).innerHTML = `<div class="error">Error: ${err.message}</div>`;
  });

// ===== ALL CONDITIONS =====
fetch(`${API_BASE}/conditions`)
  .then((res) => res.json())
  .then((data) => {
    document.getElementById('all-conditions-desc').textContent =
      data.description;
    document.getElementById('all-conditions-query').textContent = data.query;
    document.getElementById(
      'all-conditions-time'
    ).textContent = `Updated: ${new Date(data.timestamp).toLocaleString()}`;

    let html = `<table>
            <tr>
                <th>ID</th>
                <th>Condition Name</th>
                <th>Description</th>
                <th>Severity</th>
            </tr>`;

    data.data.forEach((condition) => {
      html += `<tr>
                <td>${condition.id}</td>
                <td>${condition.name}</td>
                <td>${condition.description}</td>
                <td>${condition.severity}</td>
            </tr>`;
    });

    html += '</table>';
    document.getElementById('all-conditions-data').innerHTML = html;
  })
  .catch((err) => {
    document.getElementById(
      'all-conditions-data'
    ).innerHTML = `<div class="error">Error: ${err.message}</div>`;
  });

// ===== PATIENT CONDITIONS ANALYTICS =====
fetch(`${API_BASE}/analytics/patient-conditions`)
  .then((res) => res.json())
  .then((data) => {
    document.getElementById('conditions-desc').textContent = data.description;
    document.getElementById('conditions-query').textContent = data.query;
    document.getElementById(
      'conditions-time'
    ).textContent = `Updated: ${new Date(data.timestamp).toLocaleString()}`;

    let html = `<table>
            <tr>
                <th>Condition</th>
                <th>Patient Count</th>
            </tr>`;

    data.data.forEach((item) => {
      html += `<tr>
                <td>${item.condition}</td>
                <td>${item.patient_count}</td>
            </tr>`;
    });

    html += '</table>';
    document.getElementById('conditions-data').innerHTML = html;
  })
  .catch((err) => {
    document.getElementById(
      'conditions-data'
    ).innerHTML = `<div class="error">Error: ${err.message}</div>`;
  });

// ===== SAVED EPIC OBSERVATIONS =====
fetch(`${API_BASE}/saved-epic-observations`)
  .then((res) => res.json())
  .then((data) => {
    document.getElementById('epic-obs-desc').textContent =
      data.count > 0
        ? `${data.count} observations from Epic FHIR`
        : 'No observations saved yet';
    document.getElementById('epic-obs-time').textContent = `Updated: ${new Date(
      data.timestamp
    ).toLocaleString()}`;

    if (data.count > 0) {
      let html = `<table>
                <tr>
                    <th>Patient Name</th>
                    <th>Test Name</th>
                    <th>Value</th>
                    <th>Unit</th>
                    <th>Date</th>
                </tr>`;

      data.data.forEach((obs) => {
        const date = obs.date ? new Date(obs.date).toLocaleDateString() : 'N/A';
        html += `<tr>
                    <td>${obs.patient_name}</td>
                    <td>${obs.test_name}</td>
                    <td>${obs.value}</td>
                    <td>${obs.unit || 'N/A'}</td>
                    <td>${date}</td>
                </tr>`;
      });

      html += '</table>';
      document.getElementById('epic-obs-data').innerHTML = html;
    } else {
      document.getElementById('epic-obs-data').innerHTML =
        '<div style="text-align: center; color: #999; padding: 40px;">No saved observations yet. Go to Epic FHIR dashboard and click "Save to Database" to see data here.</div>';
    }
  })
  .catch((err) => {
    document.getElementById(
      'epic-obs-data'
    ).innerHTML = `<div class="error">Error: ${err.message}</div>`;
  });
