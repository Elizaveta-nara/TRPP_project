# TRPP_project

# Описание базы данных для системы управления документами и рабочими потоками

## Используемая база данных
В качестве базы данных будет использоваться **SQLite**. SQLite – это встраиваемая кроссплатформенная реляционная база данных.

## Структура таблиц

В подсистеме управления документами и рабочими потоками для автоматизации деятельности ремонтной мастерской будут определены следующие таблицы:

- **Сотрудники**
- **Клиенты**
- **Автомобили**
- **Договоры**
- **Отчеты**

### Таблица 1.1 – Создание таблиц базы данных

| Таблица      | SQL-запрос                                                                                                                                         |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Сотрудники   | ```sql CREATE TABLE IF NOT EXISTS 'employees' ( 'id_employee' INTEGER PRIMARY KEY AUTOINCREMENT, 'name' TEXT, 'email' TEXT, 'phone_number' TEXT, 'position' TEXT, 'department' TEXT, 'chief_id' INTEGER ) ``` |
| Клиенты      | ```sql CREATE TABLE IF NOT EXISTS 'clients' ( 'id_client' INTEGER PRIMARY KEY AUTOINCREMENT, 'name' TEXT, 'email' TEXT, 'phone_number' TEXT, 'passport' TEXT ) ``` |
| Автомобили   | ```sql CREATE TABLE IF NOT EXISTS 'cars' ( 'id_auto' INTEGER PRIMARY KEY AUTOINCREMENT, 'brand' TEXT, 'model' TEXT, 'year' INTEGER, 'license_plate' TEXT, 'service_history' TEXT, 'client_id' INTEGER ) ``` |
| Договоры     | ```sql CREATE TABLE IF NOT EXISTS 'repairs' ( 'id_contract' INTEGER PRIMARY KEY AUTOINCREMENT, 'number' TEXT, 'date' TEXT, 'deal_type' TEXT, 'start_price' INTEGER, 'discount' INTEGER, 'deal_status' TEXT, 'finish_price' INTEGER, 'auto_id' INTEGER, 'client_id' INTEGER, 'employee_id' INTEGER ) ``` |
| Отчеты       | ```sql CREATE TABLE IF NOT EXISTS 'reports' ( 'id_report' INTEGER PRIMARY KEY AUTOINCREMENT, 'number' TEXT, 'date' TEXT, 'report_type' TEXT, 'description' TEXT, 'employee_id' INTEGER ) ``` |

### Таблица 1.2 – Добавление данных в таблицы базы данных

| Таблица      | SQL-запрос                                                                                                                                         |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Сотрудники   | ```sql INSERT INTO 'employees' ('name', 'email', 'phone_number', 'position', 'department', 'chief_id') VALUES (?, ?, ?, ?, ?, ?) ```             |
| Клиенты      | ```sql INSERT INTO 'clients' ('name', 'email', 'phone_number', 'passport') VALUES (?, ?, ?, ?) ```                                              |
| Автомобили   | ```sql INSERT INTO 'cars' ('brand', 'model', 'year', 'license_plate', 'service_history', 'client_id') VALUES (?, ?, ?, ?, ?, ?) ```             |
| Договоры     | ```sql INSERT INTO 'repairs' ('number', 'date', 'deal_type', 'start_price', 'discount', 'deal_status', 'finish_price', 'auto_id', 'client_id', 'employee_id') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ``` |
| Отчеты       | ```sql INSERT INTO 'reports' ('number', 'date', 'report_type', 'description', 'employee_id') VALUES (?, ?, ?, ?, ?) ```                        |

### Таблица 1.3 – Выборка данных из базы данных

