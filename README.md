```markdown
# MedShift Scheduler 🏥

> Employee scheduling and workforce management system for healthcare facilities

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.8-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

MedShift Scheduler is a comprehensive employee scheduling system designed specifically for medical clinics and healthcare facilities. It streamlines shift planning, time tracking, compliance management, and workforce optimization.

**Built for:** HealthCare Network Toronto (Bern, Switzerland deployment)

## ✨ Key Features
- 👥 **Employee Management** - Comprehensive staff profiles with medical certifications
- 📅 **Schedule Management** - Intuitive shift planning with drag-and-drop calendar
- ⏰ **Time Clock** - Clock-in/out with automatic overtime calculation
- 📊 **Dashboard** - Real-time metrics and workforce analytics
- 🔐 **Role-Based Access Control** - Granular permissions for different user roles
- 📱 **Responsive Design** - Material Design 3 UI works on all devices
- 🏥 **Medical Certifications** - Track FMH diplomas, cantonal permits, specialist certificates
- ⚕️ **Swiss Compliance** - TARMED billing codes, KVG/LAMal compliance, mandatory breaks
- 🚨 **On-Call Management** - Emergency shift scheduling and rotation management
- 📜 **Certification Expiry Tracking** - Automatic alerts 90/60/30 days before expiration
- ✅ **Minimum Staffing Validation** - Ensures compliance with doctor-to-patient ratios
- 📈 **Labor Cost Analysis** - Real-time ФОТ tracking and budget management
- 📄 **Reports** - Labor, payroll, attendance, and compliance reports
- ✉️ **Announcements** - Targeted communications to staff
- 📋 **Task Management** - Shift-based checklists and assignments
- 🔄 **Shift Templates** - Recurring schedule automation

## 🛠️ Tech Stack

**Backend:**
- Django 5.0+ (Python 3.12)
- PostgreSQL 15.8
- Celery + Redis (async tasks)
- Django REST Framework (API)

**Frontend:**
- Bootstrap 5.3
- Material Design 3 (Material Components for Web)
- Vanilla JavaScript
- Chart.js (data visualization)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Traefik (load balancing, SSL)

**Development:**
- pytest (testing)
- black (code formatting)
- flake8 (linting)

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/medshift-scheduler.git
   cd medshift-scheduler
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start database**
   ```bash
   docker-compose up -d
   ```

4. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements/development.txt
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - App: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - pgAdmin: http://localhost:15433 (username: admin@healthcarenetwork.local, password: admin)

## 📦 Project Structure

```
medshift-scheduler/
├── apps/                     # Django applications
│   ├── accounts/            # Authentication
│   ├── employees/           # Employee management
│   ├── schedules/           # Shift scheduling
│   ├── timeclock/           # Time tracking
│   ├── certifications/      # Medical certifications
│   ├── medical_compliance/  # Swiss compliance
│   ├── permissions/         # RBAC
│   ├── dashboard/           # Main dashboard
│   ├── timeoff/             # Leave requests
│   ├── notifications/       # Notification system
│   └── core/                # Shared utilities
│   ├── templates/core/
│   │   └── help.html                      # Страница Help в приложении
│   ├── views.py                           # View для Help
│   └── urls.py                            # URL для Help
├── docs/
│   ├── README.md                          # Общая информация о документации
│   ├── convert_to_pdf.sh                  # Скрипт конвертации в PDF
│   └── user-manual/
│       ├── USER_MANUAL.md                 # Полное руководство (60+ страниц)
│       ├── QUICK_START.md                 # Быстрый старт (5 минут)
│       ├── SCREENSHOT_LIST.md             # Список нужных скриншотов (45+)
│       ├── images/                        # Дополнительные изображения
│       └── screenshots/                   # Папка для скриншотов
│           ├── 01_login_page.png
│           ├── 02_login_form_highlighted.png
│           └── ... (45+ files)
├── config/                   # Django settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── static/                   # Static files (CSS, JS, images)
│   ├── docs/                           # Готовые PDF файлы
│   ├── USER_MANUAL.pdf
│   └── QUICK_START.pdf
├── templates/                # HTML templates
├── media/                    # User uploads
├── requirements/             # Python dependencies
├── docker-compose.yml        # Development Docker config
├── docker-compose-swarm.yaml # Production Docker Swarm config
├── Dockerfile                # Production Docker image
└── manage.py                 # Django management script
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production (Docker Swarm)
```bash
# Create secrets
echo "your-secret-key" | docker secret create django_secret_key -
echo "your-db-password" | docker secret create db_password -

# Deploy stack
ENV_STAGE=production docker stack deploy -c docker-compose-swarm.yaml medshift
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/schedules/tests/
```

## 📝 Development Workflow

1. Create feature branch: `git checkout -b feature/certification-expiry`
2. Make changes
3. Run tests: `pytest`
4. Format code: `black .`
5. Check linting: `flake8`
6. Commit: `git commit -m "Add certification expiry tracking"`
7. Push: `git push origin feature/certification-expiry`
8. Create Pull Request

## 📖 Documentation

- [Project Planning](docs/planning/) - Detailed project documentation
- [API Documentation](docs/api/) - REST API endpoints (coming soon)
- [Deployment Guide](docs/deployment/) - Production deployment instructions
- [User Guide](docs/user-guide/) - End-user documentation

## 🗓️ Roadmap

### Phase 1: MVP (Weeks 1-10) ✅ In Progress
- [x] Project setup
- [x] Authentication system
- [ ] Employee management
- [ ] Schedule management
- [ ] Time clock
- [ ] Basic dashboard

### Phase 2: Core Features (Weeks 11-18)
- [ ] Medical certifications
- [ ] Swiss compliance module
- [ ] Role-based permissions
- [ ] Time-off requests
- [ ] Email notifications

### Phase 3: Analytics (Weeks 19-26)
- [ ] Labor cost analysis
- [ ] Reports module
- [ ] Task management
- [ ] Announcements

### Phase 4: Advanced (Weeks 27+)
- [ ] Shift templates
- [ ] Advanced reports
- [ ] API for mobile app
- [ ] Swiss eHealth integration

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

Please ensure:
- All tests pass
- Code is formatted with `black`
- No linting errors (`flake8`)
- Commit messages are descriptive

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

**HealthCare Network Toronto**
- Location: Sion, Switzerland
- Contact: dev@healthcarenetwork.ca

**Development Team:**
- Backend Developer: [Your Name]
- Frontend Developer: [Name]
- Project Manager: [Name]

## 🙏 Acknowledgments

- Django framework
- Material Design 3 by Google
- Bootstrap team
- All open-source contributors

## 📞 Support

For support, email dev@healthcarenetwork.ca or open an issue in the GitHub repository.

---

**Status:** 🚧 In Development (Phase 1 - MVP)  
**Last Updated:** January 2025
```
