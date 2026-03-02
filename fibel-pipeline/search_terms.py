"""
ArchaeoFinder Fibel-Pipeline v3.5.2 — Suchbegriffe & Klassifikation
=====================================================================
ZENTRALE SUCHLISTE: Eine Master-Suchbegriffsliste nach Sprache,
automatisch auf alle Quellen verteilt.

v3.5.2: Bugfix
  - FIX: normalize_epoch(), normalize_material(), detect_fibula_type() hinzugefuegt
  - Diese Funktionen werden von museum_apis.py benoetigt aber fehlten

v3.5.1: Massive Erweiterung
  - 7 Sprachen (NEU: Spanisch)
  - Almgren-Klassifikation komplett
  - Perioden-Kombinationen
  - Regionale Varianten
  - Funktions- und Kontextbegriffe
"""

# =============================================================================
# MASTER-SUCHLISTE — EINE LISTE FUER ALLE QUELLEN
# =============================================================================

MASTER_TERMS = {
    # ─── DEUTSCH (Hauptsprache: DDB, museum-digital, ARACHNE) ───
    "de": [
        # Grundbegriffe
        "Fibel", "Fibel Bronze", "Fibel Eisen", "Fibel Silber", "Fibel Gold",
        "Gewandnadel", "Gewandspange", "Brosche antik", "Mantelschliesse",
        "Gewandfibel", "Trachtfibel", "Schmuckfibel",
        # ── NEU: Grundbegriffe ──
        "Fibula", "Heftel", "Fuerspan", "Fibel Kupferlegierung",
        "Fibel Buntmetall", "Fibel Messing", "Fibel Email",
        "Fibel Granat", "Fibel Almandin", "Fibel Cloisonne",
        "Fibel Niello", "Fibel vergoldet", "Fibel versilbert",
        "Fibel Zinn", "Fibel Blei", "Fibel Elektron",

        # Almgren-Klassifikation (Hauptgruppen)
        "Bogenfibel", "Kniefibel", "Armbrustfibel",
        "Scheibenfibel", "Buegelfibel", "Ringfibel",
        "Spiralfibel", "Hakenfibel", "Plattenfibel",
        "Certosafibel", "Nauheimer Fibel", "Drahtfibel",

        # Spezialformen
        "Zwiebelknopffibel", "Kreuzfibel", "Tierfibel",
        "Gleicharmige Fibel", "Emailfibel", "Distelfibel",
        "Huelsenspiralfibel", "Paukenfibel",
        "Schlangenfibel", "Brillenfibel", "Fibel Omega",
        "Kragenfibel", "Stuetzarmfibel", "Rosettenfibel",
        "Dosenfibel", "Sternfibel", "Radfibel",
        "Vogelfibel", "Pferdefibel", "Entenfibel",
        "Maskenfibel", "S-Fibel", "Blechfibel",
        "Tutulusfibel", "Fibel mit Fussknopf",
        "Fibel mit umgeschlagenem Fuss",
        "Eingliedrige Fibel", "Zweigliedrige Fibel",
        "Aucissafibel", "Huelsencharnierfibel",
        "Backenscharnierfibel", "Langton-Down-Fibel",
        "Kraftig profilierte Fibel", "Augenfibel",
        "Scharnierfibel", "Rollenkappenfibel",
        "Fibel Almgren", "Sprossenfibel",
        # ── NEU: Spezialformen ──
        "Omegafibel", "Pressblechfibel", "Filigranfibel",
        "Kerbschnittfibel", "Cloisonnefibel",
        "Almandinscheibenfibel", "Vogelkopffibel",
        "Pferdchenfibel", "S-foermige Fibel",
        "Prachtfibel", "Halbkreisfibel", "Peltafibel",
        "Raupenfibel", "Doppelknopffibel",
        "Stuetzbalken-Fibel", "Dreisprossenfibel",
        "Viersprossenfibel", "Fuenfknopffibel",
        "Buegelfibel halbrunde Kopfplatte",
        "Buegelfibel rautenfoermige Fussplatte",
        "Mittellatene-Fibel", "Spaetlatene-Fibel",
        "Fruehlatenefibel", "Armbrust-Scharnierfibel",
        "Fibel Typ Jezerine", "Fibel Typ Misano",
        "Fibel Typ Benningen", "Fibel Typ Riha",
        "Fibel Typ Ettlinger", "Fibel Typ Feugere",
        "Fibel Typ Boehme", "Fibel Typ Gaspar",
        "Fibel Typ Nijmegen", "Fibel Typ Hod Hill",
        "Fluegelnadel", "Flachbogenfibel",
        "Gabelfibel", "Doppelfibel",
        "Leiterfibel", "Gitterfibel",
        "Hakenkreuzfibel", "Swastikafibel",
        "Tierkopffibel", "Loewenfibel",
        "Hirschfibel", "Fischfibel",
        "Hasenfibel", "Greiffibel",
        "Adlerfibel", "Schluesselnadel",
        "Rautenfibel", "Rippenfibel",
        "Scheibennadel", "Hutnadel antik",
        "Fibel Typ Almgren Gruppe", "Fibel Almgren Serie",
        "Fibel Almgren I", "Fibel Almgren II",
        "Fibel Almgren III", "Fibel Almgren IV",
        "Fibel Almgren V", "Fibel Almgren VI",
        "Fibel Almgren VII",

        # Perioden-Kombinationen
        "Fibel roemisch", "Fibel Latene", "Fibel Hallstatt",
        "Fibel Voelkerwanderungszeit", "Fibel Merowingerzeit",
        "Fibel karolingisch", "Fibel Wikingerzeit",
        "Fibel fruehe Eisenzeit", "Fibel spaete Eisenzeit",
        "Fibel Bronzezeit", "Fibel Mittelalter",
        "Fibel roemische Kaiserzeit", "Fibel Spaetantike",
        "Fibel fruehes Mittelalter", "Fibel germanisch",
        "Fibel keltisch", "Fibel provinzialroemisch",
        # ── NEU: Perioden ──
        "Fibel augusteisch", "Fibel tiberisch",
        "Fibel claudisch", "Fibel flavisch",
        "Fibel trajanisch", "Fibel hadrianisch",
        "Fibel severisch", "Fibel konstantinisch",
        "Fibel 1. Jahrhundert", "Fibel 2. Jahrhundert",
        "Fibel 3. Jahrhundert", "Fibel 4. Jahrhundert",
        "Fibel 5. Jahrhundert", "Fibel 6. Jahrhundert",
        "Fibel 7. Jahrhundert", "Fibel 8. Jahrhundert",
        "Fibel Spaetlatene", "Fibel Mittellatene",
        "Fibel Fruehlatene",
        "Fibel galloroemisch", "Fibel ostgotisch",
        "Fibel langobardisch", "Fibel westgotisch",
        "Fibel angelsaechsisch", "Fibel awarisch",
        "Fibel ottonisch", "Fibel slawisch",
        "Fibel hunnisch", "Fibel skythisch",
        "Fibel burgundisch", "Fibel vandalisch",

        # Regionale Varianten
        "Fibel Rheinland", "Fibel Noricum", "Fibel Pannonien",
        "Fibel Raetien", "Fibel Germanien", "Fibel Gallien",
        "Fibel Alamannen", "Fibel Franken", "Fibel Sachsen",
        "Fibel Thueringen", "Fibel Bajuwaren",
        "Fibel Reihengrab", "Fibel Grabfund",
        # ── NEU: Regionale Varianten ──
        "Fibel Moesien", "Fibel Dakien", "Fibel Britannia",
        "Fibel Hispania", "Fibel Dalmatien", "Fibel Illyricum",
        "Fibel Limes", "Fibel Limesgebiet",
        "Fibel Trier", "Fibel Koeln", "Fibel Mainz",
        "Fibel Augsburg", "Fibel Regensburg", "Fibel Carnuntum",
        "Fibel Vindobona", "Fibel Aquileia",
        "Fibel Schwarzwald", "Fibel Schwaben",
        "Fibel Hessen", "Fibel Pfalz",
        "Fibel Niedersachsen", "Fibel Schleswig-Holstein",
        "Fibel Brandenburg", "Fibel Mecklenburg",
        "Fibel Eifel", "Fibel Hunsrueck-Eifel",

        # Kontext
        "Fibel archaeologisch", "Fibel Fundort",
        "Fibel Ausgrabung", "Fibel Grabbeigabe",
        "Fibel Schatzfund", "Fibel Hortfund",
        "Fibel Metalldetektor", "Fibel Lesefund",
        "Tracht roemisch", "Tracht germanisch",
        "Trachtbestandteil antik",
        "Gewandschmuck", "Kleidungszubehoer roemisch",
        # ── NEU: Kontext ──
        "Fibel Siedlungsfund", "Fibel Opferfund",
        "Fibel Votivfund", "Fibel Heiligtum",
        "Fibel Brandgrab", "Fibel Koerpergrab",
        "Fibel Beigabe", "Fibel Werkstattfund",
        "Fibel Produktionsabfall", "Fibel Halbfabrikat",
        "Fibel Gussform", "Fibel Punze",
        "Fibel Reparatur", "Fibel fragmentiert",
        "Fibel Bruchstueck", "Fibel Nadelrast",
        "Fibel Spiralkonstruktion", "Fibel Sehne",
        "Fibel Nadelhalter", "Fibel Buegel",
        "Fibel Fuss", "Fibel Kopf",
        "Tracht keltisch", "Tracht merowingisch",
        "Tracht alamannisch", "Tracht fraenkisch",
        "Gewandschliessung", "Mantelschliessung",
        "Kleiderverschluss antik",
        "Fibel Kastell", "Fibel Vicus",
        "Fibel Villa rustica", "Fibel Gutshof roemisch",
    ],

    # ─── ENGLISCH (Met, Cleveland, V&A, PAS, BM, etc.) ───
    "en": [
        # Grundbegriffe
        "fibula", "brooch", "ancient fibula", "ancient brooch",
        "clasp ancient", "pin brooch ancient",
        "dress fastener", "cloak pin",
        # ── NEU: Grundbegriffe ──
        "fibulae", "brooches", "ancient pin",
        "costume pin", "mantle pin", "garment fastener",
        "dress pin", "clothes fastener ancient",
        "catch plate", "pin rest", "bow brooch",

        # Roemisch
        "Roman fibula", "Roman brooch", "Roman dress pin",
        "crossbow brooch", "crossbow fibula",
        "plate brooch Roman", "disc brooch Roman",
        "knee brooch", "knee fibula",
        "aucissa brooch", "aucissa fibula",
        "trumpet brooch", "trumpet fibula",
        "fantail brooch", "fantail fibula",
        "headstud brooch", "head-stud brooch",
        "dragonesque brooch", "dolphin brooch",
        "hod hill brooch", "colchester brooch",
        "colchester derivative", "langton down brooch",
        "thistle brooch", "T-shaped brooch",
        "P-shaped brooch", "tutulus brooch",
        "onion brooch", "hinged brooch Roman",
        "sprung brooch Roman", "bow brooch Roman",
        "plate brooch late Roman",
        "provincial Roman brooch",
        "military brooch Roman",
        # ── NEU: Roemisch ──
        "Polden Hill brooch", "Wroxeter brooch",
        "Aesica brooch", "Backworth brooch",
        "Birdlip brooch", "Battersea brooch",
        "divided bow brooch", "strip bow brooch",
        "flat bow brooch", "wire brooch Roman",
        "ring-and-dot brooch", "enamelled disc brooch",
        "seal box brooch", "lozenge brooch Roman",
        "penannular brooch Roman", "omega brooch",
        "crossbow brooch type 1", "crossbow brooch type 2",
        "crossbow brooch type 3", "crossbow brooch type 4",
        "Zwiebelknopf fibula", "onion-knob fibula",
        "strongly profiled fibula", "eye fibula",
        "Aucissa type fibula", "Hod Hill type",
        "Colchester type", "Colchester two-piece",
        "Langton Down type", "Nauheim derivative",
        "Rosette brooch Roman", "umbonate brooch",
        "pelta brooch", "lunate brooch",
        "wheel brooch", "swastika brooch Roman",
        "animal brooch Roman", "horse brooch Roman",
        "horse-and-rider brooch", "hare brooch",
        "fly brooch", "lion brooch Roman",
        "dolphin fibula", "duck brooch Roman",
        "cockerel brooch", "eagle fibula Roman",
        "foot brooch Roman", "shoe brooch Roman",
        "amphora brooch", "axe brooch Roman",
        "crossbow fibula Keller", "crossbow fibula Pröttel",
        "late Roman military brooch",
        "chip-carved brooch", "Kerbschnitt brooch",
        "Romano-British brooch",
        "brooch Richborough type",
        "brooch Nauheim type",

        # Keltisch / Eisenzeit
        "La Tene fibula", "La Tene brooch",
        "Hallstatt fibula", "Hallstatt brooch",
        "Iron Age brooch", "Iron Age fibula",
        "Celtic fibula", "Celtic brooch",
        "Certosa fibula", "bow fibula",
        "Nauheim fibula", "Nauheim brooch",
        "involuted brooch", "spring brooch",
        "safety pin fibula", "serpentine fibula",
        "leech fibula",
        # ── NEU: Keltisch / Eisenzeit ──
        "early La Tene fibula", "middle La Tene fibula",
        "late La Tene fibula", "La Tene I fibula",
        "La Tene II fibula", "La Tene III fibula",
        "La Tene D fibula", "La Tene C fibula",
        "La Tene B fibula",
        "Duchcov fibula", "Marzabotto fibula",
        "Munsingen fibula", "Dux fibula",
        "flat-bowed fibula Iron Age",
        "bilateral spring fibula", "unilateral spring fibula",
        "catch plate fibula", "disc foot fibula",
        "turned-up foot fibula",
        "proto-La Tene fibula",
        "Hallstatt C fibula", "Hallstatt D fibula",
        "arc fibula", "boat fibula",
        "dragon fibula", "kettle drum fibula",
        "spectacle brooch", "eyeglass fibula",

        # Angelsaechsisch / Fruehmittelalter
        "Anglo-Saxon brooch", "Anglo-Saxon fibula",
        "annular brooch", "penannular brooch",
        "saucer brooch", "cruciform brooch",
        "long brooch", "small-long brooch",
        "applied brooch", "equal-armed brooch",
        "square-headed brooch", "great square-headed brooch",
        "Merovingian brooch", "Merovingian fibula",
        "Frankish brooch", "Migration Period brooch",
        "bird brooch early medieval",
        "zoomorphic brooch",
        # ── NEU: Angelsaechsisch / Fruehmittelalter ──
        "supporting-arm brooch", "radiate-headed brooch",
        "button brooch", "quoit brooch",
        "composite disc brooch", "keystone brooch",
        "Kentish disc brooch", "Kentish brooch",
        "garnet disc brooch", "cloisonne disc brooch",
        "Style I brooch", "Style II brooch",
        "Salin Style I", "Salin Style II",
        "chip-carved equal-armed brooch",
        "bird-headed brooch", "horse-shaped brooch",
        "serpent brooch early medieval",
        "Lombard brooch", "Lombard fibula",
        "Visigothic brooch", "Visigothic fibula",
        "Ostrogothic brooch", "Ostrogothic fibula",
        "Gepid brooch", "Thuringian brooch",
        "Alamannic brooch", "Burgundian brooch",
        "bow brooch Migration Period",
        "S-shaped brooch", "bird-shaped fibula",
        "five-knob brooch", "three-knob brooch",
        "pair of brooches", "matching brooches",
        "grave goods brooch", "burial brooch",

        # Wikinger / Skandinavisch
        "Viking brooch", "Viking fibula",
        "tortoise brooch", "oval brooch Viking",
        "trefoil brooch", "Viking ring brooch",
        "urnes brooch", "borre brooch",
        "jelling brooch", "ringerike brooch",
        "Norse brooch",
        # ── NEU: Wikinger / Skandinavisch ──
        "box brooch Viking", "domed brooch Viking",
        "equal-armed brooch Viking",
        "disc brooch Viking", "bird brooch Viking",
        "animal-headed brooch Viking",
        "Vendel period brooch", "Gotlandic brooch",
        "Baltic brooch", "Slavic brooch",
        "penannular brooch Viking",
        "thistle brooch Viking",
        "terminal ring brooch", "bramble brooch",
        "Borre style", "Jelling style",
        "Mammen style brooch", "Ringerike style",
        "Urnes style",

        # Byzantinisch
        "Byzantine brooch", "Byzantine fibula",
        "Byzantine crossbow", "late Roman brooch",
        # ── NEU: Byzantinisch ──
        "Byzantine disc brooch", "Byzantine ring brooch",
        "Byzantine cloisonne", "Byzantine enamel brooch",
        "Coptic brooch", "late antique brooch",
        "late antique fibula",

        # Griechisch / Etruskisch
        "Etruscan fibula", "Greek fibula",
        "Greek brooch", "Italic fibula",
        "Boeotian fibula", "spectacle fibula",
        "Villanova fibula", "arched fibula",
        "geometric fibula", "archaic fibula Greek",
        # ── NEU: Griechisch / Etruskisch ──
        "Mycenaean fibula", "Sub-Mycenaean fibula",
        "Protogeometric fibula", "Geometric period fibula",
        "Orientalizing fibula", "Archaic period fibula",
        "Italic bow fibula", "Italic disc fibula",
        "Etruscan gold fibula", "granulated fibula",
        "Praeneste fibula", "leech-shaped fibula",
        "navicella fibula", "sanguisuga fibula",
        "serpentine fibula Italic",
        "Apulian fibula", "Campanian fibula",
        "Sicilian fibula", "Sardinian fibula",
        "Thracian fibula", "Illyrian fibula",
        "Phrygian fibula", "Anatolian fibula",
        "Near Eastern fibula",

        # Material-Kombinationen
        "fibula gold", "fibula silver", "fibula bronze", "fibula iron",
        "brooch gold ancient", "brooch silver ancient",
        "brooch bronze ancient", "brooch copper alloy",
        "brooch enamel", "enamelled brooch", "cloisonne brooch",
        "brooch gilt", "brooch gilded",
        "brooch garnet", "garnet cloisonne brooch",
        "brooch niello", "silver gilt brooch",
        # ── NEU: Materialien ──
        "brooch gold filigree", "brooch granulation",
        "brooch glass inlay", "brooch millefiori",
        "brooch coral inlay", "brooch amber inlay",
        "brooch bone", "brooch ivory",
        "brooch jet", "brooch glass paste",
        "champlevé brooch", "tinned brooch",
        "silvered brooch", "lead alloy brooch",
        "pewter brooch", "electrum brooch",

        # Perioden
        "brooch Iron Age", "brooch Bronze Age",
        "brooch Roman period", "brooch early medieval",
        "brooch late Roman", "brooch Migration Period",
        "brooch medieval", "brooch Carolingian",
        "brooch Romanesque",
        "fibula late antique", "fibula Migration",
        # ── NEU: Perioden ──
        "brooch 1st century", "brooch 2nd century",
        "brooch 3rd century", "brooch 4th century",
        "brooch 5th century", "brooch 6th century",
        "brooch 7th century", "brooch 8th century",
        "brooch 9th century", "brooch 10th century",
        "brooch Augustan", "brooch Flavian",
        "brooch Hadrianic", "brooch Severan",
        "brooch Constantinian", "brooch Theodosian",
        "fibula Archaic", "fibula Classical",
        "fibula Hellenistic",

        # Kontext
        "brooch archaeological find",
        "brooch metal detecting", "brooch detector find",
        "brooch hoard", "brooch grave goods",
        "brooch excavation", "dress accessory Roman",
        "dress accessory medieval",
        "personal ornament Roman", "personal ornament medieval",
        "fibula collection museum",
        # ── NEU: Kontext ──
        "brooch votive", "brooch sanctuary",
        "brooch settlement find", "brooch fort find",
        "brooch villa find", "brooch military site",
        "brooch cremation burial", "brooch inhumation",
        "brooch stray find", "brooch chance find",
        "brooch treasure", "brooch Treasure Act",
        "brooch PAS find", "Portable Antiquities brooch",
        "fibula workshop", "fibula mould",
        "fibula production", "fibula trade",
        "costume accessory ancient",
        "personal adornment Roman",
        "personal adornment medieval",
        "dress fitting Roman",
    ],

    # ─── FRANZOESISCH (Europeana, POP France) ───
    "fr": [
        # Grundbegriffe
        "fibule", "broche antique", "agrafe",
        "epingle antique", "attache vetement",
        # ── NEU: Grundbegriffe ──
        "fibules", "epingle", "fermoir antique",
        "attache de manteau", "bijou vestimentaire",

        # Typen
        "fibule romaine", "fibule gauloise",
        "fibule arc", "fibule a ressort",
        "fibule a charniere", "fibule disque",
        "fibule cruciforme", "fibule zoomorphe",
        "fibule emaille", "fibule email",
        "fibule ansate", "fibule annulaire",
        "fibule penannulaire",
        "broche romaine", "broche gauloise",
        "fibule a arbalete", "fibule a genou",
        "fibule a queue de paon",
        "fibule en oignon", "fibule plate",
        # ── NEU: Typen ──
        "fibule a ailettes", "fibule a collerette",
        "fibule a disque", "fibule a plaque",
        "fibule a tete de serpent", "fibule a protubérances",
        "fibule spirale", "fibule a navicella",
        "fibule a sangsue", "fibule serpentiforme",
        "fibule a lunettes", "fibule omega",
        "fibule en arbalete type", "fibule militaire",
        "fibule a arc coudé", "fibule filiform",
        "fibule a pied releve", "fibule a griffe",
        "fibule a cheval", "fibule aviforme",
        "fibule a tete d oiseau", "fibule polylobee",
        "fibule a tete rayonnante", "fibule digitee",
        "broche cloisonnee", "broche filigranee",
        "broche emaillee", "broche champlevee",

        # Perioden
        "fibule La Tene", "fibule Hallstatt",
        "fibule merovingienne", "fibule carolingienne",
        "fibule wisigothe", "fibule franque",
        "fibule gallo-romaine",
        "broche medievale", "broche merovingienne",
        "fibule antiquite tardive",
        "fibule haut Moyen Age",
        # ── NEU: Perioden ──
        "fibule age du fer", "fibule age du bronze",
        "fibule Haut Empire", "fibule Bas Empire",
        "fibule 1er siecle", "fibule 2e siecle",
        "fibule 3e siecle", "fibule 4e siecle",
        "fibule 5e siecle", "fibule 6e siecle",
        "fibule 7e siecle",
        "fibule La Tene ancienne", "fibule La Tene moyenne",
        "fibule La Tene finale",
        "fibule epoque augusteenne",
        "fibule provinciale romaine",
        "fibule burgonde",

        # Material
        "fibule bronze", "fibule fer", "fibule argent", "fibule or",
        "broche email antique", "broche cloisonne",
        "fibule cuivre", "fibule etain",
        # ── NEU: Materialien ──
        "fibule alliage cuivreux", "fibule plomb",
        "fibule laiton", "fibule doree",
        "fibule argentee", "fibule grenat",
        "fibule corail", "fibule verre",
        "fibule pate de verre", "fibule millefiori",
        "fibule filigrane", "fibule granulation",

        # Kontext
        "fibule archeologie", "fibule fouille",
        "fibule sepulture", "fibule tresor",
        "accessoire vestimentaire romain",
        "parure antique", "garniture vestimentaire",
        # ── NEU: Kontext ──
        "fibule depot", "fibule sanctuaire",
        "fibule habitat", "fibule prospection",
        "fibule camp militaire", "fibule villa",
        "fibule necropole", "fibule incineration",
        "fibule inhumation", "fibule offrande",
        "mobilier funeraire fibule",
        "objet metallique gallo-romain",
        "petit mobilier romain",
    ],

    # ─── ITALIENISCH (Europeana) ───
    "it": [
        "fibula", "fibula romana", "spilla romana",
        "fibula etrusca", "fibula villanoviana",
        "fibula arco", "fibula arco semplice",
        "fibula disco", "fibula bronzo", "fibula ferro",
        "fibula argento", "fibula oro",
        "fibula La Tene", "fibula celtica",
        "fibula ad arco", "fibula a balestra",
        "fibula a navicella", "fibula a sanguisuga",
        "fibula serpeggiante", "fibula ad occhiali",
        "spilla antica", "fermaglio romano",
        "fibula longobarda", "fibula bizantina",
        "fibula altomedievale", "fibula paleocristiana",
        "fibula smaltata", "fibula a croce",
        "accessorio abbigliamento romano",
        "fibula a cerniera", "fibula a molla",
        "ornamento personale romano",
        # ── NEU ──
        "fibule", "fibula ad arco serpeggiante",
        "fibula a drago", "fibula ad arco rivestito",
        "fibula tipo Certosa", "fibula tipo Nauheim",
        "fibula a ginocchio", "fibula cruciforme",
        "fibula a cipolla", "fibula a disco",
        "fibula a piastra", "fibula zoomorfa",
        "fibula a cavallo", "fibula a forma di uccello",
        "fibula a occhiali", "fibula a staffa",
        "fibula tardoromana", "fibula tardoantica",
        "fibula gota", "fibula ostrogota",
        "spilla medievale", "fermaglio medievale",
        "fibula rame", "fibula lega rame",
        "fibula smalto", "fibula cloisonne",
        "fibula granata", "fibula dorata",
        "fibula argentata", "fibula filigrana",
        "corredo funerario fibula",
        "necropoli fibula", "scavo fibula",
        "rinvenimento fibula",
        "ornamento personale antico",
        "fibula Prenestina", "fibula laziale",
        "fibula picena", "fibula daunia",
    ],

    # ─── NIEDERLAENDISCH (Rijksmuseum) ───
    "nl": [
        "fibula", "gesp", "mantelspeld",
        "Romeinse fibula", "broche", "sierspeld",
        "mantelspeld Romeins", "fibula brons",
        "gesp middeleeuws", "broche antiek",
        "fibula ijzer", "fibula zilver",
        "mantelgesp", "kledingspeld",
        "fibula Keltisch", "Merovingische fibula",
        "schijffibula", "boogfibula",
        "kruisboogfibula", "ringfibula",
        "draadspeld Romeins", "sierspeld middeleeuws",
        # ── NEU ──
        "fibula goud", "fibula koper",
        "fibula koperlegering", "fibula email",
        "fibula vergulde", "verzilverde fibula",
        "fibula laat-Romeins", "fibula Germaans",
        "fibula Vikingen", "fibula vroeg-middeleeuws",
        "fibula IJzertijd", "fibula Bronstijd",
        "fibula La Tene", "fibula Hallstatt",
        "kniefibula", "plaatvormige fibula",
        "scharnierfibula", "veerfibula",
        "gelijkarmige fibula", "dierenfibula",
        "emaille broche", "cloisonne broche",
        "grafvondst fibula", "opgravingsvondst fibula",
        "detectorvondst fibula", "schatvondst fibula",
        "persoonlijk ornament", "kledingaccessoire Romeins",
        "Frankische fibula", "Saksische fibula",
        "Friese fibula",
    ],

    # ─── SPANISCH (Europeana Spanien) ───
    "es": [
        "fibula", "fibula romana", "broche romano",
        "fibula celtiberica", "fibula iberica",
        "fibula hispana", "fibula bronce",
        "fibula hierro", "fibula plata", "fibula oro",
        "fibula arco", "fibula disco", "fibula anular",
        "fibula penannular", "fibula zoomorfa",
        "fibula visigoda", "fibula La Tene",
        "broche antiguo", "broche medieval",
        "broche visigodo", "imperdible antiguo",
        "pasador vestimenta romano",
        "fibula arqueologia", "fibula excavacion",
        "adorno personal romano",
        # ── NEU ──
        "fibulas", "broche hispanorromano",
        "fibula celtibera", "fibula tipo Aucissa",
        "fibula tipo La Tene", "fibula omega",
        "fibula ballesta", "fibula rodilla",
        "fibula placa", "fibula cruciforme",
        "fibula animalistica", "fibula caballo",
        "fibula serpiente", "fibula espiral",
        "fibula cobre", "fibula aleacion cobre",
        "fibula esmaltada", "fibula dorada",
        "fibula tardorromana", "fibula bajo imperio",
        "fibula alto imperio", "fibula sueva",
        "broche altomedieval", "broche tardoantiguo",
        "ajuar funerario fibula", "necropolis fibula",
        "hallazgo fibula", "tesoro fibula",
        "indumentaria romana", "ornamento personal antiguo",
        "accesorio vestimenta romano",
        "fibula tipo Nauheim", "fibula meseta",
        "fibula peninsular", "fibula lusitana",
    ],

    # ─── SKANDINAVISCH (DiMu, SOCH) ───
    "scandi": [
        # Schwedisch
        "fibula", "draktspenne", "ringspenne",
        "bågfibula", "skivfibula", "spänne", "brosch",
        "dräktspänne", "ringspänne",
        "vikingatida spänne", "bronsålders fibula",
        "järnålderns fibula", "ovala spännbucklor",
        "likarmad spänne", "korsformig spänne",
        "rund spänne", "djurformig spänne",
        "ringspänne medeltida",
        # ── NEU: Schwedisch ──
        "fibulor", "bågspänne", "plattfibula",
        "spiralfibula", "armborstfibula",
        "vendeltida spänne", "folkvandringstida spänne",
        "merovingertida spänne",
        "gotländskt spänne", "spänne guld",
        "spänne silver", "spänne brons",
        "spänne järn", "emaljerat spänne",
        "cloisonnéspänne", "filigranspänne",
        "trepassspänne", "fågelfibula",
        "hästformigt spänne",

        # Norwegisch
        "brosje", "spenne", "draktspenne vikingtid",
        "ringspenne middelalder", "smykke vikingtid",
        "sølvspenne", "bronsespenne",
        # ── NEU: Norwegisch ──
        "fibula", "gravfunn spenne",
        "vikingtidsspenne", "jernalderspenne",
        "folkevandringstid spenne",
        "merovingertid spenne", "likearmede spenner",
        "korsformet spenne", "fugleformet spenne",
        "dyreformet spenne", "skålformet spenne",
        "penselformet spenne",

        # Englisch fuer nordische Kontexte
        "brooch Viking", "brooch Bronze Age Nordic",
        "brooch Iron Age Nordic",
        "penannular brooch Nordic", "disc brooch Nordic",
        "tortoise brooch", "oval brooch Viking",
        "ring brooch", "brooch medieval Scandinavian",
        "equal-armed brooch", "cruciform brooch Nordic",
        "trefoil brooch Viking", "bird brooch Viking",
        "urnes style brooch", "borre style brooch",
        "jelling style brooch",
        # ── NEU: Englisch nordisch ──
        "box brooch Scandinavian", "Gotlandic disc brooch",
        "Vendel period brooch", "Migration period Scandinavian",
        "animal style brooch Nordic",
        "Salin Style I brooch", "Salin Style II brooch",
        "Borre style jewellery", "Mammen style brooch",
        "Ringerike style jewellery",
        "relief brooch Viking", "gilt brooch Viking",
    ],

    # ─── NEU: GRIECHISCH (für griechische Museen / Europeana Griechenland) ───
    "el": [
        "πόρπη", "πόρπες", "περόνη", "περόνες",
        "φίμπουλα", "πόρπη αρχαία", "πόρπη ρωμαϊκή",
        "πόρπη βυζαντινή", "πόρπη χάλκινη",
        "πόρπη σιδερένια", "πόρπη χρυσή",
        "πόρπη ασημένια", "πόρπη γεωμετρική",
        "πόρπη αρχαϊκή", "πόρπη ελληνιστική",
        "πόρπη μυκηναϊκή", "κόσμημα αρχαίο",
        "fibula ancient Greek",
    ],

    # ─── NEU: LATEIN (für wissenschaftliche Datenbanken) ───
    "la": [
        "fibula", "fibulae", "fibula aenea",
        "fibula ferrea", "fibula aurea", "fibula argentea",
    ],
}


