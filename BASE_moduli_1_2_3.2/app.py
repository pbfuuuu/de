"""
МОДУЛИ 2 и 3.1–3.2: вход, список товаров с подсветкой, поиск/фильтр/сортировка.
Без формы добавления/редактирования (3.3–3.5) — она в папке FULL_moduli_1_2_3.
Запуск из этой папки после python import_data.py
"""
import sqlite3
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from tkinter import ttk


# =====================================================================
# НАСТРОЙКИ  >>> МЕНЯТЬ под вариант: стиль из Прил_3, пороги, названия
# =====================================================================
DB_PATH = 'my_shop.db'
FONT = ("Comic Sans MS", 11)                        # >>> МЕНЯТЬ: шрифт из Прил_3 (и в двух строках ниже)
FONT_BOLD = ('Comic Sans MS', 11, 'bold')
FONT_STRIKE = ('Comic Sans MS', 11, 'overstrike')
COLOR_MAIN = '#FFFFFF'              # >>> МЕНЯТЬ: основной фон (Прил_3)
COLOR_EXTRA = '#ABCFCE'             # >>> МЕНЯТЬ: дополнительный фон (шапка, панель)
COLOR_BIG_DISCOUNT = '#23E1EF'      # >>> МЕНЯТЬ: цвет подсветки большой скидки из задания
COLOR_OUT_OF_STOCK = "#D3D3D3"      # >>> МЕНЯТЬ: цвет «нет на складе» из задания
COLOR_ACCENT = '#546F94'            # >>> МЕНЯТЬ: акцент (кнопки)
BIG_DISCOUNT = 25                   # >>> МЕНЯТЬ: порог скидки из задания
IMPORT_DIR = '../import'            # папка с ресурсами заказчика (картинки, иконка)

# ---------- фильтр и сортировка (модуль 3.1–3.2)  >>> МЕНЯТЬ под вариант ----------
ALL_RANGES = 'Все диапазоны'        # >>> МЕНЯТЬ: первый пункт фильтра, как в задании
DISCOUNT_RANGES = {                 # >>> МЕНЯТЬ: подпись: (от, до) включительно
    '0-12,99 %': (0, 12.99),
    '13-16,99 %': (13, 16.99),
    '17 % и более': (17, 100)
}

NO_SORT = 'Без сортировки'
SORT_OPTIONS = {                    # >>> МЕНЯТЬ: подпись: (поле в БД, по убыванию?)
    "Цена: по возрастанию": ('price', False),
    "Цена: по убыванию": ('price', True),
    'Количество: по возрастанию': ('quantity', False),
    'Количество: по убыванию': ('quantity', True)
}


def filter_products(products, search_text, range_name, sort_name):
    """Поиск по всем текстовым полям + фильтр по скидке + сортировка."""
    words = search_text.lower().split()
    result = []
    for p in products:
        # весь текст товара одной строкой  >>> МЕНЯТЬ: поля поиска, если в варианте другие
        text = f"{p['article']} {p['name']} {p['description']} {p['category']} " \
               f"{p['manufacturer']} {p['supplier']} {p['unit']}".lower()
        if not all(word in text for word in words):
            continue
        # >>> МЕНЯТЬ: если фильтр по поставщику — вместо блока ниже:
        #     if range_name != ALL_RANGES and p['supplier'] != range_name: continue
        # а в списке фильтра: values=[ALL_RANGES] + [r[0] for r in
        #     sqlite3.connect(DB_PATH).execute('SELECT name FROM supplier').fetchall()]
        if range_name in DISCOUNT_RANGES:
            low, high = DISCOUNT_RANGES[range_name]
            if not (low <= p['discount'] <= high):
                continue
        result.append(p)

    if sort_name in SORT_OPTIONS:
        field, descending = SORT_OPTIONS[sort_name]
        result.sort(key=lambda p: p[field], reverse=descending)
    return result


def clear_window():
    for widget in root.winfo_children():
        widget.destroy()


def load_image(path, size):
    img = Image.open(path)
    img.thumbnail(size)
    return ImageTk.PhotoImage(img)


