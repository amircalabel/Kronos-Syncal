from datetime import datetime, timedelta


def crear_evento(client, *, inicio, fin, titulo="Evento de prueba", **campos):
    respuesta = client.post(
        "/api/eventos",
        json={
            "titulo": titulo,
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat(),
            **campos,
        },
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def calcular_disponibilidad_secuencial(eventos, usuarios, inicio, fin):
    resultado = {}
    for usuario in usuarios:
        ocupados = []
        for evento in eventos:
            asistentes = {evento["creador"], *evento["participantes"]}
            if usuario in asistentes:
                evento_inicio = datetime.fromisoformat(evento["inicio"])
                evento_fin = datetime.fromisoformat(evento["fin"])
                ocupados.append(
                    {
                        "inicio": max(inicio, evento_inicio),
                        "fin": min(fin, evento_fin),
                        "evento_id": evento["id"],
                    }
                )
        ocupados.sort(key=lambda intervalo: intervalo["inicio"])
        fusionados = []
        for intervalo in ocupados:
            if fusionados and intervalo["inicio"] <= fusionados[-1]["fin"]:
                fusionados[-1]["fin"] = max(
                    fusionados[-1]["fin"], intervalo["fin"]
                )
            else:
                fusionados.append(dict(intervalo))
        libres = []
        cursor = inicio
        for intervalo in fusionados:
            if cursor < intervalo["inicio"]:
                libres.append(
                    {
                        "inicio": cursor.isoformat(),
                        "fin": intervalo["inicio"].isoformat(),
                    }
                )
            cursor = max(cursor, intervalo["fin"])
        if cursor < fin:
            libres.append({"inicio": cursor.isoformat(), "fin": fin.isoformat()})
        resultado[usuario] = {
            "ocupado": [
                {
                    **intervalo,
                    "inicio": intervalo["inicio"].isoformat(),
                    "fin": intervalo["fin"].isoformat(),
                }
                for intervalo in fusionados
            ],
            "disponible": libres,
        }
    return resultado


def test_disponibilidad_ray_coincide_con_intervalos_secuenciales(cliente_autenticado):
    inicio = datetime(2035, 6, 1, 9)
    evento_a = crear_evento(
        cliente_autenticado,
        inicio=inicio,
        fin=inicio + timedelta(hours=1),
        titulo="Evento A",
        participantes=["usuario-a@test.local"],
    )
    evento_b = crear_evento(
        cliente_autenticado,
        inicio=inicio + timedelta(minutes=30),
        fin=inicio + timedelta(hours=2),
        titulo="Evento B",
        participantes=["usuario-a@test.local", "usuario-b@test.local"],
    )

    respuesta = cliente_autenticado.get(
        "/api/disponibilidad",
        params={
            "inicio": inicio.isoformat(),
            "fin": (inicio + timedelta(hours=3)).isoformat(),
            "usuarios": "usuario-a@test.local,usuario-b@test.local",
        },
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["usuarios"] == calcular_disponibilidad_secuencial(
        [evento_a, evento_b],
        ["usuario-a@test.local", "usuario-b@test.local"],
        inicio,
        inicio + timedelta(hours=3),
    )


def test_tres_eventos_recurrentes_se_expanden_en_paralelo(cliente_autenticado):
    inicio = datetime(2035, 7, 1, 10)
    eventos = [
        crear_evento(
            cliente_autenticado,
            titulo=f"Recurrente {numero}",
            inicio=inicio + timedelta(hours=numero),
            fin=inicio + timedelta(hours=numero + 1),
            rrule="FREQ=DAILY;COUNT=3",
        )
        for numero in range(3)
    ]

    respuesta = cliente_autenticado.get("/api/eventos")

    assert respuesta.status_code == 200
    ocurrencias = respuesta.json()
    for evento in eventos:
        encontradas = [
            item
            for item in ocurrencias
            if item["id"].startswith(f"{evento['id']}::")
        ]
        assert len(encontradas) == 3
