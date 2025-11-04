// Bulk Export Dashboard - JavaScript
// Using LOCAL PostgreSQL Database (no external APIs needed!)

document.addEventListener('DOMContentLoaded', () => {
  loadPatients();
  loadConditions();
});

// ===== LOAD PATIENTS FROM LOCAL DATABASE =====
function loadPatients() {
  fetch('/api/patients')
    .then((res) => {
      console.log('Patients response status:', res.status);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      return res.json();
    })
    .then((data) => {
      console.log('Patient data:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      if (!data.data || !Array.isArray(data.data)) {
        throw new Error('No patient data returned');
      }

      let html = '';

      // Display patient cards
      data.data.forEach((patient) => {
        const dob = patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A';
        
        html += `
          <div class="patient-card">
            <div class="patient-avatar" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; width: 70px; height: 70px; border-radius: 50%; font-size: 28px; font-weight: bold; margin-right: 15px;">
              ${patient.first_name.charAt(0)}${patient.last_name.charAt(0)}
            </div>
            <div class="patient-info">
              <h3>${patient.first_name} ${patient.last_name}</h3>
              <p>DOB: ${dob}</p>
              <p>Email: <a href="mailto:${patient.email}">${patient.email || 'N/A'}</a></p>
              <small class="text-muted">Patient ID: ${patient.id}</small>
            </div>
          </div>
        `;
      });

      if (html === '') {
        html = '<div class="alert alert-info">No patients found in database</div>';
      }

      document.getElementById('patients-container').innerHTML = html;

      // Show total count badge
      const statsHtml = `
        <div class="alert alert-success" style="margin-bottom: 20px;">
          <h5>📊 Database Statistics</h5>
          <p><strong>Total Patients:</strong> ${data.count}</p>
          <p><small>Data from: Local PostgreSQL Database</small></p>
        </div>
      `;

      const container = document.getElementById('patients-container');
      container.innerHTML = statsHtml + container.innerHTML;
    })
    .catch((err) => {
      console.error('Error loading patients:', err);
      document.getElementById('patients-container').innerHTML = `
        <div class="alert alert-danger">
          <h4>Error loading patients:</h4>
          <p>${err.message}</p>
          <small>Check browser console (F12) for details</small>
        </div>
      `;
    });
}

// ===== LOAD CONDITIONS FROM LOCAL DATABASE =====
function loadConditions() {
  fetch('/api/analytics/patient-conditions')
    .then((res) => res.json())
    .then((data) => {
      console.log('Conditions data:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      if (!data.data || !Array.isArray(data.data)) {
        throw new Error('No conditions data');
      }

      // Build conditions table
      let tableHtml = `
        <table class="table table-striped table-hover">
          <thead class="table-dark">
            <tr>
              <th>Condition Name</th>
              <th>Patient Count</th>
            </tr>
          </thead>
          <tbody>
      `;

      data.data.forEach((item) => {
        tableHtml += `
          <tr>
            <td><strong>${item.condition}</strong></td>
            <td><span class="badge bg-primary">${item.patient_count}</span></td>
          </tr>
        `;
      });

      tableHtml += `
          </tbody>
        </table>
      `;

      document.getElementById('pandas-table').innerHTML = tableHtml;
      document.getElementById('table-container').style.display = 'block';
    })
    .catch((err) => {
      console.log('Could not load conditions data:', err.message);
      // This is optional, so don't show error if it fails
    });
}
