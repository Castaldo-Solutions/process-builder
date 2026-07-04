# Guida all'Intervista — Process Builder

Questo documento guida la raccolta dati per AS-IS e TO-BE. Non è un modulo da compilare: è una bussola. Le domande vanno poste in modo conversazionale, adattando il linguaggio all'interlocutore, e vanno riordinate in base a quello che emerge.

La qualità del diagramma dipende al 90% da questa fase. Se esci da qui con dati ambigui, nessuno script di disegno ti salverà.

---

## Principi guida

1. Una cosa alla volta. Mai più di una domanda per turno. Lascia che chi parla vada a ruota libera: spesso le informazioni più utili arrivano dopo il silenzio.
2. Parafrasa sempre. Dopo ogni risposta importante, riformula in una frase: "Se ho capito, [X]. Giusto?". Questo tappa il 70% dei malintesi.
3. Non proporre soluzioni durante l'AS-IS. Anche se la risposta è ovvia, non la dai ora. L'AS-IS è fotografia, non terapia.
4. Pensa al diagramma mentre ascolti. Se una risposta non ti permette di decidere in quale lane mettere un'azione, chiedilo esplicitamente: "Questa cosa chi la fa materialmente, [attore X] o [attore Y]?".
5. Se manca qualcosa, fallo notare. "Mi hai detto che dopo la firma parte il lavoro, ma non mi hai detto come arriva la firma al cantiere. Come succede?".

---

## Intervista AS-IS

### Fase A — Contesto (apre la conversazione)

1. "Di che processo stiamo parlando? Ha un nome interno?"
2. "Cosa produce o abilita alla fine? Qual è il risultato atteso?"
3. "Con che frequenza gira? È giornaliero, settimanale, su richiesta?"
4. "Cosa fa scattare il processo? Qual è l'evento che lo avvia?"

### Fase B — Attori (chi c'è in gioco)

5. "Chi è coinvolto dall'inizio alla fine? Elenchiamo ruoli, non nomi di persone."
   - Per ogni attore annota: nome del ruolo, team/reparto, se è interno o esterno all'azienda.
6. "C'è qualcuno che entra solo in certi casi (es. un responsabile che interviene solo se si supera una soglia)?"
7. "C'è un sistema automatico da contare come attore (es. un gestionale che manda email da solo)? Se sì, mettiamolo in una lane 'Sistema'."

Obiettivo minimo di questa fase: avere la lista completa degli attori. Se sei insicuro, non andare avanti: torna indietro. Un attore dimenticato spesso si traduce in pain point nascosti.

### Fase C — Flusso (cosa succede, in ordine)

Procedi attore per attore, partendo da chi tocca per primo il processo. Per ogni attività chiedi sempre queste quattro cose:

