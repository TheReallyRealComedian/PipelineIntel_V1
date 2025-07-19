# Pipeline Intelligence

Pipeline Intelligence is a web application designed to track and manage a portfolio of pharmaceutical assets. It provides a centralized platform for viewing product details, clinical indications, supply chain information, and associated manufacturing challenges and technologies.

The entire application is containerized using Docker for consistent development and deployment.

## Technical Architecture

The application is built on a Python/Flask backend and a dynamic, JavaScript-powered frontend, with a PostgreSQL database for data persistence.

### High-Level Overview

The architecture follows a standard client-server model, orchestrated by Docker Compose.

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

The backend is the application's core, handling business logic, data persistence, and API endpoints. It is built using the **Flask** web framework.

The backend code is structured into three main layers:

1.  **Routes (`/backend/routes`)**: This layer handles incoming HTTP requests. It uses Flask Blueprints to organize functionality by domain (e.g., `product_routes.py`, `challenge_routes.py`). Routes are responsible for receiving requests, calling the appropriate service to handle the logic, and rendering a Jinja2 template or returning a JSON response.

2.  **Services (`/backend/services`)**: This is the business logic layer, decoupled from the web framework. It contains the core application logic. For example, `product_service.py` handles business logic related to products, while `data_management_service.py` contains the logic for importing and exporting data.

3.  **Models (`/backend/models.py`)**: This is the data access layer. It uses the **SQLAlchemy ORM** to define the database schema as Python classes (`Product`, `Indication`, `ManufacturingChallenge`, etc.). All database interactions from the services go through these models.

#### Key Libraries & Components:

*   **Flask**: The micro web framework that underpins the entire backend.
*   **Flask-SQLAlchemy & SQLAlchemy**: For Object-Relational Mapping (ORM), allowing interaction with the database using Python objects.
*   **Flask-Migrate & Alembic**: For managing database schema migrations. The `migrations/` directory contains the version history.
*   **Flask-Login**: Manages user sessions and authentication.
*   **Gunicorn**: The production-ready WSGI web server used to run the Flask application inside the Docker container.
*   **dotenv**: Manages environment variables from the `.env` file for local development.

### Frontend (HTML/CSS/JavaScript)

The frontend renders the user interface and handles user interactions in the browser.

*   **Templating**: The UI is rendered using the **Jinja2** templating engine. The `backend/templates/` directory contains all HTML templates, with `base.html` serving as the main layout.
*   **Styling**: The application uses a custom stylesheet (`backend/static/css/style.css`). **Flask-Assets** is used to bundle and minify CSS and JavaScript files for optimal performance.
*   **JavaScript**: `main.js` provides dynamic table features like client-side sorting, filtering, and inline editing. `data_export_ui.js` powers the interactive data export page.
*   **Libraries**: **Bootstrap 5** for its responsive grid and core components, and **FontAwesome** for icons.

### Database

*   **Database System**: **PostgreSQL** (version 15). The `docker-compose.yml` file defines a `db` service running the official `postgres:15-alpine` image.
*   **Data Persistence**: A Docker volume (`db_data`) is used to persist the PostgreSQL data across container restarts.
*   **Schema Management**: The database schema is defined in `backend/models.py` and managed through **Alembic** migrations located in the `migrations/versions/` directory.

### Containerization & Deployment

The entire application stack is containerized using **Docker** and orchestrated with **Docker Compose**.

*   **`docker-compose.yml`**: Defines the `db` and `backend` services and links them.
*   **`Dockerfile` (`backend/Dockerfile`)**: Specifies how to build the `backend` service image.
*   **`entrypoint.sh`**: Runs database migrations (`flask db upgrade`) before starting the Gunicorn server, ensuring the database schema is up-to-date.

---

## Local Development Setup

