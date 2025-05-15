import sqlite3
from flask import Flask, render_template, redirect, abort, url_for, send_file
from io import BytesIO
from docx import Document
import os




app = Flask(__name__)

import os

app.secret_key = os.urandom(24)  # Генерирует случайный ключ



# Функция для подключения к базе данных
def get_db_connection():
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        abort(500)

# Общая функция для выполнения SQL-запроса
def execute_query(query, params=(), fetchone=False):
    try:
        conn = get_db_connection()
        cursor = conn.execute(query, params)
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Database query error: {e}")
        abort(500)

# Генерация договора

from datetime import datetime, timedelta

@app.route('/generate_contract/<int:repair_id>', methods=['GET', 'POST'])
def generate_contract(repair_id):
    if request.method == 'POST':
        try:
            # Получение данных из формы
            replacements = {
                '==CONTRACT_NUMBER==': request.form['contract_number'],
                '==CONTRACT_DATE==': request.form['contract_date'],
                '==CLIENT_FULLNAME==': request.form['client_fullname'],
                '==CLIENT_PASSPORT_NUMBER==': request.form['client_passport_number'],
                '==CLIENT_PASSPORT_DEPARTMENT==': request.form['client_passport_department'],
                '==CLIENT_REG_ADDRESS==': request.form['client_reg_address'],
                '==EMPLOYEE_POSITION==': request.form['employee_position'],
                '==EMPLOYEE_FULLNAME==': request.form['employee_fullname'],
                '==EMPLOYEE_ATTORNEY_POWER==': request.form['employee_attorney_power'],
                '==CAR_MAKE==': request.form['car_make'],
                '==CAR_MODEL==': request.form['car_model'],
                '==CAR_LICENSE_PLATE==': request.form['car_license_plate'],
                '==CONTRACT_DEAL_LASTDATE==': request.form['contract_deal_lastdate'],
                '==CONTRACT_LASTDATE==': request.form['contract_lastdate'],  # Новое поле
                '==CONTRACT_REPAIR_PRICE==': request.form['contract_repair_price'],
                '==CONTRACT_DEAL_PAYMENT_INFO==': request.form['contract_deal_payment_info'],
                '==CONTRACT_DEAL_OTHER_INFO==': request.form['contract_deal_other_info'],
                '==CONTRACT_AWARD_PERCENT==': request.form['contract_award_percent'],
                '==CONTRACT_AWARD_DEADLINE==': request.form['contract_award_deadline'],
                '==CONTRACT_CANCEL_BEFORE==': request.form['contract_cancel_before'],
            }

            # Загрузка шаблона документа
            template_path = 'contract_template.docx'
            if not os.path.exists(template_path):
                flash('Шаблон договора не найден.', 'danger')
                return redirect(url_for('generate_contract', repair_id=repair_id))

            document = Document(template_path)

            # Замена меток-заполнителей в параграфах
            for paragraph in document.paragraphs:
                for key, value in replacements.items():
                    if key in paragraph.text:
                        paragraph.text = paragraph.text.replace(key, str(value))

            # Замена меток-заполнителей в таблицах
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in replacements.items():
                            if key in cell.text:
                                cell.text = cell.text.replace(key, str(value))

            # Сохранение документа в буфер
            buffer = BytesIO()
            document.save(buffer)
            buffer.seek(0)

            # Формирование имени файла
            contract_number = request.form['contract_number'] or 'Unknown'
            contract_date_str = request.form['contract_date']  # Формат даты для имени файла
            file_name = f'Contract_{contract_number}_{contract_date_str}.docx'

            # Отправка документа пользователю
            flash('Договор успешно сгенерирован!', 'success')
            return send_file(
                buffer,
                as_attachment=True,
                download_name=file_name,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        except Exception as e:
            flash(f'Ошибка при генерации договора: {e}', 'danger')
            return redirect(url_for('generate_contract', repair_id=repair_id))

    # Если метод GET, отображаем форму для редактирования параметров
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name, 
               clients.passport AS client_passport, employees.name AS employee_name, 
               employees.position AS employee_position
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


# Главная страница
@app.route('/')
def index():
    return redirect(url_for('repairs'))

# Ремонты
@app.route('/repairs')
def repairs():
    # Запрос для получения незавершенных договоров
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        WHERE repairs.repair_status = FALSE
    """
    repairs = execute_query(query)
    return render_template('repairs.html', repairs=repairs)


from flask import request, flash, redirect, url_for

@app.route('/update_repair_status/<int:repair_id>', methods=['POST'])
def update_repair_status(repair_id):
    query = """
        SELECT repair_status FROM repairs WHERE id_repair = ?
    """
    repair = execute_query(query, (repair_id,), fetchone=True)
    if not repair:
        abort(404)

    # Инвертируем текущий статус
    new_status = not repair['repair_status']

    # Обновляем статус в базе данных
    update_query = """
        UPDATE repairs SET repair_status = ? WHERE id_repair = ?
    """
    try:
        conn = get_db_connection()
        conn.execute(update_query, (new_status, repair_id))
        conn.commit()
        conn.close()
        flash('Статус ремонта успешно изменен!', 'success')
    except sqlite3.Error as e:
        flash(f'Ошибка при изменении статуса ремонта: {e}', 'danger')

    return redirect(url_for('repair_details', repair_id=repair_id))

@app.route('/add_repair', methods=['GET', 'POST'])
def add_repair():
    if request.method == 'POST':
        # Получение данных из формы
        number = request.form['number']
        date = request.form['date']
        repair_type = request.form['repair_type']
        start_price = float(request.form['start_price'])  # Начальная стоимость
        discount = float(request.form['discount'])  # Скидка
        client_id = request.form['client_id']
        car_id = request.form['car_id']
        employee_id = request.form['employee_id']

        # Валидация данных
        if not number or not date or not repair_type or not start_price or not client_id or not car_id or not employee_id:
            flash('Пожалуйста, заполните все обязательные поля.', 'danger')
            return redirect(url_for('add_repair'))

        # Расчет итоговой стоимости
        finish_price = start_price - (start_price * (discount / 100))

        # Вставка данных в базу данных
        query = """
            INSERT INTO repairs (number, date, repair_type, start_price, discount, repair_status, finish_price, car_id, client_id, employee_id)
            VALUES (?, ?, ?, ?, ?, FALSE, ?, ?, ?, ?)
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (number, date, repair_type, start_price, discount, finish_price, car_id, client_id, employee_id))
            conn.commit()
            conn.close()
            flash('Договор успешно добавлен!', 'success')
            return redirect(url_for('repairs'))  # Перенаправление на страницу списка договоров
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении договора: {e}', 'danger')
            return redirect(url_for('add_repair'))

    # Получение списков для выпадающих меню
    clients = execute_query("SELECT id_client, name FROM clients")
    cars = execute_query("SELECT id_car, car_brand, car_model, license_plate FROM cars")
    employees = execute_query("SELECT id, name FROM employees")

    return render_template('add_repair.html', clients=clients, cars=cars, employees=employees)

