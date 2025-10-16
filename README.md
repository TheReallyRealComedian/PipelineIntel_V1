# Pipeline Intelligence

Pipeline Intelligence is a web application designed to track and manage a portfolio of pharmaceutical assets. It provides a centralized platform for viewing product details, clinical indications, manufacturing processes, and supply chain information. It features advanced data management, a hierarchical modeling system for manufacturing complexity, and integrated LLM chat capabilities for data analysis.

The entire application is containerized using Docker for consistent development and deployment.

## Table of Contents
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Technical Architecture](#technical-architecture)
- [Database Schema](#database-schema)
- [Local Development Setup](#local-development-setup)
- [Development Workflow](#development-workflow)
- [Application Usage](#application-usage)
- [Production Deployment](#production-deployment)
- [Data Import Format](#data-import-format)
- [Contributing](#contributing)
- [License](#license)

## Key Features

- **Hierarchical Process Modeling**: Define manufacturing processes with unlimited nesting (e.g., Phase → Stage → Operation), allowing for both high-level and granular analysis.
- **Dynamic Data Tables**: Interactive tables with client-side sorting, filtering, and inline editing for all major data entities.
- **Customizable Views**: Users can customize which columns to display for each entity, with preferences saved locally.
- **Advanced Data Import**: A robust JSON import system with a preview screen, conflict resolution, automatic foreign key resolution by name, and detailed logging in the UI.
- **LLM Chat Integration**: A built-in chat interface to interact with and analyze the database's content using various Large Language Models.
- **Advanced Challenge Management**: A sophisticated system to track manufacturing challenges, distinguishing between those inherited from a process template and those added or excluded on a per-product basis.
- **Process Templates**: Define standard manufacturing process flows for different modalities (e.g., Monoclonal Antibody, Small Molecule) to ensure consistency.
- **Custom Data Export**: Generate tailored JSON exports with fine-grained field selection and a token counter for LLM prompt engineering.
- **Secure User Authentication**: A complete user registration and login system.
- **Modern UI**: A responsive design using Boehringer Ingelheim branding and a collapsible sidebar for improved navigation.

## Project Structure

A brief overview of the key directories and files in the project.

```
PipelineIntelligence/
├── backend/            # Main Flask application source code
│   ├── routes/         # Flask Blueprints for handling HTTP requests for each entity
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

The backend follows a clean architecture with a clear separation of concerns:

1.  **Routes (`/backend/routes`)**: Handles HTTP request routing using Flask Blueprints. Each major entity has its own route file (e.g., `product_routes.py`, `modality_routes.py`, `llm_routes.py`). API endpoints are separated into their own blueprints (e.g., `product_api_bp`) for clarity.

2.  **Services (`/backend/services`)**: Contains the core business logic. This layer is decoupled from the web framework, handling all database operations, data validation, and business rules. It ensures the application logic is reusable and testable.

3.  **Models (`/backend/models.py`)**: Defines the data access layer using SQLAlchemy ORM. All database table structures and their relationships are defined here.

#### Key Libraries & Components:

-   **Flask**: Micro web framework for the application's core.
-   **Flask-SQLAlchemy & SQLAlchemy**: Object-Relational Mapping (ORM) for database interaction.
-   **Flask-Migrate & Alembic**: Manages database schema migrations.
-   **Flask-Login**: Handles user session management.
-   **Flask-Assets**: Bundles and minifies CSS/JS assets.
-   **Gunicorn**: Production-ready WSGI server.
-   **psycopg2-binary**: PostgreSQL adapter for Python.
-   **tiktoken**: Used for counting tokens in the Data Export and LLM features.
-   **LangChain**: Powers integrations with various LLM providers.

### Frontend (HTML/CSS/JavaScript)

-   **Templating**: Jinja2 with reusable macros for dynamic components like sortable/filterable tables.
-   **Styling**: Custom CSS with Boehringer Ingelheim branding, using Bootstrap 5 for the responsive grid system.
-   **JavaScript**: Vanilla JavaScript for advanced table functionality, including client-side sorting/filtering, inline editing, column selection persistence, and the LLM chat interface.

## Database Schema

The application uses a powerful PostgreSQL schema designed to model pharmaceutical manufacturing complexity. It is managed via Alembic migrations and is documented in detail in `DATABASE_SCHEME.md`.

#### Core Design Principles

1.  **Hierarchical Modeling**: `Process Stages` support unlimited nesting through self-referential relationships, allowing for detailed process breakdowns (Phase → Stage → Operation).
2.  **Dual-Path Pattern**: Critical relationships, like capability requirements, exist at both a general "pattern" level (inherited from a `Modality`) and a "specific" level (overridden by a `Product`).
3.  **Name-Based Imports**: The data import system can resolve foreign key relationships by name (e.g., `"modality_name": "Monoclonal Antibody"`) instead of requiring IDs.

#### Key Entities

-   **Products (`products`)**: The central "hub" entity representing pharmaceutical assets. It contains extensive details for operational tracking, regulatory status, supply chain, and risks.
-   **Modalities (`modalities`)**: High-level product classifications (e.g., "Small Molecule", "CAR-T") that define standard process templates and capability requirements.
-   **Process Stages (`process_stages`)**: Represents individual steps in a manufacturing process. A self-referencing `parent_stage_id` allows for infinite hierarchical nesting.
-   **Process Templates (`process_templates`)**: Defines a standard sequence of `Process Stages` for a given `Modality`, forming a reusable manufacturing blueprint.
-   **Manufacturing Capabilities (`manufacturing_capabilities`)**: Granular skills or technologies required for production (e.g., "Cell Culture", "Aseptic Fill & Finish").
-   **Manufacturing Challenges (`manufacturing_challenges`)**: Potential risks or difficulties in the manufacturing process, which can be linked to products, technologies, or process stages.
-   **Manufacturing Technologies (`manufacturing_technologies`)**: Specific platforms or techniques used in manufacturing (e.g., "Twin Screw Granulation"). Now supports a **many-to-many relationship with modalities** via the `technology_modalities` junction table, allowing a single technology to be associated with multiple product types.

#### Manufacturing Network & Supply Chain

-   **Manufacturing Entities (`manufacturing_entities`)**: A polymorphic base table for any manufacturing site, either `Internal` or `External`.
-   **Internal Facilities (`internal_facilities`)** & **External Partners (`external_partners`)**: Tables containing specific details for internal sites and external CMOs, respectively.
-   **Entity Capabilities (`entity_capabilities`)**: A junction table defining which `Manufacturing Capabilities` each facility or partner possesses.

#### Operational Tracking Tables

The schema includes several tables linked directly to a `Product` to provide a detailed operational view:
-   **Product Timelines (`product_timelines`)**: Tracks key project milestones (e.g., Submission, Approval, Launch).
-   **Product Regulatory Filings (`product_regulatory_filings`)**: Manages regulatory submissions by geography and indication.
-   **Product Manufacturing Suppliers (`product_manufacturing_suppliers`)**: Provides detailed tracking of suppliers for Drug Substance (DS), Drug Product (DP), and devices.

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
    The default values in `.env` are suitable for local development. You do not need to change them to run the application locally.

3.  **Build and Run**
    ```bash
    docker-compose up --build
    ```
    This command will:
    -   Build the Docker images for the backend and database.
    -   Start the PostgreSQL and Flask containers.
    -   Automatically apply all database migrations on startup.
    -   Install all Python dependencies from `requirements.txt`.

4.  **Access the Application**
    Open your browser to: [http://localhost:5001](http://localhost:5001)

5.  **First-Time Setup**
    -   Register a new user account on the application's web interface.
    -   To populate the database with essential seed data (like modalities and capabilities), run the following script:
        ```bash
        docker-compose exec backend python backend/scripts/populate_core_data.py
        ```

### Development Workflow

-   **Live Reloading**: The Flask development server is configured for live reloading. Changes to Python files in the `backend/` directory will automatically restart the server.
-   **Database Changes**: To make changes to the database schema:
    1.  Modify your models in `backend/models.py`.
    2.  Generate a new migration script:
        ```bash
        docker-compose exec backend flask db migrate -m "A brief description of the schema change"
        ```
    3.  The new migration will be applied automatically the next time you run `docker-compose up`.
-   **Running Scripts**: To run a one-off script within the application context, use `docker-compose exec`:
    ```bash
    docker-compose exec backend python path/to/your/script.py
    ```
-   **Asset Changes**: CSS and JavaScript files in `backend/static/` are automatically bundled and minified by Flask-Assets. You may need to do a hard refresh (Ctrl+Shift+R) in your browser to see changes.

---

## Application Usage

### Data Management

-   **Import**: Upload JSON files with automatic conflict detection and foreign key resolution. The system provides a detailed preview, allowing you to accept, update, or skip each record before finalizing the import. The UI now features an enhanced logging panel that shows detailed, line-by-line progress of the import process. This log remains on screen after completion for review.
-   **Export**: Generate custom JSON datasets with fine-grained field selection across multiple entities. Includes a token counter for LLM prompt engineering.
-   **Inline Editing**: Edit data directly in tables for most entities. Changes are saved instantly with real-time validation.

### LLM Chat

-   Navigate to the "LLM Chat" page to start a conversation.
-   The chat interface has conversation memory for the current session.
-   You can define a custom "System Prompt" to guide the AI's behavior and save it to your user profile.
-   The system can connect to multiple LLM providers, which are configured in the backend.

### Table Features

-   **Sorting**: Click column headers to sort data client-side.
-   **Filtering**: Use the filter icon on each column header to show or hide specific values.
-   **Column Selection**: Customize which columns are visible in each table via the "Columns" dropdown.
-   **Persistence**: Your column visibility preferences are saved in your browser's local storage and applied automatically on future visits.

---

## Production Deployment

For a production environment, ensure the following steps are taken:

1.  Set `FLASK_ENV=production` and `FLASK_DEBUG=0` in your production environment variables.
2.  Update the `SECRET_KEY` in your `.env` file to a long, random string.
3.  Use strong, unique credentials for the PostgreSQL database (`POSTGRES_USER`, `POSTGRES_PASSWORD`).
4.  Consider using a reverse proxy like Nginx in front of Gunicorn for SSL termination, caching, and load balancing.
5.  Implement a robust backup and recovery strategy for the PostgreSQL database volume (`db_data`).

---

## Data Import Format

The application accepts a JSON array of objects for data import. The system is designed to be flexible and can resolve relationships by name.

**Example 1: Importing Products and linking to a Modality by name**

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

**Example 2: Importing Hierarchical Process Stages**

Use `parent_stage_name` to build the hierarchy. Parents must be defined before children.

```json
[
  {
    "stage_name": "Upstream Processing", 
    "hierarchy_level": 1
  },
  {
    "stage_name": "Cell Culture", 
    "hierarchy_level": 2, 
    "parent_stage_name": "Upstream Processing"
  }
]
```

**Example 3: Importing Manufacturing Technologies (New Format)**

Use the `modality_names` array to establish many-to-many relationships with modalities.

```json
[
  // Single modality
  {
    "technology_name": "Ex-Vivo T-Cell Expansion",
    "stage_name": "Chemical/Biological Production",
    "modality_names": ["CAR-T"]
  },
  // Multiple modalities
  {
    "technology_name": "Spray Drying",
    "stage_name": "Physical Processing & Drying",
    "modality_names": ["Small Molecule", "Peptides", "Oligonucleotides"]
  },
  // Generic technology (no specific modality)
  {
    "technology_name": "Track & Trace Serialization",
    "stage_name": "Secondary Packaging & Serialization",
    "modality_names": []
  },
  // DEPRECATED but supported: single modality_name
  {
    "technology_name": "Old Format Tech",
    "stage_name": "Some Stage",
    "modality_name": "Single Modality"
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