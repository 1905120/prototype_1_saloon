// Configuration
const API_URL = 'http://localhost:8000/api/v1/makerequest';
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TOTAL_STEPS = 5;

// State management
let currentStep = 1;
let formData = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeForm();
    setupEventListeners();
    updateStep();
});

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const themeToggle = document.getElementById('themeToggle');
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-theme');
        themeToggle.textContent = '🌙';
    }
    
    themeToggle.addEventListener('click', toggleTheme);
}

// Toggle theme
function toggleTheme() {
    const body = document.body;
    const themeToggle = document.getElementById('themeToggle');
    
    if (body.classList.contains('dark-theme')) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        themeToggle.textContent = '🌙';
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        themeToggle.textContent = '☀️';
    }
}

// Initialize working hours
function initializeForm() {
    const container = document.getElementById('workingHoursContainer');
    container.innerHTML = '';

    DAYS.forEach(day => {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'working-day';
        dayDiv.innerHTML = `
            <div class="day-header">
                <h4>${day}</h4>
                <label class="checkbox-label">
                    <input type="checkbox" class="is-closed" data-day="${day}">
                    <span>Closed</span>
                </label>
            </div>
            <div class="day-times" data-day="${day}">
                <div class="form-row">
                    <div class="form-group">
                        <label>Open Time</label>
                        <input type="time" class="open-time" data-day="${day}" value="09:00">
                    </div>
                    <div class="form-group">
                        <label>Close Time</label>
                        <input type="time" class="close-time" data-day="${day}" value="18:00">
                    </div>
                </div>
            </div>
        `;
        container.appendChild(dayDiv);
    });

    addWorkingHoursStyles();

    document.querySelectorAll('.is-closed').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const dayTimes = document.querySelector(`.day-times[data-day="${this.dataset.day}"]`);
            dayTimes.style.opacity = this.checked ? '0.5' : '1';
            dayTimes.style.pointerEvents = this.checked ? 'none' : 'auto';
        });
    });
}

