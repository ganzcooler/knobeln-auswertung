from pathlib import Path

from conftest import FAKE_RESPONSES

from knobeln.domain.models import BogenRef, Gruppe
from knobeln.llm.mapping import gruppe_from_llm
from knobeln.llm.models import SpielerLLM
from knobeln.io.csv_store import load_groups, read_rows, write_groups


def _gruppe(name: str, position: int) -> Gruppe:
    data = FAKE_RESPONSES[name]
    spieler = SpielerLLM.model_validate(data["spieler"][position - 1])
    return gruppe_from_llm(
        ref=BogenRef(f"{name}-p1", name, 1),
        durchgang_nr=1,
        spieler=spieler,
        position=position,
    )


def test_roundtrip_mit_bom_und_semikolon(tmp_path: Path):
    path = tmp_path / "auswertung.csv"
    write_groups(path, [_gruppe("img1.jpg", 1)])
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "Bogen_ID;Quelle" in text

    groups, fields = load_groups(path)
    assert len(groups) == 1
    assert groups[0].punkte[0] == 110
    assert "Konflikt_Detail" in fields


def test_fehlende_spalte_wird_ergaenzt(tmp_path: Path):
    path = tmp_path / "auswertung.csv"
    path.write_text(
        "Bogen_ID;Quelle;Seite;Spieler_Position;Durchgang_Nr;Spieler_Nr;"
        "Spieler_Name;Wurf_Nr;Punkte;Punkte_Roh;Korrektur;Summe_Bogen;"
        "Summe_Berechnet;Delta;Status;Warnung;Konflikt;Geprueft;Kommentar\n"
        "b;x;1;1;1;41;;1;110;110;;590;590;0;ok;;nein;nein;\n",
        encoding="utf-8",
    )
    rows, fields = read_rows(path)
    assert "Konflikt_Detail" in fields
    assert "Namenskonflikt" in fields
    assert "Summe_Bogen_Roh" in fields
    assert rows[0]["Punkte"] == "110"


def test_unbekannte_spalte_bleibt(tmp_path: Path):
    path = tmp_path / "auswertung.csv"
    write_groups(path, [_gruppe("img1.jpg", 1)])
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("Kommentar\n", "Kommentar;Eigene_Spalte\n", 1)
    lines = text.splitlines()
    lines[1] = lines[1] + ";notiz"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    groups, fields = load_groups(path)
    assert "Eigene_Spalte" in fields
    write_groups(path, groups, fields)

    neue_zeilen, _ = read_rows(path)
    assert "Eigene_Spalte" in fields
    wurf1 = next(row for row in neue_zeilen if row["Wurf_Nr"] == "1")
    assert wurf1["Eigene_Spalte"] == "notiz"


def test_komma_csv_wird_gelesen(tmp_path: Path):
    path = tmp_path / "auswertung.csv"
    path.write_text(
        "Bogen_ID,Quelle,Seite,Spieler_Position,Durchgang_Nr,Spieler_Nr,"
        "Spieler_Name,Wurf_Nr,Punkte,Punkte_Roh,Korrektur,Summe_Bogen,"
        "Summe_Berechnet,Delta,Status,Warnung,Konflikt,Geprueft,Kommentar\n"
        "b,x,1,1,1,41,,1,110,110,,590,590,0,ok,,nein,nein,\n",
        encoding="utf-8",
    )
    rows, _ = read_rows(path)
    assert rows[0]["Bogen_ID"] == "b"
    assert rows[0]["Punkte"] == "110"
