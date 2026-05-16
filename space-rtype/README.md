# 🚀 Space R-Type Invaders

> Shooter espacial estilo Nokia + R-Type con 10 niveles y jefe final épico: el Pulpo Espacial Gigante.

Disponible en dos versiones: **Python/Pygame** para escritorio/Batocera y **HTML5** para navegador con controles táctiles.

---

## 🎮 Versiones disponibles

| Versión | Archivo | Plataforma |
|---------|---------|------------|
| Python / Pygame | `space_rtype.py` | PC · Batocera · Linux |
| HTML5 / Canvas | `space_rtype.html` | Navegador · Móvil · PC |

---

## 🐍 Versión Python (Batocera / PC)

### Requisitos

```bash
pip install pygame
```

> En Batocera: `python3 -m ensurepip && python3 -m pip install pygame`

### Ejecutar

```bash
python3 space_rtype.py
```

### Controles

| Acción | Teclado | Gamepad (Batocera) |
|--------|---------|-------------------|
| Mover | `↑ ↓ ← →` o `WASD` | Analógico / D-Pad |
| Disparar | `Espacio` / `Z` / `X` | Botón A o B |
| Salir | `Escape` | — |

---

## 🌐 Versión HTML5 (Navegador / Móvil)

Abre `space_rtype.html` directamente en cualquier navegador moderno. No requiere instalación.

### Controles táctiles

| Acción | Control |
|--------|---------|
| Mover | D-pad ▲▼◀▶ en pantalla |
| Disparar | Botón rojo `FIRE` |
| Disparo automático | Botón `AUTO-FIRE` (toggle) |

También funciona con teclado (`↑↓←→` + `Espacio`).

---

## 👾 Enemigos (estilo R-Type)

| Enemigo | Descripción |
|---------|-------------|
| **Grunt Ship** | Nave Bydo básica con tentáculos. Zigzaguea y dispara hacia el jugador |
| **Swarm Ship** | Enjambre triangular ultrarrápido en formación caótica |
| **Fighter Ship** | Caza que se abalanza en picado hacia el jugador |
| **Bomber Ship** | Nave pesada que lanza minas en dos direcciones |
| **Command Ship** | Nave de mando resistente con ráfagas de 3 disparos simultáneos |

---

## 🏆 Los 10 niveles

| Nivel | Nombre | Descripción |
|-------|--------|-------------|
| 1 | Sector Alfa | Introducción con Grunt Ships |
| 2 | Nebulosa Roja | Aparecen los Swarm Ships |
| 3 | Campo de Asteroides | Se incorporan los Fighter Ships |
| 4 | Zona de Guerra | Mix de Grunt, Fighter y Swarm |
| 5 | Flota Bydo | Primeros Bomber Ships |
| 6 | Corredor Oscuro | Oleadas densas de 5 rondas |
| 7 | Fortaleza Orbital | Debut de los Command Ships |
| 8 | Enjambre Total | 5 oleadas de 10 enemigos mixtos |
| 9 | Apocalipsis Bydo | 6 oleadas de 12 enemigos. Dificultad extrema |
| 10 | **El Pulpo Espacial** | ⚠️ Jefe final — ver sección abajo |

---

## 🐙 Jefe Final: El Pulpo Espacial Gigante

El nivel 10 no tiene oleadas normales. En su lugar aparece el **Octoboss**, un pulpo espacial colosal con dos fases de combate.

### Fase 1 (HP > 50%)
- 8 tentáculos animados con movimiento ondulante
- Ráfaga en abanico de **5 proyectiles** simultáneos
- **Rayo láser giratorio** que barre la pantalla durante ~2 segundos

### Fase 2 (HP ≤ 50%) — Modo Furia
- Se vuelve rojo y más agresivo
- Ráfaga aumenta a **9 proyectiles**
- El rayo se dispara más seguido y rota más rápido
- Velocidad de movimiento aumentada

**HP total:** 500 puntos · **Puntuación al derrotarlo:** +5000

---

## ⚡ Power-Ups

| Icono | Tipo | Efecto |
|-------|------|--------|
| **P** 🟡 | Power | Sube nivel de disparo (simple → doble → triple) |
| **S** 🔵 | Shield | Absorbe el siguiente golpe sin perder HP |
| **+** 🟢 | HP | Recupera 1 punto de vida |
| **R** 🟠 | Rapid | Mejora la cadencia de disparo |

Los power-ups aparecen al destruir enemigos con ~12% de probabilidad.

---

## 📊 Sistema de puntuación

| Enemigo / Evento | Puntos base |
|-----------------|-------------|
| Grunt Ship | 100 + nivel × 10 |
| Swarm Ship | 80 + nivel × 8 |
| Fighter Ship | 200 + nivel × 20 |
| Bomber Ship | 350 + nivel × 30 |
| Command Ship | 500 + nivel × 50 |
| Octoboss derrotado | 5.000 |

---

## 🛠️ Características técnicas

**Python:**
- Motor gráfico con Pygame
- Sonidos procedurales via NumPy (opcional)
- Soporte nativo de gamepad (Batocera/SDL)
- Partículas y efectos visuales dibujados con primitivas

**HTML5:**
- Canvas 2D puro, sin dependencias externas
- Audio generado con Web Audio API
- Diseño responsive para móvil y escritorio
- Fuentes Orbitron + Share Tech Mono (Google Fonts)
- Controles táctiles con D-pad y botón FIRE

---

## 📁 Archivos

```
mis-juegos/
├── snake/
│   └── ...
└── space-rtype/
    ├── space_rtype.py      ← Versión Python/Pygame
    ├── space_rtype.html    ← Versión HTML5 táctil
    └── README.md
```

---

*Inspirado en Space Invaders (Nokia) y R-Type (Irem, 1987)*
