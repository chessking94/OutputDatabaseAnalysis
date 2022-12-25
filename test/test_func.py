import os
import unittest

from src.func import tbeval, get_conf, get_config, piececount, get_parentdirs

CONFIG_PATH = os.path.dirname(os.path.dirname(__file__))


class TestFunc(unittest.TestCase):
    def test_tbeval(self):
        self.assertEqual(tbeval(['Ke4', '2', '1']), '#+2')
        self.assertEqual(tbeval(['Ke4', '-2', '1']), '#-2')
        self.assertEqual(tbeval(['Ke4', '0', '0']), '0.00')
        self.assertEqual(tbeval(['Ke4', None, '2']), '#+2Z')
        self.assertEqual(tbeval(['Ke4', None, '-2']), '#-2Z')
        self.assertEqual(tbeval(['Ke4', None, '0']), '0.00')

    def test_conf(self):
        self.assertIsNotNone(get_conf('LichessAPIToken'))
        self.assertIsNotNone(get_conf('SqlServerConnectionStringTrusted'))

    def test_config(self):
        self.assertTrue(os.path.isfile(os.path.join(CONFIG_PATH, 'config.json')))
        self.assertIsNotNone(get_config(CONFIG_PATH, 'rootPath'))

    def test_piececount(self):
        self.assertEqual(piececount('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'), 32)
        self.assertEqual(piececount('3r2k1/p4p1p/6p1/8/1P6/2RpB2P/5PP1/n5K1 w - - 0 33'), 15)
        self.assertEqual(piececount('8/8/8/8/6k1/6pp/6P1/6K1 w - - 0 91'), 5)

    def test_get_parentdirs(self):
        self.assertEqual(get_parentdirs('C:\\Windows\\System32', 0), 'C:\\Windows\\System32')
        self.assertEqual(get_parentdirs('C:\\Windows\\System32', 1), 'C:\\Windows')
        self.assertEqual(get_parentdirs('C:\\Windows\\System32', 2), 'C:\\')


if __name__ == '__main__':
    unittest.main()
