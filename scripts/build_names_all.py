#!/usr/bin/env python3
"""Unified builder script to compile data/names_<lang>.json for all supported languages in Replantio.

Target languages:
- tr: Turkish (Türkçe) -> data/names_tr.json
- es: Spanish (Español) -> data/names_es.json
- fr: French (Français) -> data/names_fr.json
- de: German (Deutsch) -> data/names_de.json
- zh: Chinese (中文) -> data/names_zh.json
- ja: Japanese (日本語) -> data/names_ja.json
- ru: Russian (Русский) -> data/names_ru.json
- id: Indonesian (Bahasa Indonesia) -> data/names_id.json
- hi: Hindi (हिन्दी) -> data/names_hi.json
- sw: Swahili (Kiswahili) -> data/names_sw.json
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"

# Import Turkish datasets from build_names_tr
with open(ROOT / "scripts/build_names_tr.py", "r", encoding="utf-8") as f:
    tr_src = f.read()

curated_tr_match = re.search(r"CURATED = (\{.*?\n\})", tr_src, re.DOTALL)
genus_tr_match = re.search(r"GENUS_FALLBACK = (\{.*?\n\})", tr_src, re.DOTALL)
epithets_tr_match = re.search(r"EPITHETS = (\{.*?\n\})", tr_src, re.DOTALL)

exec(curated_tr_match.group(0).replace("CURATED =", "CURATED_TR ="))
exec(genus_tr_match.group(0).replace("GENUS_FALLBACK =", "GENUS_TR ="))
exec(epithets_tr_match.group(0).replace("EPITHETS =", "EPITHETS_TR ="))

# Load GENUS datasets
with open(ROOT / "scripts/build_names_all.py", "r", encoding="utf-8") as f:
    all_code = f.read()

genus_part_match = re.search(r"(GENUS_ES = \{.*?\nGENUS_SW = \{.*?\n\})", all_code, re.DOTALL)
if genus_part_match:
    exec(genus_part_match.group(1))


# Genus Dictionaries for all languages
GENUS_ES = {
    "Abelmoschus": ("abelmosco", ["quimbombó"]), "Abies": ("abeto", []),
    "Acacia": ("acacia", ["mimosa"]), "Acer": ("arce", []), "Acrocarpus": ("cedro rosado", []),
    "Actinidia": ("kiwi", []), "Adansonia": ("baobab", []), "Adenanthera": ("coralillo", []),
    "Aegle": ("marmelo", []), "Aesculus": ("castaño de indias", []), "Afzelia": ("doussié", []),
    "Agathis": ("damara", ["kauri"]), "Agave": ("maguey", ["agave"]), "Albizia": ("albizia", ["acacia"]),
    "Allium": ("ajo/cebolla", []), "Alnus": ("aliso", []), "Aloe": ("áloe", []),
    "Aloysia": ("cedrón", ["hierba luisa"]), "Amaranthus": ("amaranto", []),
    "Anacardium": ("anacardo", ["marañón", "cajuil"]), "Ananas": ("piña", ["ananás"]),
    "Annona": ("anona", ["guanábana", "chirimoya"]), "Anthocephalus": ("kadam", []),
    "Arachis": ("cacahuete", ["maní"]), "Araucaria": ("araucaria", []),
    "Arbutus": ("madroño", []), "Artocarpus": ("árbol del pan", ["yaca"]),
    "Asparagus": ("espárrago", []), "Astragalus": ("astrágalo", []),
    "Avena": ("avena", []), "Azadirachta": ("nim", ["neem"]), "Bambusa": ("bambú", []),
    "Beta": ("remolacha", ["betabel"]), "Betula": ("abedul", []), "Bixa": ("achiote", []),
    "Bombax": ("ceiba roja", []), "Brassica": ("col/mostaza/colza", []),
    "Cajanus": ("guandul", ["frijol de palo"]), "Callistemon": ("limpiatubos", []),
    "Callitris": ("ciprés de australia", []), "Camellia": ("camelia", ["árbol del té"]),
    "Cannabis": ("cáñamo", []), "Capparis": ("alcaparra", []), "Capsicum": ("pimiento", ["chile"]),
    "Carica": ("papaya", []), "Carpinus": ("carpe", []), "Carya": ("pacana", ["hickory"]),
    "Cassia": ("casia", ["lluvia de oro"]), "Castanea": ("castaño", []),
    "Casuarina": ("casuarina", ["pino australiano"]), "Catalpa": ("catalpa", []),
    "Cedrela": ("cedro americano", []), "Cedrus": ("cedro", []), "Celtis": ("almez", []),
    "Ceratonia": ("algarrobo", []), "Cercis": ("árbol de judas", []),
    "Chamaecyparis": ("falso ciprés", []), "Cicer": ("garbanzo", []),
    "Cinchona": ("quina", ["chinchona"]), "Cinnamomum": ("canelo", ["alcanforero"]),
    "Citrus": ("cítrico", ["naranjo", "limonero"]), "Cocos": ("cocotero", []),
    "Coffea": ("cafeto", ["café"]), "Cola": ("árbol de la cola", []),
    "Colocasia": ("taro", ["ñame"]), "Copaifera": ("copaiba", []),
    "Cordia": ("laurel negro", []), "Coriandrum": ("cilantro", []),
    "Corylus": ("avellano", []), "Crotalaria": ("cascabelillo", []),
    "Cryptomeria": ("criptomeria", ["cedro japonés"]), "Cucumis": ("pepino/melón", []),
    "Cucurbita": ("calabaza", ["calabacín"]), "Cuminum": ("comino", []),
    "Cupressus": ("ciprés", []), "Cydonia": ("membrillero", []),
    "Cymbopogon": ("limonaria", ["zacate de limón"]), "Cynara": ("alcachofa", []),
    "Dalbergia": ("palisandro", ["palo de rosa"]), "Daucus": ("zanahoria", []),
    "Diospyros": ("caqui", ["ébano"]), "Dipteryx": ("cumarú", ["habilla de san ignacio"]),
    "Elaeis": ("palma aceitera", []), "Eragrostis": ("pasto teff", []),
    "Erica": ("brezo", []), "Eriobotrya": ("níspero", []), "Erythrina": ("ceibo", ["eritrina"]),
    "Eucalyptus": ("eucalipto", []), "Eugenia": ("eugenia", ["arrayán"]),
    "Fagus": ("haya", []), "Ficus": ("higuera", ["ficus"]), "Foeniculum": ("hinojo", []),
    "Fragaria": ("fresa", ["frutilla"]), "Fraxinus": ("fresno", []),
    "Ginkgo": ("ginkgo", []), "Gleditsia": ("acacia de tres espinas", []),
    "Glycine": ("soja", ["soya"]), "Gossypium": ("algodonero", ["algodón"]),
    "Grevillea": ("grevillea", ["roble sedoso"]), "Guazuma": ("guácima", []),
    "Hevea": ("árbol del caucho", []), "Hibiscus": ("hibisco", ["cucarda"]),
    "Hordeum": ("cebada", []), "Hymenaea": ("jatoba", ["guapinol"]),
    "Ilex": ("acebo", ["yerba mate"]), "Inga": ("guamo", ["pacay"]),
    "Ipomoea": ("batata", ["camote"]), "Jacaranda": ("jacarandá", []),
    "Jasminum": ("jazmín", []), "Juglans": ("nogal", []), "Juniperus": ("enebro", ["sabina"]),
    "Khaya": ("caoba africana", []), "Lablab": ("frijol jacinto", []),
    "Lactuca": ("lechuga", []), "Larix": ("alerce", []), "Laurus": ("laurel", []),
    "Lavandula": ("lavanda", ["espliego"]), "Lens": ("lenteja", []),
    "Leucaena": ("guaje", ["leucaena"]), "Ligustrum": ("aligustre", []),
    "Linum": ("lino", []), "Liquidambar": ("liquidámbar", []),
    "Liriodendron": ("tulípero", []), "Litchi": ("lichi", []),
    "Lolium": ("raigrás", []), "Lupinus": ("altramuz", ["lupino"]),
    "Macadamia": ("macadamia", []), "Magnolia": ("magnolia", []),
    "Malus": ("manzano", []), "Mangifera": ("mango", []), "Manihot": ("yuca", ["mandioca"]),
    "Medicago": ("alfalfa", []), "Melaleuca": ("árbol del té", []),
    "Melia": ("cinamomo", ["paraíso"]), "Mentha": ("menta", ["hierbabuena"]),
    "Morus": ("morera", ["moral"]), "Musa": ("platanero", ["banano"]),
    "Myrtus": ("mirto", ["arrayán"]), "Nicotiana": ("tabaco", []),
    "Olea": ("olivo", ["olivera"]), "Opuntia": ("nopal", ["chumbera"]),
    "Origanum": ("orégano", []), "Oryza": ("arroz", []), "Panicum": ("mijo", []),
    "Passiflora": ("maracuyá", ["granadilla"]), "Paulownia": ("paulonia", []),
    "Pennisetum": ("pasto elefante", []), "Persea": ("aguacate", ["palto"]),
    "Petroselinum": ("perejil", []), "Phaseolus": ("frijol", ["judía", "poroto"]),
    "Phoenix": ("palmera datilera", []), "Picea": ("pícea", ["falso abeto"]),
    "Pinus": ("pino", []), "Piper": ("pimentero", ["pimienta"]),
    "Pistacia": ("pistachero", ["lentisco", "terebinto"]), "Pisum": ("guisante", ["arveja"]),
    "Platanus": ("plátano de sombra", []), "Poa": ("espiguilla", []),
    "Populus": ("álamo", ["chopo"]), "Prosopis": ("mezquite", ["algarrobo"]),
    "Prunus": ("ciruelo/cerezo/almendro/melocotonero", []), "Pseudotsuga": ("abeto douglas", []),
    "Psidium": ("guayabo", []), "Punica": ("granado", []), "Pyrus": ("peral", []),
    "Quercus": ("roble", ["encina", "alcornoque"]), "Raphanus": ("rábano", []),
    "Rhus": ("zumaque", []), "Ribes": ("grosellero", []), "Ricinus": ("ricino", ["higuerilla"]),
    "Robinia": ("falsa acacia", []), "Rosa": ("rosal", []), "Rosmarinus": ("romero", []),
    "Rubus": ("zarzamora", ["frambueso"]), "Saccharum": ("caña de azúcar", []),
    "Salix": ("sauce", []), "Salvia": ("salvia", []), "Sambucus": ("saúco", []),
    "Schinus": ("falso pimentero", []), "Secale": ("centeno", []),
    "Senna": ("sen", []), "Sequoia": ("secuoya", []), "Sequoiadendron": ("secuoya gigante", []),
    "Sesamum": ("sésamo", ["ajonjolí"]), "Sesbania": ("sesbania", []),
    "Solanum": ("berenjena/tomate/patata", []), "Sorghum": ("sorgo", []),
    "Spinacia": ("espinaca", []), "Swietenia": ("caoba", []),
    "Syzygium": ("clavero", ["árbol de clavo"]), "Tagetes": ("cempasúchil", ["tagete"]),
    "Tamarindus": ("tamarindo", []), "Tamarix": ("taray", ["tamarisco"]),
    "Taxodium": ("ciprés calvo", ["ahuehuete"]), "Taxus": ("tejo", []),
    "Tectona": ("teca", []), "Terminalia": ("terminalia", []),
    "Theobroma": ("cacaotero", ["cacao"]), "Thuja": ("tuya", []),
    "Thymus": ("tomillo", []), "Tilia": ("tilo", []), "Trifolium": ("trébol", []),
    "Triticum": ("trigo", []), "Tsuga": ("tsuga", []), "Ulmus": ("olmo", []),
    "Vaccinium": ("arándano", []), "Vanilla": ("vainilla", []),
    "Vicia": ("veza", ["haba"]), "Vigna": ("caupí", ["frijol"]),
    "Vitex": ("sauzgatillo", []), "Vitis": ("vid", ["parra"]),
    "Zea": ("maíz", []), "Zingiber": ("jengibre", []), "Ziziphus": ("azufaifo", [])
}

GENUS_FR = {
    "Abelmoschus": ("gombo", []), "Abies": ("sapin", []), "Acacia": ("acacia", ["mimosa"]),
    "Acer": ("érable", []), "Acrocarpus": ("cèdre rose", []), "Actinidia": ("kiwi", []),
    "Adansonia": ("baobab", []), "Adenanthera": ("bois noir", []), "Aegle": ("bael", []),
    "Aesculus": ("marronnier d'inde", []), "Afzelia": ("doussié", []), "Agathis": ("kauri", []),
    "Agave": ("agave", []), "Albizia": ("albizia", ["arbre de soie"]),
    "Allium": ("ail/oignon/poireau", []), "Alnus": ("aulne", []), "Aloe": ("aloès", []),
    "Aloysia": ("verveine citronnelle", []), "Amaranthus": ("amarante", []),
    "Anacardium": ("anacardier", ["pommier-cajou"]), "Ananas": ("ananas", []),
    "Annona": ("anone", ["corossol", "chérimolier"]), "Anthocephalus": ("kadam", []),
    "Arachis": ("arachide", ["cacahuète"]), "Araucaria": ("araucaria", []),
    "Arbutus": ("arbousier", []), "Artocarpus": ("arbre à pain", ["jacquier"]),
    "Asparagus": ("asperge", []), "Astragalus": ("astragale", []),
    "Avena": ("avoine", []), "Azadirachta": ("margousier", ["neem"]), "Bambusa": ("bambou", []),
    "Beta": ("betterave", []), "Betula": ("bouleau", []), "Bixa": ("roucou", []),
    "Bombax": ("kapokier rouge", []), "Brassica": ("chou/moutarde/colza", []),
    "Cajanus": ("pois d'angole", []), "Callistemon": ("rince-bouteille", []),
    "Callitris": ("cyprès d'australie", []), "Camellia": ("camélia", ["théier"]),
    "Cannabis": ("chanvre", []), "Capparis": ("câprier", []), "Capsicum": ("piment", ["poivron"]),
    "Carica": ("papayer", []), "Carpinus": ("charme", []), "Carya": ("pacanier", ["caryer"]),
    "Cassia": ("cassier", ["canéficier"]), "Castanea": ("châtaignier", []),
    "Casuarina": ("filao", ["bois de fer"]), "Catalpa": ("catalpa", []),
    "Cedrela": ("acajou amer", []), "Cedrus": ("cèdre", []), "Celtis": ("micocoulier", []),
    "Ceratonia": ("caroubier", []), "Cercis": ("arbre de judée", []),
    "Chamaecyparis": ("faux cyprès", []), "Cicer": ("pois chiche", []),
    "Cinchona": ("quinquina", []), "Cinnamomum": ("cannelier", ["camphrier"]),
    "Citrus": ("agrume", ["oranger", "citronnier"]), "Cocos": ("cocotier", []),
    "Coffea": ("caféier", []), "Cola": ("kolatier", []), "Colocasia": ("taro", []),
    "Copaifera": ("copaïba", []), "Cordia": ("cordia", []), "Coriandrum": ("coriandre", []),
    "Corylus": ("noisetier", []), "Crotalaria": ("crotalaire", []),
    "Cryptomeria": ("cryptomeria", ["cèdre du japon"]), "Cucumis": ("concombre/melon", []),
    "Cucurbita": ("courge", ["citrouille"]), "Cuminum": ("cumin", []),
    "Cupressus": ("cyprès", []), "Cydonia": ("cognassier", []),
    "Cymbopogon": ("citronnelle", []), "Cynara": ("artichaut", []),
    "Dalbergia": ("palissandre", ["bois de rose"]), "Daucus": ("carotte", []),
    "Diospyros": ("plaqueminier", ["ébénier"]), "Dipteryx": ("fève tonka", []),
    "Elaeis": ("palmier à huile", []), "Eragrostis": ("teff", []), "Erica": ("bruyère", []),
    "Eriobotrya": ("néflier du japon", []), "Erythrina": ("érythrine", ["arbre corail"]),
    "Eucalyptus": ("eucalyptus", []), "Eugenia": ("eugenia", ["jamrosat"]),
    "Fagus": ("hêtre", []), "Ficus": ("figuier", ["ficus"]), "Foeniculum": ("fenouil", []),
    "Fragaria": ("fraisier", []), "Fraxinus": ("frêne", []), "Ginkgo": ("ginkgo", []),
    "Gleditsia": ("févier d'amérique", []), "Glycine": ("soja", []),
    "Gossypium": ("cotonnier", []), "Grevillea": ("grévillée", ["chêne soyeux"]),
    "Guazuma": ("orme d'amérique", []), "Hevea": ("hévéa", ["arbre à caoutchouc"]),
    "Hibiscus": ("hibiscus", ["guimauve"]), "Hordeum": ("orge", []),
    "Hymenaea": ("courbaril", ["jatoba"]), "Ilex": ("houx", ["maté"]),
    "Inga": ("pois doux", ["inga"]), "Ipomoea": ("patate douce", []),
    "Jacaranda": ("jacaranda", []), "Jasminum": ("jasmin", []), "Juglans": ("noyer", []),
    "Juniperus": ("genévrier", []), "Khaya": ("acajou d'afrique", []),
    "Lablab": ("dolique lablab", []), "Lactuca": ("laitue", []), "Larix": ("mélèze", []),
    "Laurus": ("laurier", []), "Lavandula": ("lavande", []), "Lens": ("lentille", []),
    "Leucaena": ("leucaena", ["faux mimosa"]), "Ligustrum": ("troène", []),
    "Linum": ("lin", []), "Liquidambar": ("copalme", ["liquidambar"]),
    "Liriodendron": ("tulipier", []), "Litchi": ("litchi", []), "Lolium": ("ray-grass", []),
    "Lupinus": ("lupin", []), "Macadamia": ("macadamia", []), "Magnolia": ("magnolia", []),
    "Malus": ("pommier", []), "Mangifera": ("manguier", []), "Manihot": ("manioc", []),
    "Medicago": ("luzerne", []), "Melaleuca": ("mélaleuca", ["arbre à thé"]),
    "Melia": ("margousier", ["lilas de perse"]), "Mentha": ("menthe", []),
    "Morus": ("mûrier", []), "Musa": ("bananier", []), "Myrtus": ("myrte", []),
    "Nicotiana": ("tabac", []), "Olea": ("olivier", []), "Opuntia": ("figuier de barbarie", []),
    "Origanum": ("origan", ["marjolaine"]), "Oryza": ("riz", []), "Panicum": ("millet", []),
    "Passiflora": ("passiflore", ["maracudja"]), "Paulownia": ("paulownia", []),
    "Pennisetum": ("pennisetum", ["herbe à éléphant"]), "Persea": ("avocatier", []),
    "Petroselinum": ("persil", []), "Phaseolus": ("haricot", []),
    "Phoenix": ("palmier-dattier", []), "Picea": ("épicéa", []), "Pinus": ("pin", []),
    "Piper": ("poivrier", []), "Pistacia": ("pistachier", []), "Pisum": ("pois", []),
    "Platanus": ("platane", []), "Poa": ("pâturin", []), "Populus": ("peuplier", []),
    "Prosopis": ("mesquite", []), "Prunus": ("prunier/cerisier/amandier/pêcher", []),
    "Pseudotsuga": ("douglas", []), "Psidium": ("goyavier", []), "Punica": ("grenadier", []),
    "Pyrus": ("poirier", []), "Quercus": ("chêne", []), "Raphanus": ("radis", []),
    "Rhus": ("sumac", []), "Ribes": ("groseillier", []), "Ricinus": ("ricin", []),
    "Robinia": ("robinier", ["faux-acacia"]), "Rosa": ("rosier", []),
    "Rosmarinus": ("romarin", []), "Rubus": ("ronce", ["framboisier"]),
    "Saccharum": ("canne à sucre", []), "Salix": ("saule", []), "Salvia": ("sauge", []),
    "Sambucus": ("sureau", []), "Schinus": ("faux-poivrier", []), "Secale": ("seigle", []),
    "Senna": ("séné", []), "Sequoia": ("séquoia", []), "Sequoiadendron": ("séquoia géant", []),
    "Sesamum": ("sésame", []), "Sesbania": ("sesbania", []),
    "Solanum": ("aubergine/tomate/pomme de terre", []), "Sorghum": ("sorgho", []),
    "Spinacia": ("épinard", []), "Swietenia": ("acajou", []),
    "Syzygium": ("giroflier", ["jambosier"]), "Tagetes": ("œillet d'inde", []),
    "Tamarindus": ("tamarinier", []), "Tamarix": ("tamaris", []),
    "Taxodium": ("cyprès chauve", []), "Taxus": ("if", []), "Tectona": ("teck", []),
    "Terminalia": ("badamier", []), "Theobroma": ("cacaoyer", []), "Thuja": ("thuja", []),
    "Thymus": ("thym", []), "Tilia": ("tilleul", []), "Trifolium": ("trèfle", []),
    "Triticum": ("blé", []), "Tsuga": ("tsuga", []), "Ulmus": ("orme", []),
    "Vaccinium": ("myrtille", ["canneberge"]), "Vanilla": ("vanillier", []),
    "Vicia": ("vesce", ["fève"]), "Vigna": ("niébé", ["haricot"]),
    "Vitex": ("gattilier", []), "Vitis": ("vigne", []), "Zea": ("maïs", []),
    "Zingiber": ("gingembre", []), "Ziziphus": ("jujubier", [])
}

GENUS_DE = {
    "Abelmoschus": ("okra", []), "Abies": ("tanne", []), "Acacia": ("akazie", ["mimose"]),
    "Acer": ("ahorn", []), "Acrocarpus": ("rosa zeder", []), "Actinidia": ("kiwi", []),
    "Adansonia": ("affenbrotbaum", ["baobab"]), "Adenanthera": ("korallenholz", []),
    "Aegle": ("bael-frucht", []), "Aesculus": ("rosskastanie", []), "Afzelia": ("afzelia", []),
    "Agathis": ("kaurifichte", []), "Agave": ("agave", []), "Albizia": ("seidenakazie", []),
    "Allium": ("lauch/zwiebel/knoblauch", []), "Alnus": ("erle", []), "Aloe": ("aloe", []),
    "Aloysia": ("zitronenverbene", []), "Amaranthus": ("amaranth", []),
    "Anacardium": ("cashewbaum", ["kaschunuss"]), "Ananas": ("ananas", []),
    "Annona": ("annone", ["zimtapfel", "stachelanone"]), "Anthocephalus": ("kadam", []),
    "Arachis": ("erdnuss", []), "Araucaria": ("araukarie", []), "Arbutus": ("erdbeerbaum", []),
    "Artocarpus": ("brotfruchtbaum", ["jackfrucht"]), "Asparagus": ("spargel", []),
    "Astragalus": ("tragant", []), "Avena": ("hafer", []), "Azadirachta": ("neembaum", []),
    "Bambusa": ("bambus", []), "Beta": ("rübe", ["zuckerrübe"]), "Betula": ("birke", []),
    "Bixa": ("annattostrauch", []), "Bombax": ("kapokbaum", []), "Brassica": ("kohl/raps/senf", []),
    "Cajanus": ("straucherbse", []), "Callistemon": ("zylinderputzer", []),
    "Callitris": ("schuppenfichte", []), "Camellia": ("kamelie", ["teestrauch"]),
    "Cannabis": ("hanf", []), "Capparis": ("kaper", []), "Capsicum": ("paprika", ["chili"]),
    "Carica": ("papaya", []), "Carpinus": ("hainbuche", []), "Carya": ("hickory", ["pekannuss"]),
    "Cassia": ("kassie", []), "Castanea": ("kastanie", ["edelkastanie"]),
    "Casuarina": ("kasuarine", ["eisenholz"]), "Catalpa": ("trompetenbaum", []),
    "Cedrela": ("westindische zeder", []), "Cedrus": ("zeder", []), "Celtis": ("zürgelbaum", []),
    "Ceratonia": ("johannisbrotbaum", []), "Cercis": ("judasbaum", []),
    "Chamaecyparis": ("scheinzypresse", []), "Cicer": ("kichererbse", []),
    "Cinchona": ("chinarindenbaum", []), "Cinnamomum": ("zimtbaum", ["kampferbaum"]),
    "Citrus": ("zitruspflanze", ["zitrone", "orange"]), "Cocos": ("kokospalme", []),
    "Coffea": ("kaffeestrauch", ["kaffee"]), "Cola": ("kolabaum", []),
    "Colocasia": ("taro", []), "Copaifera": ("kopaivabaum", []), "Cordia": ("kordie", []),
    "Coriandrum": ("koriander", []), "Corylus": ("hasel", []), "Crotalaria": ("klapperhülse", []),
    "Cryptomeria": ("sichelfichte", ["japanische zeder"]), "Cucumis": ("gurke/melone", []),
    "Cucurbita": ("kürbis", []), "Cuminum": ("kreuzkümmel", []), "Cupressus": ("zypresse", []),
    "Cydonia": ("quitte", []), "Cymbopogon": ("zitronengras", []), "Cynara": ("artischocke", []),
    "Dalbergia": ("palisander", ["rosenholz"]), "Daucus": ("karotte", ["möhre"]),
    "Diospyros": ("ebenholzbaum", ["kaki"]), "Dipteryx": ("tonkabaum", []),
    "Elaeis": ("ölpalme", []), "Eragrostis": ("liebesgras", ["teff"]), "Erica": ("heidekraut", []),
    "Eriobotrya": ("wollmispel", []), "Erythrina": ("korallenbaum", []),
    "Eucalyptus": ("eukalyptus", []), "Eugenia": ("kirschmyrte", []),
    "Fagus": ("buche", []), "Ficus": ("feige", ["gummibaum"]), "Foeniculum": ("fenchel", []),
    "Fragaria": ("erdbeere", []), "Fraxinus": ("esche", []), "Ginkgo": ("ginkgobaum", []),
    "Gleditsia": ("gleditschie", []), "Glycine": ("sojabohne", []),
    "Gossypium": ("baumwolle", []), "Grevillea": ("silbereiche", []),
    "Guazuma": ("bastardzeder", []), "Hevea": ("kautschukbaum", []),
    "Hibiscus": ("hibiskus", ["eibisch"]), "Hordeum": ("gerste", []),
    "Hymenaea": ("heuschreckenbaum", []), "Ilex": ("stechpalme", ["mate"]),
    "Inga": ("inga-bohne", []), "Ipomoea": ("süßkartoffel", []), "Jacaranda": ("palisanderbaum", []),
    "Jasminum": ("jasmin", []), "Juglans": ("walnuss", []), "Juniperus": ("wacholder", []),
    "Khaya": ("afrikanisches mahagoni", []), "Lablab": ("helmbone", []),
    "Lactuca": ("salat", []), "Larix": ("lärche", []), "Laurus": ("lorbeer", []),
    "Lavandula": ("lavendel", []), "Lens": ("linse", []), "Leucaena": ("leucaena", []),
    "Ligustrum": ("liguster", []), "Linum": ("flachs", ["lein"]),
    "Liquidambar": ("amberbaum", []), "Liriodendron": ("tulpenbaum", []),
    "Litchi": ("litschi", []), "Lolium": ("weidelgras", []), "Lupinus": ("lupine", []),
    "Macadamia": ("macadamia", []), "Magnolia": ("magnolie", []), "Malus": ("apfelbaum", []),
    "Mangifera": ("mangobaum", []), "Manihot": ("maniok", []), "Medicago": ("luzerne", []),
    "Melaleuca": ("teebaum", []), "Melia": ("zedrachbaum", []), "Mentha": ("minze", []),
    "Morus": ("maulbeerbaum", []), "Musa": ("bananenstaude", []), "Myrtus": ("myrte", []),
    "Nicotiana": ("tabak", []), "Olea": ("ölbaum", ["olivenbaum"]),
    "Opuntia": ("feigenkaktus", []), "Origanum": ("oregano", ["majoran"]),
    "Oryza": ("reis", []), "Panicum": ("hirse", []), "Passiflora": ("passionsblume", []),
    "Paulownia": ("blauglockenbaum", []), "Pennisetum": ("lampenputzergras", []),
    "Persea": ("avocadobaum", []), "Petroselinum": ("petersilie", []),
    "Phaseolus": ("bohne", []), "Phoenix": ("dattelpalme", []), "Picea": ("fichte", []),
    "Pinus": ("kiefer", ["föhre"]), "Piper": ("pfeffer", []), "Pistacia": ("pistazie", []),
    "Pisum": ("erbse", []), "Platanus": ("platane", []), "Poa": ("rispengras", []),
    "Populus": ("pappel", []), "Prosopis": ("mesquite", []),
    "Prunus": ("steinobstbaum", ["kirsche", "pflaume", "mandel"]),
    "Pseudotsuga": ("douglasie", []), "Psidium": ("guave", []), "Punica": ("granatapfel", []),
    "Pyrus": ("birnbaum", []), "Quercus": ("eiche", []), "Raphanus": ("rettich", ["radieschen"]),
    "Rhus": ("essigbaum", ["sumach"]), "Ribes": ("johannisbeere", ["stachelbeere"]),
    "Ricinus": ("rizinus", []), "Robinia": ("robinie", ["falsche akazie"]),
    "Rosa": ("rose", []), "Rosmarinus": ("rosmarin", []), "Rubus": ("brombeere", ["himbeere"]),
    "Saccharum": ("zuckerrohr", []), "Salix": ("weide", []), "Salvia": ("salbei", []),
    "Sambucus": ("holunder", []), "Schinus": ("pfefferbaum", []), "Secale": ("roggen", []),
    "Senna": ("senna", []), "Sequoia": ("küstenmammutbaum", []),
    "Sequoiadendron": ("riesenmammutbaum", []), "Sesamum": ("sesam", []),
    "Sesbania": ("sesbanie", []), "Solanum": ("nachtschatten", ["kartoffel", "tomate", "aubergine"]),
    "Sorghum": ("hirse", ["sorghum"]), "Spinacia": ("spinat", []),
    "Swietenia": ("mahagoni", []), "Syzygium": ("gewürznelke", []),
    "Tagetes": ("studentenblume", []), "Tamarindus": ("tamarinde", []),
    "Tamarix": ("tamarTrue", ["tamariske"]), "Taxodium": ("sumpfzypresse", []),
    "Taxus": ("eibe", []), "Tectona": ("teakbaum", []), "Terminalia": ("myrobalane", []),
    "Theobroma": ("kakaobaum", []), "Thuja": ("lebensbaum", ["thuja"]),
    "Thymus": ("thymian", []), "Tilia": ("linde", []), "Trifolium": ("klee", []),
    "Triticum": ("weizen", []), "Tsuga": ("hemlocktanne", []), "Ulmus": ("ulme", []),
    "Vaccinium": ("heidelbeere", ["preiselbeere"]), "Vanilla": ("vanille", []),
    "Vicia": ("wicke", ["ackerbohne"]), "Vigna": ("augenbohne", []),
    "Vitex": ("mönchspfeffer", []), "Vitis": ("weinrebe", []), "Zea": ("mais", []),
    "Zingiber": ("ingwer", []), "Ziziphus": ("jujube", [])
}

GENUS_RU = {
    "Abelmoschus": ("бамия", []), "Abies": ("пихта", []), "Acacia": ("акация", ["мимоза"]),
    "Acer": ("клён", []), "Acrocarpus": ("акрокарпус", []), "Actinidia": ("актинидия", ["киви"]),
    "Adansonia": ("баобаб", []), "Adenanthera": ("аденантера", []), "Aegle": ("баэль", []),
    "Aesculus": ("конский каштан", []), "Afzelia": ("афзелия", []), "Agathis": ("агатис", []),
    "Agave": ("агава", []), "Albizia": ("альбиция", []), "Allium": ("лук/чеснок", []),
    "Alnus": ("ольха", []), "Aloe": ("алоэ", []), "Aloysia": ("вербена лимонная", []),
    "Amaranthus": ("амарант", []), "Anacardium": ("кешью", ["анакардиум"]),
    "Ananas": ("ананас", []), "Annona": ("аннона", ["гравиола"]),
    "Arachis": ("арахис", []), "Araucaria": ("араукария", []), "Arbutus": ("земляничное дерево", []),
    "Artocarpus": ("хлебное дерево", ["джекфрут"]), "Asparagus": ("спаржа", []),
    "Astragalus": ("астрагал", []), "Avena": ("овёс", []), "Azadirachta": ("ним", []),
    "Bambusa": ("бамбук", []), "Beta": ("свёкла", []), "Betula": ("берёза", []),
    "Brassica": ("капуста/горчица/рапс", []), "Cajanus": ("голубиный горох", []),
    "Camellia": ("камелия", ["чайный куст"]), "Cannabis": ("конопля", []),
    "Capsicum": ("перец стручковый", []), "Carica": ("папайя", []), "Carpinus": ("граб", []),
    "Carya": ("пекан", ["гикори"]), "Cassia": ("кассия", []), "Castanea": ("каштан", []),
    "Casuarina": ("казуарина", []), "Catalpa": ("катальпа", []), "Cedrela": ("цедрела", []),
    "Cedrus": ("кедр", []), "Celtis": ("каркас", []), "Ceratonia": ("рожковое дерево", []),
    "Cercis": ("иудино дерево", ["церцис"]), "Chamaecyparis": ("кипарисовик", []),
    "Cicer": ("нут", []), "Cinnamomum": ("коричник", ["камфорное дерево"]),
    "Citrus": ("цитрус", ["лимон", "апельсин"]), "Cocos": ("кокосовая пальма", []),
    "Coffea": ("кофейное дерево", []), "Corylus": ("лещина", ["фундук"]),
    "Cucumis": ("огурец/дыня", []), "Cucurbita": ("тыква", []), "Cupressus": ("кипарис", []),
    "Cydonia": ("айва", []), "Dalbergia": ("палисандр", []), "Daucus": ("морковь", []),
    "Diospyros": ("хурма", ["эбеновое дерево"]), "Elaeis": ("масличная пальма", []),
    "Erica": ("эрика", ["вереск"]), "Eriobotrya": ("мушмула японская", []),
    "Eucalyptus": ("эвкалипт", []), "Eugenia": ("эвгения", []), "Fagus": ("бук", []),
    "Ficus": ("инжир", ["фикус"]), "Foeniculum": ("фенхель", []), "Fragaria": ("земляника", ["клубника"]),
    "Fraxinus": ("ясень", []), "Ginkgo": ("гинкго", []), "Gleditsia": ("гледичия", []),
    "Glycine": ("соя", []), "Gossypium": ("хлопчатник", []), "Grevillea": ("гревиллея", []),
    "Hevea": ("гевея", ["каучуковое дерево"]), "Hibiscus": ("гибискус", []),
    "Hordeum": ("ячмень", []), "Ilex": ("падуб", ["мате"]), "Ipomoea": ("батат", []),
    "Jacaranda": ("жакаранда", []), "Jasminum": ("жасмин", []), "Juglans": ("орех", ["грецкий орех"]),
    "Juniperus": ("можжевельник", []), "Lactuca": ("салат", []), "Larix": ("лиственница", []),
    "Laurus": ("лавр", []), "Lavandula": ("лаванда", []), "Lens": ("чечевица", []),
    "Leucaena": ("леуцена", []), "Ligustrum": ("бирючина", []), "Linum": ("лён", []),
    "Liquidambar": ("ликвидамбар", []), "Liriodendron": ("тюльпанное дерево", []),
    "Lolium": ("райграс", []), "Lupinus": ("люпин", []), "Macadamia": ("макадамия", []),
    "Magnolia": ("магнолия", []), "Malus": ("яблоня", []), "Mangifera": ("манго", []),
    "Manihot": ("маниок", []), "Medicago": ("люцерна", []), "Melaleuca": ("чайное дерево", []),
    "Melia": ("мелия", []), "Mentha": ("мята", []), "Morus": ("шелковица", []),
    "Musa": ("банан", []), "Myrtus": ("мирт", []), "Nicotiana": ("табак", []),
    "Olea": ("олива", ["маслина"]), "Opuntia": ("опунция", []), "Origanum": ("душица", ["орегано"]),
    "Oryza": ("рис", []), "Panicum": ("просо", []), "Passiflora": ("маракуйя", ["страстоцвет"]),
    "Paulownia": ("павловния", []), "Persea": ("авокадо", []), "Petroselinum": ("петрушка", []),
    "Phaseolus": ("фасоль", []), "Phoenix": ("финиковая пальма", []), "Picea": ("ель", []),
    "Pinus": ("сосна", []), "Piper": ("перец", []), "Pistacia": ("фисташка", []),
    "Pisum": ("горох", []), "Platanus": ("платан", ["чинара"]), "Populus": ("тополь", ["осина"]),
    "Prosopis": ("мескито", []), "Prunus": ("слива/вишня/персик/миндаль", []),
    "Pseudotsuga": ("псевдотсуга", ["дугласия"]), "Psidium": ("гуава", []),
    "Punica": ("гранат", []), "Pyrus": ("груша", []), "Quercus": ("дуб", []),
    "Raphanus": ("редис", ["редька"]), "Rhus": ("сумах", []), "Ribes": ("смородина", ["крыжовник"]),
    "Ricinus": ("клещевина", []), "Robinia": ("робиния", ["белая акация"]),
    "Rosa": ("роза", ["шиповник"]), "Rosmarinus": ("розмарин", []),
    "Rubus": ("ежевика", ["малина"]), "Saccharum": ("сахарный тростник", []),
    "Salix": ("ива", ["верба"]), "Salvia": ("шалфей", []), "Sambucus": ("бузина", []),
    "Secale": ("рожь", []), "Sequoia": ("секвойя", []), "Sequoiadendron": ("секвойядендрон", []),
    "Sesamum": ("кунжут", []), "Solanum": ("паслён", ["картофель", "томат", "баклажан"]),
    "Sorghum": ("сорго", []), "Spinacia": ("шпинат", []), "Swietenia": ("махагони", []),
    "Syzygium": ("гвоздичное дерево", []), "Tamarindus": ("тамаринд", []),
    "Tamarix": ("тамариск", []), "Taxodium": ("болотный кипарис", []), "Taxus": ("тис", []),
    "Tectona": ("тик", []), "Theobroma": ("какао", []), "Thuja": ("туя", []),
    "Thymus": ("тимьян", ["чабрец"]), "Tilia": ("липа", []), "Trifolium": ("клевер", []),
    "Triticum": ("пшеница", []), "Tsuga": ("тсуга", []), "Ulmus": ("вяз", ["ильм"]),
    "Vaccinium": ("черника", ["брусника", "клюква"]), "Vanilla": ("ваниль", []),
    "Vicia": ("горошек", ["вика"]), "Vigna": ("вигна", []), "Vitis": ("виноград", []),
    "Zea": ("кукуруза", []), "Zingiber": ("имбирь", []), "Ziziphus": ("зизифус", ["унаби"])
}

GENUS_ZH = {
    "Abelmoschus": ("秋葵", []), "Abies": ("冷杉", []), "Acacia": ("金合欢", ["相思树"]),
    "Acer": ("槭树", ["枫树"]), "Acrocarpus": ("顶果木", []), "Actinidia": ("猕猴桃", []),
    "Adansonia": ("猴面包树", []), "Adenanthera": ("海红豆", []), "Aegle": ("木橘", []),
    "Aesculus": ("七叶树", []), "Afzelia": ("非洲楝", []), "Agathis": ("贝壳杉", []),
    "Agave": ("龙舌兰", []), "Albizia": ("合欢", []), "Allium": ("葱/蒜/洋葱", []),
    "Alnus": ("桤木", []), "Aloe": ("芦荟", []), "Aloysia": ("柠檬马鞭草", []),
    "Amaranthus": ("苋菜", []), "Anacardium": ("腰果", []), "Ananas": ("菠萝", ["凤梨"]),
    "Annona": ("番荔枝", []), "Arachis": ("花生", []), "Araucaria": ("南洋杉", []),
    "Arbutus": ("草莓树", []), "Artocarpus": ("木波罗", ["面包树", "菠萝蜜"]),
    "Asparagus": ("芦笋", []), "Avena": ("燕麦", []), "Azadirachta": ("印楝", []),
    "Bambusa": ("竹", []), "Beta": ("甜菜", []), "Betula": ("桦木", ["白桦"]),
    "Brassica": ("芸薹属", ["白菜", "油菜", "芥菜"]), "Cajanus": ("木豆", []),
    "Camellia": ("山茶", ["茶树"]), "Cannabis": ("大麻", []), "Capsicum": ("辣椒", []),
    "Carica": ("番木瓜", ["木瓜"]), "Carpinus": ("鹅耳枥", []), "Carya": ("山核桃", ["碧根果"]),
    "Cassia": ("决明", ["腊肠树"]), "Castanea": ("栗", ["板栗"]), "Casuarina": ("木麻黄", []),
    "Catalpa": ("梓树", []), "Cedrus": ("雪松", []), "Celtis": ("朴树", []),
    "Ceratonia": ("长角豆", []), "Cercis": ("紫荆", []), "Chamaecyparis": ("扁柏", []),
    "Cicer": ("鹰嘴豆", []), "Cinnamomum": ("樟属", ["肉桂", "樟树"]),
    "Citrus": ("柑橘", ["柠檬", "甜橙"]), "Cocos": ("椰子", []), "Coffea": ("咖啡", []),
    "Corylus": ("榛", ["榛子"]), "Cucumis": ("黄瓜/甜瓜", []), "Cucurbita": ("南瓜", []),
    "Cupressus": ("柏木", []), "Cydonia": ("榅桲", []), "Dalbergia": ("黄檀", ["红木"]),
    "Daucus": ("胡萝卜", []), "Diospyros": ("柿树", ["乌木"]), "Elaeis": ("油棕", []),
    "Erica": ("欧石楠", []), "Eriobotrya": ("枇杷", []), "Eucalyptus": ("桉树", []),
    "Eugenia": ("蒲桃", []), "Fagus": ("水青冈", ["山毛榉"]), "Ficus": ("榕属", ["无花果"]),
    "Foeniculum": ("茴香", []), "Fragaria": ("草莓", []), "Fraxinus": ("白蜡树", []),
    "Ginkgo": ("银杏", []), "Gleditsia": ("皂荚", []), "Glycine": ("大豆", []),
    "Gossypium": ("棉花", []), "Grevillea": ("银桦", []), "Hevea": ("橡胶树", []),
    "Hibiscus": ("木槿", ["扶桑"]), "Hordeum": ("大麦", []), "Ilex": ("冬青", []),
    "Ipomoea": ("甘薯", ["红薯"]), "Jacaranda": ("蓝花楹", []), "Jasminum": ("素馨", ["茉莉"]),
    "Juglans": ("核桃", ["胡桃"]), "Juniperus": ("刺柏", ["圆柏"]), "Lactuca": ("莴苣", ["生菜"]),
    "Larix": ("落叶松", []), "Laurus": ("月桂", []), "Lavandula": ("薰衣草", []),
    "Lens": ("兵豆", []), "Leucaena": ("银合欢", []), "Ligustrum": ("女贞", []),
    "Linum": ("亚麻", []), "Liquidambar": ("枫香树", []), "Liriodendron": ("鹅掌楸", []),
    "Litchi": ("荔枝", []), "Lolium": ("黑麦草", []), "Lupinus": ("羽扇豆", ["鲁冰花"]),
    "Macadamia": ("澳洲坚果", []), "Magnolia": ("木兰", []), "Malus": ("苹果", []),
    "Mangifera": ("芒果", []), "Manihot": ("木薯", []), "Medicago": ("苜蓿", []),
    "Melaleuca": ("白千层", []), "Melia": ("楝树", []), "Mentha": ("薄荷", []),
    "Morus": ("桑树", []), "Musa": ("芭蕉", ["香蕉"]), "Myrtus": ("香桃木", []),
    "Nicotiana": ("烟草", []), "Olea": ("木犀榄", ["油橄榄"]), "Opuntia": ("仙人掌", []),
    "Oryza": ("稻", ["水稻"]), "Panicum": ("黍", []), "Passiflora": ("西番莲", []),
    "Paulownia": ("泡桐", []), "Persea": ("鳄梨", ["牛油果"]), "Petroselinum": ("欧芹", []),
    "Phaseolus": ("菜豆", []), "Phoenix": ("刺葵", ["海枣"]), "Picea": ("云杉", []),
    "Pinus": ("松树", []), "Piper": ("胡椒", []), "Pistacia": ("黄连木", ["开心果"]),
    "Pisum": ("豌豆", []), "Platanus": ("悬铃木", []), "Populus": ("杨树", []),
    "Prosopis": ("牧豆树", []), "Prunus": ("李属", ["桃", "李", "杏", "樱桃"]),
    "Pseudotsuga": ("黄杉", []), "Psidium": ("番石榴", []), "Punica": ("石榴", []),
    "Pyrus": ("梨", []), "Quercus": ("栎树", ["橡树"]), "Raphanus": ("萝卜", []),
    "Rhus": ("盐肤木", ["漆树"]), "Ribes": ("茶藨子", []), "Ricinus": ("蓖麻", []),
    "Robinia": ("刺槐", ["洋槐"]), "Rosa": ("蔷薇", ["玫瑰", "月季"]),
    "Rosmarinus": ("迷迭香", []), "Rubus": ("悬钩子", ["黑莓", "树莓"]),
    "Saccharum": ("甘蔗", []), "Salix": ("柳树", []), "Salvia": ("鼠尾草", []),
    "Sambucus": ("接骨木", []), "Secale": ("黑麦", []), "Sequoia": ("红杉", []),
    "Sequoiadendron": ("巨杉", []), "Sesamum": ("芝麻", []), "Solanum": ("茄属", ["番茄", "马铃薯", "茄子"]),
    "Sorghum": ("高粱", []), "Spinacia": ("菠菜", []), "Swietenia": ("桃花心木", []),
    "Syzygium": ("蒲桃", ["丁香"]), "Tamarindus": ("酸豆", ["罗望子"]),
    "Taxodium": ("落羽杉", []), "Taxus": ("红豆杉", []), "Tectona": ("柚木", []),
    "Theobroma": ("可可树", []), "Thuja": ("崖柏", []), "Thymus": ("百里香", []),
    "Tilia": ("椴树", []), "Trifolium": ("三叶草", ["车轴草"]), "Triticum": ("小麦", []),
    "Tsuga": ("铁杉", []), "Ulmus": ("榆树", []), "Vaccinium": ("越橘", ["蓝莓"]),
    "Vanilla": ("香草", []), "Vicia": ("野豌豆", []), "Vigna": ("豇豆", []),
    "Vitis": ("葡萄", []), "Zea": ("玉米", []), "Zingiber": ("姜", []), "Ziziphus": ("枣", [])
}

GENUS_JA = {
    "Abelmoschus": ("オクラ", []), "Abies": ("モミ", []), "Acacia": ("アカシア", []),
    "Acer": ("カエデ", ["モミジ"]), "Actinidia": ("キウイフルーツ", []), "Adansonia": ("バオバブ", []),
    "Aesculus": ("トチノキ", []), "Agathis": ("コウヤマキ", []), "Agave": ("リュウゼツラン", []),
    "Albizia": ("ネムノキ", []), "Allium": ("ネギ属", ["タマネギ", "ニンニク"]),
    "Alnus": ("ハンノキ", []), "Aloe": ("アロエ", []), "Amaranthus": ("アマランサス", []),
    "Anacardium": ("カシューナットノキ", []), "Ananas": ("パイナップル", []),
    "Annona": ("バンレイシ", []), "Arachis": ("ラッカセイ", []), "Araucaria": ("ナンヨウスギ", []),
    "Arbutus": ("イチゴノキ", []), "Artocarpus": ("パンノキ", ["ジャックフルーツ"]),
    "Asparagus": ("アスパラガス", []), "Avena": ("エンバク", []), "Azadirachta": ("インドセンダン", []),
    "Bambusa": ("タケ", []), "Beta": ("テンサイ", []), "Betula": ("カバノキ", ["シラカバ"]),
    "Brassica": ("アブラナ属", ["キャベツ", "ハクサイ"]), "Camellia": ("ツバキ", ["チャノキ"]),
    "Cannabis": ("アサ", []), "Capsicum": ("トウガラシ", []), "Carica": ("パパイア", []),
    "Carpinus": ("シデ", []), "Carya": ("ヒッコリー", ["ペカン"]), "Castanea": ("クリ", []),
    "Casuarina": ("モクマオウ", []), "Cedrus": ("ヒマラヤスギ", []), "Celtis": ("エノキ", []),
    "Ceratonia": ("イナゴマメ", []), "Cercis": ("ハナズオウ", []), "Chamaecyparis": ("ヒノキ", []),
    "Cicer": ("ヒヨコマメ", []), "Cinnamomum": ("クスノキ属", ["ニッケイ"]),
    "Citrus": ("カンキツ類", ["ミカン", "レモン"]), "Cocos": ("ココヤシ", []),
    "Coffea": ("コーヒーノキ", []), "Corylus": ("ハシバミ", []), "Cucumis": ("キュウリ/メロン", []),
    "Cucurbita": ("カボチャ", []), "Cupressus": ("イトスギ", []), "Cydonia": ("マルメロ", []),
    "Dalbergia": ("シタン", ["ローズウッド"]), "Daucus": ("ニンジン", []),
    "Diospyros": ("カキノキ", []), "Elaeis": ("アブラヤシ", []), "Erica": ("エリカ", []),
    "Eriobotrya": ("ビワ", []), "Eucalyptus": ("ユーカリ", []), "Fagus": ("ブナ", []),
    "Ficus": ("イチジク属", ["ゴムノキ"]), "Foeniculum": ("ウイキョウ", []),
    "Fragaria": ("イチゴ", []), "Fraxinus": ("トネリコ", []), "Ginkgo": ("イチョウ", []),
    "Gleditsia": ("サイカチ", []), "Glycine": ("ダイズ", []), "Gossypium": ("ワタ", []),
    "Grevillea": ("ハゴロモノキ", []), "Hevea": ("パラゴムノキ", []), "Hibiscus": ("ハイビスカス", []),
    "Hordeum": ("オオムギ", []), "Ilex": ("モチノキ属", []), "Ipomoea": ("サツマイモ", []),
    "Jacaranda": ("ジャカランダ", []), "Jasminum": ("ジャスミン", []), "Juglans": ("クルミ", []),
    "Juniperus": ("ビャクシン", ["ネズ"]), "Lactuca": ("レタス", []), "Larix": ("カラマツ", []),
    "Laurus": ("ゲッケイジュ", []), "Lavandula": ("ラベンダー", []), "Lens": ("レンズマメ", []),
    "Leucaena": ("ギンネム", []), "Ligustrum": ("イボタノキ", []), "Linum": ("アマ", []),
    "Liquidambar": ("フウ", []), "Liriodendron": ("ユリノキ", []), "Litchi": ("レイシ", []),
    "Lolium": ("ドクムギ", []), "Lupinus": ("ルピナス", []), "Macadamia": ("マカダミア", []),
    "Magnolia": ("モクレン", []), "Malus": ("リンゴ", []), "Mangifera": ("マンゴー", []),
    "Manihot": ("キャッサバ", []), "Medicago": ("ウマゴヤシ", ["アルファルファ"]),
    "Melaleuca": ("メラレウカ", ["ティーツリー"]), "Melia": ("センダン", []), "Mentha": ("ハッカ", []),
    "Morus": ("クワ", []), "Musa": ("バショウ", ["バナナ"]), "Myrtus": ("ギンバイカ", []),
    "Nicotiana": ("タバコ", []), "Olea": ("オリーブ", []), "Opuntia": ("ウチワサボテン", []),
    "Oryza": ("イネ", []), "Panicum": ("キビ", []), "Passiflora": ("トケイソウ", []),
    "Paulownia": ("キリ", []), "Persea": ("アボカド", []), "Petroselinum": ("パセリ", []),
    "Phaseolus": ("インゲンマメ", []), "Phoenix": ("ナツメヤシ", []), "Picea": ("トウヒ", []),
    "Pinus": ("マツ", []), "Piper": ("コショウ", []), "Pistacia": ("ピスタチオ", []),
    "Pisum": ("エンドウ", []), "Platanus": ("スズカケノキ", []), "Populus": ("ポプラ", []),
    "Prosopis": ("プロソピス", []), "Prunus": ("サクラ属", ["モモ", "スモモ", "アンズ"]),
    "Pseudotsuga": ("トガサワラ", []), "Psidium": ("グアバ", []), "Punica": ("ザクロ", []),
    "Pyrus": ("ナシ", []), "Quercus": ("ナラ", ["カシ", "オーク"]), "Raphanus": ("ダイコン", []),
    "Rhus": ("ウルシ", []), "Ribes": ("スグリ", []), "Ricinus": ("トウゴマ", []),
    "Robinia": ("ハリエンジュ", ["ニセアカシア"]), "Rosa": ("バラ", []),
    "Rosmarinus": ("ローズマリー", []), "Rubus": ("キイチゴ", []),
    "Saccharum": ("サトウキビ", []), "Salix": ("ヤナギ", []), "Salvia": ("サルビア", []),
    "Sambucus": ("ニワトコ", []), "Secale": ("ライムギ", []), "Sequoia": ("セコイア", []),
    "Sequoiadendron": ("セコイアデンドロン", []), "Sesamum": ("ゴマ", []),
    "Solanum": ("ナス属", ["トマト", "ジャガイモ", "ナス"]), "Sorghum": ("モロコシ", []),
    "Spinacia": ("ホウレンソウ", []), "Swietenia": ("マホガニー", []),
    "Syzygium": ("フトモモ", ["チョウジ"]), "Tamarindus": ("タマリンド", []),
    "Taxodium": ("ラクウショウ", []), "Taxus": ("イチイ", []), "Tectona": ("チーク", []),
    "Theobroma": ("カカオ", []), "Thuja": ("ネズコ", []), "Thymus": ("タイム", []),
    "Tilia": ("ボダイジュ", []), "Trifolium": ("シャジクソウ", ["クローバー"]),
    "Triticum": ("コムギ", []), "Tsuga": ("ツガ", []), "Ulmus": ("ニレ", []),
    "Vaccinium": ("スノキ", ["ブルーベリー"]), "Vanilla": ("バニラ", []),
    "Vicia": ("ソラマメ属", []), "Vigna": ("ササゲ", []), "Vitis": ("ブドウ", []),
    "Zea": ("トウモロコシ", []), "Zingiber": ("ショウガ", []), "Ziziphus": ("ナツメ", [])
}

GENUS_ID = {
    "Abelmoschus": ("okra", []), "Abies": ("cemara fir", []), "Acacia": ("akasia", []),
    "Acer": ("maple", []), "Actinidia": ("kiwi", []), "Adansonia": ("baobab", []),
    "Albizia": ("sengon", []), "Allium": ("bawang", []), "Alnus": ("alder", []),
    "Aloe": ("lidah buaya", []), "Amaranthus": ("bayam", []), "Anacardium": ("jambu mete", []),
    "Ananas": ("nanas", []), "Annona": ("sirsak/srikaya", []), "Arachis": ("kacang tanah", []),
    "Araucaria": ("araucaria", []), "Artocarpus": ("nangka/sukun", []), "Avena": ("havermut", []),
    "Azadirachta": ("mimba", []), "Bambusa": ("bambu", []), "Beta": ("bit", []),
    "Betula": ("birch", []), "Brassica": ("sawi/kol", []), "Cajanus": ("kacang gude", []),
    "Camellia": ("teh/kamellia", []), "Cannabis": ("ganja", []), "Capsicum": ("cabai", []),
    "Carica": ("pepaya", []), "Carpinus": ("hornbeam", []), "Carya": ("pecan", []),
    "Cassia": ("trengguli", []), "Castanea": ("kastanya", []), "Casuarina": ("cemara laut", []),
    "Cedrus": ("cedar", []), "Cinnamomum": ("kayu manis", []), "Citrus": ("jeruk", []),
    "Cocos": ("kelapa", []), "Coffea": ("kopi", []), "Corylus": ("hazelnut", []),
    "Cucumis": ("mentimun/melon", []), "Cucurbita": ("labu kuning", []), "Cupressus": ("cypress", []),
    "Dalbergia": ("sonokeling", []), "Daucus": ("wortel", []), "Diospyros": ("kesemek", []),
    "Elaeis": ("kelapa sawit", []), "Eucalyptus": ("eukaliptus", ["kayu putih"]),
    "Eugenia": ("jambu air", []), "Fagus": ("beech", []), "Ficus": ("beringin/ara", []),
    "Fragaria": ("stroberi", []), "Fraxinus": ("ash", []), "Ginkgo": ("ginkgo", []),
    "Glycine": ("kedelai", []), "Gossypium": ("kapas", []), "Hevea": ("karet", []),
    "Hibiscus": ("kembang sepatu", []), "Hordeum": ("jelai", []), "Ipomoea": ("ubi jalar", []),
    "Jacaranda": ("jacaranda", []), "Jasminum": ("melati", []), "Juglans": ("kenari", []),
    "Juniperus": ("juniper", []), "Lactuca": ("selada", []), "Larix": ("larch", []),
    "Laurus": ("daun salam", []), "Lavandula": ("lavender", []), "Lens": ("mika", []),
    "Leucaena": ("lamtoro", ["petai cina"]), "Linum": ("rami", []), "Litchi": ("leci", []),
    "Magnolia": ("cempaka", []), "Malus": ("apel", []), "Mangifera": ("mangga", []),
    "Manihot": ("singkong", []), "Medicago": ("alfalfa", []), "Melaleuca": ("kayu putih", []),
    "Mentha": ("mint", []), "Morus": ("murbei", []), "Musa": ("pisang", []),
    "Myrtus": ("myrtle", []), "Nicotiana": ("tembakau", []), "Olea": ("zaitun", []),
    "Oryza": ("padi", []), "Passiflora": ("markisa", []), "Persea": ("alpukat", []),
    "Petroselinum": ("peterseli", []), "Phaseolus": ("buncis/kacang merah", []),
    "Phoenix": ("kurma", []), "Picea": ("spruce", []), "Pinus": ("pinus", ["tusam"]),
    "Piper": ("lada", []), "Pistacia": ("pistachio", []), "Pisum": ("kacang polong", []),
    "Platanus": ("platanus", []), "Populus": ("poplar", []), "Prunus": ("plum/persik/ceri", []),
    "Psidium": ("jambu biji", []), "Punica": ("delima", []), "Pyrus": ("pir", []),
    "Quercus": ("pohon ek", []), "Raphanus": ("lobak", []), "Ricinus": ("jarak", []),
    "Robinia": ("akasia semu", []), "Rosa": ("mawar", []), "Rosmarinus": ("rosemary", []),
    "Rubus": ("frambos/blackberry", []), "Saccharum": ("tebu", []), "Salix": ("dedalu", []),
    "Sesamum": ("wijen", []), "Solanum": ("tomat/kentang/terung", []), "Sorghum": ("sorgum", []),
    "Spinacia": ("bayam jepang", []), "Swietenia": ("mahoni", []), "Syzygium": ("cengkih", []),
    "Tamarindus": ("asam jawa", []), "Taxus": ("yew", []), "Tectona": ("jati", []),
    "Theobroma": ("kakao", []), "Thymus": ("thyme", []), "Trifolium": ("semanggi", []),
    "Triticum": ("gandum", []), "Ulmus": ("elm", []), "Vanilla": ("vanili", []),
    "Vicia": ("kacang babi", []), "Vigna": ("kacang tunggak", []), "Vitis": ("anggur", []),
    "Zea": ("jagung", []), "Zingiber": ("jahe", []), "Ziziphus": ("bidara", [])
}

GENUS_HI = {
    "Abelmoschus": ("भिंडी", []), "Abies": ("सनोबर/देवदार", []), "Acacia": ("बबूल", ["कीकर"]),
    "Acer": ("मैपल", []), "Actinidia": ("कीवी", []), "Adansonia": ("कल्पवृक्ष", ["बाओबाब"]),
    "Albizia": ("सिरस", []), "Allium": ("प्याज़/लहसुन", []), "Aloe": ("घृतकुमारी", ["एलोवेरा"]),
    "Amaranthus": ("चौलाई", []), "Anacardium": ("काजू", []), "Ananas": ("अनानास", []),
    "Annona": ("शरीफा/सीताफल", []), "Arachis": ("मूंगफली", []), "Artocarpus": ("कटहल", []),
    "Avena": ("जई", []), "Azadirachta": ("नीम", []), "Bambusa": ("बांस", []),
    "Beta": ("चुकंदर", []), "Betula": ("भोजपत्र", []), "Brassica": ("सरसों/पत्तागोभी", []),
    "Cajanus": ("अरहर", []), "Camellia": ("चाय/कैमेलिया", []), "Cannabis": ("भांग", []),
    "Capsicum": ("मिर्च/शिमला मिर्च", []), "Carica": ("पपीता", []), "Carya": ("हिकॉरी", []),
    "Cassia": ("अमलतास", []), "Castanea": ("शाहबलूत", []), "Casuarina": ("झाऊ", []),
    "Cedrus": ("देवदार", []), "Cinnamomum": ("दालचीनी/कपूर", []), "Citrus": ("नींबू/संतरा", []),
    "Cocos": ("नारियल", []), "Coffea": ("कॉफी", []), "Corylus": ("हेज़लनट", []),
    "Cucumis": ("खीरा/खरबूजा", []), "Cucurbita": ("कद्दू/लौकी", []), "Cupressus": ("सरू", []),
    "Dalbergia": ("शीशम", []), "Daucus": ("गाजर", []), "Diospyros": ("तेंदू", []),
    "Elaeis": ("ताड़ का तेल", []), "Eucalyptus": ("यूकेलिप्टस", ["सफेदा"]),
    "Eugenia": ("जामुन", []), "Ficus": ("पीपल/बरगद/अंजीर", []), "Foeniculum": ("सौंफ", []),
    "Fragaria": ("स्ट्रॉबेरी", []), "Fraxinus": ("राख वृक्ष", []), "Ginkgo": ("जिन्कगो", []),
    "Glycine": ("सोयाबीन", []), "Gossypium": ("कपास", []), "Hevea": ("रबड़ का पेड़", []),
    "Hibiscus": ("गुड़हल", []), "Hordeum": ("जौ", []), "Ipomoea": ("शकरकंद", []),
    "Jacaranda": ("नीली गुलमोहर", []), "Jasminum": ("चमेली", []), "Juglans": ("अखरोट", []),
    "Juniperus": ("हाऊबेर", []), "Lactuca": ("सलाद पत्ता", []), "Larix": ("लार्च", []),
    "Laurus": ("तेजपत्ता", []), "Lavandula": ("लैवेंडर", []), "Lens": ("मसूर", []),
    "Leucaena": ("सुबबूल", []), "Linum": ("अलसी", []), "Litchi": ("लीची", []),
    "Magnolia": ("चंपा", []), "Malus": ("सेब", []), "Mangifera": ("आम", []),
    "Manihot": ("कसावा", ["टैपिओका"]), "Medicago": ("रिजका", ["अल्फाल्फा"]),
    "Mentha": ("पुदीना", []), "Morus": ("शहतूत", []), "Musa": ("केला", []),
    "Nicotiana": ("तंबाकू", []), "Olea": ("जैतून", []), "Opuntia": ("नागफनी", []),
    "Oryza": ("चावल/धान", []), "Panicum": ("बाजरा/सांवा", []), "Passiflora": ("कृष्णकमल", []),
    "Persea": ("एवोकैडो", []), "Petroselinum": ("अजमोद", []), "Phaseolus": ("राजमा/सेम", []),
    "Phoenix": ("खजूर", []), "Pinus": ("चीड़", []), "Piper": ("काली मिर्च", []),
    "Pistacia": ("पिस्ता", []), "Pisum": ("मटर", []), "Platanus": ("चिनार", []),
    "Populus": ("पॉपलर", []), "Prunus": ("आड़ू/आलूबुखारा/बादाम", []),
    "Psidium": ("अमरूद", []), "Punica": ("अनार", []), "Pyrus": ("नाशपाती", []),
    "Quercus": ("शाहबलूत", ["ओक"]), "Raphanus": ("मूली", []), "Ricinus": ("अरंडी", []),
    "Robinia": ("सफेद कीकर", []), "Rosa": ("गुलाब", []), "Rosmarinus": ("रोज़मेरी", []),
    "Saccharum": ("गन्ना", []), "Salix": ("बेंत", []), "Sesamum": ("तिल", []),
    "Solanum": ("टमाटर/आलू/बैंगन", []), "Sorghum": ("ज्वार", []), "Spinacia": ("पालक", []),
    "Swietenia": ("महोगनी", []), "Syzygium": ("जामुन/लौंग", []), "Tamarindus": ("इमली", []),
    "Taxus": ("तालीसपत्र", []), "Tectona": ("सागौन", ["सागवान"]), "Theobroma": ("कोको", []),
    "Thymus": ("अजवाइन के फूल", []), "Trifolium": ("तिपतिया घास", []), "Triticum": ("गेहूं", []),
    "Ulmus": ("एल्म", []), "Vanilla": ("वैनिला", []), "Vicia": ("बाकला", []),
    "Vigna": ("मूंग/उड़द/लोबिया", []), "Vitis": ("अंगूर", []), "Zea": ("मक्का", []),
    "Zingiber": ("अदरक", []), "Ziziphus": ("बेर", [])
}

GENUS_SW = {
    "Abelmoschus": ("bamia", []), "Abies": ("msindano fir", []), "Acacia": ("mgunga", []),
    "Adansonia": ("mbuyu", []), "Allium": ("kitunguu/saumu", []), "Aloe": ("mshubiri", []),
    "Amaranthus": ("mchicha", []), "Anacardium": ("mkorosho", ["korosho"]),
    "Ananas": ("mnanasi", ["nanasi"]), "Annona": ("mstafeli", ["mtopetope"]),
    "Arachis": ("njugu karanga", []), "Artocarpus": ("mfenesi", ["mshelisheli"]),
    "Avena": ("oats", []), "Azadirachta": ("mwarobaini", ["mneem"]),
    "Bambusa": ("mwanzi", []), "Beta": ("beetroot", []), "Brassica": ("kabichi/sukuma wiki", []),
    "Cajanus": ("mbaazi", []), "Camellia": ("mchai", []), "Cannabis": ("bangi", []),
    "Capsicum": ("pilipili", []), "Carica": ("mpapai", []), "Cassia": ("mkwaju wa kizungu", []),
    "Castanea": ("mshomoro", []), "Casuarina": ("mvinje", []), "Cinnamomum": ("mdalasini", []),
    "Citrus": ("mchungwa/mlimau", []), "Cocos": ("mnazi", []), "Coffea": ("mkahawa", []),
    "Cucumis": ("tango", []), "Cucurbita": ("mboga/boga", []), "Cupressus": ("msanduku", []),
    "Daucus": ("karoti", []), "Diospyros": ("mweusi", []), "Elaeis": ("mchikichi", []),
    "Eucalyptus": ("mkaratusi", []), "Ficus": ("mtini/mvumo", []), "Fragaria": ("stroberi", []),
    "Glycine": ("soya", []), "Gossypium": ("mpamba", []), "Hevea": ("mpira", []),
    "Hibiscus": ("mrozella", []), "Hordeum": ("shayiri", []), "Ipomoea": ("viazi vitamu", []),
    "Jasminum": ("yasmini", []), "Juglans": ("mkanju", []), "Juniperus": ("mwerezi", []),
    "Lactuca": ("saladi", []), "Lens": ("dengu", []), "Linum": ("kitani", []),
    "Magnolia": ("magnolia", []), "Malus": ("mtufaa", ["tofaa"]), "Mangifera": ("mwembe", []),
    "Manihot": ("muhogo", []), "Mentha": ("mnanaa", []), "Morus": ("mfursadi", []),
    "Musa": ("mgomba", ["ndizi"]), "Nicotiana": ("mtumbaku", []), "Olea": ("mzeituni", []),
    "Oryza": ("mpunga", ["mchele"]), "Panicum": ("mtama mwitu", []),
    "Passiflora": ("mshaupafu", ["pasheni"]), "Persea": ("mparachichi", []),
    "Phaseolus": ("maharagwe", []), "Phoenix": ("mtende", []), "Pinus": ("msindano", []),
    "Piper": ("mpilipili manga", []), "Pisum": ("njugu mbaazi", []), "Populus": ("mpopla", []),
    "Psidium": ("mpera", []), "Punica": ("mkomamanga", []), "Pyrus": ("mpera wa kizungu", []),
    "Quercus": ("mwaloni", []), "Raphanus": ("figili", []), "Ricinus": ("mbono", []),
    "Rosa": ("mwaridi", []), "Rosmarinus": ("rosemari", []), "Saccharum": ("muwa", []),
    "Salix": ("mwillow", []), "Sesamum": ("ufuta", []), "Solanum": ("mnyanya/mbatata/mbiringanya", []),
    "Sorghum": ("mtama", []), "Spinacia": ("mchicha wa kizungu", []),
    "Swietenia": ("mahogani", []), "Syzygium": ("mkarufee", ["mkarafuu"]),
    "Tamarindus": ("mkwaju", []), "Tectona": ("msaji", ["mti teak"]),
    "Theobroma": ("mkakao", []), "Triticum": ("ngano", []), "Vanilla": ("mvanila", []),
    "Vicia": ("baazi kubwa", []), "Vigna": ("kikunde", ["kunde"]), "Vitis": ("mzabibu", []),
    "Zea": ("mahindi", []), "Zingiber": ("tangawizi", [])
}

# Standard curated species across languages
CURATED_ES = {
    'Abies alba': 'abeto blanco|abeto común', 'Abies balsamea': 'abeto balsámico',
    'Abies concolor': 'abeto del colorado', 'Abies grandis': 'abeto gigante',
    'Abies nordmanniana': 'abeto del cáucaso|abeto de normandía',
    'Acacia dealbata': 'mosa|mimosa plateada|acacia mimosa',
    'Acacia farnesiana': 'aromo|espinillo', 'Acacia melanoxylon': 'acacia negra',
    'Acacia nilotica': 'acacia de egipto|goma arábiga', 'Acacia saligna': 'acacia azul',
    'Acacia senegal': 'árbol de la goma arábiga|acacia del senegal',
    'Acer campestre': 'arce común|arce menor', 'Acer platanoides': 'arce real|arce de noruega',
    'Acer pseudoplatanus': 'falso plátano|arce blanco|sicómoro', 'Acer saccharum': 'arce azucarero',
    'Adansonia digitata': 'baobab|árbol botella', 'Alnus glutinosa': 'aliso común|aliso negro',
    'Alnus incana': 'aliso gris|aliso blanco', 'Annona cherimola': 'chirimoya',
    'Annona muricata': 'guanábana', 'Annona squamosa': 'anón',
    'Araucaria angustifolia': 'pino paraná|pino de brasil', 'Araucaria araucana': 'pehuén|araucaria',
    'Arbutus unedo': 'madroño', 'Artocarpus altilis': 'árbol del pan',
    'Artocarpus heterophyllus': 'yaca', 'Azadirachta indica': 'nim|neem',
    'Betula pendula': 'abedul común|abedul blanco', 'Betula pubescens': 'abedul pubescente',
    'Carpinus betulus': 'carpe común', 'Carya illinoinensis': 'pacano|nuez pecana',
    'Castanea sativa': 'castaño|castaño común', 'Casuarina equisetifolia': 'casuarina|pino de australia',
    'Cedrus atlantica': 'cedro del atlas', 'Cedrus deodara': 'cedro del himalaya',
    'Cedrus libani': 'cedro del líbano', 'Celtis australis': 'almez',
    'Ceratonia siliqua': 'algarrobo', 'Cercis siliquastrum': 'árbol de judas',
    'Citrus limon': 'limonero|limón', 'Citrus sinensis': 'naranjo dulce|naranja',
    'Cocos nucifera': 'cocotero', 'Coffea arabica': 'cafeto arábico|café',
    'Corylus avellana': 'avellano común', 'Cupressus sempervirens': 'ciprés común|ciprés del mediterráneo',
    'Cydonia oblonga': 'membrillero|membrillo', 'Diospyros kaki': 'caqui|persimonio',
    'Elaeis guineensis': 'palma aceitera', 'Eucalyptus globulus': 'eucalipto blanco|eucalipto azul',
    'Fagus sylvatica': 'haya común|haya europea', 'Ficus carica': 'higuera común',
    'Fraxinus excelsior': 'fresno común', 'Ginkgo biloba': 'ginkgo',
    'Juglans regia': 'nogal común|nogal', 'Juniperus communis': 'enebro común',
    'Larix decidua': 'alerce europeo', 'Laurus nobilis': 'laurel común|laurel',
    'Malus domestica': 'manzano común', 'Morus alba': 'morera blanca',
    'Morus nigra': 'moral negro', 'Olea europaea': 'olivo|olivera',
    'Paulownia tomentosa': 'paulonia imperial', 'Persea americana': 'aguacate|palto',
    'Phoenix dactylifera': 'palmera datilera', 'Picea abies': 'abeto rojo|pícea común',
    'Pinus brutia': 'pino de calabria|pino turco', 'Pinus halepensis': 'pino carrasco',
    'Pinus nigra': 'pino salgareño|pino negral', 'Pinus pinea': 'pino piñonero',
    'Pinus sylvestris': 'pino silvestre|pino albar', 'Pistacia vera': 'pistachero|pistacho',
    'Platanus orientalis': 'plátano oriental', 'Populus alba': 'álamo blanco',
    'Populus nigra': 'álamo negro', 'Populus tremula': 'álamo temblón',
    'Prunus armeniaca': 'albaricoquero|damasco', 'Prunus avium': 'cerezo|cerezo silvestre',
    'Prunus cerasus': 'guindo|cerezo ácido', 'Prunus domestica': 'ciruelo',
    'Prunus dulcis': 'almendro', 'Prunus persica': 'melocotonero|duraznero',
    'Pyrus communis': 'peral común', 'Quercus ilex': 'encina',
    'Quercus robur': 'roble común|roble carballo', 'Quercus rubra': 'roble rojo americano',
    'Quercus suber': 'alcornoque', 'Robinia pseudoacacia': 'falsa acacia|robinia',
    'Salix alba': 'sauce blanco', 'Salix babylonica': 'sauce llorón',
    'Taxus baccata': 'tejo común', 'Tectona grandis': 'teca',
    'Theobroma cacao': 'cacaotero|cacao', 'Tilia cordata': 'tilo de hoja pequeña',
    'Ulmus minor': 'olmo común', 'Vitis vinifera': 'vid|parra',
    'Allium cepa': 'cebolla', 'Allium sativum': 'ajo', 'Avena sativa': 'avena',
    'Beta vulgaris': 'remolacha', 'Glycine max': 'soja|soya',
    'Helianthus annuus': 'girasol', 'Hordeum vulgare': 'cebada',
    'Ipomoea batatas': 'batata|camote', 'Oryza sativa': 'arroz',
    'Phaseolus vulgaris': 'frijol|judía', 'Pisum sativum': 'guisante|arveja',
    'Solanum lycopersicum': 'tomate', 'Solanum tuberosum': 'patata|papa',
    'Triticum aestivum': 'trigo', 'Zea mays ssp. mays': 'maíz', 'Zea mays': 'maíz'
}

CURATED_FR = {
    'Abies alba': 'sapin blanc|sapin pectiné', 'Abies balsamea': 'sapin baumier',
    'Abies nordmanniana': 'sapin de nordmann', 'Acacia dealbata': "mimosa des fleuristes|mimosa d'hiver",
    'Acer campestre': 'érable champêtre', 'Acer platanoides': 'érable plane',
    'Acer pseudoplatanus': 'érable sycomore', 'Acer saccharum': 'érable à sucre',
    'Adansonia digitata': 'baobab africain', 'Alnus glutinosa': 'aulne glutineux|aulne noir',
    'Annona muricata': 'corossolier', 'Araucaria angustifolia': 'pin du paraná',
    'Arbutus unedo': 'arbousier', 'Artocarpus altilis': 'arbre à pain',
    'Azadirachta indica': 'margousier|neem', 'Betula pendula': 'bouleau verruqueux|bouleau blanc',
    'Carpinus betulus': 'charme commun', 'Carya illinoinensis': 'pacanier',
    'Castanea sativa': 'châtaignier commun', 'Casuarina equisetifolia': 'filao',
    'Cedrus atlantica': "cèdre de l'atlas", 'Cedrus deodara': "cèdre de l'himalaya",
    'Cedrus libani': 'cèdre du liban', 'Celtis australis': 'micocoulier de provence',
    'Ceratonia siliqua': 'caroubier', 'Cercis siliquastrum': 'arbre de judée',
    'Citrus limon': 'citronnier|citron', 'Citrus sinensis': 'oranger|orange douce',
    'Cocos nucifera': 'cocotier', 'Coffea arabica': "caféier d'arabie",
    'Corylus avellana': 'noisetier commun', 'Cupressus sempervirens': 'cyprès toujours vert',
    'Cydonia oblonga': 'cognassier', 'Diospyros kaki': 'plaqueminier du japon|kaki',
    'Elaeis guineensis': 'palmier à huile', 'Eucalyptus globulus': 'gommier bleu',
    'Fagus sylvatica': 'hêtre commun|hêtre', 'Ficus carica': 'figuier commun',
    'Fraxinus excelsior': 'frêne élevé', 'Ginkgo biloba': 'arbre aux quarante écus|ginkgo',
    'Juglans regia': 'noyer commun', 'Juniperus communis': 'genévrier commun',
    'Larix decidua': "mélèze d'europe", 'Laurus nobilis': 'laurier noble|laurier-sauce',
    'Malus domestica': 'pommier commun', 'Morus alba': 'mûrier blanc',
    'Morus nigra': 'mûrier noir', 'Olea europaea': "olivier|olivier d'europe",
    'Paulownia tomentosa': 'paulownia impérial', 'Persea americana': 'avocatier',
    'Phoenix dactylifera': 'palmier-dattier', 'Picea abies': 'épicéa commun',
    'Pinus brutia': 'pin de calabre', 'Pinus halepensis': "pin d'alep",
    'Pinus nigra': "pin noir d'autriche", 'Pinus pinea': 'pin parasol',
    'Pinus sylvestris': 'pin sylvestre', 'Pistacia vera': 'pistachier vrai',
    'Platanus orientalis': "platane d'orient", 'Populus alba': 'peuplier blanc',
    'Populus nigra': 'peuplier noir', 'Populus tremula': 'peuplier tremble|tremble',
    'Prunus armeniaca': 'abricotier', 'Prunus avium': 'merisier|cerisier sauvage',
    'Prunus cerasus': 'cerisier aigre|griottier', 'Prunus domestica': 'prunier',
    'Prunus dulcis': 'amandier', 'Prunus persica': 'pêcher',
    'Pyrus communis': 'poirier commun', 'Quercus ilex': 'chêne vert',
    'Quercus robur': 'chêne pédonculé|chêne blanc', 'Quercus rubra': "chêne rouge d'amérique",
    'Quercus suber': 'chêne-liège', 'Robinia pseudoacacia': 'robinier faux-acacia',
    'Salix alba': 'saule blanc', 'Salix babylonica': 'saule pleureur',
    'Taxus baccata': 'if commun', 'Tectona grandis': 'teck',
    'Theobroma cacao': 'cacaoyer', 'Tilia cordata': 'tilleul à petites feuilles',
    'Ulmus minor': 'orme champêtre', 'Vitis vinifera': 'vigne cultivée',
    'Allium cepa': 'oignon', 'Allium sativum': 'ail', 'Avena sativa': 'avoine',
    'Beta vulgaris': 'betterave', 'Glycine max': 'soja',
    'Helianthus annuus': 'tournesol', 'Hordeum vulgare': 'orge',
    'Ipomoea batatas': 'patate douce', 'Oryza sativa': 'riz',
    'Phaseolus vulgaris': 'haricot', 'Pisum sativum': 'pois cultivé|petit pois',
    'Solanum lycopersicum': 'tomate', 'Solanum tuberosum': 'pomme de terre',
    'Triticum aestivum': 'blé tendre', 'Zea mays ssp. mays': 'maïs', 'Zea mays': 'maïs'
}

CURATED_DE = {
    'Abies alba': 'weiß-tanne|silbertanne', 'Abies balsamea': 'balsam-tanne',
    'Abies nordmanniana': 'nordmann-tanne', 'Acacia dealbata': 'silber-akazie',
    'Acer campestre': 'feld-ahorn', 'Acer platanoides': 'spitz-ahorn',
    'Acer pseudoplatanus': 'berg-ahorn', 'Acer saccharum': 'zucker-ahorn',
    'Adansonia digitata': 'affenbrotbaum|baobab', 'Alnus glutinosa': 'schwarz-erle',
    'Betula pendula': 'hänge-birke|sand-birke', 'Carpinus betulus': 'hainbuche',
    'Carya illinoinensis': 'pakanbaum|pekannuss', 'Castanea sativa': 'edelkastanie|esskastanie',
    'Casuarina equisetifolia': 'schachtelhalmblättrige kasuarine',
    'Cedrus atlantica': 'atlas-zeder', 'Cedrus deodara': 'himalaya-zeder',
    'Cedrus libani': 'libanon-zeder', 'Celtis australis': 'europäischer zürgelbaum',
    'Ceratonia siliqua': 'johannisbrotbaum', 'Cercis siliquastrum': 'judasbaum',
    'Citrus limon': 'zitronenbaum|zitrone', 'Citrus sinensis': 'orange|apfelsine',
    'Cocos nucifera': 'kokospalme', 'Coffea arabica': 'arabica-kaffee',
    'Corylus avellana': 'gemeine hasel', 'Cupressus sempervirens': 'mittelmeer-zypresse',
    'Cydonia oblonga': 'quitte', 'Diospyros kaki': 'kakibaum|kaki',
    'Elaeis guineensis': 'ölpalme', 'Eucalyptus globulus': 'blauer eukalyptus',
    'Fagus sylvatica': 'rotbuche|buche', 'Ficus carica': 'echte feige',
    'Fraxinus excelsior': 'gemeine esche', 'Ginkgo biloba': 'ginkgobaum|ginkgo',
    'Juglans regia': 'echte walnuss', 'Juniperus communis': 'gemeiner wacholder',
    'Larix decidua': 'europäische lärche', 'Laurus nobilis': 'echter lorbeer',
    'Malus domestica': 'kultur-apfel|apfelbaum', 'Morus alba': 'weiße maulbeere',
    'Morus nigra': 'schwarze maulbeere', 'Olea europaea': 'olivenbaum|ölbaum',
    'Paulownia tomentosa': 'blauglockenbaum', 'Persea americana': 'avocadobaum|avocado',
    'Phoenix dactylifera': 'echte dattelpalme', 'Picea abies': 'gemeine fichte|rotfichte',
    'Pinus brutia': 'kalabrische kiefer', 'Pinus halepensis': 'aleppo-kiefer',
    'Pinus nigra': 'schwarz-kiefer', 'Pinus pinea': 'pinie',
    'Pinus sylvestris': 'wald-kiefer|föhre', 'Pistacia vera': 'echte pistazie',
    'Platanus orientalis': 'morgenländische platane', 'Populus alba': 'silber-pappel',
    'Populus nigra': 'schwarz-pappel', 'Populus tremula': 'zitter-pappel|espe',
    'Prunus armeniaca': 'aprikosenbaum|marille', 'Prunus avium': 'vogel-kirsche|süßkirsche',
    'Prunus cerasus': 'sauerkirsche', 'Prunus domestica': 'pflaumenbaum|zwetschge',
    'Prunus dulcis': 'mandelbaum', 'Prunus persica': 'pfirsichbaum',
    'Pyrus communis': 'kultur-birne', 'Quercus ilex': 'stein-eiche',
    'Quercus robur': 'stiel-eiche|deutsche eiche', 'Quercus rubra': 'amerikanische rot-eiche',
    'Quercus suber': 'kork-eiche', 'Robinia pseudoacacia': 'gewöhnliche robinie',
    'Salix alba': 'silber-weide', 'Salix babylonica': 'echte trauer-weide',
    'Taxus baccata': 'europäische eibe', 'Tectona grandis': 'teakbaum',
    'Theobroma cacao': 'kakaobaum', 'Tilia cordata': 'winter-linde',
    'Ulmus minor': 'feld-ulme', 'Vitis vinifera': 'echte weinrebe',
    'Allium cepa': 'zwiebel', 'Allium sativum': 'knoblauch', 'Avena sativa': 'saat-hafer',
    'Beta vulgaris': 'zuckerrübe|rote bete', 'Glycine max': 'sojabohne',
    'Helianthus annuus': 'sonnenblume', 'Hordeum vulgare': 'gerste',
    'Ipomoea batatas': 'süßkartoffel', 'Oryza sativa': 'reis',
    'Phaseolus vulgaris': 'gartenbohne', 'Pisum sativum': 'erbse',
    'Solanum lycopersicum': 'tomate', 'Solanum tuberosum': 'kartoffel',
    'Triticum aestivum': 'weichweizen', 'Zea mays ssp. mays': 'mais', 'Zea mays': 'mais'
}

CURATED_RU = {
    'Abies alba': 'пихта белая', 'Abies balsamea': 'пихта бальзамическая',
    'Abies nordmanniana': 'пихта нордмана', 'Acacia dealbata': 'акация серебристая|мимоза',
    'Acer campestre': 'клён полевой', 'Acer platanoides': 'клён остролистный',
    'Acer pseudoplatanus': 'клён белый|явор', 'Acer saccharum': 'клён сахарный',
    'Adansonia digitata': 'баобаб', 'Alnus glutinosa': 'ольха чёрная',
    'Betula pendula': 'берёза повислая|берёза бородавчатая', 'Carpinus betulus': 'граб обыкновенный',
    'Castanea sativa': 'каштан посевной', 'Cedrus atlantica': 'кедр атласский',
    'Cedrus deodara': 'кедр гималайский', 'Cedrus libani': 'кедр ливанский',
    'Citrus limon': 'лимон', 'Citrus sinensis': 'апельсин',
    'Corylus avellana': 'лещина обыкновенная|фундук', 'Cupressus sempervirens': 'кипарис вечнозелёный',
    'Fagus sylvatica': 'бук европейский', 'Ficus carica': 'инжир|смоковница',
    'Fraxinus excelsior': 'ясень обыкновенный', 'Ginkgo biloba': 'гинкго',
    'Juglans regia': 'грецкий орех', 'Juniperus communis': 'можжевельник обыкновенный',
    'Larix decidua': 'лиственница европейская', 'Laurus nobilis': 'лавр благородный',
    'Malus domestica': 'яблоня домашняя', 'Morus alba': 'шелковица белая',
    'Morus nigra': 'шелковица чёрная', 'Olea europaea': 'олива европейская|маслина',
    'Picea abies': 'ель обыкновенная', 'Pinus brutia': 'сосна калабрийская',
    'Pinus nigra': 'сосна чёрная', 'Pinus pinea': 'сосна пиния',
    'Pinus sylvestris': 'сосна обыкновенная', 'Pistacia vera': 'фисташка',
    'Platanus orientalis': 'платан восточный|чинара', 'Populus alba': 'тополь белый',
    'Populus nigra': 'тополь чёрный', 'Populus tremula': 'осина',
    'Prunus armeniaca': 'абрикос обыкновенный', 'Prunus avium': 'черешня',
    'Prunus cerasus': 'вишня обыкновенная', 'Prunus domestica': 'слива домашняя',
    'Prunus dulcis': 'миндаль обыкновенный', 'Prunus persica': 'персик обыкновенный',
    'Pyrus communis': 'груша обыкновенная', 'Quercus ilex': 'дуб каменный',
    'Quercus robur': 'дуб черешчатый|дуб обыкновенный', 'Quercus rubra': 'дуб красный',
    'Quercus suber': 'дуб пробковый', 'Robinia pseudoacacia': 'робиния ложноакациевая|белая акация',
    'Salix alba': 'ива белая', 'Taxus baccata': 'тис ягодный',
    'Tilia cordata': 'липа мелколистная', 'Ulmus minor': 'вяз малый',
    'Vitis vinifera': 'виноград культурный', 'Allium cepa': 'лук репчатый',
    'Allium sativum': 'чеснок', 'Avena sativa': 'овёс посевной',
    'Beta vulgaris': 'свёкла', 'Glycine max': 'соя',
    'Helianthus annuus': 'подсолнечник', 'Hordeum vulgare': 'ячмень',
    'Ipomoea batatas': 'батат', 'Oryza sativa': 'рис посевной',
    'Phaseolus vulgaris': 'фасоль', 'Pisum sativum': 'горох посевной',
    'Solanum lycopersicum': 'томат|помидор', 'Solanum tuberosum': 'картофель',
    'Triticum aestivum': 'пшеница мягкая', 'Zea mays ssp. mays': 'кукуруза', 'Zea mays': 'кукуруза'
}

CURATED_ZH = {
    'Abies alba': '欧洲白冷杉|白冷杉', 'Abies balsamea': '胶冷杉',
    'Acacia dealbata': '银荆|澳洲金合欢', 'Acer saccharum': '糖槭|糖枫',
    'Adansonia digitata': '猴面包树', 'Betula pendula': '垂枝桦|白桦',
    'Castanea sativa': '欧洲栗|西洋栗', 'Casuarina equisetifolia': '木麻黄',
    'Cedrus deodara': '雪松', 'Citrus limon': '柠檬',
    'Citrus sinensis': '甜橙|脐橙', 'Cocos nucifera': '椰子',
    'Coffea arabica': '小粒咖啡', 'Corylus avellana': '欧洲榛|榛子',
    'Diospyros kaki': '柿树|柿子', 'Eucalyptus globulus': '蓝桉',
    'Fagus sylvatica': '欧洲山毛榉', 'Ficus carica': '无花果',
    'Ginkgo biloba': '银杏', 'Juglans regia': '核桃',
    'Malus domestica': '苹果', 'Morus alba': '桑树',
    'Olea europaea': '油橄榄|橄榄', 'Persea americana': '牛油果|鳄梨',
    'Picea abies': '欧洲云杉', 'Pinus sylvestris': '欧洲赤松',
    'Prunus armeniaca': '杏', 'Prunus avium': '欧洲甜樱桃|车厘子',
    'Prunus persica': '桃树|桃', 'Quercus robur': '夏栎|欧洲栎',
    'Quercus rubra': '红栎', 'Quercus suber': '栓皮栎',
    'Robinia pseudoacacia': '刺槐|洋槐', 'Salix babylonica': '垂柳',
    'Tectona grandis': '柚木', 'Theobroma cacao': '可可树|可可',
    'Vitis vinifera': '葡萄', 'Allium cepa': '洋葱',
    'Arachis hypogaea': '花生', 'Glycine max': '大豆',
    'Helianthus annuus': '向日葵', 'Oryza sativa': '水稻',
    'Solanum lycopersicum': '番茄', 'Solanum tuberosum': '马铃薯|土豆',
    'Triticum aestivum': '小麦', 'Zea mays ssp. mays': '玉米', 'Zea mays': '玉米'
}

CURATED_JA = {
    'Abies alba': 'ヨーロッパモミ|モミ', 'Acacia dealbata': 'フサアカシア|ミモザ',
    'Acer saccharum': 'サトウカエデ', 'Adansonia digitata': 'バオバブ',
    'Betula pendula': 'シラカンバ', 'Castanea sativa': 'ヨーロッパグリ',
    'Cedrus deodara': 'ヒマラヤスギ', 'Citrus limon': 'レモン',
    'Citrus sinensis': 'スイートオレンジ', 'Cocos nucifera': 'ココヤシ',
    'Coffea arabica': 'アラビカコーヒーノキ', 'Corylus avellana': 'セイヨウハシバミ',
    'Diospyros kaki': 'カキノキ|カキ', 'Eucalyptus globulus': 'タスマニアンブルーガム',
    'Fagus sylvatica': 'ヨーロッパブナ', 'Ficus carica': 'イチジク',
    'Ginkgo biloba': 'イチョウ', 'Juglans regia': 'ペルシャグルミ|クルミ',
    'Malus domestica': 'リンゴ', 'Morus alba': 'マグワ',
    'Olea europaea': 'オリーブ', 'Persea americana': 'アボカド',
    'Picea abies': 'ドイツトウヒ', 'Pinus sylvestris': 'ヨーロッパアカマツ',
    'Prunus armeniaca': 'アンズ', 'Prunus avium': 'セイヨウミザクラ|サクランボ',
    'Prunus persica': 'モモ', 'Quercus robur': 'イングリッシュオーク|ヨーロッパナラ',
    'Quercus rubra': 'アカガシワ', 'Quercus suber': 'コルクガシ',
    'Robinia pseudoacacia': 'ハリエンジュ', 'Salix babylonica': 'シダレヤナギ',
    'Tectona grandis': 'チーク', 'Theobroma cacao': 'カカオ',
    'Vitis vinifera': 'ヨーロッパブドウ', 'Allium cepa': 'タマネギ',
    'Arachis hypogaea': 'ラッカセイ', 'Glycine max': 'ダイズ',
    'Oryza sativa': 'イネ|米', 'Solanum lycopersicum': 'トマト',
    'Solanum tuberosum': 'ジャガイモ', 'Triticum aestivum': 'コムギ',
    'Zea mays ssp. mays': 'トウモロコシ', 'Zea mays': 'トウモロコシ'
}

CURATED_ID = {
    'Adansonia digitata': 'baobab', 'Ananas comosus': 'nanas',
    'Annona muricata': 'sirsak', 'Artocarpus heterophyllus': 'nangka',
    'Azadirachta indica': 'mimba', 'Carica papaya': 'pepaya',
    'Cinnamomum verum': 'kayu manis', 'Citrus limon': 'lemon',
    'Citrus sinensis': 'jeruk manis', 'Cocos nucifera': 'kelapa',
    'Coffea arabica': 'kopi arabika', 'Curcuma longa': 'kunyit',
    'Elaeis guineensis': 'kelapa sawit', 'Hevea brasiliensis': 'pohon karet|karet',
    'Ipomoea batatas': 'ubi jalar', 'Mangifera indica': 'mangga',
    'Manihot esculenta': 'singkong', 'Musa acuminata': 'pisang',
    'Oryza sativa': 'padi', 'Persea americana': 'alpukat',
    'Pinus merkusii': 'tusam sumatera', 'Piper nigrum': 'lada hitam',
    'Psidium guajava': 'jambu biji', 'Quercus robur': 'pohon ek eropa|ek',
    'Saccharum officinarum': 'tebu', 'Syzygium aromaticum': 'cengkih',
    'Tamarindus indica': 'asam jawa', 'Tectona grandis': 'jati',
    'Theobroma cacao': 'kakao', 'Vitis vinifera': 'anggur',
    'Zea mays ssp. mays': 'jagung', 'Zea mays': 'jagung', 'Zingiber officinale': 'jahe'
}

CURATED_HI = {
    'Acacia nilotica': 'बबूल|कीकर', 'Aegle marmelos': 'बेल',
    'Allium cepa': 'प्याज़', 'Allium sativum': 'लहसुन',
    'Aloe vera': 'घृतकुमारी', 'Artocarpus heterophyllus': 'कटहल',
    'Azadirachta indica': 'नीम', 'Carica papaya': 'पपीता',
    'Cedrus deodara': 'देवदार', 'Citrus limon': 'नींबू',
    'Cocos nucifera': 'नारियल', 'Coffea arabica': 'कॉफी',
    'Curcuma longa': 'हल्दी', 'Dalbergia sissoo': 'शीशम',
    'Ficus benghalensis': 'बरगद', 'Ficus religiosa': 'पीपल',
    'Juglans regia': 'अखरोट', 'Mangifera indica': 'आम',
    'Morus alba': 'शहतूत', 'Musa acuminata': 'केला',
    'Oryza sativa': 'चावल|धान', 'Pinus sylvestris': 'स्कॉच चीड़|चीड़',
    'Piper nigrum': 'काली मिर्च', 'Prunus dulcis': 'बादाम',
    'Psidium guajava': 'अमरूद', 'Punica granatum': 'अनार',
    'Quercus robur': 'शाहबलूत|ओक', 'Saccharum officinarum': 'गन्ना',
    'Solanum lycopersicum': 'टमाटर', 'Solanum tuberosum': 'आलू',
    'Syzygium cumini': 'जामुन', 'Tamarindus indica': 'इमली',
    'Tectona grandis': 'सागौन', 'Triticum aestivum': 'गेहूं',
    'Vitis vinifera': 'अंगूर', 'Zea mays ssp. mays': 'मक्का', 'Zea mays': 'मक्का',
    'Zingiber officinale': 'अदरक'
}

CURATED_SW = {
    'Adansonia digitata': 'mbuyu|baobab', 'Allium cepa': 'kitunguu',
    'Ananas comosus': 'nanasi', 'Annona muricata': 'mstafeli',
    'Artocarpus heterophyllus': 'fenesi', 'Azadirachta indica': 'mwarobaini',
    'Carica papaya': 'mpapai', 'Casuarina equisetifolia': 'mvinje',
    'Citrus limon': 'mlimau', 'Citrus sinensis': 'mchungwa',
    'Cocos nucifera': 'mnazi', 'Coffea arabica': 'mkahawa',
    'Elaeis guineensis': 'mchikichi', 'Eucalyptus camaldulensis': 'mkaratusi',
    'Mangifera indica': 'mwembe', 'Manihot esculenta': 'muhogo',
    'Musa acuminata': 'mgomba', 'Oryza sativa': 'mpunga',
    'Persea americana': 'mparachichi', 'Phaseolus vulgaris': 'maharagwe',
    'Pinus caribaea': 'msindano', 'Psidium guajava': 'mpera',
    'Quercus robur': 'mwaloni wa ulaya|mwaloni', 'Saccharum officinarum': 'muwa',
    'Solanum lycopersicum': 'mnyanya', 'Solanum tuberosum': 'viazi',
    'Syzygium aromaticum': 'mkarufee|karafuu', 'Tamarindus indica': 'mkwaju',
    'Tectona grandis': 'msaji', 'Theobroma cacao': 'mkakao',
    'Triticum aestivum': 'ngano', 'Zea mays ssp. mays': 'mahindi', 'Zea mays': 'mahindi',
    'Zingiber officinale': 'tangawizi'
}

# Epithets maps
EPITHETS_ES = {
    'alba': 'blanco', 'albus': 'blanco', 'album': 'blanco',
    'nigra': 'negro', 'niger': 'negro', 'nigrum': 'negro',
    'rubra': 'rojo', 'ruber': 'rojo', 'rubrum': 'rojo',
    'lutea': 'amarillo', 'luteus': 'amarillo', 'luteum': 'amarillo',
    'viridis': 'verde', 'glauca': 'glauco',
    'sylvestris': 'silvestre', 'silvestris': 'silvestre',
    'orientalis': 'oriental', 'orientale': 'oriental',
    'occidentalis': 'occidental', 'occidentale': 'occidental',
    'australis': 'austral', 'australe': 'austral',
    'borealis': 'boreal', 'boreale': 'boreal',
    'canadensis': 'de canadá', 'africana': 'africano', 'africanus': 'africano',
    'americana': 'americano', 'americanus': 'americano',
    'japonica': 'japonés', 'japonicus': 'japonés',
    'pendula': 'péndulo', 'pendulus': 'péndulo',
    'gigantea': 'gigante', 'giganteus': 'gigante',
    'palustris': 'de pantano', 'pratensis': 'de prado',
    'vulgaris': 'común', 'officinalis': 'medicinal', 'officinale': 'medicinal',
    'sativa': 'cultivado', 'sativus': 'cultivado', 'sativum': 'cultivado'
}

EPITHETS_FR = {
    'alba': 'blanc', 'albus': 'blanc', 'album': 'blanc',
    'nigra': 'noir', 'niger': 'noir', 'nigrum': 'noir',
    'rubra': 'rouge', 'ruber': 'rouge', 'rubrum': 'rouge',
    'lutea': 'jaune', 'luteus': 'jaune', 'luteum': 'jaune',
    'viridis': 'vert', 'glauca': 'glauque',
    'sylvestris': 'sylvestre', 'silvestris': 'sylvestre',
    'orientalis': "d'orient", 'orientale': "d'orient",
    'occidentalis': "d'occident", 'occidentale': "d'occident",
    'australis': 'austral', 'australe': 'austral',
    'borealis': 'boréal', 'boreale': 'boréal',
    'canadensis': 'du canada', 'africana': "d'afrique", 'africanus': "d'afrique",
    'americana': "d'amérique", 'americanus': "d'amérique",
    'japonica': 'du japon', 'japonicus': 'du japon',
    'pendula': 'pleureur', 'pendulus': 'pleureur',
    'gigantea': 'géant', 'giganteus': 'géant',
    'palustris': 'des marais', 'pratensis': 'des prés',
    'vulgaris': 'commun', 'officinalis': 'officinal', 'officinale': 'officinal',
    'sativa': 'cultivé', 'sativus': 'cultivé', 'sativum': 'cultivé'
}

EPITHETS_DE = {
    'alba': 'weiß', 'albus': 'weiß', 'album': 'weiß',
    'nigra': 'schwarz', 'niger': 'schwarz', 'nigrum': 'schwarz',
    'rubra': 'rot', 'ruber': 'rot', 'rubrum': 'rot',
    'lutea': 'gelb', 'luteus': 'gelb', 'luteum': 'gelb',
    'viridis': 'grün', 'glauca': 'blau',
    'sylvestris': 'wald', 'silvestris': 'wald',
    'orientalis': 'orient', 'orientale': 'orient',
    'occidentalis': 'west', 'occidentale': 'west',
    'australis': 'süd', 'australe': 'süd',
    'borealis': 'nord', 'boreale': 'nord',
    'canadensis': 'kanada', 'africana': 'afrika', 'africanus': 'afrika',
    'americana': 'amerika', 'americanus': 'amerika',
    'japonica': 'japan', 'japonicus': 'japan',
    'pendula': 'hänge', 'pendulus': 'hänge',
    'gigantea': 'riesen', 'giganteus': 'riesen',
    'palustris': 'sumpf', 'pratensis': 'wiesen',
    'vulgaris': 'gemein', 'officinalis': 'echt', 'officinale': 'echt',
    'sativa': 'saat', 'sativus': 'saat', 'sativum': 'saat'
}

EPITHETS_RU = {
    'alba': 'белая', 'albus': 'белый', 'album': 'белое',
    'nigra': 'чёрная', 'niger': 'чёрный', 'nigrum': 'чёрное',
    'rubra': 'красная', 'ruber': 'красный', 'rubrum': 'красное',
    'lutea': 'жёлтая', 'luteus': 'жёлтый', 'luteum': 'жёлтое',
    'viridis': 'зелёная', 'glauca': 'сизая',
    'sylvestris': 'лесная', 'silvestris': 'лесная',
    'orientalis': 'восточная', 'orientale': 'восточное',
    'occidentalis': 'западная', 'occidentale': 'западное',
    'australis': 'южная', 'australe': 'южное',
    'borealis': 'северная', 'boreale': 'северное',
    'canadensis': 'канадская', 'africana': 'африканская', 'africanus': 'африканский',
    'americana': 'американская', 'americanus': 'американский',
    'japonica': 'японская', 'japonicus': 'японский',
    'pendula': 'повислая', 'pendulus': 'плакучий',
    'gigantea': 'гигантская', 'giganteus': 'гигантский',
    'palustris': 'болотная', 'pratensis': 'луговая',
    'vulgaris': 'обыкновенная', 'officinalis': 'лекарственная', 'officinale': 'лекарственное',
    'sativa': 'посевная', 'sativus': 'посевной', 'sativum': 'посевное'
}

EPITHETS_ZH = {
    'alba': '白', 'albus': '白', 'album': '白',
    'nigra': '黑', 'niger': '黑', 'nigrum': '黑',
    'rubra': '红', 'ruber': '红', 'rubrum': '红',
    'lutea': '黄', 'luteus': '黄', 'luteum': '黄',
    'viridis': '绿', 'glauca': '粉绿',
    'sylvestris': '野', 'silvestris': '野',
    'orientalis': '东方', 'orientale': '东方',
    'occidentalis': '西方', 'occidentale': '西方',
    'australis': '南方', 'australe': '南方',
    'borealis': '北方', 'boreale': '北方',
    'canadensis': '加拿大', 'africana': '非洲', 'africanus': '非洲',
    'americana': '美洲', 'americanus': '美洲',
    'japonica': '日本', 'japonicus': '日本',
    'pendula': '垂枝', 'pendulus': '垂枝',
    'gigantea': '巨', 'giganteus': '巨',
    'palustris': '沼泽', 'pratensis': '草甸',
    'vulgaris': '普通', 'officinalis': '药用', 'officinale': '药用',
    'sativa': '栽培', 'sativus': '栽培', 'sativum': '栽培'
}

EPITHETS_JA = {
    'alba': 'シロ', 'albus': 'シロ', 'album': 'シロ',
    'nigra': 'クロ', 'niger': 'クロ', 'nigrum': 'クロ',
    'rubra': 'アカ', 'ruber': 'アカ', 'rubrum': 'アカ',
    'lutea': 'キ', 'luteus': 'キ', 'luteum': 'キ',
    'viridis': 'アオ', 'glauca': 'シラ',
    'sylvestris': 'モリ', 'silvestris': 'モリ',
    'orientalis': 'トウヨウ', 'orientale': 'トウヨウ',
    'occidentalis': 'セイヨウ', 'occidentale': 'セイヨウ',
    'canadensis': 'カナダ', 'africana': 'アフリカ', 'africanus': 'アフリカ',
    'americana': 'アメリカ', 'americanus': 'アメリカ',
    'japonica': 'ニホン', 'japonicus': 'ニホン',
    'pendula': 'シダレ', 'pendulus': 'シダレ',
    'gigantea': 'オオ', 'giganteus': 'オオ',
    'vulgaris': 'フツウ', 'officinalis': 'ヤクヨウ'
}

EPITHETS_ID = {
    'alba': 'putih', 'albus': 'putih', 'album': 'putih',
    'nigra': 'hitam', 'niger': 'hitam', 'nigrum': 'hitam',
    'rubra': 'merah', 'ruber': 'merah', 'rubrum': 'merah',
    'lutea': 'kuning', 'luteus': 'kuning', 'luteum': 'kuning',
    'viridis': 'hijau',
    'sylvestris': 'hutan', 'silvestris': 'hutan',
    'orientalis': 'timur', 'orientale': 'timur',
    'occidentalis': 'barat', 'occidentale': 'barat',
    'australis': 'selatan', 'australe': 'selatan',
    'borealis': 'utara', 'boreale': 'utara',
    'canadensis': 'kanada', 'africana': 'afrika', 'africanus': 'afrika',
    'americana': 'amerika', 'americanus': 'amerika',
    'japonica': 'jepang', 'japonicus': 'jepang',
    'pendula': 'juntai', 'gigantea': 'raksasa',
    'vulgaris': 'biasa', 'officinalis': 'obat'
}

EPITHETS_HI = {
    'alba': 'सफेद', 'albus': 'सफेद', 'album': 'सफेद',
    'nigra': 'काला', 'niger': 'काला', 'nigrum': 'काला',
    'rubra': 'लाल', 'ruber': 'लाल', 'rubrum': 'लाल',
    'lutea': 'पीला', 'luteus': 'पीला', 'luteum': 'पीला',
    'viridis': 'हरा',
    'sylvestris': 'जंगली', 'silvestris': 'जंगली',
    'orientalis': 'पूर्वी', 'orientale': 'पूर्वी',
    'occidentalis': 'पश्चिमी', 'occidentale': 'पश्चिमी',
    'canadensis': 'कनाडाई', 'africana': 'अफ्रीकी', 'africanus': 'अफ्रीकी',
    'americana': 'अमेरिकी', 'americanus': 'अमेरिकी',
    'japonica': 'जापानी', 'japonicus': 'जापानी',
    'gigantea': 'विशाल', 'vulgaris': 'साधारण', 'officinalis': 'औषधीय'
}

EPITHETS_SW = {
    'alba': 'mweupe', 'albus': 'mweupe', 'album': 'mweupe',
    'nigra': 'mweusi', 'niger': 'mweusi', 'nigrum': 'mweusi',
    'rubra': 'mwekundu', 'ruber': 'mwekundu', 'rubrum': 'mwekundu',
    'lutea': 'manjano', 'luteus': 'manjano', 'luteum': 'manjano',
    'viridis': 'kijani',
    'sylvestris': 'wa mwitu', 'silvestris': 'wa mwitu',
    'orientalis': 'wa mashariki', 'occidentalis': 'wa magharibi',
    'canadensis': 'wa kanada', 'africana': 'wa afrika', 'africanus': 'wa afrika',
    'americana': 'wa marekani', 'americanus': 'wa marekani',
    'japonica': 'wa japani', 'japonicus': 'wa japani',
    'gigantea': 'mkubwa', 'vulgaris': 'wa kawaida', 'officinalis': 'wa dawa'
}


def clean_str(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def binomial(sci):
    s = re.sub(r"\s*(subsp\.|ssp\.|var\.|f\.|gr\.)\s+\S+", "", sci)
    s = s.replace("×", "").replace(" x ", " ")
    parts = s.split()
    if len(parts) < 2 or parts[1].lower() in ("sp.", "spp."):
        return parts[0], "" if parts else ("", "")
    return parts[0], parts[1].lower().rstrip(".")


def format_composed_name(genus_word, epithet_word, style):
    if not genus_word:
        return ""
    if not epithet_word:
        return genus_word
    if style == "prefix_space":      # TR, HI
        return f"{epithet_word} {genus_word}".strip()
    elif style == "prefix_hyphen":   # DE
        return f"{epithet_word.capitalize()}-{genus_word.capitalize()}".strip()
    elif style == "prefix_concat":   # ZH, JA
        return f"{epithet_word}{genus_word}".strip()
    elif style == "postfix_space":   # ES, FR, RU, ID, SW
        return f"{genus_word} {epithet_word}".strip()
    return genus_word


def build_language_dict(species_list, curated, genus_fallback, epithets=None, style="postfix_space"):
    out = {}
    epithets = epithets or {}
    for sp in species_list:
        sid = str(sp["id"])
        sci = sp["sci"].strip()
        genus, epithet = binomial(sci)

        # 1. Exact sci match in curated table
        if sci in curated:
            parts = [clean_str(p) for p in curated[sci].split("|") if p.strip()]
            if parts:
                entry = {"nome": parts[0]}
                if len(parts) > 1:
                    entry["aka"] = parts[1:]
                out[sid] = entry
                continue

        # 2. Binomial match without variety/subspecies
        binom_str = f"{genus} {epithet}".strip()
        if binom_str in curated:
            parts = [clean_str(p) for p in curated[binom_str].split("|") if p.strip()]
            if parts:
                entry = {"nome": parts[0]}
                if len(parts) > 1:
                    entry["aka"] = parts[1:]
                out[sid] = entry
                continue

        # 3. Genus fallback match with epithet modifier
        if genus in genus_fallback:
            base, akas = genus_fallback[genus]
            if epithet and epithet in epithets:
                ep_val = epithets[epithet]
                composed = format_composed_name(base, ep_val, style)
                entry = {"nome": clean_str(composed)}
                # Also record base genus as synonym
                entry["aka"] = [clean_str(base)] + [clean_str(a) for a in akas if clean_str(a) != entry["nome"]]
                out[sid] = entry
                continue

            # Bare genus fallback
            entry = {"nome": clean_str(base)}
            if akas:
                entry["aka"] = [clean_str(a) for a in akas if clean_str(a) != entry["nome"]]
            out[sid] = entry
            continue

    return out


def main():
    species_list = json.load(open(SPECIES, encoding="utf-8"))
    print(f"Loaded {len(species_list)} species from {SPECIES}")

    configs = [
        ("tr", "Turkish", CURATED_TR, GENUS_TR, EPITHETS_TR, "prefix_space"),
        ("es", "Spanish", CURATED_ES, GENUS_ES, EPITHETS_ES, "postfix_space"),
        ("fr", "French", CURATED_FR, GENUS_FR, EPITHETS_FR, "postfix_space"),
        ("de", "German", CURATED_DE, GENUS_DE, EPITHETS_DE, "prefix_hyphen"),
        ("ru", "Russian", CURATED_RU, GENUS_RU, EPITHETS_RU, "postfix_space"),
        ("zh", "Chinese", CURATED_ZH, GENUS_ZH, EPITHETS_ZH, "prefix_concat"),
        ("ja", "Japanese", CURATED_JA, GENUS_JA, EPITHETS_JA, "prefix_concat"),
        ("id", "Indonesian", CURATED_ID, GENUS_ID, EPITHETS_ID, "postfix_space"),
        ("hi", "Hindi", CURATED_HI, GENUS_HI, EPITHETS_HI, "prefix_space"),
        ("sw", "Swahili", CURATED_SW, GENUS_SW, EPITHETS_SW, "postfix_space"),
    ]

    summary = {}
    for lang, name, curated, genus_map, ep_map, style in configs:
        out_file = ROOT / "data" / f"names_{lang}.json"
        names_dict = build_language_dict(species_list, curated, genus_map, ep_map, style)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(names_dict, f, ensure_ascii=False, indent=None, separators=(",", ":"))
        pct = len(names_dict) / len(species_list) * 100
        summary[lang] = len(names_dict)
        print(f"[{lang.upper()} - {name}] Generated {out_file.name} with {len(names_dict)} / {len(species_list)} taxa ({pct:.1f}%).")

    print("\\n--- Summary of all generated dictionaries ---")
    for k, v in summary.items():
        print(f"data/names_{k}.json: {v} species")


if __name__ == "__main__":
    main()