# =============================================================================
# PLATTFORM → SPRACHEN (erweitert)
# =============================================================================

PLATFORM_LANGUAGES = {
    # Europeana versteht alles (50M+ Objekte aus ganz Europa)
    "europeana":        ["de", "en", "fr", "it", "nl", "es", "el"],
    # Deutsche Quellen
    "ddb":              ["de"],
    "museum_digital":   ["de"],
    "arachne":          ["de", "en", "la"],
    # Englische Museen
    "met":              ["en"],
    "cleveland":        ["en"],
    "chicago":          ["en"],
    "va":               ["en"],
    "harvard":          ["en"],
    "smithsonian":      ["en"],
    "pas":              ["en"],
    "british_museum":   ["en"],
    "walters":          ["en"],
    "penn":             ["en"],
    # ── NEU: Weitere englische Museen ──
    "getty":            ["en"],
    "boston_mfa":        ["en"],
    "corning":          ["en"],
    "ashmolean":        ["en"],
    "fitzwilliam":      ["en"],
    "national_museum_scotland": ["en"],
    "national_museum_wales":    ["en"],
    "national_museum_ireland":  ["en"],
    "york":             ["en"],
    # Niederlande
    "rijksmuseum":      ["nl", "en"],
    # Skandinavien
    "digitalt_museum":  ["scandi"],
    "soch":             ["scandi"],
    # Frankreich
    "pop_france":       ["fr"],
    # EU-Provider via Europeana
    "eu_providers":     ["de", "en", "fr", "es"],
    # ── NEU: Weitere Plattformen ──
    "kunsthistorisches_museum":  ["de", "en"],
    "naturhistorisches_museum":  ["de", "en"],
    "landesmuseum_wuerttemberg": ["de"],
    "rgzm":             ["de", "en"],
    "lmb":              ["de"],
    "roemisch_germanisches_museum": ["de", "en"],
    "limesmuseum":      ["de"],
}


