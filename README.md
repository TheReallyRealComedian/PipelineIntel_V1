# Pipeline Intelligence

Pipeline Intelligence is a web application designed to track and manage a portfolio of pharmaceutical assets. It provides a centralized platform for viewing product details, clinical indications, supply chain information, manufacturing challenges and technologies, with advanced data management and export capabilities.

The entire application is containerized using Docker for consistent development and deployment.

## Key Features

- **Dynamic Data Tables**: Interactive tables with client-side sorting, filtering, and inline editing
- **Flexible Column Management**: Users can customize which columns to display for each entity type
- **JSON Data Import**: Import data with preview and conflict resolution before committing changes
- **Custom Data Export**: Generate tailored JSON exports with token counting for LLM applications
- **User Authentication**: Secure user registration and login system
- **LLM Integration Settings**: User-specific API key management for various LLM providers
- **Modern UI**: Responsive design with Boehringer Ingelheim branding

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

1. **Routes (`/backend/routes`)**: HTTP request handling using Flask Blueprints
   - `auth_routes.py` - User authentication and registration
   - `product_routes.py` - Product management and inline editing
   - `indication_routes.py` - Clinical indications
   - `challenge_routes.py` - Manufacturing challenges with inline editing
   - `technology_routes.py` - Manufacturing technologies
   - `partner_routes.py` - Partner/CMO management
   - `data_management_routes.py` - JSON import with preview functionality
   - `export_routes.py` - Custom data export with field selection
   - `settings_routes.py` - User settings and LLM API key management
   - `api_routes.py` - RESTful API endpoints

2. **Services (`/backend/services`)**: Business logic layer
   - Decoupled from web framework for better testability
   - Handles all database operations and business rules
   - Includes specialized services for data import/export operations

3. **Models (`/backend/models.py`)**: Data access layer using SQLAlchemy ORM

#### Key Libraries & Components:

- **Flask**: Micro web framework
- **Flask-SQLAlchemy & SQLAlchemy**: Object-Relational Mapping (ORM)
- **Flask-Migrate & Alembic**: Database schema migrations
- **Flask-Login**: User session management
- **Flask-Assets**: CSS/JS bundling and minification
- **Gunicorn**: Production WSGI server
- **tiktoken**: Token counting for LLM integrations

### Frontend (HTML/CSS/JavaScript)

- **Templating**: Jinja2 with reusable macros for dynamic tables
- **Styling**: Custom CSS with Boehringer Ingelheim branding, Bootstrap 5 for responsive grid
- **JavaScript**: Advanced table functionality including:
  - Client-side sorting and filtering
  - Inline cell editing with real-time validation
  - Column selection and persistence
  - Dynamic filter dropdowns
- **User Experience**: Modern, responsive interface with hover effects and smooth transitions

### Database Schema

The application uses PostgreSQL with the following core entities:

#### 1. Products (`products`)
| Field Name                | Data Type   | Description                                                                 |
| :------------------------ | :---------- | :-------------------------------------------------------------------------- |
| `product_id`              | Integer     | **Primary Key**                                                             |
| `product_code`            | String(100) | **Unique, Required**. Business identifier (e.g., "XYZ-001")                |
| `product_name`            | String(255) | Common name of the product                                                  |
| `product_type`            | String(100) | Product type (e.g., "Monoclonal Antibody")                                 |
| `base_technology`         | String(255) | Core technology platform                                                    |
| `mechanism_of_action`     | Text        | Description of how the product works                                        |
| `dosage_form`             | String(255) | Physical form (e.g., "Tablet", "Injectable")                               |
| `therapeutic_area`        | String(255) | **Indexed**. Primary medical field (e.g., "Oncology")                      |
| `current_phase`           | String(100) | **Indexed**. Clinical development phase (e.g., "Phase III")                |
| `project_status`          | String(100) | **Indexed**. Current project status (e.g., "Ongoing")                      |
| `lead_indication`         | String(255) | Primary indication for development                                          |
| `expected_launch_year`    | Integer     | Projected market launch year                                                |
| `lifecycle_indications`   | JSONB       | Array of potential future indications                                       |
| `regulatory_designations` | JSONB       | Special regulatory statuses (e.g., "Fast Track")                           |
| `manufacturing_strategy`  | String(100) | High-level manufacturing strategy (e.g., "Internal", "CMO")                |
| `manufacturing_sites`     | JSONB       | Array of manufacturing sites                                                |
| `volume_forecast`         | JSONB       | Forecasted production volumes                                               |
| `created_at`/`updated_at` | DateTime    | Audit timestamps                                                            |

