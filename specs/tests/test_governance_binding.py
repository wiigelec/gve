from __future__ import annotations

import copy
import unittest

from specs.tooling.governance_binding import (
    CORE_AUTHORITY_KIND,
    GOVERNANCE_BINDING_FORMAT,
    IDENTITY_FORMAT,
    PLUGIN_AUTHORITY_KIND,
    GovernanceBindingError,
    canonical_governance_binding,
    governance_binding_identity,
    require_current_authorities,
    validate_governance_binding,
)


CORE = "1" * 64
PLUGIN_A = "2" * 64
PLUGIN_B = "3" * 64


class GovernanceBindingTests(unittest.TestCase):
    def plugins(self):
        return [
            {
                "authority_id": "plugin-b",
                "authority_kind": PLUGIN_AUTHORITY_KIND,
                "revision": PLUGIN_B,
            },
            {
                "authority_id": "plugin-a",
                "authority_kind": PLUGIN_AUTHORITY_KIND,
                "revision": PLUGIN_A,
            },
        ]

    def test_binding_is_deterministic_across_discovery_order(self):
        forward = canonical_governance_binding(CORE, self.plugins())
        reverse = canonical_governance_binding(CORE, reversed(self.plugins()))
        self.assertEqual(forward, reverse)
        self.assertEqual(governance_binding_identity(forward), governance_binding_identity(reverse))
        self.assertEqual(
            forward,
            {
                "binding_format": GOVERNANCE_BINDING_FORMAT,
                "identity_format": IDENTITY_FORMAT,
                "authorities": [
                    {
                        "authority_id": "gve-core",
                        "authority_kind": CORE_AUTHORITY_KIND,
                        "revision": CORE,
                    },
                    {
                        "authority_id": "plugin-a",
                        "authority_kind": PLUGIN_AUTHORITY_KIND,
                        "revision": PLUGIN_A,
                    },
                    {
                        "authority_id": "plugin-b",
                        "authority_kind": PLUGIN_AUTHORITY_KIND,
                        "revision": PLUGIN_B,
                    },
                ],
            },
        )
        self.assertEqual(
            governance_binding_identity(forward),
            "dba2f05fd217ea43783f7606e2d70f5a79eb7e0d6e6dfcd6fbfffa939bdf75ba",
        )

    def test_current_core_and_plugins_pass(self):
        binding = canonical_governance_binding(CORE, self.plugins())
        require_current_authorities(
            binding,
            {
                (CORE_AUTHORITY_KIND, "gve-core"): CORE,
                (PLUGIN_AUTHORITY_KIND, "plugin-a"): PLUGIN_A,
                (PLUGIN_AUTHORITY_KIND, "plugin-b"): PLUGIN_B,
            },
        )

    def test_stale_core_fails_even_when_plugins_are_current(self):
        binding = canonical_governance_binding(CORE, self.plugins())
        with self.assertRaisesRegex(GovernanceBindingError, "stale for gve-core"):
            require_current_authorities(
                binding,
                {
                    (CORE_AUTHORITY_KIND, "gve-core"): "4" * 64,
                    (PLUGIN_AUTHORITY_KIND, "plugin-a"): PLUGIN_A,
                    (PLUGIN_AUTHORITY_KIND, "plugin-b"): PLUGIN_B,
                },
            )

    def test_stale_plugin_fails_even_when_core_is_current(self):
        binding = canonical_governance_binding(CORE, self.plugins())
        with self.assertRaisesRegex(GovernanceBindingError, "stale for plugin-a"):
            require_current_authorities(
                binding,
                {
                    (CORE_AUTHORITY_KIND, "gve-core"): CORE,
                    (PLUGIN_AUTHORITY_KIND, "plugin-a"): "4" * 64,
                    (PLUGIN_AUTHORITY_KIND, "plugin-b"): PLUGIN_B,
                },
            )

    def test_missing_plugin_authority_fails(self):
        binding = canonical_governance_binding(CORE, self.plugins())
        with self.assertRaisesRegex(GovernanceBindingError, "missing for plugin-b"):
            require_current_authorities(
                binding,
                {
                    (CORE_AUTHORITY_KIND, "gve-core"): CORE,
                    (PLUGIN_AUTHORITY_KIND, "plugin-a"): PLUGIN_A,
                },
            )

    def test_duplicate_plugin_authority_fails(self):
        plugins = self.plugins()
        plugins.append(copy.deepcopy(plugins[0]))
        with self.assertRaisesRegex(GovernanceBindingError, "must be unique"):
            canonical_governance_binding(CORE, plugins)

    def test_noncanonical_order_fails(self):
        binding = canonical_governance_binding(CORE, self.plugins())
        binding["authorities"][1:] = reversed(binding["authorities"][1:])
        with self.assertRaisesRegex(GovernanceBindingError, "ordered by authority_id"):
            validate_governance_binding(binding)

    def test_unknown_authority_kind_fails(self):
        binding = canonical_governance_binding(CORE, self.plugins())
        binding["authorities"][1]["authority_kind"] = "unknown"
        with self.assertRaisesRegex(GovernanceBindingError, "unknown"):
            validate_governance_binding(binding)

    def test_human_name_cannot_mask_content_change(self):
        first = canonical_governance_binding(CORE, self.plugins())
        changed = canonical_governance_binding(
            CORE,
            [
                {
                    "authority_id": "plugin-a",
                    "authority_kind": PLUGIN_AUTHORITY_KIND,
                    "revision": "4" * 64,
                },
                self.plugins()[0],
            ],
        )
        self.assertNotEqual(
            governance_binding_identity(first),
            governance_binding_identity(changed),
        )


if __name__ == "__main__":
    unittest.main()
