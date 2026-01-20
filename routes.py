from flask import Blueprint, render_template, request, redirect, url_for, session
import psycopg2
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

routes_bp = Blueprint("routes", __name__)


def get_db_connection():
    """Подключение к БД PostgreSQL"""
    return psycopg2.connect(
        user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_NAME
    )


@routes_bp.route("/")
def home():
    return render_template("home.html")


@routes_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            # подключение с введенными учетными данными
            connection = psycopg2.connect(
                user=username,
                password=password,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
            )

            cursor = connection.cursor()

            # проверка роли
            cursor.execute(
                """
                SELECT rolname FROM pg_roles 
                WHERE rolname = %s AND rolinherit = true
            """,
                (username,),
            )

            role_result = cursor.fetchone()

            if role_result and username == "driving_school_employee":
                session["username"] = username  # сохраняем имя пользователя в сессии
                session["role"] = "driving_school_employee"

                cursor.close()
                connection.close()

                return redirect(url_for("routes.home"))  # перенаправляем на главную

            cursor.close()
            connection.close()

            return render_template("login.html", error="Неверный логин или пароль")

        except (
            psycopg2.OperationalError,
            UnicodeDecodeError,
        ):  # при неверных учетных данных подключения
            return render_template("login.html", error="Неверный логин или пароль")
        except psycopg2.Error:
            return render_template("login.html", error="Неверный логин или пароль")
        except Exception:
            return render_template("login.html", error="Неверный логин или пароль")

    return render_template("login.html")


@routes_bp.route("/driving-school/welcome")
def driving_school_welcome():
    """Приветствие для сотрудника автошколы"""
    if "role" not in session or session["role"] != "driving_school_employee":
        return redirect(url_for("routes.login"))

    role = session.get("role", "Гость")
    user_id = session.get("user_id", "Unknown")

    return f"""
    <h1>Добро пожаловать!</h1>
    <p>Вы успешно вошли как сотрудник автошколы (driving_school_employee)</p>
    <p>ID пользователя: {user_id}</p>
    <p>Роль: {role}</p>
    <a href="{url_for('routes.logout')}" style="padding: 10px 20px; background: red; color: white; text-decoration: none; border-radius: 4px;">Выход</a>
    """


@routes_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("routes.home"))


@routes_bp.route("/api/candidates")
def get_candidates():
    """Получить список кандидатов"""
    if "role" not in session or session["role"] != "driving_school_employee":
        return {"error": "Unauthorized"}, 401

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM candidate_to_driver LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "columns": columns,
            "data": [dict(zip(columns, row)) for row in results],
        }
    except Exception as e:
        return {"error": str(e)}, 500


@routes_bp.route("/api/statements")
def get_statements():
    """Получить список заявлений"""
    if "role" not in session or session["role"] != "driving_school_employee":
        return {"error": "Unauthorized"}, 401

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM statement_license LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "columns": columns,
            "data": [dict(zip(columns, row)) for row in results],
        }
    except Exception as e:
        return {"error": str(e)}, 500


@routes_bp.route("/api/exams")
def get_exams():
    """Получить статус экзаменов"""

    if "role" not in session or session["role"] != "driving_school_employee":
        return {"error": "Unauthorized"}, 401

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT statement_id, status_exam FROM exam LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        return {
            "columns": columns,
            "data": [dict(zip(columns, row)) for row in results],
        }
    except Exception as e:
        return {"error": str(e)}, 500


@routes_bp.route("/api/add-candidate", methods=["POST"])
def add_candidate():
    """Добавить нового кандидата"""
    if "role" not in session or session["role"] != "driving_school_employee":
        return {"error": "Unauthorized"}, 401

    try:
        data = request.get_json()

        fcs = data.get("FCs_candidate", "").strip()
        documents = data.get("documents_candidate", "").strip()
        date_birth = data.get("date_candidate", "").strip()

        if not fcs or not documents or not date_birth:
            return {"error": "Все поля обязательны"}, 400

        if not documents.isdigit() or len(documents) != 10:
            return {"error": "Номер паспорта должен содержать ровно 10 цифр"}, 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO candidate_to_driver ("FCs_candidate", "documents_candidate", "date_candidate")
            VALUES (%s, %s, %s)
            RETURNING candidate_to_driver_id
        """,
            (fcs, documents, date_birth),
        )

        new_id = cursor.fetchone()[0]
        connection.commit()

        cursor.close()
        connection.close()

        return {
            "success": True,
            "message": f"Кандидат добавлен успешно (ID: {new_id})",
            "candidate_id": new_id,
        }, 201

    except Exception as e:
        return {"error": str(e)}, 500