@app.route('/repair/<int:repair_id>')
def repair_details(repair_id):
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, cars.year, cars.service_history, clients.name AS client_name, employees.name AS employee_name
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        JOIN employees ON repairs.employee_id = employees.id
        WHERE repairs.id_repair = ?
    """
    repair = execute_query(query, (repair_id,), fetchone=True)
    if repair is None:
        abort(404)
    return render_template('repair.html', repair=repair)


@app.route('/edit_repair/<int:repair_id>', methods=['GET', 'POST'])
def edit_repair(repair_id):
    if request.method == 'POST':
        # Получение данных из формы
        number = request.form['number']
        date = request.form['date']
        repair_type = request.form['repair_type']
        start_price = float(request.form['start_price'])
        discount = float(request.form['discount'])
        client_id = request.form['client_id']
        car_id = request.form['car_id']
        employee_id = request.form['employee_id']

        # Валидация данных
        if not number or not date or not repair_type or not start_price or not client_id or not car_id or not employee_id:
            flash('Пожалуйста, заполните все обязательные поля.', 'danger')
            return redirect(url_for('edit_repair', repair_id=repair_id))

        # Расчет итоговой стоимости
        finish_price = start_price - (start_price * (discount / 100))

        # Обновление данных в базе данных
        query = """
            UPDATE repairs
            SET number = ?, date = ?, repair_type = ?, start_price = ?, discount = ?, finish_price = ?, car_id = ?, client_id = ?, employee_id = ?
            WHERE id_repair = ?
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (number, date, repair_type, start_price, discount, finish_price, car_id, client_id, employee_id, repair_id))
            conn.commit()
            conn.close()
            flash('Договор успешно обновлен!', 'success')
            return redirect(url_for('repairs'))
        except sqlite3.Error as e:
            flash(f'Ошибка при обновлении договора: {e}', 'danger')
            return redirect(url_for('edit_repair', repair_id=repair_id))

    # Получение данных договора для отображения в форме
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name, employees.name AS employee_name
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        JOIN employees ON repairs.employee_id = employees.id
        WHERE repairs.id_repair = ?
    """
    repair = execute_query(query, (repair_id,), fetchone=True)
    if not repair:
        abort(404)

    # Получение списков для выпадающих меню
    clients = execute_query("SELECT id_client, name FROM clients")
    cars = execute_query("SELECT id_car, car_brand, car_model, license_plate FROM cars")
    employees = execute_query("SELECT id, name FROM employees")

    return render_template('edit_repair.html', repair=repair, clients=clients, cars=cars, employees=employees)



# Автомобили
@app.route('/cars')
def cars():
    query = """
        SELECT * FROM cars
    """
    cars = execute_query(query)
    return render_template('cars.html', cars=cars)

from flask import request, flash, redirect, url_for


@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        # Получение данных из формы
        car_brand = request.form['brand']
        car_model = request.form['model']
        license_plate = request.form['license_plate']
        year = request.form['year']
        service_history = request.form['service_history']

        # Валидация данных
        if not car_brand or not car_model or not license_plate:
            flash('Пожалуйста, заполните обязательные поля: марка, модель и государственный номер.', 'danger')
            return redirect(url_for('add_car'))

        # Вставка данных в базу данных
        query = """
            INSERT INTO cars (car_brand, car_model, license_plate, year, service_history)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (car_brand, car_model, license_plate, year, service_history))
            conn.commit()
            conn.close()
            flash('Автомобиль успешно добавлен!', 'success')
            return redirect(url_for('cars'))  # Перенаправление на страницу со списком автомобилей
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении автомобиля: {e}', 'danger')
            return redirect(url_for('add_car'))

    # Отображение формы
    return render_template('add_car.html')

