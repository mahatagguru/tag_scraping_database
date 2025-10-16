# TAG Grading Scraper - Reporting Website

A comprehensive web-based reporting and analytics dashboard for the TAG Grading Scraper data. This modern web application provides powerful tools for exploring, analyzing, and visualizing sports card grading data.

## 🌟 Features

### 📊 Dashboard
- **Real-time Statistics**: Live overview of database metrics
- **System Health**: Database connectivity and API status monitoring
- **Recent Activity**: Latest system operations and audit logs
- **Quick Metrics**: Categories, years, sets, cards, grades, and populations

### 🏷️ Categories & Data Hierarchy
- **Hierarchical Navigation**: Browse categories → years → sets → cards
- **Expandable Interface**: Drill down through data levels
- **Rich Metadata**: View totals, descriptions, and statistics
- **Interactive Cards**: Click to explore detailed information

### 🃏 Cards Database
- **Advanced Search**: Search by player, card number, certificate, or set
- **Smart Filtering**: Filter by category, set, and other criteria
- **Pagination**: Efficient browsing of large datasets
- **Detailed Views**: Comprehensive card information and metadata

### 📈 Analytics & Insights
- **Interactive Charts**: Bar charts, pie charts, and trend lines
- **Grade Distribution**: Visual analysis of grading patterns
- **Population Trends**: Historical data analysis over time
- **Customizable Filters**: Filter by category, grade, and time range

### 🔍 Advanced Search
- **Global Search**: Search across all data types
- **Type-based Filtering**: Filter results by cards, sets, years, categories
- **Real-time Results**: Instant search with live updates
- **Detailed Results**: Rich result cards with metadata

## 🏗️ Architecture

### Backend (FastAPI)
- **RESTful API**: Clean, well-documented endpoints
- **Database Integration**: Direct connection to existing SQLite/PostgreSQL database
- **Type Safety**: Pydantic models for request/response validation
- **Error Handling**: Comprehensive error handling and logging
- **CORS Support**: Cross-origin resource sharing for frontend integration

### Frontend (React + TypeScript)
- **Modern UI**: Material-UI components with custom theming
- **Type Safety**: Full TypeScript implementation
- **State Management**: React Query for server state management
- **Responsive Design**: Mobile-friendly responsive layout
- **Real-time Updates**: Automatic data refresh and live updates

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### One-Command Setup
```bash
# Make the startup script executable (if not already done)
chmod +x start-reporting-website.sh

# Start both backend and frontend
./start-reporting-website.sh
```

This will:
1. Install backend dependencies in a virtual environment
2. Install frontend dependencies
3. Start the FastAPI backend on http://localhost:8000
4. Start the React frontend on http://localhost:3000
5. Open your browser to the dashboard

### Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: http://localhost:8000/api/docs
- **ReDoc Documentation**: http://localhost:8000/api/redoc

### Key Endpoints

#### Dashboard
- `GET /api/dashboard` - Get comprehensive dashboard statistics

#### Categories
- `GET /api/categories` - List all categories
- `GET /api/categories/{id}/years` - Get years for a category

#### Years
- `GET /api/years/{id}/sets` - Get sets for a year

#### Sets
- `GET /api/sets/{id}/cards` - Get cards for a set

#### Cards
- `GET /api/cards/{uid}/populations` - Get population data for a card

#### Search
- `GET /api/search?q={query}` - Global search across all entities

#### Analytics
- `GET /api/analytics/population-trends` - Get population trend data

## 🎨 User Interface

### Dashboard
The main dashboard provides a comprehensive overview of your data:
- **Statistics Cards**: Key metrics with visual indicators
- **System Status**: Real-time health monitoring
- **Recent Activity**: Latest operations and logs
- **Quick Navigation**: Easy access to all features

### Categories Page
Explore your data hierarchically:
- **Category Cards**: Visual cards with statistics
- **Expandable Views**: Click to drill down through data
- **Rich Metadata**: Descriptions, totals, and counts
- **Interactive Navigation**: Smooth transitions between levels

### Cards Page
Browse and search your card database:
- **Advanced Search**: Multiple search criteria
- **Smart Filters**: Category, set, and other filters
- **Card Grid**: Visual card representation
- **Detailed Views**: Comprehensive card information

### Analytics Page
Analyze your data with powerful visualizations:
- **Interactive Charts**: Bar charts, pie charts, line graphs
- **Grade Distribution**: Visual analysis of grading patterns
- **Trend Analysis**: Historical data over time
- **Customizable Filters**: Filter by various criteria

