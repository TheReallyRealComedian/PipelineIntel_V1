# Pipeline Intelligence

Pipeline Intelligence is a web application designed to track and manage a portfolio of pharmaceutical assets. It provides a centralized platform for viewing product details, clinical indications, supply chain information, manufacturing challenges and technologies, with advanced data management and export capabilities.

The entire application is containerized using Docker for consistent development and deployment.

## Table of Contents
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Technical Architecture](#technical-architecture)
- [Database Schema](#database-schema)
- [Local Development Setup](#local-development-setup)
- [Development Workflow](#development-workflow)
- [Database Query Patterns](#database-query-patterns)
- [Implementation Steps](#implementation-steps)
- [Application Usage](#application-usage)
- [Production Deployment](#production-deployment)
- [Data Import Format](#data-import-format)
- [Contributing](#contributing)
- [License](#license)

## Key Features

- **Dynamic Data Tables**: Interactive tables with client-side sorting, filtering, and inline editing.
- **Flexible Column Management**: Users can customize which columns to display for each entity type.
- **JSON Data Import**: Import data with a preview and conflict resolution before committing changes.
- **Custom Data Export**: Generate tailored JSON exports with token counting for LLM applications.
- **User Authentication**: Secure user registration and login system.
- **LLM Integration Settings**: User-specific API key management for various LLM providers.
- **Modern UI**: Responsive design with Boehringer Ingelheim branding.

## Project Structure

A brief overview of the key directories and files in the project.

```
PipelineIntelligence/
├── backend/            # Main Flask application source code
│   ├── routes/         # Flask Blueprints for handling HTTP requests
│   ├── services/       # Business logic layer, decoupled from web framework
│   ├── static/         # CSS, JavaScript, and other static assets
│   ├── templates/      # Jinja2 templates for rendering HTML
│   ├── app.py          # Flask application factory
│   ├── models.py       # SQLAlchemy ORM models
│   └── Dockerfile      # Dockerfile for the backend service
├── migrations/         # Alembic database migration scripts
├── .env                # Local environment variables (not version controlled)
├── example.env         # Template for creating the .env file
├── docker-compose.yml  # Defines and runs the multi-container Docker application
└── README.md           # This file
```

## Technical Architecture

The application is built on a Python/Flask backend with a dynamic JavaScript-powered frontend, using PostgreSQL for data persistence.

### High-Level Overview

```
+----------------+      +--------------------------+      +---------------------+
|                |      |                          |      |                     |
|      User      +----->|     Web Browser          |      |   Backend (Flask)   |
|                |      |  (HTML/CSS/JavaScript)   |<---->|  (Gunicorn Server)  |
+----------------+      |                          |      |                     |
                        +--------------------------+      +----------+----------+
                                                                     |
                                                                     |
                                                            +--------v--------+
                                                            |                 |
                                                            |   PostgreSQL    |
                                                            |    Database     |
                                                            |                 |
                                                            +-----------------+

[ All services run inside Docker containers managed by Docker Compose ]
```

### Backend (Python/Flask)

The backend follows a clean architecture with three main layers:

1.  **Routes (`/backend/routes`)**: HTTP request handling using Flask Blueprints.
    -   `auth_routes.py` - User authentication and registration.
    -   `product_routes.py` - Product management and inline editing.
    -   `modality_routes.py` - Manufacturing modalities.
    -   `challenge_routes.py` - Manufacturing challenges.
    -   `facility_routes.py` - Internal facilities and external partner management.
    -   `data_management_routes.py` - JSON import with preview functionality.
    -   `export_routes.py` - Custom data export with field selection.
    -   `settings_routes.py` - User settings and LLM API key management.
    -   `analytics_routes.py` - Endpoints for strategic analytics dashboards.

2.  **Services (`/backend/services`)**: Business logic layer.
    -   Decoupled from the web framework for better testability.
    -   Handles all database operations and business rules.

3.  **Models (`/backend/models.py`)**: Data access layer using SQLAlchemy ORM.

#### Key Libraries & Components:

-   **Flask**: Micro web framework.
-   **Flask-SQLAlchemy & SQLAlchemy**: Object-Relational Mapping (ORM).
-   **Flask-Migrate & Alembic**: Database schema migrations.
-   **Flask-Login**: User session management.
-   **Flask-Assets**: CSS/JS bundling and minification.
-   **Gunicorn**: Production WSGI server.
-   **tiktoken**: Token counting for LLM integrations.

### Frontend (HTML/CSS/JavaScript)

-   **Templating**: Jinja2 with reusable macros for dynamic tables.
-   **Styling**: Custom CSS with Boehringer Ingelheim branding, Bootstrap 5 for the responsive grid.
-   **JavaScript**: Advanced table functionality including client-side sorting/filtering, inline editing, and column selection persistence.

## Database Schema

The application uses PostgreSQL with a flexible, multi-table schema to model manufacturing intelligence. The schema is managed by Alembic migrations.

#### 1. Core Entities

-   **Products (`products`)**: The central entity representing pharmaceutical assets. Contains details on type, phase, strategy, and links to other entities.
-   **Indications (`indications`)**: Clinical indications associated with a specific `Product`.
-   **Modalities (`modalities`)**: High-level classifications of products (e.g., "Monoclonal Antibody", "CAR-T"). Defines standard requirements.
-   **Manufacturing Capabilities (`manufacturing_capabilities`)**: Granular skills or technologies required for production (e.g., "Cell Culture", "Aseptic Fill & Finish").
-   **Manufacturing Challenges (`manufacturing_challenges`)**: Potential risks or difficulties in the manufacturing process.
-   **Manufacturing Technologies (`manufacturing_technologies`)**: Specific technologies or platforms used.

#### 2. Manufacturing Network & Supply Chain

This is modeled using a polymorphic-style base table (`manufacturing_entities`) with specific details in separate tables.

-   **Manufacturing Entities (`manufacturing_entities`)**: A base table for any manufacturing location or partner. Contains `entity_id`, `entity_name`, and `entity_type` ('Internal' or 'External').
-   **Internal Facilities (`internal_facilities`)**: Stores details specific to internal sites (e.g., `facility_code`, `cost_center`).
-   **External Partners (`external_partners`)**: Stores details for external partners like CMOs (e.g., `company_name`, `relationship_type`).
-   **Product Supply Chain (`product_supply_chain`)**: Links a `Product` to a `ManufacturingEntity` for a specific manufacturing stage.

#### 3. Requirements & Capabilities (The "Matrix")

-   **Modality Requirements (`modality_requirements`)**: Junction table defining which `ManufacturingCapabilities` are required by a `Modality`.
-   **Product Requirements (`product_requirements`)**: Junction table for product-specific `ManufacturingCapabilities` that override or add to the modality's standard set.
-   **Entity Capabilities (`entity_capabilities`)**: Junction table defining which `ManufacturingCapabilities` a `ManufacturingEntity` possesses.

#### 4. Process Chain

-   **Process Stages (`process_stages`)**: Defines the steps in a manufacturing process (e.g., "Upstream", "Downstream").
-   **Process Templates (`process_templates`)**: Defines a standard sequence of `ProcessStages` for a given `Modality`.

#### 5. System Tables & Views

-   **System Tables**: `users`, `llm_settings`, `flask_sessions` for application operation.
-   **SQL Views**: Pre-aggregated views like `all_product_requirements` and `product_complexity_summary` for efficient strategic analysis.

---

## Local Development Setup

### Prerequisites

-   Git
-   Docker and Docker Compose
-   Web browser

### Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd PipelineIntelligence
    ```

2.  **Environment Configuration**
    Copy the example environment file to create your local configuration.
    ```bash
    cp example.env .env
    ```
    The default values in `.env` are suitable for local development. You can customize them if needed.

3.  **Build and Run**
    ```bash
    docker-compose up --build
    ```
    This command will:
    -   Build the Docker images for the backend and database.
    -   Start the PostgreSQL and Flask containers.
    -   Automatically apply all database migrations on startup.
    -   Install all Python dependencies.

4.  **Access the Application**
    Open your browser to: [http://localhost:5001](http://localhost:5001)

5.  **First-Time Setup**
    -   Register a new user account on the application's web interface.
    -   You can optionally populate the database with initial sample data (see "Running Scripts" below).

### Development Workflow

-   **Live Reloading**: The Flask development server is configured for live reloading. Changes to Python files in the `backend/` directory will automatically restart the server.
-   **Database Changes**: To make changes to the database schema:
    1.  Modify your models in `backend/models.py`.
    2.  Generate a new migration script:
        ```bash
        docker-compose exec backend flask db migrate -m "A brief description of the schema change"
        ```
    3.  The migration will be applied automatically the next time you run `docker-compose up`.
-   **Running Scripts**: To run a one-off script within the application context (e.g., to populate data), use `docker-compose exec`:
    ```bash
    docker-compose exec backend python backend/scripts/populate_core_data.py
    ```
-   **Asset Changes**: CSS and JavaScript files in `backend/static/` are automatically bundled and minified by Flask-Assets. You may need to do a hard refresh (Ctrl+Shift+R) in your browser to see changes.

## Database Query Patterns

### Preferred Patterns

#### Standard Model Queries - Use `Model.query`
```python
# ✅ PREFERRED
products = Product.query.all()
product = Product.query.get(id)
filtered = Product.query.filter(Product.status == 'active').all()
```

#### SQL Views - Use `db.session.query()`
```python
# ✅ REQUIRED for views
requirements = db.session.query(all_product_requirements_view).all()
```

#### Complex Multi-Model Queries - Use `db.session.query()`
```python
# ✅ ACCEPTABLE for complex cases
results = db.session.query(Product.name, Modality.category).join(Modality).all()
```

#### Pattern Selection Rule

Default to `Model.query` for single-model operations.
Use `db.session.query()` only when `Model.query` is insufficient.

## Implementation Steps

### **Step 1:** Apply the changes above to `data_management_service.py`

### **Step 2:** Run verification:
```bash
# Check for remaining inconsistencies:
grep -n "db\.session\.query(" backend/services/data_management_service.py

# Should only show view queries and complex joins after changes
```

---

## Application Usage

### Data Management

-   **Import**: Upload JSON files with automatic conflict detection. The system provides a detailed preview, allowing you to accept, update, or skip each record before finalizing the import.
-   **Export**: Generate custom JSON datasets with fine-grained field selection across multiple entities. Includes a token counter for LLM prompt engineering.
-   **Inline Editing**: Edit data directly in tables. Changes are saved instantly with real-time validation.

### Table Features

-   **Sorting**: Click column headers to sort data client-side.
-   **Filtering**: Use dropdown filters on each column to show or hide specific values.
-   **Column Selection**: Customize which columns are visible in each table.
-   **Persistence**: Your column visibility preferences are saved in your browser's local storage and applied automatically on future visits.

---

## Production Deployment

For a production environment, ensure the following steps are taken:

1.  Set `FLASK_ENV=production` and `FLASK_DEBUG=0` in your production environment variables.
2.  Update the `SECRET_KEY` in your `.env` file to a long, random string.
3.  Use strong, unique credentials for the PostgreSQL database (`POSTGRES_USER`, `POSTGRES_PASSWORD`).
4.  Consider using a reverse proxy like Nginx in front of Gunicorn for SSL termination, caching, and load balancing.
5.  Implement a robust backup and recovery strategy for the PostgreSQL database volume.

---

## Data Import Format

The application accepts a JSON array of objects for data import.

**Example 1: Importing Products and linking to a Modality by name**

The system can resolve foreign key relationships by name. Provide `modality_name` instead of `modality_id`.

```json
[
  {
    "product_code": "XYZ-001",
    "product_name": "Example mAb",
    "modality_name": "Monoclonal Antibody",
    "therapeutic_area": "Oncology",
    "current_phase": "Phase III"
  }
]
```

**Example 2: Importing Challenges and linking them to existing Products**

Use the `product_codes` array to establish many-to-many relationships.

```json
[
  {
    "challenge_name": "Scale-up Challenges",
    "challenge_category": "Manufacturing",
    "explanation": "Difficulties in scaling production from pilot to commercial.",
    "product_codes": ["XYZ-001", "ABC-002"]
  }
]
```

---

## Contributing

1.  Follow the existing code structure with a clear separation of routes, services, and models.
2.  Add appropriate Alembic database migrations for any schema changes.
3.  Include both frontend and backend validation for new features.
4.  Update this README when adding new major features or changing the architecture.

---

## License

[Add your license information here]