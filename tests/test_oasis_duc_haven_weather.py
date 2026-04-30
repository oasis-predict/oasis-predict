import unittest

from scripts.oasis_duc_haven_weather import (
    TemperatureEstimate,
    answer_high_temperature_question,
    consensus_from_estimates,
    format_answer,
    normalize_city,
)


class OasisDucHavenWeatherTest(unittest.TestCase):
    def test_normalize_city_aliases(self):
        self.assertEqual(normalize_city('Los Angeles'), 'LA')
        self.assertEqual(normalize_city('NYC'), 'NYC')
        self.assertEqual(normalize_city('Miami'), 'MIAMI')

    def test_tight_consensus_allows_buy_yes(self):
        result = consensus_from_estimates([
            TemperatureEstimate('NOAA/NWS hourly', 80.0, 0.46, True, 'official'),
            TemperatureEstimate('Open-Meteo', 80.2, 0.24, False, 'derived'),
            TemperatureEstimate('MET Norway', 79.9, 0.20, True, 'official'),
        ])

        self.assertEqual(result['trade_signal'], 'BUY_YES')
        self.assertLessEqual(result['std_dev_f'], 0.50)
        self.assertTrue(result['noaa_is_aggregator'])

    def test_loose_consensus_blocks_buy_yes(self):
        result = consensus_from_estimates([
            TemperatureEstimate('NOAA/NWS hourly', 80.0, 0.46, True, 'official'),
            TemperatureEstimate('Open-Meteo', 83.0, 0.24, False, 'derived'),
            TemperatureEstimate('MET Norway', 78.0, 0.20, True, 'official'),
        ])

        self.assertEqual(result['trade_signal'], 'NO_TRADE')
        self.assertFalse(result['exact_band_ok'])

    def test_format_answer_contains_core_fields(self):
        result = consensus_from_estimates([
            TemperatureEstimate('NOAA/NWS hourly', 80.0, 0.46, True, 'official'),
            TemperatureEstimate('Open-Meteo', 80.2, 0.24, False, 'derived'),
            TemperatureEstimate('MET Norway', 79.9, 0.20, True, 'official'),
        ])
        result.update({'city': 'Los Angeles', 'target_date': '2026-04-18', 'errors': {}})

        text = format_answer(result)

        self.assertIn('Oasis__Duc_Haven_Weather', text)
        self.assertIn('Estimated high:', text)
        self.assertIn('Signal: BUY_YES', text)

    def test_question_city_detection_uses_consensus_function(self):
        # Smoke-test city parsing path without network by monkeypatching the module function.
        import scripts.oasis_duc_haven_weather as oasis

        original = oasis.get_high_temperature_consensus
        try:
            oasis.get_high_temperature_consensus = lambda city, _date: {'city_code': city}
            self.assertEqual(answer_high_temperature_question('Highest temperature in Miami today?')['city_code'], 'MIAMI')
        finally:
            oasis.get_high_temperature_consensus = original


if __name__ == '__main__':
    unittest.main()
