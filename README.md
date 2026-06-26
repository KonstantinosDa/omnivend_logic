# Omnivend Logic

Omnivend Logic is a backend-focused inventory, logistics, and analytics platform designed for vending machine operations. It enables real-time inventory tracking, automated restocking, demand forecasting, and revenue monitoring across distributed vending machines and delivery trucks.

The system is built with scalability and automation in mind, simulating real-world operational challenges in retail logistics.

---

## Key Features

###  Real-time Inventory Tracking
- Trucks and vending machines update inventory in real time.
- Centralized system for monitoring stock across all machines.

### Demand Forecasting (Machine Learning)
- Predicts next-day sales per product per machine.
- Uses historical sales data and contextual factors to estimate demand.

###  Role-Based Access Control (RBAC)
- Secure authentication system with role-based permissions.
- Different access levels for admins, managers, drivers, and visitors.

###  Public Product Availability Search
- Users can search for products and see where they are available.
- Displays vending machine locations with stock availability.

###  Revenue Tracking
- Tracks revenue per vending machine.
- Provides insights into machine performance and profitability.

###  Automated Restocking System
- Automatically generates restocking orders based on inventory thresholds and demand forecasts.
- Reduces manual intervention and stock shortages.

---

##  Upcoming Features

###  User Management System
- Full CRUD user management (create, update, deactivate accounts).
- Enhanced admin control over system users and roles.

###  Route Optimization
- Generates optimized delivery routes for restocking trucks.
- Aims to improve logistics efficiency and reduce travel time.

###  Analytics Dashboard
- Sales trends and performance metrics.
- Machine-level and product-level analytics.
- Data visualization for operational insights.

---

## 🛠 Tech Stack

- **Backend:** Python, Django, Django REST Framework  
- **Database:** MySQL  
- **Data Processing:** Pandas  
- **Authentication:** JWT / Session-based auth (if applicable)  
- **Version Control:** Git  

---

##  Architecture Overview

The system is structured into modular components:

- Inventory Management Service  
- Order & Restocking Engine  
- Forecasting Module (ML-based)  
- Revenue Tracking System  
- User & Role Management System  
- Public Product Search API  

Each module communicates through REST APIs and shares a centralized relational database.

---

##  Purpose of the Project

This project was built to simulate a real-world vending machine logistics platform, focusing on:

- Backend system design
- API development
- Automation of operational workflows
- Data-driven decision making
- Scalable architecture principles

---

## 🔮 Future Improvements

- Docker containerization
- Celery for background tasks
- PostgreSQL migration
- Swagger/OpenAPI documentation
- Unit and integration testing
- Real-time notifications (email/SMS)
- Advanced route optimization algorithms
- Machine health monitoring

---

## Author

**Konstantinos Daravagkas**  
Backend Developer  