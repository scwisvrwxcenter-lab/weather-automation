document.addEventListener("DOMContentLoaded", () => {
    fetch('daily_forecast_cache.json')
        .then(response => response.json())
        .then(data => {
            // Set main title date range
            document.getElementById('outlook-title').innerText = `Weather Outlook ${data.date_range}`;
            
            const locationKeys = Object.keys(data.forecasts);
            if (locationKeys.length === 0) return;

            const buttonsContainer = document.getElementById('location-buttons');
            buttonsContainer.innerHTML = '';

            // Generate tab buttons for Lancaster, Madison, and Milwaukee
            locationKeys.forEach((key, index) => {
                const loc = data.forecasts[key];
                const btn = document.createElement('button');
                btn.className = `location-btn ${index === 0 ? 'active' : ''}`;
                btn.innerText = loc.display_name || key.replace('_', ' ');
                
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.location-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    renderForecastCards(loc);
                });

                buttonsContainer.appendChild(btn);
            });

            // Render Lancaster by default
            renderForecastCards(data.forecasts[locationKeys[0]]);
        })
        .catch(error => console.error('Error loading forecast cache:', error));
});

function renderForecastCards(locationData) {
    document.getElementById('region-label').innerText = locationData.region_description;

    const container = document.getElementById('forecast-cards-container');
    container.innerHTML = '';

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
}
