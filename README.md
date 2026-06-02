# E-Commerce Server API (Django REST Framework)

This repository contains the backend server for the E-Commerce platform, built using Python, Django, and Django REST Framework (DRF). It provides a secure, scalable, and highly performant RESTful API for managing user accounts, product catalogs, shopping carts, orders, manual payments, reviews, and customer inquiries.

---

## 🚀 Key Features

The server is structured modularly with custom applications under the `apps/` directory:

### 1. User Accounts (`apps.accounts`)
- **Authentication**: JWT-based stateless authentication (SimpleJWT) and Google OAuth2 integration.
- **Security**: Account registration with email OTP verification, password reset workflows (forgot password), and secure logout with token blacklisting.
- **Profiles**: User profile management with roles (e.g., standard users and administrators).

### 2. Product Catalog (`apps.product`)
- **Categories**: Dynamic category hierarchy.
- **Products**: Detailed catalog listing with SEO-friendly slug support.
- **Attributes**: Product variants (size, color, etc.) and real-time stock management.
- **Media**: Multiple image uploads per product.

### 3. Cart & Order Management (`apps.orders`)
- **Cart**: Session/database-backed shopping cart (add, update quantity, delete items, clear cart).
- **Wishlist**: Add to wishlist and easily move items to the cart.
- **Checkout**: Seamless checkout workflow converting cart items into orders.
- **Orders**: Tracking order details, cancellation, and admin-led order status updates.

### 4. Payments & Reviews (`apps.payments`)
- **Payments**: Manual payment transaction logging and submission for verification.
- **Admin Moderation**: Administrative panels to approve or reject manual payments.
- **Ratings & Reviews**: Customer feedback system allowing users to rate and review products, with admin moderation controls.

### 5. Contact & Inquiries (`apps.contact`)
- **Contact Form**: Public API for contact submissions.
- **Admin Dashboard**: Admin tools to list, read, and reply to user inquiries via email.

---

## 🛠️ Technology Stack

- **Framework**: Django & Django REST Framework (DRF)
- **Database**: SQLite (Development) / PostgreSQL-ready (`psycopg2-binary` dependency included)
- **Authentication**: JWT (JSON Web Tokens) & Google OAuth
- **Configurations**: `django-environ` for managing `.env` environment variables
- **File Serving**: WhiteNoise for static files and Pillow for media uploads
- **API Styling**: Standard RESTful design with standard pagination and exception handlers

---

## ⚙️ Getting Started

Follow these steps to run the server locally:

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Setup Virtual Environment
Clone the repository and navigate to the server folder:
```bash
cd "E - Commerce/server"
```
Create a virtual environment:
```bash
python -m venv venv
```
Activate the virtual environment:
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file inside the `server/server/` directory and configure the following variables:
```env
DEBUG=True
SECRET_KEY=your_django_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
BACKEND_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:5173

# Email Configurations
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Google OAuth (If using)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/accounts/auth/google-callback/
```

### 5. Run Migrations & Start Server
Apply database migrations:
```bash
python manage.py migrate
```
Start the development server:
```bash
python manage.py runserver
```
The server will start running at `http://127.0.0.1:8000/`.

---

## 📋 API Endpoints Map

### Accounts (`/api/v1/accounts/`)
| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/register/` | POST | Register a new user | No |
| `/otp-verify/` | POST | Verify OTP for registration | No |
| `/otp-resend/` | POST | Resend OTP code | No |
| `/login/` | POST | User login (returns JWT tokens) | No |
| `/logout/` | POST | Blacklist tokens & logout | Yes |
| `/token/refresh/` | POST | Refresh expired access token | No |
| `/profile/` | GET/PUT/PATCH | Retrieve/Update user profile | Yes |
| `/auth/google-login/` | GET | Initiate Google OAuth flow | No |

### Products (`/api/v1/product/`)
| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/categories/` | GET/POST | List/Create categories | Admin for POST |
| `/products/` | GET/POST | List/Create products | Admin for POST |
| `/products/<slug>/` | GET | Retrieve product details | No |
| `/products/<id>/edit/` | PUT/PATCH/DELETE | Update or delete product | Admin |

### Cart & Orders (`/api/v1/orders/`)
| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/cart/` | GET | View user shopping cart | Yes |
| `/cart/add/` | POST | Add items to cart | Yes |
| `/wishlist/` | GET/POST | View/Add items to wishlist | Yes |
| `/checkout/` | POST | Process order checkout | Yes |
| `/orders/` | GET | List user's orders | Yes |

### Payments & Reviews (`/api/v1/payments/`)
| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/manual/` | POST | Submit manual payment | Yes |
| `/admin/manual/<id>/approve/` | POST | Approve manual payment | Admin |
| `/reviews/` | POST | Write product review | Yes |

### Contact (`/api/v1/contact/`)
| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/submit/` | POST | Submit public contact inquiry | No |
| `/admin/` | GET | List submitted inquiries | Admin |