# =============================================================================
# AUTO-GENERIERTER QUERIES-DICT
# =============================================================================

def _build_queries():
    """Generiert QUERIES dict aus MASTER_TERMS + PLATFORM_LANGUAGES."""
    queries = {}
    for platform, langs in PLATFORM_LANGUAGES.items():
        seen = set()
        terms = []
        for lang in langs:
            for term in MASTER_TERMS.get(lang, []):
                key = term.lower().strip()
                if key not in seen:
                    seen.add(key)
                    terms.append(term)
        queries[platform] = terms
    return queries


QUERIES = _build_queries()

# ─── Scraper-Queries (manuell, nicht aus Master) ───
QUERIES["badisches_lm"] = [
    "Fibel", "Brosche", "Gewandnadel", "Armbrustfibel",
    "Scheibenfibel", "Buegelfibel", "Bronze roemisch",
    "keltisch Latene", "Schmuck antik", "Ringfibel",
    "Kniefibel", "Zwiebelknopffibel", "Emailfibel",
    "Tierfibel", "Bogenfibel", "Spiralfibel",
    # ── NEU ──
    "Certosafibel", "Nauheimer Fibel", "Drahtfibel",
    "Hakenfibel", "Brillenfibel", "Pressblechfibel",
    "Fibel Grabfund", "Fibel Hortfund",
    "Fibel Alamannen", "Fibel Franken",
]

