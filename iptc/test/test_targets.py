# -*- coding: utf-8 -*-

import unittest
import iptc

class TestTarget(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_target_create(self):
        rule = iptc.Rule()
        target = rule.create_target("MARK")

        self.failUnless(rule.target == target)

        target.set_mark = "0x123"

        t = iptc.Target(iptc.Rule(), "MARK")
        t.set_mark = "0x123"

        self.failUnless(t == target)

    def test_target_compare(self):
        t1 = iptc.Target(iptc.Rule(), "MARK")
        t1.set_mark = "0x123"

        t2 = iptc.Target(iptc.Rule(), "MARK")
        t2.set_mark = "0x123"

        self.failUnless(t1 == t2)

        t2.reset()
        t2.set_mark = "0x124"
        self.failIf(t1 == t2)

class TestXTClusteripTarget(unittest.TestCase):
    def setUp(self):
        self.rule = iptc.Rule()
        self.rule.dst = "127.0.0.2"
        self.rule.protocol = "tcp"
        self.rule.in_interface = "eth0"

        self.match = iptc.Match(self.rule, "tcp")
        self.rule.add_match(self.match)

        self.target = iptc.Target(self.rule, "CLUSTERIP")
        self.rule.target = self.target

        self.chain = iptc.Chain(iptc.TABLE_FILTER, "iptc_test_clusterip")
        iptc.TABLE_FILTER.create_chain(self.chain)

    def tearDown(self):
        self.chain.flush()
        self.chain.delete()

    def test_mode(self):
        for hashmode in ["sourceip", "sourceip-sourceport",
                "sourceip-sourceport-destport"]:
            self.target.new = ""
            self.target.hashmode = hashmode
            self.assertEquals(self.target.hashmode, hashmode)
            self.target.reset()
        for hashmode in ["asdf", "1234"]:
            self.target.new = ""
            try:
                self.target.hashmode = hashmode
            except Exception, e:
                pass
            else:
                self.fail("CLUSTERIP accepted invalid value %s" % (hashmode))
            self.target.reset()

    def test_insert(self):
        self.target.reset()
        self.target.new = ""
        self.target.hashmode = "sourceip"
        self.target.clustermac = "01:02:03:04:05:06"
        self.target.local_node = "1"
        self.target.total_nodes = "2"
        self.rule.target = self.target

        self.chain.insert_rule(self.rule)

        for r in self.chain.rules:
            if r != self.rule:
                self.chain.delete_rule(self.rule)
                self.fail("inserted rule does not match original")

        self.chain.delete_rule(self.rule)

class TestIPTRedirectTarget(unittest.TestCase):
    def setUp(self):
        self.rule = iptc.Rule()
        self.rule.dst = "127.0.0.2"
        self.rule.protocol = "tcp"
        self.rule.in_interface = "eth0"

        self.match = iptc.Match(self.rule, "tcp")
        self.rule.add_match(self.match)

        self.target = iptc.Target(self.rule, "REDIRECT")
        self.rule.target = self.target

        self.chain = iptc.Chain(iptc.TABLE_NAT, "iptc_test_redirect")
        iptc.TABLE_NAT.create_chain(self.chain)

    def tearDown(self):
        self.chain.flush()
        self.chain.delete()

    def test_mode(self):
        for port in ["1234", "1234-2345", "65534-65535"]:
            self.target.to_ports = port
            self.assertEquals(self.target.to_ports, port)
            self.target.reset()
        self.target.random = ""
        self.target.reset()
        for port in ["1234567", "2345-1234"]: # ipt bug: it accepts strings
            try:
                self.target.to_ports = port
            except Exception, e:
                pass
            else:
                self.fail("REDIRECT accepted invalid value %s" % (port))
            self.target.reset()

    def test_insert(self):
        self.target.reset()
        self.target.to_ports = "1234-1235"
        self.rule.target = self.target

        self.chain.insert_rule(self.rule)

        for r in self.chain.rules:
            if r != self.rule:
                self.chain.delete_rule(self.rule)
                self.fail("inserted rule does not match original")

        self.chain.delete_rule(self.rule)

class TestXTTosTarget(unittest.TestCase):
    def setUp(self):
        self.rule = iptc.Rule()
        self.rule.dst = "127.0.0.2"
        self.rule.protocol = "tcp"
        self.rule.in_interface = "eth0"

        self.match = iptc.Match(self.rule, "tcp")
        self.rule.add_match(self.match)

        self.target = iptc.Target(self.rule, "TOS")
        self.rule.target = self.target

        self.chain = iptc.Chain(iptc.TABLE_MANGLE, "iptc_test_tos")
        iptc.TABLE_MANGLE.create_chain(self.chain)

    def tearDown(self):
        self.chain.flush()
        self.chain.delete()

    def test_mode(self):
        for tos in ["0x12/0xff", "0x12/0x0f"]:
            self.target.set_tos = tos
            self.assertEquals(self.target.set_tos, tos)
            self.target.reset()
        for tos in [("Minimize-Delay", "0x10/0x3f"),
                    ("Maximize-Throughput", "0x08/0x3f"),
                    ("Maximize-Reliability", "0x04/0x3f"),
                    ("Minimize-Cost", "0x02/0x3f"),
                    ("Normal-Service", "0x00/0x3f")]:
            self.target.set_tos = tos[0]
            self.assertEquals(self.target.set_tos, tos[1])
            self.target.reset()
        for tos in ["0x04"]:
            self.target.and_tos = tos
            self.assertEquals(self.target.set_tos, "0x00/0xfb")
            self.target.reset()
            self.target.or_tos = tos
            self.assertEquals(self.target.set_tos, "0x04/0x04")
            self.target.reset()
            self.target.xor_tos = tos
            self.assertEquals(self.target.set_tos, "0x04/0x00")
            self.target.reset()
        for tos in ["0x1234", "0x12/0xfff", "asdf", "Minimize-Bullshit"]:
            try:
                self.target.and_tos = tos
            except Exception, e:
                pass
            else:
                self.fail("TOS accepted invalid value %s" % (tos))
            self.target.reset()
            try:
                self.target.or_tos = tos
            except Exception, e:
                pass
            else:
                self.fail("TOS accepted invalid value %s" % (tos))
            self.target.reset()
            try:
                self.target.xor_tos = tos
            except Exception, e:
                pass
            else:
                self.fail("TOS accepted invalid value %s" % (tos))
            self.target.reset()

    def test_insert(self):
        self.target.reset()
        self.target.set_tos = "0x12/0xff"
        self.rule.target = self.target

        self.chain.insert_rule(self.rule)

        for r in self.chain.rules:
            if r != self.rule:
                self.chain.delete_rule(self.rule)
                self.fail("inserted rule does not match original")

        self.chain.delete_rule(self.rule)

class TestIPTMasqueradeTarget(unittest.TestCase):
    def setUp(self):
        self.rule = iptc.Rule()
        self.rule.dst = "127.0.0.2"
        self.rule.protocol = "tcp"
        self.rule.out_interface = "eth0"

        self.target = iptc.Target(self.rule, "MASQUERADE")
        self.rule.target = self.target

        self.chain = iptc.Chain(iptc.TABLE_NAT, "POSTROUTING")

    def tearDown(self):
        pass

    def test_mode(self):
        for port in ["1234", "1234-2345"]:
            self.target.to_ports = port
            self.assertEquals(self.target.to_ports, port)
            self.target.reset()
        self.target.random = ""
        self.target.reset()
        for port in ["123456", "1234-1233", "asdf"]:
            try:
                self.target.to_ports = port
            except Exception, e:
                pass
            else:
                self.fail("MASQUERADE accepted invalid value %s" % (port))
            self.target.reset()

    def test_insert(self):
        self.target.reset()
        self.target.to_ports = "1234"
        self.rule.target = self.target

        self.chain.insert_rule(self.rule)

        found = False
        for r in self.chain.rules:
            if r == self.rule:
                found = True
                break

        self.chain.delete_rule(self.rule)

        if not found:
            self.fail("inserted rule does not match original")

def suite():
    suite_target = unittest.TestLoader().loadTestsFromTestCase(TestTarget)
    suite_cluster = \
            unittest.TestLoader().loadTestsFromTestCase(TestXTClusteripTarget)
    suite_redir = \
            unittest.TestLoader().loadTestsFromTestCase(TestIPTRedirectTarget)
    suite_tos = unittest.TestLoader().loadTestsFromTestCase(TestXTTosTarget)
    suite_masq = \
            unittest.TestLoader().loadTestsFromTestCase(TestIPTMasqueradeTarget)
    return unittest.TestSuite([suite_target, suite_cluster, suite_redir,
        suite_tos, suite_masq])

def run_tests():
    unittest.TextTestRunner(verbosity=2).run(suite())

if __name__ == "__main__":
    unittest.main()