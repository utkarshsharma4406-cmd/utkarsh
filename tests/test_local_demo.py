import unittest

from local_demo import handle_message


class ReceptionistConversationTests(unittest.TestCase):
    def test_general_question_and_unknown_clinic_details(self):
        state = {}
        self.assertIn("photo ID", handle_message(state, "What should I bring?"))
        self.assertIn("don't have", handle_message(state, "Are you open Saturday?"))

    def test_appointment_intake_and_unconfirmed_request(self):
        state = {}
        self.assertIn("What name", handle_message(state, "I'd like an appointment"))
        self.assertIn("phone number", handle_message(state, "Alex Example"))
        self.assertIn("Is that correct", handle_message(state, "555-010-1234"))
        self.assertIn("What date", handle_message(state, "yes"))
        self.assertIn("What time", handle_message(state, "next Tuesday"))
        result = handle_message(state, "2 pm")
        self.assertIn("not a confirmed appointment", result)
        self.assertNotIn("step", state)

    def test_invalid_phone_is_not_saved(self):
        state = {"step": "phone", "name": "Alex"}
        self.assertIn("7 to 15 digits", handle_message(state, "123"))
        self.assertNotIn("phone", state)

    def test_emergency_and_diagnosis_are_not_handled_as_booking(self):
        state = {}
        self.assertIn("emergency services", handle_message(state, "This is an emergency"))
        self.assertIn("can't diagnose", handle_message(state, "Can you diagnose this?"))
        self.assertNotIn("step", state)


if __name__ == "__main__":
    unittest.main()
