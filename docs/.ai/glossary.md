# Glosario de dominio

Términos del negocio. Los términos SDD (proposal, delta spec, etc.) están
en el `GLOSSARY.md` de la raíz, no acá.

## Pedidos y facturación

- **Pedido**: compra creada por un comprador (o staff en su nombre), estado
  inicial pendiente; solo editable/eliminable en pendiente (RF-30).
- **Estados de pedido**: `pendiente → aceptado → facturado → en_logistica →
  entregado`, más `rechazado` (terminal, solo duplicable). Sin transiciones
  inversas, salvo `aceptado → rechazado` (RN-28).
- **Orden de compra (OC)**: consolidación de N pedidos del mismo comprador.
  Número `OC-YYYY-NNNN`. Sin estado propio: se deriva de sus pedidos y de
  su factura (RN-29/RN-36).
- **Factura**: documento 1:1 con la OC, número fiscal `F-YYYY-NNNN`,
  inmutable, nunca se borra (RN-36).

## Stock

- **Movimiento de stock**: reserva (pedido aceptado), confirmación
  (facturado), devolución (`aceptado → rechazado`). Cantidad positiva: el
  signo lo da el tipo de movimiento (RN-35).
- **Stock disponible / reservada**: cantidad vendible y cantidad
  comprometida por pedidos aceptados; nunca negativas.

## Precios

- **Oferta / precio de oferta**: precio con vigencia sobre un producto
  (ADR-008). Precio efectivo = oferta vigente o precio de lista.
- **Snapshot de precio**: cada línea guarda `precio_unitario` +
  `precio_lista` al momento de la operación.

## Catálogo

- **Categoría hoja**: categoría de nivel 2. Todo producto pertenece a al
  menos una hoja (RN-01); árbol de profundidad máxima 2 (RN-38).
- **Colección**: lista curada de productos con slug público y orden
  opcional (RN-39).
- **Etiqueta**: vocabulario abierto para filtros y autocomplete (RN-02/03).
- **Unidad de venta**: registro abierto con cantidades fraccionarias
  permitidas (RN-23).

## Usuarios

- **Vendedor / Administrador / Comprador**: roles de `users.role`. El
  vendedor y el administrador operan `/api/admin`; el comprador, `/api/store`.
- **Visitante anónimo**: usuario sin sesión identificado por cookie
  first-party UUID; sus visitas se deduplican en ventana configurable
  (ADR-001 / RN-08).
- **Calificación**: 1..5 estrellas por producto y usuario (única, editable);
  requiere un pedido aceptado con el producto (RN-33).