| Задача                                                                                                       | SQL-запрос                                                                                                                                                                                                 |
|--------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Получение данных о договоре, автомобиле, клиенте и сотруднике по ID ремонта                                 | ```sql SELECT repairs.*, cars.brand, cars.model, cars.license_plate, clients.name AS client_name, employees.name AS employee_name FROM repairs JOIN cars ON repairs.auto_id = cars.id_auto JOIN clients ON repairs.client_id = clients.id_client JOIN employees ON repairs.employee_id = employees.id_employee WHERE repairs.id_contract = ? ``` |
| Получение списка текущих договоров (в работе)                                                              | ```sql SELECT repairs.*, cars.brand, cars.model, cars.license_plate, clients.name AS client_name FROM repairs JOIN cars ON repairs.auto_id = cars.id_auto JOIN clients ON repairs.client_id = clients.id_client WHERE repairs.deal_status = 'в работе' ``` |
| Получение списка завершенных договоров (архив)                                                             | ```sql SELECT repairs.*, cars.brand, cars.model, cars.license_plate, clients.name AS client_name FROM repairs JOIN cars ON repairs.auto_id = cars.id_auto JOIN clients ON repairs.client_id = clients.id_client WHERE repairs.deal_status = 'завершен' ``` |
| Получение списка автомобилей                                                                                 | ```sql SELECT * FROM cars ```                                                                                                                                                                          |
| Получение данных о клиенте по ID клиента                                                                    | ```sql SELECT * FROM clients WHERE id_client = ? ```                                                                                                                                                   |
| Получение списка клиентов                                                                                   | ```sql SELECT id_client, name, email, phone_number, passport FROM clients ```                                                                                                                          |
| Получение списка сотрудников                                                                                 | ```sql SELECT id_employee, name, email, phone_number, position, department FROM employees ```                                                                                                          |
| Получение данных о сотруднике по ID сотрудника                                                              | ```sql SELECT id_employee, name, email, phone_number, position, department FROM employees WHERE id_employee = ? ```                                                                                  |
| Получение списка отчетов                                                                                     | ```sql SELECT reports.*, employees.name AS employee_name FROM reports JOIN employees ON reports.employee_id = employees.id_employee ```                                                                |
| Получение данных об отчете по ID отчета                                                                     | ```sql SELECT reports.*, employees.name AS employee_name FROM reports JOIN employees ON reports.employee_id = employees.id_employee WHERE reports.id_report = ? ```                                    |
| Получение данных о ремонтах за период для отчета                                                            | ```sql SELECT repairs.*, cars.brand, cars.model, cars.license_plate FROM repairs JOIN cars ON repairs.auto_id = cars.id_auto WHERE repairs.date BETWEEN ? AND ? AND repairs.employee_id = ? AND repairs.deal_status = 'завершен' ``` |
| Получение данных о ремонтах с фильтрами по сотруднику, клиенту и автомобилю                                 | ```sql SELECT repairs.*, cars.brand, cars.model, cars.license_plate, clients.name AS client_name, employees.name AS employee_name FROM repairs JOIN cars ON repairs.auto_id = cars.id_auto JOIN clients ON repairs.client_id = clients.id_client JOIN employees ON repairs.employee_id = employees.id_employee WHERE repairs.deal_status = 'в работе' ``` |

## Заключение
Данная структура базы данных позволяет эффективно управлять документами и рабочими процессами в ремонтной мастерской, обеспечивая хранение и обработку информации о сотрудниках, клиентах, автомобилях, договорах и отчетах.

# Реализованные HTML-страницы и функции-обработчики

## Таблица 1.4 – Реализованные шаблоны для отображения данных

| Шаблон      | Отображение                                                  |
|-------------|-------------------------------------------------------------|
| base.html   | базовый шаблон с реализацией навигационного меню           |
| 404.html     | страница для отображения ошибки 404 (страница не найдена)  |
| 500.html     | страница для отображения ошибки 500 (внутренняя ошибка сервера) |
| archive.html | страница для отображения архивных договоров (завершенных)  |
| cars.html    | страница для отображения списка автомобилей                 |
| client.html  | страница для отображения деталей конкретного клиента       |
| clients.html | страница для отображения списка клиентов                    |
| employee.html| страница для отображения деталей конкретного сотрудника    |
| employees.html| страница для отображения списка сотрудников                |
| repair.html  | страница для отображения деталей конкретного договора на ремонт |
| repairs.html | страница для отображения списка текущих договоров на ремонт |
| report.html  | страница для отображения деталей конкретного отчета       |
| reports.html | страница для отображения списка отчетов                    |

## Таблица 1.5 – Реализованные функции для отображения данных

| Маршрут                        | Функция              | Описание                                                    |
|--------------------------------|----------------------|-------------------------------------------------------------|
| /                              | index                | перенаправление на /repairs                                 |
| /repairs                       | repairs              | отображение страницы repairs.html                            |
| /repair/<int:repair_id>       | repair_details       | отображение страницы repair.html                             |
| /cars                          | cars                 | отображение страницы cars.html                               |
| /clients                       | clients_list         | отображение страницы clients.html                            |
| /client/<int:client_id>       | client_details       | отображение страницы client.html                             |
| /employees                     | employees            | отображение страницы employees.html                          |
| /employee/<int:employee_id>    | employee             | отображение страницы employee.html                           |
| /reports                       | reports              | отображение страницы reports.html                            |
| /report/<int:report_id>       | report               | отображение страницы report.html                             |
| /archive                       | archive              | отображение страницы archive.html                            |
| /404                           | page_not_found       | отображение страницы 404.html при ошибке 404               |
| /500                           | internal_error       | отображение страницы 500.html при ошибке 500               |

## Заключение

Данные шаблоны и функции обеспечивают удобное отображение и управление информацией в системе управления документами и рабочими потоками ремонтной мастерской, позволяя пользователям легко находить необходимую информацию и взаимодействовать с системой.
