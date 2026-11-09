# 01: Turnier anlegen und lokale Web-App starten

**Spec:** [../spec.md](../spec.md)

**What to build:** `knobeln` startet eine lokale Web-App auf `127.0.0.1`, in der die Turnierleitung ein Turnier anlegen, umbenennen und löschen kann. Das zuletzt geöffnete Turnier wird gemerkt; die Daten liegen in SQLite. Vor dem Löschen wird eine SQLite-Kopie angelegt. Die App startet auch ohne API-Key und zeigt die leere Scannen-Ansicht.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] `knobeln` startet die Web-App nur auf `127.0.0.1`; `knobeln web` ist ein Alias.
- [x] Ein Turnier kann mit Namen angelegt, umbenannt und nach Bestätigung gelöscht werden.
- [x] Das zuletzt geöffnete Turnier wird nach einem Neustart wieder geöffnet.
- [x] Vor dem Löschen eines Turniers entsteht eine SQLite-Kopie.
- [x] Die App startet ohne API-Key und zeigt eine leere Scannen-Ansicht mit dem nächsten Schritt.
- [x] Tests am Anwendungskern und an der HTTP-Fläche decken Anlegen, Auswählen, Umbenennen, Löschen und Neustart-Persistenz ab.

## Comments

Umgesetzt in `c14e9de`; Code-Review-Fixes in `eb85b36`. Die SQLite-Sicherung nutzt jetzt die SQLite-Backup-API und ist im Test wiederherstellbar. `./scripts/check.sh` ist grün (69 passed, 1 manual skipped).
