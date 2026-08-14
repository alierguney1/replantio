#!/usr/bin/env python3
"""Build localized common name dictionaries for all supported languages in Replantio.

Target languages:
- es: Spanish (Español) -> data/names_es.json
- fr: French (Français) -> data/names_fr.json
- de: German (Deutsch) -> data/names_de.json
- zh: Chinese (中文) -> data/names_zh.json
- ja: Japanese (日本語) -> data/names_ja.json
- ru: Russian (Русский) -> data/names_ru.json
- id: Indonesian (Bahasa Indonesia) -> data/names_id.json
- hi: Hindi (हिन्दी) -> data/names_hi.json
- sw: Swahili (Kiswahili) -> data/names_sw.json

Format matching names_pt.json & names_tr.json:
{"<species_id>": {"nome": "<name>", "aka": ["<synonym1>", ...]}}
"""
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"

# ==============================================================================
# UNIVERSAL GENUS MAPPINGS ACROSS ALL 9 LANGUAGES
# ==============================================================================

# Spanish Genus Dictionary
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

# French Genus Dictionary
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

# German Genus Dictionary
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

# Russian Genus Dictionary
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

# Chinese Genus Dictionary
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

# Japanese Genus Dictionary
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

# Indonesian Genus Dictionary
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

# Hindi Genus Dictionary
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

# Swahili Genus Dictionary
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



# ==============================================================================
# CURATED SPECIES DICTIONARIES
# ==============================================================================



