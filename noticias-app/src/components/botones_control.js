import React from "react";

function BotonesControl({ buscarNoticias, resumirNoticias, cargando }) {
  return (
    <div style={{ marginBottom: "20px" }}>
      <button onClick={buscarNoticias} disabled={cargando}>
        🔍 Buscar noticias
      </button>
      <button onClick={resumirNoticias} disabled={cargando}>
        📝 Resumir todo
      </button>
    </div>
  );
}

export default BotonesControl;
