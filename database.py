import sqlite3
import pandas as pd
from models import Producto, Insumo, Barista

DB_PATH = "brew_and_byte.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def crear_tablas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS insumos (
            id_insumo  INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT    NOT NULL,
            cantidad   REAL    NOT NULL CHECK(cantidad >= 0),
            unidad     TEXT    NOT NULL,
            proveedor  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS productos (
            id_producto  INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT    NOT NULL,
            categoria    TEXT    NOT NULL CHECK(categoria IN ('Caliente', 'Frio')),
            precio_base  REAL    NOT NULL CHECK(precio_base >= 0),
            insumo_id    INTEGER REFERENCES insumos(id_insumo)
        );

        CREATE TABLE IF NOT EXISTS baristas (
            id_barista        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre            TEXT    NOT NULL,
            apellido          TEXT    NOT NULL,
            anios_experiencia INTEGER NOT NULL CHECK(anios_experiencia >= 0),
            turno             TEXT    NOT NULL CHECK(turno IN ('Manana', 'Tarde', 'Noche'))
        );
    """)

    if cursor.execute("SELECT COUNT(*) FROM insumos").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO insumos (nombre, cantidad, unidad, proveedor) VALUES (?,?,?,?)",
            [
                ("Granos Etiopia",    20, "kg",       "CoffeeTrade SA"),
                ("Leche entera",       3, "lt",        "Lacteos del Sur"),
                ("Jarabe de vainilla", 8, "unidades",  "Dulces and Co"),
                ("Granos Colombia",    2, "kg",        "CoffeeTrade SA"),
                ("Cacao en polvo",    15, "unidades",  "Dulces and Co"),
            ]
        )
        cursor.executemany(
            "INSERT INTO productos (nombre, categoria, precio_base, insumo_id) VALUES (?,?,?,?)",
            [
                ("Cappuccino",         "Caliente", 1500, 1),
                ("Latte",              "Caliente", 1400, 2),
                ("Cold Brew",          "Frio",     1800, 4),
                ("Chocolate Caliente", "Caliente", 1200, 5),
                ("Frappe Vainilla",    "Frio",     1900, 3),
            ]
        )
        cursor.executemany(
            "INSERT INTO baristas (nombre, apellido, anios_experiencia, turno) VALUES (?,?,?,?)",
            [
                ("Lucia",  "Torres",  4, "Manana"),
                ("Martin", "Garcia",  1, "Tarde"),
                ("Sofia",  "Lopez",   8, "Noche"),
                ("Tomas",  "Ramirez", 0, "Manana"),
            ]
        )

    conn.commit()
    conn.close()


def leer_insumos(proveedor=None):
    conn = get_connection()
    cursor = conn.cursor()

    if proveedor:
        rows = cursor.execute(
            "SELECT * FROM insumos WHERE proveedor = ?", (proveedor,)
        ).fetchall()
    else:
        rows = cursor.execute("SELECT * FROM insumos").fetchall()

    conn.close()

    insumos = []
    for row in rows:
        insumos.append(Insumo(
            id_insumo = row["id_insumo"],
            nombre    = row["nombre"],
            cantidad  = row["cantidad"],
            unidad    = row["unidad"],
            proveedor = row["proveedor"]
        ))
    return insumos


def crear_insumo(nombre, cantidad, unidad, proveedor):
    if not nombre.strip() or not unidad.strip() or not proveedor.strip():
        raise ValueError("Nombre, unidad y proveedor no pueden estar vacios.")
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO insumos (nombre, cantidad, unidad, proveedor) VALUES (?,?,?,?)",
        (nombre.strip(), cantidad, unidad.strip(), proveedor.strip())
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id


def actualizar_insumo(id_insumo, nombre, cantidad, unidad, proveedor):
    if not nombre.strip() or not unidad.strip() or not proveedor.strip():
        raise ValueError("Nombre, unidad y proveedor no pueden estar vacios.")
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE insumos
           SET nombre=?, cantidad=?, unidad=?, proveedor=?
           WHERE id_insumo=?""",
        (nombre.strip(), cantidad, unidad.strip(), proveedor.strip(), id_insumo)
    )
    conn.commit()
    conn.close()


def eliminar_insumo(id_insumo):
    conn = get_connection()
    conn.execute("DELETE FROM insumos WHERE id_insumo=?", (id_insumo,))
    conn.commit()
    conn.close()


def leer_productos(categoria=None):
    conn = get_connection()
    cursor = conn.cursor()

    if categoria:
        rows = cursor.execute(
            "SELECT * FROM productos WHERE categoria = ?", (categoria,)
        ).fetchall()
    else:
        rows = cursor.execute("SELECT * FROM productos").fetchall()

    conn.close()

    productos = []
    for row in rows:
        productos.append(Producto(
            id_producto = row["id_producto"],
            nombre      = row["nombre"],
            categoria   = row["categoria"],
            precio_base = row["precio_base"],
            insumo_id   = row["insumo_id"]
        ))
    return productos


