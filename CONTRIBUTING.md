# Cómo colaborar en este proyecto

Estas son unas reglas simples para que trabajemos sin pisarnos:

---

## Flujo de trabajo
- **No trabajes directo en `main`.**
- Usamos ramas:
  - `main` → estable  
  - `dev` → desarrollo  
  - `feature/lo-que-estés-haciendo` → tu rama

### Para empezar algo nuevo:
- 
   ```bash
  git checkout dev
  git pull
  git checkout -b feature/nombre-tarea

Cuando termines, hacé un Pull Request hacia dev.

Explica en pocas palabras qué cambiaste.

Si arregla un issue, poné: Closes #número.

## Commits
Que sean claros y cortos.

### Ejemplos:

feat: pantalla de login

fix: error al guardar usuario

arreglado

cosas varias

## Revisiones
Todos los cambios se revisan en equipo antes de entrar a dev.

Si ves algo que mejorar, comentá con buena onda

### Issues
Usamos Issues para organizar tareas y bugs.

Antes de abrir uno nuevo, fijate si ya existe.

## Resumen rápido
Rama por cada cosa que hagas.

Commits claros.

PRs a dev, no a main.

Revisar y comentar en equipo.