function addWorkingHoursStyles() {
    if (document.getElementById('working-hours-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'working-hours-styles';
    style.textContent = `
        .working-day {
            margin-bottom: 15px;
            padding: 12px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .day-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .day-header h4 {
            margin: 0;
            font-size: 13px;
            color: #333;
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-size: 11px;
            color: #666;
        }

        .checkbox-label input {
            margin-right: 5px;
            cursor: pointer;
        }

        .day-times {
            transition: opacity 0.3s;
        }
    `;
    document.head.appendChild(style);
}

// Setup event listeners
function setupEventListeners() {
    const form = document.getElementById('registrationForm');
    const nextBtn = document.getElementById('nextBtn');
    const backBtn = document.getElementById('backBtn');
    const submitBtn = document.getElementById('submitBtn');
    const getLocationBtn = document.getElementById('getLocationBtn');

    nextBtn.addEventListener('click', handleNext);
    backBtn.addEventListener('click', handleBack);
    submitBtn.addEventListener('click', handleSubmit);
    getLocationBtn.addEventListener('click', getLocation);
    form.addEventListener('submit', (e) => e.preventDefault());
}

// Handle Next button
function handleNext() {
    if (!validateCurrentStep()) {
        return;
    }

    saveCurrentStepData();

    if (currentStep < TOTAL_STEPS) {
        currentStep++;
        updateStep();
    }
}

// Handle Back button
function handleBack() {
    saveCurrentStepData();

    if (currentStep > 1) {
        currentStep--;
        updateStep();
    }
}

// Handle Submit
async function handleSubmit(e) {
    e.preventDefault();

    if (!validateCurrentStep()) {
        return;
    }

    saveCurrentStepData();

    const payload = buildPayload();
    await submitForm(payload);
}

// Validate current step
function validateCurrentStep() {
    const errorMessages = document.querySelectorAll('.error-message');
    errorMessages.forEach(msg => msg.textContent = '');

    let isValid = true;

    switch(currentStep) {
        case 1:
            isValid = validateStep1();
            break;
        case 2:
            isValid = validateStep2();
            break;
        case 3:
            isValid = validateStep3();
            break;
        case 4:
            isValid = validateStep4();
            break;
        case 5:
            isValid = true;
            break;
    }

    return isValid;
}

function validateStep1() {
    let isValid = true;
    const ownerName = document.getElementById('ownerName').value.trim();
    const mobile = document.getElementById('mobile').value.trim();
    const email = document.getElementById('email').value.trim();

    if (!ownerName) {
        document.getElementById('ownerName-error').textContent = 'Owner name is required';
        isValid = false;
    }

    if (!mobile) {
        document.getElementById('mobile-error').textContent = 'Mobile number is required';
        isValid = false;
    } else if (!/^[0-9]{10,15}$/.test(mobile)) {
        document.getElementById('mobile-error').textContent = 'Mobile must be 10-15 digits';
        isValid = false;
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        document.getElementById('email-error').textContent = 'Invalid email format';
        isValid = false;
    }

    return isValid;
}

function validateStep2() {
    let isValid = true;
    const salonName = document.getElementById('salonName').value.trim();
    const salonAddress = document.getElementById('salonAddress').value.trim();
    const serviceType = document.getElementById('serviceType').value;
    const business = document.getElementById('business').value.trim();

    if (!salonName) {
        document.getElementById('salonName-error').textContent = 'Salon name is required';
        isValid = false;
    }

    if (!salonAddress) {
        document.getElementById('salonAddress-error').textContent = 'Salon address is required';
        isValid = false;
    }

    if (!serviceType) {
        document.getElementById('serviceType-error').textContent = 'Service type is required';
        isValid = false;
    }

    if (!business) {
        document.getElementById('business-error').textContent = 'Business category is required';
        isValid = false;
    }

    return isValid;
}

function validateStep3() {
    let isValid = true;
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;

    if (!latitude) {
        document.getElementById('latitude-error').textContent = 'Latitude is required';
        isValid = false;
    }

    if (!longitude) {
        document.getElementById('longitude-error').textContent = 'Longitude is required';
        isValid = false;
    }

    return isValid;
}

function validateStep4() {
    let isValid = true;
    const weeklyHoliday = document.getElementById('weeklyHoliday').value;

    if (!weeklyHoliday) {
        document.getElementById('weeklyHoliday-error').textContent = 'Weekly holiday is required';
        isValid = false;
    }

    return isValid;
}

// Save current step data
function saveCurrentStepData() {
    formData.ownerName = document.getElementById('ownerName').value;
    formData.mobile = document.getElementById('mobile').value;
    formData.email = document.getElementById('email').value;
    formData.ownerAddress = document.getElementById('ownerAddress').value;
    formData.salonName = document.getElementById('salonName').value;
    formData.salonAddress = document.getElementById('salonAddress').value;
    formData.serviceType = document.getElementById('serviceType').value;
    formData.business = document.getElementById('business').value;
    formData.licence = document.getElementById('licence').value;
    formData.latitude = document.getElementById('latitude').value;
    formData.longitude = document.getElementById('longitude').value;
    formData.weeklyHoliday = document.getElementById('weeklyHoliday').value;
}

// Update step display
function updateStep() {
    // Hide all steps
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show current step
    document.getElementById(`step-${currentStep}`).classList.add('active');

    // Update header
    document.getElementById('stepTitle').textContent = `Step ${currentStep} of ${TOTAL_STEPS}`;
    document.getElementById('progressFill').style.width = `${(currentStep / TOTAL_STEPS) * 100}%`;

    // Update buttons
    const backBtn = document.getElementById('backBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    backBtn.style.display = currentStep > 1 ? 'block' : 'none';
    nextBtn.style.display = currentStep < TOTAL_STEPS ? 'block' : 'none';
    submitBtn.style.display = currentStep === TOTAL_STEPS ? 'block' : 'none';

    // If on review step, populate summary
    if (currentStep === TOTAL_STEPS) {
        populateReviewSummary();
    }
}

// Populate review summary
function populateReviewSummary() {
    const summary = document.getElementById('reviewSummary');
    summary.innerHTML = `
        <div class="review-item">
            <div class="review-label">Owner Information</div>
            <div class="review-value">
                <strong>${formData.ownerName}</strong><br>
                ${formData.mobile}<br>
                ${formData.email || 'No email provided'}<br>
                ${formData.ownerAddress || 'No address provided'}
            </div>
        </div>
        <div class="review-item">
            <div class="review-label">Salon Information</div>
            <div class="review-value">
                <strong>${formData.salonName}</strong><br>
                ${formData.salonAddress}<br>
                Type: ${formData.serviceType}<br>
                Category: ${formData.business}<br>
                Licence: ${formData.licence || 'Not provided'}
            </div>
        </div>
        <div class="review-item">
            <div class="review-label">Location</div>
            <div class="review-value">
                Latitude: ${formData.latitude}<br>
                Longitude: ${formData.longitude}
            </div>
        </div>
        <div class="review-item">
            <div class="review-label">Working Hours</div>
            <div class="review-value">
                Weekly Holiday: ${formData.weeklyHoliday}
            </div>
        </div>
    `;
}

// Get current location
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                document.getElementById('latitude').value = position.coords.latitude.toFixed(4);
                document.getElementById('longitude').value = position.coords.longitude.toFixed(4);
                showMessage('Location retrieved successfully', 'success');
            },
            function(error) {
                showMessage('Unable to retrieve location: ' + error.message, 'error');
            }
        );
    } else {
        showMessage('Geolocation is not supported by this browser', 'error');
    }
}

