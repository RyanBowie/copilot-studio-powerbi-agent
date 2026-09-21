"""Keep publication exceptions narrow: public discovery and two test-only fictional origins."""
import re
import unittest

from validate_publication import has_private_tenant_url


class PublicationPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.pattern = re.compile(
            r"https://[A-Za-z0-9-]+\.(?:crm\d*\.dynamics\.com|onmicrosoft\.com)", re.I)

    def test_public_discovery_endpoint_is_not_a_private_tenant(self):
        self.assertFalse(has_private_tenant_url("agent/configure_portable.py",
                                               "https://globaldisco.crm.dynamics.com", self.pattern))

    def test_fictional_origins_are_only_exempt_in_their_test_source(self):
        for name in ("synthetic", "other"):
            origin = "https://" + name + ".crm.dynamics.com"
            self.assertFalse(has_private_tenant_url(
                "agent\\tests\\test_portable_runtime.py", origin, self.pattern))
            for path in ("agent/configure_portable.py", "solution/src/bots/runtime/configuration.json",
                         "solution/runtime.zip::agent/tests/test_portable_runtime.py"):
                self.assertTrue(has_private_tenant_url(path, origin, self.pattern))

    def test_public_endpoint_does_not_hide_a_second_private_origin(self):
        text = "https://globaldisco.crm.dynamics.com https://" + "private" + ".crm.dynamics.com"
        self.assertTrue(has_private_tenant_url("agent/configure_portable.py", text, self.pattern))


if __name__ == "__main__":
    unittest.main()
