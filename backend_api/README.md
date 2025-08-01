# Daily Journal API Backend

A secure, production-ready FastAPI backend for the Daily Journal application with authentication, journal entry management, and export features.

## 🚀 Features

- **User Authentication & Authorization**
  - JWT-based authentication with secure password hashing (bcrypt)
  - User registration and login
  - Role-based access control (regular_user, admin)
  - Token verification and validation

- **Journal Entry Management**
  - Full CRUD operations for journal entries
  - Mood tracking with predefined mood types
  - Tag support for categorization
  - Private/public entry visibility
  - Advanced search and filtering

- **Export Functionality**
  - Export entries to TXT and PDF formats
  - Date range filtering for exports
  - Automatic file cleanup
  - User-specific export files

- **Security & Performance**
  - Input validation and sanitization
  - Rate limiting to prevent abuse
  - Thread-safe file-based database operations
  - CORS support for frontend integration
  - Comprehensive error handling

- **API Documentation**
  - Auto-generated OpenAPI/Swagger documentation
  - Detailed endpoint descriptions
  - Request/response schemas
  - Interactive API explorer

## 📋 Prerequisites

- Python 3.8+
- pip (Python package installer)

## 🛠️ Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd daily-journal-tracker-93142/backend_api
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

## 🔧 Configuration

Create a `.env` file in the backend_api directory with the following variables:

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# Application Configuration
ENVIRONMENT=development
PORT=8000

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

⚠️ **Important**: Change the `JWT_SECRET_KEY` to a secure random string in production!

## 🚀 Running the Application

### Development Mode

```bash
# Using the development script
python run.py

# Or using uvicorn directly
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
# Set environment to production
export ENVIRONMENT=production

# Run with gunicorn (install gunicorn first)
pip install gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📖 API Documentation

Once the server is running, you can access:

- **Interactive API Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Documentation (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON Schema**: http://localhost:8000/openapi.json

## 🔍 API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/verify` - Verify JWT token

### Journal Entries
- `GET /api/entries` - Get user's journal entries (paginated)
- `POST /api/entries` - Create a new journal entry
- `GET /api/entries/{entry_id}` - Get specific journal entry
- `PUT /api/entries/{entry_id}` - Update journal entry
- `DELETE /api/entries/{entry_id}` - Delete journal entry
- `GET /api/entries/search/query` - Search entries with filters

### Export
- `POST /api/export/entries` - Export entries to TXT/PDF
- `GET /api/export/download/{filename}` - Download exported file
- `DELETE /api/export/cleanup` - Cleanup old export files

### Health & Info
- `GET /` - Basic health check
- `GET /health` - Detailed health check
- `GET /api/info` - API information and capabilities

## 🧪 Testing

### Run API Tests

```bash
# Make sure the server is running first
python run.py &

# Run the test suite
python test_api.py

# Stop the server
kill %1
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/

# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'

# Create a journal entry (replace YOUR_TOKEN with actual token)
curl -X POST http://localhost:8000/api/entries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "My First Entry",
    "content": "Today was a great day!",
    "mood": "happy",
    "tags": ["personal", "reflection"]
  }'
```

## 📁 Project Structure

```
backend_api/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── entries.py       # Journal entry endpoints
│   │   │   └── export.py        # Export endpoints
│   │   ├── main.py              # FastAPI app configuration
│   │   └── generate_openapi.py  # OpenAPI schema generator
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   └── utils/
│       ├── database.py          # File-based database operations
│       ├── auth.py              # Authentication utilities
│       ├── security.py          # Security middleware
│       └── export.py            # Export utilities
├── interfaces/
│   └── openapi.json            # Generated OpenAPI specification
├── data/                       # Database files (auto-created)
│   ├── users.json             # User data
│   ├── entries.json           # Journal entries
│   └── exports/               # Export files
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── run.py                    # Development server script
├── test_api.py              # API test suite
└── README.md                # This file
```

## 🔒 Security Features

- **Password Security**: Bcrypt hashing with salt
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Pydantic models for request validation
- **Input Sanitization**: XSS prevention for text inputs
- **Rate Limiting**: Prevent API abuse
- **File Locking**: Thread-safe database operations
- **CORS Configuration**: Configurable cross-origin requests
- **Error Handling**: Secure error messages without data leakage

## 🗃️ Database

The application uses a file-based JSON database for simplicity:

- `data/users.json` - User accounts and profiles
- `data/entries.json` - Journal entries
- Thread-safe operations with file locking
- Automatic backup and recovery
- Easy migration to SQL databases if needed

## 📊 Mood Types

The application supports the following mood types:

- `very_happy` - Very Happy 😄
- `happy` - Happy 😊
- `neutral` - Neutral 😐
- `sad` - Sad 😢
- `very_sad` - Very Sad 😭
- `anxious` - Anxious 😰
- `excited` - Excited 🤩
- `calm` - Calm 😌
- `angry` - Angry 😠
- `grateful` - Grateful 🙏

## 🚀 Deployment

### Using Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```env
ENVIRONMENT=production
JWT_SECRET_KEY=your-very-secure-secret-key-here
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=WARNING
RATE_LIMIT_ENABLED=true
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the correct directory
   cd backend_api
   # Check Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Permission Errors**
   ```bash
   # Create data directory
   mkdir -p data
   chmod 755 data
   ```

3. **Port Already in Use**
   ```bash
   # Kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

4. **Dependency Conflicts**
   ```bash
   # Create fresh virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 📝 Development

### Adding New Endpoints

1. Create route functions in appropriate files under `src/api/routes/`
2. Add Pydantic models in `src/models/schemas.py`
3. Update the main app in `src/api/main.py` if needed
4. Regenerate OpenAPI spec: `python src/api/generate_openapi.py`

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Run tests
python test_api.py
```

## 📄 License

This project is part of the Daily Journal application suite.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section
- Check server logs for error details

---

**Happy Journaling! 📔✨**
