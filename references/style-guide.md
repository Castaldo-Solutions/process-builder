# Process Builder — Guida allo Stile Visivo Swimlane

Questo documento definisce la palette, le forme e le convenzioni visive del Process Builder.

Lo stile adottato è **ibrido BPMN + palette Process Builder**: manteniamo una palette coerente e riconoscibile, ma usiamo le forme e i simboli di BPMN 2.0 per garantire riconoscibilità universale presso chi conosce la notazione standard.

---

## Palette colori

### Contenitore di Fase (Phase Container)
- Sfondo header: `#0057B7` (blu primario)
- Testo header: `#FFFFFF` (bianco)
- Bordo: `#0057B7`
- Font: grassetto, 11pt

### Lane per attore (assegnazione colori in ordine)
Assegna i colori alle lane nell'ordine seguente, riciclando se ci sono più di 5 attori:

| Ordine | Sfondo lane | Bordo |
|--------|-------------|-------|
| 1° attore | `#FFF2CC` (giallo crema) | `#d6b656` |
| 2° attore | `#FCE4D6` (rosa salmone) | `#d6b656` |
| 3° attore | `#FFFFFF` (bianco) | `#B7B7B7` |
| 4° attore | `#E2EFDA` (verde chiaro) | `#70AD47` |
| 5° attore | `#DEEAF1` (azzurro chiaro) | `#4472C4` |

Il testo del nome attore nella lane: `#000000`, grassetto, 10pt.

---

## Forme (notazione ibrida BPMN)

