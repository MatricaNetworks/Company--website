# Matrica Networks - Cybersecurity Company Website

A complete, production-ready cybersecurity company website built with vanilla HTML/CSS/JavaScript frontend and pure Python backend. Features a dark, futuristic design with neon accents, comprehensive admin portal, employee management, job posting system, and advanced security measures.

## 🚀 Features

### Frontend
- **Modern UI/UX**: Dark cyberpunk design with neon accents and smooth animations
- **Responsive Design**: Mobile-first approach, works on all devices
- **WebGL 3D Visualization**: Rotating globe/shield on homepage with fallback SVG
- **Dynamic Content**: Blog system, job listings, services showcase
- **Security-First**: CSRF protection, input validation, XSS prevention

### Backend
- **Pure Python**: Using only Python standard library (no external dependencies)
- **Security Focused**: PBKDF2 password hashing, secure sessions, rate limiting
- **SQLite Database**: Comprehensive schema with 14 tables
- **RESTful API**: Clean JSON API for all frontend interactions
- **Logging & Audit**: Complete activity tracking and security logging

### Admin Portal
- **Employee Management**: Full CRUD operations for user accounts
- **Project & Task Management**: Assign and track work progress
- **Content Management**: Create/edit blog posts, case studies, updates
- **Careers Management**: Post job openings, manage applications
- **Document Management**: Upload and manage company documents
- **Audit Logging**: Track all admin activities for security

### Employee Portal
- **Digital ID Card**: QR code generation for employee identification
- **Attendance Tracking**: Clock in/out system with time tracking
- **Leave Management**: Request and track vacation/sick leave
- **Task Dashboard**: View assigned projects and tasks
- **Document Access**: Access company handbook and policies

## 📋 Requirements

- **Python 3.10+** (uses standard library only)
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)
- **Operating System**: Linux (Ubuntu 22.04 recommended), macOS, Windows