@app.route('/edit_car/<int:car_id>', methods=['GET', 'POST'])
def edit_car(car_id):
    if request.method == 'POST':
        # Получение данных из формы
        car_brand = request.form['brand']
        car_model = request.form['model']
        license_plate = request.form['license_plate']
        year = request.form['year']
        service_history = request.form['service_history']

        # Валидация данных
        if not car_brand or not car_model or not license_plate:
            flash('Пожалуйста, заполните обязательные поля: марка, модель и государственный номер.', 'danger')
            return redirect(url_for('edit_car', car_id=car_id))

        # Обновление данных в базе данных
        query = """
            UPDATE cars
            SET car_brand = ?, car_model = ?, license_plate = ?, year = ?, service_history = ?
            WHERE id_car = ?
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (car_brand, car_model, license_plate, year, service_history, car_id))
            conn.commit()
            conn.close()
            flash('Автомобиль успешно обновлен!', 'success')
            return redirect(url_for('cars'))
        except sqlite3.Error as e:
            flash(f'Ошибка при обновлении автомобиля: {e}', 'danger')
            return redirect(url_for('edit_car', car_id=car_id))

    # Получение данных автомобиля для отображения в форме
    query = """
        SELECT * FROM cars WHERE id_car = ?
    """
    car = execute_query(query, (car_id,), fetchone=True)
    if not car:
        abort(404)

    return render_template('edit_car.html', car=car)

# Список клиентов
@app.route('/clients')
def clients_list():
    query = """
        SELECT id_client, name, email, phone_number, passport
        FROM clients
    """
    clients = execute_query(query)
    return render_template('clients.html', clients=clients)

@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        # Логика добавления клиента
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        passport = request.form['passport']
        car_id = request.form['car_id'] or None

        # Валидация данных
        if not name or not email or not phone_number:
            flash('Пожалуйста, заполните обязательные поля: ФИО, email и номер телефона.', 'danger')
            return redirect(url_for('add_client'))

        # Вставка данных в базу данных
        try:
            conn = get_db_connection()

            # Добавление клиента
            query_client = """
                INSERT INTO clients (name, email, phone_number, passport)
                VALUES (?, ?, ?, ?)
            """
            cursor = conn.execute(query_client, (name, email, phone_number, passport))
            client_id = cursor.lastrowid  # Получаем ID только что добавленного клиента

            # Если выбран автомобиль, обновляем его client_id
            if car_id:
                query_update_car = """
                    UPDATE cars
                    SET client_id = ?
                    WHERE id_car = ?
                """
                conn.execute(query_update_car, (client_id, car_id))

            conn.commit()
            conn.close()
            flash('Клиент успешно добавлен!', 'success')
            return redirect(url_for('clients_list'))  # Перенаправление на страницу списка клиентов
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении клиента: {e}', 'danger')
            return redirect(url_for('add_client'))

    # Получение списка автомобилей для выпадающего списка
    query = "SELECT id_car, car_brand, car_model, license_plate FROM cars WHERE client_id IS NULL"
    cars = execute_query(query)
    return render_template('add_client.html', cars=cars)

@app.route('/client/<int:client_id>')
def client_details(client_id):
    # Получение данных о клиенте
    query_client = """
        SELECT * FROM clients WHERE id_client = ?
    """
    client = execute_query(query_client, (client_id,), fetchone=True)
    if not client:
        abort(404)

    # Получение автомобилей клиента
    query_cars = """
        SELECT cars.car_brand, cars.car_model, cars.license_plate
        FROM cars
        WHERE cars.client_id = ?
    """
    cars = execute_query(query_cars, (client_id,))

    return render_template('client.html', client=client, cars=cars)

@app.route('/edit_client/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    if request.method == 'POST':
        # Получение данных из формы
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        passport = request.form['passport']
        address = request.form['address']

        # Валидация данных
        if not name or not email or not phone_number:
            flash('Пожалуйста, заполните обязательные поля: ФИО, email и номер телефона.', 'danger')
            return redirect(url_for('edit_client', client_id=client_id))

        # Обновление данных в базе данных
        query = """
            UPDATE clients
            SET name = ?, email = ?, phone_number = ?, passport = ?, address = ?
            WHERE id_client = ?
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (name, email, phone_number, passport, address, client_id))
            conn.commit()
            conn.close()
            flash('Данные клиента успешно обновлены!', 'success')
            return redirect(url_for('clients_list'))
        except sqlite3.Error as e:
            flash(f'Ошибка при обновлении данных клиента: {e}', 'danger')
            return redirect(url_for('edit_client', client_id=client_id))

    # Получение данных клиента для отображения в форме
    query = """
        SELECT * FROM clients WHERE id_client = ?
    """
    client = execute_query(query, (client_id,), fetchone=True)
    if not client:
        abort(404)

    return render_template('edit_client.html', client=client)


