from commanderai.collection.parser import parse_collection


def test_parse_simple_lines():
    text = """1 Sol Ring
2 Forest
1 Atraxa, Praetors' Voice"""
    entries = parse_collection(text)
    assert len(entries) == 3
    assert entries[0].quantity == 1
    assert entries[0].card_name == "Sol Ring"
    assert entries[1].quantity == 2
    assert entries[1].card_name == "Forest"
    assert entries[2].card_name == "Atraxa, Praetors' Voice"


def test_parse_with_set_code():
    text = "1 Sol Ring (C21)\n1 Command Tower (CMR) 350"
    entries = parse_collection(text)
    assert len(entries) == 2
    assert entries[0].set_code == "C21"
    assert entries[1].set_code == "CMR"
    assert entries[1].collector_number == "350"


def test_parse_with_x_quantity():
    text = "4x Lightning Bolt\n2x Counterspell"
    entries = parse_collection(text)
    assert len(entries) == 2
    assert entries[0].quantity == 4
    assert entries[0].card_name == "Lightning Bolt"


def test_skip_comments():
    text = """# This is a comment
// Also a comment
1 Sol Ring
"""
    entries = parse_collection(text)
    assert len(entries) == 1
    assert entries[0].card_name == "Sol Ring"


def test_parse_csv():
    text = """Name,Quantity,Set
Sol Ring,1,C21
Command Tower,2,CMR
"""
    entries = parse_collection(text)
    assert len(entries) == 2
    assert entries[0].card_name == "Sol Ring"
    assert entries[0].quantity == 1
    assert entries[1].card_name == "Command Tower"
    assert entries[1].quantity == 2


def test_parse_empty():
    assert parse_collection("") == []
    assert parse_collection("   \n\n  ") == []
