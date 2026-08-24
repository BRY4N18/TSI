import axe, { Result, RunOptions } from 'axe-core';

/**
 * PG-UI-006 — accesibilidad comprobada con `axe` sobre el DOM real del componente.
 *
 * **Por qué aquí y no en una suite E2E.** La regla del plan decía «verificable
 * con axe en la suite E2E», pero **no existe suite E2E** en el proyecto: ni
 * Playwright ni Cypress. La regla se apoyaba en algo que no estaba, así que
 * llevaba desde el principio sin poder cumplirse.
 *
 * Angular renderiza el componente en un DOM de verdad dentro de Karma, y axe
 * analiza ese DOM igual que analizaría una página completa. Se aprovechan las
 * 1418 pruebas que ya corren en vez de montar una infraestructura nueva.
 *
 * ⚠️ **Lo que este enfoque NO ve, y conviene tenerlo escrito:** el orden de
 * tabulación entre componentes, el foco tras navegar, y el contraste real
 * cuando los estilos globales no están cargados en el TestBed. Son cosas que
 * solo se ven con la aplicación entera en un navegador. Esta comprobación cubre
 * estructura, etiquetas, roles y nombres accesibles — la mayor parte de lo que
 * la regla enumera, no toda.
 */

/**
 * Reglas que se comprueban. Se nombran de forma explícita en vez de «todas»
 * porque el conjunto por defecto de axe cambia entre versiones: una
 * actualización podría añadir reglas y romper pruebas ajenas al cambio, o
 * quitarlas y relajar la comprobación **sin que nadie se entere** — que es el
 * modo de fallo que este plan persigue.
 */
export const REGLAS_WCAG: RunOptions = {
  runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
};

export interface HallazgoA11y {
  id: string;
  impacto: string;
  descripcion: string;
  elementos: string[];
}

/** Ejecuta axe sobre un elemento y devuelve las violaciones en forma legible. */
export async function analizarAccesibilidad(
  elemento: Element,
  opciones: RunOptions = REGLAS_WCAG,
): Promise<HallazgoA11y[]> {
  const resultado = await axe.run(elemento, opciones);
  return resultado.violations.map((v: Result) => ({
    id: v.id,
    impacto: v.impact ?? 'desconocido',
    descripcion: v.help,
    elementos: v.nodes.map((n) => n.html.slice(0, 120)),
  }));
}

/** Convierte los hallazgos en un mensaje que dice qué arreglar y dónde. */
export function describir(hallazgos: HallazgoA11y[]): string {
  return hallazgos
    .map(
      (h) =>
        `  [${h.impacto}] ${h.id}: ${h.descripcion}\n` +
        h.elementos.map((e) => `      ${e}`).join('\n'),
    )
    .join('\n');
}
