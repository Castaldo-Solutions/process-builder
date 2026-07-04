# Guida al JSON di Input — Process Builder

Questo documento descrive lo schema JSON che lo script `scripts/generate_swimlane.py` accetta in input. Lo script produce un file `.drawio` pronto per essere aperto in diagrams.net.

Non scrivere mai XML draw.io a mano: produci solo il JSON, poi lancia lo script.

---

## Schema di alto livello

```json
{
  "title": "nome_processo",
  "legend": false,
  "phases": [ ... ]
}
```

| Campo | Tipo | Obbligatorio | Default | Descrizione |
|-------|------|--------------|---------|-------------|
| `title` | string | no | "processo" | Usato per il nome file di default |
| `legend` | boolean | no | `false` | Se `true`, aggiunge la legenda sotto il diagramma |
| `phases` | array | si | — | Lista delle fasi (puo essere anche una sola) |

Nota sulla legenda: di default e **disattivata**. Attivala solo se il diagramma e destinato a qualcuno che non conosce la notazione BPMN.

---

## Struttura di una fase

```json
{
  "name": "FASE 1 - NOME FASE",
  "actors": ["Attore A", "Attore B", "Attore C"],
  "elements": [ ... ],
  "connections": [ ... ]
}
```

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `name` | string | si | Nome della fase, in MAIUSCOLO |
| `actors` | array di string | si | Lista dei ruoli; ognuno diventa una lane |
| `elements` | array di oggetti | si | Nodi del processo (task, gateway, start/end, pain point, link event) |
| `connections` | array di oggetti | si | Frecce (sequence flow) tra elementi |

Se il processo e a fase unica, crea un solo elemento in `phases` con un `name` rappresentativo (es. `"PROCESSO - ONBOARDING CLIENTE"`). NON separare in fasi artificiali (vedi `interview-guide.md`, sezione F).

---

## Tipi di elemento

| `type` | Forma BPMN | Descrizione |
|--------|------------|-------------|
| `start` | Cerchio bordo sottile verde | Evento di avvio del processo |
| `end` | Cerchio bordo spesso rosso | Evento di fine del processo |
| `action` | Rettangolo arrotondato bianco | Task manuale (AS-IS standard) |
| `action_auto` | Rettangolo arrotondato verde chiaro | Task automatizzato (TO-BE) |
| `action_new` | Rettangolo arrotondato azzurro | Task nuovo introdotto nel TO-BE |
| `action_deleted` | Rettangolo tratteggiato grigio | Task eliminato nel TO-BE (raro, usare con parsimonia) |
| `gateway_xor` | Rombo giallo con **X** | Gateway esclusivo (si/no, A/B) |
| `gateway_and` | Rombo giallo con **+** | Gateway parallelo (tutte le strade si attivano) |
| `gateway_or` | Rombo giallo con **O** | Gateway inclusivo (una o piu strade in base a condizioni) |
| `link_out` | Cerchio bianco bordato nero con freccia ► | Link event uscente (cross-lane lungo) |
| `link_in` | Cerchio bianco bordato nero con freccia ◄ | Link event entrante (cross-lane lungo) |
| `pain_point` | Rettangolo rosa bordo rosso | Pain point posizionato FUORI dalla lane |
| `info_panel` | Rettangolo azzurro bordo blu | Pannello informativo: varianze di dipartimento o di scenario in un TO-BE generalizzato. Fuori lane, non connesso al flusso |

Alias retrocompatibili (ancora accettati):
- `decision` -> gestito come `gateway_xor`
- `gateway` (senza suffisso) -> gestito come `gateway_xor`
- `connector` (vecchio "pallino nero") -> gestito come `link_out` neutro

---

## Campi degli elementi

### Campi comuni
- `id` (string, obbligatorio): identificatore univoco in tutto il file
- `type` (string, obbligatorio): uno dei tipi sopra
- `actor` (string): nome dell'attore/lane di appartenenza; deve corrispondere esattamente a un valore in `actors`. Non serve per `pain_point` se usi `target`.
- `label` (string): testo mostrato dentro o accanto all'elemento

### Campi specifici

**Task (`action` / `action_auto` / `action_new` / `action_deleted`)**
- `tool` (string, opzionale): nome dello strumento usato. Viene reso come label colorata sotto il task. Riconosciuti: WhatsApp, CMS, Email, Excel, Office, ERP, Gestionale, App, Telefono, Carta. Tutti gli altri vengono mostrati in grigio.

**Gateway (`gateway_xor` / `gateway_and` / `gateway_or`)**
- Il `label` e la domanda da mostrare (es. "Approvato?" per XOR). Termina sempre con "?".
- Il simbolo interno (X, +, O) viene aggiunto automaticamente.

**Link event (`link_out` / `link_in`)**
- `link_label` (string, consigliato): lettera o numero identificativo della coppia (es. "A"). Se la coppia outgoing/incoming ha la stessa label, il lettore capisce dove riprendere.
- Non ha `tool`.

**Pain point (`pain_point`)**
- `actor` (string, opzionale): attore a cui il pain point e associato. Usato per ordinare i pain point se non c'e `target`.
- `target` (string, opzionale ma consigliato): id dell'elemento del flusso a cui il pain point si riferisce. Se presente, lo script disegna una linea tratteggiata rossa dal pain point al task. Senza `target`, il pain point resta fluttuante.
- `label` (string, obbligatorio): descrizione breve del problema. Se non contiene gia "PAIN POINT", viene prefissato automaticamente con `"(!) PAIN POINT N: "`.