def load_products():
    """Все товары + названия справочников.  >>> МЕНЯТЬ: столбцы и JOIN под свою схему"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # обращение к столбцам по имени: product['price']
    rows = conn.execute(
        """SELECT product.id, product.article, product.name, product.unit, product.description,
                    product.photo, product.quantity, product.price, product.discount, 
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


def product_card(parent, product):
    """Карточка товара: фото слева, описание посередине, скидка справа."""
    # цвет фона: сначала остаток, потом скидка  >>> МЕНЯТЬ условия под задание
    # («превышает 25 %» -> знак >, «не менее 25 %» -> знак >=)
    if product["quantity"] == 0:
        bg = COLOR_OUT_OF_STOCK
    elif product["discount"] > BIG_DISCOUNT:
        bg = COLOR_BIG_DISCOUNT
    else:
        bg = COLOR_MAIN

    card = tk.Frame(parent, bg=bg, highlightbackground="black", highlightthickness=1)
    card.pack(fill="x", padx=10, pady=5)

    # нет фото -> заглушка picture.png
    if product["photo"]:
        photo_path = f"{IMPORT_DIR}/{product['photo']}"
    else:
        photo_path = f"{IMPORT_DIR}/picture.png"
    photo = load_image(photo_path, (150, 100))
    photo_label = tk.Label(card, image=photo, bg=bg)
    photo_label.image = photo           # иначе картинку удалит сборщик мусора
    photo_label.pack(side="left", padx=10, pady=5)

    # скидку ставим раньше описания: описание с expand=True забирает оставшееся место
    tk.Label(card, text=f"Действующая\nскидка\n{product['discount']:g} %",
             font=FONT_BOLD, bg=bg, width=12).pack(side="right", padx=10)

    info = tk.Frame(card, bg=bg)
    info.pack(side="left", fill="both", expand=True, pady=5)

    def add_line(text):
        tk.Label(info, text=text, font=FONT, bg=bg, anchor="w",
                 justify="left", wraplength=600).pack(fill="x")

    # >>> МЕНЯТЬ строки карточки под макет варианта
    add_line(f"{product['category']} | {product['name']}")
    add_line(f"Описание товара: {product['description'] or '—'}")
    add_line(f"Производитель: {product['manufacturer']}")
    add_line(f"Поставщик: {product['supplier']}")

    # цена: при скидке старая — красная зачёркнутая, рядом итоговая
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


def show_login():
    global login_entry, password_entry  # поля нужны функции login
    clear_window()
    root.title("ООО «ЧитайГород» — Вход")  # >>> МЕНЯТЬ название компании

    logo = load_image(f"{IMPORT_DIR}/icon.png", (200, 120))
    logo_label = tk.Label(root, image=logo, bg=COLOR_MAIN)
    logo_label.image = logo
    logo_label.pack(pady=(40, 0))

    form = tk.Frame(root, bg=COLOR_MAIN)
    form.pack(pady=30)

    tk.Label(form, text='Логин', font=FONT, bg=COLOR_MAIN).grid(row=0, column=0, sticky='w', pady=5)
    login_entry = tk.Entry(form, font=FONT, width=30)
    login_entry.grid(row=0, column=1, pady=5)

    tk.Label(form, text='Пароль', font=FONT, bg=COLOR_MAIN).grid(row=1, column=0, sticky='w', pady=5)
    password_entry = tk.Entry(form, font=FONT, width=30, show='*')
    password_entry.grid(row=1, column=1, pady=5)

    tk.Button(form, text='Войти', font=FONT, bg=COLOR_ACCENT,
              fg='white', command=login).grid(row=2, column=0, pady=15)
    tk.Button(form, text='Войти как гость', font=FONT, bg=COLOR_ACCENT,
              fg='white', command=login_as_guest).grid(row=2, column=1, pady=15)


def login():
    login_text = login_entry.get().strip()
    password_text = password_entry.get().strip()

    if not login_text or not password_text:
        messagebox.showwarning('Незаполненные поля', 'Введите логин и пароль.\nОба поля обязательные')
        return

    conn = sqlite3.connect(DB_PATH)
    # >>> МЕНЯТЬ имена таблиц/столбцов, если в схеме другие (users, role, login, password)
    user = conn.execute(
        """SELECT users.full_name, role.name
            FROM users
            JOIN role ON role.id = users.role_id
            WHERE users.login = ? AND users.password = ?""",
        (login_text, password_text),).fetchone()
    conn.close()

    if user is None:
        messagebox.showerror('Ошибка входа', 'Неверный логин или пароль.')
        return

    full_name, role = user
    show_product(full_name, role)


