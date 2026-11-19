function calendarioApp() {
  return {
    eventos: [],
    calendarios: [],
    form: {
      id: null,
      titulo: "",
      descripcion: "",
      inicio: "",
      fin: "",
      calendario_id: "",
      todo_el_dia: false,
      participantes: [],
    },
    nodoRemoto: "",
    error: "",
    mensaje: "",

    async cargar() {
      this.error = "";
      try {
        let respuesta = await fetch("/api/calendarios");
        if (!respuesta.ok) throw new Error("No se pudieron cargar los calendarios.");
        this.calendarios = await respuesta.json();
        if (this.calendarios.length === 0) {
          respuesta = await fetch("/api/calendarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre: "Personal", propietario: "local" }),
          });
          if (!respuesta.ok) throw new Error("No se pudo crear el calendario inicial.");
          this.calendarios = [await respuesta.json()];
        }
        if (!this.form.calendario_id) {
          this.form.calendario_id = this.calendarios[0].id;
        }
        respuesta = await fetch("/api/eventos");
        if (!respuesta.ok) throw new Error("No se pudieron cargar los eventos.");
        this.eventos = await respuesta.json();
      } catch (error) {
        this.error = error.message;
      }
    },

    async crear() {
      this.error = "";
      this.mensaje = "";
      const editando = Boolean(this.form.id);
      const datos = {
        titulo: this.form.titulo,
        descripcion: this.form.descripcion,
        inicio: this.form.inicio,
        fin: this.form.fin,
        calendario_id: this.form.calendario_id || null,
        todo_el_dia: this.form.todo_el_dia,
        participantes: this.form.participantes,
      };
      try {
        const respuesta = await fetch(
          editando ? `/api/eventos/${this.form.id}` : "/api/eventos",
          {
            method: editando ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
          },
        );
        if (!respuesta.ok) throw new Error("No se pudo guardar el evento.");
        this.limpiarFormulario();
        await this.cargar();
        this.mensaje = editando ? "Evento actualizado." : "Evento creado.";
      } catch (error) {
        this.error = error.message;
      }
    },

    editar(evento) {
      this.form = {
        id: evento.id,
        titulo: evento.titulo,
        descripcion: evento.descripcion || "",
        inicio: evento.inicio.slice(0, 16),
        fin: evento.fin.slice(0, 16),
        calendario_id: evento.calendario_id || "",
        todo_el_dia: evento.todo_el_dia,
        participantes: evento.participantes || [],
      };
      this.mensaje = "";
    },

    limpiarFormulario() {
      this.form = {
        id: null,
        titulo: "",
        descripcion: "",
        inicio: "",
        fin: "",
        calendario_id: this.calendarios[0]?.id || "",
        todo_el_dia: false,
        participantes: [],
      };
    },

    async eliminar(id) {
      this.error = "";
      this.mensaje = "";
      try {
        const respuesta = await fetch(`/api/eventos/${id}`, { method: "DELETE" });
        if (!respuesta.ok) throw new Error("No se pudo eliminar el evento.");
        await this.cargar();
        this.mensaje = "Evento eliminado.";
      } catch (error) {
        this.error = error.message;
      }
    },

    async sincronizar() {
      this.error = "";
      this.mensaje = "";
      if (!this.nodoRemoto.trim()) {
        this.error = "Indica la URL o dirección del nodo remoto.";
        return;
      }
      const claveCheckpoint = `kronos-sync-checkpoint:${this.nodoRemoto.trim()}`;
      const anterior = localStorage.getItem(claveCheckpoint);
      const query = anterior
        ? `?desde=${encodeURIComponent(anterior)}`
        : "";
      try {
        const deltaRespuesta = await fetch(`/api/sync/delta${query}`);
        if (!deltaRespuesta.ok) throw new Error("No se pudo preparar el delta.");
        const delta = await deltaRespuesta.json();
        const respuesta = await fetch("/api/sync/enviar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            destino: this.nodoRemoto.trim(),
            cambios: { eventos: delta.eventos, tombstones: delta.tombstones },
          }),
        });
        const resultado = await respuesta.json();
        if (!respuesta.ok || resultado.status === "error") {
          throw new Error(resultado.detail || resultado.error || "Falló la sincronización.");
        }
        localStorage.setItem(claveCheckpoint, delta.checkpoint);
        this.mensaje = "Cambios sincronizados correctamente.";
      } catch (error) {
        this.error = error.message;
      }
    },
  };
}
