// Variables to hold chart instances
let reviewCountPerYearChart;
let peakMonthsChart;
let reviewsByCategoryChart;

// Function to handle sentiment analysis
document.getElementById('submitButton').addEventListener('click', async function (event) {
    event.preventDefault();
    const reviewInput = document.getElementById('reviewInput').value;
    const sentimentText = document.getElementById('sentiment');

    // Clear previous results and classes
    sentimentText.textContent = '';
    sentimentText.classList.remove('positive', 'negative');

    if (reviewInput.trim() === '') {
        alert("Please enter a review before submitting.");
        return;
    }

    try {
        const response = await fetch('http://localhost:5001/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ review: reviewInput })
        });

        if (response.ok) {
            const data = await response.json();

            // Display sentiment label and scores
            sentimentText.textContent = `${data.sentiment}`;

            // Apply color based on sentiment
            if (data.sentiment.toLowerCase() === 'positive') {
                sentimentText.classList.add('positive');
            } else if (data.sentiment.toLowerCase() === 'negative') {
                sentimentText.classList.add('negative');
            }

        } else {
            const errorData = await response.json();
            alert(errorData.error || "An error occurred during sentiment analysis.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred during sentiment analysis.");
    }
});


// Function to fetch and render dashboard data
async function fetchDataAndRenderDashboard() {
    // Disable filters during data fetching
    document.getElementById('yearFilterContainer').disabled = true;

    // Show loading UI
    document.getElementById('loading').style.display = 'block';

    const selectedYears = Array.from(document.querySelectorAll('.yearCheckbox:checked'))
        .map(checkbox => checkbox.value);
    const monthFilter = document.getElementById('monthFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;

    // Construct common query parameters that will be shared
    const commonParams = {
        years: selectedYears.join(','),
        category: categoryFilter !== 'all' ? categoryFilter : '',
        month: monthFilter !== 'all' ? monthFilter : ''
    };

    const peakParams = {
        year: selectedYears.length > 0 ? selectedYears.join(',') : 'all',  // Handle empty years
        category: categoryFilter !== 'all' ? categoryFilter : '',
    };

    const categoryParams = {
        year: selectedYears.length > 0 ? selectedYears.join(',') : 'all',  // Multiple years separated by commas
        category: categoryFilter !== 'all' ? categoryFilter : '',
        month: monthFilter !== 'all' ? monthFilter : ''
    };

    try {
        // Fetch data for review count per year (with year, month, and category filters)
        const reviewCountParams = new URLSearchParams(commonParams);  // Includes year, month, and category
        const reviewCountPerYear = await fetch(`http://localhost:5001/dashboard/review_count_per_year?${reviewCountParams}`).then(res => res.json());

        // Fetch data for peak months (with year and category filters, but no month filter)
        const peakMonthsParams = new URLSearchParams(peakParams);  // Only years and category
        const peakMonths = await fetch(`http://localhost:5001/dashboard/peak_months?${peakMonthsParams}`).then(res => res.json());

        // Fetch data for reviews by category (with year, month, and category filters)
        const reviewsByCategoryParams = new URLSearchParams(categoryParams);  // Includes year, month, and category
        const reviewsByCategory = await fetch(`http://localhost:5001/dashboard/reviews_by_category?${reviewsByCategoryParams}`).then(res => res.json());

        // Render charts with the fetched data
        renderReviewCountPerYearChart(reviewCountPerYear);
        renderPeakMonths(peakMonths);
        renderReviewsByCategory(reviewsByCategory);

    } catch (error) {
        console.error("Error fetching dashboard data:", error);
        alert("An error occurred while loading the dashboard data.");
    } finally {
        // Re-enable filters and hide loading indicator
        document.getElementById('yearFilterContainer').disabled = false;
        document.getElementById('loading').style.display = 'none';
    }
}

async function populateYearFilter() {
    try {
        const years = await fetch('http://localhost:5001/dashboard/years').then(res => res.json());

        const container = document.getElementById('yearFilterContainer');

        // Filter out any invalid values like undefined, null, or empty strings
        const validYears = years.filter(year => {
            // Only keep valid years (non-null, non-empty, and non-undefined)
            return year != null && year !== '' && year !== undefined;
        });


        // Add the checkboxes dynamically for each valid year
        validYears.forEach(year => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = true;
            checkbox.value = year;
            checkbox.id = `year-${year}`;
            checkbox.classList.add('yearCheckbox');

            const label = document.createElement('label');
            label.htmlFor = `year-${year}`;
            label.textContent = year;

            // Append the checkbox and label to the container
            container.appendChild(checkbox);
            container.appendChild(label);
            container.appendChild(document.createElement('br'));  // Line break for neatness
        });

        // Add event listener to re-fetch and update dashboard on change
        document.querySelectorAll('.yearCheckbox').forEach(checkbox => {
            checkbox.addEventListener('change', fetchDataAndRenderDashboard);
        });

    } catch (error) {
        console.error("Error populating year filter:", error);
    }
}

