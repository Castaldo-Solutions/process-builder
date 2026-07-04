#!/usr/bin/env python3
"""
Process Builder - Swimlane Generator
-------------------------------------
Genera file draw.io (.drawio) in stile ibrido BPMN con palette curata
a partire da un JSON descrittivo.

Uso:
    python generate_swimlane.py <input.json> [output.drawio]
    python generate_swimlane.py <input.json> --validate

Se output non e specificato, usa il titolo dal JSON o "output.drawio".

Obiettivi di design (versione 2.1):
- Forme BPMN standard (start sottile, end spesso, gateway con simbolo, link event).
- Layout a colonne con step fisso: niente sovrapposizioni tra elementi.
- Pain point posizionati FUORI dalla lane, sotto il phase container, connessi al
  task con linea tratteggiata; distribuiti su piu righe se non entrano in una.
- Label "AUTO"/"NUOVO" dentro il rettangolo del task (non sotto).
- Tool label separata sotto il task, altezza dedicata nella lane.
- Legenda opzionale (default false) e disegnata solo se richiesta.
- Connettori cross-lane: coppia di link event (outgoing A -> incoming A) quando
  il percorso e lungo; frecce dirette per distanze brevi.
- Validazione completa dell'input con messaggi actionable: id duplicati,
  attori inesistenti, connessioni orfane, tipi sconosciuti.

Exit code: 0 = successo, 1 = errore (JSON invalido o schema non rispettato).
Con --strict anche i warning diventano bloccanti.

Schema JSON di input: vedi references/drawio-xml-guide.md.
"""

import argparse
import json
import math
import re
import sys
from xml.etree.ElementTree import Element, SubElement, indent, tostring

__version__ = "2.1.0"

# =============================================================================
# Costanti di stile e layout
# =============================================================================

# Palette fase/lane
PHASE_HEADER_H = 40
LANE_H         = 140
LANE_LABEL_W   = 30
# PHASE_LABEL_W deve coincidere con lo startSize del phase (PHASE_HEADER_H):
# le lane si posizionano a x=PHASE_LABEL_W, e se non combacia con la striscia
# titolo del phase le lane non risultano incapsulate nel phase container.
PHASE_LABEL_W  = PHASE_HEADER_H

PHASE_STYLE = (
    "swimlane;startSize={h};horizontal=0;"
    "fillColor=#0057B7;strokeColor=#0057B7;fontColor=#FFFFFF;"
    "fontStyle=1;fontSize=11;collapsible=0;html=1;"
).format(h=PHASE_HEADER_H)

LANE_COLORS = [
    {"fill": "#FFF2CC", "stroke": "#d6b656"},  # giallo crema
    {"fill": "#FCE4D6", "stroke": "#d6b656"},  # rosa salmone
    {"fill": "#FFFFFF", "stroke": "#B7B7B7"},  # bianco
    {"fill": "#E2EFDA", "stroke": "#70AD47"},  # verde chiaro
    {"fill": "#DEEAF1", "stroke": "#4472C4"},  # azzurro chiaro
]

# Dimensioni elementi
TASK_W       = 140
TASK_H       = 50
GATEWAY_W    = 90
GATEWAY_H    = 90
EVENT_W      = 40   # start/end
EVENT_H      = 40
LINK_W       = 28   # link event
LINK_H       = 28
PAIN_W       = 170
PAIN_H       = 60
TOOL_H       = 20   # altezza label strumento sotto task

# Layout geometrico
COL_W        = 180  # passo colonna (center-to-center)
TASK_Y       = 45   # y del task dentro la lane (da top della lane)
START_X      = 20   # primo elemento x dentro la lane (dopo label lane)
PHASE_X      = 20   # phase container x
PHASE_Y0     = 20   # prima fase y
PHASE_V_GAP  = 30   # gap verticale tra fasi
PAIN_V_GAP   = 25   # distanza pain-point area - phase container
PAIN_ROW_H   = 80   # altezza di una riga di pain point
PAIN_H_GAP   = 20   # distanza orizzontale minima tra pain point
LEGEND_V_GAP = 50

# Pannelli informativi (varianze TO-BE generalizzato)
INFO_W       = 320  # larghezza pannello informativo
INFO_H       = 75   # altezza pannello informativo
INFO_ROW_H   = 95   # altezza della banda dei pannelli informativi
INFO_V_GAP   = 25   # distanza tra banda pain point e banda pannelli informativi

# Colori strumenti
TOOL_COLORS = {
    "whatsapp":  "#7030A0",
    "cms":       "#4472C4",
    "email":     "#FF7C00",
    "excel":     "#217346",
    "office":    "#217346",
    "erp":       "#C55A11",
    "gestionale":"#C55A11",
    "app":       "#2E74B5",
    "telefono":  "#888888",
    "carta":     "#8B4513",
}

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# =============================================================================
# Helper
# =============================================================================

_id_counter = 2  # 0 e 1 sono riservati

def new_id():
    global _id_counter
    _id_counter += 1
    return str(_id_counter)

def reset_ids():
    global _id_counter
    _id_counter = 2

def lane_style(index: int) -> str:
    c = LANE_COLORS[index % len(LANE_COLORS)]
    return (
        "swimlane;startSize={lw};horizontal=0;"
        "fillColor={fill};strokeColor={stroke};"
        "fontStyle=1;fontSize=10;collapsible=0;html=1;"
    ).format(lw=LANE_LABEL_W, fill=c["fill"], stroke=c["stroke"])

def tool_color(tool_name: str) -> str:
    if not tool_name:
        return "#595959"
    key = str(tool_name).lower().strip()
    for k, v in TOOL_COLORS.items():
        if k in key:
            return v
    return "#595959"

def safe_value(text) -> str:
    """Converte newline in &#xa; per l'attributo value di draw.io."""
    if text is None:
        return ""
    return str(text).replace("\n", "&#xa;")

def xml_pretty(root: Element) -> str:
    # Indentazione nativa di ElementTree (Python >= 3.9): nessun re-parsing
    # dell'XML, quindi nessuna superficie XXE/billion-laughs.
    indent(root, space="  ")
    raw = tostring(root, encoding="unicode")
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw + "\n"
    # tostring escapa '&' a '&amp;' anche dentro l'entita' &#xa; (newline):
    # drawio interpreterebbe '&amp;#xa;' come testo letterale invece che a capo.
    # Ripristino l'entity cosi' i newline nelle label funzionano.
    result = result.replace("&amp;#xa;", "&#xa;")
    return result

# =============================================================================
# Classificazione tipi
# =============================================================================

FLOW_TYPES = {
    "start", "end",
    "action", "action_auto", "action_new", "action_deleted",
    "gateway", "gateway_xor", "gateway_and", "gateway_or",
    "decision",  # alias legacy -> gateway_xor
    "link_out", "link_in", "connector",  # legacy connector -> link generico
}

