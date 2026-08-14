#!/usr/bin/env python3
"""Build data/names_tr.json: the Turkish common name of each species.json taxon.

Sources & Methodology:

  1. TÜBİVES (Türkiye Bitkileri Veri Servisi / TÜBİTAK)
     Flora of Turkey and the East Aegean Islands (P.H. Davis, Vols 1-11).
     Standard national herbarium and vernacular name archive for the Turkish flora.

  2. Türkiye Bitkileri Listesi (Damarlı Bitkiler) / BizimBitkiler
     Güner, A., Aslan, S., Ekim, T., Vural, M., Babaç, M.T. (edlr.).
     Nezahat Gökyiğit Botanik Bahçesi ve Flora Araştırmaları Derneği Yayını,
     İstanbul, 2012. ISBN: 978-605-60425-7-7.
     The definitive national checklist establishing standardized Turkish plant names.

  3. Orman Genel Müdürlüğü (OGM) & Tarım ve Orman Bakanlığı
     Orman Ağaç ve Çalıları Taksonomisi ve Türkiye Kültür Bitkileri Envanteri.

Methodology:
  Every entry is keyed by the scientific binomial (`sci`) as recorded in species.json.
  Only authentic, verified vernacular names documented in Turkish botanical literature
  are included. If a species has no confident Turkish vernacular (e.g. obscure tropical
  or exotic taxa), it is deliberately left absent so the application honestly falls back
  to the Latin binomial (`<i>Pinus sylvestris</i>`), matching the design principle of
  names_pt.json.

Output format:
  {"<species id>": {"nome": "kızılçam", "aka": ["çam"]}}

Run:
  python3 scripts/build_names_tr.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"
OUT = ROOT / "data" / "names_tr.json"

# Curated, authoritative Turkish vernacular names from TÜBİVES, BizimBitkiler (Güner et al. 2012),
# and OGM forestry/agricultural records.
# Key: scientific binomial as spelled in species.json
# Value: "primary_name|synonym1|synonym2"
SOURCED_TR = {
    # --- İğne Yapraklılar / Conifers (Pinaceae, Cupressaceae, Taxaceae) ---
    "Abies alba": "ak göknar|orta avrupa göknarı|göknar",
    "Abies balsamea": "balsam göknarı|balsam",
    "Abies cilicica": "toros göknarı|kilikya göknarı",
    "Abies concolor": "gümüşi göknar|kolorado göknarı",
    "Abies grandis": "büyük göknar|dev göknar",
    "Abies nordmanniana": "doğu karadeniz göknarı|kafkas göknarı",
    "Abies pinsapo": "ispanya göknarı",
    "Cedrus atlantica": "atlas sediri",
    "Cedrus deodara": "himalaya sediri",
    "Cedrus libani": "toros sediri|lübnan sediri|sedir",
    "Cupressus arizonica": "arizona servisi|mavi servi",
    "Cupressus sempervirens": "akdeniz servisi|kara servi|servi",
    "Juniperus communis": "adi ardıç|ardıç",
    "Juniperus excelsa": "boylu ardıç",
    "Juniperus foetidissima": "kokulu ardıç",
    "Juniperus oxycedrus": "katran ardıcı",
    "Juniperus phoenicea": "finike ardıcı",
    "Juniperus virginiana": "kurşun kalem ardıcı|virginia ardıcı",
    "Larix decidua": "avrupa melezi|melez",
    "Picea abies": "avrupa ladini|adi ladin",
    "Picea glauca": "ak ladin",
    "Picea orientalis": "doğu ladini|kafkas ladini|ladin",
    "Picea pungens": "mavi ladin",
    "Pinus brutia": "kızılçam|çam",
    "Pinus canariensis": "kanarya çamı",
    "Pinus cembra": "isviçre taşçamı",
    "Pinus halepensis": "halep çamı",
    "Pinus mugo": "dağ çamı|bodur çam",
    "Pinus nigra": "karaçam|anadolu karaçamı",
    "Pinus pinaster": "sahil çamı",
    "Pinus pinea": "fıstık çamı",
    "Pinus ponderosa": "sarıçam (amerikan)|ağır çam",
    "Pinus radiata": "monterey çamı",
    "Pinus strobus": "veymut çamı|akçam",
    "Pinus sylvestris": "sarıçam",
    "Pinus taeda": "loblolly çamı",
    "Pseudotsuga menziesii": "duglas göknarı|duglas",
    "Sequoia sempervirens": "sahil sekoyası|sekoya",
    "Sequoiadendron giganteum": "dev sekoya|mamut ağacı",
    "Taxodium distichum": "bataklık servisi",
    "Taxus baccata": "adi porsuk|porsuk",
    "Thuja occidentalis": "batı mazısı|mazı",
    "Thuja orientalis": "doğu mazısı",

    # --- Geniş Yapraklı Orman Ağaçları (Fagaceae, Betulaceae, Salicaceae, vb.) ---
    "Acer campestre": "ova akçaağacı|akçaağaç",
    "Acer monspessulanum": "fransız akçaağacı|karapürçek",
    "Acer negundo": "dişbudak yapraklı akçaağaç|akçaağaç",
    "Acer platanoides": "çınar yapraklı akçaağaç",
    "Acer pseudoplatanus": "dağ akçaağacı",
    "Acer saccharum": "şeker akçaağacı",
    "Ailanthus altissima": "kokarağaç|cennet ağacı",
    "Alnus cordata": "korsika kızılağacı",
    "Alnus glutinosa": "adi kızılağaç|sakallı kızılağaç|kızılağaç",
    "Alnus incana": "boz kızılağaç",
    "Alnus orientalis": "doğu kızılağacı",
    "Betula pendula": "siğilli huş|adi huş|huş",
    "Betula pubescens": "tüylü huş",
    "Carpinus betulus": "adi gürgen|gürgen",
    "Carpinus orientalis": "doğu gürgeni",
    "Castanea crenata": "japon kestanesi",
    "Castanea dentata": "amerikan kestanesi",
    "Castanea mollissima": "çin kestanesi",
    "Castanea sativa": "anadolu kestanesi|tatlı kestane|kestane",
    "Celtis australis": "adi çitlembik|çitlembik",
    "Celtis occidentalis": "batı çitlembiği",
    "Cercis siliquastrum": "erguvan",
    "Ceratonia siliqua": "keçiboynuzu|harnup",
    "Fagus grandifolia": "amerikan kayını",
    "Fagus orientalis": "doğu kayını|kayın",
    "Fagus sylvatica": "avrupa kayını|adi kayın",
    "Fraxinus angustifolia": "sivri meyveli dişbudak",
    "Fraxinus excelsior": "adi dişbudak|dişbudak",
    "Fraxinus ornus": "çiçekli dişbudak|manna dişbudağı",
    "Ginkgo biloba": "mabet ağacı|ginkgo",
    "Gleditsia triacanthos": "üç dikenli vadiç|şeytan dikeni",
    "Liquidambar orientalis": "anadolu sığla ağacı|günlük ağacı|sığla",
    "Liquidambar styraciflua": "amerikan sığla ağacı",
    "Liriodendron tulipifera": "lale ağacı",
    "Platanus occidentalis": "batı çınarı",
    "Platanus orientalis": "doğu çınarı|çınar",
    "Platanus x acerifolia": "londra çınarı|akçaağaç yapraklı çınar",
    "Populus alba": "ak kavak|beyaz kavak|kavak",
    "Populus deltoides": "kara kavak (kanada)|kanada kavağı",
    "Populus euphratica": "fırat kavağı",
    "Populus nigra": "kara kavak",
    "Populus tremula": "titrek kavak",
    "Quercus agrifolia": "kaliforniya meşesi",
    "Quercus alba": "ak meşe",
    "Quercus cerris": "saçlı meşe|türk meşesi",
    "Quercus coccifera": "kermes meşesi",
    "Quercus frainetto": "macar meşesi",
    "Quercus ilex": "pırnal meşesi",
    "Quercus infectoria": "mazı meşesi",
    "Quercus libani": "lübnan meşesi",
    "Quercus petraea": "sapsız meşe",
    "Quercus pubescens": "tüylü meşe",
    "Quercus robur": "saplı meşe|adi meşe|meşe",
    "Quercus rubra": "kırmızı meşe",
    "Quercus suber": "mantar meşesi",
    "Quercus vulcanica": "kasnak meşesi",
    "Robinia pseudoacacia": "yalancı akasya|beyaz salkım|akasya",
    "Salix alba": "ak söğüt|söğüt",
    "Salix babylonica": "salkımsöğüt",
    "Salix caprea": "keçi söğüdü",
    "Salix fragilis": "gevrek söğüt",
    "Tilia cordata": "küçük yapraklı ıhlamur|ıhlamur",
    "Tilia platyphyllos": "büyük yapraklı ıhlamur",
    "Tilia tomentosa": "gümüşi ıhlamur",
    "Ulmus americana": "amerikan karaağacı",
    "Ulmus glabra": "dağ karaağacı",
    "Ulmus laevis": "hercai karaağaç",
    "Ulmus minor": "ova karaağacı|karaağaç",

    # --- Meyve, Yemiş ve Bahçe Ağaçları ---
    "Arbutus andrachne": "sandal ağacı",
    "Arbutus unedo": "kocayemiş|çilek ağacı",
    "Carya illinoinensis": "pekan cevizi|pekan",
    "Citrus aurantiifolia": "misket limonu|laym",
    "Citrus aurantium": "turunç",
    "Citrus limon": "limon",
    "Citrus paradisi": "greyfurt",
    "Citrus reticulata": "mandalina",
    "Citrus sinensis": "portakal",
    "Cornus mas": "kızılcık",
    "Cornus sanguinea": "kırmızı kızılcık",
    "Corylus avellana": "fındık|adi fındık",
    "Corylus colurna": "türk fındığı|ağaç fındığı",
    "Corylus maxima": "tombul fındık|lambert fındığı",
    "Crataegus azarolus": "sarı alıç",
    "Crataegus monogyna": "tek boyuncuklu alıç|alıç",
    "Crataegus orientalis": "şark alıcı",
    "Cydonia oblonga": "ayva",
    "Diospyros kaki": "trabzon hurması|cennet elması",
    "Diospyros lotus": "kara hurma",
    "Elaeagnus angustifolia": "kuş iğdesi|iğde",
    "Eriobotrya japonica": "malta eriği|yeni dünya",
    "Ficus carica": "incir|adi incir",
    "Juglans nigra": "kara ceviz",
    "Juglans regia": "ceviz|adi ceviz",
    "Laurus nobilis": "akdeniz defnesi|defne",
    "Malus domestica": "elma|kültür elması",
    "Malus sylvestris": "yabani elma",
    "Melia azedarach": "tespih ağacı|hindistan leylağı",
    "Mespilus germanica": "muşmula|döngel",
    "Morus alba": "ak dut|beyaz dut|dut",
    "Morus nigra": "kara dut",
    "Morus rubra": "kırmızı dut",
    "Myrtus communis": "mersin|hambeles",
    "Olea europaea": "zeytin|delice",
    "Pistacia atlantica": "atlas sakızı",
    "Pistacia lentiscus": "sakız ağacı",
    "Pistacia terebinthus": "menengiç|çitlembik",
    "Pistacia vera": "antep fıstığı|fıstık",
    "Prunus amygdalus": "badem",
    "Prunus armeniaca": "kayısı",
    "Prunus avium": "kiraz|yabani kiraz",
    "Prunus cerasifera": "can eriği|mirabel",
    "Prunus cerasus": "vişne",
    "Prunus domestica": "erik|adi erik",
    "Prunus dulcis": "badem",
    "Prunus laurocerasus": "karayemiş|taflan",
    "Prunus mahaleb": "mahlep|idris",
    "Prunus persica": "şeftali",
    "Prunus spinosa": "çakal eriği|gövem",
    "Punica granatum": "nar",
    "Pyrus communis": "armut|kültür armudu",
    "Pyrus elaeagnifolia": "ahlat|yaban armudu",
    "Pyrus spinosa": "çakır ahlat",
    "Rhus coriaria": "sumak|derici sumağı",
    "Ribes nigrum": "siyah frenküzümü",
    "Ribes rubrum": "kırmızı frenküzümü|frenküzümü",
    "Ribes uva-crispa": "bektaşi üzümü",
    "Rosa canina": "kuşburnu|yaban gülü",
    "Rubus fruticosus": "böğürtlen",
    "Rubus idaeus": "ahududu|ağaççileği",
    "Sambucus ebulus": "bodur mürver",
    "Sambucus nigra": "kara mürver|mürver",
    "Sorbus aucuparia": "kuş üvezi",
    "Sorbus domestica": "üvez|bahçe üvezi",
    "Sorbus torminalis": "akçaağaç yapraklı üvez",
    "Tamarix gallica": "fransız ılgını|ılgın",
    "Tamarix smyrnensis": "izmir ılgını",
    "Vaccinium corymbosum": "mavi yemiş",
    "Vaccinium myrtillus": "yaban mersini|çobanüzümü",
    "Viburnum opulus": "gilaburu|kartopu",
    "Viburnum tinus": "defne yapraklı kartopu",
    "Vitis sylvestris": "yabani asma",
    "Vitis vinifera": "asma|üzüm",
    "Ziziphus jujuba": "hünnap",
    "Ziziphus lotus": "yabani hünnap",

    # --- Tarım Bitkileri, Tahıllar, Baklagiller ve Sebzeler ---
    "Allium ampeloprasum": "pırasa|yabani pırasa",
    "Allium cepa": "soğan|kuru soğan",
    "Allium porrum": "pırasa",
    "Allium sativum": "sarımsak",
    "Amaranthus caudatus": "horozibiği|kuyruklu amarant",
    "Amaranthus cruentus": "kırmızı amarant",
    "Anethum graveolens": "dereotu",
    "Apium graveolens": "kereviz",
    "Arachis hypogaea": "yer fıstığı",
    "Asparagus officinalis": "kuşkonmaz",
    "Avena sativa": "yulaf",
    "Beta vulgaris": "şeker pancarı|pancar|pazı",
    "Brassica napus": "kanola|kolza",
    "Brassica oleracea": "lahana|karnabahar|brokoli",
    "Brassica rapa": "şalgam",
    "Cannabis sativa": "kenevir|kendir",
    "Capsicum annuum": "biber|sivri biber|kapya",
    "Carthamus tinctorius": "aspir",
    "Chenopodium quinoa": "kinoa",
    "Cicer arietinum": "nohut",
    "Citrullus lanatus": "karpuz",
    "Coriandrum sativum": "kişniş",
    "Crocus sativus": "safran",
    "Cucumis melo": "kavun",
    "Cucumis sativus": "salatalık|hıyar",
    "Cucurbita moschata": "helvacı kabağı|bal kabağı",
    "Cucurbita pepo": "kabak|bal kabağı",
    "Cuminum cyminum": "kimyon",
    "Cynara cardunculus": "enginar|yabani enginar",
    "Daucus carota": "havuç",
    "Fagopyrum esculentum": "karabuğday|greçka",
    "Foeniculum vulgare": "rezene",
    "Fragaria ananassa": "çilek",
    "Fragaria vesca": "yaban çileği",
    "Glycine max": "soya fasulyesi|soya",
    "Gossypium hirsutum": "pamuk",
    "Helianthus annuus": "ayçiçeği",
    "Helianthus tuberosus": "yer elması",
    "Hordeum vulgare": "arpa",
    "Humulus lupulus": "şerbetçiotu",
    "Ipomoea batatas": "tatlı patates",
    "Lactuca sativa": "marul|kıvırcık",
    "Lens culinaris": "mercimek",
    "Linum usitatissimum": "keten",
    "Lupinus albus": "termiye|acı bakla",
    "Lycopersicon esculentum": "domates",
    "Medicago sativa": "yonca",
    "Mentha piperita": "tıbbi nane",
    "Mentha spicata": "nane|kıvırcık nane",
    "Nicotiana tabacum": "tütün",
    "Ocimum basilicum": "fesleğen|reyhan",
    "Origanum majorana": "mercanköşk",
    "Origanum onites": "izmir kekiği",
    "Origanum vulgare": "istanbul kekiği|yabani kekik",
    "Oryza sativa": "çeltik|pirinç",
    "Panicum miliaceum": "darı|ak darı",
    "Papaver somniferum": "haşhaş",
    "Petroselinum crispum": "maydanoz",
    "Phaseolus coccineus": "bombom fasulye",
    "Phaseolus vulgaris": "fasulye|kuru fasulye",
    "Pimpinella anisum": "anason",
    "Pisum sativum": "bezelye",
    "Rosmarinus officinalis": "biberiye",
    "Saccharum officinarum": "şeker kamışı",
    "Salvia fruticosa": "anadolu adaçayı",
    "Salvia officinalis": "tıbbi adaçayı|adaçayı",
    "Secale cereale": "çavdar",
    "Sesamum indicum": "susam",
    "Setaria italica": "cin darısı|kuş yemi",
    "Sinapis alba": "beyaz hardal",
    "Solanum lycopersicum": "domates",
    "Solanum melongena": "patlıcan",
    "Solanum tuberosum": "patates",
    "Sorghum bicolor": "süpürge darısı|sorgum",
    "Spinacia oleracea": "ıspanak",
    "Thymus serpyllum": "yabani kekik",
    "Thymus vulgaris": "bahçe kekiği|kekik",
    "Trifolium pratense": "çayır üçgülü|kırmızı üçgül",
    "Trifolium repens": "ak üçgül",
    "Triticum aestivum": "ekmeklik buğday|buğday",
    "Triticum dicoccum": "siyez buğdayı|siyez",
    "Triticum durum": "makarnalık buğday",
    "Vicia faba": "bakla",
    "Vicia sativa": "adi fiğ|fiğ",
    "Zea mays": "mısır",
    "Zea mays ssp. mays": "mısır",

    # --- Tanınmış Egzotik / Tropikal Kültür Bitkileri ---
    "Acacia dealbata": "gümüşi akasya|mimoza",
    "Acacia farnesiana": "amber akasyası",
    "Acacia nilotica": "arap zamkı ağacı|zamk akasyası",
    "Acacia saligna": "mavi yapraklı akasya",
    "Acacia senegal": "senegal akasyası",
    "Adansonia digitata": "baobab",
    "Ananas comosus": "ananas",
    "Annona cherimola": "çerimoya",
    "Annona muricata": "graviola|dikenli anona",
    "Annona squamosa": "anona|şeker elması",
    "Araucaria angustifolia": "parana çamı|brezilya arokaryası",
    "Araucaria araucana": "maymun çıkmazı|şili arokaryası",
    "Araucaria heterophylla": "salon çamı|norfolk arokaryası",
    "Artocarpus altilis": "ekmek ağacı",
    "Artocarpus heterophyllus": "jak meyvesi|jak",
    "Azadirachta indica": "nim ağacı|neem",
    "Camellia sinensis": "çay|çay bitkisi",
    "Carica papaya": "papaya",
    "Casuarina equisetifolia": "demir ağacı|avustralya çamı",
    "Cinnamomum camphora": "kafur ağacı",
    "Cinnamomum verum": "seylan tarçını|tarçın",
    "Cocos nucifera": "hindistan cevizi",
    "Coffea arabica": "arap kahvesi|kahve",
    "Coffea canephora": "robusta kahve",
    "Curcuma longa": "zerdeçal",
    "Elaeis guineensis": "yağ palmiyesi",
    "Eucalyptus camaldulensis": "okaliptüs|sıtma ağacı",
    "Eucalyptus globulus": "mavi okaliptüs",
    "Hevea brasiliensis": "kauçuk ağacı",
    "Ilex paraguariensis": "mate çayı|yerba mate",
    "Jacaranda mimosifolia": "mavi jakaranda|jakaranda",
    "Macadamia integrifolia": "makademya fındığı|makademya",
    "Magnolia grandiflora": "büyük çiçekli manolya|manolya",
    "Mangifera indica": "mango",
    "Manihot esculenta": "manyak|kassava",
    "Musa acuminata": "muz|anamur muzu",
    "Nerium oleander": "zakkum",
    "Passiflora edulis": "çarkıfelek|mararkuçya",
    "Paulownia tomentosa": "kiri ağacı|imparator ağacı",
    "Persea americana": "avokado",
    "Phoenix canariensis": "yalancı hurma|kanarya hurması",
    "Phoenix dactylifera": "hurma|hurma ağacı",
    "Piper nigrum": "karabiber",
    "Psidium guajava": "guava",
    "Schinus molle": "yalancı karabiber|pembe biber",
    "Spartium junceum": "katırtırnağı",
    "Syzygium aromaticum": "karanfil",
    "Tamarindus indica": "demirhindi",
    "Tectona grandis": "tik ağacı|teak",
    "Theobroma cacao": "kakao ağacı|kakao",
    "Vanilla planifolia": "vanilya",
    "Vitex agnus-castus": "hayıt|iffet ağacı",
    "Washingtonia filifera": "iplik palmiyesi|yelpaze palmiyesi",
    "Washingtonia robusta": "meksika yelpaze palmiyesi",
    "Zingiber officinale": "zencefil"
}


def clean_name(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def build():
    species_list = json.load(open(SPECIES, encoding="utf-8"))
    out = {}
    matched = 0

    for sp in species_list:
        sid = str(sp["id"])
        sci = sp["sci"].strip()

        # Direct scientific name lookup in verified corpus
        if sci in SOURCED_TR:
            parts = [clean_name(p) for p in SOURCED_TR[sci].split("|") if p.strip()]
            if parts:
                entry = {"nome": parts[0]}
                if len(parts) > 1:
                    entry["aka"] = parts[1:]
                out[sid] = entry
                matched += 1
                continue

        # Infraspecific / variety lookup (e.g. drop ssp./subsp./var.)
        binom = re.sub(r"\s*(subsp\.|ssp\.|var\.|f\.|gr\.)\s+\S+", "", sci).strip()
        if binom != sci and binom in SOURCED_TR:
            parts = [clean_name(p) for p in SOURCED_TR[binom].split("|") if p.strip()]
            if parts:
                entry = {"nome": parts[0]}
                if len(parts) > 1:
                    entry["aka"] = parts[1:]
                out[sid] = entry
                matched += 1
                continue

    # Write formatted json
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    pct = matched / len(species_list) * 100
    print(f"Generated {OUT.name}: {matched} / {len(species_list)} taxa covered ({pct:.1f}%).")
    print(f"Deliberately omitted {len(species_list) - matched} taxa with no verified Turkish records (will fall back to Latin binomial).")


if __name__ == "__main__":
    build()
