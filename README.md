# Shopping Cart EDA Project

**Live demo:** https://ecommerce-shopping-eda-klwya92pj9yhf3vrh4kupn.streamlit.app

A multi-page Streamlit application for exploring and reporting on e-commerce shopping cart data: customers, products, orders, and sales. The app combines exploratory data analysis (EDA), marketing and KPI dashboards, and a voice-driven data assistant powered by the Google Gemini API.

## Features

| Page | Description |
|---|---|
| **Home** | Landing page with a full data preview and an auto-generated data dictionary describing every column. |
| **Univariate Analysis** | Distribution analysis of numerical and categorical fields (age, price, quantity, product type, gender, etc.). |
| **Dashboard KPIs** | Core business metrics — total customers, total orders, total revenue, and average order value. |
| **Marketing Report** | Sales and marketing insights broken down by time period, geography, and product category. |
| **Voice Interface** | Conversational assistant that answers questions about the dataset using natural speech, built on the Gemini API. |

## Findings

Snapshot of the live app and the key numbers it surfaces from the dataset (Jan 2021 – Oct 2021):

- **616** unique customers placed **993** orders, for **$1,031,800** in total revenue and an average order value of **$1,039.07**.
- Order volume is fairly evenly spread across Australian states, led by South Australia and Queensland (140 orders each), with the rest of the states/territories in the 100–130 range.
- Daily revenue is highly variable (spikes up to ~$10k vs. a baseline of $2k–$4k), while monthly revenue trends upward over the year with peaks in March and July.
- The flattened dataset joins all four tables (customer, order, product, sale) into one row per sale line item, which is what powers the Marketing Report's filters (state, date range, product count).

| Home | Dashboard KPIs | Marketing Report |
|---|---|---|
| ![Home page](assets/home.jpg) | ![Dashboard KPIs page](assets/dashboard_kpis.jpg) | ![Marketing Report page](assets/marketing_report.jpg) |

## Tech Stack

- **Framework:** [Streamlit](https://streamlit.io/)
- **Data processing:** pandas, NumPy
- **Visualization:** Plotly Express / Plotly Graph Objects
- **Voice / AI assistant:** Google Gemini (`google-genai`)
- **Storage:** MySQL (source schema), Parquet/CSV (processed data used by the app)

See [requirements.txt](requirements.txt) for pinned package versions.

## Project Structure

```
.
├── Home.py                     # Landing page + data dictionary
├── pages/
│   ├── Univariate Analysis.py  # Distribution charts
│   ├── Dashboard KPIs.py       # KPI summary cards
│   ├── Marketing Report.py     # Marketing/sales breakdowns
│   └── Voice Interface.py      # Gemini-powered voice Q&A
├── store_database.sql          # MySQL schema + seed data (source of truth)
├── cleaned_data.csv            # Flattened, cleaned dataset (CSV)
├── cleaned_data.parquet        # Flattened, cleaned dataset (Parquet, used by the app)
├── EDA steps.ipynb             # Exploratory notebook
├── Shopping Cart EDA.ipynb     # EDA notebook
└── requirements.txt
```

## Getting Started

1. Create and activate an environment with Python 3.12.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional, for the Voice Interface page) Add your Gemini API key to a `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```
4. Run the app:
   ```bash
   streamlit run Home.py
   ```

## Database Schema

The source data is modeled as a relational MySQL database (`store_db`) with four tables: `customers`, `products`, `orders`, and `sales`. Orders belong to customers, and each order can contain multiple sale line items, each referencing a product.

### Entity-Relationship Diagram

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    ORDERS ||--o{ SALES : contains
    PRODUCTS ||--o{ SALES : "sold in"

    CUSTOMERS {
        int customer_id PK
        varchar customer_name
        varchar gender
        tinyint age
        varchar home_address
        varchar zip_code
        varchar city
        varchar state
        varchar country
    }

    ORDERS {
        int order_id PK
        int customer_id FK
        date order_date
        date delivery_date
    }

    PRODUCTS {
        int product_id PK
        varchar product_type
        varchar product_name
        varchar size
        varchar colour
        int quantity
        varchar description
    }

    SALES {
        int sales_id PK
        int order_id FK
        int product_id FK
        decimal price_per_unit
        int quantity
        decimal total_price
    }
```

### Table Reference

**customers**
| Column | Type | Notes |
|---|---|---|
| customer_id | INT | Primary key |
| customer_name | VARCHAR(100) | |
| gender | VARCHAR(30) | |
| age | TINYINT UNSIGNED | |
| home_address | VARCHAR(150) | |
| zip_code | VARCHAR(10) | |
| city | VARCHAR(100) | |
| state | VARCHAR(100) | |
| country | VARCHAR(100) | |

**products**
| Column | Type | Notes |
|---|---|---|
| product_id | INT | Primary key |
| product_type | VARCHAR(50) | e.g. Shirt |
| product_name | VARCHAR(100) | |
| size | VARCHAR(10) | |
| colour | VARCHAR(30) | |
| quantity | INT | Stock quantity |
| description | VARCHAR(255) | |

**orders**
| Column | Type | Notes |
|---|---|---|
| order_id | INT | Primary key |
| customer_id | INT | Foreign key → customers.customer_id |
| order_date | DATE | |
| delivery_date | DATE | |

**sales**
| Column | Type | Notes |
|---|---|---|
| sales_id | INT | Primary key |
| order_id | INT | Foreign key → orders.order_id |
| product_id | INT | Foreign key → products.product_id |
| price_per_unit | DECIMAL(10,2) | |
| quantity | INT | Units sold in this line item |
| total_price | DECIMAL(10,2) | price_per_unit × quantity |

For the app, these four tables are joined and flattened into a single analysis-ready table stored as `cleaned_data.csv` / `cleaned_data.parquet`.

## Data Rebuild (optional)

To recreate the source MySQL database from scratch:

```bash
mysql -u <user> -p < store_database.sql
```

This drops and recreates the `store_db` database and repopulates all four tables from the original data.
