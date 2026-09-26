import unittest

from kindlecomicconverter.KCC_gui import isDuplicateLinkedMessage, isSupportAnnouncement


class SupportContentTest(unittest.TestCase):
    def test_linkedin_referral_is_support_content(self):
        payload = {
            "name": "Give a software job referral to KCC dev! - LinkedIn",
            "link": "https://www.linkedin.com/in/example",
        }

        self.assertTrue(isSupportAnnouncement("general", payload))

    def test_regular_announcement_is_not_support_content(self):
        payload = {
            "name": "All KCC options explained/quick tutorial - YouTube",
            "link": "https://www.youtube.com/example",
        }

        self.assertFalse(isSupportAnnouncement("tutorials", payload))

    def test_duplicate_linked_message_is_suppressed(self):
        message = '<a href="https://example.com">Supported devices</a>'
        item_text = "   Supported devices"

        self.assertTrue(isDuplicateLinkedMessage(message, item_text, [item_text]))

    def test_repeated_plain_message_is_retained(self):
        message = "Conversion complete"

        self.assertFalse(isDuplicateLinkedMessage(message, message, [message]))


if __name__ == "__main__":
    unittest.main()
