# FITS 👕🧥👗  

FITS is a web app designed to digitize and organize your wardrobe, making outfit planning seamless and efficient. Users can upload and categorize clothing items, mix and match outfits, and easily keep track of their closet—all in one place.

---

## 📚 Table of Contents

- [Features](#-features)
- [Setup Instructions](#️-setup-instructions-maclinux)
- [Database Initialization](#database-initialization)
- [Running the App](#running-the-app)
- [CAS Login Notes](#cas-login-notes)
- [External Data](#external-data)

---

## 🧰 Features

- Secure Yale CAS login
- Upload clothing items with automatic background removal
- Search by brand, size, type, color, and fabric
- Save and view custom outfits
- Add friends and view their saved outfits
- PostgreSQL database integration

---

## ⚙️ Setup Instructions (Mac/Linux)

1. Clone the Repository
```bash
    git clone <your-repo-url>
    cd <your-project-directory>
```
2. Create and Activate Virtual Environment

    python3 -m venv .venv
    source .venv/bin/activate

3. Install Dependencies

    pip install -r requirements.txt

    If you encounter errors related to image libraries (like rembg), install:

    brew install libjpeg libpng

4. Set Up the Environment Variables

    Create a `.env` file in the root directory with the following content:

    user="your_postgres_user"
    password="your_postgres_password"
    host="your_postgres_host"
    port="5432"
    dbname="your_postgres_db"
    SECRET_KEY=your_flask_secret_key

    (Do not commit this file.)

---

## Database Initialization:

The app requires default values for tables like brands, sizes, colors, and fabrics. These are defined in default_values.py.

To initialize:

    from database import init_all_default_values
    from default_values import default_tables

    init_all_default_values(default_tables)

Ensure your PostgreSQL server is running and tables are created beforehand.

---

## Running the App:

    python runserver.py 8000

Visit in your browser:

    http://127.0.0.1:8000

---

## CAS Login Notes:

This app uses Yale CAS authentication.

---

## External Data:

All required data (brands, sizes, colors, etc.) is stored in the database and initialized via default_values.py. No external dataset is needed.
