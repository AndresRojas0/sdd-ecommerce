# ADR-002 — Reactivación nativa del usuario dado de baja

## Contexto

La baja del usuario es lógica (`is_active = false`, RN-17): se conservan
sus visitas, favoritos y pedidos. Cuando el usuario vuelve a la plataforma
debe recuperar los pedidos de su autoría, incluidos los que ya fueron
confirmados como órdenes de compra. Se evaluaron tres estrategias:
reactivación nativa, reasignación administrativa y archivo inerte.

## Decisión

**Reactivación nativa**: el email es identidad única y la cuenta nunca se
elimina físicamente. El usuario regresa autenticándose con el mismo email;
recupera automáticamente todo su historial (pedidos, órdenes de compra,
favoritos, calificaciones) porque conserva el mismo `userId`. No existe
migración ni fusión de datos.

Complementariamente (RF-18): al eliminarse, el usuario puede optar por
eliminar también sus pedidos no confirmados; las órdenes de compra ya
emitidas no se eliminan (RN-19).

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Reasignación administrativa (merge de pedidos hacia cuentas nuevas) | Requiere herramienta extra, auditoría y es propensa a errores. Queda como posible herramienta futura, no como base. |
| Archivo inerte (historial congelado visible solo al staff) | Castiga al cliente que vuelve: pierde su propio historial. |

## Consecuencias

- Positivas: cero migración; historial íntegro y auditable; coherente con la baja lógica.
- Negativas: el email se convierte en identidad permanente; un usuario que quiera "empezar de cero" usará otro email y su historial anterior queda desvinculado de su nueva cuenta.
