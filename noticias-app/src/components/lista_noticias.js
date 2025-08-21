import React from "react";
import Noticia from "./components/noticia";

function ListaNoticias({ noticias }) {
  return (
    <div>
      {noticias.length === 0 && <p>No hay noticias todavía</p>}
      {noticias.map((n, idx) => (
        <Noticia key={idx} noticia={n} />
      ))}
    </div>
  );
}

export default ListaNoticias;
