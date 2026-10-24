-- =====================================================================
-- МОДУЛЬ 1. Схема БД (SQLite), 3НФ.
-- >>> МЕНЯТЬ: справочники и поля под столбцы Excel-файлов варианта.
-- Правила: id INTEGER PRIMARY KEY; ссылка = что_id INTEGER NOT NULL REFERENCES таблица(id),
-- справочник = id + name TEXT NOT NULL UNIQUE; деньги и % — REAL, штуки — INTEGER;
-- после последнего поля запятой нет; после каждой таблицы — точка с запятой.
-- Порядок: сначала справочники, потом таблицы, которые на них ссылаются.
-- =====================================================================

CREATE TABLE role(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE category(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE manufacturer(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE supplier(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE order_status(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE pickup_point(
    id INTEGER PRIMARY KEY,
    address TEXT NOT NULL
);

-- >>> МЕНЯТЬ: столбцы товара = столбцы Tovar.xlsx; повторяющиеся значения -> ссылка на справочник
CREATE TABLE product(
    id INTEGER PRIMARY KEY,
    article TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    description TEXT,
    photo TEXT,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    discount REAL NOT NULL,
    category_id INTEGER NOT NULL REFERENCES category(id),
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturer(id),
    supplier_id INTEGER NOT NULL REFERENCES supplier(id)
);

CREATE TABLE users(
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role_id INTEGER NOT NULL REFERENCES role(id)
);

-- >>> МЕНЯТЬ: столбцы заказа = столбцы Заказ_import.xlsx
CREATE TABLE orders(
    id INTEGER PRIMARY KEY,
    order_date TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    pickup_code INTEGER NOT NULL,
    pickup_point_id INTEGER NOT NULL REFERENCES pickup_point(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    order_status_id INTEGER NOT NULL REFERENCES order_status(id)
);

-- состав заказа: связь «многие ко многим», составной первичный ключ
CREATE TABLE order_item(
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES product(id),
    quantity INTEGER NOT NULL,
    PRIMARY KEY(order_id, product_id)
);