OFF_LANE_TYPES = {"pain_point", "info_panel"}

KNOWN_TYPES = FLOW_TYPES | OFF_LANE_TYPES

def canonical_type(etype: str) -> str:
    if etype == "decision":
        return "gateway_xor"
    if etype == "gateway":
        return "gateway_xor"
    if etype == "connector":
        return "link_out"
    return etype

def is_flow_element(etype: str) -> bool:
    return etype in FLOW_TYPES

# =============================================================================
# Validazione input
# =============================================================================

class ValidationReport:
    """Raccoglie errori (bloccanti) e warning (non bloccanti) con messaggi
    actionable: dicono sempre DOVE sta il problema e COME correggerlo."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    @property
    def ok(self):
        return not self.errors


def validate(data) -> ValidationReport:
    rep = ValidationReport()

    if not isinstance(data, dict):
        rep.error("Il JSON di input deve essere un oggetto {...}, non {}.".format(
            type(data).__name__))
        return rep

    phases = data.get("phases")
    if phases is None:
        rep.error('Manca il campo obbligatorio "phases" (lista delle fasi, anche una sola).')
        return rep
    if not isinstance(phases, list) or not phases:
        rep.error('"phases" deve essere una lista non vuota di fasi.')
        return rep

    all_ids = {}          # id -> (phase_idx, tipo) per check duplicati e riferimenti
    link_labels = {"out": [], "in": []}

    for pi, phase in enumerate(phases):
        where = 'fase {} ("{}")'.format(pi + 1, phase.get("name", "?")) \
            if isinstance(phase, dict) else "fase {}".format(pi + 1)

        if not isinstance(phase, dict):
            rep.error("La {} deve essere un oggetto {{...}}.".format(where))
            continue

        if not phase.get("name"):
            rep.warn('La fase {} non ha "name": usero "FASE {}".'.format(pi + 1, pi + 1))

        actors = phase.get("actors")
        if not isinstance(actors, list) or not actors:
            rep.error('Nella {} manca "actors" (lista non vuota di ruoli, uno per lane).'
                      .format(where))
            actors = []
        else:
            seen_actors = set()
            for a in actors:
                if not isinstance(a, str) or not a.strip():
                    rep.error('Nella {} c\'e un attore non valido: {!r}. '
                              'Ogni attore deve essere una stringa non vuota.'
                              .format(where, a))
                elif a in seen_actors:
                    rep.error('Nella {} l\'attore "{}" compare due volte in "actors". '
                              'Ogni attore deve avere una sola lane.'.format(where, a))
                else:
                    seen_actors.add(a)
            if len(actors) > len(LANE_COLORS):
                rep.warn('La {} ha {} attori: i colori delle lane verranno riciclati '
                         'oltre il {}o attore.'.format(where, len(actors), len(LANE_COLORS)))

        elements = phase.get("elements")
        if not isinstance(elements, list):
            rep.error('Nella {} manca "elements" (lista dei nodi del processo).'.format(where))
            elements = []
        elif not elements:
            rep.warn("La {} non ha elementi: verra disegnata vuota.".format(where))

        for ei, elem in enumerate(elements):
            if not isinstance(elem, dict):
                rep.error("Nella {}, l'elemento in posizione {} deve essere un oggetto {{...}}."
                          .format(where, ei + 1))
                continue
            eid = elem.get("id")
            if not eid or not isinstance(eid, str):
                rep.error('Nella {}, l\'elemento in posizione {} non ha un "id" valido '
                          '(stringa non vuota).'.format(where, ei + 1))
                continue
            if eid in all_ids:
                rep.error('Id duplicato "{}": usato nella fase {} e nella {}. '
                          'Ogni id deve essere univoco in TUTTO il file, anche tra fasi diverse.'
                          .format(eid, all_ids[eid][0] + 1, where))
                continue

            raw_type = elem.get("type", "action")
            if raw_type not in KNOWN_TYPES:
                rep.warn('Elemento "{}" ({}): tipo sconosciuto "{}", verra disegnato come '
                         'task generico. Tipi validi: {}.'
                         .format(eid, where, raw_type, ", ".join(sorted(KNOWN_TYPES))))
            etype = canonical_type(raw_type)
            all_ids[eid] = (pi, etype)

            if etype in FLOW_TYPES or raw_type not in KNOWN_TYPES:
                actor = elem.get("actor")
                if actor and actors and actor not in actors:
                    rep.warn('Elemento "{}" ({}): l\'attore "{}" non esiste in "actors" '
                             'della fase. Verra messo nella prima lane ("{}"). '
                             'Controlla maiuscole e spazi.'
                             .format(eid, where, actor, actors[0] if actors else "?"))
                elif not actor and etype in FLOW_TYPES:
                    rep.warn('Elemento "{}" ({}): manca "actor", verra messo nella prima lane.'
                             .format(eid, where))

            if etype in ("link_out", "link_in"):
                lbl = elem.get("link_label", elem.get("label"))
                if not lbl:
                    rep.warn('Link event "{}" ({}): manca "link_label". Senza etichetta '
                             'il lettore non capisce quale coppia collega.'.format(eid, where))
                else:
                    link_labels["out" if etype == "link_out" else "in"].append(str(lbl))

    # Secondo giro: riferimenti (target dei pain point, connessioni) hanno
    # bisogno della mappa completa degli id.
    for pi, phase in enumerate(phases):
        if not isinstance(phase, dict):
            continue
        where = 'fase {} ("{}")'.format(pi + 1, phase.get("name", "?"))
        elements = phase.get("elements") if isinstance(phase.get("elements"), list) else []

        for elem in elements:
            if not isinstance(elem, dict):
                continue
            eid = elem.get("id")
            if canonical_type(elem.get("type", "")) == "pain_point":
                tgt = elem.get("target")
                if tgt and tgt not in all_ids:
                    rep.warn('Pain point "{}" ({}): il target "{}" non corrisponde a nessun '
                             'elemento. Il pain point restera senza linea tratteggiata.'
                             .format(eid, where, tgt))
                elif tgt and all_ids[tgt][1] in OFF_LANE_TYPES:
                    rep.warn('Pain point "{}" ({}): il target "{}" e un altro elemento fuori '
                             'lane. Punta a un task o gateway del flusso.'
                             .format(eid, where, tgt))
                elif not tgt:
                    rep.warn('Pain point "{}" ({}): manca "target", restera fluttuante '
                             'senza collegamento al passo problematico.'.format(eid, where))

        connections = phase.get("connections")
        if connections is None:
            rep.warn('La {} non ha "connections": nessuna freccia verra disegnata per '
                     'questa fase.'.format(where))
            connections = []
        elif not isinstance(connections, list):
            rep.error('Nella {}, "connections" deve essere una lista.'.format(where))
            connections = []

        for ci, conn in enumerate(connections):
            cwhere = "connessione {} della {}".format(ci + 1, where)
            if not isinstance(conn, dict):
                rep.error("La {} deve essere un oggetto {{...}}.".format(cwhere))
                continue
            frm, to = conn.get("from"), conn.get("to")
            if not frm or not to:
                rep.error('La {} deve avere entrambi i campi "from" e "to".'.format(cwhere))
                continue
            for side, ref in (("from", frm), ("to", to)):
                if ref not in all_ids:
                    rep.error('La {} punta a un id inesistente: "{}"="{}" non e dichiarato '
                              'in nessuna fase. Correggi l\'id o aggiungi l\'elemento.'
                              .format(cwhere, side, ref))
                elif all_ids[ref][1] in OFF_LANE_TYPES:
                    rep.error('La {} collega "{}" che e un {} (fuori flusso). '
                              'Pain point e info panel non fanno parte del sequence flow: '
                              'per i pain point usa il campo "target".'
                              .format(cwhere, ref, all_ids[ref][1]))
            color = conn.get("color")
            if color and not HEX_COLOR_RE.match(str(color)):
                rep.warn('La {} ha un colore non valido "{}" (atteso formato "#RRGGBB"). '
                         'Verra usato comunque, ma draw.io potrebbe ignorarlo.'
                         .format(cwhere, color))

    # Coppie di link event
    outs, ins = sorted(link_labels["out"]), sorted(link_labels["in"])
    for lbl in set(outs) - set(ins):
        rep.warn('Link event: "link_out" con etichetta "{}" senza il corrispondente '
                 '"link_in". Il lettore non trovera il punto di ripresa.'.format(lbl))
    for lbl in set(ins) - set(outs):
        rep.warn('Link event: "link_in" con etichetta "{}" senza il corrispondente '
                 '"link_out".'.format(lbl))

    return rep

# =============================================================================
# Layout: assegnazione colonne
# =============================================================================

def element_width(etype: str) -> int:
    t = canonical_type(etype)
    if t.startswith("action"):
        return TASK_W
    if t.startswith("gateway"):
        return GATEWAY_W
    if t in ("start", "end"):
        return EVENT_W
    if t in ("link_in", "link_out"):
        return LINK_W
    return TASK_W

def element_height(etype: str) -> int:
    t = canonical_type(etype)
    if t.startswith("action"):
        return TASK_H
    if t.startswith("gateway"):
        return GATEWAY_H
    if t in ("start", "end"):
        return EVENT_H
    if t in ("link_in", "link_out"):
        return LINK_H
    return TASK_H

def assign_columns(elements):
    """
    Ogni elemento flow occupa una colonna. Pain point (off-lane) non occupano colonne.
    Ritorna dict {id: col_index}.
    """
    cols = {}
    col = 0
    for e in elements:
        if not isinstance(e, dict) or "id" not in e:
            continue
        etype = canonical_type(e.get("type", "action"))
        if etype in OFF_LANE_TYPES:
            cols[e["id"]] = None
        else:
            # Tipi flow e tipi sconosciuti (disegnati come task) occupano colonna
            cols[e["id"]] = col
            col += 1
    return cols

def col_to_center_x(col: int) -> int:
    """Centro della colonna (col 0 centrato in START_X + COL_W/2)."""
    return START_X + COL_W // 2 + col * COL_W

def n_columns(elements) -> int:
    return sum(
        1 for e in elements
        if isinstance(e, dict)
        and canonical_type(e.get("type", "action")) not in OFF_LANE_TYPES
    )

def phase_inner_width(elements) -> int:
    n = n_columns(elements)
    col_w = START_X + n * COL_W + START_X  # margine dx simmetrico
    n_info = sum(
        1 for e in elements
        if isinstance(e, dict) and canonical_type(e.get("type", "")) == "info_panel"
    )
    if n_info:
        info_w = START_X + n_info * INFO_W + (n_info - 1) * 20 + START_X
        return max(col_w, info_w)
    return col_w

def phase_total_width(elements) -> int:
    return PHASE_LABEL_W + phase_inner_width(elements)

def phase_height(n_lanes: int) -> int:
    # Il phase e' un swimlane horizontal=0: la striscia titolo (startSize) e'
    # orizzontale e NON aggiunge altezza. L'altezza e' la somma delle lane,
    # cosi' le lane piastrellano esattamente il phase container.
    return max(1, n_lanes) * LANE_H

def pain_per_row(phase_w: int) -> int:
    """Quanti pain point entrano in una riga sotto il phase container."""
    avail = phase_w - PHASE_LABEL_W
    return max(1, (avail + PAIN_H_GAP) // (PAIN_W + PAIN_H_GAP))

def pain_rows_needed(n_pain: int, phase_w: int) -> int:
    if not n_pain:
        return 0
    return math.ceil(n_pain / pain_per_row(phase_w))

# =============================================================================
# Generatori di singolo elemento
# =============================================================================

def draw_start(root, xml_id, parent, label, center_x):
    x = center_x - EVENT_W // 2
    y = (LANE_H - EVENT_H) // 2
    style = (
        "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
        "fillColor=#92D050;strokeColor=#66A30E;fontSize=9;fontStyle=1;"
        "verticalLabelPosition=bottom;verticalAlign=top;labelWidth=110;"
    )
    cell = SubElement(root, "mxCell",
        id=xml_id, value=safe_value(label or ""),
        style=style, vertex="1", parent=parent
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(EVENT_W), height=str(EVENT_H),
        **{"as": "geometry"}
    )

def draw_end(root, xml_id, parent, label, center_x):
    x = center_x - EVENT_W // 2
    y = (LANE_H - EVENT_H) // 2
    style = (
        "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
        "fillColor=#FF9999;strokeColor=#CC0000;strokeWidth=3;"
        "fontSize=9;fontStyle=1;"
        "verticalLabelPosition=bottom;verticalAlign=top;labelWidth=110;"
    )
    cell = SubElement(root, "mxCell",
        id=xml_id, value=safe_value(label or ""),
        style=style, vertex="1", parent=parent
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(EVENT_W), height=str(EVENT_H),
        **{"as": "geometry"}
    )

def draw_task(root, xml_id, parent, label, center_x, variant="manual"):
    """variant: manual | auto | new | deleted"""
    x = center_x - TASK_W // 2
    y = TASK_Y
    if variant == "auto":
        style = ("rounded=1;whiteSpace=wrap;html=1;arcSize=10;"
                 "fillColor=#E2EFDA;strokeColor=#70AD47;strokeWidth=2;fontSize=10;")
        badge = "AUTO"
        badge_color = "#2F6F2B"
    elif variant == "new":
        style = ("rounded=1;whiteSpace=wrap;html=1;arcSize=10;"
                 "fillColor=#DEEAF1;strokeColor=#4472C4;strokeWidth=2;fontSize=10;")
        badge = "NUOVO"
        badge_color = "#2A4B8D"
    elif variant == "deleted":
        style = ("rounded=1;whiteSpace=wrap;html=1;arcSize=10;dashed=1;"
                 "fillColor=#F2F2F2;strokeColor=#808080;fontColor=#808080;"
                 "strokeWidth=1;fontSize=10;")
        badge = "ELIMINATO"
        badge_color = "#808080"
    else:
        style = ("rounded=1;whiteSpace=wrap;html=1;arcSize=10;"
                 "fillColor=#FFFFFF;strokeColor=#000000;fontSize=10;")
        badge = None
        badge_color = None

    cell = SubElement(root, "mxCell",
        id=xml_id, value=safe_value(label or ""),
        style=style, vertex="1", parent=parent
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(TASK_W), height=str(TASK_H),
        **{"as": "geometry"}
    )

    # Badge AUTO/NUOVO/ELIMINATO come piccola label in alto a destra dentro il task
    if badge:
        bid = new_id()
        bstyle = (
            "text;html=1;strokeColor=none;fillColor=none;"
            "align=right;verticalAlign=top;fontSize=7;"
            "fontColor={c};fontStyle=3;"
        ).format(c=badge_color)
        bcell = SubElement(root, "mxCell",
            id=bid, value=badge, style=bstyle,
            vertex="1", parent=parent
        )
        SubElement(bcell, "mxGeometry",
            x=str(x + TASK_W - 55), y=str(y + 2),
            width="52", height="12",
            **{"as": "geometry"}
        )

def draw_tool_label(root, parent, task_center_x, tool_name):
    if not tool_name:
        return
    tid = new_id()
    tcolor = tool_color(tool_name)
    x = task_center_x - TASK_W // 2
    y = TASK_Y + TASK_H + 2
    style = (
        "text;html=1;strokeColor=none;fillColor=none;"
        "align=center;verticalAlign=middle;fontSize=9;"
        "fontColor={c};fontStyle=3;"
    ).format(c=tcolor)
    cell = SubElement(root, "mxCell",
        id=tid, value="[ {n} ]".format(n=tool_name), style=style,
        vertex="1", parent=parent
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(TASK_W), height=str(TOOL_H),
        **{"as": "geometry"}
    )

def draw_gateway(root, xml_id, parent, label, center_x, kind="xor"):
    x = center_x - GATEWAY_W // 2
    y = (LANE_H - GATEWAY_H) // 2
    has_label = bool(label and str(label).strip())

    # XOR con domanda: la domanda sta DENTRO il rombo e il marker X si omette
    # (ammesso da BPMN 2.0: il gateway esclusivo "blank" e la forma piu
    # comune). Cosi nessuna label esterna puo essere attraversata dalle
    # frecce che corrono nel corridoio alto della lane.
    if has_label and kind == "xor":
        style = (
            "rhombus;whiteSpace=wrap;html=1;"
            "fillColor=#FFE699;strokeColor=#d6b656;"
            "fontSize=9;fontStyle=1;verticalAlign=middle;"
        )
        cell = SubElement(root, "mxCell",
            id=xml_id, value=safe_value(label),
            style=style, vertex="1", parent=parent
        )
        SubElement(cell, "mxGeometry",
            x=str(x), y=str(y), width=str(GATEWAY_W), height=str(GATEWAY_H),
            **{"as": "geometry"}
        )
        return

    # AND / OR (o XOR senza domanda): marker BPMN centrato nel rombo,
    # eventuale label esterna in alto a sinistra.
    style = (
        "rhombus;whiteSpace=wrap;html=1;"
        "fillColor=#FFE699;strokeColor=#d6b656;"
        "fontSize=10;fontStyle=1;"
        "verticalLabelPosition=top;verticalAlign=bottom;"
        "labelPosition=left;align=right;"
    )
    cell = SubElement(root, "mxCell",
        id=xml_id, value=safe_value(label or ""),
        style=style, vertex="1", parent=parent
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(GATEWAY_W), height=str(GATEWAY_H),
        **{"as": "geometry"}
    )

    symbols = {"xor": "X", "and": "+", "or": "O"}
    sym = symbols.get(kind, "X")
    sid = new_id()
    sstyle = (
        "text;html=1;strokeColor=none;fillColor=none;"
        "align=center;verticalAlign=middle;fontSize=14;"
        "fontColor=#8B6914;fontStyle=1;"
    )
    scell = SubElement(root, "mxCell",
        id=sid, value=sym, style=sstyle,
        vertex="1", parent=parent
    )
    SubElement(scell, "mxGeometry",
        x=str(x + GATEWAY_W // 2 - 8), y=str(y + GATEWAY_H // 2 - 8),
        width="16", height="16",
        **{"as": "geometry"}
    )

def draw_link_event(root, xml_id, parent, label_inside, center_x, direction="out", lane_h=LANE_H):
    """direction: out | in. label_inside: lettera (A, B, C)."""
    x = center_x - LINK_W // 2
    y = (lane_h - LINK_H) // 2
    style = (
        "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
        "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;"
        "fontSize=10;fontStyle=1;"
    )
    cell = SubElement(root, "mxCell",
        id=xml_id, value=safe_value(label_inside or ""),
        style=style, vertex="1", parent=parent
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(LINK_W), height=str(LINK_H),
        **{"as": "geometry"}
    )

    # Piccolo triangolo/freccia accanto per indicare direzione
    arrow = "▶" if direction == "out" else "◀"
    aid = new_id()
    ax = x - 10 if direction == "in" else x + LINK_W + 2
    astyle = (
        "text;html=1;strokeColor=none;fillColor=none;"
        "align=center;verticalAlign=middle;fontSize=10;"
        "fontColor=#555555;"
    )
    acell = SubElement(root, "mxCell",
        id=aid, value=arrow, style=astyle,
        vertex="1", parent=parent
    )
    SubElement(acell, "mxGeometry",
        x=str(ax), y=str(y + 6),
        width="10", height="14",
        **{"as": "geometry"}
    )

# =============================================================================
# Disegno pain point (fuori lane)
# =============================================================================

def draw_pain_point(root_elem, xml_id, label, x, y):
    style = (
        "rounded=1;whiteSpace=wrap;html=1;arcSize=8;"
        "fillColor=#FFD7D7;strokeColor=#C00000;strokeWidth=2;"
        "fontColor=#C00000;fontStyle=1;fontSize=9;"
    )
    cell = SubElement(root_elem, "mxCell",
        id=xml_id, value=safe_value(label),
        style=style, vertex="1", parent="1"
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(PAIN_W), height=str(PAIN_H),
        **{"as": "geometry"}
    )

def draw_pain_link(root_elem, source_id, target_id):
    """Linea tratteggiata rossa pain_point -> task."""
    edge_id = new_id()
    # Aggancio leggermente a sinistra del centro-basso del task, cosi la
    # tratteggiata non corre sovrapposta a un'eventuale freccia del flusso
    # che entra dal centro-basso.
    style = (
        "edgeStyle=none;dashed=1;html=1;"
        "strokeColor=#C00000;strokeWidth=1;"
        "startArrow=none;endArrow=none;"
        "exitX=0.5;exitY=0;exitDx=0;exitDy=0;"
        "entryX=0.3;entryY=1;entryDx=0;entryDy=0;"
    )
    edge = SubElement(root_elem, "mxCell",
        id=edge_id, style=style, edge="1",
        source=source_id, target=target_id, parent="1"
    )
    SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})

def draw_info_panel(root_elem, xml_id, label, x, y):
    """Pannello informativo azzurro: nei TO-BE generalizzati ospita le varianze
    (di dipartimento o di scenario) di un processo di riferimento comune a piu'
    dipartimenti. Vive in una banda dedicata sotto le fasi, non e' connesso al flusso."""
    style = (
        "rounded=1;whiteSpace=wrap;html=1;arcSize=6;"
        "fillColor=#DEEAF1;strokeColor=#4472C4;strokeWidth=2;"
        "fontColor=#1F3864;fontSize=9;align=left;verticalAlign=top;spacing=6;"
    )
    cell = SubElement(root_elem, "mxCell",
        id=xml_id, value=safe_value(label),
        style=style, vertex="1", parent="1"
    )
    SubElement(cell, "mxGeometry",
        x=str(x), y=str(y), width=str(INFO_W), height=str(INFO_H),
        **{"as": "geometry"}
    )

