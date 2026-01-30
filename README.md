How to Run the Project (Flask – University Housing System)
=========================================================
Youtube link for demo: https://youtu.be/dPBpuGtpCxU

This project is a Flask-based prototype for ASE Assignment 6.
The TA can run it either after cloning from GitHub or from a downloaded ZIP.


Prerequisites
-------------
- Python 3.9+ (tested with Python 3.10)
- Git (only if cloning from GitHub)
- Windows / macOS / Linux
- Internet connection (for installing dependencies)


1. Clone the Repository (TA workflow)
------------------------------------
If using Git:

git clone <YOUR_GITHUB_REPO_URL>
cd ase25-assignment06

If a ZIP file is provided instead:
- Unzip the file
- Open a terminal in the unzipped folder
- cd into the project directory


2. Create and Activate Virtual Environment
------------------------------------------

Windows (PowerShell):

python -m venv venv
.\venv\Scripts\activate

macOS / Linux:

python3 -m venv venv
source venv/bin/activate


3. Install Dependencies
-----------------------
Make sure the file name is exactly: requirements.txt

pip install -r requirements.txt


4. Run the Flask Application
----------------------------
You can start the app in either of the following ways:

flask run

or

python app.py

The application will start at:
http://127.0.0.1:5000


5. Application Access
---------------------

Student Flow
------------
Open:
http://127.0.0.1:5000/register

Register using a university email address, for example:
anything@uni-bayreuth.de

Email verification is simulated:
- Open the Demo Inbox shown in the UI
- Get verification code and click verify button.
- Complete registration

After login, students can use:
- Rooms
- Events
- Event requests
- Info pages (rules, facilities, contacts)


6. Admin Login (IMPORTANT)
-------------------------
The admin account is predefined.

ADMIN_EMAIL    = admin@uni-bayreuth.de
ADMIN_PASSWORD = admin123

Login via:
http://127.0.0.1:5000/login


Admin Capabilities
------------------
- View and manage event requests
- Filter requests: Pending / Accepted / Rejected
- Accept or reject requests with comments
- View students per room
- View students per event
- Open / close room registration
- Full admin dashboard (not visible to students)

All admin features are protected by backend role checks.


7. Notes for TA / Evaluation
----------------------------
- Email verification is mocked via Demo Inbox (no real email service)
- Role-based access control:
  - Students cannot access admin routes
  - Admin-only data is protected on the backend
- Database:
  - SQLite
  - Auto-created on first run
- Seed data includes:
  - Rooms
  - Events
  - Info pages (rules, facilities, contacts)


8. Resetting the Database (Optional)
-----------------------------------
To start with a clean state:

1. Stop the Flask server
2. Delete the SQLite database file
   (located in the instance/ folder or project root)
3. Restart the application

The database will be re-created and seeded automatically.


Troubleshooting
---------------
- Package installation fails:
  → Verify Python version (3.9+)
- The application run using pycharm while production.

