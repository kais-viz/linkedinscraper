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

    /* Cover letter section commented out
    if ('cover_letter' in jobData) {
        updateCoverLetter(jobData.cover_letter);
    } else {
        updateCoverLetter(null);
    }
    */
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
                        starButton.innerHTML = 'Unstar Job';
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
                        starButton.innerHTML = 'Star Job';
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
    // var coverLetterDiv = document.getElementById('bottom-pane'); // Get the cover letter div - commented out
    console.log('Updating job details: ' + job.id); // Log the jobId here
    var html = '<h2 class="job-title">' + job.title + '</h2>';
    
    // Add star button next to title
    var isStarred = job.starred === 1;
    html += '<button id="star-job-button" class="job-button star-button' + (isStarred ? ' starred' : '') + '" onclick="toggleStar(' + job.id + ')">' + 
            (isStarred ? 'Unstar Job' : 'Star Job') + '</button>';
    
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
    html += '<a href="' + job.job_url + '" target="_blank" style="background-color: #0058db;" class="job-button">Go to job</a>';
    // html += '<button class="job-button" onclick="markAsCoverLetter(' + job.id + ')">Cover Letter</button>';
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

    jobDetailsDiv.innerHTML = html;
    /* Cover letter section commented out
    if (job.cover_letter) {
        // Update the cover letter div with formatted text using markdown
        var formattedCoverLetter = markdownToHtml(job.cover_letter);
        coverLetterDiv.innerHTML = '<div class="job-description">' + formattedCoverLetter + '</div>';
    } else {
        // Clear the cover letter div if no cover letter exists
        coverLetterDiv.innerHTML = '';
    }
    */
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

function markAsCoverLetter(jobId) {
    console.log('Marking job as cover letter: ' + jobId)
    fetch('/get_CoverLetter/' + jobId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Log the response
            if (data.cover_letter) {
                // Show the job details again, this will also update the cover letter
                showJobDetails(jobId);
            }
        });
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
            }
        });
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

/* Resizer functionality commented out since we don't need it without the cover letter section
var resizer = document.getElementById('resizer');
var jobDetails = document.getElementById('job-details');
var bottomPane = document.getElementById('bottom-pane');
var originalHeight, originalMouseY;

resizer.addEventListener('mousedown', function(e) {
    e.preventDefault();
    originalHeight = jobDetails.getBoundingClientRect().height;
    originalMouseY = e.pageY;
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
});

function drag(e) {
    var delta = e.pageY - originalMouseY;
    jobDetails.style.height = (originalHeight + delta) + "px";
    bottomPane.style.height = `calc(100% - ${originalHeight + delta}px - 10px)`;
}

function stopDrag() {
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDrag);
}
*/
