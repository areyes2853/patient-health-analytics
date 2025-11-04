// Epic FHIR Patient Dashboard - JavaScript
// Using LOCAL PostgreSQL Database (no external APIs needed!)

let observationsModalInstance = null;

// ===== FETCH PATIENTS FROM LOCAL DATABASE =====
fetch('/api/patients')
  .then((res) => {
    console.log('Response status:', res.status);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
  })
  .then((data) => {
    console.log('Patient data received:', data);

    // Check if there's an error in the response
    if (data.error) {
      throw new Error(data.error);
    }

    // Check if data.data exists and is an array
    if (!data.data || !Array.isArray(data.data)) {
      console.error('Invalid data structure:', data);
      throw new Error('No patient data returned from database');
    }

    let html = '';

    // Display patient cards with avatars
    data.data.forEach((patient) => {
      const dob = patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A';
      
      html += `
                <div class="patient-card">
                    <div class="patient-avatar" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; width: 60px; height: 60px; border-radius: 50%; font-size: 24px; font-weight: bold;">
                        ${patient.first_name.charAt(0)}${patient.last_name.charAt(0)}
                    </div>
                    <div class="patient-info">
                        <h3>${patient.first_name} ${patient.last_name}</h3>
                        <p>DOB: ${dob}</p>
                        <p>Email: ${patient.email || 'N/A'}</p>
                        <p><small class="text-muted">ID: ${patient.id}</small></p>
                    </div>
                </div>
            `;
    });

    if (html === '') {
      html = '<div class="alert alert-info">No patients found in database</div>';
    }

    document.getElementById('patients-container').innerHTML = html;

    // Show total count
    const countHtml = `
      <div class="alert alert-info">
        <strong>Total Patients in Database:</strong> ${data.count}
      </div>
    `;
    document.getElementById('patients-container').innerHTML = countHtml + document.getElementById('patients-container').innerHTML;
  })
  .catch((err) => {
    console.error('Error details:', err);
    document.getElementById(
      'patients-container'
    ).innerHTML = `
      <div class="alert alert-danger">
        <h4>Error loading patients from database:</h4>
        <p>${err.message}</p>
        <hr>
        <p><small>This dashboard queries your local PostgreSQL database</small></p>
        <p><small>Check the browser console (F12) for more details</small></p>
      </div>
    `;
  });

// ===== FETCH CONDITIONS ANALYTICS =====
fetch('/api/analytics/patient-conditions')
  .then((res) => res.json())
  .then((data) => {
    console.log('Conditions data:', data);
    
    if (data.data && data.data.length > 0) {
      let html = '<h4>Conditions by Patient Count</h4>';
      html += '<table class="table table-striped"><thead><tr><th>Condition</th><th>Patient Count</th></tr></thead><tbody>';
      
      data.data.forEach((item) => {
        html += `<tr><td>${item.condition}</td><td>${item.patient_count}</td></tr>`;
      });
      
      html += '</tbody></table>';
      
      const conditionsSection = document.getElementById('table-container');
      if (conditionsSection) {
        conditionsSection.innerHTML = html;
        conditionsSection.style.display = 'block';
      }
    }
  })
  .catch((err) => {
    console.log('Could not load conditions data:', err.message);
  });
