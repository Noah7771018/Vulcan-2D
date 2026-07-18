import os
import unittest

import numpy as np

from vulcan2d import model as M
from vulcan2d import serve
from vulcan2d import calibrate


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ModelTests(unittest.TestCase):
    def test_triangle_has_one_apex_and_monotone_branches(self):
        for peak in (5.0, -1.7):
            wave = M.triangle(peak)
            apex = int(np.argmax(np.abs(wave)))
            direction = np.sign(peak)
            self.assertTrue(np.all(direction * np.diff(wave[:apex + 1]) > 0))
            self.assertTrue(np.all(direction * np.diff(wave[apex:]) < 0))
            self.assertEqual(np.count_nonzero(wave == wave[apex]), 1)

    def test_hrs_and_lrs_random_terms_are_decoupled(self):
        p = M.Params()
        w = np.array([0.4, 0.6])
        low_residual = np.array([-1.0, -1.0])
        high_residual = np.array([1.0, 1.0])

        hrs_low = M.G_ensemble(np.zeros(2), low_residual, w, p, p.Gon)
        hrs_high = M.G_ensemble(np.zeros(2), high_residual, w, p, p.Gon)
        lrs_low = M.G_ensemble(np.ones(2), low_residual, w, p, p.Gon)
        lrs_high = M.G_ensemble(np.ones(2), high_residual, w, p, p.Gon)

        self.assertGreater(hrs_high, hrs_low)
        self.assertAlmostEqual(lrs_high, lrs_low)

    def test_calibrated_profile_matches_multi_seed_targets(self):
        path = os.path.join(ROOT, "vulcan2d", "vulcan2d_calibrated.npz")
        p = M.Params.from_npz(path)
        result = calibrate.audit(p)

        targets = {
            "Vset": (1.298, 25.0, 0.05, 3.0),
            "Vreset": (-1.075, 24.1, 0.05, 3.0),
            "R_HRS": (2.045e8, 45.5, 0.10, 5.0),
            "R_LRS": (2.939e5, 28.4, 0.10, 5.0),
            "Icc": (5.146e-5, 1.0, 0.03, 1.0),
        }
        for column, (mean, target_cv, mean_tol, cv_tol) in targets.items():
            actual_mean = np.median(result[column + "_mean"])
            actual_cv = np.median(result[column + "_cv"])
            self.assertLess(abs(actual_mean / mean - 1.0), mean_tol, column)
            self.assertLess(abs(actual_cv - target_cv), cv_tol, column)

        self.assertGreater(np.median(result["Vset_slope"]), 0.0)
        self.assertLess(np.median(result["lnR_HRS_slope"]), 0.0)
        self.assertGreater(np.median(result["lnR_LRS_slope"]), 0.0)

    def test_ui_default_variability_preserves_calibration(self):
        p = M.Params()
        expected = (p.sigma_lnG, p.sigma_Gon, p.sigma_theta, p.m_set, p.m_reset)
        serve._apply_overrides(p, {"sigma": [str(serve.SIGMA_UI_DEFAULT)]})
        actual = (p.sigma_lnG, p.sigma_Gon, p.sigma_theta, p.m_set, p.m_reset)
        np.testing.assert_allclose(actual, expected, rtol=1e-9)

    def test_cycle_resampling_keeps_the_same_device_structure(self):
        p = M.Params()
        _, frozen_a = M.simulate_cycles(p, n_cycles=1, seed=1)
        _, frozen_b = M.simulate_cycles(p, n_cycles=1, seed=2)
        np.testing.assert_allclose(frozen_a["w"], frozen_b["w"])
        np.testing.assert_allclose(frozen_a["dtheta"], frozen_b["dtheta"])


if __name__ == "__main__":
    unittest.main()
