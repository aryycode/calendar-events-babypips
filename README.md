# BabyPips Economic Calendar Scraper

## API Documentation

### Available Endpoints

1. **GET /** - API Documentation
   - Returns: API information and available endpoints

2. **GET /calendar** - Scrape economic calendar
   - Parameters:
     - `year` (optional): Specific year (e.g. 2025)
     - `week` (optional): Week number (1-53)
     - `currency` (optional): Filter by currency (e.g. USD,EUR)
     - `impact` (optional): Filter by impact level (high,medium,low)
   - Example: `/calendar?year=2025&week=32&currency=USD&impact=high`

3. **GET /weeks** - Get available weeks
   - Returns: List of weeks with date ranges

4. **GET /health** - Health check
   - Returns: System status and requirements

## Example Responses

### Calendar Response
```json
{
  "success": true,
  "total_events": 42,
  "events": [
    {
      "date": "2025-08-05",
      "time": "14:30",
      "currency": "USD",
      "event_name": "Non-Farm Payrolls",
      "importance": "High",
      "actual": "200K",
      "forecast": "195K",
      "previous": "190K"
    }
  ]
}
```

### Weeks Response
```json
{
  "available_weeks": [
    {
      "year": 2025,
      "week": 32,
      "display": "Week 32, 2025",
      "date_range": "Aug 05 - Aug 09, 2025"
    }
  ]
}
```

## Docker Setup

### Prerequisites
1. Install Docker:
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - MacOS: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/

2. Ensure Docker is running

### Running with Docker
```bash
# Build the image
docker compose build

# Start the container
docker compose up

# Access the API
curl http://localhost:5000/calendar
```

### Development
For live reloading during development:
```bash
docker compose up --build
```

## Notes
- First run may take time to download dependencies
- Runs on port 5000 by default
- Chrome runs in headless mode