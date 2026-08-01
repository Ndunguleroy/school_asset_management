# School Asset Management System

A web based system built with Python Flask for managing school assets across departments and faculties.

## Features
- Role based access control (Admin, Asset Officer, Department Head, Staff)
- Asset registration, allocation and tracking
- Maintenance management
- Asset request and approval workflow
- Reports and inventory management

## Tech Stack
- Backend: Python 3 with Flask
- Database: MySQL
- Frontend: HTML, CSS, Bootstrap 5, JavaScript
- ORM: Flask SQLAlchemy
- Authentication: Flask Login

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/yourusername/school_asset_management.git
cd school_asset_management

### 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Create your .env file
Copy the .env.example file and fill in your values:
cp .env.example .env

### 5. Set up the database
Create a MySQL database called school_assets_db then run:
flask db upgrade

### 6. Create the first admin account
python3 create_admin.py

### 7. Run the application
python3 run.py