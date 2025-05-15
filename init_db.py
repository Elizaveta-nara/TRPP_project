import sqlite3

# Создание и подключение к базе данных
connection = sqlite3.connect('database.db')
cur = connection.cursor()

# Создание таблицы сотрудников
cur.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone_number TEXT,
    position TEXT,
    department TEXT,
    chief_id INTEGER
);
""")

# Создание таблицы клиентов
cur.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id_client INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone_number TEXT,
    passport TEXT
);
""")

# Создание таблицы автомобилей
cur.execute("""
CREATE TABLE IF NOT EXISTS cars (
    id_car INTEGER PRIMARY KEY AUTOINCREMENT,
    car_brand TEXT,
    car_model TEXT NOT NULL,
    license_plate TEXT NOT NULL,
    year INTEGER,
    service_history TEXT,
    client_id INTEGER,  -- Убрано NOT NULL
    FOREIGN KEY (client_id) REFERENCES clients(id_client) ON DELETE SET NULL
);
""")



# Создание таблицы ремонтов
cur.execute("""
CREATE TABLE IF NOT EXISTS repairs (
    id_repair INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    date TEXT NOT NULL,
    repair_type TEXT NOT NULL,
    start_price REAL NOT NULL,
    discount INTEGER,
    repair_status BOOLEAN NOT NULL,
    finish_price REAL, 
    car_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    public_key TEXT,  -- Добавлено поле для публичного ключа
    signature TEXT,   -- Добавлено поле для подписи
    FOREIGN KEY (car_id) REFERENCES cars(id_car) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id_client) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
""")

