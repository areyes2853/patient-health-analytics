// Epic FHIR Patient Dashboard - JavaScript

let observationsModalInstance = null;

// ===== FETCH EPIC PATIENTS =====
fetch('/api/epic/patients')
  .then((res) => res.json())
  .then((data) => {
    let html = '';

    // Display patient cards with avatars
    data.data.forEach((patient) => {
      html += `
                <div class="patient-card">
                    <img src="${patient.avatar}" alt="${patient.first_name}" class="patient-avatar">
                    <div class="patient-info">
                        <h3>${patient.first_name} ${patient.last_name}</h3>
                        <p>DOB: ${patient.dob} | Gender: ${patient.gender}</p>
                        <p style="margin-top: 10px;">
                            <button class="btn btn-sm btn-primary" onclick="loadObservations('${patient.id}', '${patient.first_name} ${patient.last_name}')">
                                View Labs
                            </button>
                        </p>
                    </div>
                </div>
            `;
    });

    document.getElementById('patients-container').innerHTML = html;

    // Show pandas table
    if (data.table_html) {
      document.getElementById('pandas-table').innerHTML = data.table_html;
      document.getElementById('table-container').style.display = 'block';
    }
  })
  .catch((err) => {
    document.getElementById(
      'patients-container'
    ).innerHTML = `<div class="alert alert-danger">Error loading patients: ${err.message}</div>`;
  });

// ===== LOAD OBSERVATIONS FOR PATIENT =====
function loadObservations(patientId, patientName) {
  fetch(`/api/epic/observations/${patientId}`)
    .then((res) => res.json())
    .then((data) => {
      // Set modal title
      document.getElementById(
        'observationsTitle'
      ).textContent = `Labs & Observations for ${patientName}`;

      if (data.error) {
        document.getElementById(
          'observations-content'
        ).innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
      } else if (data.data && data.data.length > 0) {
        // Build table
        let html = `
                    <table class="observations-table">
                        <thead>
                            <tr>
                                <th>Test Name</th>
                                <th>Value</th>
                                <th>Unit</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

        data.data.forEach((obs) => {
          const date = obs.date
            ? new Date(obs.date).toLocaleDateString()
            : 'N/A';
          html += `
                        <tr>
                            <td>${obs.code}</td>
                            <td><strong>${obs.value}</strong></td>
                            <td>${obs.unit || 'N/A'}</td>
                            <td>${date}</td>
                        </tr>
                    `;
        });

        html += `
                        </tbody>
                    </table>
                    <div style="margin-top: 20px;">
                        <button class="btn btn-success" onclick="saveObservationsToDb('${patientId}')">
                            💾 Save to Database
                        </button>
                    </div>
                `;

        document.getElementById('observations-content').innerHTML = html;
      } else {
        document.getElementById(
          'observations-content'
        ).innerHTML = `<div class="alert alert-info">No observations found for this patient.</div>`;
      }

      // Show modal
      observationsModalInstance = new bootstrap.Modal(
        document.getElementById('observationsModal')
      );
      observationsModalInstance.show();
    })
    .catch((err) => {
      document.getElementById(
        'observations-content'
      ).innerHTML = `<div class="alert alert-danger">Error loading observations: ${err.message}</div>`;
      observationsModalInstance = new bootstrap.Modal(
        document.getElementById('observationsModal')
      );
      observationsModalInstance.show();
    });
}

// ===== SAVE OBSERVATIONS TO DATABASE =====
function saveObservationsToDb(patientId) {
  fetch(`/api/epic/save-observations/${patientId}`, {
    method: 'POST',
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.message) {
        alert(`✅ Success! Saved ${data.count} observations to database`);
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    })
    .catch((err) => alert(`❌ Error: ${err.message}`));
}
