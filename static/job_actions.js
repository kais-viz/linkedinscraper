var selectedJob = null;

async function showJobDetails(jobId) {
    if (selectedJob !== null) {
        selectedJob.classList.remove('job-item-selected');
    }
    console.log('Showing job details: ' + jobId); 
    var newSelectedJob = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
    newSelectedJob.classList.add('job-item-selected');
    selectedJob = newSelectedJob;

    const response = await fetch('/job_details/' + jobId);
    const jobData = await response.json();

    updateJobDetails(jobData);
    
    // Load notes for this job after a short delay to ensure the DOM is updated
    setTimeout(() => {
        loadJobNotes(jobId);
    }, 100);
}

// Function to toggle star status for a job
function toggleStar(jobId) {
    console.log('Toggling star for job: ' + jobId);
    fetch('/toggle_star/' + jobId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Log the response
            if (data.success) {
                var jobCard = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
                var starButton = document.getElementById('star-job-button');
                
                if (data.starred === 1) {
                    // Update job card in the list
                    jobCard.classList.add('job-item-starred');
                    // Add star icon if it doesn't exist
                    if (!jobCard.querySelector('.job-star-icon')) {
                        const starIcon = document.createElement('span');
                        starIcon.className = 'job-star-icon';
                        starIcon.innerHTML = '★';
                        jobCard.appendChild(starIcon);
                    }
                    
                    // Update star button
                    if (starButton) {
                        starButton.classList.add('starred');
                    }
                } else {
                    // Update job card in the list
                    jobCard.classList.remove('job-item-starred');
                    // Remove star icon if it exists
                    const starIcon = jobCard.querySelector('.job-star-icon');
                    if (starIcon) {
                        starIcon.remove();
                    }
                    
                    // Update star button
                    if (starButton) {
                        starButton.classList.remove('starred');
                    }
                }
            }
        });
}





/* Cover letter function commented out
function updateCoverLetter(coverLetter) {
    var coverLetterPane = document.getElementById('cover-letter-pane');
    // Check if the coverLetterPane exists
    if (coverLetterPane) {
        // Check if cover letter exists
        if (coverLetter === null) {
            coverLetterPane.innerText = 'No cover letter exists for this job.';
        } else {
            // Use markdown formatting for cover letter
            coverLetterPane.innerHTML = markdownToHtml(coverLetter);
        }
    }
}
*/



function updateJobDetails(job) {
    var jobDetailsDiv = document.getElementById('job-details');
    console.log('Updating job details: ' + job.id); // Log the jobId here
    var html = '<h2 class="job-title">' + job.title + '</h2>';
    
    // Add date with day of week in bold above company
    var formattedDate = formatDateWithDayOfWeek(job.date);
    
    
    // Add job criteria including company and location
    html += '<div class="job-criteria" style="margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px;">';
    html += '<div class="criteria-item job-date"><strong>Posted:</strong> ' + formattedDate + '</div>';
    html += '<div class="criteria-item"><strong>Company:</strong> ' + job.company + '</div>';
    if (job.location) {
        html += '<div class="criteria-item"><strong>Location:</strong> ' + job.location + '</div>';
    }
    if (job.seniority_level) {
        html += '<div class="criteria-item"><strong>Seniority Level:</strong> ' + job.seniority_level + '</div>';
    }
    if (job.employment_type) {
        html += '<div class="criteria-item"><strong>Employment Type:</strong> ' + job.employment_type + '</div>';
    }
    if (job.job_function) {
        html += '<div class="criteria-item"><strong>Job Function:</strong> ' + job.job_function + '</div>';
    }
    if (job.industries) {
        html += '<div class="criteria-item"><strong>Industries:</strong> ' + job.industries + '</div>';
    }
    html += '</div>';
    
    html += '<div class="button-container">';
    // Add star button before Go to job
    var isStarred = job.starred === 1;
    html += '<button id="star-job-button" class="job-button star-button' + (isStarred ? ' starred' : '') + '" onclick="toggleStar(' + job.id + ')">' + 
            '<span class="star-icon">★</span>' + '</button>';
    html += '<a href="' + job.job_url + '" target="_blank" style="background-color: #0058db;" class="job-button">Go to job</a>';
    html += '<button class="job-button" onclick="markAsApplied(' + job.id + ')">Applied</button>';
    html += '<button class="job-button" style="background-color: #cc130e;" onclick="markAsRejected(' + job.id + ')">Rejected</button>';
    html += '<button class="job-button" style="background-color: #a9b024;" onclick="markAsInterview(' + job.id + ')">Interview</button>';
    html += '<button class="job-button" style="background-color: #5f5f5e;" onclick="hideJob(' + job.id + ')">Hide</button>';
    html += '</div>';
    
    // Format job description using markdown
    var formattedDescription = '';
    if (job.job_description) {
        formattedDescription = markdownToHtml(job.job_description);
    }
    
    html += '<div class="job-description">' + formattedDescription + '</div>';

    // Only update the job details div, not the notes section
    jobDetailsDiv.innerHTML = html;
    
    // Store the job ID in a data attribute on the page for reference
    document.body.dataset.currentJobId = job.id;
}


