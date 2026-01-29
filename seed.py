# seed.py
from datetime import datetime, timezone
import auth


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _make_password_hash(password: str) -> str:
    """
    Build password_hash in the SAME format your auth.login() expects.
    Stored format is: "salt$sha256(salt + password)"
    We reuse auth._make_password_hash() to guarantee it matches login().
    """
    return auth._make_password_hash(password)



def seed_if_empty(db):
    # -------------------------
    # Rooms
    # -------------------------
    c = db.execute("SELECT COUNT(*) AS n FROM rooms").fetchone()["n"]
    if int(c) == 0:
        rooms = [
            ("single", "Single Room A", "Private room, quiet.", 320, 1, 1),
            ("shared", "Shared Room B", "Shared room for 2 students.", 220, 2, 1),
            ("studio", "Studio C", "Studio with kitchenette.", 450, 1, 1),
            ("shared", "Shared Room D", "Shared room for 3 students.", 180, 3, 1),
        ]
        db.executemany(
            "INSERT INTO rooms (type, title, description, price_eur, capacity, available) VALUES (?, ?, ?, ?, ?, ?)",
            rooms,
        )

    # -------------------------
    # Info pages (UPSERT by slug)
    # This ensures new pages are added even if table is not empty.
    # -------------------------
    pages = [
        ("arrival", "Arrival & Living Information",
         "WELCOME TO UNIVERSITY HOUSING\n\n"
         "This page provides essential information for students arriving at the university and living in university housing.\n\n"
         "RULES\n"
         "• No smoking inside rooms or buildings\n"
         "• Quiet hours: 22:00 – 07:00\n"
         "• Keep shared kitchens and bathrooms clean\n"
         "• Guests only during the day (no overnight stays)\n"
         "• Follow fire safety rules at all times\n"
         "• Damage to rooms/facilities may result in extra costs\n\n"
         "FACILITIES\n"
         "• Furnished rooms (bed, desk, chair, wardrobe)\n"
         "• Shared kitchens (depending on room type)\n"
         "• Laundry room (washing machines & dryers)\n"
         "• Study rooms and common areas\n"
         "• Bicycle storage\n"
         "• Waste separation & recycling points\n"
         "• 24/7 building access for residents\n\n"
         "SERVICES\n"
         "• Housing administration support\n"
         "• Maintenance and repair service\n"
         "• Internet access in all rooms\n"
         "• Orientation and social events\n"
         "• Emergency support coordination\n\n"
         "CONTACTS\n"
         "• Housing Office: housing@uni-bayreuth.de\n"
         "• Emergency: 112\n\n"
         "IMPORTANT NOTES\n"
         "• Room changes depend on admin settings\n"
         "• Keep your university email active for official communication\n"
         "• Check official announcements for updates\n"
        ),

        ("rules", "Dorm Rules",
         "• No smoking.\n"
         "• Quiet hours after 22:00.\n"
         "• Keep shared spaces clean.\n"
         "• Respect other residents.\n"
         "• Follow fire safety instructions.\n"),

        ("facilities", "Facilities",
         "• Laundry room.\n"
         "• Study room.\n"
         "• Bike storage.\n"
         "• 24/7 security.\n"
         "• Common area / lounge.\n"),

        ("services", "Services",
         "• Housing office support.\n"
         "• Maintenance & repairs.\n"
         "• Internet/Wi-Fi access.\n"
         "• Orientation and dorm events.\n"
         "• Lost & found / front desk help (if available).\n"),

        ("contacts", "Contacts",
         "Housing office: housing@uni-bayreuth.de\n"
         "Emergency: 112\n"
         "Non-emergency (campus/security if applicable): ask housing office.\n"),
    ]

    for slug, title, content in pages:
        db.execute(
            """
            INSERT INTO info_pages (slug, title, content)
            VALUES (?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
              title = excluded.title,
              content = excluded.content
            """,
            (slug, title, content),
        )

    # -------------------------
    # Events
    # -------------------------
    c = db.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
    if int(c) == 0:
        now = _now_iso()
        events = [
            ("Welcome Meetup", "orientation", "2026-02-01T18:00", "Main Hall", "Meet other students.", 50, "admin@uni-bayreuth.de", now),
            ("Study Group: CS", "study_group", "2026-02-03T16:00", "Library", "Weekly CS study group.", None, "admin@uni-bayreuth.de", now),
            ("Board Games Night", "social", "2026-02-05T19:00", "Common Room", "Bring your own games.", 20, "admin@uni-bayreuth.de", now),
        ]
        db.executemany(
            """
            INSERT INTO events (title, category, date_time, location, description, quota, created_by_email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            events,
        )

    # -------------------------
    # Admin user
    # -------------------------
    ADMIN_EMAIL = "admin@uni-bayreuth.de"
    ADMIN_PASSWORD = "admin123"

    u = db.execute("SELECT 1 FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
    if not u:
        pw_hash = _make_password_hash(ADMIN_PASSWORD)
        db.execute(
            """
            INSERT INTO users (email, password_hash, role, created_at)
            VALUES (?, ?, 'admin', ?)
            """,
            (ADMIN_EMAIL, pw_hash, _now_iso()),
        )

    db.commit()
