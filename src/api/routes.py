"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import jsonify, request
from datetime import date
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User, Task, Category, TaskOffered, Profile, AccountSettings, TaskDealed, Payment, Review, Message, Dispute, Admin_action
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from datetime import datetime

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)

# Endpoint para obtener todos los usuarios


@api.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    users_list = [user.serialize() for user in users]
    return jsonify(users_list), 200

# Endpoint para obtener un usuario por su id


@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify(user.serialize()), 200
    return jsonify({"error": "Usuario no encontrado"}), 404

# Endpoint para crear un nuevo usuario


@api.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Se requiere un Email valido"}), 400
    if not data or 'password' not in data:
        return jsonify({"error": "Se requiere una contraseña valida"}), 400
    if not data or 'username' not in data:
        return jsonify({"error": "Se requiere un nombre de usuario valido"}), 400

    # Importar datetime y crear current_time
    current_time = datetime.utcnow()

    new_user = User(
        email=data['email'], password=data['password'], username=data['username'],
        created_at=current_time, modified_at=current_time
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201

# Endpoint para actualizar un usuario


@api.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos inválidos"}), 400

    user.email = data.get('email', user.email)
    user.username = data.get('username', user.username)
    user.password = data.get('password', user.password)
    user.modified_at = datetime.utcnow()

    db.session.commit()
    return jsonify(user.serialize()), 200

# Endpoint para eliminar un usuario


@api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Usuario eliminado"}), 200
    return jsonify({"error": "Usuario no encontrado"}), 404

# Endpoint para obtener todas las tareas


@api.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    tasks_list = [task.serialize() for task in tasks]

    return jsonify(tasks_list), 200

# Endpoint para obtener una tarea en concreto


@api.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return jsonify(task.serialize()), 200
    return jsonify({"error": "Tarea no encontrada"}), 404

# Endpoint para eliminar una tarea en concreto


@api.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_tasks(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Tarea eliminada"}), 200
    return jsonify({"error": "Tarea no encontrada"}), 404

# Endpoint para crear una tarea


@api.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos inválidos"}), 400
        if 'title' not in data:
            return jsonify({"error": "Se requiere un título válido"}), 400
        if 'description' not in data:
            return jsonify({"error": "Se requiere una descripción válida"}), 400
        if 'publisher_id' not in data:
            return jsonify({"error": "Se requiere un ID de publicador válido"}), 400

        current_time = datetime.utcnow()
        new_task = Task(
            title=data['title'],
            description=data['description'],
            publisher_id=data['publisher_id'],
            location=data.get('location'),
            price=data.get('price'),
            due_at=current_time,
            # Valor por defecto 'pending' si no se proporciona
            status=data.get('status', 'pending')
        )

        db.session.add(new_task)
        db.session.commit()
        return jsonify(new_task.serialize_all_data()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear la tarea: {str(e)}"}), 500

# Endpoint para actualizar una tarea ya existente


@api.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"error": "Tarea no encontrada"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos inválidos"}), 400

        # Actualizar campos
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.location = data.get('location', task.location)
        task.price = data.get('price', task.price)
        task.due_at = data.get('due_at', task.due_at)
        task.status = data.get('status', task.status)
        task.publisher_id = data.get('publisher_id', task.publisher_id)

        # Manejar categorías (relación n:n)
        if 'category_id' in data:
            # Primero verificamos si la categoría existe
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({"error": "Categoría no encontrada"}), 404

            # Limpiar categorías actuales y agregar la nueva
            task.categories = [category]

        db.session.commit()
        return jsonify(task.serialize_all_data()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar la tarea: {str(e)}"}), 500

# Endpoint para obtener las tareas de un usuario en concreto


@api.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_tasks_by_user(user_id):
    user = User.query.get(user_id)
    # Si el usuario no existe, da error
    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    query = Task.query.filter_by(publisher_id=user_id)

    # Filtrar por estado
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    # Filtrar por fechas
    from_date = request.args.get('from_date')
    if from_date:
        query = query.filter(Task.created_at >= from_date)

    to_date = request.args.get('to_date')
    if to_date:
        query = query.filter(Task.created_at <= to_date)

    tasks = query.all()
    tasks_list = [task.serialize_all_data() for task in tasks]
    return jsonify(tasks_list), 200

# Endpoint para eliminar una tarea en concreto de un usuario en concreto


@api.route('/users/<int:user_id>/tasks/<int:task_id>', methods=['DELETE'])
def delete_tasks_by_user(user_id, task_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "usuario inválido"}), 404

    task = Task.query.filter_by(id=task_id, publisher_id=user_id).first()
    if not task:
        return jsonify({"error": "tarea inválida o no pertenece al usuario"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Tarea eliminada"}), 200

# Endpoint para obtener todas las categorías


@api.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    categories_list = [category.serialize() for category in categories]
    return jsonify(categories_list), 200

# Endpoint para obtener una categoría específica


@api.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    category = Category.query.get(category_id)
    if category:
        return jsonify(category.serialize()), 200
    return jsonify({"error": "Categoría no encontrada"}), 404

# Endpoint para crear una nueva categoría


@api.route('/categories', methods=['POST'])
def create_category():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Se requiere un nombre válido para la categoría"}), 400

        new_category = Category(name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        return jsonify(new_category.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear la categoría: {str(e)}"}), 500

# Endpoint para eliminar una categoria en concreto


@api.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Categoría no encontrada"}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Categoría eliminada"}), 200

# Endpoint para actualizar una categoría ya existente


@api.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Categoría no encontrada"}), 404

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Se requiere un nombre válido para la categoría"}), 400

    category.name = data['name']
    db.session.commit()
    return jsonify(category.serialize()), 200

# Endpoint para obtener todas las categorías de una tarea específica


@api.route('/tasks/<int:task_id>/categories', methods=['GET'])
def get_categories_by_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Tarea no encontrada"}), 404

    categories = task.categories
    return jsonify([category.serialize() for category in categories]), 200

# Endpoint para obtener todas las tareas de una categoría específica


@api.route('/categories/<int:category_id>/tasks', methods=['GET'])
def get_tasks_by_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Categoría no encontrada"}), 404

    tasks = category.tasks
    return jsonify([task.serialize() for task in tasks]), 200

# Endpoint para agregar una categoría a una tarea


@api.route('/tasks/<int:task_id>/categories', methods=['POST'])
def add_category_to_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Tarea no encontrada"}), 404

    data = request.get_json()
    if not data or 'category_id' not in data:
        return jsonify({"error": "Se requiere un ID de categoría válido"}), 400

    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({"error": "Categoría no encontrada"}), 404

    task.categories.append(category)
    db.session.commit()
    return jsonify(task.serialize()), 200

# Endpoint para eliminar una categoria de una tarea en especifico


@api.route('/tasks/<int:task_id>/categories', methods=['DELETE'])
def remove_category_from_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Tarea no encontrada"}), 404

    data = request.get_json()
    if not data or 'category_id' not in data:
        return jsonify({"error": "Se requiere un ID de categoría válido"}), 400

    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({"error": "Categoría no encontrada"}), 404

    if category in task.categories:
        task.categories.remove(category)
        db.session.commit()
        return jsonify(task.serialize()), 200
    else:
        return jsonify({"error": "La categoría no está asociada a la tarea"}), 400

# Endpoint para obtener el perfil de un usuario


@api.route('/users/<int:user_id>/profile', methods=['GET'])
def get_profile(user_id):
    profile = Profile.query.get(user_id)
    if not profile:
        return jsonify({"error": "Perfil no encontrado"}), 404

    return jsonify(profile.serialize()), 200

# Endpoint para modificar el perfil de un usuario


@api.route('/users/<int:user_id>/profile', methods=['PUT'])
def update_profile(user_id):
    profile = Profile.query.get(user_id)
    if not profile:
        return jsonify({"error": "Perfil no encontrado"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos inválidos"}), 400

    current_time = datetime.utcnow()

    profile.name = data.get("name", profile.name)
    profile.last_name = data.get("last_name", profile.last_name)
    profile.birth_date = data.get("birth_date", profile.birth_date)
    profile.bio = data.get("bio", profile.bio)
    profile.avatar = data.get("avatar", profile.avatar)
    profile.skills = data.get("skills", profile.skills)
    profile.rating_avg = data.get("rating_avg", profile.rating_avg)
    profile.city = data.get("city", profile.city)
    profile.modified_at = current_time

    db.session.commit()
    return jsonify(profile.serialize()), 200

# PLEASE ADD THIS TO ROUTES IN MAIN:

# ========= SEND OFFER (POST /api/tasks/:id/offers) =========


@api.route('/tasks/<int:task_id>/offers', methods=['POST'])
def create_offer(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    data = request.get_json() or {}
    tasker_id = data.get("tasker_id")      # mientras no haya auth, lo pedimos
    # se guardará en TaskOffered.status (Numeric)
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

    offer.status = amount      # usamos 'status' como "pending para prueba"
    offer.message = message

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "No se pudo guardar la oferta"}), 500

    out = offer.serialize()
    out["amount"] = float(offer.status) if offer.status is not None else None
    return jsonify(out), 201


@api.route('/tasks/<int:task_id>/offers', methods=['GET'])
def get_offers(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    offers = TaskOffered.query.filter_by(task_id=task_id).all()
    result = []
    for offer in offers:
        item = offer.serialize()
        # igual que en el POST, sacamos amount del status
        item["amount"] = float(
            offer.status) if offer.status is not None else None
        result.append(item)

    return jsonify(result), 200


# ========= REVIEW TASKER (POST /api/tasks/:id/reviews) =========
@api.route('/tasks/<int:task_id>/reviews', methods=['POST'])
def create_review(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    data = request.get_json() or {}
    rating = data.get("rating")            # 1..5 (float/int)
    comment = (data.get("comment") or "").strip()

    # Inferimos cliente y tasker para simplificar:
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


@api.route('/tasks/<int:task_id>/reviews', methods=['GET'])
def get_reviews(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    reviews = Review.query.filter_by(task_id=task_id).all()
    result = [review.serialize() for review in reviews]
    return jsonify(result), 200


# ========= TASK CHAT =========
# GET /api/tasks/:id/messages  -> lista mensajes del deal más reciente
# POST /api/tasks/:id/messages -> crea mensaje en el deal más reciente
def _latest_deal(task_id):
    return TaskDealed.query.filter_by(task_id=task_id).order_by(TaskDealed.id.desc()).first()


@api.route('/tasks/<int:task_id>/messages', methods=['GET'])
def list_messages(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify([]), 200

    deal = _latest_deal(task_id)
    if not deal:
        return jsonify([]), 200

    msgs = Message.query.filter_by(dealer_id=deal.id).order_by(
        Message.created_at.asc(), Message.id.asc()).all()
    return jsonify([m.serialize() for m in msgs]), 200


@api.route('/tasks/<int:task_id>/messages', methods=['POST'])
def create_message(task_id):
    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    sender_id = data.get("sender_id")     # mientras no haya auth, lo pedimos

    if not body or not sender_id:
        return jsonify({"message": "body y sender_id son obligatorios"}), 400

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    deal = _latest_deal(task_id)
    if not deal:
        return jsonify({"message": "No hay deal para esta tarea"}), 404

    # (simple) validación: que sea cliente o tasker del deal
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
        return jsonify({"message": "No se pudo crear el mensaje (¿unique en dealer_id?)"}), 500

    return jsonify(msg.serialize()), 201


@api.route('/tasks/<int:task_id>/deals', methods=['POST'])
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

    # Validar que la offer existe y corresponde a esta task (y ojalá al mismo tasker)
    offer = TaskOffered.query.filter_by(id=offer_id, task_id=task_id).first()
    if not offer:
        return jsonify({"message": "Offer no encontrada para esta tarea"}), 400
    # Si tu modelo de oferta tiene tasker_id, valídalo:
    if hasattr(offer, "tasker_id") and offer.tasker_id != tasker_id:
        return jsonify({"message": "offer_id no corresponde al tasker indicado"}), 400

    # Evitar duplicado por (task_id, tasker_id) si así lo manejas
    deal = TaskDealed.query.filter_by(
        task_id=task_id, tasker_id=tasker_id).first()
    if not deal:
        deal = TaskDealed(
            task_id=task_id,
            tasker_id=tasker_id,
            offer_id=offer.id,   # <-- clave
        )
        # Si status es NOT NULL:
        deal.status = "pending"   # o 0 si es entero
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


@api.route('/api/tasks/<int:task_id>/deal', methods=['GET'])
def get_latest_deal_for_task(task_id):
    deal = TaskDealed.query.filter_by(task_id=task_id)\
                           .order_by(TaskDealed.id.desc()).first()
    if not deal:
        return jsonify({"message": "No hay deals para esta tarea"}), 404
    return jsonify(deal.serialize()), 200

    # api.py (o donde tengas tus rutas)


@api.route("/api/offers/<int:offer_id>/accept", methods=["POST"])
def accept_offer(offer_id):
    # Ajusta el nombre del modelo de oferta a tu caso real:
    offer = TaskOffered.query.get(offer_id)   # o Offer.query.get(...)
    if not offer:
        return jsonify({"message": "Oferta no encontrada"}), 404

    task = Task.query.get(offer.task_id)
    if not task:
        return jsonify({"message": "Tarea no encontrada"}), 404

    # dueño/cliente de la tarea (ajusta si usas client_id en vez de publisher_id)
    client_id = getattr(task, "client_id", None) or task.publisher_id
    if not client_id:
        return jsonify({"message": "La tarea no tiene cliente/publisher definido"}), 400

    # crea el deal
    deal = TaskDealed(
        task_id=task.id,
        offer_id=offer.id,
        client_id=client_id,
        tasker_id=offer.tasker_id,               # el worker que ofertó
        fixed_price=getattr(offer, "amount", None),
        status="accepted",
        accepted_at=date.today(),
    )

    # (opcional) reflejar en Task
    task.assigned_tasker_id = offer.tasker_id
    task.status = "assigned"

    db.session.add(deal)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "No se pudo crear el deal"}), 500

    return jsonify(deal.serialize()), 201