@app.route('/report/<int:report_id>')
def report(report_id):
    query = """
        SELECT reports.*, employees.name AS employee_name
        FROM reports
        JOIN employees ON reports.employee_id = employees.id
        WHERE reports.id = ?
    """
    report = execute_query(query, (report_id,), fetchone=True)
    if not report:
        abort(404)
    return render_template('report.html', report=report)

# Отчёты
@app.route('/reports')
def reports():
    query = """
        SELECT reports.*, employees.name AS employee_name
        FROM reports
        JOIN employees ON reports.employee_id = employees.id
    """
    reports = execute_query(query)
    return render_template('reports.html', reports=reports)

@app.route('/generate_personal_report/<int:report_id>')
def generate_personal_report(report_id):
    # Получение данных отчета из базы данных
    query = """
        SELECT reports.*, employees.name AS employee_name
        FROM reports
        JOIN employees ON reports.employee_id = employees.id
        WHERE reports.id = ?
    """
    report = execute_query(query, (report_id,), fetchone=True)
    if not report:
        abort(404)

    # Запрос для получения данных по ремонтам за указанный период и со статусом "завершен"
    repairs_query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        WHERE repairs.date BETWEEN ? AND ? 
          AND repairs.employee_id = ?
          AND repairs.repair_status = TRUE  -- Добавлено условие для статуса "завершен"
    """
    repairs = execute_query(repairs_query, (report['start_date'], report['end_date'], report['employee_id']))


    # Загрузка шаблона отчета
    template_path = 'template_basic_report.docx'
    if not os.path.exists(template_path):
        flash('Шаблон отчета не найден.', 'danger')
        return redirect(url_for('reports'))

    document = Document(template_path)

    # Заполнение шаблона данными
    replacements = {
        '==REPORT_DATE==': datetime.now().strftime('%d.%m.%Y'),
        '==EMPLOYEE_NAME==': report['employee_name'],
        '==START_DATE==': report['start_date'],
        '==END_DATE==': report['end_date'],
    }

    # Замена меток-заполнителей в параграфах
    for paragraph in document.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, str(value))

    # Заполнение таблицы с ремонтами
    table = document.tables[0]  # Получаем первую таблицу в документе

    # Добавляем строки с данными из базы данных
    for i, repair in enumerate(repairs, start=1):
        row = table.add_row().cells  # Добавляем новую строку
        row[0].text = str(i)  # Номер строки
        row[1].text = f"{repair['number']} от {repair['date']}"  # Договор
        row[2].text = f"{repair['car_brand']} {repair['car_model']}, {repair['license_plate']}"  # Автомобиль
        row[3].text = f"{repair['start_price']} ₽"  # Сумма сделки
        row[4].text = f"{repair['start_price'] * 0.2} ₽"  # Сумма вознаграждения (20%)
        row[5].text = report['employee_name']  # Специалист

    # Заполнение итогов
    total_repairs = len(repairs)
    total_price = sum(repair['start_price'] for repair in repairs)
    total_reward = total_price * 0.2

    summary_table = document.tables[1]  # Получаем вторую таблицу (итоги)
    summary_table.rows[1].cells[2].text = str(total_repairs)  # Общее количество ремонтов
    summary_table.rows[2].cells[2].text = f"{total_price} рублей"  # Суммарная стоимость ремонтов
    summary_table.rows[3].cells[2].text = f"{total_reward} рублей"  # Суммарная стоимость вознаграждения

    # Сохранение документа в буфер
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    # Формирование имени файла
    file_name = f'Personal_Report_{report["number"]}_{report["start_date"]}_{report["end_date"]}.docx'

    # Отправка документа пользователю
    return send_file(
        buffer,
        as_attachment=True,
        download_name=file_name,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@app.route('/add_report', methods=['GET', 'POST'])
def add_report():
    if request.method == 'POST':
        # Получение данных из формы
        number = request.form['number']
        date = request.form['date']
        report_type = request.form['report_type']
        description = request.form['description']
        employee_id = request.form['employee_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Валидация данных
        if not number or not date or not report_type or not employee_id or not start_date or not end_date:
            flash('Пожалуйста, заполните все обязательные поля.', 'danger')
            return redirect(url_for('add_report'))

        # Вставка данных в базу данных
        query = """
            INSERT INTO reports (number, date, report_type, description, employee_id, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (number, date, report_type, description, employee_id, start_date, end_date))
            conn.commit()
            conn.close()
            flash('Отчет успешно добавлен!', 'success')
            return redirect(url_for('reports'))
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении отчета: {e}', 'danger')
            return redirect(url_for('add_report'))

    # Получение списка сотрудников для выпадающего списка
    employees = execute_query("SELECT id, name FROM employees")
    return render_template('add_report.html', employees=employees)

