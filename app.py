# app.py
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import app as app
from flask import Flask, jsonify, request, abort, render_template, redirect, session


from db import close_db, get_db, get_db_path, init_db
from dto import RoomDto, EventDto, InfoPageDto
from seed import seed_if_empty
import auth


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
def _session_email() -> str:
    return (session.get("email") or "").strip().lower()

def _session_role() -> str:
    return (session.get("role") or "").strip().lower()


def _ensure_db(app: Flask):
    if not os.path.exists(get_db_path(app)):
        init_db(app)

    db = sqlite3.connect(get_db_path(app))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    seed_if_empty(db)
    db.close()


def _user_row(db, email: str):
    return db.execute("SELECT email, role FROM users WHERE email = ?", (email,)).fetchone()


def _require_student(db, _ignored_email_param=None) -> Optional[str]:
    email = _session_email()
    role = _session_role()

    if not email:
        return "Not logged in."
    if not auth.is_allowed_email(email):
        return "Only @uni-bayreuth.de emails are allowed."
    u = _user_row(db, email)
    if not u:
        return "User not found."
    if role != "student" or u["role"] != "student":
        return "Only students can perform this action."
    return None



def _require_admin(db, _ignored_email_param=None) -> Optional[str]:
    email = _session_email()
    role = _session_role()

    if not email:
        return "Not logged in."
    u = _user_row(db, email)
    if not u:
        return "User not found."
    if role != "admin" or u["role"] != "admin":
        return "Admin only."
    return None



def _room_dto_from_row(row) -> RoomDto:
    booked = int(row["booked_count"])
    capacity = int(row["capacity"])
    remaining = max(0, capacity - booked)
    is_full = remaining == 0

    return RoomDto(
        id=int(row["id"]),
        type=row["type"],
        title=row["title"],
        description=row["description"],
        price_eur=int(row["price_eur"]),
        capacity=capacity,
        available=bool(row["available"]),
        booked_count=booked,
        remaining=remaining,
        is_full=is_full,
    )



def _event_dto_from_row(row) -> EventDto:
    registered = int(row["registered_count"])
    quota = row["quota"]
    quota_val = None if quota is None else int(quota)

    if quota_val is None:
        remaining = None
        is_full = False
    else:
        remaining = max(0, quota_val - registered)
        is_full = remaining == 0

    return EventDto(
        id=int(row["id"]),
        title=row["title"],
        category=row["category"],
        date_time=row["date_time"],
        location=row["location"],
        description=row["description"],
        quota=quota_val,
        registered_count=registered,
        remaining=remaining,
        is_full=is_full,
    )


def _info_dto(row) -> InfoPageDto:
    return InfoPageDto(
        id=int(row["id"]),
        slug=row["slug"],
        title=row["title"],
        content=row["content"],
    )