CURATED_ES = {'Abies alba': 'abeto blanco|abeto común', 'Abies balsamea': 'abeto balsámico|abeto del bálsamo', 'Abies concolor': 'abeto del colorado|abeto blanco de california', 'Abies grandis': 'abeto gigante', 'Abies nordmanniana': 'abeto del cáucaso|abeto de normandía', 'Acacia dealbata': 'mosa|mimosa plateada|acacia mimosa', 'Acacia farnesiana': 'aromo|espinillo|acacia de las indias', 'Acacia melanoxylon': 'acacia negra|acacia de madera negra', 'Acacia nilotica': 'acacia de egipto|goma arábiga', 'Acacia saligna': 'acacia azul|acacia de hoja azul', 'Acacia senegal': 'árbol de la goma arábiga|acacia del senegal', 'Acer campestre': 'arce común|arce menor', 'Acer platanoides': 'arce real|arce de noruega', 'Acer pseudoplatanus': 'falso plátano|arce blanco|sicómoro', 'Acer saccharum': 'arce azucarero|arce del azúcar', 'Adansonia digitata': 'baobab|árbol botella', 'Alnus glutinosa': 'aliso común|aliso negro|alno', 'Alnus incana': 'aliso gris|aliso blanco', 'Annona cherimola': 'chirimoya|chirimoyo', 'Annona muricata': 'guanábana|catuche', 'Annona squamosa': 'anón|chirimoya de la habana', 'Araucaria angustifolia': 'pino paraná|pino de brasil|araucaria misionera', 'Araucaria araucana': 'pehuén|pino araucano|araucaria', 'Araucaria heterophylla': 'pino de norfolk|araucaria excelsa', 'Arbutus unedo': 'madroño|madroñera', 'Artocarpus altilis': 'árbol del pan|frutipán', 'Artocarpus heterophyllus': 'yaca|árbol de jaca', 'Azadirachta indica': 'nim|neem|árbol del nim', 'Betula pendula': 'abedul común|abedul blanco|abedul péndulo', 'Betula pubescens': 'abedul pubescente', 'Carpinus betulus': 'carpe común|hojarazo|charmilla', 'Carya illinoinensis': 'pacano|nogal americano|nuez pecana', 'Castanea crenata': 'castaño japonés', 'Castanea dentata': 'castaño americano', 'Castanea mollissima': 'castaño chino', 'Castanea sativa': 'castaño|castaño común|castaño europeo', 'Casuarina equisetifolia': 'casuarina|árbol de la tristeza|pino de australia', 'Cedrus atlantica': 'cedro del atlas', 'Cedrus deodara': 'cedro del himalaya|cedro deodara', 'Cedrus libani': 'cedro del líbano', 'Celtis australis': 'almez|almezo|latonero', 'Ceratonia siliqua': 'algarrobo|algarrobero', 'Cercis siliquastrum': 'árbol del amor|árbol de judas|ciclamor', 'Citrus aurantiifolia': 'lima|limero', 'Citrus aurantium': 'naranjo amargo|naranjo agrio', 'Citrus limon': 'limonero|limón', 'Citrus paradisi': 'pomelo|toronja', 'Citrus reticulata': 'mandarino|mandarina', 'Citrus sinensis': 'naranjo dulce|naranjo|naranja', 'Cocos nucifera': 'cocotero|palma de coco', 'Coffea arabica': 'cafeto arábico|café', 'Coffea canephora': 'cafeto robusta|café robusta', 'Corylus avellana': 'avellano|avellano común', 'Corylus colurna': 'avellano turco', 'Cupressus arizonica': 'ciprés de arizona|ciprés azul', 'Cupressus sempervirens': 'ciprés común|ciprés del mediterráneo|ciprés piramidal', 'Cydonia oblonga': 'membrillero|membrillo', 'Diospyros kaki': 'caqui|kaki|persimonio', 'Elaeis guineensis': 'palma aceitera|palma africana de aceite', 'Eriobotrya japonica': 'níspero japonés|níspero del japón', 'Eucalyptus camaldulensis': 'eucalipto rojo|eucalipto camaldulense', 'Eucalyptus globulus': 'eucalipto blanco|eucalipto azul', 'Eucalyptus grandis': 'eucalipto rosado|eucalipto grande', 'Fagus grandifolia': 'haya americana', 'Fagus sylvatica': 'haya común|haya europea|haya', 'Ficus benjamina': 'benjamina|ficus benjamina', 'Ficus carica': 'higuera|higuera común', 'Ficus elastica': 'árbol del caucho|gomero|ficus elástica', 'Fraxinus excelsior': 'fresno común|fresno norteño', 'Fraxinus ornus': 'fresno de flor|fresno del maná', 'Ginkgo biloba': 'ginkgo|árbol de los cuarenta escudos', 'Gleditsia triacanthos': 'acacia de tres espinas|gleditsia', 'Grevillea robusta': 'roble sedoso|grevillea|árbol de fuego', 'Hevea brasiliensis': 'árbol del caucho|seringuera', 'Ilex paraguariensis': 'yerba mate|árbol del mate', 'Jacaranda mimosifolia': 'jacarandá|tarco', 'Juglans nigra': 'nogal negro|nogal negro americano', 'Juglans regia': 'nogal común|nogal europeo|nogal', 'Juniperus communis': 'enebro común|enebro', 'Juniperus oxycedrus': 'enebro de la miera|cada', 'Larix decidua': 'alerce europeo|alerce', 'Laurus nobilis': 'laurel|laurel común|lauro', 'Liquidambar styraciflua': 'liquidámbar americano|ocozol', 'Liriodendron tulipifera': 'tulípero de virginia|árbol de las tulipas', 'Macadamia integrifolia': 'macadamia|nuez de macadamia', 'Magnolia grandiflora': 'magnolio|magnolia común', 'Malus domestica': 'manzano|manzano común', 'Mangifera indica': 'mango|árbol de mango', 'Melia azedarach': 'cinamomo|árbol del paraíso|agracejo', 'Morus alba': 'morera blanca|morera', 'Morus nigra': 'moral negro|moral|mora negra', 'Myrtus communis': 'mirto|arrayán', 'Olea europaea': 'olivo|olivera|aceituno', 'Paulownia tomentosa': 'paulonia imperial|árbol de la emperatriz', 'Persea americana': 'aguacate|palto|aguacatero', 'Phoenix canariensis': 'palmera canaria|palma fénix', 'Phoenix dactylifera': 'palmera datilera|datilero', 'Picea abies': 'abeto rojo|pícea común', 'Pinus brutia': 'pino de calabria|pino turco', 'Pinus canariensis': 'pino canario', 'Pinus halepensis': 'pino carrasco|pino de alepo', 'Pinus nigra': 'pino salgareño|pino negral|pino laricio', 'Pinus pinaster': 'pino rodeno|pino marítimo|pino negral', 'Pinus pinea': 'pino piñonero|pino manso', 'Pinus ponderosa': 'pino ponderosa|pino amarillo', 'Pinus radiata': 'pino insigne|pino de monterey', 'Pinus strobus': 'pino de weymouth|pino blanco americano', 'Pinus sylvestris': 'pino silvestre|pino albar|pino del norte', 'Pistacia lentiscus': 'lentisco|mata charneca', 'Pistacia terebinthus': 'cornicabra|terebinto', 'Pistacia vera': 'pistachero|alfóncigo|árbol del pistacho', 'Platanus orientalis': 'plátano oriental', 'Platanus x acerifolia': 'plátano de sombra|plátano de paseo', 'Populus alba': 'álamo blanco|chopo blanco', 'Populus nigra': 'álamo negro|chopo negro', 'Populus tremula': 'álamo temblón|chopo temblón', 'Prosopis juliflora': 'algarroba|mezquite', 'Prunus amygdalus': 'almendro|almendrero', 'Prunus armeniaca': 'albaricoquero|damasco', 'Prunus avium': 'cerezo|cerezo silvestre', 'Prunus cerasifera': 'ciruelo mirobolano|cerezo de jardín', 'Prunus cerasus': 'guindo|cerezo ácido', 'Prunus domestica': 'ciruelo|ciruelo europeo', 'Prunus dulcis': 'almendro|almendro común', 'Prunus persica': 'melocotonero|duraznero|durazno', 'Prunus spinosa': 'endrino|ciruelo silvestre', 'Pseudotsuga menziesii': 'abeto de douglas|pino de oregón', 'Psidium guajava': 'guayabo|guayaba', 'Punica granatum': 'granado|granada', 'Pyrus communis': 'peral|peral común', 'Quercus agrifolia': 'encina de california|roble de california', 'Quercus alba': 'roble blanco americano', 'Quercus cerris': 'roble cabelludo|roble turco', 'Quercus coccifera': 'coscoja|marrubio', 'Quercus frainetto': 'roble de hungría', 'Quercus ilex': 'encina|carrasca|chaparro', 'Quercus petraea': 'roble albar|roble sésil', 'Quercus pubescens': 'roble pubescente', 'Quercus robur': 'roble común|roble carballo|roble pedunculado', 'Quercus rubra': 'roble rojo americano', 'Quercus suber': 'alcornoque|alcornoque mediterráneo', 'Robinia pseudoacacia': 'falsa acacia|robinia|acacia blanca', 'Salix alba': 'sauce blanco|sauce común', 'Salix babylonica': 'sauce llorón', 'Sambucus nigra': 'saúco negro|saúco común', 'Schinus molle': 'falso pimentero|aguaribay|árbol de la pimienta', 'Sequoiadendron giganteum': 'secuoya gigante|árbol mamut', 'Sequoia sempervirens': 'secuoya roja|secuoya de california', 'Swietenia macrophylla': 'caoba|caoba de honduras', 'Syzygium aromaticum': 'árbol del clavo|clavero', 'Tamarindus indica': 'tamarindo', 'Tamarix gallica': 'tamarisco|taray', 'Taxus baccata': 'tejo|tejo común', 'Tectona grandis': 'teca|árbol de teca', 'Theobroma cacao': 'cacao|árbol del cacao', 'Thuja occidentalis': 'tuya occidental|árbol de la vida', 'Tilia cordata': 'tilo de hoja pequeña|tilo silvestre', 'Tilia platyphyllos': 'tilo de hoja ancha|tilo común', 'Ulmus americana': 'olmo americano', 'Ulmus glabra': 'olmo de montaña', 'Ulmus minor': 'olmo común|olmo negro|negrillo', 'Vitex agnus-castus': 'sauzgatillo|hierba de la castidad', 'Vitis vinifera': 'vid|vid europea|parra', 'Ziziphus jujuba': 'azufaifo|jinjolero|azufaifa', 'Allium cepa': 'cebolla', 'Allium sativum': 'ajo', 'Apium graveolens': 'apio', 'Arachis hypogaea': 'cacahuete|maní', 'Avena sativa': 'avena', 'Beta vulgaris': 'remolacha', 'Brassica napus': 'colza|canola', 'Capsicum annuum': 'pimiento|chile', 'Cicer arietinum': 'garbanzo', 'Cucumis sativus': 'pepino', 'Cucurbita pepo': 'calabacín|calabaza', 'Daucus carota': 'zanahoria', 'Fragaria ananassa': 'fresa|fresón', 'Glycine max': 'soja|soya', 'Gossypium hirsutum': 'algodón', 'Helianthus annuus': 'girasol', 'Hordeum vulgare': 'cebada', 'Ipomoea batatas': 'batata|camote|boniato', 'Lactuca sativa': 'lechuga', 'Lens culinaris': 'lenteja', 'Medicago sativa': 'alfalfa', 'Nicotiana tabacum': 'tabaco', 'Oryza sativa': 'arroz', 'Phaseolus vulgaris': 'judía|frijol|habichuela|poroto', 'Pisum sativum': 'guisante|arveja|chícharo', 'Solanum lycopersicum': 'tomate|tomatera', 'Lycopersicon esculentum': 'tomate', 'Solanum tuberosum': 'patata|papa', 'Spinacia oleracea': 'espinaca', 'Trifolium pratense': 'trébol rojo|trébol violeta', 'Trifolium repens': 'trébol blanco', 'Triticum aestivum': 'trigo|trigo harinero', 'Zea mays ssp. mays': 'maíz', 'Zea mays': 'maíz'}
CURATED_FR = {'Abies alba': 'sapin blanc|sapin pectiné|sapin des vosges', 'Abies balsamea': 'sapin baumier', 'Abies concolor': 'sapin du colorado|sapin concolore', 'Abies grandis': 'grand sapin|sapin de vancouver', 'Abies nordmanniana': 'sapin de nordmann|sapin du caucase', 'Acacia dealbata': "mimosa des fleuristes|mimosa d'hiver|acacia", 'Acacia farnesiana': 'cassier|mimosa de farnèse', 'Acacia melanoxylon': 'acacia à bois noir|mimosa à bois noir', 'Acacia nilotica': "gommier rouge|acacia d'égypte", 'Acacia saligna': 'mimosa bleuâtre|acacia bleuâtre', 'Acacia senegal': 'gommier blanc|acacia du sénégal', 'Acer campestre': 'érable champêtre', 'Acer platanoides': 'érable plane|faux platane', 'Acer pseudoplatanus': 'érable sycomore|sycomore', 'Acer saccharum': 'érable à sucre', 'Adansonia digitata': 'baobab africain|arbre bouteille', 'Alnus cordata': 'aulne de corse|aulne à feuilles en cœur', 'Alnus glutinosa': 'aulne glutineux|aulne noir|vergne', 'Alnus incana': 'aulne blanc|aulne blanchâtre', 'Annona cherimola': 'chérimolier|anone', 'Annona muricata': 'corossolier|corossol épineux', 'Araucaria angustifolia': 'pin du paraná|araucaria du brésil', 'Araucaria araucana': 'désespoir des singes|pin du chili|araucaria', 'Arbutus unedo': 'arbousier|arbre aux fraises', 'Artocarpus altilis': 'arbre à pain', 'Artocarpus heterophyllus': 'jacquier', 'Azadirachta indica': 'margousier|arbre neem|neem', 'Betula pendula': 'bouleau verruqueux|bouleau blanc', 'Betula pubescens': 'bouleau pubescent', 'Carpinus betulus': 'charme commun|charmille', 'Carya illinoinensis': 'pacanier|noix de pécan', 'Castanea crenata': 'châtaignier du japon', 'Castanea dentata': "châtaignier d'amérique", 'Castanea mollissima': 'châtaignier de chine', 'Castanea sativa': 'châtaignier commun|châtaignier', 'Casuarina equisetifolia': 'filao|bois de fer|casuarina', 'Cedrus atlantica': "cèdre de l'atlas", 'Cedrus deodara': "cèdre de l'himalaya|cèdre déodar", 'Cedrus libani': 'cèdre du liban', 'Celtis australis': 'micocoulier de provence|micocoulier', 'Ceratonia siliqua': 'caroubier', 'Cercis siliquastrum': 'arbre de judée|gainier commun', 'Citrus aurantiifolia': 'limettier|lime acide', 'Citrus aurantium': 'bigaradier|oranger amer', 'Citrus limon': 'citronnier|citron', 'Citrus paradisi': 'pomelo|pamplemousse', 'Citrus reticulata': 'mandarinier|mandarine', 'Citrus sinensis': 'oranger|orange douce', 'Cocos nucifera': 'cocotier|palmier de coco', 'Coffea arabica': "caféier d'arabie|café arabica", 'Coffea canephora': 'caféier robusta|café robusta', 'Corylus avellana': 'noisetier commun|coudrier', 'Corylus colurna': 'noisetier de byzance', 'Cupressus arizonica': "cyprès de l'arizona|cyprès bleu", 'Cupressus sempervirens': "cyprès toujours vert|cyprès d'italie|cyprès de provence", 'Cydonia oblonga': 'cognassier|coing', 'Diospyros kaki': 'plaqueminier du japon|kaki', 'Elaeis guineensis': 'palmier à huile', 'Eriobotrya japonica': 'néflier du japon|bibacier', 'Eucalyptus camaldulensis': 'gommier rouge|eucalyptus des rivières', 'Eucalyptus globulus': 'gommier bleu|eucalyptus commun', 'Eucalyptus grandis': 'eucalyptus rose', 'Fagus grandifolia': "hêtre d'amérique", 'Fagus sylvatica': 'hêtre commun|hêtre européen|fayard', 'Ficus carica': 'figuier commun|figuier', 'Ficus elastica': 'caoutchouc|figuier élastique', 'Fraxinus excelsior': 'frêne élevé|frêne commun', 'Fraxinus ornus': 'frêne à fleurs|frêne à manne', 'Ginkgo biloba': 'arbre aux quarante écus|ginkgo', 'Gleditsia triacanthos': "févier d'amérique|févier épineux", 'Grevillea robusta': "chêne soyeux d'australie|grévillée robuste", 'Hevea brasiliensis': 'hévéa|arbre à caoutchouc', 'Ilex paraguariensis': 'yerba maté|maté', 'Jacaranda mimosifolia': 'jacaranda|flamboyant bleu', 'Juglans nigra': "noyer noir|noyer d'amérique", 'Juglans regia': 'noyer commun|noyer de perse', 'Juniperus communis': 'genévrier commun|genévrier', 'Juniperus oxycedrus': 'cade|genévrier oxycèdre', 'Larix decidua': "mélèze d'europe|mélèze", 'Laurus nobilis': "laurier noble|laurier-sauce|laurier d'apollon", 'Liquidambar styraciflua': "copalme d'amérique|liquidambar", 'Liriodendron tulipifera': 'tulipier de virginie', 'Macadamia integrifolia': 'noyer du queensland|macadamia', 'Magnolia grandiflora': 'magnolia à grandes fleurs', 'Malus domestica': 'pommier commun|pommier', 'Mangifera indica': 'manguier', 'Melia azedarach': 'margousier à feuilles de frêne|lilas des indes', 'Morus alba': 'mûrier blanc', 'Morus nigra': 'mûrier noir', 'Myrtus communis': 'myrte commun|myrte', 'Olea europaea': "olivier|olivier d'europe", 'Paulownia tomentosa': 'paulownia impérial|arbre impérial', 'Persea americana': 'avocatier', 'Phoenix canariensis': 'palmier des canaries', 'Phoenix dactylifera': 'palmier-dattier|dattier', 'Picea abies': 'épicéa commun|épicéa des vosges', 'Pinus brutia': 'pin de calabre|pin turc', 'Pinus canariensis': 'pin des canaries', 'Pinus halepensis': "pin d'alep", 'Pinus nigra': "pin noir d'autriche|pin noir", 'Pinus pinaster': 'pin maritime|pin des landes', 'Pinus pinea': 'pin parasol|pin pignon', 'Pinus ponderosa': "pin ponderosa|pin jaune d'amérique", 'Pinus radiata': 'pin de monterey|pin insigne', 'Pinus strobus': 'pin de weymouth|pin blanc', 'Pinus sylvestris': 'pin sylvestre|pin du nord', 'Pistacia lentiscus': 'lentisque|arbre au mastic', 'Pistacia terebinthus': 'térébinthe|pistachier térébinthe', 'Pistacia vera': 'pistachier vrai|pistachier', 'Platanus orientalis': "platane d'orient", 'Platanus x acerifolia': "platane commun|platane à feuilles d'érable", 'Populus alba': 'peuplier blanc|peuplier de hollande', 'Populus nigra': 'peuplier noir', 'Populus tremula': 'peuplier tremble|tremble', 'Prunus amygdalus': 'amandier|amandier commun', 'Prunus armeniaca': 'abricotier', 'Prunus avium': 'merisier|cerisier des oiseaux|cerisier sauvage', 'Prunus cerasifera': 'prunier myrobolan|myrobolan', 'Prunus cerasus': 'cerisier aigre|griottier', 'Prunus domestica': 'prunier commun|prunier', 'Prunus dulcis': 'amandier', 'Prunus persica': 'pêcher|pêcher commun', 'Prunus spinosa': 'prunellier|épine noire', 'Pseudotsuga menziesii': 'douglas|sapin de douglas', 'Psidium guajava': 'goyavier', 'Punica granatum': 'grenadier|grenadier commun', 'Pyrus communis': 'poirier commun|poirier', 'Quercus agrifolia': 'chêne vert de californie', 'Quercus alba': "chêne blanc d'amérique", 'Quercus cerris': 'chêne chevelu|chêne de bourgogne', 'Quercus coccifera': 'chêne kermès|chêne des garrigues', 'Quercus ilex': 'chêne vert|yeuse', 'Quercus petraea': 'chêne sessile|chêne rouvre', 'Quercus pubescens': 'chêne pubescent|chêne blanc', 'Quercus robur': 'chêne pédonculé|chêne blanc|chêne commun', 'Quercus rubra': "chêne rouge d'amérique", 'Quercus suber': 'chêne-liège', 'Robinia pseudoacacia': 'robinier faux-acacia|acacia', 'Salix alba': 'saule blanc|saule argenté', 'Salix babylonica': 'saule pleureur', 'Sambucus nigra': 'sureau noir', 'Sequoiadendron giganteum': 'séquoia géant|arbre mammouth', 'Sequoia sempervirens': "séquoia à feuilles d'if|séquoia toujours vert", 'Swietenia macrophylla': "acajou du honduras|acajou d'amérique", 'Syzygium aromaticum': 'giroflier|arbre à clou de girofle', 'Tamarindus indica': 'tamarinier', 'Taxus baccata': "if commun|if d'europe|if", 'Tectona grandis': "teck|teck d'indochine", 'Theobroma cacao': 'cacaoyer|cacaotier', 'Thuja occidentalis': 'thuja occidental|arbre de vie', 'Tilia cordata': 'tilleul à petites feuilles|tilleul des bois', 'Tilia platyphyllos': 'tilleul à grandes feuilles', 'Ulmus glabra': 'orme de montagne', 'Ulmus minor': 'orme champêtre|orme blanc', 'Vitex agnus-castus': 'gattilier|arbre au poivre', 'Vitis vinifera': 'vigne cultivée|vigne rouge|vigne', 'Ziziphus jujuba': 'jujubier commun|jujubier', 'Allium cepa': 'oignon', 'Allium sativum': 'ail', 'Apium graveolens': 'céleri', 'Arachis hypogaea': 'arachide|cacahuète', 'Avena sativa': 'avoine', 'Beta vulgaris': 'betterave', 'Brassica napus': 'colza', 'Capsicum annuum': 'poivron|piment', 'Cicer arietinum': 'pois chiche', 'Cucumis sativus': 'concombre', 'Cucurbita pepo': 'courgette|citrouille', 'Daucus carota': 'carotte', 'Fragaria ananassa': 'fraisier cultivé|fraise', 'Glycine max': 'soja', 'Gossypium hirsutum': 'cotonnier', 'Helianthus annuus': 'tournesol', 'Hordeum vulgare': 'orge', 'Ipomoea batatas': 'patate douce', 'Lactuca sativa': 'laitue', 'Lens culinaris': 'lentille', 'Medicago sativa': 'luzerne', 'Nicotiana tabacum': 'tabac', 'Oryza sativa': 'riz', 'Phaseolus vulgaris': 'haricot commun|haricot', 'Pisum sativum': 'pois cultivé|petit pois', 'Solanum lycopersicum': 'tomate', 'Lycopersicon esculentum': 'tomate', 'Solanum tuberosum': 'pomme de terre', 'Spinacia oleracea': 'épinard', 'Trifolium pratense': 'trèfle violet|trèfle des prés', 'Trifolium repens': 'trèfle blanc', 'Triticum aestivum': 'blé tendre|froment', 'Zea mays ssp. mays': 'maïs', 'Zea mays': 'maïs'}
CURATED_DE = {'Abies alba': 'weiß-tanne|silbertanne|tanne', 'Abies balsamea': 'balsam-tanne', 'Abies concolor': 'kolorado-tanne|grau-tanne', 'Abies grandis': 'küsten-tanne|riesen-tanne', 'Abies nordmanniana': 'nordmann-tanne|kaukasus-tanne', 'Acacia dealbata': 'silber-akazie|falsche mimose', 'Acacia farnesiana': 'antillen-akazie|süße akazie', 'Acacia melanoxylon': 'australische schwarzholz-akazie', 'Acacia nilotica': 'ägyptische akazie|arabischer gummi-baum', 'Acacia senegal': 'verek-akazie|gummiarabikum-baum', 'Acer campestre': 'feld-ahorn|maßholder', 'Acer platanoides': 'spitz-ahorn', 'Acer pseudoplatanus': 'berg-ahorn', 'Acer saccharum': 'zucker-ahorn', 'Adansonia digitata': 'afrikanischer affenbrotbaum|baobab', 'Alnus cordata': 'herzblättrige erle|korsische erle', 'Alnus glutinosa': 'schwarz-erle|rot-erle', 'Alnus incana': 'grau-erle|weiß-erle', 'Annona cherimola': 'cherimoya|zuckerapfel', 'Annona muricata': 'stachelanone|sauersack', 'Araucaria angustifolia': 'brasilianische araukarie|parana-kiefer', 'Araucaria araucana': 'chilenische araukarie|andentanne', 'Arbutus unedo': 'westlicher erdbeerbaum|erdbeerbaum', 'Artocarpus altilis': 'echter brotfruchtbaum|brotfrucht', 'Artocarpus heterophyllus': 'jackfruchtbaum|jackfrucht', 'Azadirachta indica': 'neembaum|niembaum', 'Betula pendula': 'hänge-birke|sand-birke|weiß-birke', 'Betula pubescens': 'moor-birke|haar-birke', 'Carpinus betulus': 'hainbuche|weißbuche|hagebuche', 'Carya illinoinensis': 'pakanbaum|pekannuss', 'Castanea crenata': 'japanische kastanie', 'Castanea dentata': 'amerikanische kastanie', 'Castanea mollissima': 'chinesische kastanie', 'Castanea sativa': 'edelkastanie|esskastanie|marone', 'Casuarina equisetifolia': 'schachtelhalmblättrige kasuarine|eisenholz', 'Cedrus atlantica': 'atlas-zeder', 'Cedrus deodara': 'himalaya-zeder', 'Cedrus libani': 'libanon-zeder', 'Celtis australis': 'europäischer zürgelbaum', 'Ceratonia siliqua': 'johannisbrotbaum|karubenbaum', 'Cercis siliquastrum': 'gewöhnlicher judasbaum|judasbaum', 'Citrus aurantiifolia': 'echte limette|limone', 'Citrus aurantium': 'bitterorange|pomeranze', 'Citrus limon': 'zitronenbaum|zitrone', 'Citrus paradisi': 'grapefruit|paradiesapfel', 'Citrus reticulata': 'mandarine|mandarinenbaum', 'Citrus sinensis': 'orange|apfelsine', 'Cocos nucifera': 'kokospalme|kokosnuss', 'Coffea arabica': 'arabica-kaffee|bergkaffee', 'Coffea canephora': 'robusta-kaffee', 'Corylus avellana': 'gemeine hasel|haselnussstrauch', 'Corylus colurna': 'baum-hasel|türkische hasel', 'Cupressus arizonica': 'arizona-zypresse', 'Cupressus sempervirens': 'mittelmeer-zypresse|echte zypresse', 'Cydonia oblonga': 'quitte|echte quitte', 'Diospyros kaki': 'kakibaum|kaki', 'Elaeis guineensis': 'ölpalme|afrikanische ölpalme', 'Eriobotrya japonica': 'japanische wollmispel|loquat|mispel', 'Eucalyptus camaldulensis': 'roter eukalyptus', 'Eucalyptus globulus': 'blauer eukalyptus|fieberbaum', 'Eucalyptus grandis': 'roten eukalyptus', 'Fagus grandifolia': 'amerikanische buche', 'Fagus sylvatica': 'rotbuche|buche', 'Ficus carica': 'echte feige|feigenbaum', 'Ficus elastica': 'gummibaum|kautschukfeige', 'Fraxinus excelsior': 'gemeine esche|hoch-esche', 'Fraxinus ornus': 'blumen-esche|manna-esche', 'Ginkgo biloba': 'ginkgobaum|ginkgo|fächerblattbaum', 'Gleditsia triacanthos': 'amerikanische gleditschie|lederhülsenbaum', 'Grevillea robusta': 'australische silbereiche|seideneiche', 'Hevea brasiliensis': 'kautschukbaum|parakautschukbaum', 'Ilex paraguariensis': 'mate-strauch|mate-tee', 'Jacaranda mimosifolia': 'palisanderholzbaum|blauglockenbaum|jakaranda', 'Juglans nigra': 'schwarznuss|schwarzer walnussbaum', 'Juglans regia': 'echte walnuss|walnussbaum', 'Juniperus communis': 'gemeiner wacholder|heidewacholder', 'Juniperus oxycedrus': 'spanischer wacholder|stech-wacholder', 'Larix decidua': 'europäische lärche|lärche', 'Laurus nobilis': 'echter lorbeer|lorbeerbaum', 'Liquidambar styraciflua': 'amerikanischer amberbaum', 'Liriodendron tulipifera': 'tulpenbaum|echter tulpenbaum', 'Macadamia integrifolia': 'macadamianuss|queenslandnuss', 'Magnolia grandiflora': 'immergrüne magnolie', 'Malus domestica': 'kultur-apfel|apfelbaum', 'Mangifera indica': 'mangobaum|mango', 'Melia azedarach': 'zedrachbaum|indischer flieder', 'Morus alba': 'weiße maulbeere', 'Morus nigra': 'schwarze maulbeere', 'Myrtus communis': 'gemeine myrte|brautmyrte', 'Olea europaea': 'olivenbaum|echter ölbaum', 'Paulownia tomentosa': 'blauglockenbaum|kaiser-paulownie', 'Persea americana': 'avocadobaum|avocado', 'Phoenix canariensis': 'kanarische dattelpalme', 'Phoenix dactylifera': 'echte dattelpalme|dattelbaum', 'Picea abies': 'gemeine fichte|rotfichte|wald-fichte', 'Pinus brutia': 'kalabrische kiefer|türkische kiefer', 'Pinus canariensis': 'kanarische kiefer', 'Pinus halepensis': 'aleppo-kiefer', 'Pinus nigra': 'schwarz-kiefer|österreichische schwarzkiefer', 'Pinus pinaster': 'see-kiefer|strand-kiefer', 'Pinus pinea': 'pinie|italienische steinkiefer', 'Pinus ponderosa': 'gelb-kiefer|ponderosa-kiefer', 'Pinus radiata': 'monterey-kiefer|strahlige kiefer', 'Pinus strobus': 'weymouth-kiefer|strobe', 'Pinus sylvestris': 'wald-kiefer|gemeine kiefer|föhre', 'Pistacia lentiscus': 'mastixstrauch|wilde pistazie', 'Pistacia terebinthus': 'terebinthe|terpentin-pistazie', 'Pistacia vera': 'echte pistazie|pistazienbaum', 'Platanus orientalis': 'morgenländische platane', 'Platanus x acerifolia': 'ahornblättrige platane|gemeine platane', 'Populus alba': 'silber-pappel|weiß-pappel', 'Populus nigra': 'schwarz-pappel', 'Populus tremula': 'zitter-pappel|espe', 'Prunus amygdalus': 'mandelbaum|mandel', 'Prunus armeniaca': 'marille|aprikosenbaum', 'Prunus avium': 'vogel-kirsche|süßkirsche', 'Prunus cerasifera': 'kirschpflaume|myrobalane', 'Prunus cerasus': 'sauerkirsche|weichselkirsche', 'Prunus domestica': 'pflaumenbaum|zwetschge', 'Prunus dulcis': 'mandelbaum', 'Prunus persica': 'pfirsichbaum|pfirsich', 'Prunus spinosa': 'schlehdorn|schlehe|schwarzdorn', 'Pseudotsuga menziesii': 'gewöhnliche douglaspflanze|douglasie', 'Psidium guajava': 'echte guave|guavenbaum', 'Punica granatum': 'granatapfelbaum|granatapfel', 'Pyrus communis': 'kultur-birne|birnbaum', 'Quercus agrifolia': 'kalifornische steineiche', 'Quercus alba': 'amerikanische weißeiche', 'Quercus cerris': 'zerr-eiche', 'Quercus coccifera': 'kermes-eiche', 'Quercus ilex': 'stein-eiche|grün-eiche', 'Quercus petraea': 'trauben-eiche|winter-eiche', 'Quercus pubescens': 'flaum-eiche', 'Quercus robur': 'stiel-eiche|sommer-eiche|deutsche eiche', 'Quercus rubra': 'amerikanische rot-eiche|roteiche', 'Quercus suber': 'kork-eiche', 'Robinia pseudoacacia': 'gewöhnliche robinie|silberregen|falsche akazie', 'Salix alba': 'silber-weide', 'Salix babylonica': 'echte trauer-weide', 'Sambucus nigra': 'schwarzer holunder|holler', 'Sequoiadendron giganteum': 'riesenmammutbaum|mammutbaum', 'Sequoia sempervirens': 'küstenmammutbaum|redwood', 'Swietenia macrophylla': 'amerikanisches mahagoni', 'Syzygium aromaticum': 'gewürznelkenbaum|gewürznelke', 'Tamarindus indica': 'tamarindenbaum|tamarinde', 'Taxus baccata': 'europäische eibe|gemeine eibe', 'Tectona grandis': 'teakbaum|teak', 'Theobroma cacao': 'kakaobaum|kakao', 'Thuja occidentalis': 'abendländischer lebensbaum|thuja', 'Tilia cordata': 'winter-linde|stein-linde', 'Tilia platyphyllos': 'sommer-linde|großblättrige linde', 'Ulmus glabra': 'berg-ulme', 'Ulmus minor': 'feld-ulme', 'Vitex agnus-castus': 'mönchspfeffer|keuschlamm', 'Vitis vinifera': 'echte weinrebe|weinstock', 'Ziziphus jujuba': 'chinesische jujube|brustbeere', 'Allium cepa': 'zwiebel|küchenzwiebel', 'Allium sativum': 'knoblauch', 'Apium graveolens': 'sellerie', 'Arachis hypogaea': 'erdnuss', 'Avena sativa': 'saat-hafer|hafer', 'Beta vulgaris': 'zuckerrübe|rote bete', 'Brassica napus': 'raps', 'Capsicum annuum': 'paprika|chilipfeffer', 'Cicer arietinum': 'kichererbse', 'Cucumis sativus': 'gurke', 'Cucurbita pepo': 'gartenkürbis|zucchini', 'Daucus carota': 'karotte|möhre', 'Fragaria ananassa': 'garten-erdbeere|erdbeere', 'Glycine max': 'sojabohne', 'Gossypium hirsutum': 'baumwolle', 'Helianthus annuus': 'sonnenblume', 'Hordeum vulgare': 'gerste', 'Ipomoea batatas': 'süßkartoffel|batate', 'Lactuca sativa': 'kopfsalat|gartensalat', 'Lens culinaris': 'linse', 'Medicago sativa': 'luzerne|alfa-alfa', 'Nicotiana tabacum': 'tabak', 'Oryza sativa': 'reis', 'Phaseolus vulgaris': 'gartenbohne|grüne bohne', 'Pisum sativum': 'erbse|garten-erbse', 'Solanum lycopersicum': 'tomate', 'Lycopersicon esculentum': 'tomate', 'Solanum tuberosum': 'kartoffel', 'Spinacia oleracea': 'spinat', 'Trifolium pratense': 'rot-klee|wiesen-klee', 'Trifolium repens': 'weiß-klee', 'Triticum aestivum': 'weichweizen|saat-weizen', 'Zea mays ssp. mays': 'mais', 'Zea mays': 'mais'}
CURATED_RU = {'Abies alba': 'пихта белая|пихта европейская', 'Abies balsamea': 'пихта бальзамическая', 'Abies concolor': 'пихта одноцветная', 'Abies nordmanniana': 'пихта нордмана|пихта кавказская', 'Acacia dealbata': 'акация серебристая|мимоза', 'Acacia farnesiana': 'акация фарнеза', 'Acer campestre': 'клён полевой|паклён', 'Acer platanoides': 'клён остролистный|клён платановидный', 'Acer pseudoplatanus': 'клён белый|явор', 'Acer saccharum': 'клён сахарный', 'Adansonia digitata': 'баобаб|адансония пальчатая', 'Alnus glutinosa': 'ольха чёрная|ольха клейкая', 'Alnus incana': 'ольха серая', 'Betula pendula': 'берёза повислая|берёза бородавчатая', 'Betula pubescens': 'берёза пушистая', 'Carpinus betulus': 'граб обыкновенный', 'Castanea sativa': 'каштан посевной|каштан благородный', 'Cedrus atlantica': 'кедр атласский', 'Cedrus deodara': 'кедр гималайский', 'Cedrus libani': 'кедр ливанский', 'Citrus limon': 'лимон', 'Citrus sinensis': 'апельсин', 'Corylus avellana': 'лещина обыкновенная|фундук', 'Cupressus sempervirens': 'кипарис вечнозелёный', 'Fagus sylvatica': 'бук европейский|бук лесной', 'Ficus carica': 'инжир|смоковница|фиговое дерево', 'Fraxinus excelsior': 'ясень обыкновенный', 'Ginkgo biloba': 'гинкго двулопастный|гинкго', 'Juglans regia': 'грецкий орех', 'Juniperus communis': 'можжевельник обыкновенный', 'Larix decidua': 'лиственница европейская', 'Laurus nobilis': 'лавр благородный', 'Malus domestica': 'яблоня домашняя', 'Morus alba': 'шелковица белая|тутовое дерево', 'Morus nigra': 'шелковица чёрная', 'Olea europaea': 'олива европейская|маслина', 'Picea abies': 'ель обыкновенная|ель европейская', 'Pinus brutia': 'сосна калабрийская|сосна пицундская', 'Pinus nigra': 'сосна чёрная', 'Pinus pinea': 'сосна пиния|пиния', 'Pinus sylvestris': 'сосна обыкновенная|сосна лесная', 'Platanus orientalis': 'платан восточный|чинара', 'Populus alba': 'тополь белый|тополь серебристый', 'Populus nigra': 'тополь чёрный|осокорь', 'Populus tremula': 'осина|тополь дрожащий', 'Prunus armeniaca': 'абрикос обыкновенный', 'Prunus avium': 'черешня', 'Prunus cerasus': 'вишня обыкновенная', 'Prunus domestica': 'слива домашняя', 'Prunus dulcis': 'миндаль обыкновенный', 'Prunus persica': 'персик обыкновенный', 'Pyrus communis': 'груша обыкновенная', 'Quercus ilex': 'дуб каменный', 'Quercus petraea': 'дуб скальный', 'Quercus robur': 'дуб черешчатый|дуб обыкновенный|дуб летний', 'Quercus rubra': 'дуб красный', 'Quercus suber': 'дуб пробковый', 'Robinia pseudoacacia': 'робиния ложноакациевая|белая акация', 'Salix alba': 'ива белая|ветла', 'Taxus baccata': 'тис ягодный', 'Tilia cordata': 'липа мелколистная|липа сердцевидная', 'Ulmus minor': 'вяз малый|берест', 'Vitis vinifera': 'виноград культурный', 'Allium cepa': 'лук репчатый', 'Allium sativum': 'чеснок', 'Avena sativa': 'овёс посевной', 'Beta vulgaris': 'свёкла обыкновенная', 'Glycine max': 'соя культурная', 'Helianthus annuus': 'подсолнечник однолетний', 'Hordeum vulgare': 'ячмень обыкновенный', 'Oryza sativa': 'рис посевной', 'Phaseolus vulgaris': 'фасоль обыкновенная', 'Pisum sativum': 'горох посевной', 'Solanum lycopersicum': 'томат|помидор', 'Solanum tuberosum': 'картофель', 'Triticum aestivum': 'пшеница мягкая', 'Zea mays ssp. mays': 'кукуруза', 'Zea mays': 'кукуруза'}
CURATED_ZH = {'Abies alba': '欧洲白冷杉|白冷杉', 'Abies balsamea': '胶冷杉|加拿大香脂冷杉', 'Abies concolor': '白冷杉|科罗拉多冷杉', 'Abies nordmanniana': '高加索冷杉|诺德曼冷杉', 'Acacia dealbata': '银荆|澳洲金合欢', 'Acacia farnesiana': '鸭皂树|金合欢', 'Acacia melanoxylon': '黑木相思|黑木金合欢', 'Acacia senegal': '阿拉伯胶树|塞内加尔金合欢', 'Acer campestre': '欧洲田野槭|田园槭', 'Acer platanoides': '挪威槭|欧亚槭', 'Acer pseudoplatanus': '欧亚槭|糖槭', 'Acer saccharum': '糖槭|糖枫', 'Adansonia digitata': '猴面包树', 'Alnus glutinosa': '欧洲黑桤木|黑桤木', 'Annona cherimola': '秘鲁番荔枝', 'Annona muricata': '刺果番荔枝', 'Araucaria angustifolia': '巴拉那松|巴西南洋杉', 'Araucaria araucana': '智利南洋杉', 'Arbutus unedo': '草莓树|野草莓树', 'Artocarpus altilis': '面包树', 'Artocarpus heterophyllus': '菠萝蜜', 'Azadirachta indica': '印楝|苦楝树', 'Betula pendula': '垂枝桦|白桦', 'Carpinus betulus': '欧洲鹅耳枥', 'Carya illinoinensis': '碧根果|美国山核桃', 'Castanea mollissima': '板栗', 'Castanea sativa': '欧洲栗|西洋栗', 'Casuarina equisetifolia': '木麻黄', 'Cedrus atlantica': '阿特拉斯雪松', 'Cedrus deodara': '雪松', 'Cedrus libani': '黎巴嫩雪松', 'Celtis australis': '欧洲朴树', 'Ceratonia siliqua': '长角豆|角豆树', 'Cercis siliquastrum': '南欧紫荆', 'Citrus limon': '柠檬', 'Citrus reticulata': '柑橘|橘子', 'Citrus sinensis': '甜橙|脐橙', 'Cocos nucifera': '椰子|椰子树', 'Coffea arabica': '小粒咖啡|阿拉比卡咖啡', 'Corylus avellana': '欧洲榛|榛子', 'Cupressus sempervirens': '地中海柏木|意大利柏木', 'Cydonia oblonga': '榅桲', 'Diospyros kaki': '柿树|柿子', 'Elaeis guineensis': '油棕', 'Eucalyptus camaldulensis': '赤桉', 'Eucalyptus globulus': '蓝桉', 'Fagus sylvatica': '欧洲山毛榉|欧洲水青冈', 'Ficus carica': '无花果', 'Ficus elastica': '印度榕|橡胶榕', 'Fraxinus excelsior': '欧洲白蜡树', 'Ginkgo biloba': '银杏|白果树', 'Gleditsia triacanthos': '美国皂荚', 'Hevea brasiliensis': '巴西橡胶树|三叶橡胶树', 'Juglans regia': '核桃|胡桃', 'Juniperus communis': '欧洲刺柏|刺柏', 'Larix decidua': '欧洲落叶松', 'Laurus nobilis': '月桂|月桂树', 'Liquidambar styraciflua': '北美枫香', 'Macadamia integrifolia': '澳洲坚果|夏威夷果', 'Malus domestica': '苹果|苹果树', 'Mangifera indica': '芒果', 'Morus alba': '桑树|白桑', 'Morus nigra': '黑桑', 'Olea europaea': '油橄榄|橄榄', 'Paulownia tomentosa': '毛泡桐|泡桐', 'Persea americana': '牛油果|鳄梨', 'Phoenix dactylifera': '海枣|椰枣', 'Picea abies': '欧洲云杉', 'Pinus brutia': '土耳其松', 'Pinus halepensis': '阿勒颇松', 'Pinus nigra': '欧洲黑松', 'Pinus pinea': '意大利石松', 'Pinus sylvestris': '欧洲赤松|欧洲针松', 'Pistacia vera': '开心果|阿月浑子', 'Platanus orientalis': '三球悬铃木|法国梧桐', 'Populus alba': '银白杨', 'Populus nigra': '黑杨', 'Populus tremula': '欧洲山杨', 'Prunus armeniaca': '杏|杏树', 'Prunus avium': '欧洲甜樱桃|车厘子', 'Prunus cerasus': '欧洲酸樱桃', 'Prunus domestica': '欧洲李', 'Prunus dulcis': '扁桃|巴旦木', 'Prunus persica': '桃树|桃', 'Punica granatum': '石榴', 'Pyrus communis': '西洋梨|白梨', 'Quercus ilex': '冬青栎', 'Quercus robur': '夏栎|欧洲栎|英国栎', 'Quercus rubra': '红栎|北美红橡', 'Quercus suber': '栓皮栎|软木栎', 'Robinia pseudoacacia': '刺槐|洋槐', 'Salix alba': '白柳', 'Salix babylonica': '垂柳', 'Taxus baccata': '欧洲红豆杉', 'Tectona grandis': '柚木', 'Theobroma cacao': '可可树|可可', 'Tilia cordata': '小叶椴|心叶椴', 'Ulmus minor': '欧洲山榆', 'Vitis vinifera': '葡萄|酿酒葡萄', 'Allium cepa': '洋葱', 'Allium sativum': '大蒜', 'Arachis hypogaea': '花生', 'Avena sativa': '燕麦', 'Beta vulgaris': '甜菜', 'Brassica napus': '油菜', 'Glycine max': '大豆|黄豆', 'Gossypium hirsutum': '陆地棉|棉花', 'Helianthus annuus': '向日葵', 'Hordeum vulgare': '大麦', 'Ipomoea batatas': '红薯|甘薯', 'Lactuca sativa': '生菜|莴苣', 'Oryza sativa': '水稻|稻谷', 'Phaseolus vulgaris': '菜豆|四季豆', 'Pisum sativum': '豌豆', 'Solanum lycopersicum': '番茄|西红柿', 'Solanum tuberosum': '马铃薯|土豆', 'Triticum aestivum': '小麦', 'Zea mays ssp. mays': '玉米', 'Zea mays': '玉米'}
CURATED_JA = {'Abies alba': 'ヨーロッパモミ|モミ', 'Abies balsamea': 'バルサムモミ', 'Abies nordmanniana': 'コーカサスモミ|ノルドマンモミ', 'Acacia dealbata': 'フサアカシア|ミモザ', 'Acer campestre': 'コバノトネリコカエデ', 'Acer platanoides': 'ノルウェーカエデ', 'Acer pseudoplatanus': 'セイヨウカジカエデ', 'Acer saccharum': 'サトウカエデ|シュガーメープル', 'Adansonia digitata': 'バオバブ', 'Alnus glutinosa': 'ヨーロッパハンノキ|ハンノキ', 'Betula pendula': 'シラカンバ|シラカバ', 'Carpinus betulus': 'セイヨウシデ|シデ', 'Carya illinoinensis': 'ペカン|ピーカンナッツ', 'Castanea sativa': 'ヨーロッパグリ|クリ', 'Casuarina equisetifolia': 'トクサバモクマオウ|モクマオウ', 'Cedrus atlantica': 'アトラスシーダー', 'Cedrus deodara': 'ヒマラヤスギ', 'Cedrus libani': 'レバノンスギ', 'Ceratonia siliqua': 'キャロブ|イナゴマメ', 'Citrus limon': 'レモン', 'Citrus sinensis': 'スイートオレンジ|オレンジ', 'Cocos nucifera': 'ココヤシ|ヤシ', 'Coffea arabica': 'アラビカコーヒーノキ|コーヒーノキ', 'Corylus avellana': 'セイヨウハシバミ|ヘーゼルナッツ', 'Cupressus sempervirens': 'イトスギ|セイヨウヒノキ', 'Cydonia oblonga': 'マルメロ', 'Diospyros kaki': 'カキノキ|カキ', 'Eucalyptus camaldulensis': 'リバーレッドガム|ユーカリ', 'Eucalyptus globulus': 'タスマニアンブルーガム|ユーカリ', 'Fagus sylvatica': 'ヨーロッパブナ|ブナ', 'Ficus carica': 'イチジク|イチジクノキ', 'Fraxinus excelsior': 'セイヨウトネリコ', 'Ginkgo biloba': 'イチョウ', 'Juglans regia': 'ペルシャグルミ|クルミ', 'Juniperus communis': 'セイヨウネズ|ジュニパー', 'Larix decidua': 'ヨーロッパカラマツ', 'Laurus nobilis': 'ゲッケイジュ|ローレル', 'Malus domestica': 'リンゴ|セイヨウリンゴ', 'Mangifera indica': 'マンゴー', 'Morus alba': 'マグワ|クワ', 'Olea europaea': 'オリーブ|オリーブノキ', 'Paulownia tomentosa': 'キリ|桐', 'Persea americana': 'アボカド', 'Phoenix dactylifera': 'ナツメヤシ', 'Picea abies': 'ドイツトウヒ|ヨーロッパトウヒ', 'Pinus brutia': 'カラブリアマツ', 'Pinus nigra': 'ヨーロッパクロマツ', 'Pinus pinea': 'イタリアカサマツ', 'Pinus sylvestris': 'ヨーロッパアカマツ|オウシュウアカマツ', 'Pistacia vera': 'ピスタチオ', 'Populus alba': 'ウラジロハコヤナギ|ギンドロ', 'Populus nigra': 'クロポプラ', 'Populus tremula': 'ヨーロッパヤマナラシ', 'Prunus armeniaca': 'アンズ|アプリコット', 'Prunus avium': 'セイヨウミザクラ|サクランボ', 'Prunus cerasus': 'スミミザクラ|サワーチェリー', 'Prunus domestica': 'セイヨウスモモ|プルーン', 'Prunus dulcis': 'アーモンド|ヘントウ', 'Prunus persica': 'モモ|ハナモモ', 'Punica granatum': 'ザクロ', 'Pyrus communis': 'セイヨウナシ|洋梨', 'Quercus ilex': 'ヒイラギガシ', 'Quercus robur': 'イングリッシュオーク|ヨーロッパナラ|ナラ', 'Quercus rubra': 'アカガシワ|レッドオーク', 'Quercus suber': 'コルクガシ', 'Robinia pseudoacacia': 'ハリエンジュ|ニセアカシア', 'Salix alba': 'シロヤナギ', 'Salix babylonica': 'シダレヤナギ', 'Taxus baccata': 'ヨーロッパイチイ', 'Tectona grandis': 'チーク', 'Theobroma cacao': 'カカオ', 'Tilia cordata': 'フユボダイジュ', 'Ulmus minor': 'コバノニレ', 'Vitis vinifera': 'ヨーロッパブドウ|ブドウ', 'Allium cepa': 'タマネギ', 'Allium sativum': 'ニンニク', 'Arachis hypogaea': 'ラッカセイ|落花生', 'Avena sativa': 'エンバク|オート麦', 'Glycine max': 'ダイズ|大豆', 'Helianthus annuus': 'ヒマワリ', 'Hordeum vulgare': 'オオムギ|大麦', 'Oryza sativa': 'イネ|米', 'Phaseolus vulgaris': 'インゲンマメ', 'Pisum sativum': 'エンドウ', 'Solanum lycopersicum': 'トマト', 'Solanum tuberosum': 'ジャガイモ', 'Triticum aestivum': 'コムギ|小麦', 'Zea mays ssp. mays': 'トウモロコシ', 'Zea mays': 'トウモロコシ'}
CURATED_ID = {'Abies alba': 'cemara perak eropa|fir', 'Acacia auriculiformis': 'akasia daun lebar|akasia', 'Acacia mangium': 'akasia mangium|tongke hitam', 'Adansonia digitata': 'baobab|ki tambleg', 'Albizia chinensis': 'sengon laut|jeungjing', 'Albizia falcataria': 'sengon|albasia', 'Ananas comosus': 'nanas', 'Annona muricata': 'sirsak', 'Annona squamosa': 'srikaya', 'Artocarpus altilis': 'sukun', 'Artocarpus heterophyllus': 'nangka', 'Azadirachta indica': 'mindi|mimba', 'Cajanus cajan': 'kacang gude|kacang hiris', 'Capsicum annuum': 'cabai merah|cabai', 'Carica papaya': 'pepaya', 'Cassia fistula': 'trengguli|tengguli', 'Casuarina equisetifolia': 'cemara laut', 'Cinnamomum verum': 'kayu manis', 'Citrus limon': 'lemon', 'Citrus sinensis': 'jeruk manis', 'Cocos nucifera': 'kelapa', 'Coffea arabica': 'kopi arabika', 'Coffea canephora': 'kopi robusta', 'Curcuma longa': 'kunyit', 'Cymbopogon citratus': 'serai|sereh', 'Diospyros kaki': 'kesemek', 'Elaeis guineensis': 'kelapa sawit', 'Eucalyptus alba': 'kayu putih timor', 'Eucalyptus deglupta': 'kayu leda|eukaliptus pelangi', 'Ficus carica': 'pohon ara|tin', 'Ficus elastica': 'karet kebo|karet merah', 'Glycine max': 'kedelai', 'Hevea brasiliensis': 'pohon karet|karet', 'Ipomoea batatas': 'ubi jalar', 'Leucaena leucocephala': 'petai cina|lamtoro', 'Magnolia champaca': 'cempaka wangi', 'Mangifera indica': 'mangga', 'Manihot esculenta': 'singkong|ubi kayu', 'Moringa oleifera': 'kelor', 'Morus alba': 'murbei putih|besaran', 'Musa acuminata': 'pisang', 'Myristica fragrans': 'pala', 'Nicotiana tabacum': 'tembakau', 'Oryza sativa': 'padi|beras', 'Persea americana': 'alpukat', 'Phaseolus vulgaris': 'buncis', 'Pinus merkusii': 'tusam sumatera|pinus merkusii', 'Piper nigrum': 'lada hitam|merica', 'Psidium guajava': 'jambu biji|jambu kluthuk', 'Punica granatum': 'delima', 'Quercus robur': 'pohon ek eropa|ek', 'Saccharum officinarum': 'tebu', 'Syzygium aromaticum': 'cengkih|cengkeh', 'Tamarindus indica': 'asam jawa', 'Tectona grandis': 'jati|pohon jati', 'Theobroma cacao': 'kakao|cokelat', 'Vitis vinifera': 'anggur', 'Zea mays ssp. mays': 'jagung', 'Zea mays': 'jagung', 'Zingiber officinale': 'jahe'}
CURATED_HI = {'Abies pindrow': 'पिंड्रो देवदार|रघु', 'Acacia catechu': 'खैर|कत्था', 'Acacia nilotica': 'बबूल|कीकर', 'Acacia senegal': 'खेर|सफेद खैर', 'Aegle marmelos': 'बेल|बिल्व', 'Albizia lebbeck': 'सिरस|सरस', 'Allium cepa': 'प्याज़', 'Allium sativum': 'लहसुन', 'Aloe vera': 'घृतकुमारी|एलोवेरा', 'Artocarpus heterophyllus': 'कटहल', 'Azadirachta indica': 'नीम', 'Brassica juncea': 'सरसों|राई', 'Butea monosperma': 'पलाश|ढाक', 'Cajanus cajan': 'अरहर|तूर', 'Capsicum annuum': 'मिर्च', 'Carica papaya': 'पपीता', 'Cassia fistula': 'अमलतास', 'Cedrus deodara': 'देवदार', 'Cicer arietinum': 'चना', 'Cinnamomum verum': 'दालचीनी', 'Citrus limon': 'नींबू', 'Cocos nucifera': 'नारियल', 'Coffea arabica': 'कॉफी', 'Coriandrum sativum': 'धनिया', 'Curcuma longa': 'हल्दी', 'Cuminum cyminum': 'जीरा', 'Dalbergia sissoo': 'शीशम', 'Diospyros kaki': 'जापानी फल|तेंदू', 'Ficus benghalensis': 'बरगद|वट', 'Ficus carica': 'अंजीर', 'Ficus religiosa': 'पीपल', 'Glycine max': 'सोयाबीन', 'Gossypium hirsutum': 'कपास', 'Helianthus annuus': 'सूरजमुखी', 'Hordeum vulgare': 'जौ', 'Juglans regia': 'अखरोट', 'Lens culinaris': 'मसूर', 'Mangifera indica': 'आम', 'Moringa oleifera': 'सहजन|मुनगा', 'Morus alba': 'शहतूत', 'Musa acuminata': 'केला', 'Ocimum tenuiflorum': 'तुलसी', 'Oryza sativa': 'चावल|धान', 'Pennisetum glaucum': 'बाजरा', 'Phaseolus vulgaris': 'राजमा', 'Pinus roxburghii': 'चीड़', 'Pinus sylvestris': 'स्कॉच चीड़|चीड़', 'Piper nigrum': 'काली मिर्च', 'Pisum sativum': 'मटर', 'Prunus dulcis': 'बादाम', 'Psidium guajava': 'अमरूद', 'Punica granatum': 'अनार', 'Pyrus communis': 'नाशपाती', 'Quercus robur': 'शाहबलूत|ओक', 'Ricinus communis': 'अरंडी', 'Saccharum officinarum': 'गन्ना', 'Sesamum indicum': 'तिल', 'Solanum lycopersicum': 'टमाटर', 'Solanum tuberosum': 'आलू', 'Syzygium cumini': 'जामुन', 'Tamarindus indica': 'इमली', 'Tectona grandis': 'सागौन|सागवान', 'Terminalia arjuna': 'अर्जुन', 'Trigonella foenum-graecum': 'मेथी', 'Triticum aestivum': 'गेहूं', 'Vigna mungo': 'उड़द', 'Vigna radiata': 'मूंग', 'Vitis vinifera': 'अंगूर', 'Zea mays ssp. mays': 'मक्का', 'Zea mays': 'मक्का', 'Zingiber officinale': 'अदरक'}
CURATED_SW = {'Adansonia digitata': 'mbuyu|baobab', 'Allium cepa': 'kitunguu', 'Allium sativum': 'kitunguu saumu', 'Ananas comosus': 'nanasi', 'Annona muricata': 'mstafeli', 'Artocarpus heterophyllus': 'fenesi', 'Avicennia marina': 'mchu', 'Azadirachta indica': 'mwarobaini|mneem', 'Cajanus cajan': 'mbaazi', 'Capsicum annuum': 'pilipili hoho|pilipili', 'Carica papaya': 'mpapai|papai', 'Casuarina equisetifolia': 'mvinje', 'Cinnamomum verum': 'mdalasini', 'Citrus limon': 'mlimau|ndimu', 'Citrus sinensis': 'mchungwa|machungwa', 'Cocos nucifera': 'mnazi|nazi', 'Coffea arabica': 'mkahawa|kahawa', 'Curcuma longa': 'manjano', 'Cymbopogon citratus': 'mchai', 'Elaeis guineensis': 'mchikichi|chikichi', 'Eucalyptus camaldulensis': 'mkaratusi mwekundu|mkaratusi', 'Ficus carica': 'mtini|tini', 'Glycine max': 'soya', 'Gossypium hirsutum': 'mpamba|pamba', 'Helianthus annuus': 'alizeti', 'Ipomoea batatas': 'viazi vitamu', 'Mangifera indica': 'mwembe|embe', 'Manihot esculenta': 'muhogo', 'Moringa oleifera': 'mronge|muringa', 'Morus alba': 'mfursadi|mforosadi', 'Musa acuminata': 'mgomba|ndizi', 'Nicotiana tabacum': 'mtumbaku|tumbaku', 'Oryza sativa': 'mpunga|mchele', 'Pennisetum glaucum': 'uwele', 'Persea americana': 'mparachichi|parachichi', 'Phaseolus vulgaris': 'maharagwe', 'Pinus caribaea': 'msindano', 'Pinus patula': 'msindano wa milimani', 'Piper nigrum': 'mtilini|pilipili manga', 'Psidium guajava': 'mpera|mapera', 'Punica granatum': 'mkomamanga', 'Quercus robur': 'mwaloni wa ulaya|mwaloni', 'Rhizophora mucronata': 'mkoko', 'Ricinus communis': 'mbono', 'Saccharum officinarum': 'mwaa|muwa', 'Sesamum indicum': 'ufuta', 'Solanum lycopersicum': 'mnyanya|nyanya', 'Solanum tuberosum': 'viazi mbatata|viazi', 'Sorghum bicolor': 'mtama', 'Syzygium aromaticum': 'mkarufee|karafuu', 'Tamarindus indica': 'mkwaju|ukwaju', 'Tectona grandis': 'mti teak|msaji', 'Theobroma cacao': 'mkakao|kakao', 'Triticum aestivum': 'ngano', 'Vigna unguiculata': 'kikunde|kunde', 'Zea mays ssp. mays': 'mahindi', 'Zea mays': 'mahindi', 'Zingiber officinale': 'tangawizi'}

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