@app.template_filter('format_date')
def format_date_filter(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        return date_str  # Возвращаем исходную строку, если формат некорректен

@app.route('/edit_report/<int:report_id>', methods=['GET', 'POST'])
def edit_report(report_id):
    if request.method == 'POST':
        # Получение данных из формы
        number = request.form['number']
        date = request.form['date']
        report_type = request.form['report_type']
        description = request.form['description']
        employee_id = request.form['employee_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Проверка наличия report_id в данных формы
        if 'report_id' not in request.form:
            flash('Ошибка: отсутствует report_id в данных формы.', 'danger')
            return redirect(url_for('reports'))

        report_id = request.form['report_id']  # Убедитесь, что report_id передается из формы

        # Валидация данных
        if not number or not date or not report_type or not employee_id or not start_date or not end_date:
            flash('Пожалуйста, заполните все обязательные поля.', 'danger')
            return redirect(url_for('edit_report', report_id=report_id))  # Передаем report_id

        # Отладочный вывод
        print("Form data:")
        print(f"Number: {number}, Date: {date}, Report Type: {report_type}, Description: {description}, Employee ID: {employee_id}, Start Date: {start_date}, End Date: {end_date}, Report ID: {report_id}")

        # Обновление данных в базе данных
        query = """
            UPDATE reports
            SET number = ?, date = ?, report_type = ?, description = ?, employee_id = ?, start_date = ?, end_date = ?
            WHERE id = ?
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (number, date, report_type, description, employee_id, start_date, end_date, report_id))
            conn.commit()
            conn.close()
            flash('Отчет успешно обновлен!', 'success')
            return redirect(url_for('reports'))
        except sqlite3.Error as e:
            flash(f'Ошибка при обновлении отчета: {e}', 'danger')
            return redirect(url_for('edit_report', report_id=report_id))  # Передаем report_id

    # Получение данных отчета для отображения в форме
    query = """
        SELECT * FROM reports WHERE id = ?
    """
    report = execute_query(query, (report_id,), fetchone=True)
    if not report:
        abort(404)

    # Получение списка сотрудников для выпадающего списка
    employees = execute_query("SELECT id, name FROM employees")
    return render_template('edit_report.html', report=report, employees=employees)







from openpyxl import Workbook
import io


from datetime import datetime

@app.route('/generate_occupancy_report', methods=['GET', 'POST'])
def generate_occupancy_report():
    if request.method == 'POST':
        # Получение данных из формы
        employee_id = request.form.get('employee_id')
        client_id = request.form.get('client_id')
        car_id = request.form.get('car_id')
        action = request.form.get('action')  # Получаем действие (excel, pdf, chart)

        # Формирование SQL-запроса
        query = """
            SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name, employees.name AS employee_name
            FROM repairs
            JOIN cars ON repairs.car_id = cars.id_car
            JOIN clients ON repairs.client_id = clients.id_client
            JOIN employees ON repairs.employee_id = employees.id
            WHERE repairs.repair_status = FALSE  -- Фильтр по статусу "в работе"
        """
        params = []

        # Если выбран конкретный сотрудник, добавляем условие в запрос
        if employee_id:
            query += " AND repairs.employee_id = ?"
            params.append(employee_id)

        # Если выбран конкретный клиент, добавляем условие в запрос
        if client_id:
            query += " AND repairs.client_id = ?"
            params.append(client_id)

        # Если выбран конкретный автомобиль, добавляем условие в запрос
        if car_id:
            query += " AND repairs.car_id = ?"
            params.append(car_id)

        # Сортировка по дате
        query += " ORDER BY repairs.date ASC"

        # Выполнение запроса
        repairs = execute_query(query, tuple(params))
        print("Ремонтные записи:", repairs)  # Отладочный вывод

        # Проверка наличия данных
        if not repairs:
            flash('Данные не найдены для указанных фильтров.', 'warning')
            return redirect(url_for('generate_occupancy_report'))

        # Обработка действий
        if action == "excel":
            # Создание Excel-документа
            wb = Workbook()
            ws = wb.active
            ws.title = "Занятость"
            headers = ["Номер договора", "Дата", "Автомобиль", "Клиент", "Сотрудник", "Статус"]
            ws.append(headers)

            # Заполнение данных
            total_count = 0
            total_price = 0
            for repair in repairs:
                row = [
                    repair['number'],
                    repair['date'],
                    f"{repair['car_brand']} {repair['car_model']} ({repair['license_plate']})",
                    repair['client_name'],
                    repair['employee_name'],
                    "Завершен" if repair['repair_status'] else "В работе"
                ]
                ws.append(row)
                total_count += 1
                total_price += repair['start_price']

            # Добавление итоговой строки
            ws.append(["", "", "", "", "Итого:", total_count])
            ws.append(["", "", "", "", "Общая стоимость:", total_price])

            # Добавление фильтра по датам
            ws.auto_filter.ref = f"A1:F{len(repairs) + 3}"  # Добавляем фильтр ко всей таблице

            # Сохранение документа в буфер
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            # Отправка документа пользователю
            return send_file(
                output,
                as_attachment=True,
                download_name="occupancy_report.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif action == "chart":
            # Генерация графика
            chart_buffer = generate_chart(repairs)
            return send_file(
                chart_buffer,
                as_attachment=True,
                download_name="chart.png",
                mimetype="image/png"
            )

    # Если метод GET, отображаем форму для фильтров
    employees = execute_query("SELECT id, name FROM employees")
    clients = execute_query("SELECT id_client, name FROM clients")
    cars = execute_query("SELECT id_car, car_brand, car_model, license_plate FROM cars")
    return render_template('generate_occupancy_report.html', employees=employees, clients=clients, cars=cars)


import matplotlib.pyplot as plt
import base64
from io import BytesIO

def generate_chart(repairs):
    dates = [repair['date'] for repair in repairs]
    prices = [repair['start_price'] for repair in repairs]

    plt.figure(figsize=(8, 4))
    plt.bar(dates, prices, color='blue')
    plt.xlabel("Дата")
    plt.ylabel("Стоимость")
    plt.title("График стоимости ремонтов")

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    return buffer

# Сотрудники
@app.route('/employees')
def employees():
    query = """
        SELECT id, name, email, phone_number, position, department
        FROM employees
    """
    employees = execute_query(query)
    return render_template('employees.html', employees=employees)

@app.route('/employee/<int:employee_id>')
def employee(employee_id):
    query = """
        SELECT id, name, email, phone_number, position, department
        FROM employees
        WHERE id = ?
    """
    employee = execute_query(query, (employee_id,), fetchone=True)
    if employee is None:
        abort(404)
    return render_template('employee.html', employee=employee)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        # Получение данных из формы
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        position = request.form['position']
        department = request.form['department']

        # Валидация данных
        if not name or not email or not phone_number or not position:
            flash('Пожалуйста, заполните обязательные поля: ФИО, email, номер телефона и должность.', 'danger')
            return redirect(url_for('add_employee'))

        # Вставка данных в базу данных
        query = """
            INSERT INTO employees (name, email, phone_number, position, department)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (name, email, phone_number, position, department))
            conn.commit()
            conn.close()
            flash('Сотрудник успешно добавлен!', 'success')
            return redirect(url_for('employees'))  # Перенаправление на страницу списка сотрудников
        except sqlite3.Error as e:
            flash(f'Ошибка при добавлении сотрудника: {e}', 'danger')
            return redirect(url_for('add_employee'))

    # Отображение формы
    return render_template('add_employee.html')

@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if request.method == 'POST':
        # Получение данных из формы
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        position = request.form['position']
        department = request.form['department']

        # Валидация данных
        if not name or not email or not phone_number or not position:
            flash('Пожалуйста, заполните обязательные поля: ФИО, email, номер телефона и должность.', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))

        # Обновление данных в базе данных
        query = """
            UPDATE employees
            SET name = ?, email = ?, phone_number = ?, position = ?, department = ?
            WHERE id = ?
        """
        try:
            conn = get_db_connection()
            conn.execute(query, (name, email, phone_number, position, department, employee_id))
            conn.commit()
            conn.close()
            flash('Данные сотрудника успешно обновлены!', 'success')
            return redirect(url_for('employees'))
        except sqlite3.Error as e:
            flash(f'Ошибка при обновлении данных сотрудника: {e}', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))

    # Получение данных сотрудника для отображения в форме
    query = """
        SELECT * FROM employees WHERE id = ?
    """
    employee = execute_query(query, (employee_id,), fetchone=True)
    if not employee:
        abort(404)

    return render_template('edit_employee.html', employee=employee)

