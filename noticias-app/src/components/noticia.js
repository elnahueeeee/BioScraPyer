import React from "react";

function Noticia({ noticia, textoMostrado }) {
  const abrirEnlace = () => {
    window.open(noticia.link, "_blank");
  };

  return (
    <div
      style={{
        border: "1px solid #ccc",
        borderRadius: "8px",
        padding: "10px",
        marginBottom: "15px",
        backgroundColor: "#f9f9f9",
      }}
    >
      <h2>{noticia.titulo}</h2>
      <p style={{ whiteSpace: "pre-wrap" }}>{textoMostrado}</p>
      <button onClick={abrirEnlace}>🌐 Abrir fuente</button>
    </div>
  );
}

export default Noticia;