QUERIES["digicult_saarland"] = [
    "Fibel", "Brosche", "Gewandnadel", "Schmuck antik",
    "roemisch Bronze", "keltisch Eisen", "Fibel Grabfund",
    "Armbrustfibel", "Scheibenfibel", "Ringfibel",
    # ── NEU ──
    "Zwiebelknopffibel", "Kniefibel", "Emailfibel",
    "Fibel Merowingerzeit", "Fibel galloroemisch",
    "Tierfibel", "Bogenfibel", "Spiralfibel",
]

QUERIES["coinhirsch"] = [
    "Fibel", "Brosche", "roemisch", "keltisch",
    "Gewandnadel", "antik Schmuck",
    # ── NEU ──
    "Zwiebelknopffibel", "Emailfibel", "Scheibenfibel",
    "Armbrustfibel", "Ringfibel",
]


# =============================================================================
# KLASSIFIKATION — EPOCHEN, TYPEN, MATERIALIEN (erweitert)
# =============================================================================

EPOCH_MAP = {
    # Deutsch
    "bronzezeit": "Bronzezeit", "hallstatt": "Hallstattzeit",
    "latene": "Latènezeit", "la tene": "Latènezeit",
    "la tène": "Latènezeit", "eisenzeit": "Eisenzeit",
    "roemisch": "Römisch", "römisch": "Römisch",
    "kaiserzeit": "Römische Kaiserzeit", "spätantike": "Spätantike",
    "voelkerwanderung": "Völkerwanderungszeit",
    "merowingerzeit": "Merowingerzeit", "karolingisch": "Karolingisch",
    "mittelalter": "Mittelalter", "wikingerzeit": "Wikingerzeit",
    "germanisch": "Germanisch",
    # ── NEU: Deutsch ──
    "frühlatène": "Frühlatène", "fruehlatenee": "Frühlatène",
    "mittellatène": "Mittellatène", "mittellatene": "Mittellatène",
    "spätlatène": "Spätlatène", "spaetlatene": "Spätlatène",
    "hallstatt c": "Hallstatt C", "hallstatt d": "Hallstatt D",
    "augusteisch": "Augusteisch", "tiberisch": "Tiberisch",
    "claudisch": "Claudisch", "flavisch": "Flavisch",
    "trajanisch": "Trajanisch", "hadrianisch": "Hadrianisch",
    "severisch": "Severisch", "konstantinisch": "Konstantinisch",
    "ottonisch": "Ottonisch",
    "gallorömisch": "Gallorömisch", "galloroemisch": "Gallorömisch",
    "provinzialrömisch": "Provinzialrömisch",
    "langobardisch": "Langobardisch",
    "ostgotisch": "Ostgotisch", "westgotisch": "Westgotisch",
    "angelsächsisch": "Angelsächsisch", "angelsaechsisch": "Angelsächsisch",
    "fränkisch": "Fränkisch", "fraenkisch": "Fränkisch",
    "alamannisch": "Alamannisch", "awarisch": "Awarisch",
    "slawisch": "Slawisch", "hunnisch": "Hunnisch",
    "burgundisch": "Burgundisch",
    "frühmittelalter": "Frühmittelalter",
    "hochmittelalter": "Hochmittelalter",
    "spätmittelalter": "Spätmittelalter",
    "vendel": "Vendelzeit",

    # Englisch
    "bronze age": "Bronzezeit", "iron age": "Eisenzeit",
    "roman": "Römisch", "late roman": "Spätantike",
    "migration period": "Völkerwanderungszeit",
    "anglo-saxon": "Angelsächsisch", "viking": "Wikingerzeit",
    "medieval": "Mittelalter", "early medieval": "Frühmittelalter",
    "carolingian": "Karolingisch", "merovingian": "Merowingerzeit",
    "byzantine": "Byzantinisch",
    # ── NEU: Englisch ──
    "late bronze age": "Späte Bronzezeit",
    "early iron age": "Frühe Eisenzeit",
    "late iron age": "Späte Eisenzeit",
    "early la tene": "Frühlatène", "middle la tene": "Mittellatène",
    "late la tene": "Spätlatène",
    "la tene i": "Latène I", "la tene ii": "Latène II",
    "la tene iii": "Latène III",
    "la tene a": "Latène A", "la tene b": "Latène B",
    "la tene c": "Latène C", "la tene d": "Latène D",
    "hallstatt c": "Hallstatt C", "hallstatt d": "Hallstatt D",
    "augustan": "Augusteisch", "tiberian": "Tiberisch",
    "claudian": "Claudisch", "flavian": "Flavisch",
    "trajanic": "Trajanisch", "hadrianic": "Hadrianisch",
    "severan": "Severisch", "constantinian": "Konstantinisch",
    "late antique": "Spätantike",
    "sub-roman": "Subrömisch",
    "post-roman": "Nachrömisch",
    "lombard": "Langobardisch",
    "ostrogothic": "Ostgotisch", "visigothic": "Westgotisch",
    "frankish": "Fränkisch", "alamannic": "Alamannisch",
    "vendel period": "Vendelzeit",
    "geometric period": "Geometrisch",
    "orientalizing": "Orientalisierend",
    "archaic": "Archaisch", "classical": "Klassisch",
    "hellenistic": "Hellenistisch",
    "mycenaean": "Mykenisch",
    "etruscan": "Etruskisch",
    "italic": "Italisch",
    "thracian": "Thrakisch", "illyrian": "Illyrisch",

    # Franzoesisch
    "gaulois": "Keltisch", "gallo-romain": "Gallorömisch",
    "romain": "Römisch", "médiéval": "Mittelalter",
    "mérovingien": "Merowingerzeit", "carolingien": "Karolingisch",
    "âge du fer": "Eisenzeit", "âge du bronze": "Bronzezeit",
    # ── NEU: Franzoesisch ──
    "haut empire": "Hohe Kaiserzeit",
    "bas empire": "Späte Kaiserzeit",
    "antiquite tardive": "Spätantike",
    "haut moyen age": "Frühmittelalter",
    "la tene ancienne": "Frühlatène",
    "la tene moyenne": "Mittellatène",
    "la tene finale": "Spätlatène",
    "wisigoth": "Westgotisch", "burgonde": "Burgundisch",
    "franc": "Fränkisch",

    # Italienisch
    "romano": "Römisch", "etrusco": "Etruskisch",
    "villanoviano": "Villanova", "medievale": "Mittelalter",
    "longobardo": "Langobardisch", "altomedievale": "Frühmittelalter",
    # ── NEU: Italienisch ──
    "tardoromano": "Spätrömisch", "tardoantico": "Spätantik",
    "paleocristiano": "Frühchristlich",
    "arcaico": "Archaisch", "classico": "Klassisch",
    "ellenistico": "Hellenistisch",
    "protostorico": "Protohistorisch",
    "età del ferro": "Eisenzeit", "età del bronzo": "Bronzezeit",
    "ostrogoto": "Ostgotisch",
    "goto": "Gotisch",

    # Spanisch
    "celtiberico": "Keltiberisch", "iberico": "Iberisch",
    "visigodo": "Westgotisch", "hispanoromano": "Hispanorömisch",
    # ── NEU: Spanisch ──
    "tardorromano": "Spätrömisch", "bajo imperio": "Späte Kaiserzeit",
    "alto imperio": "Hohe Kaiserzeit",
    "suevo": "Suebisch", "edad del hierro": "Eisenzeit",
    "edad del bronce": "Bronzezeit",
    "altomedieval": "Frühmittelalter",

    # ── NEU: Griechisch (transliteriert) ──
    "geometriko": "Geometrisch", "archaiko": "Archaisch",
    "klassiko": "Klassisch", "ellinistiko": "Hellenistisch",
    "romaiko": "Römisch", "byzantino": "Byzantinisch",
    "mykinaiko": "Mykenisch",
}

