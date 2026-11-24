from app.crdt import (
    actualizar_evento_crdt,
    crear_evento_crdt,
    deserialize_doc,
    doc_a_dict,
    fusionar_eventos,
    serialize_doc,
)


def test_recurrencia_exdates_sobrevive_la_fusion_crdt():
    doc_a = crear_evento_crdt(
        {
            "titulo": "Evento recurrente",
            "rrule": "FREQ=WEEKLY;COUNT=4",
            "exdates": ["2026-12-01T10:00:00", "2026-12-08T10:00:00"],
            "visibilidad": "publico",
        }
    )
    doc_b = deserialize_doc(serialize_doc(doc_a))
    actualizar_evento_crdt(
        doc_a,
        {"exdates": ["2026-12-15T10:00:00"]},
        "9999-12-31T23:59:59+00:00",
    )

    fusionar_eventos(doc_b, doc_a)
    resultado = doc_a_dict(doc_b)

    assert resultado["rrule"] == "FREQ=WEEKLY;COUNT=4"
    assert resultado["exdates"] == ["2026-12-15T10:00:00"]


def test_visibilidad_privada_sobrevive_la_fusion_crdt():
    doc_a = crear_evento_crdt(
        {
            "titulo": "Evento privado",
            "visibilidad": "publico",
        }
    )
    doc_b = deserialize_doc(serialize_doc(doc_a))
    actualizar_evento_crdt(
        doc_a,
        {"visibilidad": "privado"},
        "9999-12-31T23:59:59+00:00",
    )

    fusionar_eventos(doc_b, doc_a)

    assert doc_a_dict(doc_b)["visibilidad"] == "privado"
