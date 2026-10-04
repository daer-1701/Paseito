import unittest
from unittest.mock import patch
from app import identity


class PointsIdentityTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch('app.identity.time.monotonic', return_value=100)
        self.now = self.clock.start()
        self.addCleanup(self.clock.stop)
        for mapping in (identity._grants, identity._attempts):
            isolated = patch.dict(mapping, {}, clear=True)
            isolated.start()
            self.addCleanup(isolated.stop)
        self.ticket = identity.begin('conversation')
        self.token = identity.issue('conversation', self.ticket, user=1)

    def test_cookie_and_conversation_are_both_required(self):
        self.assertIsNotNone(identity.get(self.token, 'conversation'))
        self.assertIsNone(identity.get(self.token, 'another'))
        self.assertIsNone(identity.get(None, 'conversation'))
        self.assertNotIn('user_id', identity.public(identity.get(self.token, 'conversation')))

    def test_ninety_seconds_of_inactivity_revokes_access(self):
        self.now.return_value = 190
        self.assertIsNone(identity.get(self.token, 'conversation', touch=True))

    def test_activity_cannot_extend_ten_minute_limit(self):
        for now in range(150, 700, 50):
            self.now.return_value = now
            self.assertIsNotNone(identity.get(self.token, 'conversation', touch=True))
        self.now.return_value = 700
        self.assertIsNone(identity.get(self.token, 'conversation', touch=True))

    def test_reset_cancels_pending_validation_and_current_grant(self):
        identity.revoke_session('conversation')
        self.assertIsNone(identity.get(self.token, 'conversation'))
        self.assertIsNone(identity.issue('conversation', self.ticket, user=1))


if __name__ == '__main__':
    unittest.main()