FIBULA_TYPES = [
    # Almgren Hauptgruppen
    "Bogenfibel", "Kniefibel", "Armbrustfibel", "Scheibenfibel",
    "Buegelfibel", "Ringfibel", "Spiralfibel",
    # Sonderformen
    "Certosafibel", "Nauheimer Fibel", "Zwiebelknopffibel",
    "Kreuzfibel", "Tierfibel", "Gleicharmige Fibel",
    "Hakenfibel", "Plattenfibel", "Emailfibel",
    "Distelfibel", "Hülsenspirale", "Paukenfibel",
    "Schlangenfibel", "Brillenfibel", "Omega-Fibel",
    "Kragenfibel", "Stützarmfibel", "Rosettenfibel",
    "Dosenfibel", "Sternfibel", "Radfibel", "Blechfibel",
    "Tutulusfibel", "S-Fibel", "Drahtfibel",
    "Maskenfibel", "Vogelfibel", "Pferdefibel", "Entenfibel",
    "Aucissafibel", "Augenfibel", "Rollenkappenfibel",
    # Englische Typen
    "Crossbow", "Penannular", "Annular", "Disc brooch",
    "Saucer brooch", "Cruciform", "Long brooch",
    "Equal-armed", "Trefoil", "Tortoise brooch",
    "Trumpet", "Fantail", "Headstud", "Dragonesque",
    "Hod Hill", "Colchester", "Aucissa", "T-shaped",
    "Dolphin", "Thistle", "Langton Down",
    # Italienische Typen
    "Navicella", "Sanguisuga", "Serpeggiante",
    "Ad occhiali", "Ad arco semplice",
    "Villanova",

    # ── NEU: Deutsche Typen ──
    "Pressblechfibel", "Filigranfibel", "Kerbschnittfibel",
    "Cloisonnéfibel", "Almandinscheibenfibel",
    "Omegafibel", "Flügelfibel", "Gabelfibel",
    "Doppelfibel", "Leiterfibel", "Gitterfibel",
    "Halbkreisfibel", "Peltafibel", "Raupenfibel",
    "Doppelknopffibel", "Dreisprossenfibel",
    "Viersprossenfibel", "Fünfknopffibel",
    "Flachbogenfibel", "Mittellatènefibel",
    "Spätlatènefibel", "Frühlatènefibel",
    "Armbrust-Scharnierfibel", "Rautenfibel",
    "Rippenfibel", "Vogelkopffibel",
    "Tierkopffibel", "Löwenfibel", "Hirschfibel",
    "Fischfibel", "Hasenfibel", "Greiffibel",
    "Adlerfibel", "Hahnenfibel", "Reiterfibel",
    "Schuhfibel", "Amphora-Fibel", "Axtfibel",
    "Prachtfibel", "Stuetzbalken-Fibel",
    "Hülsencharnierfibel", "Backenscharnierfibel",

    # ── NEU: Englische Typen ──
    "Polden Hill", "Wroxeter", "Aesica",
    "Backworth", "Birdlip", "Battersea",
    "Divided bow", "Strip bow", "Flat bow",
    "Wire brooch", "Ring-and-dot", "Seal box",
    "Lozenge", "Umbonate", "Lunate",
    "Wheel brooch", "Swastika",
    "Button brooch", "Quoit brooch",
    "Keystone", "Kentish disc",
    "Radiate-headed", "Supporting-arm",
    "Composite disc", "Small-long",
    "Square-headed", "Great square-headed",
    "Romano-British", "Colchester derivative",
    "Colchester two-piece", "Nauheim derivative",
    "Chip-carved", "Horse-and-rider",
    "Cockerel brooch", "Eagle fibula",
    "Duck brooch", "Hare brooch",
    "Fly brooch", "Shoe brooch",
    "Amphora brooch", "Axe brooch",
    "Pelta", "S-shaped brooch",
    "Bird-headed", "Box brooch",

    # ── NEU: Französische Typen ──
    "Fibule à ailettes", "Fibule à collerette",
    "Fibule digitée", "Fibule polylobée",
    "Fibule à tête rayonnante",

    # ── NEU: Spanische Typen ──
    "Fíbula de caballito", "Fíbula de doble resorte",
    "Fíbula anular hispánica", "Fíbula de La Tène hispánica",

    # ── NEU: Griechisch/Ostmediterran ──
    "Mycenaean", "Sub-Mycenaean", "Protogeometric",
    "Geometric period", "Orientalizing",
    "Boeotian", "Thessalian", "Illyrian fibula type",
    "Thracian", "Phrygian", "Anatolian",
    "Praeneste", "Apulian", "Campanian",
]