**Pannello informativo (`info_panel`)**
- `label` (string, obbligatorio): testo della varianza. Conviene una prima riga-titolo, poi `\n` e il dettaglio.
- Non ha `actor` ne `target`: vive in una banda azzurra dedicata sotto la fase, affiancato agli altri pannelli della stessa fase.
- Uso: nei TO-BE **generalizzati**, quando un processo di riferimento e comune a piu dipartimenti, le differenze vanno nei pannelli invece di moltiplicare gli swimlane. Regola: un pannello deve giustificare *perche* la varianza e intrinseca all'attivita; se e solo accidente storico, va sanata uniformando.

---

## Campo `connections`

Ogni connessione e un oggetto:

```json
{"from": "a1", "to": "a2", "label": "Si", "color": "#00B050", "return": false}
```

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `from` | string | si | Id dell'elemento origine |
| `to` | string | si | Id dell'elemento destinazione |
| `label` | string | no | Testo sulla freccia (es. "Si", "No") |
| `color` | string | no | Colore esadecimale della freccia |
| `return` | boolean | no | Se `true`, forza routing verso l'alto (utile per "No" che torna indietro) |

Convenzioni:
- Freccia "Si": `"color": "#00B050"` (verde)
- Freccia "No": `"color": "#FF0000"` (rosso)
- Freccia neutra: `"color": "#000000"` (nero) o omettere

---

## Esempio completo: richiesta ferie (fase unica)

```json
{
  "title": "richiesta_ferie",
  "legend": false,
  "phases": [
    {
      "name": "PROCESSO - RICHIESTA FERIE",
      "actors": ["Dipendente", "Responsabile", "HR"],
      "elements": [
        {"id": "s1", "type": "start", "actor": "Dipendente", "label": ""},
        {"id": "a1", "type": "action", "actor": "Dipendente", "label": "Compilare modulo", "tool": "Excel"},
        {"id": "a2", "type": "action", "actor": "Responsabile", "label": "Valutare richiesta", "tool": "Email"},
        {"id": "g1", "type": "gateway_xor", "actor": "Responsabile", "label": "Approvata?"},
        {"id": "a3", "type": "action", "actor": "HR", "label": "Registrare nel gestionale", "tool": "Gestionale"},
        {"id": "e1", "type": "end", "actor": "HR", "label": "Approvata"},
        {"id": "e2", "type": "end", "actor": "Responsabile", "label": "Rifiutata"},
        {"id": "pp1", "type": "pain_point", "actor": "Responsabile", "target": "a2",
         "label": "Email si perdono tra 100 messaggi al giorno"}
      ],
      "connections": [
        {"from": "s1", "to": "a1"},
        {"from": "a1", "to": "a2"},
        {"from": "a2", "to": "g1"},
        {"from": "g1", "to": "a3", "label": "Si", "color": "#00B050"},
        {"from": "a3", "to": "e1"},
        {"from": "g1", "to": "e2", "label": "No", "color": "#FF0000", "return": true}
      ]
    }
  ]
}
```

---

## Esempio con link event (flusso cross-lane lungo)

Se il "No" di un gateway deve tornare molto indietro (es. a un task 4 colonne prima in un'altra lane), invece di una freccia-serpente usa una coppia di link event:

```json
{
  "id": "lo1", "type": "link_out", "actor": "Responsabile", "link_label": "A"
},
{
  "id": "li1", "type": "link_in", "actor": "Dipendente", "link_label": "A"
}
```

E le connessioni:

```json
{"from": "g1", "to": "lo1", "label": "No", "color": "#FF0000"},
{"from": "li1", "to": "a1"}
```

Il lettore capisce che "A" outgoing si ricollega ad "A" incoming senza tracciare una freccia lunga.

---

## Regole di validita

Lo script valida il JSON prima di generare. Gli **errori** bloccano la generazione (exit code 1) con un messaggio che spiega come correggere; gli **avvisi** lasciano generare il file ma vanno controllati.

1. Gli id devono essere univoci in tutto il file (anche tra fasi diverse). Duplicato = ERRORE.
2. Ogni `actor` di un elemento flow deve esistere in `actors` della sua fase. Altrimenti AVVISO e fallback alla prima lane.
3. Ogni `from` e `to` di una connessione devono puntare a id esistenti e a elementi del flusso. Id inesistente o riferito a pain point / info panel = ERRORE.
4. I pain point vengono disegnati fuori dalla lane, sotto il phase container. Non occupano una colonna del flusso. La numerazione "(!) PAIN POINT N" e automatica e globale: non mettere il numero nella label.
5. Le frecce tra elementi dello stesso attore sono figlie della lane; cross-lane sono figlie del phase; cross-phase sono figlie di root.
6. Gli elementi flow sono disposti in ordine in colonne automatiche. Ogni elemento occupa una colonna. Se vuoi elementi "paralleli" (es. due end distinti per "Si" e "No"), accetta che vengano piazzati in colonne diverse.
7. Le coppie `link_out`/`link_in` devono avere `link_label` combacianti: una label spaiata genera un AVVISO.

Per controllare il JSON senza generare il file:
```bash
python scripts/generate_swimlane.py input.json --validate
```

---

## Comandi tipici

Generare AS-IS:
```bash
python scripts/generate_swimlane.py processo_as_is.json processo_as_is.drawio
```

Generare TO-BE Quick Win:
```bash
python scripts/generate_swimlane.py processo_to_be_qw.json processo_to_be_quick-win.drawio
```

Generare TO-BE Full Automation:
```bash
python scripts/generate_swimlane.py processo_to_be_fa.json processo_to_be_full-automation.drawio
```