To run the application on your local machine, you will need Git, Docker, and Docker Compose installed.

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd PipelineIntelligence
    ```

2.  **Create Environment File**
    Create a `.env` file in the project root by copying the provided `.env` content. You can change `SECRET_KEY` for better security.
    ```env
    SECRET_KEY=a-very-secret-key-that-you-should-change
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=asset_tracker_db
    DATABASE_URL=postgresql://user:password@db:5432/asset_tracker_db
    ```

3.  **Build and Run with Docker Compose**
    From the project root, run the following command:
    ```sh
    docker-compose up --build
    ```
    This will build the Docker images, start the database and backend containers, and apply any pending database migrations.

4.  **Access the Application**
    Once the containers are running, you can access the application in your web browser at:
    [http://localhost:5001](http://localhost:5001)

5.  **First-Time Use**
    You will need to register a new user to log in and access the application features.

---

## Database Schema Overview

The application utilizes a PostgreSQL database. The schema is designed around a central **Product** entity, with several related entities describing its characteristics, challenges, and supply chain.

### 1. Products (`products`)

The core entity representing a pharmaceutical asset.

| Field Name                | Data Type                | Description                                                                 |
| :------------------------ | :----------------------- | :-------------------------------------------------------------------------- |
| `product_id`              | Integer                  | **Primary Key**.                                                            |
| `product_code`            | String(100)              | **Unique, Required**. The main business identifier for the product (e.g., "XYZ-001"). |
| `product_name`            | String(255)              | The common name of the product.                                             |
| `product_type`            | String(100)              | The type of product (e.g., "Monoclonal Antibody", "Small Molecule").        |
| `base_technology`         | String(255)              | The core technology platform used for the product.                          |
| `mechanism_of_action`     | Text                     | A description of how the product works.                                     |
| `dosage_form`             | String(255)              | The physical form of the drug (e.g., "Tablet", "Injectable").               |
| `therapeutic_area`        | String(255)              | The primary medical field for the product (e.g., "Oncology"). Indexed.      |
| `current_phase`           | String(100)              | The current clinical development phase (e.g., "Phase III"). Indexed.        |
| `project_status`          | String(100)              | The current status of the project (e.g., "Ongoing"). Indexed.               |
| `lead_indication`         | String(255)              | The primary indication the product is being developed for.                  |
| `expected_launch_year`    | Integer                  | The projected year of market launch.                                        |
| `lifecycle_indications`   | JSONB                    | A JSON field to store a list of potential future indications.               |
| `regulatory_designations` | JSONB                    | A JSON field for special regulatory statuses (e.g., "Fast Track").          |
| `manufacturing_strategy`  | String(100)              | The high-level strategy for manufacturing (e.g., "Internal", "CMO").        |
| `manufacturing_sites`     | JSONB                    | A JSON field to list the manufacturing sites.                               |
| `volume_forecast`         | JSONB                    | A JSON field to store forecasted production volumes.                        |
| `created_at` / `updated_at` | DateTime             | Timestamps for record creation and last update.                             |

### 2. Indications (`indications`)

Represents specific clinical indications for which a product is being developed.

| Field Name              | Data Type   | Description                                                           |
| :---------------------- | :---------- | :-------------------------------------------------------------------- |
| `indication_id`         | Integer     | **Primary Key**.                                                      |
| `product_id`            | Integer     | Foreign Key linking to `products.product_id`.                         |
| `indication_name`       | String(255) | **Required**. The name of the medical indication.                     |
| `therapeutic_area`      | String(255) | The medical field for this specific indication.                       |
| `development_phase`     | String(100) | The development phase for this specific indication.                   |
| `expected_launch_year`  | Integer     | The projected launch year for this indication.                        |

### 3. Manufacturing Challenges (`manufacturing_challenges`)

Defines specific challenges related to manufacturing.

| Field Name             | Data Type   | Description                                                           |
| :--------------------- | :---------- | :-------------------------------------------------------------------- |
| `challenge_id`         | Integer     | **Primary Key**.                                                      |
| `challenge_category`   | String(255) | **Required**. A high-level category for the challenge. Indexed.       |
| `challenge_name`       | String(255) | **Required, Unique**. The specific name of the challenge.             |
| `explanation`          | Text        | A detailed description of the challenge.                              |

### 4. Manufacturing Technologies (`manufacturing_technologies`)

Defines specific technologies used in the manufacturing process.

| Field Name        | Data Type   | Description                                              |
| :---------------- | :---------- | :------------------------------------------------------- |
| `technology_id`   | Integer     | **Primary Key**.                                         |
| `technology_name` | String(255) | **Required, Unique**. The name of the technology.        |
| `description`     | Text        | A detailed description of the technology.                |

### 5. Partners (`partners`)

Represents external partners, such as Contract Manufacturing Organizations (CMOs).

| Field Name       | Data Type   | Description                                              |
| :--------------- | :---------- | :------------------------------------------------------- |
| `partner_id`     | Integer     | **Primary Key**.                                         |
| `partner_name`   | String(255) | **Required, Unique**. The name of the partner company.   |
| `specialization` | Text        | A description of the partner's area of expertise.        |

### 6. Product Supply Chain (`product_supply_chain`)

Links products to internal sites or external partners for different manufacturing stages.

| Field Name           | Data Type   | Description                                                                 |
| :------------------- | :---------- | :-------------------------------------------------------------------------- |
| `id`                 | Integer     | **Primary Key**.                                                            |
| `product_id`         | Integer     | **Required**. Foreign Key linking to `products.product_id`.                 |
| `manufacturing_stage`| String(255) | **Required**. The stage of manufacturing (e.g., "Drug Substance", "API").   |
| `supply_model`       | String(100) | The model of supply (e.g., "Primary", "Secondary").                         |
| `partner_id`         | Integer     | Foreign Key linking to `partners.partner_id`. Used for external partners.   |
| `internal_site_name` | String(255) | The name of the internal manufacturing site.                                |

### 7. Association Tables

These tables manage the many-to-many relationships.

| Table Name                | Links                                                   | Purpose                                           |
| :------------------------ | :------------------------------------------------------ | :------------------------------------------------ |
| `product_to_challenge`    | `products` ↔ `manufacturing_challenges`                 | Associates products with the challenges they face.|
| `product_to_technology`   | `products` ↔ `manufacturing_technologies`               | Associates products with the technologies they use.|

### 8. System Tables (`users`, `llm_settings`)

Manages user authentication and settings.

| Table              | Field Name                     | Description                                           |
| :----------------- | :----------------------------- | :---------------------------------------------------- |
| **`users`**        | `id`, `username`, `password`   | Standard user authentication fields.                  |
| **`llm_settings`** | `id`, `user_id`, `*_api_key`   | Stores user-specific API keys for LLM providers (optional). |