MATERIAL_MAP = {
    # Deutsch
    "bronze": "Bronze", "eisen": "Eisen", "silber": "Silber",
    "gold": "Gold", "kupfer": "Kupfer", "email": "Email",
    "zinn": "Zinn", "messing": "Messing", "buntmetall": "Buntmetall",
    # Englisch
    "copper alloy": "Kupferlegierung", "copper": "Kupfer",
    "iron": "Eisen", "silver": "Silber",
    "gilt": "Vergoldet", "gilded": "Vergoldet",
    "enamel": "Email", "garnet": "Granat",
    "cloisonne": "Cloisonné", "tin": "Zinn",
    "pewter": "Zinn", "brass": "Messing",
    "electrum": "Elektron", "niello": "Niello",
    # Franzoesisch
    "fer": "Eisen", "argent": "Silber",
    "cuivre": "Kupfer", "or": "Gold",
    "etain": "Zinn", "laiton": "Messing",
    # Italienisch
    "bronzo": "Bronze", "ferro": "Eisen",
    "argento": "Silber", "oro": "Gold", "rame": "Kupfer",
    # Spanisch
    "hierro": "Eisen", "plata": "Silber",
    "bronce": "Bronze", "cobre": "Kupfer",

    # ── NEU: Deutsch ──
    "kupferlegierung": "Kupferlegierung",
    "vergoldet": "Vergoldet", "versilbert": "Versilbert",
    "blei": "Blei", "granat": "Granat",
    "almandin": "Almandin", "koralle": "Koralle",
    "bernstein": "Bernstein", "glas": "Glas",
    "glaspaste": "Glaspaste", "millefiori": "Millefiori",
    "filigran": "Filigran", "granulation": "Granulation",
    "champlevé": "Champlevé", "kerbschnitt": "Kerbschnitt",
    "tauschierung": "Tauschierung", "pressblech": "Pressblech",

    # ── NEU: Englisch ──
    "gold": "Gold", "lead": "Blei", "lead alloy": "Bleilegierung",
    "bone": "Knochen", "ivory": "Elfenbein", "jet": "Gagat",
    "glass": "Glas", "glass paste": "Glaspaste",
    "millefiori": "Millefiori", "coral": "Koralle",
    "amber": "Bernstein", "filigree": "Filigran",
    "granulation": "Granulation", "champlevé": "Champlevé",
    "chip-carved": "Kerbschnitt",
    "tinned": "Verzinnt", "silvered": "Versilbert",
    "silver-gilt": "Silbervergoldet",
    "inlaid": "Tauschiert", "damascened": "Damasziert",

    # ── NEU: Französisch ──
    "alliage cuivreux": "Kupferlegierung",
    "plomb": "Blei", "grenat": "Granat",
    "corail": "Koralle", "ambre": "Bernstein",
    "verre": "Glas", "filigrane": "Filigran",
    "dore": "Vergoldet", "argente": "Versilbert",

    # ── NEU: Italienisch ──
    "lega rame": "Kupferlegierung",
    "piombo": "Blei", "granato": "Granat",
    "smalto": "Email", "avorio": "Elfenbein",

    # ── NEU: Spanisch ──
    "aleacion cobre": "Kupferlegierung",
    "plomo": "Blei", "esmalte": "Email",
    "granate": "Granat", "coral": "Koralle",
}