- "Cosa fa materialmente?" (verbo all'infinito: verifica, invia, approva, carica)
- "Con quale strumento?" (WhatsApp, email, gestionale, Excel, CRM, telefono)
- "Quanto tempo ci vuole di solito?"
- "Cosa succede dopo? A chi passa la palla?"

Domande di rinforzo da usare quando serve:

- "Ci sono punti dove qualcuno deve decidere o approvare? Se sì, cosa succede in caso di sì e in caso di no?"
- "Ci sono casi in cui il processo torna indietro o si ripete? In quali condizioni?"
- "Ci sono eccezioni importanti da includere nel diagramma, anche se capitano raramente?"
- "Dove finisce il processo? Come si riconosce che è completato?"

### Fase D — Strumenti e handoff

Spesso il grosso dei pain point sta qui. Chiedi in modo mirato:

8. "Quanti sistemi diversi vengono usati in tutto il processo?"
9. "I sistemi si parlano tra loro o qualcuno copia dati a mano da uno all'altro?"
10. "Ci sono dati che vengono inseriti più di una volta, in posti diversi?"
11. "Come passano le informazioni da un attore al successivo? Email, chat, gestionale, telefono, carta?"

### Fase E — Pain point

Non chiedere "quali sono i pain point?" in modo astratto. Usa questa scaletta:

12. "Qual è la parte del processo che vi fa perdere più tempo?"
13. "Dove si fanno più errori? Chi se ne accorge, e quando?"
14. "Cosa vorreste non dover fare?"
15. "Ci sono passaggi spesso dimenticati o saltati? Perché?"
16. "Ci sono ritardi ricorrenti? Da cosa dipendono?"
17. "Se poteste cambiare una sola cosa, quale sarebbe?"

Ogni pain point deve avere: descrizione breve (max 12 parole), chi lo subisce (attore), a quale passo del flusso è attaccato.

---

## Fase F — Fasi del processo (SEZIONE CRITICA)

Questa parte è quella che più spesso viene gestita male. Leggila con attenzione: vale per AS-IS e TO-BE.

### Cosa è una fase in questo formato di swimlane

Una fase è un contenitore visivo (phase container blu) che raggruppa un insieme di lane e attività. NON è semplicemente un "momento cronologico". In uno swimlane Process Builder si usa una fase separata SOLO se è soddisfatta almeno UNA di queste tre condizioni:

1. **Cambio netto degli attori dominanti.** Tra una fase e l'altra, la maggior parte degli attori protagonisti cambia. Esempio vero: nel processo "Gestione Eventi" la fase pre-evento la gestiscono marketing e commerciale, quella in-evento operations e tecnici di campo, quella post-evento amministrazione e customer care. Tre gruppi quasi disgiunti: fasi separate giustificate.

2. **Cambio netto degli strumenti o delle procedure.** Gli strumenti principali cambiano quasi tutti. Esempio vero: pre-evento con CRM e email; in-evento con radio, tablet di campo, checklist cartacea; post-evento con gestionale di fatturazione e sondaggio NPS.

3. **Cambio netto dello scopo operativo.** Non è "stessa cosa, prima e dopo", è un altro obiettivo. Esempio: "istruttoria pratica" vs "erogazione finanziamento" sono obiettivi diversi; "attivazione servizio" vs "gestione ricorrente" sono obiettivi diversi.

Se NON c'è nessuna delle tre condizioni, il processo è a fase unica. Punto. Non forzare la divisione solo perché "è lungo": un processo lungo ma con stessi attori, stessi strumenti e stesso scopo resta a fase unica. Meglio un diagramma lungo in orizzontale che tre fasi finte che confondono il lettore.

### Procedimento operativo

Dopo aver raccolto il flusso, prima di disegnare:

Step 1. Prova a riassumere il processo in 2-4 blocchi naturali. Esempio: "preparazione", "esecuzione", "chiusura". Usa il linguaggio che ha usato l'utente.

Step 2. Per ogni coppia di blocchi adiacenti, rispondi a questo triage di tre domande:

- Cambiano gli attori dominanti tra questo blocco e il precedente? (sì / in parte / no)
- Cambiano gli strumenti principali? (sì / in parte / no)
- Cambia lo scopo operativo? (sì / in parte / no)

Step 3. Conta i "sì" per ogni confine tra blocchi:

- 2 o 3 "sì" → taglio di fase giustificato (usa phase container separato)
- 1 "sì" → borderline, proponi all'utente ma prediligi "fase unica"
- 0 "sì" → non separare, è lo stesso blocco

Step 4. Presenta all'utente la tua ipotesi in modo motivato:

"Dal flusso che abbiamo ricostruito mi sembra che il processo abbia [N] fasi distinte: [lista]. Le separo perché [motivo specifico, es. 'dopo l'approvazione cambia il protagonista: da commerciale si passa a operations, e cambiano anche gli strumenti, da CRM a gestionale di produzione']. Ti sembra corretto o preferisci una struttura diversa?"

Oppure, se il processo non ha fasi vere:

"Non vedo un cambio netto di attori, strumenti o scopo. Proporrei un diagramma a fase unica, che secondo me risulta più pulito. Ti va bene così o preferisci che lo divida lo stesso, magari per leggibilità?"

L'utente ha l'ultima parola. Se insiste su una divisione che tu consideri forzata, accettala ma annotalo nel riassunto finale come "scelta editoriale dell'utente, non un vero cambio di fase".

### Esempi concreti (da usare come riferimento)

Esempio 1 — "Gestione Eventi" (TRE FASI GIUSTIFICATE):
- Pre-evento: marketing + commerciale, usano CRM + email, scopo = vendita biglietti e preparazione.
- In-evento: operations + tecnici, usano radio + tablet + checklist, scopo = esecuzione.
- Post-evento: amministrazione + customer care, usano gestionale + email, scopo = fatturazione e feedback.
→ 3 fasi, ognuna con attori, strumenti e scopo diversi.

Esempio 2 — "Richiesta ferie" (FASE UNICA):
- Dipendente compila richiesta, HR valuta, approva, registra.
- Stessi attori dall'inizio alla fine, stessi strumenti (gestionale HR + email), stesso scopo.
→ Nessuna fase separata. Diagramma unico anche se il flusso è lungo.

Esempio 3 — "Chiusura lavori + Correttivo" (DUE FASI GIUSTIFICATE):
- Chiusura lavori: Team Cantiere + Amministratore + Ufficio Tecnico, scopo = chiudere il lavoro fatto.
- Richiesta correttivo: Amministratore + Ufficio Tecnico + Team Cantiere, scopo = gestire una richiesta di rework.
- Gli attori sono gli stessi MA lo scopo operativo è nettamente diverso (un flusso chiude, l'altro apre un problema) e il trigger è diverso.
→ 2 fasi, giustificate dal cambio di scopo.

Esempio 4 — "Onboarding cliente" (FASE UNICA tipicamente):
- Commerciale raccoglie dati, back office crea cartella, IT crea account.
- Stesso scopo: portare il cliente dallo stato "firmato" a "operativo". Attori in sequenza ma nessun gruppo si alterna nettamente.
→ Fase unica, anche se ci sono 3 attori diversi che si passano la palla.

---

### Fase G — Domanda di chiusura AS-IS

"C'è qualcosa che non ti ho chiesto e che conta? Un'eccezione, un caso particolare, qualcosa che succede raramente ma che nel diagramma andrebbe incluso?"

---

## Conferma prima di disegnare

Prima di generare il JSON, presenta all'utente un riassunto strutturato. Usa questo formato (adattalo al tono dell'utente, ma mantieni le sezioni):

```
Ho ricostruito il processo così:

PROCESSO: [nome]
SCOPO: [una riga]
TRIGGER: [cosa lo fa partire]
FREQUENZA: [quanto spesso gira]

ATTORI ([N]):
- [Nome ruolo] — [team/reparto, interno/esterno]
- ...

STRUTTURA A FASI: [N fasi, con motivazione, oppure "fase unica"]
1. [Nome fase] — [una riga su cosa succede]
2. ...

FLUSSO (per fase):
Fase 1 — [nome]:
 - [Attore] fa [azione] con [strumento]
 - [Attore] decide [domanda?]: sì → [...]; no → [...]
 - ...

PAIN POINT ([N]):
 - [#1] [descrizione] — subito da [attore], passo [riferimento]
 - ...

Correggo qualcosa prima di disegnare?
```

Aspetta l'ok esplicito prima di procedere alla generazione del JSON. Un giro di correzione qui vale dieci iterazioni sul file .drawio.

---

## Intervista TO-BE

L'obiettivo è capire aspirazioni e vincoli PRIMA di proporre soluzioni. Non partire con "io farei così": ascolta.

### Fase A — Visione

1. "Se questo processo funzionasse perfettamente, cosa sarebbe diverso da oggi?"
2. "Qual è il pain point che ti pesa di più? Quello che, risolto, cambia davvero la giornata di chi lavora nel processo?"
3. "Ci sono processi simili nella tua azienda che già funzionano bene? Cosa li fa funzionare?"

### Fase B — Vincoli

4. "Quali strumenti o sistemi attuali NON sono sostituibili? (contratti in essere, decisioni di gruppo, integrazioni vincolanti)"
5. "Budget: preferite soluzioni a basso costo o siete aperti a investimenti più seri?"
6. "Tempo: entro quando volete vedere i primi miglioramenti in produzione?"
7. "Resistenza al cambiamento: ci sono persone che potrebbero frenare l'adozione?"
8. "Compliance: ci sono vincoli normativi che limitano cosa si può automatizzare?"

### Fase C — Roadmap

9. "Preferite partire da un cambio piccolo e rapido (quick win) o ripensare il processo da zero?"
10. "Avete risorse tecniche interne (IT, dev) o dovete affidarvi a un partner?"
11. "Come misurerete il successo? Quali metriche vi aspettate di vedere migliorare?"

### Mappatura pain point → soluzioni

Prima di generare i due diagrammi TO-BE, costruisci e condividi questa tabella con l'utente:

| # | Pain point | Impatto attuale | Soluzione Quick Win | Soluzione Full Automation |
|---|------------|-----------------|---------------------|---------------------------|
| 1 | ...        | ore/errori/costi| tool o automazione leggera | integrazione completa |

Poi chiedi: "Per la versione Quick Win includo i pain point [lista]; per la Full Automation includo anche [lista]. Va bene così o cambiamo?"

### Domanda di chiusura TO-BE

"C'è qualcosa di importante che non ti ho chiesto? Qualcosa che ti aspetti di vedere nel TO-BE e che non abbiamo ancora discusso?"

---

## Errori frequenti da evitare

- **Scambiare la cronologia per una fase.** "Prima succede A, poi B" non basta: deve cambiare qualcosa di strutturale (attori / strumenti / scopo).
- **Mettere decisioni come se fossero azioni.** Se c'è un "sì/no" o un "se, allora", quello è un gateway (rombo), non un rettangolo.
- **Dimenticare il sistema come attore.** Se un gestionale manda email notturne da solo, va in una lane "Sistema". Non attribuire la sua attività a una persona.
- **Pain point generici.** "C'è confusione" non serve. "Il tecnico riceve la richiesta su WhatsApp e la perde tra i messaggi personali" serve.
- **Forzare il cliente a usare vocabolario tecnico.** Se non conosce "workflow" o "gateway", non imporlo. Usa il suo linguaggio.
- **Dividere in fasi per leggibilità quando non servono.** Se il processo è lungo ma compatto, meglio un diagramma orizzontale ampio che tre fasi artificiali.