function markAsApplied(jobId) {
    console.log('Marking job as applied: ' + jobId)
    fetch('/mark_applied/' + jobId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Log the response
            if (data.success) {
                var jobCard = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
                jobCard.classList.add('job-item-applied');
            }
        });
}

// Function to load notes for a job
async function loadJobNotes(jobId) {
    console.log('Loading notes for job: ' + jobId);
    try {
        const response = await fetch('/get_notes/' + jobId);
        const data = await response.json();
        
        // Get the notes textarea
        const notesTextarea = document.getElementById('job-notes');
        
        // Set the notes content
        if (notesTextarea) {
            console.log('Found notes textarea, setting value to:', data.notes);
            notesTextarea.value = data.notes || '';
            // Store the current job ID
            notesTextarea.dataset.jobId = jobId;
        } else {
            console.error('Notes textarea not found in the DOM');
        }
    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

// Function to save notes for a job
async function saveNotes() {
    const notesTextarea = document.getElementById('job-notes');
    if (!notesTextarea) {
        console.error('Notes textarea not found');
        return;
    }
    
    // Get job ID from textarea data attribute or from body data attribute
    let jobId = notesTextarea.dataset.jobId;
    if (!jobId) {
        jobId = document.body.dataset.currentJobId;
    }
    
    if (!jobId) {
        console.error('No job ID found for notes');
        return;
    }
    
    console.log('Saving notes for job ID:', jobId);
    const notes = notesTextarea.value;
    
    try {
        const response = await fetch('/save_notes/' + jobId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ notes: notes })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show a success message
            const saveStatus = document.getElementById('save-status');
            if (saveStatus) {
                saveStatus.textContent = 'Notes saved!';
                saveStatus.style.display = 'inline';
                
                // Hide the message after 2 seconds
                setTimeout(() => {
                    saveStatus.style.display = 'none';
                }, 2000);
            }
            
            // Update the data attribute with the current job ID
            notesTextarea.dataset.jobId = jobId;
        }
    } catch (error) {
        console.error('Error saving notes:', error);
    }
}

function markAsRejected(jobId) {
    console.log('Marking job as rejected: ' + jobId)
    fetch('/mark_rejected/' + jobId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Log the response
            if (data.success) {
                var jobCard = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
                jobCard.classList.add('job-item-rejected');
            }
        });
}

function hideJob(jobId) {
    fetch('/hide_job/' + jobId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                var jobCard = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
                
                // Find the next sibling in the DOM that is a job-item
                var nextJobCard = jobCard.nextElementSibling;
                while(nextJobCard && !nextJobCard.classList.contains('job-item')) {
                    nextJobCard = nextJobCard.nextElementSibling;
                }
                
                // If a next job exists, show its details
                if (nextJobCard) {
                    var nextJobId = nextJobCard.getAttribute('data-job-id');
                    showJobDetails(nextJobId);
                }
                
                // Hide the current job
                jobCard.style.display = 'none'; // Or you can remove it from DOM entirely

                // If no next job exists, clear the job details div
                if (!nextJobCard) {
                    var jobDetailsDiv = document.getElementById('job-details');
                    jobDetailsDiv.innerHTML = '';
                }
                
                // Update job count
                updateJobCount();
            }
        });
}

// Function to toggle visibility of applied/interview/rejected jobs
function toggleAppliedJobs() {
    const toggleButton = document.getElementById('toggle-applied-button');
    const jobItems = document.querySelectorAll('.job-item');
    
    // Toggle the active state of the button
    toggleButton.classList.toggle('active');
    const hideApplied = toggleButton.classList.contains('active');
    
    jobItems.forEach(jobItem => {
        // Check if the job has been applied to, interviewed for, or rejected
        const isApplied = jobItem.classList.contains('job-item-applied');
        const isInterview = jobItem.classList.contains('job-item-interview');
        const isRejected = jobItem.classList.contains('job-item-rejected');
        
        if (hideApplied && (isApplied || isInterview || isRejected)) {
            jobItem.classList.add('applied-hidden');
        } else {
            jobItem.classList.remove('applied-hidden');
        }
    });
    
    // Update the job count
    updateJobCount();
}

// Function to update the job count
function updateJobCount() {
    const jobCountElement = document.getElementById('job-count');
    if (jobCountElement) {
        // Count jobs that are visible (not hidden by any filter)
        const visibleJobs = document.querySelectorAll('.job-item:not([style*="display: none"]):not(.search-hidden):not(.location-hidden):not(.applied-hidden)').length;
        jobCountElement.textContent = visibleJobs;
    }
}

