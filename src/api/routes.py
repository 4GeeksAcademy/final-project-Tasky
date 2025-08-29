# src/api/routes.py
from flask import Blueprint, jsonify, request
from flask_cors import CORS
from datetime import date
from datetime import datetime

# <-- asegúrate que Profile está en models.py
from api.models import db, User, Task, Profile, TaskDealed, Message, TaskOffered, Review

api = Blueprint("api", __name__)
# útil si el front envía cookies/credenciales
CORS(api, supports_credentials=True)

# =========================
# HEALTH
# =========================


@api.get("/health")
def health():
    return jsonify({"msg": "Hello from Tasky API"}), 200


# =========================
# USERS
# =========================
@api.get("/users")
def get_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200


@api.get("/users/<int:user_id>")
def get_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(u.serialize()), 200


@api.post("/users")
def create_user():
    data = request.get_json() or {}
    if not data.get("email") or not data.get("password") or not data.get("username"):
        return jsonify({"error": "email, password y username son requeridos"}), 400

    u = User(
        email=data["email"],
        password=data["password"],      # TODO: hashear en prod
        username=data["username"]
    )
    db.session.add(u)
    db.session.commit()
    return jsonify(u.serialize()), 201


@api.put("/users/<int:user_id>")
def update_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json() or {}
    u.email = data.get("email", u.email)
    u.username = data.get("username", u.username)
    u.password = data.get("password", u.password)  # TODO: hashear en prod
    db.session.commit()
    return jsonify(u.serialize()), 200


@api.delete("/users/<int:user_id>")
def delete_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"error": "Usuario no encontrado"}), 404
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "Usuario eliminado"}), 200


@api.get("/users/by-username/<string:username>")
def get_user_by_username(username):
    # .ilike hace búsqueda case-insensitive
    u = User.query.filter(User.username.ilike(username)).first()
    if not u:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(u.serialize()), 200


# =========================
# PROFILES (PUBLIC/PRIVATE)
# =========================
@api.get("/users/<int:user_id>/profile")
def get_profile(user_id):
    prof = Profile.query.get(user_id)  # PK = user_id en este modelo
    if not prof:
        return jsonify({"error": "Perfil no encontrado"}), 404
    return jsonify(prof.serialize()), 200


