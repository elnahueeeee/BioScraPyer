import React, { useState, useEffect, useRef } from "react";
import BotonesControl from "./components/botones_control";
import Noticia from "./components/noticia";

function App() {
  const [noticias, setNoticias] = useState([]);
  const [indiceActual, setIndiceActual] = useState(0);
  const [textoMostrado, setTextoMostrado] = useState("");
  const [cargando, setCargando] = useState(false);

  const intervaloRef = useRef(null); // <-- guardamos el interval ID

  // Buscar noticias
  const buscarNoticias = async () => {
    setCargando(true);
    try {
      const resp = await fetch("http://127.0.0.1:8000/noticias");
      const data = await resp.json();
      const noticiasIniciales = data.map((n) => ({ ...n, resumen: null }));
      setNoticias(noticiasIniciales);
      setIndiceActual(0);
    } catch (e) {
      console.error(e);
      alert("Error al buscar noticias");
    } finally {
      setCargando(false);
    }
  };

  // Resumir todas las noticias
  const resumirNoticias = async () => {
    if (noticias.length === 0) return;
    setCargando(true);
    try {
      const textos = noticias.map((n) => n.contenido.join("\n\n"));
      const resp = await fetch("http://127.0.0.1:8000/resumir_batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contenidos: textos }),
      });
      const resumenes = await resp.json();
      const noticiasConResumen = noticias.map((n, i) => ({
        ...n,
        resumen: resumenes[i],
      }));
      setNoticias(noticiasConResumen);
    } catch (e) {
      console.error(e);
      alert("Error al resumir noticias");
    } finally {
      setCargando(false);
    }
  };

  // Efecto escritura

  const mostrarTextoConEfecto = (texto, velocidad = 15) => {
    // Limpiar cualquier animación previa
    if (intervaloRef.current) {
      clearInterval(intervaloRef.current);
    }
    setTextoMostrado("");
    let i = -1;

    intervaloRef.current = setInterval(() => {
      if (i >= texto.length) {
        clearInterval(intervaloRef.current);
        intervaloRef.current = null;
        return;
      }
      setTextoMostrado((prev) => prev + texto.charAt(i));
      i++;
    }, velocidad);
  };

  // Navegación
  const siguienteNoticia = () => {
    if (indiceActual < noticias.length - 1) setIndiceActual(indiceActual + 1);
  };
  const anteriorNoticia = () => {
    if (indiceActual > 0) setIndiceActual(indiceActual - 1);
  };

  // Actualizar efecto escritura al cambiar noticia
  useEffect(() => {
    if (noticias.length === 0) return;
    const noticia = noticias[indiceActual];
    const texto = noticia.resumen
      ? noticia.resumen
      : noticia.contenido.slice(0, 3).join("\n\n");
    mostrarTextoConEfecto(texto);
    // eslint-disable-next-line
  }, [indiceActual, noticias]); // <-- Cierra el useEffect correctamente

  return (
    <div style={{ padding: "20px", maxWidth: "900px", margin: "0 auto" }}>
      <h1>Noticias sobre Cambio Climático</h1>
      <BotonesControl
        buscarNoticias={buscarNoticias}
        resumirNoticias={resumirNoticias}
        cargando={cargando}
      />
      {noticias.length > 0 && (
        <div style={{ marginBottom: "10px" }}>
          <button onClick={anteriorNoticia} disabled={indiceActual === 0}>
            ← Anterior
          </button>
          <span style={{ margin: "0 10px" }}>
            {indiceActual + 1}/{noticias.length}
          </span>
          <button
            onClick={siguienteNoticia}
            disabled={indiceActual === noticias.length - 1}
          >
            Siguiente →
          </button>
        </div>
      )}
      {noticias.length > 0 && (
        <Noticia
          noticia={noticias[indiceActual]}
          textoMostrado={textoMostrado}
        />
      )}
      {noticias.length === 0 && !cargando && <p>No hay noticias todavía</p>}
      {cargando && <p>Cargando...</p>}
    </div>
  );
}

export default App;