### START (Start Event)
Notazione BPMN: cerchio con bordo **sottile** verde.
- Forma: ellissi perfetta (aspect=fixed)
- Sfondo: `#92D050` (verde)
- Bordo: `#66A30E`, spessore 1
- Etichetta: opzionale, breve (es. "Richiesta ricevuta"), posizionata SOTTO il cerchio (mai dentro: non c'e spazio)
- Dimensione: 40x40 px

### END (End Event)
Notazione BPMN: cerchio con bordo **spesso** rosso.
- Forma: ellissi perfetta
- Sfondo: `#FF9999` (salmone)
- Bordo: `#CC0000`, spessore 3
- Etichetta: opzionale, breve (es. "Pratica chiusa"), posizionata SOTTO il cerchio
- Dimensione: 40x40 px

### Task (Action)
Notazione BPMN: rettangolo arrotondato.
- Sfondo: `#FFFFFF`
- Bordo: `#000000`, spessore 1
- arcSize: 10 (arrotondamento leggero)
- Testo: nero, centrato, 10pt
- Dimensione: 140x50 px
- Label verbo all'infinito o imperativo ("Verifica dati", "Invia conferma")

### Gateway (Decision)
Notazione BPMN: rombo. Esistono tre tipi, distinti dal simbolo interno.

#### Gateway esclusivo (XOR) — il piu comune
Una sola strada si attiva a valle (si/no, A/B/C).
- Forma: rombo
- Sfondo: `#FFE699` (giallo paglierino)
- Bordo: `#d6b656`, spessore 1
- La domanda (es. "Approvato?") sta DENTRO il rombo e il marker X si omette: e il gateway esclusivo "blank", forma ammessa e piu diffusa di BPMN 2.0. Cosi nessuna label esterna puo essere attraversata dalle frecce. Se il gateway non ha domanda, lo script disegna la **X** centrata.
- Le uscite etichettate partono da lati diversi del rombo (assegnati automaticamente dallo script in base alla geometria della destinazione) per non sovrapporre le frecce; le label stanno vicino al rombo
- Dimensione: 90x90 px

#### Gateway parallelo (AND)
Tutte le strade a valle partono insieme.
- Forma: rombo stesso stile
- Simbolo interno: **+**
- Testo sopra: descrizione del parallelismo (es. "Avvia contemporaneamente")
- Usa quando piu attivita partono in parallelo dopo un punto di snodo.

#### Gateway inclusivo (OR)
Una o piu strade a valle si attivano in base alle condizioni.
- Forma: rombo stesso stile
- Simbolo interno: **O** (cerchio)
- Usa piu raramente, solo se il processo lo richiede veramente.

Il tipo default, se non specificato, e XOR.

### Link Event (connettore cross-lane) in stile BPMN
Quando il flusso passa a una lane diversa, specialmente se il percorso e lungo o il diagramma si affolla, al posto di una freccia lunga si usa una coppia di "link event": un outgoing (cerchio con freccia verso destra dentro) e un incoming (cerchio con freccia verso sinistra), etichettati con la stessa label.

- Forma: cerchio (ellissi, aspect=fixed)
- Bordo: `#000000`, spessore 2
- Sfondo: `#FFFFFF`
- Simbolo interno: freccia (triangolo verso destra per outgoing, verso sinistra per incoming)
- Label sopra: stessa lettera/numero per la coppia (es. "A", "B", "1")
- Dimensione: 25x25 px

I link event sostituiscono il vecchio "cerchio nero pieno" usato come generico connettore cross-lane. Sono piu leggibili e riducono il numero di frecce che attraversano il diagramma.

Quando usarli:
- Il flusso cross-lane e lungo (attraversa 2 o piu lane di distanza).
- Il punto di ripresa e lontano dal punto di uscita (es. "No" di un gateway che torna indietro a 4 step prima).
- Ci sono gia troppe frecce che si incrociano nell'area interessata.

Quando NON usarli:
- Transizione cross-lane a distanza di una sola lane: basta una freccia diretta, piu leggibile.

### Pain Point
- Forma: rettangolo arrotondato con bordo spesso rosso
- Sfondo: `#FFD7D7` (rosa chiaro)
- Bordo: `#C00000`, spessore 2
- Testo: `#C00000`, grassetto, 9pt
- Formato testo: `(!) PAIN POINT N: [descrizione breve]`
- Dimensione: 160x55 px
- Posizionamento: **fuori dalla lane dell'attore che lo subisce**, sopra o sotto, collegato con una linea tratteggiata grigia (non una freccia) al passo problematico. Questo evita sovrapposizioni con gli elementi del flusso.

---

## Frecce (Sequence Flow BPMN)

### Freccia normale (stessa fase, fra due task)
- Colore: `#000000`
- Spessore: 1
- Stile: solida, punta triangolare piena
- Routing: ortogonale

### Freccia "Si" (uscita positiva da gateway)
- Colore: `#00B050` (verde)
- Label: "Si", in verde
- Posizionamento preferito: verso destra o verso il basso (flusso principale)

### Freccia "No" (uscita negativa da gateway)
- Colore: `#FF0000` (rosso)
- Label: "No", in rosso
- Posizionamento preferito: verso l'alto o verso sinistra (ritorno o eccezione)

### Freccia cross-lane diretta
- Colore: `#000000`
- Quando possibile, passa per un link event (vedi sopra).

### Linea di collegamento pain point -> task
- Colore: `#C00000`
- Stile: **tratteggiata** (non freccia)
- Spessore: 1

---

## Annotazioni strumento (tool annotation)

Posizionata come label separata **sotto** il rettangolo del task.

Formato: `[tool] WhatsApp`, `[tool] CMS`, ecc. (oppure quadratino colorato davanti al nome).
Font: 9pt, italic, colore associato allo strumento.

### Colori strumenti standard

| Strumento | Colore |
|-----------|--------|
| WhatsApp | `#7030A0` (viola) |
| CMS (generico) | `#4472C4` (blu) |
| Email | `#FF7C00` (arancione) |
| Excel / Office | `#217346` (verde Microsoft) |
| ERP / Gestionale | `#C55A11` (marrone) |
| App custom | `#2E74B5` (blu scuro) |
| Telefono | `#888888` (grigio) |
| Carta / Fisico | `#8B4513` (marrone carta) |
| Default (altro) | `#595959` (grigio scuro) |

---

## Dimensioni standard

| Elemento | Larghezza | Altezza |
|----------|-----------|---------|
| Phase container (altezza per lane) | calcolato in base al contenuto | 40 (header) + N_lanes x 140 |
| Lane header (larghezza label) | 30 px | — |
| Task (action) | 140 px | 50 px |
| Gateway (decision) | 90 px | 90 px |
| START / END | 40 px | 40 px |
| Link event | 25 px | 25 px |
| Pain point | 160 px | 55 px |
| Spaziatura orizzontale tra centri (colonne) | 180 px | — |
| Margine verticale nella lane (y del task) | 45 px dall'alto | — |

**Perche lane alte 140 px?** Servono 50 px per il task, 20 px per la tool label sotto, 20 px per la freccia di collegamento pain point se presente, piu margini superiori/inferiori (15 px x 2). Questo evita sovrapposizioni e lascia respiro.

---

## Legenda (opzionale)

La legenda e **opzionale**: per default e disattivata (`legend: false`). La attivi solo se il diagramma e destinato a persone che non conoscono la notazione BPMN.

Quando presente, include:
- START (cerchio sottile verde)
- END (cerchio spesso rosso)
- Task (rettangolo arrotondato)
- Gateway XOR (rombo con X)
- Gateway AND (rombo con +) — solo se presente nel diagramma
- Link event (cerchio con freccia, con label "A")
- Pain point (rettangolo rosa)

La legenda si disegna **sotto l'ultimo phase container**, distanziata di 40 px, su sfondo grigio chiaro (`#F5F5F5`) con bordo grigio.

---

## Convenzioni di testo

- Nomi delle lane: Title Case (es. "Team Cantiere", "Ufficio Tecnico")
- Nomi delle fasi: MAIUSCOLO (es. "FASE 1 - CHIUSURA LAVORI")
- Testo nei task: verbo all'infinito o imperativo (es. "Completare il lavoro", "Inviare le foto")
- Testo nei gateway: domanda con "?" finale (es. "Approvato?", "Compliant?"), breve (max ~5 parole: deve stare dentro il rombo)
- Pain point: "(!) PAIN POINT N: [descrizione breve, max 12 parole]" — la numerazione e GLOBALE su tutto il diagramma (non riparte da 1 a ogni fase); lo script numera da solo, non mettere il numero nella label
- Label link event: una singola lettera maiuscola (A, B, C) o un numero (1, 2, 3)

---

## Variazioni TO-BE

Nel diagramma TO-BE aggiungi queste variazioni:

### Task automatizzato (sostituisce un'azione manuale)
- Sfondo: `#E2EFDA` (verde chiaro)
- Bordo: `#70AD47` (verde), spessore 2
- Label interna secondaria: "AUTO", in piccolo, grigio scuro `#404040`, italic
- Segnala che questo step e stato automatizzato rispetto all'AS-IS.

### Task nuovo (introdotto nel TO-BE, non esisteva prima)
- Sfondo: `#DEEAF1` (azzurro chiaro)
- Bordo: `#4472C4` (blu), spessore 2
- Label interna secondaria: "NUOVO"

### Task eliminato
Non viene rappresentato nel TO-BE: si rimuove. Se utile comunicare cosa e stato tolto rispetto all'AS-IS, puoi usare un box tratteggiato grigio con scritta "ELIMINATO: [cosa faceva prima]". Usalo con parsimonia.

### Pain point risolto
Non appare nel TO-BE: e stato risolto dall'automazione. La sintesi testuale finale elenchera i pain point risolti.

### Pannello informativo (info_panel)
- Sfondo: `#DEEAF1` (azzurro chiaro)
- Bordo: `#4472C4` (blu), spessore 2
- Testo: `#1F3864` (blu scuro), 9pt, allineato a sinistra in alto
- Vive in una banda dedicata sotto la fase (sotto la banda pain point), non connesso al flusso
- Uso: nei TO-BE generalizzati, dove un processo di riferimento e comune a piu dipartimenti, ospita la varianza (di dipartimento o di scenario) invece di moltiplicare gli swimlane

---

## Regole di qualita riassuntive

1. Una lane per attore, mai due attori nella stessa lane.
2. Le fasi sono rare: servono solo se cambiano attori/strumenti/scopo (vedi interview-guide).
3. I gateway sono rombi, non rettangoli. Mai confondere un task con una decisione.
4. I pain point stanno fuori dalla lane del flusso, collegati con linea tratteggiata al passo problematico.
5. Se un flusso cross-lane e lungo, usa link event (coppia A/A) invece di una freccia-serpente.
6. Le frecce "No" preferibilmente vanno verso l'alto o indietro; le "Si" verso destra o in basso. Riduce gli incroci.
7. La legenda e opzionale: includila solo se serve al destinatario del diagramma.