def build_language_dict(species_list, curated, genus_fallback):
    out = {}
    for sp in species_list:
        sid = str(sp["id"])
        sci = sp["sci"].strip()
        genus, epithet = binomial(sci)

        # 1. Exact sci match
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

        # 3. Genus fallback match
        if genus in genus_fallback:
            base, akas = genus_fallback[genus]
            entry = {"nome": clean_str(base)}
            if akas:
                entry["aka"] = [clean_str(a) for a in akas if clean_str(a) != entry["nome"]]
            out[sid] = entry
            continue

    return out


def main():
    species_list = json.load(open(SPECIES, encoding="utf-8"))
    print(f"Loaded {len(species_list)} species from {SPECIES}")

    # All 9 non-EN/PT/TR languages in Replantio
    configs = [
        ("es", "Spanish", CURATED_ES, GENUS_ES),
        ("fr", "French", CURATED_FR, GENUS_FR),
        ("de", "German", CURATED_DE, GENUS_DE),
        ("zh", "Chinese", CURATED_ZH, GENUS_ZH),
        ("ja", "Japanese", CURATED_JA, GENUS_JA),
        ("ru", "Russian", CURATED_RU, GENUS_RU),
        ("id", "Indonesian", CURATED_ID, GENUS_ID),
        ("hi", "Hindi", CURATED_HI, GENUS_HI),
        ("sw", "Swahili", CURATED_SW, GENUS_SW),
    ]

    summary = {}
    for lang, name, curated, genus_map in configs:
        out_file = ROOT / "data" / f"names_{lang}.json"
        names_dict = build_language_dict(species_list, curated, genus_map)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(names_dict, f, ensure_ascii=False, indent=None, separators=(",", ":"))
        pct = len(names_dict) / len(species_list) * 100
        summary[lang] = len(names_dict)
        print(f"[{lang.upper()} - {name}] Generated {out_file.name} with {len(names_dict)} / {len(species_list)} taxa ({pct:.1f}%).")

    print("\n--- Summary of all generated dictionaries ---")
    for k, v in summary.items():
        print(f"data/names_{k}.json: {v} species")


if __name__ == "__main__":
    main()
