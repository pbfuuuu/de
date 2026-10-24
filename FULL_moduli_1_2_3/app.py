"""
Модули 2 и 3. Приложение магазина: вход по ролям, список товаров,
поиск/фильтр/сортировка, добавление, редактирование и удаление товаров.
"""
import os
import shutil
import sqlite3
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

# =====================================================================
# НАСТРОЙКИ  >>> МЕНЯТЬ под вариант: стиль из Прил_3, пороги, названия
# =====================================================================
DB_PATH = "my_shop.db"
IMPORT_DIR = "../import"          # папка с ресурсами заказчика (фото, логотип, заглушка)
IMAGES_DIR = "images"             # сюда сохраняются фото, загруженные администратором
COMPANY = "ООО «ЧитайГород»"      # >>> МЕНЯТЬ: название компании в заголовках окон

FONT = ("Comic Sans MS", 11)                      # >>> МЕНЯТЬ: шрифт из Прил_3
FONT_BOLD = ("Comic Sans MS", 11, "bold")
FONT_STRIKE = ("Comic Sans MS", 11, "overstrike")
COLOR_MAIN = "#FFFFFF"            # >>> МЕНЯТЬ: основной фон
COLOR_EXTRA = "#ABCFCE"           # >>> МЕНЯТЬ: дополнительный фон
COLOR_ACCENT = "#546F94"          # >>> МЕНЯТЬ: акцент (кнопки)
COLOR_BIG_DISCOUNT = "#23E1EF"    # >>> МЕНЯТЬ: цвет большой скидки
COLOR_OUT_OF_STOCK = "#D3D3D3"    # >>> МЕНЯТЬ: цвет «нет на складе»
COLOR_ERROR = "#FFD6D6"           # подсветка поля с ошибкой ввода
BIG_DISCOUNT = 25                 # >>> МЕНЯТЬ: порог («превышает 25 %» -> знак >)

ROLE_ADMIN = "Администратор"      # >>> МЕНЯТЬ: названия ролей как в user_import
ROLE_MANAGER = "Менеджер"

# ---------- фильтр и сортировка (модуль 3)  >>> МЕНЯТЬ под вариант ----------
ALL_RANGES = "Все диапазоны"
DISCOUNT_RANGES = {               # подпись: (от, до) включительно
    "0–12,99 %": (0, 12.99),
    "13–16,99 %": (13, 16.99),
    "17 % и более": (17, 100),
}
NO_SORT = "Без сортировки"
SORT_OPTIONS = {                  # подпись: (поле, по убыванию?)
    "Цена: по возрастанию": ("price", False),
    "Цена: по убыванию": ("price", True),
    "Количество: по возрастанию": ("quantity", False),
    "Количество: по убыванию": ("quantity", True),
}

edit_window = None                # открытое окно редактирования (может быть только одно)
refresh_list = None               # функция перерисовки списка, задаётся в show_product


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =====================================================================
def clear_window():
    """Удаляет из главного окна всё, чтобы нарисовать другой экран."""
    for widget in root.winfo_children():
        widget.destroy()


def load_image(path, size):
    """Открывает картинку и уменьшает её до size, сохраняя пропорции."""
    img = Image.open(path)
    img.thumbnail(size)
    return ImageTk.PhotoImage(img)


def photo_path(photo):
    """Путь к фото товара: сначала ищем среди загруженных админом, потом в ресурсах.
    Если фото нет — заглушка picture.png."""
    if photo and os.path.exists(os.path.join(IMAGES_DIR, photo)):
        return os.path.join(IMAGES_DIR, photo)
    if photo and os.path.exists(os.path.join(IMPORT_DIR, photo)):
        return os.path.join(IMPORT_DIR, photo)
    return os.path.join(IMPORT_DIR, "picture.png")