def crear_producto(nombre, categoria, precio_base, insumo_id=None):
    if not nombre.strip():
        raise ValueError("El nombre no puede estar vacio.")
    if categoria not in ("Caliente", "Frio"):
        raise ValueError("Categoria debe ser Caliente o Frio.")
    if precio_base < 0:
        raise ValueError("El precio no puede ser negativo.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, categoria, precio_base, insumo_id) VALUES (?,?,?,?)",
        (nombre.strip(), categoria, precio_base, insumo_id)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id


def importar_productos_csv(ruta_csv="productos_dataset.csv"):
    """Lee un CSV con pandas y da de alta cada fila usando crear_producto().

    Recorre el DataFrame con un for y llama a la funcion de alta que ya
    tenemos programada (una fila = un producto). Devuelve la cantidad de
    productos que se cargaron correctamente.
    """
    df = pd.read_csv(ruta_csv)

    cargados = 0
    for _, fila in df.iterrows():
        insumo_id = fila["insumo_id"]
        # el CSV puede traer celdas vacias en insumo_id -> las pasamos como None
        if pd.isna(insumo_id):
            insumo_id = None
        else:
            insumo_id = int(insumo_id)

        try:
            crear_producto(
                nombre      = str(fila["nombre"]),
                categoria   = str(fila["categoria"]),
                precio_base = float(fila["precio_base"]),
                insumo_id   = insumo_id
            )
            cargados += 1
        except ValueError as e:
            print(f"Fila omitida ({fila['nombre']}): {e}")

    return cargados


def actualizar_producto(id_producto, nombre, categoria, precio_base, insumo_id=None):
    if not nombre.strip():
        raise ValueError("El nombre no puede estar vacio.")
    if categoria not in ("Caliente", "Frio"):
        raise ValueError("Categoria debe ser Caliente o Frio.")
    if precio_base < 0:
        raise ValueError("El precio no puede ser negativo.")

    conn = get_connection()
    conn.execute(
        """UPDATE productos
           SET nombre=?, categoria=?, precio_base=?, insumo_id=?
           WHERE id_producto=?""",
        (nombre.strip(), categoria, precio_base, insumo_id, id_producto)
    )
    conn.commit()
    conn.close()


def eliminar_producto(id_producto):
    conn = get_connection()
    conn.execute("DELETE FROM productos WHERE id_producto=?", (id_producto,))
    conn.commit()
    conn.close()


def leer_baristas():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM baristas").fetchall()
    conn.close()

    baristas = []
    for row in rows:
        baristas.append(Barista(
            id_barista        = row["id_barista"],
            nombre            = row["nombre"],
            apellido          = row["apellido"],
            anios_experiencia = row["anios_experiencia"],
            turno             = row["turno"]
        ))
    return baristas


def crear_barista(nombre, apellido, anios_experiencia, turno):
    if not nombre.strip() or not apellido.strip():
        raise ValueError("Nombre y apellido no pueden estar vacios.")
    if turno not in ("Manana", "Tarde", "Noche"):
        raise ValueError("Turno debe ser Manana, Tarde o Noche.")
    if anios_experiencia < 0 or anios_experiencia > 50:
        raise ValueError("Anos de experiencia invalidos.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO baristas (nombre, apellido, anios_experiencia, turno) VALUES (?,?,?,?)",
        (nombre.strip(), apellido.strip(), anios_experiencia, turno)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id


def actualizar_barista(id_barista, nombre, apellido, anios_experiencia, turno):
    if not nombre.strip() or not apellido.strip():
        raise ValueError("Nombre y apellido no pueden estar vacios.")
    if turno not in ("Manana", "Tarde", "Noche"):
        raise ValueError("Turno debe ser Manana, Tarde o Noche.")
    if anios_experiencia < 0 or anios_experiencia > 50:
        raise ValueError("Anos de experiencia invalidos.")

    conn = get_connection()
    conn.execute(
        """UPDATE baristas
           SET nombre=?, apellido=?, anios_experiencia=?, turno=?
           WHERE id_barista=?""",
        (nombre.strip(), apellido.strip(), anios_experiencia, turno, id_barista)
    )
    conn.commit()
    conn.close()


def eliminar_barista(id_barista):
    conn = get_connection()
    conn.execute("DELETE FROM baristas WHERE id_barista=?", (id_barista,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    crear_tablas()

    print("=== INSUMOS ===")
    for ins in leer_insumos():
        print(ins)

    print("\n=== PRODUCTOS ===")
    for prod in leer_productos():
        print(prod)

    print("\n=== BARISTAS ===")
    for bar in leer_baristas():
        print(bar)
