import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from scoring import score_sequence

def test_known_amp():
    result = score_sequence("GIGKFLHSAKKFGKAFVGEIMNS")
    assert result["length"] == 23
    assert result["length_valid"] == True
    assert 2.5 <= result["charge"] <= 6.0
    assert result["hemolysis"] in ["low", "medium"]

def test_length_flag():
    result = score_sequence("KLFK")
    assert result["length_valid"] == False

def test_high_charge():
    result = score_sequence("KKKKKKKKKRRRR")
    assert result["charge"] > 8

def test_composite_range():
    result = score_sequence("KLFKKLKKIGAVLKVLTTGLPALIS")
    assert 0.0 <= result["composite_score"] <= 1.0

def test_all_fields_present():
    result = score_sequence("KLFKKLKKIGAVLKVLTTGLPALIS")
    for key in ["sequence","length","charge","hydrophobicity","amphipathicity",
                "hemolysis","toxicity","mic_estimate","length_valid","composite_score"]:
        assert key in result
