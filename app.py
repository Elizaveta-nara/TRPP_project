import sqlite3
from flask import Flask, render_template, redirect, abort, url_for, send_file
from io import BytesIO
from docx import Document
import os

app = Flask(__name__)

import os

app.secret_key = os.urandom(24)  # Генерирует случайный ключ


def get_db_connection():
    """
    Устанавливает соединение с базой данных SQLite.
    
    Returns:
        sqlite3.Connection: Объект соединения с базой данных.
    
    Raises:
        HTTP 500: Если произошла ошибка при подключении к базе данных.
    """
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        abort(500)


def execute_query(query, params=(), fetchone=False):
    """
    Выполняет SQL-запрос к базе данных.
    
    Args:
        query (str): SQL-запрос для выполнения.
        params (tuple, optional): Параметры для запроса. По умолчанию ().
        fetchone (bool, optional): Если True, возвращает одну строку, иначе все строки. По умолчанию False.
    
    Returns:
        list or sqlite3.Row: Результат запроса (все строки или одна строка).
    
    Raises:
        HTTP 500: Если произошла ошибка при выполнении запроса.
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute(query, params)
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Database query error: {e}")
        abort(500)


from datetime import datetime, timedelta

@app.route('/generate_contract/<int:repair_id>', methods=['GET', 'POST'])
def generate_contract(repair_id):
    """
    Генерирует договор в формате DOCX на основе шаблона и данных из базы.
    
    Args:
        repair_id (int): ID ремонта, для которого генерируется договор.
    
    Returns:
        Response: DOCX-файл договора для скачивания или HTML-форму для редактирования параметров.
    
    Raises:
        HTTP 404: Если ремонт с указанным ID не найден.
        HTTP 500: Если произошла ошибка при генерации договора.
    """
    if request.method == 'POST':
        try:
            # Получение данных из формы
            replacements = {
                '==CONTRACT_NUMBER==': request.form['contract_number'],
                '==CONTRACT_DATE==': request.form['contract_date'],
                # ... остальные замены ...
            }

            # Загрузка шаблона документа
            template_path = 'contract_template.docx'
            if not os.path.exists(template_path):
                flash('Шаблон договора не найден.', 'danger')
                return redirect(url_for('generate_contract', repair_id=repair_id))

            document = Document(template_path)

            # Замена меток в документе
            for paragraph in document.paragraphs:
                for key, value in replacements.items():
                    if key in paragraph.text:
                        paragraph.text = paragraph.text.replace(key, str(value))

            # Сохранение документа в буфер
            buffer = BytesIO()
            document.save(buffer)
            buffer.seek(0)

            # Отправка документа пользователю
            flash('Договор успешно сгенерирован!', 'success')
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f'Contract_{repair_id}.docx',
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        except Exception as e:
            flash(f'Ошибка при генерации договора: {e}', 'danger')
            return redirect(url_for('generate_contract', repair_id=repair_id))

    # GET запрос - отображение формы
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, 
               clients.name AS client_name, clients.passport AS client_passport, 
               employees.name AS employee_name, employees.position AS employee_position
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        JOIN employees ON repairs.employee_id = employees.id
        WHERE repairs.id_repair = ?
    """
    repair = execute_query(query, (repair_id,), fetchone=True)
    if not repair:
        abort(404)

    return render_template('edit_contract.html', repair=repair, repair_id=repair_id)


@app.route('/')
def index():
    """Перенаправляет на страницу с ремонтами."""
    return redirect(url_for('repairs'))


@app.route('/repairs')
def repairs():
    """
    Отображает список активных ремонтов.
    
    Returns:
        Response: HTML-страница со списком ремонтов.
    """
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        WHERE repairs.repair_status = FALSE
    """
    repairs = execute_query(query)
    return render_template('repairs.html', repairs=repairs)


# ... аналогичные docstrings для остальных функций ...


@app.route('/archive')
def archive():
    """
    Отображает архив завершенных ремонтов.
    
    Returns:
        Response: HTML-страница со списком завершенных ремонтов.
    """
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        WHERE repairs.repair_status = TRUE
    """
    repairs = execute_query(query)
    return render_template('archive.html', repairs=repairs)


@app.errorhandler(404)
def page_not_found(e):
    """
    Обработчик ошибки 404 (страница не найдена).
    
    Args:
        e (Exception): Объект исключения.
    
    Returns:
        Response: HTML-страница с сообщением об ошибке 404.
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """
    Обработчик ошибки 500 (внутренняя ошибка сервера).
    
    Args:
        e (Exception): Объект исключения.
    
    Returns:
        Response: HTML-страница с сообщением об ошибке 500.
    """
    return render_template('500.html', error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