# =============================================================================
# Disegno frecce (sequence flow)
# =============================================================================

def draw_edge(root, source_xml, target_xml, parent, label="", color="#000000",
              is_return=False, exit_hint=None, entry_hint=None):
    """exit_hint: None | "right" | "top" | "bottom" — lato di uscita preferito
    dalla sorgente. entry_hint: None | "left" — lato di ingresso preferito.
    Usati per separare le frecce attorno ai gateway ed evitare sovrapposizioni."""
    eid = new_id()
    style_parts = [
        "edgeStyle=orthogonalEdgeStyle",
        "rounded=0",
        "html=1",
        "jettySize=auto",
        "strokeColor={c}".format(c=color),
    ]
    if label:
        style_parts.append("fontColor={c}".format(c=color))
        style_parts.append("fontStyle=1")
        style_parts.append("fontSize=10")
    if is_return:
        # Frecce "No" / ritorno: preferisci uscita dall'alto e entrata dall'alto
        style_parts.append("exitX=0.5;exitY=0;exitDx=0;exitDy=0")
        style_parts.append("entryX=0.5;entryY=0;entryDx=0;entryDy=0")
    elif exit_hint == "right":
        style_parts.append("exitX=1;exitY=0.5;exitDx=0;exitDy=0")
    elif exit_hint == "top":
        style_parts.append("exitX=0.5;exitY=0;exitDx=0;exitDy=0")
    elif exit_hint == "bottom":
        style_parts.append("exitX=0.5;exitY=1;exitDx=0;exitDy=0")
    if not is_return:
        if entry_hint == "left":
            style_parts.append("entryX=0;entryY=0.5;entryDx=0;entryDy=0")
        elif entry_hint == "top":
            style_parts.append("entryX=0.5;entryY=0;entryDx=0;entryDy=0")
        elif entry_hint == "bottom":
            style_parts.append("entryX=0.5;entryY=1;entryDx=0;entryDy=0")
    style = ";".join(style_parts) + ";"
    edge = SubElement(root, "mxCell",
        id=eid, value=safe_value(label), style=style, edge="1",
        source=source_xml, target=target_xml, parent=parent
    )
    if label:
        # Label vicina alla sorgente (es. subito fuori dal gateway), non a
        # meta freccia dove diventa ambigua.
        SubElement(edge, "mxGeometry", relative="1", x="-0.6",
                   **{"as": "geometry"})
    else:
        SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})
    return eid