# Создание таблицы отчетов
cur.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    date TEXT NOT NULL,
    report_type TEXT NOT NULL,
    description TEXT,
    employee_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,  -- Начальная дата периода
    end_date TEXT NOT NULL,    -- Конечная дата периода
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
""")

# Добавление данных

# Сотрудники
employees = [
    ('Алексеев Дмитрий Сергеевич', 'alekseev@autoshop.ru', '80001112233', 'механик', 'ремонтный цех', 0),
    ('Борисова Анна Александровна', 'borisova@autoshop.ru', '80002223344', 'администратор', 'офис', 0),
    ('Васильев Алексей Иванович', 'vasilyev@autoshop.ru', '80003334455', 'мастер по двигателям', 'ремонтный цех', 1),
    ('Григорьева Ольга Викторовна', 'grigoreva@autoshop.ru', '80004445566', 'бухгалтер', 'офис', 0),
    ('Дмитриев Сергей Петрович', 'dmitriev@autoshop.ru', '80005556677', 'электрик', 'ремонтный цех', 2),
    ('Егорова Елена Михайловна', 'egorova@autoshop.ru', '80006667788', 'менеджер по продажам', 'офис', 0),
    ('Жуков Андрей Викторович', 'zhukov@autoshop.ru', '80007778899', 'моторист', 'ремонтный цех', 3),
    ('Зайцева Татьяна Ивановна', 'zaitseva@autoshop.ru', '80008889900', 'специалист по шиномонтажу', 'ремонтный цех', 4),
    ('Ильин Павел Александрович', 'ilin@autoshop.ru', '80009990011', 'мастер по кузовному ремонту', 'ремонтный цех', 5),
    ('Киселева Мария Дмитриевна', 'kiseleva@autoshop.ru', '80000001122', 'специалист по диагностике', 'ремонтный цех', 6)
]
cur.executemany("""
INSERT INTO employees (name, email, phone_number, position, department, chief_id) 
VALUES (?, ?, ?, ?, ?, ?)
""", employees)


# Клиенты
clients = [
    ('Александров Алексей Сергеевич', 'aleksandrov@ya.ru', '89151112233', '4051 111222', ),
    ('Борисов Владимир Иванович', 'borisov@ya.ru', '89152223344', '4052 222333'),
    ('Васильева Елена Петровна', 'vasileva@ya.ru', '89153334455', '4053 333444'),
    ('Григорьев Дмитрий Александрович', 'grigorev@ya.ru', '89154445566', '4054 444555'),
    ('Дмитриева Ольга Викторовна', 'dmitrieva@ya.ru', '89155556677', '4055 555666'),
    ('Егоров Сергей Иванович', 'egorov@ya.ru', '89156667788', '4056 666777'),
    ('Жукова Мария Александровна', 'zhukova@ya.ru', '89157778899', '4057 777888'),
    ('Ильин Алексей Дмитриевич', 'ilin@ya.ru', '89158889900', '4058 888999'),
    ('Киселев Павел Сергеевич', 'kiselev@ya.ru', '89159990011', '4059 999000'),
    ('Козлов Денис Викторович', 'kozlov@ya.ru', '89150001122', '4060 000111')
]
cur.executemany("""
INSERT INTO clients (name, email, phone_number, passport) 
VALUES (?, ?, ?, ?)
""", clients)

# Машины

cars = [
    ('Toyota', 'Camry', 'A111AA111', 2017, 'Замена масла и фильтров', 1),
    ('Ford', 'Mustang', 'B222BB222', 2018, 'Диагностика двигателя', 2),
    ('Hyundai', 'Tucson', 'C333CC333', 2019, 'Замена тормозных колодок', 3),
    ('Mazda', 'CX-9', 'D444DD444', 2020, 'Проблема с коробкой передач', 4),
    ('Kia', 'Optima', 'E555EE555', 2021, 'Техническое обслуживание', 5),
    ('Volkswagen', 'Golf', 'F666FF666', 2016, 'Ремонт подвески', 6),
    ('Renault', 'Duster', 'G777GG777', 2015, 'Замена аккумулятора', 7),
    ('Nissan', 'X-Trail', 'H888HH888', 2014, 'Ремонт кондиционера', 8),
    ('Skoda', 'Octavia', 'I999II999', 2013, 'Замена ремня ГРМ', 9),
    ('Honda', 'Civic', 'J000JJ000', 2012, 'Ремонт электросистемы', 10)
]
cur.executemany("""
INSERT INTO cars (car_brand, car_model, license_plate, year, service_history, client_id) 
VALUES (?, ?, ?, ?, ?, ?)
""", cars)


# Ремонты
repairs = [
    ('2024-1-РМ', '01.04.2024', 'Техническое обслуживание', 5000, 10, False, None, 1, 1, 1, None, None),
    ('2024-2-РМ', '02.04.2024', 'Диагностика двигателя', 10000, 5, False, None, 2, 2, 2, None, None),
    ('2024-3-РМ', '03.04.2024', 'Замена тормозов', 7000, 7, True, 6510, 3, 3, 3, None, None),
    ('2024-4-РМ', '04.04.2024', 'Ремонт КПП', 15000, 8, False, None, 4, 4, 4, None, None),
    ('2024-5-РМ', '05.04.2024', 'Обслуживание двигателя', 20000, 5, True, 19000, 5, 5, 5, None, None),
    ('2024-6-РМ', '06.04.2024', 'Ремонт подвески', 8000, 10, False, None, 6, 6, 6, None, None),
    ('2024-7-РМ', '07.04.2024', 'Замена аккумулятора', 3000, 0, True, 3000, 7, 7, 7, None, None),
    ('2024-8-РМ', '08.04.2024', 'Ремонт кондиционера', 12000, 15, False, None, 8, 8, 8, None, None),
    ('2024-9-РМ', '09.04.2024', 'Замена ремня ГРМ', 9000, 5, True, 8550, 9, 9, 9, None, None),
    ('2024-10-РМ', '10.04.2024', 'Ремонт электросистемы', 18000, 10, False, None, 10, 10, 10, None, None)
]
cur.executemany("""
INSERT INTO repairs (number, date, repair_type, start_price, discount, repair_status, finish_price, car_id, client_id, employee_id, public_key, signature) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", repairs)


# Пример данных для вставки
reports = [
    ('2024-01', '01.04.2024', 'Ежедневный отчет', 'Отчет по выполненным ТО', 1, '01.04.2024', '30.04.2024'),
    ('2024-02', '05.04.2024', 'Аналитический отчет', 'Отчет по ремонту двигателей', 2, '01.04.2000', '30.04.2040'),
    ('2024-03', '11.04.2024', 'Отчет по тормозной системе', 'Завершено 5 ремонтов тормозной системы', 3, '01.04.2024', '30.04.2024')
]
cur.executemany("""
INSERT INTO reports (number, date, report_type, description, employee_id, start_date, end_date) 
VALUES (?, ?, ?, ?, ?, ?, ?)
""", reports)

# Сохранение изменений и закрытие соединения
connection.commit()
connection.close()
