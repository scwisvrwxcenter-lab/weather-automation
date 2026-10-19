document.addEventListener("DOMContentLoaded", () => {
    fetch('daily_forecast_cache.json')
        .then(response => response.json())
        .then(data => {
            // Update Header Date Range
            document.getElementById('outlook-title').innerText = `Weather Outlook ${data.date_range}`;
            
            // Assuming we are displaying the first location (e.g., Lancaster, WI)
            const locationKey = Object.keys(data.forecasts)[0];
            const locationData = data.forecasts[locationKey];
            
            document.getElementById('region-label').innerText = locationData.region_description;

            const container = document.getElementById('forecast-cards-container');
            container.innerHTML = '';

            // Loop through each of the 7 days and build cards
            locationData.days.forEach(day => {
                const card = document.createElement('div');
                card.className = 'forecast-card';
                card.innerHTML = `
                    <div class="card-header">
                        <span class="day-name">${day.day_name}</span>
                        <span class="day-date">${day.date}</span>
                    </div>
                    <div class="card-body">
                        <div class="temps">${day.high}° / ${day.low}°</div>
                        <div class="precip">${day.precip_prob}% Precip</div>
                        <div class="risk">${day.risk_level}</div>
                        <div class="condition">${day.condition}</div>
                    </div>
                `;
                container.appendChild(card);
            });

            // Set footer summary text
            document.getElementById('outlook-summary').innerText = 
                `Updated daily via high-resolution model data. Current status: Active 7-day forecast loaded successfully.`;
        })
        .catch(error => console.error('Error loading forecast cache:', error));
});