def load_products():
    """Все товары вместе с названиями категории, производителя и поставщика."""
    # >>> МЕНЯТЬ: столбцы и JOIN под свою схему (какие справочники у товара)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # обращение к столбцам по имени: product["price"]
    rows = conn.execute(
        """SELECT product.id, product.article, product.name, product.unit, product.description,
                  product.photo, product.quantity, product.price, product.discount,
                  product.category_id, product.manufacturer_id, product.supplier_id,
                  category.name AS category,
                  manufacturer.name AS manufacturer,
                  supplier.name AS supplier
           FROM product
           JOIN category ON category.id = product.category_id
           JOIN manufacturer ON manufacturer.id = product.manufacturer_id
           JOIN supplier ON supplier.id = product.supplier_id"""
    ).fetchall()
    conn.close()
    return rows


def load_dictionary(table):
    """Справочник (category / manufacturer / supplier) -> список (id, name)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(f"SELECT id, name FROM {table} ORDER BY name").fetchall()
    conn.close()
    return rows


def filter_products(products, search_text, range_name, sort_name):
    """Отбирает товары по поиску и диапазону скидки, затем сортирует."""
    words = search_text.lower().split()
    result = []
    for p in products:
        # весь текст товара одной строкой, чтобы искать сразу по всем полям
        # >>> МЕНЯТЬ: перечислить все текстовые поля товара своего варианта
        text = f"{p['article']} {p['name']} {p['description']} {p['category']} " \
               f"{p['manufacturer']} {p['supplier']} {p['unit']}".lower()
        if not all(word in text for word in words):
            continue
        # >>> МЕНЯТЬ: если фильтр по поставщику — вместо блока ниже:
        #     if range_name != ALL_RANGES and p['supplier'] != range_name: continue
        # а в списке фильтра: values=[ALL_RANGES] + [name for _, name in load_dictionary('supplier')]
        if range_name in DISCOUNT_RANGES:
            low, high = DISCOUNT_RANGES[range_name]
            if not (low <= p["discount"] <= high):
                continue
        result.append(p)

    if sort_name in SORT_OPTIONS:
        field, descending = SORT_OPTIONS[sort_name]
        result.sort(key=lambda p: p[field], reverse=descending)
    return result


# =====================================================================
# МОДУЛЬ 2. КАРТОЧКА ТОВАРА С ПОДСВЕТКОЙ
# =====================================================================
def product_card(parent, product, on_click=None):
    """Рисует одну карточку: фото слева, описание посередине, скидка справа."""
    # цвет фона: сначала остаток, потом скидка  >>> МЕНЯТЬ условия под вариант
    if product["quantity"] == 0:
        bg = COLOR_OUT_OF_STOCK
    elif product["discount"] > BIG_DISCOUNT:
        bg = COLOR_BIG_DISCOUNT
    else:
        bg = COLOR_MAIN

    card = tk.Frame(parent, bg=bg, highlightbackground="black", highlightthickness=1)
    card.pack(fill="x", padx=10, pady=5)

    photo = load_image(photo_path(product["photo"]), (150, 100))
    photo_label = tk.Label(card, image=photo, bg=bg)
    photo_label.image = photo          # иначе картинку удалит сборщик мусора
    photo_label.pack(side="left", padx=10, pady=5)

    # скидку ставим раньше описания: описание с expand=True забирает оставшееся место
    tk.Label(card, text=f"Действующая\nскидка\n{product['discount']:g} %",
             font=FONT_BOLD, bg=bg, width=12).pack(side="right", padx=10)

    info = tk.Frame(card, bg=bg)
    info.pack(side="left", fill="both", expand=True, pady=5)

    def add_line(text):
        tk.Label(info, text=text, font=FONT, bg=bg, anchor="w",
                 justify="left", wraplength=600).pack(fill="x")

    # >>> МЕНЯТЬ строки карточки под макет варианта (Прил. к заданию)
    add_line(f"{product['category']} | {product['name']}")
    add_line(f"Описание товара: {product['description'] or '—'}")
    add_line(f"Производитель: {product['manufacturer']}")
    add_line(f"Поставщик: {product['supplier']}")

    # цена: при скидке старая — красная и зачёркнутая, рядом итоговая
    price_row = tk.Frame(info, bg=bg)
    price_row.pack(fill="x")
    tk.Label(price_row, text="Цена:", font=FONT, bg=bg).pack(side="left")
    if product["discount"] > 0:
        final_price = product["price"] * (100 - product["discount"]) / 100
        tk.Label(price_row, text=f"{product['price']:.2f}", font=FONT_STRIKE,
                 fg="red", bg=bg).pack(side="left", padx=5)
        tk.Label(price_row, text=f"{final_price:.2f}", font=FONT,
                 fg="black", bg=bg).pack(side="left")
    else:
        tk.Label(price_row, text=f"{product['price']:.2f}", font=FONT,
                 bg=bg).pack(side="left", padx=5)

    add_line(f"Единица измерения: {product['unit']}")
    add_line(f"Количество на складе: {product['quantity']}")

    if on_click is not None:            # администратор: клик по карточке открывает редактирование
        bind_click(card, on_click)


def bind_click(widget, handler):
    """Вешает обработчик клика на виджет и на всё, что внутри него."""
    widget.bind("<Button-1>", lambda e: handler())
    widget.configure(cursor="hand2")
    for child in widget.winfo_children():
        bind_click(child, handler)


# =====================================================================
# МОДУЛЬ 2. ВХОД
# =====================================================================
def show_login():
    global login_entry, password_entry   # поля нужны функции login
    clear_window()
    root.title(f"{COMPANY} — Вход")

    logo = load_image(f"{IMPORT_DIR}/icon.png", (200, 120))
    logo_label = tk.Label(root, image=logo, bg=COLOR_MAIN)
    logo_label.image = logo
    logo_label.pack(pady=(40, 0))

    form = tk.Frame(root, bg=COLOR_MAIN)
    form.pack(pady=30)

    tk.Label(form, text="Логин", font=FONT, bg=COLOR_MAIN).grid(row=0, column=0, sticky="w", pady=5)
    login_entry = tk.Entry(form, font=FONT, width=30)
    login_entry.grid(row=0, column=1, pady=5)

    tk.Label(form, text="Пароль", font=FONT, bg=COLOR_MAIN).grid(row=1, column=0, sticky="w", pady=5)
    password_entry = tk.Entry(form, font=FONT, width=30, show="*")
    password_entry.grid(row=1, column=1, pady=5)

    tk.Button(form, text="Войти", font=FONT, bg=COLOR_ACCENT, fg="white",
              command=login).grid(row=2, column=0, pady=15)
    tk.Button(form, text="Войти как гость", font=FONT, bg=COLOR_ACCENT, fg="white",
              command=login_as_guest).grid(row=2, column=1, pady=15)


def login():
    login_text = login_entry.get().strip()
    password_text = password_entry.get().strip()

    if not login_text or not password_text:
        messagebox.showwarning("Незаполненные поля",
                               "Введите логин и пароль.\nОба поля обязательны.")
        return

    conn = sqlite3.connect(DB_PATH)
    # >>> МЕНЯТЬ имена таблиц/столбцов, если в схеме другие (users, role, login, password)
    user = conn.execute(
        """SELECT users.full_name, role.name
           FROM users
           JOIN role ON role.id = users.role_id
           WHERE users.login = ? AND users.password = ?""",
        (login_text, password_text),
    ).fetchone()
    conn.close()

    if user is None:
        messagebox.showerror("Ошибка входа",
                             "Неверный логин или пароль.\nПроверьте раскладку клавиатуры и Caps Lock.")
        return

    full_name, role = user
    show_product(full_name, role)


def login_as_guest():
    show_product("Гость", "Гость")


# =====================================================================
# МОДУЛИ 2–3. ЭКРАН СПИСКА ТОВАРОВ
# =====================================================================
def show_product(full_name, role):
    global refresh_list
    clear_window()
    root.title(f"{COMPANY} — Список товаров")
    is_admin = role == ROLE_ADMIN
    can_search = role in (ROLE_ADMIN, ROLE_MANAGER)

    # ---------- шапка: логотип, заголовок, ФИО справа, выход ----------
    header = tk.Frame(root, bg=COLOR_EXTRA)
    header.pack(fill="x")

    logo = load_image(f"{IMPORT_DIR}/icon.png", (120, 60))
    logo_label = tk.Label(header, image=logo, bg=COLOR_EXTRA)
    logo_label.image = logo
    logo_label.pack(side="left", padx=10, pady=5)

    # >>> МЕНЯТЬ подпись, если в задании объект другой (например, «Список услуг»)
    tk.Label(header, text="Список товаров", font=FONT_BOLD, bg=COLOR_EXTRA).pack(side="left", padx=10, pady=10)
    tk.Button(header, text="Выйти", font=FONT, bg=COLOR_ACCENT, fg="white",
              command=show_login).pack(side="right", padx=10)
    tk.Label(header, text=full_name, font=FONT, bg=COLOR_EXTRA).pack(side="right", padx=10)

    # ---------- панель поиска/фильтра/сортировки (менеджер и администратор) ----------
    search_var = tk.StringVar()
    range_var = tk.StringVar(value=ALL_RANGES)
    sort_var = tk.StringVar(value=NO_SORT)

    if can_search:
        bar = tk.Frame(root, bg=COLOR_EXTRA)
        bar.pack(fill="x", padx=10, pady=5)

        tk.Label(bar, text="Поиск:", font=FONT, bg=COLOR_EXTRA).pack(side="left", padx=5)
        tk.Entry(bar, textvariable=search_var, font=FONT, width=22).pack(side="left", padx=5, pady=5)

        # >>> МЕНЯТЬ подпись фильтра (например, «Поставщик:»)
        tk.Label(bar, text="Скидка:", font=FONT, bg=COLOR_EXTRA).pack(side="left", padx=5)
        ttk.Combobox(bar, textvariable=range_var, state="readonly", font=FONT, width=14,
                     values=[ALL_RANGES] + list(DISCOUNT_RANGES)).pack(side="left", padx=5)

        tk.Label(bar, text="Сортировка:", font=FONT, bg=COLOR_EXTRA).pack(side="left", padx=5)
        ttk.Combobox(bar, textvariable=sort_var, state="readonly", font=FONT, width=24,
                     values=[NO_SORT] + list(SORT_OPTIONS)).pack(side="left", padx=5)

        if is_admin:
            tk.Button(bar, text="Добавить товар", font=FONT, bg=COLOR_ACCENT, fg="white",
                      command=lambda: open_product_form(None)).pack(side="right", padx=5)

    # ---------- прокручиваемая область (рецепт: Canvas + Scrollbar + Frame) ----------
    canvas = tk.Canvas(root, bg=COLOR_MAIN, highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    list_frame = tk.Frame(canvas, bg=COLOR_MAIN)
    window_id = canvas.create_window((0, 0), window=list_frame, anchor="nw")

    list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    def refresh(*args):
        """Заново читает товары из БД и рисует их с учётом поиска, фильтра и сортировки."""
        for widget in list_frame.winfo_children():
            widget.destroy()
        for product in filter_products(load_products(), search_var.get(), range_var.get(), sort_var.get()):
            if is_admin:
                # p=product фиксирует текущий товар для каждой карточки
                product_card(list_frame, product, on_click=lambda p=product: open_product_form(p["id"]))
            else:
                product_card(list_frame, product)

    # любое изменение поиска, фильтра или сортировки сразу обновляет список
    for var in (search_var, range_var, sort_var):
        var.trace_add("write", refresh)

    refresh_list = refresh             # чтобы форма товара могла обновить список после сохранения
    refresh()


# =====================================================================
# МОДУЛЬ 3. ФОРМА ДОБАВЛЕНИЯ / РЕДАКТИРОВАНИЯ / УДАЛЕНИЯ ТОВАРА
# =====================================================================
def open_product_form(product_id):
    """product_id = None — добавление, число — редактирование."""
    global edit_window
    # нельзя открыть второе окно редактирования
    if edit_window is not None and edit_window.winfo_exists():
        messagebox.showwarning("Окно уже открыто",
                               "Сначала сохраните или закройте открытое окно редактирования товара.")
        edit_window.lift()
        return

    product = None
    if product_id is not None:
        product = next((p for p in load_products() if p["id"] == product_id), None)

    categories = load_dictionary("category")          # >>> МЕНЯТЬ имена таблиц-справочников
    manufacturers = load_dictionary("manufacturer")
    suppliers = load_dictionary("supplier")

    win = tk.Toplevel(root)                            # отдельное окно поверх главного
    edit_window = win
    title = "Редактирование товара" if product else "Добавление товара"
    win.title(f"{COMPANY} — {title}")
    win.configure(bg=COLOR_MAIN)
    win.geometry("760x640")

    head = tk.Frame(win, bg=COLOR_EXTRA)
    head.pack(fill="x")
    tk.Label(head, text=title, font=FONT_BOLD, bg=COLOR_EXTRA).pack(side="left", padx=10, pady=10)
    tk.Button(head, text="Назад", font=FONT, bg=COLOR_ACCENT, fg="white",
              command=win.destroy).pack(side="right", padx=10)

    body = tk.Frame(win, bg=COLOR_MAIN)
    body.pack(fill="both", expand=True, padx=15, pady=10)
    form = tk.Frame(body, bg=COLOR_MAIN)
    form.pack(side="left", fill="y")

    row = 0

    def add_entry(label, hint=""):
        """Подпись + поле ввода + серая подсказка о формате под полем."""
        nonlocal row
        tk.Label(form, text=label, font=FONT, bg=COLOR_MAIN).grid(row=row, column=0, sticky="nw", pady=2)
        cell = tk.Frame(form, bg=COLOR_MAIN)
        cell.grid(row=row, column=1, sticky="w", pady=2)
        entry = tk.Entry(cell, font=FONT, width=30)
        entry.pack(anchor="w")
        if hint:
            tk.Label(cell, text=hint, font=("Comic Sans MS", 9), fg="gray40", bg=COLOR_MAIN).pack(anchor="w")
        row += 1
        return entry

    def add_combo(label, items):
        """Подпись + выпадающий список значений из справочника."""
        nonlocal row
        tk.Label(form, text=label, font=FONT, bg=COLOR_MAIN).grid(row=row, column=0, sticky="w", pady=2)
        box = ttk.Combobox(form, values=[name for _, name in items], state="readonly", font=FONT, width=28)
        box.grid(row=row, column=1, sticky="w", pady=2)
        row += 1
        return box

    # ID: при добавлении не показываем, при редактировании — только чтение
    if product:
        id_entry = add_entry("ID")
        id_entry.insert(0, str(product["id"]))
        id_entry.config(state="readonly")

    # >>> МЕНЯТЬ набор полей под вариант (как в задании)
    article_entry = add_entry("Артикул *")
    name_entry = add_entry("Наименование *")
    category_box = add_combo("Категория *", categories)
    manufacturer_box = add_combo("Производитель *", manufacturers)
    supplier_box = add_combo("Поставщик *", suppliers)
    price_entry = add_entry("Цена, руб. *", "число ≥ 0, например 499.90")
    unit_entry = add_entry("Единица измерения *")
    quantity_entry = add_entry("Количество на складе *", "целое число ≥ 0")
    discount_entry = add_entry("Скидка, % *", "от 0 до 100")

    tk.Label(form, text="Описание", font=FONT, bg=COLOR_MAIN).grid(row=row, column=0, sticky="nw", pady=2)
    description_text = tk.Text(form, font=FONT, width=30, height=4, wrap="word")
    description_text.grid(row=row, column=1, sticky="w", pady=2)

    # ---------- фото справа (модуль 3.4) ----------
    side = tk.Frame(body, bg=COLOR_MAIN)
    side.pack(side="right", fill="y", padx=(15, 0))
    photo_label = tk.Label(side, bg=COLOR_MAIN, highlightthickness=1, highlightbackground="black")
    photo_label.pack(pady=5)
    new_photo = {"path": None}         # выбранный, но ещё не сохранённый файл

    def show_photo():
        path = new_photo["path"] or photo_path(product["photo"] if product else None)
        image = load_image(path, (300, 200))
        photo_label.config(image=image)
        photo_label.image = image

    def choose_photo():
        path = filedialog.askopenfilename(parent=win, title="Выберите фото товара",
                                          filetypes=[("Изображения", "*.png *.jpg *.jpeg")])
        if path:
            new_photo["path"] = path
            show_photo()

    tk.Button(side, text="Выбрать фото", font=FONT, bg=COLOR_ACCENT, fg="white",
              command=choose_photo).pack(fill="x", pady=3)

    # ---------- заполняем поля при редактировании  >>> МЕНЯТЬ вместе с набором полей ----------
    if product:
        article_entry.insert(0, product["article"])
        name_entry.insert(0, product["name"])
        category_box.set(product["category"])
        manufacturer_box.set(product["manufacturer"])
        supplier_box.set(product["supplier"])
        price_entry.insert(0, f"{product['price']:.2f}")
        unit_entry.insert(0, product["unit"])
        quantity_entry.insert(0, str(product["quantity"]))
        discount_entry.insert(0, f"{product['discount']:g}")
        description_text.insert("1.0", product["description"] or "")
    else:
        unit_entry.insert(0, "шт.")
        discount_entry.insert(0, "0")
    show_photo()

    # ---------- проверка и сохранение ----------
    def mark(widget, ok):
        """Визуальная подсказка: поле с ошибкой подсвечивается розовым."""
        if isinstance(widget, ttk.Combobox):
            return
        widget.config(bg="white" if ok else COLOR_ERROR)

    def to_number(text, kind):
        try:
            return kind(text.strip().replace(",", "."))
        except ValueError:
            return None

    def id_by_name(items, name):
        return next((item_id for item_id, item_name in items if item_name == name), None)

    def save():
        errors = []

        def check(widget, ok, message):
            mark(widget, ok)
            if not ok:
                errors.append("• " + message)

        # >>> МЕНЯТЬ проверки под поля своего варианта (что обязательно, какие числа)
        article = article_entry.get().strip()
        name = name_entry.get().strip()
        unit = unit_entry.get().strip()
        price = to_number(price_entry.get(), float)
        quantity = to_number(quantity_entry.get(), int)
        discount = to_number(discount_entry.get(), float)

        check(article_entry, bool(article), "Заполните поле «Артикул».")
        check(name_entry, bool(name), "Заполните поле «Наименование».")
        check(category_box, bool(category_box.get()), "Выберите категорию из списка.")
        check(manufacturer_box, bool(manufacturer_box.get()), "Выберите производителя из списка.")
        check(supplier_box, bool(supplier_box.get()), "Выберите поставщика из списка.")
        check(price_entry, price is not None and price >= 0, "Цена — число не меньше 0, например 499.90.")
        check(unit_entry, bool(unit), "Заполните поле «Единица измерения».")
        check(quantity_entry, quantity is not None and quantity >= 0,
              "Количество — целое число не меньше 0.")
        check(discount_entry, discount is not None and 0 <= discount <= 100,
              "Скидка — число от 0 до 100.")

        if errors:
            messagebox.showerror("Ошибка ввода данных",
                                 "Товар не сохранён. Исправьте поля, подсвеченные розовым:\n\n"
                                 + "\n".join(errors), parent=win)
            return

        old_photo = product["photo"] if product else None
        photo = old_photo
        if new_photo["path"]:
            # 3.4: фото уменьшаем до 300x200 и сохраняем в папку приложения
            os.makedirs(IMAGES_DIR, exist_ok=True)
            photo = f"product_{int(time.time())}.png"
            img = Image.open(new_photo["path"])
            img.thumbnail((300, 200))
            img.save(os.path.join(IMAGES_DIR, photo))

        # >>> МЕНЯТЬ: порядок значений = порядок столбцов в INSERT и UPDATE ниже
        values = (article, name, unit, description_text.get("1.0", "end").strip() or None, photo,
                  quantity, round(price, 2), discount,
                  id_by_name(categories, category_box.get()),
                  id_by_name(manufacturers, manufacturer_box.get()),
                  id_by_name(suppliers, supplier_box.get()))
        conn = sqlite3.connect(DB_PATH)
        if product is None:
            # ID при добавлении = максимальный в БД + 1
            new_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM product").fetchone()[0]
            conn.execute(
                """INSERT INTO product (id, article, name, unit, description, photo, quantity, price,
                                        discount, category_id, manufacturer_id, supplier_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (new_id,) + values)
        else:
            conn.execute(
                """UPDATE product SET article = ?, name = ?, unit = ?, description = ?, photo = ?,
                                      quantity = ?, price = ?, discount = ?, category_id = ?,
                                      manufacturer_id = ?, supplier_id = ?
                   WHERE id = ?""", values + (product["id"],))
        conn.commit()
        conn.close()

        # 3.4: старое фото удаляем, только если оно было загружено в папку приложения
        if new_photo["path"] and old_photo and os.path.exists(os.path.join(IMAGES_DIR, old_photo)):
            os.remove(os.path.join(IMAGES_DIR, old_photo))

        messagebox.showinfo("Сохранено", "Данные товара сохранены.", parent=win)
        win.destroy()
        refresh_list()

    # ---------- 3.5: удаление ----------
    def delete():
        conn = sqlite3.connect(DB_PATH)
        # >>> МЕНЯТЬ имя таблицы состава заказа, если другое
        in_orders = conn.execute("SELECT COUNT(*) FROM order_item WHERE product_id = ?",
                                 (product["id"],)).fetchone()[0]
        if in_orders:
            conn.close()
            messagebox.showerror("Удаление невозможно",
                                 "Этот товар есть в заказах, поэтому его нельзя удалить.", parent=win)
            return
        if not messagebox.askyesno("Подтверждение удаления",
                                   f"Удалить товар «{product['name']}»?\nЭто действие нельзя отменить.",
                                   icon="warning", parent=win):
            conn.close()
            return
        conn.execute("DELETE FROM product WHERE id = ?", (product["id"],))
        conn.commit()
        conn.close()
        messagebox.showinfo("Удалено", "Товар удалён.", parent=win)
        win.destroy()
        refresh_list()

    buttons = tk.Frame(win, bg=COLOR_EXTRA)
    buttons.pack(fill="x", side="bottom")
    tk.Button(buttons, text="Сохранить", font=FONT, bg=COLOR_ACCENT, fg="white",
              command=save).pack(side="left", padx=15, pady=8)
    if product:
        tk.Button(buttons, text="Удалить товар", font=FONT, bg=COLOR_ACCENT, fg="white",
                  command=delete).pack(side="left", pady=8)


# =====================================================================
# ЗАПУСК
# =====================================================================
root = tk.Tk()
root.geometry("1100x720")
root.configure(bg=COLOR_MAIN)
icon = tk.PhotoImage(file=f"{IMPORT_DIR}/icon.png")
root.iconphoto(True, icon)

show_login()
root.mainloop()