#архив
@app.route('/archive')
def archive():
    # Запрос для получения завершенных договоров
    query = """
        SELECT repairs.*, cars.car_brand, cars.car_model, cars.license_plate, clients.name AS client_name
        FROM repairs
        JOIN cars ON repairs.car_id = cars.id_car
        JOIN clients ON repairs.client_id = clients.id_client
        WHERE repairs.repair_status = TRUE
    """
    repairs = execute_query(query)
    return render_template('archive.html', repairs=repairs)


from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature


class VerifySignatureForm(FlaskForm):
    repair_id = IntegerField('ID договора', validators=[DataRequired()])
    public_key = StringField('Публичный ключ', validators=[DataRequired()])
    submit = SubmitField('Проверить подпись')

# Генерация ключей
def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Подпись данных
def sign_data(private_key, data):
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

# Проверка подписи
def verify_signature(public_key, data, signature):
    try:
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False

# Главная страница
@app.route('/')
def home():
    return "Добро пожаловать в приложение с ЭЦП!"

# Страница для подписания контракта
@app.route('/sign_contract/<int:repair_id>', methods=['POST'])
def sign_contract(repair_id):
    # Получение данных контракта из базы данных
    conn = get_db_connection()
    query = """
        SELECT * FROM repairs WHERE id_repair = ?
    """
    repair = conn.execute(query, (repair_id,)).fetchone()
    conn.close()

    if not repair:
        abort(404, description="Контракт не найден")

    # Генерация ключей
    private_key, public_key = generate_keys()

    # Данные для подписи (например, номер контракта и дата)
    contract_data = f"{repair['number']}_{repair['date']}"

    # Подпись данных
    signature = sign_data(private_key, contract_data)

    # Сохранение публичного ключа и подписи в базе данных
    conn = get_db_connection()
    update_query = """
        UPDATE repairs
        SET public_key = ?, signature = ?
        WHERE id_repair = ?
    """
    conn.execute(update_query, (
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode(),
        signature.hex(),
        repair_id
    ))
    conn.commit()
    conn.close()

    flash('Контракт успешно подписан!', 'success')
    return redirect(url_for('repair_details', repair_id=repair_id))