def _get_setting(db, key: str, default: str = "0") -> str:
    row = db.execute("SELECT value FROM admin_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.teardown_appcontext(close_db)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    with app.app_context():
        _ensure_db(app)

    # ---------------- Pages ----------------
    @app.get("/")
    def root_redirect():
        return redirect("/login")

    @app.get("/login")
    def login_page():
        return render_template("login.html")

    @app.get("/register")
    def register_page():
        return render_template("register.html")

    @app.get("/verify")
    def verify_page():
        return render_template("verify.html")

    @app.get("/demo-inbox")
    def demo_inbox_page():
        return render_template("demo_inbox.html")

    @app.get("/rooms")
    def rooms_page():
        return render_template("rooms.html")

    @app.get("/events")
    def events_page():
        return render_template("events.html")

    @app.get("/admin")
    def admin_page():
        return render_template("admin.html")

    @app.get("/info/<slug>")
    def info_page(slug):
        return render_template("info.html", slug=slug)

    @app.post("/api/auth/register")
    def api_register():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not auth.is_allowed_email(email):
            return jsonify({"error": "Only @uni-bayreuth.de emails allowed"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        db = get_db(app)
        try:
            code, retry_in = auth.start_registration(db, email, password)
        except ValueError as e:
            if str(e) == "USER_ALREADY_EXISTS":
                return jsonify({"error": "User already exists. Please login."}), 400
            return jsonify({"error": "Registration failed"}), 400

        if code == "":
            return jsonify({"error": "Please wait before requesting a new code.", "retry_in_seconds": retry_in}), 429

        return jsonify({
            "message": "Verification created. Open /demo-inbox and click Verify (demo).",
            "cooldown_seconds": retry_in
        }), 200



    def _require_logged_in() -> Optional[str]:
        if not _session_email():
            return "Not logged in."
        return None

    @app.post("/api/auth/resend")
    def api_resend():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()

        if not auth.is_allowed_email(email):
            return jsonify({"error": "Only @uni-bayreuth.de emails allowed"}), 400

        db = get_db(app)
        try:
            code, retry_in = auth.resend_code(db, email)
        except ValueError as e:
            if str(e) == "USER_ALREADY_EXISTS":
                return jsonify({"error": "User already exists. Please login."}), 400
            if str(e) == "NO_PENDING_REGISTRATION":
                return jsonify({"error": "No pending registration. Please register first."}), 400
            return jsonify({"error": "Resend failed"}), 400

        if code == "":
            return jsonify({"error": "Please wait before resending.", "retry_in_seconds": retry_in}), 429

        return jsonify({
            "message": "Verification re-generated. Open /demo-inbox and click Verify (demo).",
            "cooldown_seconds": retry_in
        }), 200

    @app.post("/api/auth/verify")
    def api_verify():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        code = (data.get("code") or "").strip()

        if not auth.is_allowed_email(email):
            return jsonify({"error": "Invalid email domain"}), 400
        if not code:
            return jsonify({"error": "Code is required"}), 400

        db = get_db(app)
        ok = auth.verify_code_and_create_user(db, email, code)
        if not ok:
            return jsonify({"error": "Wrong code. Try again."}), 400

        return jsonify({"message": "Verified. You can now login."})

    @app.post("/api/auth/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not auth.is_allowed_email(email):
            return jsonify({"error": "Invalid email domain"}), 400

        db = get_db(app)
        ok, role = auth.login(db, email, password)
        if not ok:
            return jsonify({"error": "Invalid email or password"}), 401

        # set session
        session["email"] = email
        session["role"] = role

        return jsonify({"message": "Login successful", "email": email, "role": role})

    @app.post("/api/auth/logout")
    def api_logout():
        session.clear()
        return jsonify({"message": "Logged out"})

    @app.get("/api/demo/verification-status")
    def api_demo_verification_status():
        email = (request.args.get("email") or "").strip().lower()
        if not email:
            return jsonify({"error": "email is required"}), 400

        db = get_db(app)
        row = db.execute(
            """
            SELECT email, created_at, last_sent_at
            FROM email_verifications
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

        if not row:
            return jsonify({"error": "No pending verification for this email"}), 404

        return jsonify({
            "email": row["email"],
            "created_at": row["created_at"],
            "last_sent_at": row["last_sent_at"],
        })

    @app.post("/api/demo/verify")
    def api_demo_verify():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        if not email:
            return jsonify({"error": "email is required"}), 400

        if not auth.is_allowed_email(email):
            return jsonify({"error": "Only @uni-bayreuth.de emails allowed"}), 400

        # Never allow admin emails through demo verification
        # (optional but safest)
        if email.endswith("@uni-bayreuth.de") and email.startswith("demo.admin"):
            return jsonify({"error": "Admin accounts cannot be verified via demo flow."}), 403

        db = get_db(app)

        pending = db.execute(
            "SELECT password_hash FROM email_verifications WHERE email = ?",
            (email,),
        ).fetchone()
        if not pending:
            return jsonify({"error": "No pending verification for this email"}), 404

        # If user exists, just remove pending
        existing = db.execute("SELECT email FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            db.execute("DELETE FROM email_verifications WHERE email = ?", (email,))
            db.commit()
            return jsonify({"message": "Already verified"}), 200

        # Always create as student
        db.execute(
            """
            INSERT INTO users (email, password_hash, role, created_at)
            VALUES (?, ?, 'student', ?)
            """,
            (email, pending["password_hash"], _now_iso()),
        )
        db.execute("DELETE FROM email_verifications WHERE email = ?", (email,))
        db.commit()

        return jsonify({"message": "Verified (demo). Student user created."}), 200

    @app.get("/api/admin/settings/rooms_open")
    def api_admin_get_rooms_open():
        admin_email = (request.args.get("admin_email") or "").strip().lower()
        db = get_db(app)

        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        value = _get_setting(db, "rooms_open", "1")
        return jsonify({"open": value == "1"}), 200

    @app.post("/api/admin/settings/rooms_open")
    def api_admin_set_rooms_open():
        data = request.get_json(silent=True) or {}
        admin_email = (data.get("admin_email") or "").strip().lower()
        open_val = data.get("open", None)

        db = get_db(app)
        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        # accept true/false or "1"/"0"
        if isinstance(open_val, bool):
            value = "1" if open_val else "0"
        elif isinstance(open_val, str) and open_val in ("0", "1"):
            value = open_val
        else:
            return jsonify({"error": "open must be boolean (true/false) or '0'/'1'"}), 400

        db.execute(
            """
            INSERT INTO admin_settings (key, value)
            VALUES ('rooms_open', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (value,),
        )
        db.commit()

        return jsonify({"message": "Updated", "open": value == "1"}), 200

    # ---------------- Demo Inbox API ----------------
    @app.get("/api/demo/last-code")
    def api_demo_last_code():
        email = (request.args.get("email") or "").strip().lower()
        if not email:
            return jsonify({"error": "email is required"}), 400

        db = get_db(app)
        row = db.execute(
            """
            SELECT code_plain AS code, created_at, last_sent_at
            FROM email_verifications
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

        if not row:
            return jsonify({"error": "No pending verification for this email"}), 404

        return jsonify({
            "email": email,
            "code": row["code"],
            "created_at": row["created_at"],
            "last_sent_at": row["last_sent_at"],
        })

    # ---------------- Rooms APIs ----------------
    @app.get("/api/admin/settings/rooms_open")
    def api_rooms_open():
        db = get_db(app)
        value = _get_setting(db, "rooms_open", "1")
        return jsonify({"open": value == "1"})

    @app.get("/api/rooms")
    def api_rooms():
        db = get_db(app)
        rows = db.execute(
            """
            SELECT r.*,
                   (SELECT COUNT(*) FROM room_bookings rb WHERE rb.room_id = r.id) AS booked_count
            FROM rooms r
            ORDER BY r.id
            """
        ).fetchall()
        return jsonify([_room_dto_from_row(r).to_dict() for r in rows])

    @app.get("/api/me/room")
    def api_me_room():
        email = (request.args.get("email") or "").strip().lower()
        db = get_db(app)

        if not email:
            return jsonify({"room": None})

        row = db.execute(
            """
            SELECT r.*
            FROM room_bookings rb
            JOIN rooms r ON r.id = rb.room_id
            WHERE rb.user_email = ?
            """,
            (email,),
        ).fetchone()

        if not row:
            return jsonify({"room": None})

        booked = db.execute(
            "SELECT COUNT(*) AS c FROM room_bookings WHERE room_id = ?",
            (row["id"],),
        ).fetchone()["c"]

        dto = RoomDto(
            id=int(row["id"]),
            type=row["type"],
            title=row["title"],
            description=row["description"],
            price_eur=int(row["price_eur"]),
            capacity=int(row["capacity"]),
            available=bool(row["available"]),
            booked_count=int(booked),
            remaining=max(0, int(row["capacity"]) - int(booked)),
            is_full=(int(booked) >= int(row["capacity"])),
        )
        return jsonify({"room": dto.to_dict()})



    @app.post("/api/rooms/<int:room_id>/join")
    def api_join_room(room_id: int):
        db = get_db(app)

        err = _require_student(db)
        if err:
            return jsonify({"error": err}), 401

        email = _session_email()

        rooms_open = _get_setting(db, "rooms_open", "1") == "1"
        if not rooms_open:
            return jsonify({"error": "Room selection is closed by admin."}), 403

        existing = db.execute("SELECT room_id FROM room_bookings WHERE user_email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"error": "You are already in a room. Leave it first to switch."}), 409

        room = db.execute("SELECT id, capacity FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        booked = db.execute("SELECT COUNT(*) AS c FROM room_bookings WHERE room_id = ?", (room_id,)).fetchone()["c"]
        if int(booked) >= int(room["capacity"]):
            return jsonify({"error": "Room is full"}), 409

        try:
            db.execute(
                "INSERT INTO room_bookings (room_id, user_email, created_at) VALUES (?, ?, ?)",
                (room_id, email, _now_iso()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "You are already in a room. Leave it first to switch."}), 409

        return jsonify({"message": "Joined room"})

    # ---------------- Events APIs (pagination) ----------------
    @app.get("/api/events")
    def api_events():
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "4"))
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 50:
            page_size = 4

        db = get_db(app)
        total = db.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"]
        offset = (page - 1) * page_size

        rows = db.execute(
            """
            SELECT e.*,
                   (SELECT COUNT(*) FROM event_registrations er WHERE er.event_id = e.id) AS registered_count
            FROM events e
            ORDER BY e.date_time ASC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()

        items = [_event_dto_from_row(r).to_dict() for r in rows]
        has_prev = page > 1
        has_next = (offset + page_size) < int(total)

        return jsonify({
            "items": items,
            "page": page,
            "page_size": page_size,
            "has_prev": has_prev,
            "has_next": has_next,
            "total": int(total),
        })

    @app.post("/api/events/<int:event_id>/register")
    def api_register_event(event_id: int):
        db = get_db(app)

        err = _require_student(db)
        if err:
            return jsonify({"error": err}), 401

        email = _session_email()

        ev = db.execute("SELECT id, quota FROM events WHERE id = ?", (event_id,)).fetchone()
        if not ev:
            return jsonify({"error": "Event not found"}), 404

        registered = db.execute(
            "SELECT COUNT(*) AS c FROM event_registrations WHERE event_id = ?",
            (event_id,),
        ).fetchone()["c"]

        quota = ev["quota"]
        if quota is not None and int(registered) >= int(quota):
            return jsonify({"error": "Event is full"}), 409

        try:
            db.execute(
                "INSERT INTO event_registrations (event_id, user_email, created_at) VALUES (?, ?, ?)",
                (event_id, email, _now_iso()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "You are already registered for this event"}), 409

        return jsonify({"message": "Registered"})

    @app.get("/api/settings/rooms_open")
    def api_public_rooms_open():
        db = get_db(app)
        value = _get_setting(db, "rooms_open", "1")
        return jsonify({"open": value == "1"})

    @app.post("/api/rooms/leave")
    def api_leave_room():
        db = get_db(app)

        err = _require_student(db)
        if err:
            return jsonify({"error": err}), 401

        rooms_open = _get_setting(db, "rooms_open", "1") == "1"
        if not rooms_open:
            return jsonify({"error": "Room selection is closed by admin. You cannot leave your room now."}), 403

        email = _session_email()
        db.execute("DELETE FROM room_bookings WHERE user_email = ?", (email,))
        db.commit()
        return jsonify({"message": "Left room"})

    @app.get("/api/me/events")
    def api_me_events():
        email = (request.args.get("email") or "").strip().lower()
        db = get_db(app)

        err = _require_student(db, email)
        if err:
            return jsonify({"error": err}), 401

        rows = db.execute(
            """
            SELECT e.*,
                   (SELECT COUNT(*) FROM event_registrations er WHERE er.event_id = e.id) AS registered_count
            FROM event_registrations my
            JOIN events e ON e.id = my.event_id
            WHERE my.user_email = ?
            ORDER BY e.date_time ASC
            """,
            (email,),
        ).fetchall()

        items = [_event_dto_from_row(r).to_dict() for r in rows]
        return jsonify(items)

    # ---------------- Info APIs ----------------
    @app.get("/api/info/<slug>")
    def api_info(slug):
        db = get_db(app)
        row = db.execute("SELECT * FROM info_pages WHERE slug = ?", (slug,)).fetchone()
        if not row:
            abort(404)
        return jsonify(_info_dto(row).to_dict())

    @app.get("/info")
    def info_root_page():
        # default slug can be anything; we will ignore it and load all via API
        return render_template("info.html", slug="all")

    @app.get("/api/info")
    def api_info_all():
        db = get_db(app)
        rows = db.execute(
            "SELECT slug, title, content FROM info_pages ORDER BY slug"
        ).fetchall()

        items = []
        for r in rows:
            items.append({
                "slug": r["slug"],
                "title": r["title"],
                "content": r["content"],
            })
        return jsonify(items)

    # ---------------- Event Requests (student + admin) ----------------
    @app.get("/api/event-requests")
    def api_event_requests_list():
        email = (request.args.get("email") or "").strip().lower()
        db = get_db(app)

        err = _require_student(db, email)
        if err:
            return jsonify({"error": err}), 401

        rows = db.execute(
            """
            SELECT er.*
            FROM event_requests er
            LEFT JOIN student_hidden_event_requests h
              ON h.request_id = er.id AND h.student_email = er.requested_by_email
            WHERE er.requested_by_email = ?
              AND h.id IS NULL
            ORDER BY er.created_at DESC
            """,
            (email,),
        ).fetchall()

        out = []
        for r in rows:
            out.append({
                "id": int(r["id"]),
                "title": r["title"],
                "category": r["category"],
                "date_time": r["date_time"],
                "location": r["location"],
                "description": r["description"],
                "quota": (None if r["quota"] is None else int(r["quota"])),
                "status": r["status"],
                "admin_comment": r["admin_comment"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })
        return jsonify(out)

    @app.post("/api/event-requests")
    def api_event_requests_create():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()

        title = (data.get("title") or "").strip()
        category = (data.get("category") or "").strip()
        date_time = (data.get("date_time") or "").strip()
        location = (data.get("location") or "").strip()
        description = (data.get("description") or "").strip()
        quota = data.get("quota", None)

        db = get_db(app)
        err = _require_student(db, email)
        if err:
            return jsonify({"error": err}), 401

        if not title or category not in ("social", "orientation", "study_group") or not date_time or not location or not description:
            return jsonify({"error": "Invalid request fields"}), 400

        if quota is not None:
            try:
                quota_int = int(quota)
                if quota_int < 0:
                    return jsonify({"error": "Quota must be non-negative"}), 400
                quota = quota_int
            except Exception:
                return jsonify({"error": "Quota must be null or an integer"}), 400

        now = _now_iso()
        db.execute(
            """
            INSERT INTO event_requests
              (title, category, date_time, location, description, quota, requested_by_email, status, admin_comment, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?, ?)
            """,
            (title, category, date_time, location, description, quota, email, now, now),
        )
        db.commit()
        return jsonify({"message": "Event request created", "status": "pending"})

    @app.post("/api/event-requests/<int:req_id>/hide")
    def api_event_requests_hide(req_id: int):
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        db = get_db(app)

        err = _require_student(db, email)
        if err:
            return jsonify({"error": err}), 401

        row = db.execute(
            "SELECT id, requested_by_email, status FROM event_requests WHERE id = ?",
            (req_id,),
        ).fetchone()

        if not row:
            return jsonify({"error": "Request not found"}), 404
        if row["requested_by_email"] != email:
            return jsonify({"error": "Not your request"}), 403
        if row["status"] == "pending":
            return jsonify({"error": "Pending requests cannot be hidden"}), 409

        try:
            db.execute(
                """
                INSERT INTO student_hidden_event_requests (request_id, student_email, created_at)
                VALUES (?, ?, ?)
                """,
                (req_id, email, _now_iso()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"message": "Already hidden"})

        return jsonify({"message": "Hidden"})

    @app.get("/api/admin/event-requests")
    def api_admin_event_requests():
        status = (request.args.get("status") or "pending").strip().lower()
        admin_email = (request.args.get("admin_email") or "").strip().lower()
        db = get_db(app)

        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        if status not in ("pending", "accepted", "rejected"):
            status = "pending"

        rows = db.execute(
            """
            SELECT *
            FROM event_requests
            WHERE status = ?
            ORDER BY updated_at DESC
            """,
            (status,),
        ).fetchall()

        out = []
        for r in rows:
            out.append({
                "id": int(r["id"]),
                "title": r["title"],
                "category": r["category"],
                "date_time": r["date_time"],
                "location": r["location"],
                "description": r["description"],
                "quota": (None if r["quota"] is None else int(r["quota"])),
                "requested_by_email": r["requested_by_email"],
                "status": r["status"],
                "admin_comment": r["admin_comment"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })
        return jsonify(out)

    @app.post("/api/admin/event-requests/<int:req_id>/decision")
    def api_admin_event_request_decision(req_id: int):
        data = request.get_json(silent=True) or {}
        admin_email = (data.get("admin_email") or "").strip().lower()
        action = (data.get("action") or "").strip().lower()  # accept/reject
        comment = (data.get("comment") or "").strip()

        db = get_db(app)
        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        req = db.execute("SELECT * FROM event_requests WHERE id = ?", (req_id,)).fetchone()
        if not req:
            return jsonify({"error": "Request not found"}), 404

        if action not in ("accept", "reject"):
            return jsonify({"error": "Action must be accept or reject"}), 400

        now = _now_iso()

        if action == "reject":
            if not comment:
                return jsonify({"error": "Rejection comment is required"}), 400
            db.execute(
                """
                UPDATE event_requests
                SET status = 'rejected', admin_comment = ?, updated_at = ?
                WHERE id = ?
                """,
                (comment, now, req_id),
            )
            db.commit()
            return jsonify({"message": "Rejected"})

        if req["status"] == "accepted":
            return jsonify({"message": "Already accepted"})

        db.execute(
            """
            UPDATE event_requests
            SET status = 'accepted', admin_comment = NULL, updated_at = ?
            WHERE id = ?
            """,
            (now, req_id),
        )
        db.execute(
            """
            INSERT INTO events (title, category, date_time, location, description, quota, created_by_email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req["title"],
                req["category"],
                req["date_time"],
                req["location"],
                req["description"],
                req["quota"],
                req["requested_by_email"],
                now,
            ),
        )
        db.commit()
        return jsonify({"message": "Accepted and published"})

    @app.get("/api/admin/rooms")
    def api_admin_rooms():
        admin_email = (request.args.get("admin_email") or "").strip().lower()
        db = get_db(app)
        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        rows = db.execute(
            """
            SELECT r.*,
                   (SELECT COUNT(*) FROM room_bookings rb WHERE rb.room_id = r.id) AS booked_count
            FROM rooms r
            ORDER BY r.id
            """
        ).fetchall()
        return jsonify([_room_dto_from_row(r).to_dict() for r in rows])

    @app.get("/api/admin/rooms/<int:room_id>/students")
    def api_admin_room_students(room_id: int):
        admin_email = (request.args.get("admin_email") or "").strip().lower()
        db = get_db(app)
        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        room = db.execute("SELECT id, title FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if not room:
            return jsonify({"error": "Room not found"}), 404

        rows = db.execute(
            """
            SELECT user_email, created_at
            FROM room_bookings
            WHERE room_id = ?
            ORDER BY created_at ASC
            """,
            (room_id,),
        ).fetchall()

        students = [{"email": r["user_email"], "joined_at": r["created_at"]} for r in rows]
        return jsonify({"room_id": room_id, "room_title": room["title"], "students": students})

    @app.get("/api/admin/events")
    def api_admin_events():
        admin_email = (request.args.get("admin_email") or "").strip().lower()
        db = get_db(app)
        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        rows = db.execute(
            """
            SELECT e.*,
                   (SELECT COUNT(*) FROM event_registrations er WHERE er.event_id = e.id) AS registered_count
            FROM events e
            ORDER BY e.date_time ASC
            """
        ).fetchall()

        return jsonify([_event_dto_from_row(r).to_dict() for r in rows])

    @app.post("/api/events/<int:event_id>/leave")
    def api_leave_event(event_id: int):
        db = get_db(app)

        err = _require_student(db)
        if err:
            return jsonify({"error": err}), 401

        email = _session_email()

        db.execute(
            "DELETE FROM event_registrations WHERE event_id = ? AND user_email = ?",
            (event_id, email),
        )
        db.commit()

        return jsonify({"message": "Left event"})

    @app.get("/api/admin/events/<int:event_id>/students")
    def api_admin_event_students(event_id: int):
        admin_email = (request.args.get("admin_email") or "").strip().lower()
        db = get_db(app)
        err = _require_admin(db, admin_email)
        if err:
            return jsonify({"error": err}), 401

        ev = db.execute("SELECT id, title FROM events WHERE id = ?", (event_id,)).fetchone()
        if not ev:
            return jsonify({"error": "Event not found"}), 404

        rows = db.execute(
            """
            SELECT user_email, created_at
            FROM event_registrations
            WHERE event_id = ?
            ORDER BY created_at ASC
            """,
            (event_id,),
        ).fetchall()

        students = [{"email": r["user_email"], "registered_at": r["created_at"]} for r in rows]
        return jsonify({"event_id": event_id, "event_title": ev["title"], "students": students})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
