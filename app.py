import streamlit as st
import pandas as pd
import database as db

db.crear_tablas()

st.set_page_config(
    page_title="Brew & Byte Manager",
    layout="wide"
)

st.title("Brew & Byte Manager")
st.caption("Sistema de gestion - ORT Coffee Roasters")
st.divider()

seccion = st.sidebar.selectbox(
    "Navegar a",
    ["Carta de Productos", "Control de Insumos", "Staff de Baristas", "Estadisticas"]
)

st.sidebar.divider()
st.sidebar.caption("Brew & Byte Manager v1.0")


if seccion == "Carta de Productos":
    st.header("Carta de Productos")

    col_filtro, _ = st.columns([2, 4])
    with col_filtro:
        filtro_cat = st.selectbox("Filtrar por categoria", ["Todos", "Caliente", "Frio"])

    categoria_param = None if filtro_cat == "Todos" else filtro_cat
    productos = db.leer_productos(categoria=categoria_param)

    if productos:
        filas = []
        for p in productos:
            filas.append({
                "ID":          p.id_producto,
                "Nombre":      p.nombre,
                "Categoria":   p.categoria,
                "Precio base": f"${p.precio_base:,.0f}",
                "Con IVA":     f"${p.precio_con_iva():,.2f}",
                "Insumo ID":   p.insumo_id if p.insumo_id else "-"
            })
        st.dataframe(filas, use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos registrados.")

    st.divider()

    with st.expander("Agregar nuevo producto"):
        insumos_disponibles = db.leer_insumos()
        opciones_insumo = {f"{i.nombre} (ID {i.id_insumo})": i.id_insumo
                           for i in insumos_disponibles}

        with st.form("form_producto"):
            nombre_p    = st.text_input("Nombre del producto")
            categoria_p = st.selectbox("Categoria", ["Caliente", "Frio"])
            precio_p    = st.number_input("Precio base ($)", min_value=0.0, step=50.0)
            insumo_sel  = st.selectbox("Insumo principal", ["Sin asociar"] + list(opciones_insumo.keys()))
            submit_p    = st.form_submit_button("Guardar producto")

        if submit_p:
            if not nombre_p.strip():
                st.error("El nombre no puede estar vacio.")
            elif precio_p <= 0:
                st.error("El precio debe ser mayor a cero.")
            else:
                insumo_id_sel = opciones_insumo.get(insumo_sel)
                try:
                    db.crear_producto(nombre_p, categoria_p, precio_p, insumo_id_sel)
                    st.success(f"Producto '{nombre_p}' agregado correctamente.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with st.expander("Eliminar producto"):
        if productos:
            opciones_del = {f"[{p.id_producto}] {p.nombre}": p.id_producto for p in productos}
            prod_borrar  = st.selectbox("Seleccionar producto a eliminar", list(opciones_del.keys()))
            if st.button("Eliminar", key="del_prod"):
                db.eliminar_producto(opciones_del[prod_borrar])
                st.success("Producto eliminado.")
                st.rerun()
        else:
            st.info("No hay productos para eliminar.")

    with st.expander("Modificar producto"):
        productos_todos = db.leer_productos()
        if productos_todos:
            opciones_mod = {f"[{p.id_producto}] {p.nombre}": p for p in productos_todos}
            prod_sel_key = st.selectbox("Seleccionar producto", list(opciones_mod.keys()), key="mod_prod_sel")
            prod_sel     = opciones_mod[prod_sel_key]

            with st.form("form_mod_producto"):
                nuevo_nombre_p = st.text_input("Nombre",   value=prod_sel.nombre)
                nueva_cat_p    = st.selectbox("Categoria", ["Caliente", "Frio"],
                                              index=0 if prod_sel.categoria == "Caliente" else 1)
                nuevo_precio_p = st.number_input("Precio base ($)", value=prod_sel.precio_base,
                                                 min_value=0.0, step=50.0)
                submit_mod_p   = st.form_submit_button("Guardar cambios")

            if submit_mod_p:
                if not nuevo_nombre_p.strip():
                    st.error("El nombre no puede estar vacio.")
                elif nuevo_precio_p <= 0:
                    st.error("El precio debe ser mayor a cero.")
                else:
                    try:
                        db.actualizar_producto(prod_sel.id_producto, nuevo_nombre_p,
                                               nueva_cat_p, nuevo_precio_p, prod_sel.insumo_id)
                        st.success("Producto actualizado.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))


elif seccion == "Control de Insumos":
    st.header("Control de Insumos")

    insumos = db.leer_insumos()

    proveedores = sorted(set(i.proveedor for i in insumos))
    col_f, _ = st.columns([2, 4])
    with col_f:
        filtro_prov = st.selectbox("Filtrar por proveedor", ["Todos"] + proveedores)

    if filtro_prov != "Todos":
        insumos = db.leer_insumos(proveedor=filtro_prov)

    criticos = [i for i in insumos if i.necesita_reposicion()]
    if criticos:
        st.warning(f"Hay {len(criticos)} insumo(s) con stock critico.")

    if insumos:
        filas_i = []
        for i in insumos:
            filas_i.append({
                "ID":        i.id_insumo,
                "Nombre":    i.nombre,
                "Cantidad":  i.cantidad,
                "Unidad":    i.unidad,
                "Proveedor": i.proveedor,
                "Estado":    i.estado_stock()
            })
        st.dataframe(filas_i, use_container_width=True, hide_index=True)
    else:
        st.info("No hay insumos registrados.")

    st.divider()

    with st.expander("Agregar nuevo insumo"):
        with st.form("form_insumo"):
            nombre_i    = st.text_input("Nombre del insumo")
            cantidad_i  = st.number_input("Cantidad", min_value=0.0, step=1.0)
            unidad_i    = st.text_input("Unidad (kg, lt, unidades...)")
            proveedor_i = st.text_input("Proveedor")
            submit_i    = st.form_submit_button("Guardar insumo")

        if submit_i:
            if not nombre_i.strip() or not unidad_i.strip() or not proveedor_i.strip():
                st.error("Todos los campos son obligatorios.")
            else:
                try:
                    db.crear_insumo(nombre_i, cantidad_i, unidad_i, proveedor_i)
                    st.success(f"Insumo '{nombre_i}' agregado.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with st.expander("Eliminar insumo"):
        todos_ins = db.leer_insumos()
        if todos_ins:
            ops_del_i  = {f"[{i.id_insumo}] {i.nombre}": i.id_insumo for i in todos_ins}
            ins_borrar = st.selectbox("Seleccionar insumo", list(ops_del_i.keys()))
            if st.button("Eliminar", key="del_ins"):
                db.eliminar_insumo(ops_del_i[ins_borrar])
                st.success("Insumo eliminado.")
                st.rerun()

    with st.expander("Modificar insumo"):
        todos_ins2  = db.leer_insumos()
        if todos_ins2:
            ops_mod_i   = {f"[{i.id_insumo}] {i.nombre}": i for i in todos_ins2}
            ins_sel_key = st.selectbox("Seleccionar insumo", list(ops_mod_i.keys()), key="mod_ins_sel")
            ins_sel     = ops_mod_i[ins_sel_key]

            with st.form("form_mod_insumo"):
                nuevo_nombre_i    = st.text_input("Nombre",    value=ins_sel.nombre)
                nueva_cantidad_i  = st.number_input("Cantidad", value=ins_sel.cantidad, min_value=0.0, step=1.0)
                nueva_unidad_i    = st.text_input("Unidad",    value=ins_sel.unidad)
                nuevo_proveedor_i = st.text_input("Proveedor", value=ins_sel.proveedor)
                submit_mod_i      = st.form_submit_button("Guardar cambios")

            if submit_mod_i:
                if not nuevo_nombre_i.strip() or not nueva_unidad_i.strip() or not nuevo_proveedor_i.strip():
                    st.error("Todos los campos son obligatorios.")
                else:
                    try:
                        db.actualizar_insumo(ins_sel.id_insumo, nuevo_nombre_i,
                                             nueva_cantidad_i, nueva_unidad_i, nuevo_proveedor_i)
                        st.success("Insumo actualizado.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))


elif seccion == "Estadisticas":
    st.header("Estadisticas de Productos")
    st.caption("Analisis de la carta con medidas de tendencia central (Pandas)")

    with st.expander("Importar productos desde CSV"):
        st.write("Carga el dataset `productos_dataset.csv` en la base usando la "
                 "misma alta del CRUD (una fila = un producto).")
        if st.button("Importar productos_dataset.csv"):
            try:
                cargados = db.importar_productos_csv("productos_dataset.csv")
                st.success(f"Se cargaron {cargados} productos desde el CSV. "
                           "Revisa la Carta de Productos para verificarlo.")
            except FileNotFoundError:
                st.error("No se encontro el archivo productos_dataset.csv.")

    st.divider()

    # Leemos los productos ya cargados directamente desde la base con Pandas.
    conn = db.get_connection()
    df = pd.read_sql("SELECT nombre, categoria, precio_base FROM productos", conn)
    conn.close()

    if df.empty:
        st.info("No hay productos cargados todavia. Importa el CSV para analizar los datos.")
    else:
        st.subheader("Datos analizados")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Medidas de tendencia central sobre la columna numerica precio_base.
        media   = df["precio_base"].mean()
        mediana = df["precio_base"].median()
        moda    = df["precio_base"].mode()  # puede haber mas de una moda

        st.subheader("Medidas de tendencia central (precio base)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Media",   f"${media:,.2f}")
        col2.metric("Mediana", f"${mediana:,.2f}")
        if len(moda) == 1:
            col3.metric("Moda", f"${moda.iloc[0]:,.2f}")
        else:
            col3.metric("Moda", "Varias")

        st.write(f"**Media:** ${media:,.2f}")
        st.write(f"**Mediana:** ${mediana:,.2f}")
        modas_texto = ", ".join(f"${m:,.2f}" for m in moda)
        st.write(f"**Moda:** {modas_texto}")

        st.subheader("Interpretacion")
        diferencia = abs(media - mediana)
        if diferencia < media * 0.05:
            comentario_centro = (
                "La media y la mediana son muy parecidas, asi que los precios "
                "estan bastante equilibrados y no hay valores extremos que tiren "
                "el promedio para un lado."
            )
        else:
            comentario_centro = (
                "La media y la mediana se diferencian bastante, lo que sugiere "
                "que hay algunos productos con precios mas altos (o mas bajos) "
                "que corren el promedio respecto del valor del medio."
            )

        if len(moda) == 1:
            comentario_moda = (
                f"Ademas, hay una moda clara en ${moda.iloc[0]:,.2f}: es el precio "
                "que mas se repite en la carta, probablemente el rango de nuestros "
                "productos mas tipicos."
            )
        else:
            comentario_moda = (
                "En cuanto a la moda, hay varios precios que se repiten la misma "
                "cantidad de veces, asi que los valores estan mas repartidos y no "
                "existe un unico precio dominante."
            )

        st.write(comentario_centro + " " + comentario_moda)


elif seccion == "Staff de Baristas":
    st.header("Staff de Baristas")

    baristas = db.leer_baristas()

    if baristas:
        filas_b = []
        for b in baristas:
            filas_b.append({
                "ID":          b.id_barista,
                "Nombre":      b.nombre_completo(),
                "Turno":       b.turno,
                "Experiencia": f"{b.anios_experiencia} anio(s)",
                "Nivel":       b.nivel_experiencia()
            })
        st.dataframe(filas_b, use_container_width=True, hide_index=True)
    else:
        st.info("No hay baristas registrados.")

    if baristas:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total staff", len(baristas))
        masters  = sum(1 for b in baristas if b.nivel_experiencia() == "Master Barista")
        col2.metric("Master Baristas", masters)
        exp_prom = sum(b.anios_experiencia for b in baristas) / len(baristas)
        col3.metric("Exp. promedio", f"{exp_prom:.1f} anios")

    st.divider()

    with st.expander("Agregar nuevo barista"):
        with st.form("form_barista"):
            nombre_b   = st.text_input("Nombre")
            apellido_b = st.text_input("Apellido")
            anios_b    = st.number_input("Anos de experiencia", min_value=0, max_value=50, step=1)
            turno_b    = st.selectbox("Turno", ["Manana", "Tarde", "Noche"])
            submit_b   = st.form_submit_button("Guardar barista")

        if submit_b:
            if not nombre_b.strip() or not apellido_b.strip():
                st.error("Nombre y apellido son obligatorios.")
            else:
                try:
                    db.crear_barista(nombre_b, apellido_b, anios_b, turno_b)
                    st.success(f"Barista '{nombre_b} {apellido_b}' agregado.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with st.expander("Eliminar barista"):
        if baristas:
            ops_del_b  = {f"[{b.id_barista}] {b.nombre_completo()}": b.id_barista for b in baristas}
            bar_borrar = st.selectbox("Seleccionar barista", list(ops_del_b.keys()))
            if st.button("Eliminar", key="del_bar"):
                db.eliminar_barista(ops_del_b[bar_borrar])
                st.success("Barista eliminado.")
                st.rerun()

    with st.expander("Modificar barista"):
        if baristas:
            ops_mod_b   = {f"[{b.id_barista}] {b.nombre_completo()}": b for b in baristas}
            bar_sel_key = st.selectbox("Seleccionar barista", list(ops_mod_b.keys()), key="mod_bar_sel")
            bar_sel     = ops_mod_b[bar_sel_key]

            with st.form("form_mod_barista"):
                nuevo_nombre_b   = st.text_input("Nombre",   value=bar_sel.nombre)
                nuevo_apellido_b = st.text_input("Apellido", value=bar_sel.apellido)
                nuevos_anios_b   = st.number_input("Anos de experiencia", value=bar_sel.anios_experiencia,
                                                   min_value=0, max_value=50, step=1)
                nuevo_turno_b    = st.selectbox("Turno", ["Manana", "Tarde", "Noche"],
                                                index=["Manana", "Tarde", "Noche"].index(bar_sel.turno))
                submit_mod_b     = st.form_submit_button("Guardar cambios")

            if submit_mod_b:
                if not nuevo_nombre_b.strip() or not nuevo_apellido_b.strip():
                    st.error("Nombre y apellido son obligatorios.")
                else:
                    try:
                        db.actualizar_barista(bar_sel.id_barista, nuevo_nombre_b,
                                              nuevo_apellido_b, nuevos_anios_b, nuevo_turno_b)
                        st.success("Barista actualizado.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
