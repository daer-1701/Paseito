import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from jarvis.store import connect, upsert, search, validate_record
from jarvis.agent import chat
from jarvis.knowledge import schedule_status
from jarvis.context import opening_status, BOLIVIA


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / 'test.sqlite3')
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def record(self, kind='venue', **changes):
        return {'id': kind + ':test', 'kind': kind, 'title': 'Café Norte', 'text': 'café',
                'attributes': {'category': 'cafetería', 'floor': '2'},
                'source_url': 'https://example.com', 'updated_at': (self.now - timedelta(days=2)).isoformat(), **changes}

    def event(self, start, end, **changes):
        return self.record('event', attributes={'starts_at': start.isoformat(), 'ends_at': end.isoformat(),
            'location': 'Sala de prueba', 'description': 'Evento de prueba'}, **changes)

    def test_event_query_does_not_return_hoy_hay_venue(self):
        upsert(self.db, self.record(title='HOY HAY', text='restaurante hoy hay'))
        result = chat(self.db, '¿Qué eventos hay hoy?')
        self.assertEqual(result['intent'], 'event_search')
        self.assertEqual(result['sources'], [])
        self.assertIn('No tengo eventos confirmados', result['answer'])

    def test_events_today_exclude_future_and_finished(self):
        now = datetime(2026, 10, 3, 16, tzinfo=BOLIVIA)
        for label, start, end in [('today', now + timedelta(hours=1), now + timedelta(hours=2)),
                                   ('tomorrow', now + timedelta(days=1), now + timedelta(days=1, hours=1)),
                                   ('finished', now - timedelta(hours=2), now - timedelta(hours=1))]:
            upsert(self.db, self.event(start, end, id='event:' + label))
        self.assertEqual([r['id'] for r in search(self.db, 'eventos hoy', now=now, kinds={'event'}, event_day=now.date(), browse=True)], ['event:today'])

    def test_promotions_require_terms_and_time_window(self):
        def promo(label, start, end):
            return self.record('promotion', id='promotion:' + label, expires_at=end.isoformat(), attributes={
                'starts_at': start.isoformat(), 'venue_id': 'venue:test', 'benefit': 'Beneficio de prueba', 'terms': 'Solo pruebas'})
        upsert(self.db, promo('active', self.now - timedelta(hours=1), self.now + timedelta(hours=1)))
        upsert(self.db, promo('future', self.now + timedelta(hours=1), self.now + timedelta(hours=2)))
        upsert(self.db, promo('expired', self.now - timedelta(days=1), self.now - timedelta(hours=1)))
        self.assertEqual([r['id'] for r in search(self.db, 'promociones', now=self.now, kinds={'promotion'}, browse=True)], ['promotion:active'])
        with self.assertRaises(ValueError):
            validate_record(self.record('promotion', expires_at=(self.now + timedelta(days=1)).isoformat()))

    def test_price_question_does_not_claim_venue_has_a_price(self):
        upsert(self.db, self.record())
        result = chat(self.db, '¿Cuánto cuesta un café?')
        self.assertIn('precio ni stock confirmados', result['answer'])

    def test_known_zero_price_and_unknown_stock(self):
        upsert(self.db, self.record('product', attributes={'venue_id': 'venue:test', 'price_bs': 0}))
        result = chat(self.db, 'precio café')
        self.assertIn('Bs 0', result['answer'])
        self.assertIn('Stock no confirmado', result['answer'])

    def test_tenant_without_hours_is_explicit(self):
        upsert(self.db, self.record(title='Crocs'))
        result = chat(self.db, '¿A qué hora abre Crocs?')
        self.assertIn('horario individual confirmado de Crocs', result['answer'])
        self.assertIn('locales individuales', result['answer'])

    def test_tenant_schedule_overnight_and_special_date(self):
        hours = {'4': [['12:00', '01:00']], '5': [['12:00', '22:00']], 'special': {'2026-10-03': []}}
        self.assertTrue(schedule_status(hours, datetime(2026, 10, 3, 0, 30, tzinfo=BOLIVIA))['open_now'])
        self.assertFalse(schedule_status(hours, datetime(2026, 10, 3, 13, tzinfo=BOLIVIA))['open_now'])
        self.assertFalse(schedule_status(hours, datetime(2026, 10, 2, 0, 30, tzinfo=BOLIVIA))['open_now'])

    def test_general_schedule_accounts_for_previous_day(self):
        friday = opening_status(datetime(2026, 10, 2, 0, 30, tzinfo=BOLIVIA))
        saturday = opening_status(datetime(2026, 10, 3, 0, 30, tzinfo=BOLIVIA))
        self.assertFalse(friday['sources'][2]['attributes']['open_now'])
        self.assertTrue(saturday['sources'][2]['attributes']['open_now'])
        self.assertEqual(friday['sources'][2]['updated_at'], saturday['sources'][2]['updated_at'])

    def test_drafts_excluded_and_approval_requires_responsible(self):
        upsert(self.db, self.record(attributes={'review_status': 'draft'}))
        self.assertEqual(search(self.db, 'café'), [])
        with self.assertRaises(ValueError):
            validate_record(self.record(attributes={'review_status': 'approved'}))

    def test_second_choice_and_deleted_selection(self):
        upsert(self.db, self.record(id='venue:one', title='Café Uno'))
        upsert(self.db, self.record(id='venue:two', title='Café Dos'))
        first = chat(self.db, 'Busco café')
        selected = first['sources'][1]['id']
        second = chat(self.db, 'Guíame al segundo', first['session_id'])
        self.assertEqual(second['sources'][0]['id'], selected)
        self.db.execute('DELETE FROM records WHERE id=?', (selected,))
        self.db.commit()
        self.assertEqual(chat(self.db, '¿Dónde queda?', first['session_id'])['sources'], [])

    def test_multiple_requests_cover_distinct_categories(self):
        upsert(self.db, self.record(id='venue:coffee'))
        upsert(self.db, self.record(id='venue:shirt', title='Moda Norte', text='ropa', attributes={'category': 'ropa'}))
        result = chat(self.db, 'Quiero una camisa y un café')
        self.assertEqual({r['id'] for r in result['sources']}, {'venue:coffee', 'venue:shirt'})

    def test_budget_excludes_unknown_and_expensive_products(self):
        for label, price in [('cheap', 30), ('expensive', 150), ('unknown', None)]:
            attrs = {'venue_id': 'venue:test'}
            if price is not None:
                attrs['price_bs'] = price
            upsert(self.db, self.record('product', id='product:' + label, attributes=attrs))
        result = chat(self.db, 'Comprar café hasta 50 Bs')
        self.assertEqual([r['id'] for r in result['sources']], ['product:cheap'])

    def test_invalid_typed_attributes_fail_validation(self):
        for attrs in ({'verified_at': 123}, {'review_status': {}}, {'price_bs': float('nan')},
                      {'hours': {'special': []}}, {'hours': {'0': [['25:00', '22:00']]}}):
            with self.subTest(attrs=attrs), self.assertRaises(ValueError):
                validate_record(self.record(attributes=attrs))


if __name__ == '__main__':
    unittest.main()