@api.put("/users/<int:user_id>/profile")
def update_profile(user_id):
    """
    Crea o actualiza el perfil del usuario.
    Si el perfil no existe, lo crea con valores por defecto para
    las columnas NOT NULL (name, etc.).
    """
    data = request.get_json() or {}

    # por si quieres validar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    prof = Profile.query.get(user_id)  # PK = user_id
    if not prof:
        # ---- crear con DEFAULTS para NOT NULL ----
        prof = Profile(
            user_id=user_id,
            # name es NOT NULL -> usa body o username o string vacío
            name=(data.get("name") or user.username or ""),
            # estas pueden ser NOT NULL en tu modelo; si lo son, ponles default
            last_name=data.get("last_name") or "",
            avatar=data.get("avatar") or "",
            city=data.get("city") or "",
            # si tu col no es NOT NULL, puede ir None
            birth_date=data.get("birth_date"),
            bio=data.get("bio") or "",
            skills=data.get("skills") or "",
            rating_avg=data.get("rating_avg") or 0.0,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        db.session.add(prof)
    else:
        # ---- actualizar sólo los campos recibidos ----
        for field in ["name", "last_name", "avatar", "city", "birth_date", "bio", "skills", "rating_avg"]:
            if field in data and data[field] is not None:
                setattr(prof, field, data[field])
        prof.modified_at = datetime.utcnow()

    db.session.commit()
    return jsonify(prof.serialize()), 200

# =========================
# TASKS (mínimo viable)
# =========================


@api.get("/tasks")
def list_tasks():
    tasks = Task.query.all()
    return jsonify([t.serialize() for t in tasks]), 200


@api.post("/tasks")
def create_task():
    data = request.get_json() or {}
    if not data.get("title") or not data.get("description") or not data.get("publisher_id"):
        return jsonify({"error": "title, description, publisher_id son requeridos"}), 400

    t = Task(
        title=data["title"],
        description=data["description"],
        publisher_id=data["publisher_id"],
        location=data.get("location"),
        price=data.get("price"),
        status=data.get("status", "pending"),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(t.serialize()), 201


@api.get("/tasks/<int:task_id>")
def get_task(task_id):
    t = Task.query.get(task_id)
    if not t:
        return jsonify({"error": "Tarea no encontrada"}), 404
    return jsonify(t.serialize()), 200


@api.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    t = Task.query.get(task_id)
    if not t:
        return jsonify({"error": "Tarea no encontrada"}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "Tarea eliminada"}), 200


# tasks by user

@api.get("/users/<int:user_id>/tasks")
def get_tasks_by_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    query = Task.query.filter_by(publisher_id=user_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    from_date = request.args.get("from_date")
    if from_date:
        query = query.filter(Task.created_at >= from_date)

    to_date = request.args.get("to_date")
    if to_date:
        query = query.filter(Task.created_at <= to_date)

    tasks = query.all()
    return jsonify([t.serialize_all_data() for t in tasks]), 200


@api.delete("/users/<int:user_id>/tasks")
def delete_tasks_by_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    tasks = Task.query.filter_by(publisher_id=user_id).all()
    if not tasks:
        return jsonify({"message": "No se encontraron tareas para este usuario"}), 404

    for t in tasks:
        db.session.delete(t)
    db.session.commit()

    return jsonify({"message": f"Se eliminaron {len(tasks)} tareas del usuario {user_id}"}), 200


# ========= OFFERS =========

@api.post("/tasks/<int:task_id>/offers")
def create_offer(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    data = request.get_json() or {}
    tasker_id = data.get("tasker_id")              # mientras no haya auth
    amount = data.get("amount")
    message = (data.get("message") or "").strip()

    if not tasker_id or amount is None:
        return jsonify({"message": "tasker_id y amount son obligatorios"}), 400

    # upsert por (task_id, tasker_id)
    offer = TaskOffered.query.filter_by(
        task_id=task_id, tasker_id=tasker_id).first()
    if not offer:
        offer = TaskOffered(task_id=task_id, tasker_id=tasker_id)
        db.session.add(offer)

    # Nota: hoy usas 'status' para guardar amount en modo demo
    offer.status = amount
    offer.message = message

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "No se pudo guardar la oferta"}), 500

    out = offer.serialize()
    out["amount"] = float(offer.status) if offer.status is not None else None
    return jsonify(out), 201


@api.get("/tasks/<int:task_id>/offers")
def get_offers(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    offers = TaskOffered.query.filter_by(task_id=task_id).all()
    result = []
    for offer in offers:
        item = offer.serialize()
        item["amount"] = float(
            offer.status) if offer.status is not None else None
        result.append(item)

    return jsonify(result), 200


# ========= REVIEWS =========

@api.post("/tasks/<int:task_id>/reviews")
def create_review(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    data = request.get_json() or {}
    rating = data.get("rating")                     # 1..5
    comment = (data.get("comment") or "").strip()

    # Inferimos cliente y tasker
    publisher_id = task.publisher_id
    deal = TaskDealed.query.filter_by(
        task_id=task_id).order_by(TaskDealed.id.desc()).first()
    worker_id = data.get("worker_id") or (deal.tasker_id if deal else None)

    if rating is None or worker_id is None or deal is None:
        return jsonify({"message": "rating y worker_id/deal requeridos (no se pudo inferir)"}), 400

    # 1 review por deal
    existing = Review.query.filter_by(task_dealed_id=deal.id).first()
    if existing:
        return jsonify({"message": "Ya existe una review para este deal"}), 409

    review = Review(
        review=comment,
        rate=rating,
        created_at=datetime.utcnow(),
        publisher_id=publisher_id,
        worker_id=worker_id,
        task_dealed_id=deal.id,
        task_id=task_id,
    )
    db.session.add(review)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "No se pudo guardar la review"}), 500

    return jsonify(review.serialize()), 201


@api.get("/tasks/<int:task_id>/reviews")
def get_reviews(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    reviews = Review.query.filter_by(task_id=task_id).all()
    return jsonify([r.serialize() for r in reviews]), 200


# ========= TASK CHAT =========

def _latest_deal(task_id):
    return TaskDealed.query.filter_by(task_id=task_id).order_by(TaskDealed.id.desc()).first()


@api.get("/tasks/<int:task_id>/messages")
def list_messages(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify([]), 200

    deal = _latest_deal(task_id)
    if not deal:
        return jsonify([]), 200

    msgs = Message.query.filter_by(dealer_id=deal.id).order_by(
        Message.created_at.asc(), Message.id.asc()
    ).all()
    return jsonify([m.serialize() for m in msgs]), 200


@api.post("/tasks/<int:task_id>/messages")
def create_message(task_id):
    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    sender_id = data.get("sender_id")                 # mientras no haya auth

    if not body or not sender_id:
        return jsonify({"message": "body y sender_id son obligatorios"}), 400

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    deal = _latest_deal(task_id)
    if not deal:
        return jsonify({"message": "No hay deal para esta tarea"}), 404

    # debe ser cliente o tasker del deal
    if sender_id not in (deal.client_id, deal.tasker_id):
        return jsonify({"message": "sender_id no pertenece a este deal"}), 403

    msg = Message(
        body=body,
        created_at=datetime.utcnow(),
        dealer_id=deal.id,
        sender_id=sender_id
    )
    db.session.add(msg)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "No se pudo crear el mensaje"}), 500

    return jsonify(msg.serialize()), 201


# ========= DEALS =========

@api.post("/tasks/<int:task_id>/deals")
def create_deal(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    data = request.get_json() or {}
    tasker_id = data.get("tasker_id")
    offer_id = data.get("offer_id")
    if not tasker_id:
        return jsonify({"message": "tasker_id es obligatorio"}), 400
    if not offer_id:
        return jsonify({"message": "offer_id es obligatorio"}), 400

    # validar offer contra la task (y tasker si aplica)
    offer = TaskOffered.query.filter_by(id=offer_id, task_id=task_id).first()
    if not offer:
        return jsonify({"message": "Offer no encontrada para esta tarea"}), 400
    if hasattr(offer, "tasker_id") and offer.tasker_id != tasker_id:
        return jsonify({"message": "offer_id no corresponde al tasker indicado"}), 400

    # evitar duplicado (task_id, tasker_id)
    deal = TaskDealed.query.filter_by(
        task_id=task_id, tasker_id=tasker_id).first()
    if not deal:
        deal = TaskDealed(
            task_id=task_id,
            tasker_id=tasker_id,
            offer_id=offer.id,
            status="pending"          # si tu columna es NOT NULL
        )
        db.session.add(deal)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "No se pudo guardar el deal",
            "error": e.__class__.__name__,
            "detail": str(getattr(e, "orig", e))
        }), 500

    return jsonify({
        "id": deal.id,
        "task_id": deal.task_id,
        "tasker_id": deal.tasker_id,
        "offer_id": deal.offer_id,
        "status": deal.status
    }), 201


