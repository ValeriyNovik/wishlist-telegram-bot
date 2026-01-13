  #подключение к БД (cursor - объект для выполнения sql- команд
import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

  #создание таблицы Бд
def init_db():
    with open("create_tables.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    conn.commit()

    #добавить пользователя (insert or ignore - вставка данных, без падения при вводе дублирующихся данных (дубликат записан не будет) (прим. повторная попытка авторизоваться)
    # insert into - создание новой строки в таблице
def add_user(tg_id, tg_username, display_name):
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id, telegram_username, display_name) VALUES (?, ?, ?)",
        (tg_id, tg_username, display_name)
    )
    conn.commit()

    #select - взять определенный столбец из таблицы
    #from - из какой таблицы взять данные 
    #where - фильтр (какие строки попадут в запрос)
def get_user_by_tg(tg_id):
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
    return cursor.fetchone()


def add_wish(user_id, description, link, price):
    cursor.execute(
        "INSERT INTO wishes (user_id, description, link, price) VALUES (?, ?, ?, ?)",
        (user_id, description, link, price)
    )
    conn.commit()

    #order by - сортировка; desc - от наиб. к наим.
def get_wishes(user_id):
    cursor.execute(
        "SELECT description, link, price FROM wishes WHERE user_id = ? ORDER BY rowid DESC",
        (user_id,)
    )
    return cursor.fetchall()


    # получить желания вместе с id
def get_wishes_with_id(user_id):
    cursor.execute(
        "SELECT id, description, link, price FROM wishes WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    )
    return cursor.fetchall()


    # удаляем желание по wish_id 
def delete_wish(user_id, wish_id):
    cursor.execute(
        "DELETE FROM wishes WHERE id = ? AND user_id = ?",
        (wish_id, user_id)
    )
    conn.commit()
    return cursor.rowcount

    # ? заполнится позже реальным значением (защита от sql-инъекции) 
def create_group(name, code):
    cursor.execute(
        "INSERT INTO groups (name, invite_code) VALUES (?, ?)",
        (name, code)
    )
    conn.commit()


def get_group_by_code(code):
    cursor.execute("SELECT * FROM groups WHERE invite_code = ?", (code,))
    return cursor.fetchone()


def add_user_to_group(group_id, user_id, group_username):
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, group_username) VALUES (?, ?, ?)",
        (group_id, user_id, group_username)
    )
    conn.commit()


def get_group_users(group_id):
    cursor.execute(
        "SELECT group_username, user_id FROM group_members WHERE group_id = ?",
        (group_id,)
    )
    return cursor.fetchall()


def get_user_groups(user_id):
    cursor.execute(
        "SELECT group_id FROM group_members WHERE user_id = ?",
        (user_id,)
    )
    return [row[0] for row in cursor.fetchall()]

    #join-запросы - используются для объединения строк из двух или более таблиц на основе связанных столбцов, создавая единый результирующий набор данных из разрозненной информации ("мост" между таблицами)
    #проверка, есть ли группа у 2 пользователей 
def users_have_common_group(user1_id, user2_id):
    cursor.execute("""
        SELECT 1
        FROM group_members gm1
        JOIN group_members gm2
        ON gm1.group_id = gm2.group_id
        WHERE gm1.user_id = ? AND gm2.user_id = ?
        LIMIT 1
    """, (user1_id, user2_id))

    return cursor.fetchone() is not None

    #возвращение групп пользователя
def get_groups_for_user(user_id):
    cursor.execute("""
        SELECT g.id, g.name
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    return cursor.fetchall()

    #показать список пользователей в группе
def get_users_in_group(group_id):
    cursor.execute("""
        SELECT gm.group_username, u.id
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
    """, (group_id,))
    return cursor.fetchall()


def get_group_by_id(group_id: int):
    cursor.execute("SELECT id, name, invite_code FROM groups WHERE id = ?", (group_id,))
    return cursor.fetchone()

    #select 1 - проверка факта существования данных (строки)
    #limit 1 - после нахождения нужной строки, производится остановка поиска
def is_user_in_group(group_id: int, user_id: int) -> bool:
    cursor.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ? LIMIT 1",
        (group_id, user_id)
    )
    return cursor.fetchone() is not None

    
def group_username_exists(group_id: int, group_username: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND group_username = ? LIMIT 1",
        (group_id, group_username)
    )
    return cursor.fetchone() is not None


def make_unique_group_username(group_id: int, base: str) -> str:
    base = (base or "user").strip()
    candidate = base
    i = 2
    while group_username_exists(group_id, candidate):
        candidate = f"{base}_{i}"
        i += 1
    return candidate

    #добавляет пользователя в группу и выдает ему имя (telegram_username // userID)
def add_user_to_group_auto(group_id: int, user_id: int, telegram_username: str, telegram_id: int):
    
    
    if is_user_in_group(group_id, user_id):
        return  # возвращает если пользователь уже в группе 

    base = telegram_username if telegram_username else f"user{telegram_id}"
    unique_username = make_unique_group_username(group_id, base)

    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, group_username) VALUES (?, ?, ?)",
        (group_id, user_id, unique_username)
    )
    conn.commit()