# Страница для проверки подписи контракта
@app.route('/verify_contract', methods=['GET', 'POST'])
def verify_contract():
    form = VerifySignatureForm()
    result = None

    if form.validate_on_submit():
        # Получение данных из формы
        repair_id = form.repair_id.data
        public_key_pem = form.public_key.data

        # Получение данных контракта из базы данных
        conn = get_db_connection()
        query = """
            SELECT * FROM repairs WHERE id_repair = ?
        """
        repair = conn.execute(query, (repair_id,)).fetchone()
        conn.close()

        if not repair:
            flash('Контракт не найден', 'danger')
            return redirect(url_for('verify_contract'))

        # Получение публичного ключа и подписи из базы данных
        public_key_pem_db = repair['public_key']
        signature = repair['signature']

        if not public_key_pem_db or not signature:
            flash('Публичный ключ или подпись отсутствуют', 'danger')
            return redirect(url_for('verify_contract'))

        # Данные для проверки
        contract_data = f"{repair['number']}_{repair['date']}"

        # Проверка подписи
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            is_valid = verify_signature(public_key, contract_data, bytes.fromhex(signature))
            result = 'Подпись действительна' if is_valid else 'Подпись недействительна'
        except Exception as e:
            result = f'Ошибка при проверке подписи: {e}'

    return render_template('verify_contract.html', form=form, result=result)


# Обработчики ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html', error=str(e)), 500





if __name__ == '__main__':
    app.run(debug=True)