@api.get("/tasks/<int:task_id>/deal")
def get_latest_deal_for_task(task_id):
    deal = TaskDealed.query.filter_by(
        task_id=task_id).order_by(TaskDealed.id.desc()).first()
    if not deal:
        return jsonify({"message": "No hay deals para esta tarea"}), 404
    return jsonify(deal.serialize()), 200


@api.post("/offers/<int:offer_id>/accept")
def accept_offer(offer_id):
    offer = TaskOffered.query.get(offer_id)
    if not offer:
        return jsonify({"message": "Oferta no encontrada"}), 404

    task = Task.query.get(offer.task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    client_id = getattr(task, "client_id", None) or task.publisher_id
    if not client_id:
        return jsonify({"message": "La tarea no tiene cliente/publisher definido"}), 400

    deal = TaskDealed(
        task_id=task.id,
        offer_id=offer.id,
        client_id=client_id,
        tasker_id=offer.tasker_id,
        fixed_price=getattr(offer, "amount", None),
        status="accepted",
        accepted_at=date.today(),
    )

    # reflejar en Task (opcional)
    task.assigned_tasker_id = offer.tasker_id
    task.status = "assigned"

    db.session.add(deal)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "No se pudo crear el deal"}), 500

    return jsonify(deal.serialize()), 201