# =============================================================================
# KLASSIFIKATIONS-FUNKTIONEN (benoetigt von museum_apis.py)
# =============================================================================

def normalize_epoch(text: str) -> str:
    """Normalisiert Epochenbezeichnungen aus verschiedenen Sprachen.
    
    Durchsucht den Text nach bekannten Epochen-Schluesselwoertern
    und gibt die normalisierte deutsche Bezeichnung zurueck.
    
    Args:
        text: Freitext mit Epochenangabe (kann beliebige Sprache sein)
    
    Returns:
        Normalisierte Epochenbezeichnung oder Original-Text
    """
    if not text:
        return ""
    text_lower = text.lower().strip()
    
    # Exakter Match zuerst (laengere Keys zuerst fuer Praezision)
    for key in sorted(EPOCH_MAP.keys(), key=len, reverse=True):
        if key in text_lower:
            return EPOCH_MAP[key]
    
    return text.strip()


def normalize_material(text: str) -> str:
    """Normalisiert Materialbezeichnungen aus verschiedenen Sprachen.
    
    Args:
        text: Freitext mit Materialangabe
    
    Returns:
        Normalisierte Materialbezeichnung oder Original-Text
    """
    if not text:
        return ""
    text_lower = text.lower().strip()
    
    # Laengere Keys zuerst (z.B. "copper alloy" vor "copper")
    for key in sorted(MATERIAL_MAP.keys(), key=len, reverse=True):
        if key in text_lower:
            return MATERIAL_MAP[key]
    
    return text.strip()


