# MedShift Scheduler Documentation

## 📚 Available Documentation

### For End Users:
- **[User Manual](user-manual/USER_MANUAL.md)** - Complete guide for using the system
- **[Quick Start Guide](user-manual/QUICK_START.md)** - 5-minute setup guide
- **[Screenshot List](user-manual/SCREENSHOT_LIST.md)** - Required screenshots for manual

### For Developers:
- Coming in Phase 2

### For Administrators:
- Coming in Phase 2

---

## 🖼️ Taking Screenshots

1. Seed the database: `python manage.py seed_employees`
2. Follow the checklist in `user-manual/SCREENSHOT_LIST.md`
3. Save screenshots to `user-manual/screenshots/`
4. Use naming convention: `[number]_[description].png`

---

## 📄 Converting to PDF

### Requirements:
```bash
# Install pandoc
# macOS
brew install pandoc basictex

# Ubuntu/Debian
sudo apt install pandoc texlive-xetex

# Windows
# Download from https://pandoc.org/installing.html