// Build payload
function buildPayload() {
    const workingHours = [];

    DAYS.forEach(day => {
        const isClosed = document.querySelector(`.is-closed[data-day="${day}"]`).checked;
        const openTime = document.querySelector(`.open-time[data-day="${day}"]`).value;
        const closeTime = document.querySelector(`.close-time[data-day="${day}"]`).value;

        workingHours.push({
            day: day,
            openTime: openTime,
            closeTime: closeTime,
            isClosed: isClosed
        });
    });

    return {
        action: 'create-client',
        ownerName: formData.ownerName,
        mobile: formData.mobile,
        email: formData.email || null,
        ownerAddress: formData.ownerAddress,
        salonName: formData.salonName,
        salonAddress: formData.salonAddress,
        serviceType: formData.serviceType,
        business: formData.business,
        licence: formData.licence || null,
        weeklyHoliday: formData.weeklyHoliday,
        location: {
            latitude: parseFloat(formData.latitude),
            longitude: parseFloat(formData.longitude)
        },
        workingHours: workingHours,
        version: 1,
        registeredAt: new Date().toISOString(),
        approvalStatus: 'PENDING'
    };
}

// Submit form
async function submitForm(payload) {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.result.status === 'SUCCESS') {
            showMessage('Registration submitted successfully! Your salon will be reviewed soon.', 'success');
            setTimeout(() => {
                currentStep = 1;
                formData = {};
                document.getElementById('registrationForm').reset();
                initializeForm();
                updateStep();
            }, 2000);
        } else {
            const errorMsg = result.result.message || result.err_details.err_msg || 'Registration failed';
            showMessage(errorMsg, 'error');
        }
    } catch (error) {
        showMessage('Error submitting form: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
    }
}

// Show message
function showMessage(message, type) {
    const successMsg = document.getElementById('successMessage');
    const errorMsg = document.getElementById('errorMessage');

    if (type === 'success') {
        successMsg.textContent = message;
        successMsg.style.display = 'block';
        errorMsg.style.display = 'none';
    } else {
        errorMsg.textContent = message;
        errorMsg.style.display = 'block';
        successMsg.style.display = 'none';
    }

    setTimeout(() => {
        successMsg.style.display = 'none';
        errorMsg.style.display = 'none';
    }, 5000);
}
