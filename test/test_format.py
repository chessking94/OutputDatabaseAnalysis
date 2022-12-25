import unittest

from chess.engine import Mate

from src.format import calc_phase, calc_timespent, format_eval, get_date, get_name, get_result, get_sourceid, get_tag


class TestFormat(unittest.TestCase):
    def test_calc_phase(self):
        # endgames
        self.assertEqual(calc_phase('2b1Q3/p6p/1p3pk1/2pP4/P1P3q1/1P3N2/5P2/5K2 b - - 7 38', 3), 3)  # last phase = 3
        self.assertEqual(calc_phase('2b2k2/p2q1p1p/1p1p1Q2/2pP4/P1P3P1/1P3N2/5P2/5K2 b - - 0 32', 2), 3)  # majors/minors <= 6

        # middlegames
        self.assertEqual(calc_phase('r1bqn1k1/pppp1ppp/5b2/8/3P4/8/PPP2PPP/RNBQ1BK1 w - - 0 12', 1), 2)  # majors/minors <= 10
        self.assertEqual(calc_phase('r1q1r1k1/pbpn1pbp/1p1pp1p1/6B1/2PPP3/P2B1N2/1P1Q1PPP/1R2R1K1 b - - 7 15', 1), 2)  # white back rank < 4
        self.assertEqual(calc_phase('r2q1rk1/1bp1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 w - - 0 10', 1), 2)  # black back rank < 4
        self.assertEqual(calc_phase('r1q1r1k1/pbpn1pbp/1p1pp1p1/6B1/2PPP3/P2B1N2/1P1Q1PPP/1R2R1K1 b - - 7 15', 2), 2)  # last phase = 2

        # opening
        self.assertEqual(calc_phase('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 1), 1)  # no middlegame/endgame criteria were met

    def test_calc_timespent(self):
        self.assertEqual(calc_timespent(100, 90, 5), 15)
        self.assertEqual(calc_timespent(100, 103, 5), 2)
        self.assertEqual(calc_timespent(100, 90, 0), 10)
        self.assertEqual(calc_timespent(100, 103, 0), 0)
        self.assertEqual(calc_timespent(None, 180, 3), 0)
        self.assertEqual(calc_timespent(180, None, 3), '')

    def test_format_eval(self):
        self.assertEqual(format_eval('#+3'), Mate(+3))
        self.assertEqual(format_eval('10'), 0.1)
        self.assertEqual(format_eval('-125'), -1.25)
        self.assertEqual(format_eval('0'), 0)

    def test_get_date(self):
        self.assertEqual(get_date('2022.01.02'), ['2022.01.02', '2021-12'])
        self.assertEqual(get_date('2021.12.01'), ['2021.12.01', '2021-11'])
        self.assertEqual(get_date('2021.10.01'), ['2021.10.01', '2021-09'])
        self.assertEqual(get_date('1899.??.??'), ['1899.01.01', '1898-12'])
        self.assertEqual(get_date('1899.03.??'), ['1899.03.01', '1899-02'])
        self.assertEqual(get_date('1899.??.01'), ['1899.01.01', '1898-12'])
        self.assertEqual(get_date(None), ['', None])

    def test_get_name(self):
        self.assertEqual(get_name(None), ['', ''])
        self.assertEqual(get_name('Last, First'), ['Last', 'First'])
        self.assertEqual(get_name('Last'), ['Last', ''])
        self.assertEqual(get_name(', First'), [', First', ''])
        self.assertEqual(get_name(' , First'), ['', 'First'])

    def test_get_result(self):
        self.assertEqual(get_result(None), '')
        self.assertEqual(get_result('1-0'), '1.0')
        self.assertEqual(get_result('0-1'), '0.0')
        self.assertEqual(get_result('1/2-1/2'), '0.5')

    def test_get_sourceid(self):
        self.assertEqual(get_sourceid(None, None, None), ['', ''])
        self.assertEqual(get_sourceid('https://lichess.org/wijf97Ts', None, None), ['Lichess', 'wijf97Ts'])
        self.assertEqual(get_sourceid('Chess.com', 'https://www.chess.com/game/live/9664507939', None), ['Chess.com', '9664507939'])
        self.assertEqual(get_sourceid('FICS freechess.org', None, '311053399'), ['FICS', '311053399'])

    def test_get_tag(self):
        self.assertEqual(get_tag(None), '')
        self.assertEqual(get_tag('D44'), 'D44')


if __name__ == '__main__':
    unittest.main()