### Search Page
Find specific data quickly:
- **Global Search**: Search across all data types
- **Type Filtering**: Filter results by entity type
- **Real-time Results**: Instant search feedback
- **Rich Results**: Detailed result cards

## 🔧 Configuration

### Environment Variables
The backend uses the same environment variables as the main scraper:
- `POSTGRES_HOST` - PostgreSQL host (default: localhost)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - PostgreSQL database name

### Frontend Configuration
The frontend automatically connects to the backend API. To change the API URL:
1. Create a `.env` file in the `frontend` directory
2. Add: `REACT_APP_API_URL=http://your-api-url:port/api`

## 📊 Data Visualization

### Chart Types
- **Bar Charts**: Category distribution, set counts
- **Pie Charts**: Grade distribution, category breakdown
- **Line Charts**: Population trends over time
- **Tables**: Detailed data listings with sorting

### Interactive Features
- **Hover Tooltips**: Detailed information on hover
- **Click Interactions**: Drill down into specific data
- **Filter Integration**: Charts update based on filters
- **Responsive Design**: Charts adapt to screen size

## 🔍 Search Capabilities

### Search Types
- **Text Search**: Search by player names, card numbers, certificates
- **Type Filtering**: Filter by cards, sets, years, categories
- **Fuzzy Matching**: Find results even with partial matches
- **Real-time Results**: Instant search feedback

### Search Features
- **Global Search**: Search across all data types simultaneously
- **Type-specific Results**: Filter results by entity type
- **Rich Metadata**: Detailed result information
- **Quick Actions**: View details directly from search results

## 🛠️ Development

### Backend Development
```bash
cd backend
source venv/bin/activate
python main.py
```

The backend uses FastAPI with automatic API documentation generation.

### Frontend Development
```bash
cd frontend
npm start
```

The frontend uses React with TypeScript and Material-UI.

### Adding New Features
1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Add new pages in `src/pages/`
3. **API Integration**: Update `src/services/api.ts`
4. **Types**: Update `src/types/index.ts`

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
- Check Python version (3.9+ required)
- Verify virtual environment is activated
- Check if port 8000 is available
- Review error logs in terminal

#### Frontend Won't Start
- Check Node.js version (16+ required)
- Verify npm packages are installed
- Check if port 3000 is available
- Clear npm cache: `npm cache clean --force`

#### Database Connection Issues
- Verify database is running
- Check environment variables
- Review database connection logs
- Ensure database schema is up to date

#### No Data Showing
- Run the scraping pipeline to populate data
- Check database connection
- Verify API endpoints are working
- Review browser console for errors

### Getting Help
1. Check the terminal output for error messages
2. Review the browser console for frontend errors
3. Check the API documentation at `/api/docs`
4. Verify database connectivity and data

## 📈 Performance

### Optimization Features
- **Lazy Loading**: Load data only when needed
- **Pagination**: Efficient handling of large datasets
- **Caching**: React Query caching for API responses
- **Debounced Search**: Optimized search performance
- **Virtual Scrolling**: Efficient rendering of large lists

### Scalability
- **Database Indexing**: Optimized database queries
- **API Pagination**: Efficient data transfer
- **Frontend Optimization**: Minimal re-renders
- **Responsive Design**: Works on all screen sizes

## 🔒 Security

### Security Features
- **CORS Configuration**: Proper cross-origin setup
- **Input Validation**: Pydantic model validation
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **XSS Prevention**: React's built-in XSS protection

### Best Practices
- **Environment Variables**: Sensitive data in environment
- **API Rate Limiting**: Prevent abuse (can be added)
- **Input Sanitization**: Clean user inputs
- **Error Handling**: Secure error messages

## 🚀 Deployment

### Production Deployment
1. **Backend**: Deploy FastAPI with Gunicorn or similar
2. **Frontend**: Build and serve static files
3. **Database**: Use PostgreSQL for production
4. **Reverse Proxy**: Use Nginx for static files and API routing

### Docker Deployment
```bash
# Build backend image
cd backend
docker build -t tag-scraper-api .

# Build frontend image
cd frontend
docker build -t tag-scraper-frontend .

# Run with docker-compose
docker-compose up -d
```

## 📝 License

This reporting website is part of the TAG Grading Scraper project and follows the same MIT License.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
1. Check this README
2. Review the API documentation
3. Check the main project documentation
4. Open an issue on GitHub

---

**Made with ❤️ for the TAG Grading Scraper Project**
