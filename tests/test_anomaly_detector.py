import unittest
from lambdas.anomaly_alerter.anomaly_detector import detect_anomalies

class TestAnomalyDetector(unittest.TestCase):
    def test_spike_detected(self):
        data = {'Amazon EC2': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 4.0]}
        anomalies = detect_anomalies(data)
        self.assertEqual(len(anomalies), 1)
        self.assertGreater(anomalies[0]['pct_change'], 100)

    def test_stable_not_flagged(self):
        data = {'Amazon S3': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.51]}
        anomalies = detect_anomalies(data)
        self.assertEqual(len(anomalies), 0)

    def test_noise_filter(self):
        # Spikes below $1 should be ignored
        data = {'AWS Config': [0.01]*7 + [0.05]}
        anomalies = detect_anomalies(data, min_spend=1.0)
        self.assertEqual(len(anomalies), 0)

    def test_multiple_services(self):
        data = {
            'Amazon EC2': [1.0]*7 + [5.0], # spike
            'Amazon S3': [0.5]*7 + [0.5],  # stable
            'Amazon RDS': [2.0]*7 + [8.0], # spike
        }
        anomalies = detect_anomalies(data)
        self.assertEqual(len(anomalies), 2)
        services = [a['service'] for a in anomalies]
        self.assertIn('Amazon EC2', services)
        self.assertIn('Amazon RDS', services)
        self.assertNotIn('Amazon S3', services)

    def test_sorted_by_biggest_spike(self):
        data = {
            'Amazon EC2': [1.0]*7 + [3.0],
            'Amazon RDS': [1.0]*7 + [10.0],
        }
        anomalies = detect_anomalies(data)
        self.assertGreater(anomalies[0]['pct_change'], anomalies[1]['pct_change'])
        self.assertEqual(anomalies[0]['service'], 'Amazon RDS')

if __name__ == '__main__':
    unittest.main()