def detect_fibula_type(text: str) -> str:
    """Erkennt den Fibeltyp aus Titel/Beschreibung.
    
    Durchsucht den Text nach bekannten Fibeltypen (deutsch + englisch).
    Gibt den ERSTEN gefundenen Typ zurueck (laengste Matches zuerst).
    
    Args:
        text: Titel und/oder Beschreibung des Objekts
    
    Returns:
        Erkannter Fibeltyp oder leerer String
    """
    if not text:
        return ""
    text_lower = text.lower()
    
    # Laengere Typen zuerst pruefen (z.B. "Nauheimer Fibel" vor "Fibel")
    for ftype in sorted(FIBULA_TYPES, key=len, reverse=True):
        if ftype.lower() in text_lower:
            return ftype
    
    return ""


def print_stats():
    total_terms = sum(len(v) for v in MASTER_TERMS.values())
    total_queries = sum(len(v) for v in QUERIES.values())
    print(f"\n=== MASTER-TERMS: {total_terms} ueber {len(MASTER_TERMS)} Sprachen ===")
    for lang, terms in MASTER_TERMS.items():
        print(f"  {lang:8s}: {len(terms):3d} Begriffe")
    print(f"\n=== QUERIES: {total_queries} total ueber {len(QUERIES)} Quellen ===")
    for platform, terms in sorted(QUERIES.items(), key=lambda x: -len(x[1])):
        langs = PLATFORM_LANGUAGES.get(platform, [])
        print(f"  {platform:20s}: {len(terms):3d} Begriffe  ({', '.join(langs)})")


if __name__ == "__main__":
    print_stats()
