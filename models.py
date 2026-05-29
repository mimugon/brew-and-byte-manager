class Producto:

    def __init__(self, id_producto, nombre, categoria, precio_base, insumo_id=None):
        self.id_producto = id_producto
        self.nombre = nombre
        self.categoria = categoria
        self.precio_base = precio_base
        self.insumo_id = insumo_id

    def precio_con_iva(self):
        return round(self.precio_base * 1.21, 2)

    def es_bebida_fria(self):
        return self.categoria.lower() == "frío"

    def __str__(self):
        return f"{self.nombre} - ${self.precio_con_iva()}"


class Insumo:

    def __init__(self, id_insumo, nombre, cantidad, unidad, proveedor):
        self.id_insumo = id_insumo
        self.nombre = nombre
        self.cantidad = cantidad
        self.unidad = unidad
        self.proveedor = proveedor

    def necesita_reposicion(self):
        return self.cantidad < 5

    def estado_stock(self):
        if self.cantidad == 0:
            return "SIN STOCK"
        elif self.necesita_reposicion():
            return "CRITICO"
        else:
            return "OK"

    def __str__(self):
        return f"{self.nombre} - {self.cantidad} {self.unidad}"


class Barista:

    def __init__(self, id_barista, nombre, apellido, anios_experiencia, turno):
        if anios_experiencia < 0 or anios_experiencia > 50:
            raise ValueError("Anos de experiencia invalidos.")

        self.id_barista = id_barista
        self.nombre = nombre
        self.apellido = apellido
        self.anios_experiencia = anios_experiencia
        self.turno = turno

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def nivel_experiencia(self):
        if self.anios_experiencia < 1:
            return "Trainee"
        elif self.anios_experiencia < 3:
            return "Junior"
        elif self.anios_experiencia < 7:
            return "Senior"
        else:
            return "Master Barista"

    def __str__(self):
        return f"{self.nombre_completo()} - Turno: {self.turno}"


if __name__ == "__main__":
    p = Producto(1, "Cappuccino", "Caliente", 1500)
    print(p)

    i = Insumo(1, "Granos Etiopia", 3, "kg", "CoffeeTrade SA")
    print(i)

    b = Barista(1, "Lucia", "Torres", 4, "Manana")
    print(b)
