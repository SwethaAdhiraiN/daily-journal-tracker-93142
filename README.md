# Daily Journal Tracker

A modern, secure daily journal application with mood tracking, tag support, and export capabilities. Built with FastAPI backend and designed for React frontend integration.

## 🎯 Project Overview

This daily journal application enables users to:
- **Record Daily Thoughts**: Create, edit, and manage journal entries
- **Track Moods**: Monitor emotional patterns with mood tracking
- **Organize with Tags**: Categorize entries for easy retrieval
- **Search & Filter**: Advanced search capabilities
- **Export Data**: Download entries as TXT or PDF files
- **Secure Access**: JWT-based authentication with role management

## 🏗️ Architecture

The application follows a microservices architecture with separate backend and frontend containers:

### Backend API (`backend_api/`)
- **Framework**: FastAPI with Python 3.8+
- **Authentication**: JWT tokens with bcrypt password hashing
- **Database**: File-based JSON storage with thread-safe operations
- **Features**: CRUD operations, search, export, rate limiting
- **Status**: ✅ **COMPLETED** - Production-ready implementation

### Frontend App (`frontend_app/`)
- **Framework**: React with modern UI components
- **Features**: Responsive design, dark mode, offline support
- **Status**: 🔄 **Pending** - Ready for development

## 🚀 Quick Start

### Backend API

1. **Navigate to backend directory**:
   ```bash
   cd backend_api
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start the server**:
   ```bash
   # Development mode
   python run.py
   
   # Or use the deployment script
   ./deploy.sh start
   ```

5. **Access API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Testing the API

```bash
cd backend_api
python test_api.py
```

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - User logout

### Journal Entries
- `GET /api/entries` - List user entries (paginated)
- `POST /api/entries` - Create new entry
- `GET /api/entries/{id}` - Get specific entry
- `PUT /api/entries/{id}` - Update entry
- `DELETE /api/entries/{id}` - Delete entry
- `GET /api/entries/search/query` - Search entries

### Export
- `POST /api/export/entries` - Export to TXT/PDF
- `GET /api/export/download/{filename}` - Download file

## 🔧 Features Implemented

### ✅ Backend Features (Completed)
- [x] User registration and authentication
- [x] JWT-based security with bcrypt password hashing
- [x] Journal entry CRUD operations
- [x] Mood tracking (10 mood types)
- [x] Tag support and organization
- [x] Advanced search and filtering
- [x] Export to TXT and PDF formats
- [x] Rate limiting and security measures
- [x] Input validation and sanitization
- [x] Thread-safe file operations
- [x] Comprehensive API documentation
- [x] Health checks and monitoring
- [x] Role-based access control
- [x] Automatic OpenAPI specification

### 🔄 Frontend Features (Pending)
- [ ] Modern React UI with responsive design
- [ ] User authentication interface
- [ ] Journal entry management interface
- [ ] Dashboard with mood visualization
- [ ] Calendar view for entries
- [ ] Search and filter interface
- [ ] Export functionality UI
- [ ] Dark mode support
- [ ] Offline capabilities with localStorage

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and serialization
- **JWT** - Secure authentication tokens
- **bcrypt** - Password hashing
- **ReportLab** - PDF generation
- **Slowapi** - Rate limiting
- **Uvicorn** - ASGI server

### Database
- **JSON Files** - Simple, portable file-based storage
- **Thread-safe operations** with file locking
- **Easy migration path** to SQL databases

### Security
- **JWT Authentication** with secure token handling
- **Password Hashing** with bcrypt and salt
- **Input Validation** with Pydantic models
- **Rate Limiting** to prevent abuse
- **CORS Configuration** for frontend integration
- **Input Sanitization** for XSS prevention

## 📊 Mood Types Supported

The application supports comprehensive mood tracking:

- 😄 Very Happy
- 😊 Happy  
- 😐 Neutral
- 😢 Sad
- 😭 Very Sad
- 😰 Anxious
- 🤩 Excited
- 😌 Calm
- 😠 Angry
- 🙏 Grateful

## 🔒 Security Features

- **Secure Authentication**: JWT tokens with configurable expiration
- **Password Security**: bcrypt hashing with salt rounds
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API abuse prevention
- **Error Handling**: Secure error responses
- **File Security**: Thread-safe database operations
- **CORS Protection**: Configurable cross-origin policies

## 📁 Project Structure

```
daily-journal-tracker-93142/
├── backend_api/                 # ✅ FastAPI Backend (COMPLETED)
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/         # API endpoint definitions
│   │   │   └── main.py         # FastAPI application
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic models
│   │   └── utils/
│   │       ├── auth.py         # Authentication utilities
│   │       ├── database.py     # File-based database
│   │       ├── security.py     # Security middleware
│   │       └── export.py       # Export functionality
│   ├── interfaces/
│   │   └── openapi.json        # API specification
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment template
│   ├── run.py                 # Development server
│   ├── deploy.sh              # Deployment script
│   ├── test_api.py            # API test suite
│   └── README.md              # Backend documentation
└── frontend_app/               # 🔄 React Frontend (PENDING)
    └── (To be implemented)
```

## 🧪 Testing

The backend includes comprehensive testing:

```bash
# Run API tests
cd backend_api
python test_api.py

# Manual testing with curl
curl http://localhost:8000/api/info
```

## 🚀 Deployment

### Development
```bash
cd backend_api
./deploy.sh start
```

### Production
```bash
cd backend_api
ENVIRONMENT=production ./deploy.sh start
```

### Docker (Recommended for Production)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend_api/requirements.txt .
RUN pip install -r requirements.txt
COPY backend_api/ .
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Current Status

### ✅ Completed Components
- **Backend API**: Full implementation with all endpoints
- **Authentication System**: JWT-based security
- **Database Layer**: Thread-safe file operations
- **Export System**: TXT and PDF generation
- **API Documentation**: Auto-generated OpenAPI specs
- **Testing Suite**: Comprehensive API tests
- **Deployment Tools**: Production-ready scripts

### 🔄 Next Steps
- Frontend React application development
- Integration between frontend and backend
- Enhanced UI/UX design implementation
- Mobile responsiveness optimization
- Advanced features (calendar view, analytics)

## 📚 Documentation

- **API Documentation**: Available at `/docs` when server is running
- **Backend README**: `backend_api/README.md`
- **OpenAPI Specification**: `backend_api/interfaces/openapi.json`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## 📄 License

This project is part of the Daily Journal application suite.

---

**Backend Status**: ✅ **Production Ready**  
**Frontend Status**: 🔄 **Ready for Development**

**Happy Journaling!** 📔✨