// Function to search jobs by title and description
function searchJobs() {
    const searchText = document.getElementById('job-search').value.toLowerCase();
    const jobItems = document.querySelectorAll('.job-item');
    
    jobItems.forEach(async (jobItem) => {
        const jobId = jobItem.getAttribute('data-job-id');
        const jobTitle = jobItem.querySelector('h3').textContent.toLowerCase();
        const jobCompany = jobItem.querySelector('p').textContent.toLowerCase();
        
        // Don't process already hidden jobs
        if (jobItem.style.display === 'none') {
            return;
        }
        
        // First check if the search term is in the title or company
        if (searchText === '' || jobTitle.includes(searchText) || jobCompany.includes(searchText)) {
            jobItem.classList.remove('search-hidden');
        } else {
            // If not found in title/company, fetch job details to check description
            try {
                const response = await fetch('/job_details/' + jobId);
                const jobData = await response.json();
                const jobDescription = jobData.job_description.toLowerCase();
                
                if (jobDescription.includes(searchText)) {
                    jobItem.classList.remove('search-hidden');
                } else {
                    jobItem.classList.add('search-hidden');
                }
            } catch (error) {
                console.error('Error fetching job details:', error);
            }
        }
    });
    
    // Update the job count after all async operations are done
    setTimeout(updateJobCount, 500);
}

// Function to clear the search
function clearSearch() {
    document.getElementById('job-search').value = '';
    const jobItems = document.querySelectorAll('.job-item');
    
    jobItems.forEach(jobItem => {
        jobItem.classList.remove('search-hidden');
    });
    
    // Update the job count
    updateJobCount();
}

// Function to filter jobs by location
function filterByLocation() {
    const locationText = document.getElementById('location-search').value.toLowerCase();
    const jobItems = document.querySelectorAll('.job-item');
    
    jobItems.forEach(jobItem => {
        // Don't process already hidden jobs
        if (jobItem.style.display === 'none') {
            return;
        }
        
        const jobLocation = jobItem.querySelector('p').textContent.toLowerCase();
        
        if (locationText === '' || jobLocation.includes(locationText)) {
            jobItem.classList.remove('location-hidden');
        } else {
            jobItem.classList.add('location-hidden');
        }
    });
    
    // Update the job count
    updateJobCount();
}

// Function to clear the location filter
function clearLocationFilter() {
    document.getElementById('location-search').value = '';
    const jobItems = document.querySelectorAll('.job-item');
    
    jobItems.forEach(jobItem => {
        jobItem.classList.remove('location-hidden');
    });
    
    // Update the job count
    updateJobCount();
}


function markAsInterview(jobId) {
    console.log('Marking job as interview: ' + jobId)
    fetch('/mark_interview/' + jobId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Log the response
            if (data.success) {
                var jobCard = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
                jobCard.classList.add('job-item-interview');
            }
        });
}

// Debounce function to limit how often a function is called
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

// Add event listener for auto-save on input
document.addEventListener('click', function(event) {
    // This will run once after the DOM is fully loaded
    const notesTextarea = document.getElementById('job-notes');
    if (notesTextarea && !notesTextarea.hasAutoSave) {
        notesTextarea.hasAutoSave = true;
        notesTextarea.addEventListener('input', debounce(saveNotes, 1000));
    }
});

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Toggle Applied button functionality
    const toggleAppliedButton = document.getElementById('toggle-applied-button');
    if (toggleAppliedButton) {
        toggleAppliedButton.addEventListener('click', toggleAppliedJobs);
        // Set initial state to active (hide applied jobs by default)
        toggleAppliedButton.classList.add('active');
        toggleAppliedJobs();
    }
    
    // Resizer functionality for notes section
    var resizer = document.getElementById('resizer');
    var jobDetails = document.getElementById('job-details');
    var bottomPane = document.getElementById('bottom-pane');
    
    if (resizer && jobDetails && bottomPane) {
        var originalHeight, originalMouseY;
        
        resizer.addEventListener('mousedown', function(e) {
            e.preventDefault();
            originalHeight = jobDetails.getBoundingClientRect().height;
            originalMouseY = e.pageY;
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDrag);
        });
        
        function drag(e) {
            e.preventDefault(); // Prevent text selection during drag
            var delta = e.pageY - originalMouseY;
            
            // Calculate new heights
            var newJobDetailsHeight = (originalHeight + delta);
            var containerHeight = jobDetails.parentElement.getBoundingClientRect().height;
            
            // Ensure minimum heights for both sections
            if (newJobDetailsHeight < 200) {
                newJobDetailsHeight = 200;
            } else if (containerHeight - newJobDetailsHeight < 200) {
                newJobDetailsHeight = containerHeight - 200;
            }
            
            // Apply the new heights
            jobDetails.style.height = newJobDetailsHeight + "px";
            bottomPane.style.height = (containerHeight - newJobDetailsHeight - 15) + "px"; // Reduced from 25px to 15px
        }
        
        function stopDrag() {
            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', stopDrag);
        }
    }
    
    // Set up save button event listener
    const saveButton = document.getElementById('save-notes-button');
    if (saveButton) {
        saveButton.addEventListener('click', saveNotes);
    }
    
    // Set up auto-save for notes textarea
    const notesTextarea = document.getElementById('job-notes');
    if (notesTextarea) {
        notesTextarea.addEventListener('input', debounce(saveNotes, 1000));
    }
});