# =============================================================================
# Generazione completa del grafo
# =============================================================================

def build_graph(data):
    reset_ids()

    graph = Element("mxGraphModel",
        dx="1422", dy="762", grid="1", gridSize="10",
        guides="1", tooltips="1", connect="1", arrows="1",
        fold="1", page="1", pageScale="1",
        pageWidth="1654", pageHeight="1169",
        math="0", shadow="0"
    )
    root = SubElement(graph, "root")
    SubElement(root, "mxCell", id="0")
    SubElement(root, "mxCell", id="1", parent="0")

    phases = data.get("phases", [])
    want_legend = bool(data.get("legend", False))

    id_map = {}              # id logico -> id XML
    elem_registry = {}       # id logico -> dict {etype, actor, phase_idx, center_x, lane_xml_id}
    phase_layouts = []       # per phase: {xml_id, x, y, w, h, pain_area_y, lanes_by_actor}
    deferred_edges = []
    deferred_pain_links = []

    # ---- Primo passo: disegna le fasi con lane e elementi del flusso ---------
    current_y = PHASE_Y0

    for phase_idx, phase in enumerate(phases):
        phase_name = phase.get("name") or "FASE {}".format(phase_idx + 1)
        actors = phase.get("actors", [])
        elements = phase.get("elements", []) or []
        connections = phase.get("connections", []) or []

        n_lanes = len(actors)
        p_w = phase_total_width(elements)
        p_h = phase_height(n_lanes)

        phase_xml_id = new_id()
        phase_cell = SubElement(root, "mxCell",
            id=phase_xml_id, value=safe_value(phase_name),
            style=PHASE_STYLE, vertex="1", parent="1"
        )
        SubElement(phase_cell, "mxGeometry",
            x=str(PHASE_X), y=str(current_y),
            width=str(p_w), height=str(p_h),
            **{"as": "geometry"}
        )

        lanes_by_actor = {}
        for i, actor in enumerate(actors):
            lane_xml_id = new_id()
            lanes_by_actor[actor] = lane_xml_id
            lane_cell = SubElement(root, "mxCell",
                id=lane_xml_id, value=safe_value(actor),
                style=lane_style(i), vertex="1", parent=phase_xml_id
            )
            SubElement(lane_cell, "mxGeometry",
                x=str(PHASE_LABEL_W),
                y=str(i * LANE_H),
                width=str(p_w - PHASE_LABEL_W),
                height=str(LANE_H),
                **{"as": "geometry"}
            )

        # Calcola colonne per gli elementi di questa fase
        cols = assign_columns(elements)

        for elem in elements:
            eid = elem["id"]
            raw_type = elem.get("type", "action")
            etype = canonical_type(raw_type)

            if etype in OFF_LANE_TYPES:
                # pain point / info panel: si disegnano dopo la fase
                elem_registry[eid] = {
                    "etype": etype, "raw_type": raw_type,
                    "actor": elem.get("actor"),
                    "phase_idx": phase_idx, "col": None,
                    "target": elem.get("target"),
                    "label": elem.get("label", ""),
                }
                continue

            actor = elem.get("actor") or (actors[0] if actors else None)
            if actor not in lanes_by_actor:
                # se l'attore non esiste, fallback alla prima lane
                actor = actors[0] if actors else None
            lane_parent = lanes_by_actor.get(actor, phase_xml_id)

            col = cols.get(eid, 0) or 0
            cx = col_to_center_x(col)

            xml_id = new_id()
            id_map[eid] = xml_id

            if etype == "start":
                draw_start(root, xml_id, lane_parent, elem.get("label", ""), cx)
            elif etype == "end":
                draw_end(root, xml_id, lane_parent, elem.get("label", ""), cx)
            elif etype in ("action", "action_auto", "action_new", "action_deleted"):
                variant = {
                    "action": "manual",
                    "action_auto": "auto",
                    "action_new": "new",
                    "action_deleted": "deleted",
                }[etype]
                draw_task(root, xml_id, lane_parent, elem.get("label", ""), cx, variant)
                # Tool label sotto
                tool = elem.get("tool")
                if tool:
                    draw_tool_label(root, lane_parent, cx, tool)
            elif etype == "gateway_xor":
                draw_gateway(root, xml_id, lane_parent, elem.get("label", ""), cx, "xor")
            elif etype == "gateway_and":
                draw_gateway(root, xml_id, lane_parent, elem.get("label", ""), cx, "and")
            elif etype == "gateway_or":
                draw_gateway(root, xml_id, lane_parent, elem.get("label", ""), cx, "or")
            elif etype == "link_out":
                draw_link_event(root, xml_id, lane_parent,
                                elem.get("link_label", elem.get("label", "A")),
                                cx, "out")
            elif etype == "link_in":
                draw_link_event(root, xml_id, lane_parent,
                                elem.get("link_label", elem.get("label", "A")),
                                cx, "in")
            else:
                # fallback: disegna come task
                draw_task(root, xml_id, lane_parent, elem.get("label", ""), cx, "manual")

            elem_registry[eid] = {
                "etype": etype, "raw_type": raw_type,
                "actor": actor, "phase_idx": phase_idx,
                "lane_idx": actors.index(actor) if actor in actors else 0,
                "col": col, "center_x": cx,
                "lane_xml_id": lane_parent,
                "phase_xml_id": phase_xml_id,
            }

        # Area pain point sotto questa fase
        pain_area_y = current_y + p_h + PAIN_V_GAP

        # Conta i pain point di questa fase per calcolare altezza area
        # (se non entrano in una riga, si distribuiscono su piu righe)
        pain_of_phase = [
            e for e in elements
            if canonical_type(e.get("type", "")) == "pain_point"
        ]
        pain_rows = pain_rows_needed(len(pain_of_phase), p_w)

        # Area pannelli informativi: sotto la banda pain point
        info_of_phase = [
            e for e in elements
            if canonical_type(e.get("type", "")) == "info_panel"
        ]
        info_area_y = (pain_area_y + pain_rows * PAIN_ROW_H
                       + (INFO_V_GAP if info_of_phase else 0))

        phase_layouts.append({
            "xml_id": phase_xml_id,
            "x": PHASE_X, "y": current_y,
            "w": p_w, "h": p_h,
            "pain_area_y": pain_area_y,
            "info_area_y": info_area_y,
            "lanes_by_actor": lanes_by_actor,
            "n_pain": len(pain_of_phase),
            "n_info": len(info_of_phase),
        })

        # Accumula connessioni
        for conn in connections:
            deferred_edges.append({**conn, "phase_xml_id": phase_xml_id,
                                   "lanes_by_actor": lanes_by_actor})

        # Sposta y: include la banda pain point e quella dei pannelli informativi
        info_rows = 1 if info_of_phase else 0
        current_y = info_area_y + info_rows * INFO_ROW_H + PHASE_V_GAP

    # ---- Secondo passo: disegna pain point (distribuiti sotto le fasi) ------
    # Per ogni fase, raccolgo i pain point, li ordino per posizione target e li
    # distribuisco nell'area sotto il phase container senza sovrapposizioni,
    # andando a capo su una nuova riga quando la larghezza non basta.
    # La numerazione e GLOBALE su tutto il diagramma, non riparte per fase.
    pain_counter = 0
    for phase_idx, phase in enumerate(phases):
        layout = phase_layouts[phase_idx]
        pain_area_y = layout["pain_area_y"]
        phase_x = layout["x"]
        phase_w = layout["w"]

        pain_points = [
            e for e in phase.get("elements", []) or []
            if canonical_type(e.get("type", "")) == "pain_point"
        ]

        if not pain_points:
            continue

        # Ordina per x del target (se esiste), altrimenti per ordine
        def target_x(pp):
            tgt = pp.get("target")
            if tgt and tgt in elem_registry:
                reg = elem_registry[tgt]
                if reg.get("center_x") is not None:
                    # x assoluta: phase x + striscia titolo fase + x nel contenuto
                    return phase_x + PHASE_LABEL_W + reg["center_x"]
            # fallback: prima colonna
            return phase_x + PHASE_LABEL_W + START_X + COL_W // 2

        pain_sorted = sorted(pain_points, key=target_x)

        per_row = pain_per_row(phase_w)
        min_gap = PAIN_W + PAIN_H_GAP
        min_x = phase_x + PHASE_LABEL_W
        max_x = phase_x + phase_w - PAIN_W

        for row_start in range(0, len(pain_sorted), per_row):
            row = row_start // per_row
            row_y = pain_area_y + row * PAIN_ROW_H
            row_items = pain_sorted[row_start:row_start + per_row]

            # Posizione desiderata: centrata sul target, dentro i margini.
            xs = [max(min_x, min(max_x, target_x(pp) - PAIN_W // 2))
                  for pp in row_items]
            # Doppia passata: prima spingo a destra chi si sovrappone al
            # precedente, poi rientro da destra se ho superato il margine.
            # La capacita per riga garantisce che il risultato non si
            # sovrapponga mai.
            for i in range(1, len(xs)):
                xs[i] = max(xs[i], xs[i - 1] + min_gap)
            if xs and xs[-1] > max_x:
                xs[-1] = max_x
                for i in range(len(xs) - 2, -1, -1):
                    xs[i] = min(xs[i], xs[i + 1] - min_gap)

            for i, (pp, px) in enumerate(zip(row_items, xs)):
                pid = pp["id"]
                label = pp.get("label", "")
                pain_counter += 1
                # Auto-numerazione se la label non contiene gia "PAIN POINT"
                if "PAIN POINT" not in str(label).upper():
                    idx = pain_counter
                    if "\n" in label:
                        first, rest = label.split("\n", 1)
                        label = "(!) PAIN POINT {}: {}\n{}".format(idx, first, rest)
                    else:
                        label = "(!) PAIN POINT {}: {}".format(idx, label)

                xml_id = new_id()
                id_map[pid] = xml_id
                draw_pain_point(root, xml_id, label, px, row_y)

                # Linea tratteggiata verso il target se specificato
                tgt = pp.get("target")
                if tgt and tgt in id_map:
                    deferred_pain_links.append((xml_id, id_map[tgt]))

    # ---- Pass pannelli informativi (banda sotto i pain point) --------------
    for phase_idx, phase in enumerate(phases):
        layout = phase_layouts[phase_idx]
        info_panels = [
            e for e in phase.get("elements", []) or []
            if canonical_type(e.get("type", "")) == "info_panel"
        ]
        if not info_panels:
            continue
        ix = layout["x"] + PHASE_LABEL_W + START_X
        iy = layout["info_area_y"]
        for ip in info_panels:
            xml_id = new_id()
            id_map[ip["id"]] = xml_id
            draw_info_panel(root, xml_id, ip.get("label", ""), ix, iy)
            ix += INFO_W + 20

    # ---- Terzo passo: disegna le frecce del flusso --------------------------
    # Pre-pass: pianifica ogni edge (ritorno, lato di uscita, lato di
    # ingresso). Le uscite di uno stesso gateway ricevono LATI UNICI cosi due
    # frecce non corrono mai sovrapposte sullo stesso corridoio; la preferenza
    # e geometrica: colonna adiacente stessa lane -> destra, lane sopra/sotto
    # -> alto/basso, salto di colonne nella stessa lane -> scavalco dall'alto.
    skipped_connections = []
    edge_plans = []
    gateway_sides_used = {}  # from_id -> set di lati gia occupati

    SIDE_FALLBACK = {
        "right":  ["right", "top", "bottom"],
        "top":    ["top", "right", "bottom"],
        "bottom": ["bottom", "right", "top"],
    }

    for conn in deferred_edges:
        from_id = conn.get("from")
        to_id = conn.get("to")
        label = conn.get("label", "")
        color = conn.get("color", "#000000")
        phase_xml_id = conn["phase_xml_id"]
        lanes_by_actor = conn["lanes_by_actor"]

        from_xml = id_map.get(from_id)
        to_xml = id_map.get(to_id)
        if not from_xml or not to_xml:
            skipped_connections.append((from_id, to_id))
            continue

        from_reg = elem_registry.get(from_id, {})
        to_reg = elem_registry.get(to_id, {})
        from_actor = from_reg.get("actor")
        to_actor = to_reg.get("actor")

        # Parent dell'edge: stessa lane -> lane; altrimenti phase
        if (from_actor and to_actor and from_actor == to_actor
                and from_actor in lanes_by_actor):
            edge_parent = lanes_by_actor[from_actor]
        elif from_reg.get("phase_idx") != to_reg.get("phase_idx"):
            edge_parent = "1"
        else:
            edge_parent = phase_xml_id

        # Euristica "ritorno": freccia "No" o esplicitamente marcata
        label_lower = (label or "").strip().lower()
        is_return = (
            conn.get("return", False)
            or label_lower in {"no"}
            and (to_reg.get("col") is not None and from_reg.get("col") is not None
                 and to_reg["col"] < from_reg["col"])
        )

        same_phase = from_reg.get("phase_idx") == to_reg.get("phase_idx")
        same_lane = (same_phase
                     and from_reg.get("lane_idx") == to_reg.get("lane_idx"))
        col_gap = None
        if from_reg.get("col") is not None and to_reg.get("col") is not None:
            col_gap = to_reg["col"] - from_reg["col"]

        from_is_gateway = str(from_reg.get("etype", "")).startswith("gateway")
        if from_is_gateway and is_return:
            # I ritorni escono dal vertice alto: prenota subito quel lato,
            # qualunque sia l'ordine delle connessioni nel JSON.
            gateway_sides_used.setdefault(from_id, set()).add("top")

        edge_plans.append({
            "from_id": from_id, "from_xml": from_xml, "to_xml": to_xml,
            "parent": edge_parent, "label": label, "color": color,
            "is_return": is_return, "from_is_gateway": from_is_gateway,
            "same_phase": same_phase, "same_lane": same_lane,
            "col_gap": col_gap, "from_reg": from_reg, "to_reg": to_reg,
        })

    for plan in edge_plans:
        from_reg, to_reg = plan["from_reg"], plan["to_reg"]
        exit_hint = None
        entry_hint = None

        if plan["from_is_gateway"] and not plan["is_return"]:
            # Lato preferito in base alla geometria della destinazione
            if plan["same_lane"] and plan["col_gap"] == 1:
                pref = "right"
            elif (plan["same_lane"] and plan["col_gap"] is not None
                  and plan["col_gap"] >= 2):
                pref = "top"      # scavalca gli elementi intermedi dall'alto
            elif (plan["same_phase"] and not plan["same_lane"]
                  and to_reg.get("lane_idx") is not None
                  and from_reg.get("lane_idx") is not None):
                pref = ("top" if to_reg["lane_idx"] < from_reg["lane_idx"]
                        else "bottom")
            else:
                pref = "right"
            used = gateway_sides_used.setdefault(plan["from_id"], set())
            exit_hint = next((s for s in SIDE_FALLBACK[pref] if s not in used),
                             pref)
            used.add(exit_hint)
            if (exit_hint == "top" and plan["same_lane"]
                    and plan["col_gap"] and plan["col_gap"] >= 2):
                entry_hint = "top"
        elif (not plan["is_return"] and plan["same_lane"]
              and plan["col_gap"] is not None and plan["col_gap"] >= 2):
            # Anche fuori dai gateway: un salto di colonne nella stessa lane
            # scavalca dall'alto invece di attraversare gli elementi in mezzo.
            exit_hint = "top"
            entry_hint = "top"

        # Ingresso nei gateway da una lane diversa: se la colonna e adiacente
        # entra da sinistra; se salta colonne (che potrebbero contenere
        # elementi) entra dal lato della lane di provenienza, cosi il tratto
        # orizzontale corre nella lane di origine e non attraversa nulla.
        if (entry_hint is None
                and str(to_reg.get("etype", "")).startswith("gateway")
                and plan["col_gap"] is not None and plan["col_gap"] > 0
                and from_reg.get("lane_idx") != to_reg.get("lane_idx")
                and from_reg.get("lane_idx") is not None
                and to_reg.get("lane_idx") is not None):
            if plan["col_gap"] == 1:
                entry_hint = "left"
            else:
                entry_hint = ("bottom"
                              if from_reg["lane_idx"] > to_reg["lane_idx"]
                              else "top")

        draw_edge(root, plan["from_xml"], plan["to_xml"], plan["parent"],
                  plan["label"], plan["color"], plan["is_return"],
                  exit_hint, entry_hint)

    # ---- Quarto passo: linee tratteggiate pain -> task ----------------------
    for pain_xml, task_xml in deferred_pain_links:
        draw_pain_link(root, pain_xml, task_xml)

    # ---- Legenda opzionale --------------------------------------------------
    if want_legend:
        draw_legend(root, current_y + LEGEND_V_GAP)

    return graph, skipped_connections

# =============================================================================
# Legenda
# =============================================================================

def draw_legend(root, y):
    # Contenitore legenda
    lid = new_id()
    cell = SubElement(root, "mxCell",
        id=lid, value="LEGENDA",
        style=("swimlane;startSize=22;fillColor=#F5F5F5;strokeColor=#666666;"
               "fontStyle=1;fontSize=10;collapsible=0;html=1;"),
        vertex="1", parent="1"
    )
    SubElement(cell, "mxGeometry",
        x=str(PHASE_X), y=str(y), width="760", height="90",
        **{"as": "geometry"}
    )

    # Elementi della legenda
    items = [
        ("START", 12, 32, 40, 40,
         "ellipse;aspect=fixed;fillColor=#92D050;strokeColor=#66A30E;fontSize=8;fontStyle=1;"),
        ("END", 65, 32, 40, 40,
         "ellipse;aspect=fixed;fillColor=#FF9999;strokeColor=#CC0000;strokeWidth=3;fontSize=8;fontStyle=1;"),
        ("Task", 120, 36, 90, 32,
         "rounded=1;fillColor=#FFFFFF;strokeColor=#000000;fontSize=9;"),
        ("Gateway (X)", 225, 32, 50, 40,
         "rhombus;fillColor=#FFE699;strokeColor=#d6b656;fontSize=8;"),
        ("A", 295, 40, 24, 24,
         "ellipse;aspect=fixed;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=9;fontStyle=1;"),
        ("Link event", 325, 40, 70, 24,
         "text;fontSize=8;align=left;"),
        ("(!) Pain point", 410, 36, 100, 32,
         "rounded=1;fillColor=#FFD7D7;strokeColor=#C00000;fontColor=#C00000;fontStyle=1;fontSize=8;strokeWidth=2;"),
        ("Info / Variante", 525, 36, 110, 32,
         "rounded=1;fillColor=#DEEAF1;strokeColor=#4472C4;fontColor=#1F3864;fontStyle=1;fontSize=8;strokeWidth=2;"),
    ]
    for lbl, lx, ly, lw, lh, lstyle in items:
        iid = new_id()
        ic = SubElement(root, "mxCell",
            id=iid, value=safe_value(lbl), style=lstyle,
            vertex="1", parent=lid
        )
        SubElement(ic, "mxGeometry",
            x=str(lx), y=str(ly), width=str(lw), height=str(lh),
            **{"as": "geometry"}
        )

# =============================================================================
# Entry point
# =============================================================================

def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\-. ]", "", str(name), flags=re.UNICODE)
    name = name.strip().replace(" ", "_").lower()
    return name or "processo"


def load_input(path: str):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERRORE: file non trovato: {}".format(path), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print("ERRORE: JSON non valido in {} (riga {}, colonna {}): {}".format(
            path, e.lineno, e.colno, e.msg), file=sys.stderr)
        print("Suggerimento: controlla virgole mancanti/di troppo, parentesi e "
              "virgolette doppie (il JSON non accetta apici singoli).", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print("ERRORE: impossibile leggere {}: {}".format(path, e), file=sys.stderr)
        sys.exit(1)


def print_report(rep: ValidationReport):
    for w in rep.warnings:
        print("AVVISO: {}".format(w), file=sys.stderr)
    for e in rep.errors:
        print("ERRORE: {}".format(e), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Genera un file draw.io (.drawio) in stile Process Builder "
                    "(swimlane ibrido BPMN) da un JSON descrittivo.",
        epilog="Schema del JSON di input: references/drawio-xml-guide.md",
    )
    parser.add_argument("input", help="file JSON di input")
    parser.add_argument("output", nargs="?", default=None,
                        help="file .drawio di output (default: dal titolo nel JSON)")
    parser.add_argument("--validate", action="store_true",
                        help="valida soltanto il JSON senza generare il file")
    parser.add_argument("--strict", action="store_true",
                        help="tratta anche gli avvisi come errori bloccanti")
    parser.add_argument("--version", action="version",
                        version="%(prog)s {}".format(__version__))
    args = parser.parse_args()

    data = load_input(args.input)

    rep = validate(data)
    print_report(rep)

    if not rep.ok or (args.strict and rep.warnings):
        n_err = len(rep.errors) + (len(rep.warnings) if args.strict else 0)
        print("\nValidazione fallita: {} problema/i da correggere nel JSON. "
              "Nessun file generato.".format(n_err), file=sys.stderr)
        sys.exit(1)

    if args.validate:
        print("Validazione OK: {} ({} avvisi).".format(
            args.input, len(rep.warnings)))
        sys.exit(0)

    output_path = args.output
    if not output_path:
        title = sanitize_filename(data.get("title", "processo"))
        output_path = "{}.drawio".format(title)

    graph, skipped = build_graph(data)
    xml_str = xml_pretty(graph)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
    except OSError as e:
        print("ERRORE: impossibile scrivere {}: {}".format(output_path, e),
              file=sys.stderr)
        sys.exit(1)

    for frm, to in skipped:
        print('AVVISO: connessione saltata ("{}" -> "{}"): id non risolto.'.format(
            frm, to), file=sys.stderr)

    # Riepilogo a stdout
    fasi = len(data.get("phases", []))
    tot = sum(len(p.get("elements", []) or []) for p in data.get("phases", []))
    pain = sum(
        sum(1 for e in (p.get("elements", []) or [])
            if isinstance(e, dict) and e.get("type") == "pain_point")
        for p in data.get("phases", [])
    )
    info = sum(
        sum(1 for e in (p.get("elements", []) or [])
            if isinstance(e, dict) and e.get("type") == "info_panel")
        for p in data.get("phases", [])
    )
    print("File draw.io generato: {}".format(output_path))
    print("  Fasi: {} | Elementi: {} | Pain point: {} | Info panel: {} | Legenda: {}".format(
        fasi, tot, pain, info,
        "si" if data.get("legend", False) else "no"
    ))
    if rep.warnings:
        print("  Avvisi: {} (vedi sopra) — il file e stato generato comunque.".format(
            len(rep.warnings)))


if __name__ == "__main__":
    main()
