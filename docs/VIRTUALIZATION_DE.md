# Rubot Virtualisierungs-Leitfaden

## Rubot in virtuellen Maschinen ausführen

Beim Betrieb von Rubot in virtualisierten Umgebungen gibt es wichtige Überlegungen bezüglich CPU-Architektur und PyTorch-Kompatibilität.

### CPU-Architektur-Kompatibilität

**⚠️ Wichtig:** Vermeiden Sie beim Betrieb von Rubot in einer virtuellen Maschine die Verwendung der `qemu64` CPU-Architektur, da diese PyTorch zum Absturz bringen kann.

**Empfohlene Lösung:** Verwenden Sie die Host-CPU-Architektur für Ihre Rubot-VM anstelle der generischen `qemu64`-Architektur.

### Warum das wichtig ist

Rubot verwendet Docling für die PDF-Verarbeitung, welches wiederum auf PyTorch für verschiedene Machine-Learning-Operationen angewiesen ist, einschließlich:
- OCR (Optische Zeichenerkennung) mit EasyOCR
- Dokumentstruktur-Analyse
- Bildverarbeitung

Die `qemu64` CPU-Architektur ist ein generisches CPU-Modell mit dem kleinsten gemeinsamen Nenner, dem viele moderne CPU-Features fehlen, die PyTorch erwartet und für die es optimiert. Dies kann zu folgenden Problemen führen:
- Laufzeitfehler während PyTorch-Operationen
- Abstürze während der Dokumentverarbeitung
- Schlechte Leistung oder Hängenbleiben während OCR-Operationen

### Konfigurationsbeispiele

#### QEMU/KVM
Anstelle von:
```bash
-cpu qemu64
```

Verwenden Sie:
```bash
-cpu host
```

Oder geben Sie Ihr tatsächliches CPU-Modell an:
```bash
-cpu Skylake-Client
```

#### VirtualBox
- Gehen Sie zu VM-Einstellungen → System → Prozessor
- Aktivieren Sie "PAE/NX aktivieren"
- Erwägen Sie die Aktivierung von "VT-x/AMD-V aktivieren", falls verfügbar

#### VMware
- Verwenden Sie die Option "Intel VT-x/EPT oder AMD-V/RVI virtualisieren"
- Vermeiden Sie Kompatibilitätsmodus-Einstellungen, die CPU-Features einschränken könnten

### Alternative: Nur-CPU-Modus

Falls Sie `qemu64` verwenden müssen oder PyTorch-Probleme auftreten, können Sie Rubot zwingen, den Nur-CPU-Modus zu verwenden:

```bash
export DOCLING_USE_CPU_ONLY=true
```

Oder in Ihrer `.env`-Datei:
```
DOCLING_USE_CPU_ONLY=true
```

Dies deaktiviert die GPU-Beschleunigung und verwendet konservativere CPU-Operationen, die mit eingeschränkten CPU-Architekturen kompatibel sind.

### Leistungsüberlegungen

- **Host-CPU-Architektur**: Beste Leistung, vollständige Feature-Unterstützung
- **Spezifisches CPU-Modell**: Gute Leistung, die meisten Features unterstützt
- **Nur-CPU-Modus**: Langsamer, aber kompatibler
- **qemu64**: Nicht empfohlen, kann zu Fehlern führen

### Fehlerbehebung

Falls Sie PyTorch-bezogene Fehler in einer VM antreffen:

1. Überprüfen Sie die CPU-Konfiguration Ihrer VM
2. Versuchen Sie `DOCLING_USE_CPU_ONLY=true` zu aktivieren
3. Reduzieren Sie die Verarbeitungslast mit `MAX_PDF_PAGES=10`
4. Deaktivieren Sie OCR mit `DOCLING_DO_OCR=false`, falls nötig

### Verwandte Konfiguration

Siehe die Hauptkonfigurationsdokumentation für andere Docling/PyTorch-bezogene Einstellungen:
- `DOCLING_USE_CPU_ONLY`: Nur-CPU-Verarbeitung erzwingen
- `DOCLING_OCR_ENGINE`: OCR-Engine wählen (easyocr, tesseract, rapidocr)
- `DOCLING_DO_OCR`: OCR-Verarbeitung aktivieren/deaktivieren
- `DOCLING_BATCH_SIZE`: Speicherverbrauch während der Verarbeitung kontrollieren