//document.getElementById('yearFilter').addEventListener('change', fetchDataAndRenderDashboard);
document.getElementById('monthFilter').addEventListener('change', fetchDataAndRenderDashboard);
document.getElementById('categoryFilter').addEventListener('change', fetchDataAndRenderDashboard);
document.getElementById('yearFilterContainer').addEventListener('change', fetchDataAndRenderDashboard);


async function populateFilters() {
    try {
        // Only populate categories since the years are already populated elsewhere
        const categories = await fetch('http://localhost:5001/dashboard/categories').then(res => res.json());

        const categoryFilter = document.getElementById('categoryFilter');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });

    } catch (error) {
        console.error("Error populating filters:", error);
    }
}

async function populateMonthFilter() {
    try {
        // Fetch the months data from the API
        const months = await fetch('http://localhost:5001/dashboard/months').then(res => res.json());

        const monthFilter = document.getElementById('monthFilter');

        // Check if 'All' option already exists to prevent duplication
        if (!monthFilter.querySelector('option[value="all"]')) {
            // Add the 'All' option only if it doesn't exist
            const allOption = document.createElement('option');
            allOption.value = 'all';
            allOption.textContent = 'All';
            monthFilter.appendChild(allOption);
        }

        // Then, add the months dynamically (assuming months is an array of numbers 1-12)
        months.forEach(month => {
            const option = document.createElement('option');
            option.value = month;
            option.textContent = getMonthName(month);  // Converts month number to month name
            monthFilter.appendChild(option);
        });
    } catch (error) {
        console.error("Error populating month filter:", error);
    }
}
// Helper function to convert month number to month name
function getMonthName(monthNumber) {
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return monthNames[monthNumber - 1];
}

// Render functions
function renderReviewCountPerYearChart(data) {
    if (!data || data.length === 0) {
        console.warn("No data available for Review Count Per Year.");
        return;
    }

    const ctx = document.getElementById('reviewsPerYearChart').getContext('2d');
    if (reviewCountPerYearChart) {
        reviewCountPerYearChart.destroy();
    }

    const years = data.map(item => item.year);
    const counts = data.map(item => item.count);

    reviewCountPerYearChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: [{
                label: 'Count of Reviews per Year',
                data: counts,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function () {
                            return ''; // Hides the default title
                        },
                        label: function (context) {
                            let year = context.label;
                            let count = context.raw;
                            return `YEAR ${year} : ${count}`;
                        }
                    }
                }
            }
        }
    });
}

function renderPeakMonths(data) {
    if (!data || data.length === 0) {
        console.warn("No data available for Peak Months.");
        return;
    }

    const ctx = document.getElementById('peakMonthsChart').getContext('2d');
    if (peakMonthsChart) {
        peakMonthsChart.destroy();
    }

    const monthAbbreviations = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const months = data.map(item => monthAbbreviations[item.month - 1]);
    const counts = data.map(item => item.review_count);

    peakMonthsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Peak Months of Reviews',
                data: counts,
                fill: false,
                borderColor: 'rgba(255, 99, 132, 1)',
                tension: 0.1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function () {
                            return ''; // Hides the default title
                        },
                        label: function (context) {
                            let month = context.label;
                            let review_count = context.raw;
                            return `${month} : ${review_count}`;
                        }
                    }
                }
            }
        }
    });
}


function renderReviewsByCategory(data) {
    if (!data || data.length === 0) {
        console.warn("No data available for Reviews by Category.");
        return;
    }

    const ctx = document.getElementById('reviewsByCategoryChart').getContext('2d');
    if (reviewsByCategoryChart) {
        reviewsByCategoryChart.destroy();
    }

    const categories = data.map(item => item.categories);
    const positiveCounts = data.map(item => item.positive_count);
    const negativeCounts = data.map(item => item.negative_count);

    reviewsByCategoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Positive Reviews',
                    data: positiveCounts,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Negative Reviews',
                    data: negativeCounts,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Call the function to load the dashboard on page load
window.onload = async () => {
    await populateYearFilter();
    await populateMonthFilter(); // Populate the month filter
    await populateFilters(); // For categories
    fetchDataAndRenderDashboard();
};

document.getElementById("uploadForm").addEventListener("submit", function (event) {
    event.preventDefault();  // Prevent the form from submitting the usual way

    const fileInput = document.getElementById("file");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Show loading message while uploading
    document.getElementById("result").textContent = "Uploading and processing file... Please wait.";
    fetch("http://127.0.0.1:5001/upload", {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Concatenate the base URL with the relative download URL
            const fullDownloadUrl = `http://127.0.0.1:5001${data.download_url}`;
            fetchDataAndRenderDashboard();
            // Display download link
            document.getElementById("result").innerHTML = `File processed successfully.</a>`;
            document.getElementById("batch-result").innerHTML = `<a href="${fullDownloadUrl}" target="_blank">Click here to Download</a>`;
        } else {
            document.getElementById("result").textContent = "Error: " + data.message;
        }
    })
    .catch(error => {
        console.error("Error uploading file:", error);
        document.getElementById("result").textContent = "Error uploading file.";
    });
});

