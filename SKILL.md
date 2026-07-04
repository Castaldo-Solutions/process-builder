---
name: process-builder
description: >
  Crea swimlane diagram professionali e leggibili come file draw.io (.drawio),
  usando notazione ibrida BPMN con palette curata. Gestisce due modalita: AS-IS (documenta
  il processo attuale con pain point, attori, strumenti) e TO-BE (propone automazioni con
  roadmap a 2 versioni: Quick Win e Full Automation). Usa questa skill ogni volta che
  l'utente vuole: mappare un processo aziendale, fare un'analisi AS-IS di un flusso di lavoro,
  proporre automazioni o miglioramenti a un processo esistente, creare una roadmap di
  trasformazione digitale, disegnare un diagramma di processo con swimlane, analizzare chi
  fa cosa e con quale strumento in un processo. Se l'utente menziona "swimlane", "processo",
  "flusso", "AS-IS", "TO-BE", "pain point", "automazione", "flowchart", "diagramma di flusso"
  o descrive un processo aziendale con piu attori, attiva questa skill immediatamente.
---

# Process Builder Skill

Questa skill guida la creazione di swimlane diagram professionali in notazione **ibrida BPMN con palette curata**, esportati come file `.drawio` pronti per diagrams.net.

**Leggi questi file prima di fare qualsiasi cosa:**
- `references/interview-guide.md` — come condurre l'intervista (AS-IS e TO-BE) e come decidere se servono fasi
- `references/style-guide.md` — forme, colori, simboli BPMN adottati
- `references/drawio-xml-guide.md` — schema del JSON di input per lo script

Esempi completi di JSON pronti da studiare: cartella `examples/` (fase unica, tre fasi con link event, TO-BE con info panel).

---

## REGOLA ZERO: mai generare senza informazioni complete

Prima di produrre qualsiasi JSON o diagramma, verifica di avere TUTTE e quattro queste informazioni. Se ne manca anche solo una, NON generare: fai domande (una per turno, come da `interview-guide.md`).

1. **Chi fa cosa** — la lista completa degli attori (ruoli, non nomi) e, per ciascuno, le azioni concrete che compie. Se non sai in quale lane mettere un'azione, l'informazione non e completa.
2. **Quando** — cosa fa scattare il processo (trigger), in che ordine avvengono le azioni, chi passa la palla a chi, e dove finisce il processo.
3. **Con quale strumento** — per ogni azione, lo strumento usato (email, Excel, gestionale, WhatsApp, telefono, carta...). Gli handoff tra strumenti sono la sede tipica dei pain point: non tirare a indovinare.
4. **Le decisioni** — esistono punti in cui qualcuno decide o approva? Da cosa dipende la decisione? Cosa succede in caso di si e in caso di no? Ogni "se... allora..." raccontato dall'utente e un gateway da chiarire.

Se l'utente fornisce una descrizione gia completa su tutti e quattro i punti, procedi senza domande inutili. Se la descrizione e parziale, chiedi SOLO cio che manca: non ripartire da zero con l'intervista completa. Non inventare mai attori, strumenti o decisioni non menzionati: un diagramma plausibile ma inventato e peggio di una domanda in piu.

---

## REGOLA ASSOLUTA: usa sempre lo script Python

Non scrivere mai XML draw.io a mano. Il formato e delicato e un errore di escape rende il file inutilizzabile. L'unico modo corretto e:

**Passo A — crea il JSON** che descrive il processo (schema in `references/drawio-xml-guide.md`), salvalo come `[nome_processo].json`.

**Passo B — esegui lo script:**
```bash
python <path-skill>/scripts/generate_swimlane.py [nome_processo].json [output].drawio
```

Lo script si occupa del layout, dei caratteri speciali, della legenda opzionale e delle forme BPMN. Se segnala un errore, correggi il JSON, non l'XML.

---

## Due modalita: AS-IS e TO-BE

### Modalita AS-IS
Fotografia del processo cosi com'e: chi fa cosa, quando, con quale strumento, dove sono i pain point. Neutra, descrittiva.

### Modalita TO-BE
Propone il processo ottimizzato in 2 varianti:
- **Quick Win** — automazioni leggere, realizzabili in 2-4 settimane con strumenti gia disponibili
- **Full Automation** — scenario target con integrazioni profonde o investimenti significativi

---

## Workflow AS-IS

### 1. Intervista
Conduci l'intervista seguendo `references/interview-guide.md` (sezione AS-IS). Segui i principi guida: una domanda per turno, parafrasa sempre, non proporre soluzioni ancora.

**Sezione F — Fasi: attenzione particolare.** Non creare fasi separate solo perche il processo e lungo. Usa una fase separata solo se tra un blocco e l'altro cambiano almeno due tra: attori dominanti, strumenti principali, scopo operativo. In caso contrario, il diagramma resta a fase unica. Vedi gli esempi nella guida per allenare il giudizio.

### 2. Conferma
Prima di generare il JSON, riassumi il processo nel formato strutturato indicato in `interview-guide.md` (sezione "Conferma prima di disegnare") e chiedi conferma esplicita.

Non saltare questo passo: un giro di correzione qui vale dieci iterazioni sul file .drawio.

### 3. Costruisci il JSON di input
Traduci il processo in JSON. Schema completo e tipi di elemento in `references/drawio-xml-guide.md`.

Decisione chiave sulla legenda: se il diagramma e per un cliente che conosce BPMN o per uso interno, lascia `"legend": false`. Attivala solo se il destinatario e uno stakeholder non tecnico che ha bisogno di riferimenti visivi.

Ricordati dei tipi BPMN:
- Decisione -> `gateway_xor` (rombo con X) — il default per si/no
- Parallelismo -> `gateway_and` (rombo con +)
- Pain point -> tipo dedicato, metti `target` con l'id del task problematico per il collegamento tratteggiato
- Cross-lane lungo -> coppia `link_out` / `link_in` con stessa `link_label` invece di una freccia lunga