## ⚡ Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd matrica
```

### 2. Initialize Database
```bash
cd backend
python db_init.py
```

### 3. Start Server
```bash
python server.py
```

### 4. Access Application
- **Website**: http://localhost:8000
- **Admin Portal**: http://localhost:8000/portal/admin.html
- **Employee Portal**: http://localhost:8000/portal/employee.html

### 5. Admin Login
- **Username**: psychy
- **Password**: Ka05ml@2120

## 🎨 Customizing the Logo

### Replacing the Logo Files

1. **SVG Logo** (`frontend/assets/images/logo.svg`):
   ```bash
   # Replace with your SVG logo (recommended size: 40x40px)
   cp your-logo.svg frontend/assets/images/logo.svg
   ```

2. **Favicon** (`frontend/assets/images/favicon.png`):
   ```bash
   # Replace with your favicon (16x16 or 32x32 PNG)
   cp your-favicon.png frontend/assets/images/favicon.png
   ```

### Logo Requirements
- **Format**: SVG (vector) or PNG with transparency
- **Size**: 40x40px for navigation, scales automatically
- **Colors**: White/light colors work best with dark theme
- **Style**: Simple, recognizable at small sizes

### Updating Brand Name
Edit these files to change "Matrica Networks":

1. **HTML Files**: Update `<title>` tags and navigation text
2. **CSS Variables**: Modify brand colors in `frontend/assets/css/base.css`:
   ```css
   :root {
       --neon-blue: #00ffff;      /* Primary brand color */
       --neon-green: #00ff41;     /* Secondary brand color */
       --neon-purple: #ff00ff;    /* Accent color */
   }
   ```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Start Services**:
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

2. **Stop Services**:
   ```bash
   chmod +x stop_server.sh
   ./stop_server.sh
   ```

3. **View Logs**:
   ```bash
   docker-compose logs -f matrica
   ```

### Manual Docker Build

1. **Build Image**:
   ```bash
   docker build -t matrica-networks .\n   ```

2. **Run Container**:
   ```bash
   docker run -d \\\n     --name matrica \\\n     -p 8000:8000 \\\n     -v $(pwd)/backend/matrica.db:/app/backend/matrica.db \\\n     -v $(pwd)/backend/logs:/app/backend/logs \\\n     -v $(pwd)/backend/storage:/app/backend/storage \\\n     matrica-networks\n   ```

## 🌐 Production Deployment

### Server Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB minimum for logs and uploads
- **Network**: SSL certificate for HTTPS (required for production)

### Nginx Reverse Proxy Setup
```nginx
server {\n    listen 443 ssl http2;\n    server_name yourdomain.com;\n    \n    ssl_certificate /path/to/your/certificate.crt;\n    ssl_certificate_key /path/to/your/private.key;\n    \n    location / {\n        proxy_pass http://localhost:8000;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }\n    \n    # Security headers\n    add_header X-Frame-Options DENY;\n    add_header X-Content-Type-Options nosniff;\n    add_header X-XSS-Protection \"1; mode=block\";\n    add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\";\n}\n```

### Environment Variables
```bash
# Production settings\nexport MATRICA_ENV=production\nexport MATRICA_HOST=0.0.0.0\nexport MATRICA_PORT=8000\nexport MATRICA_DB_PATH=/app/data/matrica.db\nexport MATRICA_LOG_LEVEL=INFO\n```

### Systemd Service (Linux)
Create `/etc/systemd/system/matrica.service`:
```ini
[Unit]\nDescription=Matrica Networks Web Application\nAfter=network.target\n\n[Service]\nType=simple\nUser=matrica\nGroup=matrica\nWorkingDirectory=/opt/matrica\nExecStart=/usr/bin/python3 backend/server.py\nRestart=always\nRestartSec=10\n\n# Security settings\nPrivateTmp=true\nNoNewPrivileges=true\nProtectSystem=strict\nProtectHome=true\nReadWritePaths=/opt/matrica/backend/logs /opt/matrica/backend/storage\n\n[Install]\nWantedBy=multi-user.target\n```

Enable and start:
```bash\nsudo systemctl enable matrica\nsudo systemctl start matrica\nsudo systemctl status matrica\n```

## 📁 Project Structure

```\nmatrica/\n├── backend/                    # Python backend server\n│   ├── server.py              # Main WSGI application\n│   ├── models.py              # Database models\n│   ├── controllers.py         # API controllers\n│   ├── middleware.py          # Security middleware\n│   ├── auth.py                # Authentication utilities\n│   ├── db_init.py             # Database initialization\n│   ├── logs/                  # Application logs\n│   │   └── app.log           # Main log file\n│   └── storage/               # File storage\n│       ├── uploads/           # User uploads\n│       └── docs/              # Company documents\n│           ├── handbook.pdf\n│           └── policy.pdf\n├── frontend/                   # Static web frontend\n│   ├── index.html             # Homepage\n│   ├── products.html          # Products page\n│   ├── services.html          # Services page\n│   ├── blog.html              # Blog/content page\n│   ├── careers.html           # Careers page\n│   ├── contact.html           # Contact page\n│   ├── portal/                # Employee portal\n│   │   ├── login.html         # Login page\n│   │   ├── admin.html         # Admin dashboard\n│   │   └── employee.html      # Employee dashboard\n│   └── assets/                # Static assets\n│       ├── css/               # Stylesheets\n│       │   ├── base.css       # Base styles and variables\n│       │   ├── layout.css     # Layout and grid\n│       │   ├── components.css # UI components\n│       │   └── neon.css       # Neon effects\n│       ├── js/                # JavaScript files\n│       │   ├── main.js        # Main application\n│       │   ├── api.js         # API client\n│       │   ├── ui.js          # UI utilities\n│       │   ├── router.js      # Client-side routing\n│       │   └── webgl/         # WebGL globe\n│       │       ├── globe.js   # Globe implementation\n│       │       └── shaders.js # WebGL shaders\n│       └── images/            # Images\n│           ├── logo.svg       # Company logo\n│           └── favicon.png    # Site favicon\n├── docker-compose.yml         # Docker composition\n├── Dockerfile                 # Docker build file\n├── start_server.sh           # Start script\n├── stop_server.sh            # Stop script\n└── README.md                 # This file\n```

## 🔧 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/me` - Get current user info

### Public Endpoints
- `GET /api/jobs` - Get published job listings
- `GET /api/jobs/{id}` - Get job details
- `GET /api/blogs` - Get published blog posts
- `POST /api/contact` - Submit contact form

### Admin Endpoints (Requires Admin Role)
- `GET /api/employees` - List employees
- `POST /api/employees` - Create employee
- `GET /api/admin/jobs` - List all jobs
- `POST /api/admin/jobs` - Create job posting
- `PUT /api/admin/jobs/{id}` - Update job
- `DELETE /api/admin/jobs/{id}` - Delete job

## 🔐 Security Features

### Authentication & Authorization
- **PBKDF2 Password Hashing**: 100,000 iterations with salt
- **Secure Sessions**: HTTPOnly cookies with CSRF tokens
- **Role-Based Access**: Admin and employee role separation
- **Session Timeout**: 24-hour automatic expiration

### Input Validation & Sanitization
- **SQL Injection Prevention**: Prepared statements only
- **XSS Protection**: HTML entity encoding
- **CSRF Protection**: Token validation on all mutations
- **Path Traversal Prevention**: File access restrictions

### Rate Limiting
- **API Endpoints**: 100 requests per 15 minutes per IP
- **Login Attempts**: 5 attempts per 15 minutes per IP
- **Contact Form**: 3 submissions per hour per IP

### Security Headers
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: strict`

## 📊 Database Schema

### Core Tables
- **users**: Employee accounts and admin users
- **sessions**: Secure session management
- **projects**: Project management
- **tasks**: Task assignments and tracking
- **jobs**: Career postings and management
- **blogs**: Content management system
- **attendance**: Employee time tracking
- **contact_inquiries**: Contact form submissions
- **audit_log**: Security and activity logging

## 🔍 Troubleshooting

### Common Issues

1. **Port 8000 Already in Use**:
   ```bash
   # Find process using port 8000\n   lsof -i :8000\n   # Kill the process\n   kill -9 <PID>\n   ```

2. **Database Permission Issues**:
   ```bash\n   # Fix database permissions\n   chmod 664 backend/matrica.db\n   chown www-data:www-data backend/matrica.db  # Linux\n   ```

3. **WebGL Not Loading**:
   - Ensure browser supports WebGL\n   - Check browser console for errors\n   - Fallback SVG will display if WebGL unavailable\n\n4. **Admin Login Issues**:\n   ```bash\n   # Reset admin password\n   cd backend\n   python3 -c \"from db_init import create_admin_user; create_admin_user()\"\n   ```

### Log Files
- **Application Logs**: `backend/logs/app.log`
- **Error Logs**: Check browser console
- **Docker Logs**: `docker-compose logs matrica`

### Debug Mode
Enable debug logging:
```python\n# In backend/server.py\nlogging.basicConfig(level=logging.DEBUG)\n```

## 🚀 Performance Optimization

### Frontend
- **Minify CSS/JS**: Use build tools for production
- **Image Optimization**: Compress images, use WebP format
- **CDN**: Serve static assets from CDN
- **Caching**: Set appropriate cache headers

### Backend
- **Database Indexing**: All queries use proper indexes
- **Connection Pooling**: Implement for high traffic
- **Static File Serving**: Use Nginx for static files
- **Load Balancing**: Multiple server instances for scale

## 📈 Monitoring

### Health Checks
```bash\n# Check if server is running\ncurl -f http://localhost:8000/\n\n# Check API health\ncurl -f http://localhost:8000/api/me\n```

### Log Monitoring
```bash\n# Monitor application logs\ntail -f backend/logs/app.log\n\n# Monitor access patterns\ngrep \"POST\\|PUT\\|DELETE\" backend/logs/app.log\n```

## 🛡️ Backup & Recovery

### Database Backup
```bash\n# Create backup\ncp backend/matrica.db backend/backups/matrica_$(date +%Y%m%d_%H%M%S).db\n\n# Automated backup script\n#!/bin/bash\nBACKUP_DIR=\"/backup/matrica\"\ncp backend/matrica.db \"$BACKUP_DIR/matrica_$(date +%Y%m%d_%H%M%S).db\"\nfind \"$BACKUP_DIR\" -name \"matrica_*.db\" -mtime +30 -delete\n```

### File Storage Backup
```bash\n# Backup uploaded files\ntar -czf storage_backup_$(date +%Y%m%d).tar.gz backend/storage/\n```

## 📞 Support

### Documentation
- **API Documentation**: Available at `/api/docs` (when enabled)
- **User Guides**: Check `docs/` directory
- **Video Tutorials**: Available on company portal

### Technical Support
- **Email**: support@matricanetworks.com
- **Documentation**: This README and inline code comments
- **Issue Tracking**: Use your preferred system

## 🔄 Updates & Maintenance

### Regular Maintenance
1. **Database Cleanup**: Remove old sessions and logs monthly
2. **Log Rotation**: Rotate logs weekly to prevent disk full
3. **Security Updates**: Monitor Python security advisories
4. **Backup Verification**: Test backup restoration monthly

### Version Control
- Use semantic versioning (e.g., v1.0.0)
- Tag releases in Git
- Maintain changelog
- Test updates in staging environment

## 📝 License

Copyright (c) 2025 Matrica Networks Pvt Ltd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

**Built with ❤️ for cybersecurity professionals**

*Securing the digital frontier, one byte at a time.*
