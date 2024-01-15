# System for accounting, tracking and analyzing the performance of operations by dental technicians

## Table of contents
* [Introduction](#introduction)
* [Technologies](#technologies)
* [Tools](#tools)
* [Installation](#installation)

<a name="introduction"></a>
## Introduction

The system is designed for a dental laboratory. The laboratory receives orders from clients (doctors). Each order consists of products. To perform each product, several dental technicians must perform a sequence of operations. After completing all the work, the doctor accepts and pays for the products.

There are 5 roles in the system:
1. *Doctor*. The doctor can register in the system, place orders and view the progress of his orders.
2. *Dental technician*. A dental technician can receive operations to perform and mark their statuses.
3. *Chief dental technician*. The Chief technician can assign operations to technicians and view the progress of all work. Also, the chief technician can perform operations just like a regular technician.
4. *Laboratory administrator*. The administrator can view the progress of work, place and adjust orders, and distribute operations to technicians.
5. *Director*. The director has the same capabilities as the administrator, but he also has access to statistics on order fulfillment.

<a name="technologies"></a>
## Technologies
* Backend:
  - Python 3.10
  - Django 4
  - Django REST Framework
  - DRF-simplejwt
  - DRF-spectacular
* Frontend:
  - JavaScript
  - React
  - Axios
  - Material UI and Bootstrap
  - JWT-decode
* Database:
  - PostgreSQL

<a name="tools"></a>
## Tools
* Python interpreter
* VS Code
* Package manager for Node.js - npm
* Package manager for Python - pip
* DBeaver
* Git

<a name="installation"></a>
## Installation
1. Clone the repository:
```commandline
git clone https://github.com/AlexSserb/dental-lab.git
```
2. Create PostgreSQL database using PgAdmin or DBeaver with name "DentalLabDB" and port 5432.

3. Run backend part.

3.1. Create and activate virtual environment:
```commandline
cd dental-lab\backend
python -m venv venv 
venv\\Scripts\\activate
```
3.2. Install requirements:
```commandline
pip install -r requirements.txt 
```
3.3. Create and run migrations:
```commandline
python manage.py makemigrations
python manage.py migrate
```
3.4. Load all fixtures:
```commandline
python manage.py loaddata groups_data.json
```

4. Run frontend part.
```commandline
cd dental-lab\frontend
npm i
npm start
```