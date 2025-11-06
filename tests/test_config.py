"""Tests for cogstim.helpers.constants module."""

from cogstim.helpers.constants import (
    ANS_EASY_RATIOS,
    ANS_HARD_RATIOS,
    MTS_EASY_RATIOS,
    MTS_HARD_RATIOS,
)


class TestConfigRatios:
    """Test ratio constants and their properties."""

    def test_ans_easy_ratios_properties(self):
        """Test ANS easy ratios have expected properties."""
        # All ratios should be between 0 and 1
        for ratio in ANS_EASY_RATIOS:
            assert 0 < ratio < 1, f"Ratio {ratio} should be between 0 and 1"
        
        # Should be sorted (ascending)
        assert ANS_EASY_RATIOS == sorted(ANS_EASY_RATIOS), "ANS easy ratios should be sorted"
        
        # Should contain expected ratios
        expected_ratios = [1/5, 1/4, 1/3, 2/5, 1/2, 3/5, 2/3, 3/4]
        assert ANS_EASY_RATIOS == expected_ratios, "ANS easy ratios should match expected values"

    def test_ans_hard_ratios_properties(self):
        """Test ANS hard ratios have expected properties."""
        # All ratios should be between 0 and 1
        for ratio in ANS_HARD_RATIOS:
            assert 0 < ratio < 1, f"Ratio {ratio} should be between 0 and 1"
        
        # Should be sorted (ascending)
        assert ANS_HARD_RATIOS == sorted(ANS_HARD_RATIOS), "ANS hard ratios should be sorted"
        
        # Should contain expected ratios
        expected_ratios = [4/5, 5/6, 6/7, 7/8, 8/9, 9/10, 10/11, 11/12]
        assert ANS_HARD_RATIOS == expected_ratios, "ANS hard ratios should match expected values"

    def test_mts_easy_ratios_properties(self):
        """Test MTS easy ratios have expected properties."""
        # All ratios should be between 0 and 1
        for ratio in MTS_EASY_RATIOS:
            assert 0 < ratio < 1, f"Ratio {ratio} should be between 0 and 1"
        
        # Should be sorted (ascending)
        assert MTS_EASY_RATIOS == sorted(MTS_EASY_RATIOS), "MTS easy ratios should be sorted"
        
        # Should contain expected ratios
        expected_ratios = [2/3, 3/4, 4/5, 5/6, 6/7]
        assert MTS_EASY_RATIOS == expected_ratios, "MTS easy ratios should match expected values"

    def test_mts_hard_ratios_properties(self):
        """Test MTS hard ratios have expected properties."""
        # All ratios should be between 0 and 1
        for ratio in MTS_HARD_RATIOS:
            assert 0 < ratio < 1, f"Ratio {ratio} should be between 0 and 1"
        
        # Should be sorted (ascending)
        assert MTS_HARD_RATIOS == sorted(MTS_HARD_RATIOS), "MTS hard ratios should be sorted"
        
        # Should contain expected ratios
        expected_ratios = [7/8, 8/9, 9/10, 10/11, 11/12]
        assert MTS_HARD_RATIOS == expected_ratios, "MTS hard ratios should match expected values"

    def test_ratio_sets_disjoint(self):
        """Test that easy and hard ratio sets are disjoint."""
        # ANS ratios should not overlap
        ans_overlap = set(ANS_EASY_RATIOS) & set(ANS_HARD_RATIOS)
        assert len(ans_overlap) == 0, f"ANS easy and hard ratios should not overlap, but found: {ans_overlap}"
        
        # MTS ratios should not overlap
        mts_overlap = set(MTS_EASY_RATIOS) & set(MTS_HARD_RATIOS)
        assert len(mts_overlap) == 0, f"MTS easy and hard ratios should not overlap, but found: {mts_overlap}"

    def test_ratio_precision(self):
        """Test that ratios maintain reasonable precision."""
        all_ratios = ANS_EASY_RATIOS + ANS_HARD_RATIOS + MTS_EASY_RATIOS + MTS_HARD_RATIOS
        
        for ratio in all_ratios:
            # Ratios should be representable as fractions with small denominators
            # This is a heuristic check - ratios like 1/3, 2/3 should be exact
            assert isinstance(ratio, float), f"Ratio {ratio} should be a float"
            assert not (ratio != ratio), f"Ratio {ratio} should not be NaN"
            assert ratio != float('inf'), f"Ratio {ratio} should not be infinite"