### 4. Esegui lo script e consegna
```bash
python <path>/scripts/generate_swimlane.py nome_processo.json nome_processo.drawio
```

Presenta il link al file e aggiungi un commento sintetico: fasi, attori, pain point, strumenti principali.

---

## Workflow TO-BE

### 1. Acquisisci l'AS-IS
Il TO-BE parte sempre da un AS-IS. Accetta:
- File `.drawio` (leggi l'XML)
- Immagine del diagramma AS-IS (analizzala visivamente)
- Descrizione raccolta nell'intervista AS-IS appena conclusa

Se non c'e AS-IS, proponi di farlo prima. Un TO-BE senza AS-IS perde la funzione di confronto.

### 2. Prioritizza i pain point
Costruisci una lista ordinata per impatto (tempo, errori, ritardi, costi) con stima di difficolta di risoluzione. Chiedi conferma all'utente prima di proporre soluzioni.

### 3. Intervista TO-BE
Segui `references/interview-guide.md` (sezione TO-BE) per capire visione, vincoli (budget, tempo, resistenza, compliance) e preferenze di roadmap PRIMA di proporre soluzioni.

### 4. Mappatura pain point -> soluzioni
Per ogni pain point proponi due soluzioni:
- **Quick Win**: bassa complessita, impatto visibile in 2-4 settimane
- **Full Automation**: integrazione profonda, impatto massimo

Presenta la tabella di mappatura (vedi `interview-guide.md`) e concordate insieme quali soluzioni vanno in ciascuna versione.

### 5. Genera i due file .drawio
Nomi file:
- `[cliente]_[processo]_to-be_quick-win.drawio`
- `[cliente]_[processo]_to-be_full-automation.drawio`

Nel JSON, usa i tipi dedicati per distinguere:
- `action_auto` (verde) — task automatizzato che prima era manuale
- `action_new` (azzurro) — task introdotto ex novo dal TO-BE
- `action_deleted` (tratteggiato grigio, da usare con parsimonia) — se vuoi far vedere cosa hai rimosso
- `info_panel` (pannello azzurro) — varianze di dipartimento o di scenario in un TO-BE **generalizzato**

I pain point risolti NON vanno riportati nel TO-BE: sono stati risolti.

**TO-BE generalizzato.** Quando uno stesso processo di riferimento e comune a piu dipartimenti, non moltiplicare gli swimlane: disegna un TO-BE di riferimento e metti le differenze nei pannelli `info_panel` (banda azzurra sotto la fase). Un pannello deve giustificare *perche* la varianza e intrinseca alla natura dell'attivita; se e solo accidente storico, va sanata uniformando, non documentata.

### 6. Sintesi roadmap
Dopo aver generato i due file, presenta:

```
QUICK WIN (stima: X settimane)
- Pain point risolti: [lista]
- Automazioni: [lista]
- Strumenti/tecnologie: [lista]

FULL AUTOMATION (stima: X mesi)
- Pain point risolti: [lista + quelli della Quick Win]
- Automazioni aggiuntive: [lista]
- Strumenti/tecnologie: [lista]
```

---

## Regole di qualita del diagramma

1. **Una lane per attore**, mai due attori nella stessa lane.
2. **Fasi rare e giustificate**: solo se cambiano 2+ tra attori/strumenti/scopo. Vedi `interview-guide.md` sezione F.
3. **Gateway, non rettangoli**, per le decisioni. Scegli il tipo corretto (xor per si/no, and per parallelismo).
4. **Pain point fuori lane**: lo script li posiziona sotto il phase container. Usa `target` per legarli al task problematico con linea tratteggiata.
5. **Link event per cross-lane lungo**: se il flusso deve tornare indietro o attraversare piu di una lane, usa una coppia `link_out`/`link_in` con stessa `link_label` invece di una freccia-serpente.
6. **Strumenti annotati** con `tool`: appaiono come label colorata sotto il task.
7. **Legenda opzionale**: di default `legend: false`. Attivala solo se serve al destinatario.
8. **Nomi attori coerenti** tra AS-IS e TO-BE: devono combaciare esattamente per facilitare il confronto.

---

## Nomenclatura file

- `[cliente]_[processo]_as-is.drawio`
- `[cliente]_[processo]_to-be_quick-win.drawio`
- `[cliente]_[processo]_to-be_full-automation.drawio`

Se il nome cliente non e noto: `[processo]_as-is.drawio`, ecc.

---

## Cosa fare se lo script si lamenta

Lo script valida il JSON prima di generare e scrive su stderr messaggi che dicono dove sta il problema e come correggerlo. Due livelli:

- **ERRORE** (bloccante, exit code 1, nessun file generato): JSON malformato, `phases`/`actors`/`elements` mancanti, id duplicati, connessioni con `from`/`to` inesistenti o che puntano a pain point / info panel.
- **AVVISO** (il file viene generato comunque): attore non presente in `actors` (fallback prima lane), tipo sconosciuto (disegnato come task), pain point senza `target`, link event spaiati o senza `link_label`, colore non `#RRGGBB`.

Comandi utili:
```bash
python <path>/scripts/generate_swimlane.py input.json --validate   # solo controllo, nessun file
python <path>/scripts/generate_swimlane.py input.json out.drawio --strict  # anche gli avvisi bloccano
```

Se lo script segnala errori, correggi il JSON e rilancia. Non correggere MAI l'XML a mano.

Se il diagramma si apre ma e visivamente sbagliato, 9 volte su 10 il problema e nel JSON (attori giusti? ordine elementi giusto? connessioni corrette?), non nello script.
