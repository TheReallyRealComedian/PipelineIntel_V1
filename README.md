## Technical Architecture

UsecaseExplorer is a modern web application built on a Python/Flask backend and a dynamic, JavaScript-powered frontend. The entire application is containerized using Docker for consistent development and deployment.

### High-Level Overview

The architecture follows a standard client-server model, orchestrated by Docker Compose.

```
+----------------+      +--------------------------+      +---------------------+      +----------------+
|                |      |                          |      |                     |      |                |
|      User      +----->|     Web Browser          |      |   Backend (Flask)   |      |   LLM APIs     |
|                |      |  (HTML/CSS/JavaScript)   |<---->|  (Gunicorn Server)  |<---->| (OpenAI, etc.) |
+----------------+      |                          |      |                     |      |                |
                        +--------------------------+      +----------+----------+      +----------------+
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

The backend is the application's core, handling business logic, data persistence, and communication with external AI services. It is built using the **Flask** web framework.

The backend code is structured into three main layers:

1.  **Routes (`/backend/routes`)**: This layer handles incoming HTTP requests. It uses Flask Blueprints to organize functionality by domain (e.g., `usecase_routes.py`, `area_routes.py`). Routes are responsible for receiving requests, calling the appropriate service to handle the logic, and rendering a Jinja2 template or returning a JSON response.

2.  **Services (`/backend/services`)**: This is the business logic layer. It's decoupled from the web framework and contains the core application logic. For example, `llm_service.py` handles all interactions with different LLM providers, while `data_management_service.py` contains the complex logic for importing and exporting data. This separation makes the code more maintainable and testable.

3.  **Models (`/backend/models.py`)**: This is the data access layer. It uses the **SQLAlchemy ORM** to define the database schema as Python classes (`Area`, `ProcessStep`, `UseCase`, etc.). All database interactions from the services go through these models.

#### Key Libraries & Components:

*   **Flask**: The micro web framework that underpins the entire backend.
*   **Flask-SQLAlchemy & SQLAlchemy**: For Object-Relational Mapping (ORM), allowing interaction with the database using Python objects.
*   **Flask-Migrate & Alembic**: For managing database schema migrations. The `migrations/` directory contains the version history, allowing for controlled, repeatable updates to the database structure.
*   **Flask-Login**: Manages user sessions, authentication, and access control.
*   **Gunicorn**: The production-ready WSGI web server used to run the Flask application inside the Docker container.
*   **LLM SDKs**: The application integrates with multiple Large Language Model providers using their respective Python libraries (`openai`, `anthropic`, `google-generativeai`).
*   **dotenv**: Manages environment variables from the `.env` file for local development.

### Frontend (HTML/CSS/JavaScript)

The frontend is responsible for rendering the user interface and handling user interactions in the browser.

*   **Templating**: The UI is rendered using the **Jinja2** templating engine. The `backend/templates/` directory contains all HTML templates, with `base.html` serving as the main layout.
*   **Styling**: The application uses a custom stylesheet (`backend/static/css/style.css`) that follows the Boehringer Ingelheim brand style guide. **Flask-Assets** is used to bundle and minify CSS and JavaScript files for optimal performance, with bundled assets being output to the `backend/static/gen/` directory.
*   **JavaScript**: The frontend employs a modular JavaScript approach:
    *   **UI Modules (`/backend/static/js`)**: Specific files like `breadcrumb_ui.js`, `usecase_overview.js`, and `review_process_links_ui.js` handle the logic for different parts of the application, such as dynamic dropdowns, table filtering, and interactive modals.
    *   **Common Modules**: `common_llm_chat.js` provides a reusable interface for the AI chat functionality seen across different pages.
    *   **Main Entry Point**: `main.js` initializes all the necessary UI modules on page load.
*   **Libraries**: The frontend is built on **Bootstrap 5** for its responsive grid system and core components, and **FontAwesome** for icons.

### Database

*   **Database System**: The application is configured to use **PostgreSQL** (version 15). The `docker-compose.yml` file defines a `db` service that runs the official `postgres:15-alpine` image.
*   **Data Persistence**: A Docker volume (`db_data`) is used to persist the PostgreSQL data, ensuring that data is not lost when the container is stopped or restarted.
*   **Schema Management**: Database schema is defined in `backend/models.py` and managed through **Alembic** migrations located in the `migrations/versions/` directory.

### Containerization & Deployment

The entire application stack is containerized using **Docker** and orchestrated with **Docker Compose**, ensuring a consistent and reproducible environment.

*   **`docker-compose.yml`**: This file defines and links the two primary services:
    *   `db`: The PostgreSQL database container.
    *   `backend`: The Flask application container. It is configured to depend on the `db` service, ensuring the database is healthy before the backend starts.
*   **`Dockerfile` (`backend/Dockerfile`)**: This file specifies how to build the `backend` service image. It installs Python dependencies from `requirements.txt`, copies the application code, and sets `gunicorn` as the command to run the application.
*   **`entrypoint.sh`**: A shell script that runs when the `backend` container starts. It is responsible for running database migrations via Alembic (`flask db upgrade`) before starting the Gunicorn server, ensuring the database schema is up-to-date.
---

## Database Schema Overview

The application utilizes a PostgreSQL database, managed by SQLAlchemy and Alembic for migrations. The schema is designed around three core concepts: **Areas**, **Process Steps**, and **Use Cases**, with a flexible system for establishing relevance links and adding descriptive tags.

### 1. Areas (`areas`)

This table represents the highest-level business or functional domains in the organization.

| Field Name      | Data Type       | Description                                         |
| :-------------- | :-------------- | :-------------------------------------------------- |
| `id`            | Integer         | Primary Key.                                        |
| `name`          | String(255)     | The unique name of the area (e.g., "Logistics").    |
| `description`   | Text            | A detailed description of the area's scope.         |
| `created_at`    | DateTime        | Timestamp of when the area was created.             |

### 2. Process Steps (`process_steps`)

These are the individual processes or "Process Target Pictures" (PTPs) that exist within an **Area**.

| Field Name                  | Data Type       | Description                                                           |
| :-------------------------- | :-------------- | :-------------------------------------------------------------------- |
| `id`                        | Integer         | Primary Key.                                                          |
| `bi_id`                     | String(255)     | A unique Business ID for the step (e.g., "MFG-001").                  |
| `name`                      | String(255)     | The descriptive name of the process step.                             |
| `area_id`                   | Integer         | Foreign Key linking to the parent `areas.id`.                         |
| `step_description`          | Text            | A short, high-level description of the step.                          |
| `vision_statement`          | Text            | The future vision or goal for this process.                           |
| `what_is_actually_done`     | Text            | A description of the current state or "as-is" process.                |
| `in_scope`                  | Text            | Defines what is included within this process step.                    |
| `out_of_scope`              | Text            | Defines what is explicitly excluded from this process step.           |
| `pain_points`               | Text            | Known issues, challenges, or inefficiencies in the current process.   |
| `interfaces_text`           | Text            | Description of interactions with other systems or processes.          |
| `targets_text`              | Text            | Specific goals and objectives for this process.                       |
| `summary`                   | Text            | A generic, often AI-generated, summary of the step.                   |
| `raw_content`               | Text            | Unstructured, raw text or notes about the process step.               |
| `llm_comment_1` to `_5`     | Text            | Five fields for storing comments or analyses, often from LLMs.        |
| `created_at` / `updated_at` | DateTime        | Timestamps for creation and last update.                              |

### 3. Use Cases (`use_cases`)

These represent specific, actionable ideas or projects that are direct children of a **Process Step**.

| Field Name                      | Data Type       | Description                                                            |
| :------------------------------ | :-------------- | :--------------------------------------------------------------------- |
| `id`                            | Integer         | Primary Key.                                                           |
| `bi_id`                         | String(255)     | A unique Business ID for the use case (e.g., "UC-001").                |
| `name`                          | String(255)     | The descriptive name of the use case.                                  |
| `process_step_id`               | Integer         | Foreign Key linking to the parent `process_steps.id`.                  |
| `priority`                      | Integer         | Priority score (1-4). Mapped to High, Medium, Low.                     |
| `wave`                          | String(255)     | A project wave or grouping identifier (e.g., "Wave 1", "2024").        |
| `status`                        | String(255)     | Current status (e.g., "Ideated", "Ongoing", "Completed").              |
| `effort_level`                  | String(255)     | Estimated effort (e.g., "Low", "Medium", "High").                      |
| `usecase_type_category`         | String(255)     | Use Case category (e.g., "Strategic", "Improvement", "Fundamental").   |
| `business_problem_solved`       | Text            | The "as-is" situation and business need this use case addresses.       |
| `target_solution_description`   | Text            | The proposed "to-be" state or solution description.                    |
| `technologies_text`             | Text            | Comma-separated list of technologies involved.                         |
| `requirements`                  | Text            | Specific requirements for implementation.                              |
| `dependencies_text`             | Text            | Redundancies and dependencies on other projects, systems, or teams.    |
| `effort_quantification`         | Text            | A detailed description of the effort involved (costs, time).           |
| `potential_quantification`      | Text            | A detailed description of the potential benefits.                      |
| `contact_persons_text`          | Text            | Key contacts for this use case.                                        |
| `related_projects_text`         | Text            | Links or mentions of other related projects.                           |
| `pilot_site_factory_text`       | Text            | The designated pilot site or factory for implementation.               |
| `reduction_time_transfer`       | String(255)     | Estimated time reduction for product transfer.                         |
| `reduction_time_launches`       | String(255)     | Estimated time reduction for product launches.                         |
| `reduction_costs_supply`        | String(255)     | Estimated cost reduction in the supply chain.                          |
| `quality_improvement_quant`     | String(255)     | Estimated quality improvement.                                         |
| `summary`                       | Text            | A high-level summary of the use case.                                  |
| `inspiration`                   | Text            | The source of inspiration or original idea.                            |
| `ideation_notes`                | Text            | Original notes from the ideation phase.                                |
| `further_ideas`                 | Text            | Additional ideas or inputs.                                            |
| `raw_content`                   | Text            | Unstructured, raw text or notes about the use case.                    |
| `relevants_text`                | Text            | Legacy field for free-text tags.                                       |
| `llm_comment_1` to `_5`         | Text            | Five fields for storing comments or analyses, often from LLMs.         |
| `created_at` / `updated_at`     | DateTime        | Timestamps for creation and last update.                               |

### 4. Tags (`tags` & `usecase_tag_association`)

A flexible tagging system for `Use Cases` to categorize them by IT systems, data types, or general keywords.

| Table                 | Field Name | Data Type    | Description                                                     |
| :-------------------- | :--------- | :----------- | :-------------------------------------------------------------- |
| **`tags`**            | `id`       | Integer      | Primary Key.                                                    |
|                       | `name`     | String(255)  | The name of the tag (e.g., "SAP", "Batch Records").             |
|                       | `category` | String(50)   | The type of tag (e.g., `it_system`, `data_type`, `tag`).        |
| **`usecase_tag_...`** | `usecase_id` | Integer    | Foreign Key to `use_cases.id`.                                  |
|                       | `tag_id`   | Integer      | Foreign Key to `tags.id`.                                       |

### 5. Users & Settings (`users`, `llm_settings`)

Manages user authentication and user-specific settings for Large Language Model (LLM) providers.

| Table              | Field Name                     | Data Type    | Description                                                         |
| :----------------- | :----------------------------- | :----------- | :------------------------------------------------------------------ |
| **`users`**        | `id`                           | Integer      | Primary Key.                                                        |
|                    | `username`                     | String(80)   | Unique username for login.                                          |
|                    | `password`                     | String(255)  | Hashed user password.                                               |
|                    | `system_prompt`                | Text         | User's custom system prompt for the general AI chat.                |
|                    | `step_summary_system_prompt`   | Text         | User's custom system prompt for the "Summarize Step" AI feature.    |
| **`llm_settings`** | `id`                           | Integer      | Primary Key.                                                        |
|                    | `user_id`                      | Integer      | Foreign Key to `users.id`.                                          |
|                    | `openai_api_key`               | String(255)  | User-specific OpenAI API key.                                       |
|                    | `anthropic_api_key`            | String(255)  | User-specific Anthropic API key.                                    |
|                    | `google_api_key`               | String(255)  | User-specific Google API key.                                       |
|                    | `ollama_base_url`              | String(255)  | URL for a self-hosted Ollama instance.                              |
|                    | `apollo_client_id`             | String(255)  | User-specific Apollo (BI Internal) Client ID.                       |
|                    | `apollo_client_secret`         | String(255)  | User-specific Apollo (BI Internal) Client Secret.                   |

### 6. Relevance Link Tables

These four tables establish scored relevance connections between the core entities. They all share a similar structure.

| Table                                 | Source                   | Target               | Description                                           |
| :------------------------------------ | :----------------------- | :------------------- | :---------------------------------------------------- |
| `usecase_area_relevance`              | `use_cases.id`           | `areas.id`           | Links a Use Case to a relevant Area.                  |
| `usecase_step_relevance`              | `use_cases.id`           | `process_steps.id`   | Links a Use Case to a relevant Process Step.          |
| `usecase_usecase_relevance`           | `use_cases.id` (source)  | `use_cases.id` (target)| Links a Use Case to another relevant Use Case.        |
| `process_step_process_step_relevance` | `process_steps.id` (source) | `process_steps.id` (target) | Links a Process Step to another relevant Process Step.|

**Common Fields in all Relevance Tables:**

| Field Name          | Data Type | Description                                                        |
| :------------------ | :-------- | :----------------------------------------------------------------- |
| `id`                | Integer   | Primary Key.                                                       |
| `source_*_id`       | Integer   | Foreign Key to the source entity's ID.                             |
| `target_*_id`       | Integer   | Foreign Key to the target entity's ID.                             |
| `relevance_score`   | Integer   | A score from 0 to 100 indicating the strength of the connection.   |
| `relevance_content` | Text      | A description or justification for the relevance link.             |
| `created_at` / `updated_at` | DateTime | Timestamps for creation and last update.                     |