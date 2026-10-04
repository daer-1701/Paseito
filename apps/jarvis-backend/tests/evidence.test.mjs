import test from 'node:test';
import assert from 'node:assert/strict';
import { tarjetasDeEvidencia, clavePiso } from '../../../frontend/js/evidence.mjs';

test('maps every knowledge type and preserves unknown/zero prices', () => {
  const cards = tarjetasDeEvidencia(['venue', 'product', 'promotion', 'event', 'faq'].map(kind => ({
    id: kind, kind, title: kind, attributes: { price_bs: 0, starts_at: '2026-10-04T01:00:00Z' }
  })));
  assert.deepEqual(cards.map(c => c.tipo), ['lugar', 'producto', 'promocion', 'evento', 'info']);
  assert.equal(cards[1].precio_bs, 0);
  assert.match(cards[3].fecha, /3/);
  assert.equal(tarjetasDeEvidencia([{kind:'product', attributes:{}}])[0].precio_bs, undefined);
});

test('does not label a source approved or expose non HTTP links', () => {
  const [card] = tarjetasDeEvidencia([{kind:'venue', source_url:'javascript:alert(1)', attributes:{}}]);
  assert.equal(card.fuente_url, '');
  assert.equal(card.verificacion, 'Fuente disponible');
  assert.equal(card.verificado_en, '');
});

test('normalizes numeric and named floors for cards and guides', () => {
  for (const floor of [3, '3', 'Piso 3', 'Tercer Piso']) assert.equal(clavePiso(floor), '3');
  assert.equal(clavePiso('planta baja'), 'PB');
  assert.equal(clavePiso('semisótano'), 'S');
  assert.equal(clavePiso(''), null);
});
