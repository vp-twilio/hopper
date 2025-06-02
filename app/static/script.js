$(document).ready(function () {

    let currentScriptId = 1;

    const runHistoryTable = $('#runHistoryTable').DataTable({
        ajax: {
            url: `/runs/script/${currentScriptId}`, // Replace with the correct endpoint
            dataSrc: '' // Adjust based on the API response structure
        },
        columns: [
            {data: null, render: (data, type, row, meta) => meta.row + 1}, // Row number
            {data: 'script_name', defaultContent: 'N/A'}, // Script Name
            {data: 'filename', defaultContent: 'N/A'}, // File Name
            {data: 'web_port', defaultContent: 'N/A'}, // Port
            {data: 'env', defaultContent: 'N/A'}, // Environment
            {data: 'status', defaultContent: 'N/A'}, // Status of the run
            {data: 'started_at', defaultContent: 'N/A'}, // Start time
            {data: 'completed_at', defaultContent: 'N/A'}, // Completion time
            {
                data: null,
                render: (data) => {
                    if (data.status === 'running') {
                        return `
                <button class="btn btn-danger btn-sm stop-run-btn" data-id="${data.id}">Stop Run</button>
                <a href="http://${window.location.hostname}:${data.web_port}" target="_blank" class="btn btn-primary btn-sm">Locust UI</a>
            `;
                    } else if (data.status === 'completed') {
                        return `
                <a href="/runs/${data.id}/report" target="_blank" class="btn btn-success btn-sm">Download Report</a>
            `;
                    }
                    return ''; // No button for other statuses
                }
            }  // Actions column
        ],
        order: [[6, 'desc']],
        autoWidth: false,
        paging: true,
        searching: true,
        ordering: true,
        dom: "<'row'<'col-sm-12'f>>" + // Search box
            "<'row'<'col-sm-12'tr>>" + // Table
            "<'row'<'col-sm-4'l><'col-sm-4'i><'col-sm-4'p>>", // Info and pagination
        lengthMenu: [10, 25, 50, 100],
        language: {
            lengthMenu: "Show _MENU_ entries"
        }
    });

    // Handle Back to Scripts button
    $('#backToScriptsBtn').on('click', function () {
        $('#runHistorySection').hide();
        $('#scriptsSection').show();
    });

    // Handle New Run button
    $('#newRunBtn').on('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('newRunModal'));
        modal.show();
    });

    // Handle New Run form submission
    $('#newRunForm').on('submit', function (e) {
        e.preventDefault();
        const formData = {
            script_id: currentScriptId,
            users: $('#users').val(),
            spawn_rate: $('#spawnRate').val(),
            run_time: $('#runTime').val(),
            env: $('#env').val(),
            web_port: $('#webPort').val()
        };

        console.log(formData);

        $.ajax({
            url: '/runs/start-test',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData), // Convert formData to JSON
            success: function () {
                alert('Test run started successfully!');
                $('#newRunModal').modal('hide');
                runHistoryTable.ajax.reload();
            },
            error: function () {
                alert('Failed to start test run.');
            }
        });
    });

    // Handle actions in the Run History table
    $('#runHistoryTable').on('click', '.view-status-btn', function () {
        const runId = $(this).data('id');
        $.get(`/runs/status/${runId}`, function (status) {
            alert(`Status: ${status.status}\nStarted At: ${status.started_at}\nCompleted At: ${status.completed_at || 'In Progress'}`);
        });
    });

    $('#runHistoryTable').on('click', '.stop-run-btn', function () {
        const runId = $(this).data('id');
        if (confirm('Are you sure you want to stop this run?')) {
            const loader = document.createElement('div');
            loader.className = 'position-fixed top-50 start-50 translate-middle';
            loader.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            `;
            document.body.appendChild(loader);
            $.post(`/runs/stop-test/${runId}`, function () {
                alert('Test run stopped successfully!');
                runHistoryTable.ajax.reload();
            }).fail(function () {
                alert('Failed to stop test run.');
            }).always(function () {
                // Hide loader
                loader.remove();
            });
        }
    });

    // Initialize DataTable
    const table = $('#scriptsTable').DataTable({
        ajax: {
            url: '/scripts/',
            dataSrc: ''
        },
        columns: [
            {data: null, render: (data, type, row, meta) => meta.row + 1},
            {data: 'name'},
            {data: 'filename', defaultContent: 'N/A'},
            {data: 'team_name', defaultContent: 'N/A'},
            {data: 'service_name', defaultContent: 'N/A'},
            {
                data: null,
                render: (data) => `
          <button class="btn btn-info btn-sm view-btn" data-id="${data.id}">View</button>
          <button class="btn btn-warning btn-sm update-btn" data-id="${data.id}">Update</button>
          <button class="btn btn-danger btn-sm delete-btn" data-id="${data.id}">Delete</button>
          <button class="btn btn-success btn-sm run-btn" data-id="${data.id}">Run History</button>
          <button class="btn btn-primary btn-sm run-btn" data-id="${data.id}">Run</button>
        `
            }
        ],
        autoWidth: false,
        paging: true,
        searching: true,
        ordering: true,
        dom: "<'row'<'col-sm-12'f>>" + // Length menu (left) and search box (right)
            "<'row'<'col-sm-12'tr>>" + // Table
            "<'row'<'col-sm-4'l><'col-sm-4'i><'col-sm-4'p>>", // Info (left) and pagination (right)
        lengthMenu: [10, 25, 50, 100], // Options for "Show X entries"
        language: {
            lengthMenu: "Show _MENU_ entries"
        }
    });

    // Populate team filter dropdown
    $.get('/teams/', function (teams) {
        const teamFilter = $('#teamFilter');
        teams.forEach(team => {
            teamFilter.append(`<option value="${team.name}">${team.name}</option>`);
        });
    });

    // Filter table based on team selection
    $('#teamFilter').on('change', function () {
        const selectedTeam = $(this).val();
        table.column(3).search(selectedTeam).draw();
    });

    // Handle Add Script button
    $('#addScriptBtn').on('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('addScriptModal'));
        modal.show();
        loadDropdowns().then(() => {

        }); // Populate team and service dropdowns
    });

    // Handle Add Script form submission
    $('#addScriptForm').on('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(this);

        // Debugging: Log form data
        for (const [key, value] of formData.entries()) {
            console.log(`${key}:`, value);
        }

        $.ajax({
            url: '/scripts/',
            type: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function () {
                alert('Script added successfully!');
                $('#addScriptModal').modal('hide');
                $('#scriptsTable').DataTable().ajax.reload();
            },
            error: function () {
                alert('Failed to add script.');
            }
        });
    });

    // Handle Run History button
    $('#runHistoryBtn').on('click', function () {
        window.location.href = '/run-history';
    });

    // Populate teams and services dropdowns
    function loadDropdowns() {
        return new Promise((resolve, reject) => {
            // Populate team dropdown
            $.get('/teams/', function (teams) {
                const addTeamSelect = $('#addScriptTeam');
                const updateTeamSelect = $('#scriptTeam');
                addTeamSelect.empty().append('<option value="" disabled selected>Select Team</option>');
                updateTeamSelect.empty().append('<option value="" disabled>Select Team</option>');
                teams.forEach(team => {
                    addTeamSelect.append(`<option value="${team.id}">${team.name}</option>`);
                    updateTeamSelect.append(`<option value="${team.id}">${team.name}</option>`);
                });

                // Populate service dropdown
                $.get('/services/', function (services) {
                    const addServiceSelect = $('#addScriptService');
                    const updateServiceSelect = $('#scriptService');
                    addServiceSelect.empty().append('<option value="" disabled selected>Select Service</option>');
                    updateServiceSelect.empty().append('<option value="" disabled>Select Service</option>');
                    services.forEach(service => {
                        addServiceSelect.append(`<option value="${service.id}">${service.name}</option>`);
                        updateServiceSelect.append(`<option value="${service.id}">${service.name}</option>`);
                    });

                    // Resolve the promise after both dropdowns are populated
                    resolve();
                }).fail(reject);
            }).fail(reject);
        });
    }

    // Handle View button
    $('#scriptsTable').on('click', '.view-btn', function () {
        const id = $(this).data('id');
        loadDropdowns().then(() => {
            $.get(`/scripts/${id}`, function (script) {
                $('#scriptForm [name="id"]').val(script.id);
                $('#scriptForm [name="name"]').val(script.name).prop('readonly', true);
                $('#scriptForm [name="description"]').val(script.description).prop('readonly', true);
                $('#scriptForm [name="team_id"]').val(script.team_id).prop('disabled', true);
                $('#scriptForm [name="service_id"]').val(script.service_id).prop('disabled', true);

                // Show downloadable link for the script file
                const downloadLink = `/scripts/${id}/download`;
                $('#scriptFileLink').show().attr('href', downloadLink).text('Download Script File');
                $('#scriptFileInput').hide(); // Hide file input

                $('#scriptModalLabel').text('View Script'); // Set modal title
                $('#updateScriptBtn').hide(); // Hide Update button
                const modal = new bootstrap.Modal(document.getElementById('scriptModal'));
                modal.show();
            });
        });
    });

// Handle Update button
    $('#scriptsTable').on('click', '.update-btn', function () {
        const id = $(this).data('id');
        loadDropdowns().then(() => {
            $.get(`/scripts/${id}`, function (script) {
                $('#scriptForm [name="id"]').val(script.id);
                $('#scriptForm [name="name"]').val(script.name).prop('readonly', false);
                $('#scriptForm [name="description"]').val(script.description).prop('readonly', false);
                $('#scriptForm [name="team_id"]').val(script.team_id).prop('disabled', false);
                $('#scriptForm [name="service_id"]').val(script.service_id).prop('disabled', false);
                $('#scriptFileLink').hide(); // Hide view link
                $('#scriptFileInput').show(); // Show file input
                $('#scriptModalLabel').text('Update Script'); // Set modal title
                $('#updateScriptBtn').show(); // Show Update button
                const modal = new bootstrap.Modal(document.getElementById('scriptModal'));
                modal.show();
            });
        });
    });

    // Handle Update form submission
    $('#scriptForm').on('submit', function (e) {
        e.preventDefault();
        const id = $('#scriptForm [name="id"]').val();
        const formData = new FormData();
        formData.append('name', $('#scriptForm [name="name"]').val());
        formData.append('description', $('#scriptForm [name="description"]').val());
        formData.append('team_id', $('#scriptForm [name="team_id"]').val());
        formData.append('service_id', $('#scriptForm [name="service_id"]').val());

        // Append file if a new file is selected
        const fileInput = $('#scriptFileInput')[0].files[0];
        if (fileInput) {
            formData.append('script_file', fileInput);
        }

        $.ajax({
            url: `/scripts/${id}`,
            type: 'PUT',
            processData: false,
            contentType: false,
            data: formData,
            success: function () {
                alert('Script updated successfully!');
                $('#scriptModal').modal('hide');
                $('#scriptsTable').DataTable().ajax.reload();
            },
            error: function () {
                alert('Failed to update script.');
            }
        });
    });

    // Handle Delete button
    $('#scriptsTable').on('click', '.delete-btn', function () {
        const id = $(this).data('id');
        if (confirm('Are you sure you want to delete this script?')) {
            $.ajax({
                url: `/scripts/${id}`,
                type: 'DELETE',
                success: function () {
                    alert('Script deleted successfully!');
                    table.ajax.reload();
                },
                error: function () {
                    alert('Failed to delete script.');
                }
            });
        }
    });

    // Handle Run button
    $('#scriptsTable').on('click', '.run-btn', function () {
        const id = $(this).data('id');
        currentScriptId = id; // Set the current script ID
        $('#scriptsSection').hide(); // Hide the scripts section
        $('#runHistorySection').show(); // Show the run history section
        $('#runHistoryTable').DataTable().ajax.url(`/runs/script/${currentScriptId}`).load(); // Load run history for the script
    });

    // Load dropdowns when the modal is opened
    //$('#scriptModal').on('show.bs.modal', loadDropdowns);
});