def login_as_guest():
    show_product('Гость', 'Гость')


def show_product(full_name, role):
    clear_window()
    root.title("ООО «ЧитайГород» — Список товаров")  # >>> МЕНЯТЬ название компании

    header = tk.Frame(root, bg=COLOR_EXTRA)
    header.pack(fill='x')

    # поиск/фильтр/сортировка только у этих ролей  >>> МЕНЯТЬ названия ролей как в user_import
    can_search = role in ('Администратор', 'Менеджер')
    search_var = tk.StringVar()
    range_var = tk.StringVar(value=ALL_RANGES)
    sort_var = tk.StringVar(value=NO_SORT)

    if can_search:
        bar = tk.Frame(root, bg=COLOR_EXTRA)
        bar.pack(fill='x', padx=10, pady=5)

        tk.Label(bar, text='Поиск', font=FONT, bg=COLOR_EXTRA).pack(side='left', padx=5)
        tk.Entry(bar, textvariable=search_var, font=FONT, width=25).pack(side='left', padx=5, pady=5)

        # >>> МЕНЯТЬ подпись фильтра (например, «Поставщик»)
        tk.Label(bar, text='Скидка', font=FONT, bg=COLOR_EXTRA).pack(side='left', padx=5)
        ttk.Combobox(bar, textvariable=range_var, state='readonly', font=FONT, width=14,
                     values=[ALL_RANGES] + list(DISCOUNT_RANGES)).pack(side='left', padx=5)

        tk.Label(bar, text='Сортировка', font=FONT, bg=COLOR_EXTRA).pack(side='left', padx=5)
        ttk.Combobox(bar, textvariable=sort_var, state='readonly', font=FONT, width=14,
                     values=[NO_SORT] + list(SORT_OPTIONS)).pack(side='left', padx=5)

    logo = load_image(f'{IMPORT_DIR}/icon.png', (120, 60))
    logo_label = tk.Label(header, image=logo, bg=COLOR_EXTRA)
    logo_label.image = logo
    logo_label.pack(side='left', padx=10, pady=5)

    tk.Label(header, text='Список товаров', font=FONT_BOLD, bg=COLOR_EXTRA).pack(side='left', padx=10, pady=10)
    tk.Button(header, text='Выйти', font=FONT, bg=COLOR_ACCENT, fg='white',
              command=show_login).pack(side='right', padx=10)
    tk.Label(header, text=full_name, font=FONT, bg=COLOR_EXTRA).pack(side='right', padx=10)

    # прокрутка: рецепт Canvas + Scrollbar + Frame, копировать как есть
    canvas = tk.Canvas(root, bg=COLOR_MAIN, highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient='vertical', command=canvas.yview)
    list_frame = tk.Frame(canvas, bg=COLOR_MAIN)
    window_id = canvas.create_window((0, 0), window=list_frame, anchor='nw')

    list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window_id, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    root.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(-1 * (e.delta // 120), 'units'))

    scrollbar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)

    all_products = load_products()

    def refresh(*args):
        """Перерисовывает список с учётом поиска, фильтра и сортировки."""
        for widget in list_frame.winfo_children():
            widget.destroy()
        for product in filter_products(all_products, search_var.get(), range_var.get(), sort_var.get()):
            product_card(list_frame, product)

    # любое изменение поиска, фильтра или сортировки сразу обновляет список
    for var in (search_var, range_var, sort_var):
        var.trace_add('write', refresh)

    refresh()


# =====================================================================
# ЗАПУСК
# =====================================================================
root = tk.Tk()
root.geometry('1000x700')
root.configure(bg=COLOR_MAIN)
icon = tk.PhotoImage(file=f'{IMPORT_DIR}/icon.png')
root.iconphoto(True, icon)

show_login()
root.mainloop()