#### 2. Indications (`indications`)
Specific clinical indications linked to products.

#### 3. Manufacturing Challenges (`manufacturing_challenges`)
Categorized manufacturing challenges with many-to-many product relationships.

#### 4. Manufacturing Technologies (`manufacturing_technologies`)
Technologies used in manufacturing processes.

#### 5. Partners (`partners`)
External partners including Contract Manufacturing Organizations (CMOs).

#### 6. Product Supply Chain (`product_supply_chain`)
Links products to internal sites or external partners for different manufacturing stages.

#### 7. Association Tables
- `product_to_challenge`: Many-to-many relationship between products and challenges
- `product_to_technology`: Many-to-many relationship between products and technologies

#### 8. System Tables
- `users`: User authentication
- `llm_settings`: User-specific LLM API keys and settings

---

## Local Development Setup

### Prerequisites
- Git
- Docker and Docker Compose
- Web browser

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd PipelineIntelligence
   ```

2. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=a-very-secret-key-that-you-should-change-in-production
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=asset_tracker_db
   DATABASE_URL=postgresql://user:password@db:5432/asset_tracker_db
   ```

3. **Build and Run**
   ```bash
   docker-compose up --build
   ```
   
   This will:
   - Build the Docker images
   - Start PostgreSQL and Flask containers
   - Apply database migrations automatically
   - Install all dependencies

4. **Access the Application**
   Open your browser to: [http://localhost:5001](http://localhost:5001)

5. **First-Time Setup**
   - Register a new user account
   - Import sample data via the Data Management page (optional)

### Development Workflow

- **Live Reloading**: The application supports live reloading during development
- **Database Changes**: Use `flask db migrate` and `flask db upgrade` for schema changes
- **Asset Changes**: CSS/JS files are automatically bundled and minified

---

## Application Usage

### Data Management
- **Import**: Upload JSON files with automatic conflict detection and preview
- **Export**: Generate custom JSON datasets with field selection and token counting
- **Inline Editing**: Edit data directly in tables with real-time validation

### Table Features
- **Sorting**: Click column headers to sort ascending/descending
- **Filtering**: Use dropdown filters to show/hide specific values
- **Column Selection**: Customize which columns are displayed
- **Persistence**: Table preferences are saved per user session

### User Settings
- Configure LLM API keys for OpenAI, Anthropic, Google, and other providers
- Set up local model endpoints (Ollama)
- Configure Apollo integration settings

---

## Production Deployment

For production deployment:

1. Update the `SECRET_KEY` in your `.env` file
2. Configure proper PostgreSQL credentials
3. Set `FLASK_ENV=production`
4. Consider using a reverse proxy (nginx) for SSL termination
5. Set up proper backup procedures for the PostgreSQL database

---

## Data Import Format

The application accepts JSON arrays for data import. Example format for products:

```json
[
  {
    "product_code": "XYZ-001",
    "product_name": "Example Drug",
    "therapeutic_area": "Oncology",
    "current_phase": "Phase III",
    "project_status": "Ongoing",
    "expected_launch_year": 2026
  }
]
```

For manufacturing challenges, include `product_codes` array to link to existing products:

```json
[
  {
    "challenge_name": "Scale-up Challenges",
    "challenge_category": "Manufacturing",
    "explanation": "Difficulties in scaling production",
    "product_codes": ["XYZ-001", "ABC-002"]
  }
]
```

---

## Contributing

1. Follow the existing code structure with routes, services, and models separation
2. Add appropriate database migrations for schema changes
3. Include both frontend and backend validation for new features
4. Update this README when adding new major features

---

## License

[Add your license information here]