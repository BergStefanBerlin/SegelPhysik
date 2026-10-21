from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from segelphysik.core.auftrieb import Vektor
from segelphysik.core.frames import Pose
from segelphysik.core.kraftmodell import (
    KraftErgebnis, Kraftbeitrag, Wrench, aggregiere_kraftbeitraege,
)
from segelphysik.core.kraefte_anzeige import (
    Datenstatus, KraefteAnzeigeAdapter, Quellbezug,
)
from segelphysik.core.pfeilstil import BEITRAGS_DEFINITIONEN, GRUPPEN_TITEL
from segelphysik.gui.kraefte_werte import (
    BEITRAG_ROLLE, ID_ROLLE, SNAPSHOT_ROLLE, SPALTEN,
    KraefteWerteFenster, KraefteWerteModell,
)

pytestmark = [pytest.mark.gui, pytest.mark.integration]

P = (0.0, 0.0, 0.0)
FRAME = "simulationsframe"


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(params=("python", "cpp"), autouse=True)
def backend(request, monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", request.param)


def _snapshot(koerper="boot", *, generation=2, sequenz=3, fehlend=False,
              hydro=(0, 0, 48000)):
    quellen = (
        Quellbezug("gewicht", "schwerkraft", originalangriff_m=P),
        Quellbezug("auftrieb", "hydrostatik", originalangriff_m=(0, .35, 0)),
        Quellbezug("rumpf_1", "hydrodynamik_rumpf"),
        Quellbezug("rumpf_2", "hydrodynamik_rumpf"),
    )
    beitraege = (
        Kraftbeitrag("schwerkraft", Wrench(FRAME, P, (0, 0, -49050), P)),
        Kraftbeitrag("hydrostatik", Wrench(FRAME, (0, .35, 0), hydro, P)),
        Kraftbeitrag("hydrodynamik_rumpf", Wrench(FRAME, P, (-100, 0, 0), P)),
        Kraftbeitrag("hydrodynamik_rumpf", Wrench(FRAME, P, (-200, 0, 0), P)),
    )
    erwartet = quellen
    if fehlend:
        erwartet += (Quellbezug(
            "added_mass", "added_mass", Datenstatus.NICHT_BERECHNET),)
    gesamt, beitraege = aggregiere_kraftbeitraege(beitraege, P)
    ergebnis = KraftErgebnis(
        SimpleNamespace(), Vektor(gesamt.kraft_N), Vektor(gesamt.moment_Nm),
        (0.0,) * 6, beitraege, P, True)
    return KraefteAnzeigeAdapter().snapshot(
        ergebnis, koerper_id=koerper, generation=generation, sequenz=sequenz,
        zeit_s=12.4, kraftpose=Pose(FRAME, "koerper", P, (1, 0, 0, 0)),
        quellen=quellen, erwartet=erwartet, masse_kg=5000, g_m_s2=9.81)


def _modell(app, *snapshots):
    modell = KraefteWerteModell()
    modell.snapshots_setzen(snapshots or (_snapshot(),))
    return modell


def test_koerperwahl_zeigt_nicht_berechnete_koerper_ohne_erfundene_nullwerte(fenster):
    fenster.koerper_setzen(("boot", "anderes"))
    fenster.snapshots_setzen((_snapshot(),))
    fenster.koerperwahl.setCurrentIndex(1)
    assert fenster.koerperwahl.currentData() == "anderes"
    assert fenster.modell.rowCount() == 0
    assert all(not karte.text() for karte in fenster.karten)
    assert "Nicht berechnet" in fenster.datenstatus.text()
    assert "anderes" in fenster.datenstatus.text()
    # Ein späteres Ergebnis wird ohne physische Aktivierungsänderung übernommen.
    fenster.snapshots_setzen((_snapshot(), _snapshot("anderes")))
    assert fenster.koerperwahl.currentData() == "anderes"
    assert fenster.modell.rowCount() == 1
    assert not fenster.datenstatus.text()
    fenster.snapshots_setzen(())
    assert fenster.koerperwahl.count() == 2
    assert fenster.modell.rowCount() == 0
    assert "anderes" in fenster.datenstatus.text()


@pytest.fixture
def fenster(app):
    haupt = QMainWindow()
    dock = KraefteWerteFenster(haupt)
    haupt.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    dock.snapshots_setzen((_snapshot(),))
    yield dock
    haupt.close()
    haupt.deleteLater()
    app.processEvents()


def test_echtzeitwerte_buendeln_ohne_timer_neustart(fenster, monkeypatch):
    anzeigen = Mock(wraps=fenster._snapshots_anzeigen)
    starten = Mock(wraps=fenster._werte_timer.start)
    monkeypatch.setattr(fenster, "_snapshots_anzeigen", anzeigen)
    monkeypatch.setattr(fenster._werte_timer, "start", starten)
    for sequenz in range(4, 34):
        neu = _snapshot(sequenz=sequenz)
        fenster.snapshots_setzen((neu,), verzoegert=True)
    assert fenster._werte_timer.interval() == 100
    assert fenster._werte_timer.timerType() == Qt.TimerType.PreciseTimer
    assert starten.call_count == 1
    anzeigen.assert_not_called()
    QTest.qWait(150)
    assert anzeigen.call_count == 1
    assert fenster._snapshots == (neu,)
    assert not fenster._werte_timer.isActive()
    assert fenster._ausstehende_snapshots is None


def test_finalwert_und_invalidierung_ueberholen_ausstehende_werte(fenster):
    neu = _snapshot(sequenz=4)
    fenster.snapshots_setzen((neu,), verzoegert=True)
    fenster.ausstehende_werte_anzeigen()
    assert fenster._snapshots == (neu,)
    assert not fenster._werte_timer.isActive()
    fenster.snapshots_setzen((_snapshot(sequenz=5),), verzoegert=True)
    fenster.snapshots_setzen(())
    fenster.kopf.setText("Auswertung fehlgeschlagen")
    fenster.ausstehende_werte_anzeigen()
    assert not fenster._werte_timer.isActive()
    assert fenster._ausstehende_snapshots is None
    assert fenster.modell.rowCount() == 0
    assert fenster.kopf.text() == "Auswertung fehlgeschlagen"
    neu = _snapshot(generation=3)
    fenster.snapshots_setzen((_snapshot(sequenz=6),), verzoegert=True)
    fenster.snapshots_setzen((neu,))
    fenster.ausstehende_werte_anzeigen()
    assert fenster._snapshots == (neu,)


def test_verzoegerte_snapshots_validieren_synchron(fenster):
    with pytest.raises(TypeError, match="Anzeigesnapshots"):
        fenster.snapshots_setzen((object(),), verzoegert=True)
    with pytest.raises(ValueError, match="Pro Koerper"):
        fenster.snapshots_setzen((_snapshot(), _snapshot()), verzoegert=True)
    assert not fenster._werte_timer.isActive()


def test_identische_texte_werden_nicht_erneut_gesetzt(fenster, monkeypatch):
    fenster.legende_setzen({})
    labels = (fenster.kopf, *fenster.karten, fenster.datenstatus, fenster.legende)
    aufrufe = []
    for label in labels:
        spy = Mock(wraps=label.setText)
        monkeypatch.setattr(label, "setText", spy)
        aufrufe.append(spy)
    details = QSignalSpy(fenster.details.textChanged)
    fenster.snapshots_setzen((_snapshot(),))
    fenster.legende_setzen({})
    for aufruf in aufrufe:
        aufruf.assert_not_called()
    assert details.count() == 0


def test_register_definiert_namen_farben_und_defaults():
    definitionen = {d.id: d for d in BEITRAGS_DEFINITIONEN}
    for d in definitionen.values():
        assert d.gruppe in GRUPPEN_TITEL
        assert d.titel and len(d.farbe) == 7 and d.farbe.startswith("#")
    assert {d.id for d in definitionen.values() if d.sichtbar} == {
        "schwerkraft", "hydrostatik", "fremdkraft"}
    assert definitionen["hydrostatik"].gestrichelt
    assert len({definitionen["hydrodynamik_" + r].farbe
                for r in ("rumpf", "kiel", "ruder", "volumenkoerper")}) == 4


def test_hierarchie_und_qt_modellvertrag(app):
    snapshot = _snapshot()
    modell = _modell(app, snapshot)
    assert modell.columnCount() == len(SPALTEN) == 13
    assert modell.rowCount() == 1
    koerper = modell.index(0, 0)
    assert koerper.data() == "boot"
    assert koerper.data(SNAPSHOT_ROLLE) is snapshot
    assert not modell.parent(koerper).isValid()
    assert modell.rowCount(koerper) == len(snapshot.gruppen) + 1
    gruppe = modell.index(0, 0, koerper)
    assert gruppe.data().startswith("Summe: Gewicht und Auftrieb")
    assert modell.rowCount(gruppe) == 2
    for row in range(modell.rowCount(gruppe)):
        quelle = modell.index(row, 0, gruppe)
        assert quelle.parent() == gruppe
        assert quelle.data(SNAPSHOT_ROLLE) is snapshot
        assert quelle.data(BEITRAG_ROLLE) is snapshot.beitraege[row]
        assert modell.index_fuer_id(quelle.data(ID_ROLLE)) == quelle
        assert modell.rowCount(quelle) == 0
    assert gruppe.parent() == koerper
    assert modell.rowCount(modell.index(0, 1)) == 0
    assert not modell.index(-1, 0).isValid()
    assert not modell.index(0, 13).isValid()
    assert modell.data(QModelIndex()) is None
    assert modell.headerData(2, Qt.Orientation.Horizontal) == "F_x (Welt)"
    assert modell.headerData(13, Qt.Orientation.Horizontal) is None


def test_komponenten_betraege_punkt_und_details(app):
    modell = _modell(app)
    id_ = ("boot", "auftrieb")
    assert modell.index_fuer_id(id_, 4).data() == "48 000 N"
    assert modell.index_fuer_id(id_, 6).data() == "16 800 Nm"
    assert modell.index_fuer_id(id_, 9).data() == "16 800 Nm"
    for spalte in range(2, 10):
        assert modell.index_fuer_id(id_, spalte).data(
            Qt.ItemDataRole.TextAlignmentRole) == (
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter).value
    assert "realer Angriff" in modell.index_fuer_id(id_, 10).data()
    assert "(0,00 m; 0,35 m; 0,00 m)" in modell.index_fuer_id(id_, 10).data()
    text = modell.detailtext(id_)
    assert "48 000 N" in text and "16 800 Nm" in text
    assert "M(P) = M(A) + (A - P) x F" in text
    assert "direktes Quellenmoment" in text
    assert "kein zusaetzlicher Bilanzbeitrag" in modell.detailtext(
        ("boot", "summe:gesamt"))
    assert "kein bestaetigter originalangriff" in modell.detailtext(
        ("boot", "rumpf_1")).lower()


def test_sichtbarkeit_ist_nur_darstellung_und_bleibt_stabil(app):
    snapshot = _snapshot()
    modell = _modell(app, snapshot)
    spy = QSignalSpy(modell.sichtbarkeit_geaendert)
    id_ = ("boot", "auftrieb")
    check = modell.index_fuer_id(id_, 1)
    assert check.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked.value
    assert modell.setData(check, Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
    assert spy.count() == 1 and spy.at(0) == [id_, False]
    assert check.data(SNAPSHOT_ROLLE) is snapshot
    assert snapshot.bilanz.wrench.kraft_N == (-300, 0, -1050)
    assert not modell.setData(check, "neue Kraft", Qt.ItemDataRole.EditRole)
    assert not modell.setData(check, 1, Qt.ItemDataRole.CheckStateRole)
    assert not (modell.flags(check) & Qt.ItemFlag.ItemIsEditable)
    assert not modell.setData(modell.index(0, 1), 2, Qt.ItemDataRole.CheckStateRole)
    modell.snapshots_setzen((replace(snapshot, sequenz=4),))
    assert modell.index_fuer_id(id_, 1).data(
        Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Unchecked.value
    assert spy.count() == 1


def test_teilsumme_fehlend_und_null_sind_unterscheidbar(app):
    snapshot = _snapshot(fehlend=True, hydro=(0, 0, 0))
    modell = _modell(app, snapshot)
    assert modell.index_fuer_id(("boot", "auftrieb"), 12).data() == "null"
    assert modell.index_fuer_id(("boot", "auftrieb"), 4).data() == "0 N"
    id_ = ("boot", "added_mass")
    assert modell.index_fuer_id(id_, 12).data() == "nicht berechnet"
    assert modell.index_fuer_id(id_, 4).data() == "nicht berechnet"
    assert "unvollstaendig" in modell.index_fuer_id(("boot", "summe:gesamt")).data()
    assert "nicht bewertbar" in modell.kopftext(snapshot)
    assert "Im Gleichgewicht" not in modell.kopftext(snapshot)


def test_kleinwerte_werden_nur_optisch_zu_null_gerundet(app):
    snapshot = _snapshot(hydro=(1e-18, 0, 0))
    modell = _modell(app, snapshot)
    assert modell.index_fuer_id(("boot", "auftrieb"), 2).data() == "0 N"
    assert modell.index_fuer_id(("boot", "auftrieb"), 12).data() == "aktiv"
    beitrag = modell.index_fuer_id(("boot", "auftrieb"), 2).data(BEITRAG_ROLLE)
    assert beitrag.wrench.kraft_N[0] == 1e-18
    assert "Gleichgewicht nicht bewertet" in modell.kopftext(snapshot)


def test_endliche_komponenten_mit_nicht_darstellbarem_betrag(app):
    modell = _modell(app, _snapshot(hydro=(1.6e308, 1.6e308, 1.6e308)))
    assert modell.index_fuer_id(("boot", "auftrieb"), 5).data() == (
        "Betrag nicht darstellbar")
    assert format(1.6e308, ",.0f").replace(",", " ") + " N" in modell.detailtext(
        ("boot", "auftrieb"))


def test_mehrkoerper_bilden_keine_neue_gesamtsumme(app):
    modell = _modell(app, _snapshot("eins"), _snapshot("zwei"))
    assert modell.rowCount() == 2
    for row, koerper in enumerate(("eins", "zwei")):
        index = modell.index(row, 0)
        assert index.data() == koerper
        assert modell.index_fuer_id((koerper, "summe:gesamt")).parent() == index
        assert modell.index_fuer_id((koerper, "rumpf_1")).data() != (
            modell.index_fuer_id((koerper, "rumpf_2")).data())
    with pytest.raises(ValueError, match="genau ein"):
        modell.snapshots_setzen((_snapshot("eins"), _snapshot("eins")))
    assert modell.rowCount() == 2
    with pytest.raises(TypeError, match="Anzeigesnapshots"):
        modell.snapshots_setzen((object(),))


def test_lifecycle_entfernt_alte_koerper_und_ids(app):
    modell = _modell(app)
    modell.snapshots_setzen((_snapshot("neu"),))
    assert not modell.index_fuer_id(("boot", "gewicht")).isValid()
    assert modell.index(0, 0).data() == "neu"
    assert len(modell._sichtbar) == len(modell._ids)
    modell.snapshots_setzen(())
    assert modell.rowCount() == 0 and not modell._sichtbar
    assert not modell.index(0, 0).isValid()


def test_fensterauswahl_bidirektional_ohne_rueckkopplung(fenster):
    spy = QSignalSpy(fenster.auswahl_geaendert)
    id_ = ("boot", "auftrieb")
    fenster.baum.setCurrentIndex(fenster.modell.index_fuer_id(id_))
    assert spy.count() == 1 and spy.at(0) == [id_]
    assert "Auftrieb F_A" in fenster.details.toPlainText()
    assert "Snapshot #3" in fenster.kopf.text()
    fenster.auswaehlen(("boot", "rumpf_1"))
    assert spy.count() == 1
    assert fenster.baum.currentIndex().data(ID_ROLLE) == ("boot", "rumpf_1")
    fenster.auswaehlen(None)
    assert spy.count() == 1 and "Snapshot #3" in fenster.kopf.text()
    assert fenster.details.isReadOnly()
    with pytest.raises(KeyError, match="Unbekannte Anzeige-ID"):
        fenster.auswaehlen(("fehlt", "auftrieb"))


def test_updates_erhalten_auswahl_aber_nicht_ueber_generation(fenster):
    spy = QSignalSpy(fenster.auswahl_geaendert)
    id_ = ("boot", "auftrieb")
    fenster.auswaehlen(id_)
    gruppe = fenster.baum.currentIndex().parent()
    fenster.baum.setExpanded(gruppe, False)
    fenster.snapshots_setzen((_snapshot(sequenz=4),))
    assert fenster.baum.currentIndex().data(ID_ROLLE) == id_
    assert not fenster.baum.isExpanded(fenster.baum.currentIndex().parent())
    assert "Snapshot #4" in fenster.details.toPlainText()
    assert spy.count() == 0
    fenster.snapshots_setzen((_snapshot(generation=3, sequenz=0),))
    assert fenster.baum.currentIndex().data(ID_ROLLE) is None
    assert spy.count() == 1 and spy.at(0) == [None]
    assert "Generation 3" in fenster.kopf.text()


def test_gleiche_struktur_aktualisiert_werte_ohne_neue_tabellenzeilen(app):
    modell = _modell(app)
    index = modell.index_fuer_id(("boot", "auftrieb"))
    zeile = index.internalPointer()
    reset = QSignalSpy(modell.modelReset)
    neu = _snapshot(sequenz=4, hydro=(0, 0, 47000))
    modell.snapshots_setzen((neu,))
    assert reset.count() == 0
    assert modell.index_fuer_id(("boot", "auftrieb")).internalPointer() is zeile
    assert index.data(SNAPSHOT_ROLLE) is neu
    assert modell.index_fuer_id(("boot", "auftrieb"), 4).data() == "47 000 N"


def test_fensterlayout_spalten_und_erreichbarkeit_ohne_physikpersistenz(app):
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtGui import QGuiApplication
    from segelphysik.core.einstellungen import VORLAGE, wert_pruefen
    eltern = QMainWindow()
    fenster = KraefteWerteFenster(eltern)
    eltern.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, fenster)
    fenster.setFloating(True)
    fenster.baum.setColumnWidth(0, 333)
    fenster.baum.header().moveSection(0, 1)
    fenster.move(100000, 100000)
    gespeichert = wert_pruefen(
        VORLAGE["kraefteanzeige"]["fensterlayout"], fenster.layout_exportieren())
    fenster.baum.setColumnWidth(0, 90)
    fenster.layout_anwenden(gespeichert)
    assert fenster.baum.columnWidth(0) == 333
    assert fenster.baum.header().visualIndex(0) == 1
    assert any(s.availableGeometry().contains(fenster.frameGeometry().center())
               for s in QGuiApplication.screens())
    assert not {"sequenz", "solver", "auswahl", "kraefte"} & gespeichert.keys()
    eltern.close()
    eltern.deleteLater()
    app.processEvents()


def test_neustart_stellt_layout_stil_und_sichtbarkeit_aber_keine_physik_wieder_her(
        app, tmp_path, monkeypatch):
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.gui.hauptfenster import HauptFenster
    pfad = str(tmp_path / "neustart.json")
    original_laden = Einstellungen.laden.__func__
    monkeypatch.setattr(
        Einstellungen, "laden",
        classmethod(lambda cls: original_laden(cls, pfad)))
    erstes = HauptFenster()
    try:
        ein = erstes._einstellungen
        for key in ("koerperframe", "weltursprung", "komponenten", "logarithmisch"):
            ein.setzen("kraefteanzeige", key, True)
        ein.setzen("kraefteanzeige", "kraftreferenz_N", 200)
        ein.setzen("kraefteanzeige", "sichtbarkeiten",
                   {"knoten:boot": {"auftrieb": False}})
        ein.setzen("pfeil_f_a", "kopf", 1.7)
        dock = erstes._kraefte_werte
        dock.snapshots_setzen((_snapshot(),))
        dock.auswaehlen(("boot", "auftrieb"))
        dock.baum.setColumnWidth(0, 347)
        dock.baum.header().moveSection(0, 2)
        dock.move(100000, 100000)
    finally:
        erstes.close()
        app.processEvents()
    zweites = HauptFenster()
    try:
        neu = zweites._einstellungen
        dock = zweites._kraefte_werte
        assert dock.baum.columnWidth(0) == 347
        assert dock.baum.header().visualIndex(0) == 2
        assert any(s.availableGeometry().contains(dock.frameGeometry().center())
                   for s in app.screens())
        assert neu.get("pfeil_f_a", "kopf") == 1.7
        assert neu.get("kraefteanzeige", "kraftreferenz_N") == 200
        assert neu.get("kraefteanzeige", "sichtbarkeiten") == {
            "knoten:boot": {"auftrieb": False}}
        assert all(dock.optionen[key].isChecked()
                   for key in ("koerperframe", "weltursprung", "komponenten"))
        assert not zweites._kraftanzeige_snapshots
        assert not dock._snapshots
        assert dock._aktive_id is None
        assert zweites._echtzeit_kraefteresultat is None
        assert zweites._echtzeit_zustand is None
        assert dock.modell.rowCount() == 0
    finally:
        zweites.close()
        app.processEvents()


def test_koerperauswahl_bleibt_bei_mehrkoerperupdate(fenster):
    fenster.ansicht_setzen(dict(
        mehrkoerper=True, koerperframe=False, weltursprung=False, komponenten=False))
    fenster.snapshots_setzen((_snapshot(), _snapshot("zwei")))
    fenster.baum.setCurrentIndex(fenster.modell.index_fuer_koerper("zwei"))
    fenster.snapshots_setzen((_snapshot(sequenz=4), _snapshot("zwei", sequenz=4)))
    assert fenster.baum.currentIndex().data(SNAPSHOT_ROLLE).koerper_id == "zwei"
    assert fenster.kopf.text().startswith("zwei")


def test_anzeigekoerperwahl_ist_unabhaengig_und_bewahrt_snapshot(fenster):
    eins, zwei = _snapshot(), _snapshot("zwei")
    fenster.snapshots_setzen((eins, zwei))
    assert fenster.modell.rowCount() == 1
    fenster.koerperwahl.setCurrentIndex(1)
    assert fenster.modell.index(0, 0).data(SNAPSHOT_ROLLE) is zwei
    fenster.snapshots_setzen((replace(zwei, sequenz=8), replace(eins, sequenz=8)))
    assert fenster.koerperwahl.currentData() == "zwei"
    assert fenster.modell.rowCount() == 1


def test_frame_und_bezug_wechseln_nur_die_ansicht(app):
    snapshot = replace(_snapshot(), kraftpose=Pose(
        FRAME, "koerper", (2, 3, 0), (2**-.5, 0, 0, 2**-.5)))
    modell = _modell(app, snapshot)
    id_ = ("boot", "rumpf_1")
    modell.ansicht_setzen(koerperframe=True, weltursprung=True)
    assert "Koerper" in modell.headerData(2, Qt.Orientation.Horizontal)
    assert modell.index_fuer_id(id_, 3).data() == "100 N"
    assert "Weltursprung" in modell.kopftext(snapshot)
    assert modell.index_fuer_id(id_).data(SNAPSHOT_ROLLE) is snapshot
    assert modell.anzeigebeitrag(snapshot, snapshot.beitraege[2]).wrench.frame == "koerper"


def test_fenster_schliessen_wieder_oeffnen_und_reset(fenster, app):
    fenster.auswaehlen(("boot", "auftrieb"))
    fenster.oeffnen()
    app.processEvents()
    assert fenster.isVisible()
    fenster.close()
    app.processEvents()
    assert not fenster.isVisible()
    fenster.oeffnen()
    app.processEvents()
    assert fenster.isVisible()
    assert fenster.baum.currentIndex().data(ID_ROLLE) == ("boot", "auftrieb")
    fenster.snapshots_setzen(())
    assert fenster.kopf.text() == "Kein Anzeigesnapshot"
    assert all(not karte.text() for karte in fenster.karten)
    assert fenster.modell.rowCount() == 0


def test_checkbox_durch_echte_qt_tastatur(fenster, app):
    spy = QSignalSpy(fenster.sichtbarkeit_geaendert)
    fenster.oeffnen()
    fenster.baum.setCurrentIndex(
        fenster.modell.index_fuer_id(("boot", "auftrieb"), 1))
    app.processEvents()
    QTest.keyClick(fenster.baum, Qt.Key.Key_Space)
    app.processEvents()
    assert spy.count() == 1 and spy.at(0) == [("boot", "auftrieb"), False]


def test_karten_kennzeichnen_unvollstaendige_bilanz(fenster):
    fenster.snapshots_setzen((_snapshot(fehlend=True),))
    assert "Teilsumme" in fenster.karten[0].text()
    assert "nicht bewertbar" in fenster.karten[2].text()
    assert "teilsumme" in fenster.karten[2].text()
