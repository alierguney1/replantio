import { aggregateClimate, scoreSpecies, grade, gradeColor, monthlyDaylengths } from "./scoring.js";
import { CLASSES, projection, maturityYears, co2eKgPerTree, co2eTonsPerHa, height, dbhCm, crownDiameterM, crownDisplayM, STEMS_PER_HA } from "./growth.js";

const $ = s => document.querySelector(s);
// ---------- language: browser-detected, four options, cycling toggle ----------
const LANGS = ["pt", "en", "es", "fr"];
const navLang = (navigator.language || "en").slice(0, 2).toLowerCase();
const storedLang = localStorage.getItem("lang");
const LANG = LANGS.includes(storedLang) ? storedLang : (LANGS.includes(navLang) ? navLang : "en");
const LOCALE = { pt: "pt-BR", en: "en-US", es: "es-419", fr: "fr-FR" }[LANG];
const PT = {
  "Draw an area anywhere on Earth: Replantio shows which species would thrive there, how they grow, the carbon they store, and what restoration costs. Open data, open model.": "Desenhe uma área em qualquer lugar do mundo: o Replantio mostra quais espécies prosperariam ali, como crescem, o carbono que guardam e quanto custa restaurar. Dados abertos, modelo aberto.",
  "created by": "criado por",
  "Open source on GitHub": "Código aberto no GitHub",
  "Go to my location": "Ir para minha localização",
  "Could not get your location.": "Não foi possível obter sua localização.",
  "Analyzing area": "Analisando a área",
  "Analysis failed": "Falha na análise",
  "Retry": "Tentar de novo",
  "Climate normals &middot; Open-Meteo ERA5, 10 years daily": "Normais climáticas &middot; Open-Meteo ERA5, 10 anos diários",
  "Soil profile &middot; SoilGrids 2.0": "Perfil do solo &middot; SoilGrids 2.0",
  "Scoring {n} species": "Avaliando {n} espécies",
  "Could not load the climate record for this point. The Open-Meteo archive may be busy or rate limited; wait a moment and retry.":
    "Não foi possível carregar o histórico climático deste ponto. O arquivo do Open-Meteo pode estar ocupado ou limitado; aguarde um momento e tente de novo.",
  "{s} of {n} species rate suitable or better": "{s} de {n} espécies avaliadas como adequadas ou melhores",
  "Site climate &middot; ERA5 2015&ndash;2024": "Clima do local &middot; ERA5 2015&ndash;2024",
  "Recommended species": "Espécies recomendadas",
  "soil pH": "pH do solo", "elevation": "elevação", "daylength": "duração do dia", "record low": "mínima recorde",
  "sun": "sol", "humidity": "umidade", "cloud": "nuvens", "slope": "declive", "facing": "face",
  "kWh/m²·day": "kWh/m²·dia",
  "mean daily shortwave radiation, all weather included": "radiação solar média diária, já contando o tempo nublado",
  "high humidity plus high cloud cover marks fog-prone sites": "umidade e nebulosidade altas indicam locais com neblina",
  "no data": "sem dados", "n/a": "n/d",
  "E": "L", "W": "O", "SW": "SO", "NW": "NO",
  "This area looks like open water (no soil data, elevation {e} m). Species scores here reflect climate only and are unlikely to be meaningful.":
    "Esta área parece ser água aberta (sem dados de solo, elevação {e} m). As notas abaixo refletem só o clima e provavelmente não fazem sentido.",
  "Show scores anyway": "Mostrar mesmo assim",
  "Nothing clears the bar for this filter here.": "Nada passa do corte com esse filtro aqui.",
  "Show {n} more": "Mostrar mais {n}",
  "Native here": "Nativas daqui",
  "Only species in this country's native flora (WCVP)": "Só espécies da flora nativa deste país (WCVP)",
  "All uses": "Todos os usos",
  "timber": "madeira", "fruit": "fruta", "environment": "ambiental", "medicinal": "medicinal",
  "forage": "forragem", "materials": "materiais", "food": "alimento", "ornamental": "ornamental",
  "native": "nativa", "nearby": "na região",
  "Part of the native flora of this country (WCVP)": "Parte da flora nativa deste país (WCVP)",
  "GBIF occurrence records near this area": "Registros de ocorrência (GBIF) perto desta área",
  "Excellent": "Excelente", "Very suitable": "Muito adequada", "Suitable": "Adequada",
  "Marginal": "Marginal", "Very marginal": "Muito marginal", "Not suitable": "Inadequada",
  "{rate} growth &middot; {zone}": "crescimento {rate} &middot; {zone}",
  "fast": "rápido", "medium": "médio", "slow": "lento", "tropical": "tropical", "temperate": "temperado",
  "Temperature": "Temperatura", "Rainfall": "Chuva", "Soil pH": "pH do solo",
  "tolerated {a} to {d} · optimal {b} to {c}": "tolera {a} a {d} · ótimo {b} a {c}",
  "Photoperiod outside this species' range: 0.5 penalty applied.": "Fotoperíodo fora da faixa da espécie: penalidade de 0,5 aplicada.",
  "Needs winter dormancy; the coldest month here is too warm for it.": "Precisa de dormência de inverno; o mês mais frio aqui é quente demais.",
  "Origin": "Origem", "Use": "Uso", "Time to max height": "Tempo até altura máx.", "Mature canopy": "Copa adulta",
  "all origins": "todas", "any": "qualquer", "under {n} years": "até {n} anos",
  "native here": "nativas daqui", "all uses": "todos", "Maturity": "Maturidade",
  "no limit": "sem limite", "no minimum": "sem mínimo",
  "criteria": "critérios", "clear criteria": "limpar critérios",
  "{n} of {t}": "{n} de {t}", "{n} species": "{n} espécies",
  "Reaches ~95% of its max height in ~{n} years (class-level model).": "Atinge ~95% da altura máxima em ~{n} anos (modelo por classe).",
  "Trunk &oslash; 20 yr": "Tronco &oslash; 20 anos", "Canopy, 20 yr": "Copa, 20 anos",
  "CO&#8322;e/tree, 20 yr": "CO&#8322;e/árvore, 20 anos", "Stand CO&#8322;e, 20 yr": "CO&#8322;e do plantio, 20 anos",
  "Best window": "Melhor janela", "Hardy to": "Resiste até",
  "Trees in this area, 3&times;3 m": "Árvores na área, 3&times;3 m", "Area CO&#8322;e by year 20": "CO&#8322;e da área em 20 anos",
  "mean": "média", "per year": "por ano", "y": "a", "yr": "anos", "trunk": "tronco",
  "Suitability follows the FAO EcoCrop model (trapezoidal climate envelopes, most-limiting-factor). Growth and carbon are class-level estimates":
    "A adequação segue o modelo EcoCrop da FAO (envelopes climáticos trapezoidais, fator mais limitante). Crescimento e carbono são estimativas por classe",
  "(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006), for screening, not planting prescriptions.":
    "(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006): triagem, não prescrição de plantio.",
  "Data:": "Dados:", "Photos: iNaturalist": "Fotos: iNaturalist", "Map:": "Mapa:",
  "Search a city or place": "Busque uma cidade ou lugar",
  "Draw area": "Desenhar área",
  "Click to drop points &middot; right-click, double-click or click the first point to close &middot; Esc cancels":
    "Clique para marcar pontos &middot; botão direito, duplo clique ou clique no primeiro ponto para fechar &middot; Esc cancela",
  "No matches": "Sem resultados",
  "Replantio · replanting intelligence": "Replantio · inteligência de replantio",
  "Habit": "Porte", "all habits": "todos os portes",
  "shrubs": "arbustos", "herbs": "ervas", "grasses": "gramíneas", "vines": "trepadeiras",
  "Cycle": "Ciclo", "{a} to {b} days": "{a} a {b} dias",
  "Find plantable land in this view": "Achar áreas plantáveis nesta vista",
  "Zoom in to city scale to scan for plantable land.": "Aproxime até a escala de cidade para escanear áreas plantáveis.",
  "Nothing promising in this view. Try another neighborhood.": "Nada promissor nesta vista. Tente outro canto.",
  "The land scan service is busy; try again in a minute.": "O serviço de varredura está ocupado; tente de novo em um minuto.",
  "click to analyze": "clique para analisar",
  "candidate areas": "áreas candidatas",
  "Simulate planting": "Simular plantio",
  "Stop simulation": "Fechar simulação",
  "year": "ano", "height": "altura", "crown": "copa",
  "Close": "Fechar", "Selected area": "Área selecionada", "fit": "ajuste",
  "Delete area": "Excluir área",
  "Import area (GeoJSON, KML, zipped shapefile)": "Importar área (GeoJSON, KML, shapefile zipado)",
  "No polygons found in the file.": "Nenhum polígono encontrado no arquivo.",
  "Could not read the file.": "Não foi possível ler o arquivo.",
  "The shapefile must use WGS84 geographic coordinates (like SARE requires).": "O shapefile precisa estar em coordenadas geográficas WGS84 (como o SARE exige).",
  "Report": "Relatório", "SHP (SARE)": "SHP (SARE)", "CSV": "CSV",
  "area": "área", "areas": "áreas", "planted": "plantados",
  "Legal &middot; Forest Code": "Legal &middot; Código Florestal",
  "Property": "Imóvel", "APP type": "Tipo de APP",
  "up to 1 MF": "até 1 MF", "1 to 2 MF": "1 a 2 MF", "2 to 4 MF": "2 a 4 MF", "over 4 MF": "acima de 4 MF",
  "rivers and streams": "rios e igarapés", "springs": "nascentes", "lakes and ponds": "lagos e lagoas",
  "Strip to recompose (Art. 61-A)": "Faixa a recompor (Art. 61-A)",
  "{w} m on each margin": "{w} m em cada margem",
  "Art. 61-B: total recomposition capped at {p}% of the property": "Art. 61-B: recomposição total limitada a {p}% da área do imóvel",
  "above 4 MF the 61-B cap does not apply; for rivers, 20 m covers watercourses up to 10 m wide":
    "acima de 4 MF não há teto do Art. 61-B; para rios, os 20 m valem para cursos d'água de até 10 m de largura",
  "SMA 32 targets (SP)": "Metas SMA 32 (SP)",
  "ombrophilous and seasonal forests": "florestas ombrófilas e estacionais",
  "cerradao / cerrado stricto sensu": "cerradão / cerrado stricto sensu",
  "{n} years": "{n} anos",
  "sign-off gate (Anexo II)": "atesto (Anexo II)",
  "Plots for this area: {n} of 100 m2 (25 x 4 m). A regenerant counts from 50 cm height with CAP under 15 cm.":
    "Parcelas para esta área: {n} de 100 m² (25 × 4 m). Regenerante conta a partir de 50 cm de altura com CAP menor que 15 cm.",
  "Anexo III suggests at least 80 regional native species for full-area planting. It is guidance, not a requirement.":
    "O Anexo III sugere ao menos 80 espécies nativas regionais no plantio em área total. É orientação, não exigência.",
  "Restoration cost": "Custo de restauração",
  "range across labour arrangements, own workforce to contracted; 2023 prices, 3x2 m spacing":
    "faixa da mão de obra própria à empreitada; preços de 2023, espaçamento 3x2 m",
  "Natural regeneration management": "Condução da regeneração natural",
  "Regeneration + enrichment": "Condução + enriquecimento",
  "Regeneration + densification + enrichment": "Condução + adensamento + enriquecimento",
  "Seedling planting, mechanized": "Plantio de mudas, mecanizado",
  "Seedling planting, manual": "Plantio de mudas, não mecanizado",
  "Direct seeding, mechanized": "Semeadura direta, mecanizada",
  "Direct seeding, manual": "Semeadura direta, não mecanizada",
  "Seedling planting in this area": "Plantio de mudas nesta área",
  "Costs: Instituto Escolhas 2023": "Custos: Instituto Escolhas 2023",
  "Score in the 2040s": "Nota nos anos 2040",
  "Rescored on a 2040-2049 CMIP6 projection (MRI-AGCM3-2-S), same scoring engine":
    "Reavaliada com a projeção CMIP6 2040-2049 (MRI-AGCM3-2-S), mesmo mecanismo de nota",
  "Falls below suitable in the 2040s climate (CMIP6)": "Cai abaixo de adequada no clima dos anos 2040 (CMIP6)",
  "Export report": "Exportar relatório",
  "central sample of {n} trees": "amostra central de {n} árvores",
  "showing {n} of {t} trees": "mostrando {n} de {t} árvores",
  "trees": "árvores",
  "click plants a sapling · right-click removes it · Cmd+Z undoes": "clique planta uma muda · botão direito remove · Cmd+Z desfaz",
};
const ES = {
  "Draw an area anywhere on Earth: Replantio shows which species would thrive there, how they grow, the carbon they store, and what restoration costs. Open data, open model.": "Dibuja un área en cualquier lugar del mundo: Replantio muestra qué especies prosperarían allí, cómo crecen, el carbono que guardan y cuánto cuesta restaurar. Datos abiertos, modelo abierto.",
  "created by": "creado por",
  "Open source on GitHub": "Código abierto en GitHub",
  "Go to my location": "Ir a mi ubicación",
  "Could not get your location.": "No se pudo obtener tu ubicación.",
  "Analyzing area": "Analizando el área", "Analysis failed": "Falló el análisis", "Retry": "Reintentar",
  "Climate normals &middot; Open-Meteo ERA5, 10 years daily": "Normales climáticas &middot; Open-Meteo ERA5, 10 años diarios",
  "Soil profile &middot; SoilGrids 2.0": "Perfil del suelo &middot; SoilGrids 2.0",
  "Scoring {n} species": "Evaluando {n} especies",
  "Could not load the climate record for this point. The Open-Meteo archive may be busy or rate limited; wait a moment and retry.": "No se pudo cargar el registro climático de este punto. El archivo de Open-Meteo puede estar ocupado; espere un momento y reintente.",
  "{s} of {n} species rate suitable or better": "{s} de {n} especies califican adecuadas o mejores",
  "Site climate &middot; ERA5 2015&ndash;2024": "Clima del sitio &middot; ERA5 2015&ndash;2024",
  "Recommended species": "Especies recomendadas",
  "soil pH": "pH del suelo", "elevation": "elevación", "daylength": "duración del día", "record low": "mínima récord",
  "sun": "sol", "humidity": "humedad", "cloud": "nubes", "slope": "pendiente", "facing": "orientación",
  "kWh/m²·day": "kWh/m²·día",
  "mean daily shortwave radiation, all weather included": "radiación solar media diaria, nubosidad incluida",
  "high humidity plus high cloud cover marks fog-prone sites": "humedad y nubosidad altas señalan sitios con niebla",
  "no data": "sin datos", "n/a": "n/d", "E": "E", "W": "O", "SW": "SO", "NW": "NO",
  "This area looks like open water (no soil data, elevation {e} m). Species scores here reflect climate only and are unlikely to be meaningful.": "Esta área parece agua abierta (sin datos de suelo, elevación {e} m). Las notas reflejan solo el clima y probablemente no signifiquen nada.",
  "Show scores anyway": "Mostrar de todos modos",
  "Nothing clears the bar for this filter here.": "Nada supera el corte con este filtro aquí.",
  "Show {n} more": "Mostrar {n} más",
  "Native here": "Nativas de aquí",
  "Only species in this country's native flora (WCVP)": "Solo especies de la flora nativa de este país (WCVP)",
  "All uses": "Todos los usos",
  "timber": "madera", "fruit": "fruta", "environment": "ambiental", "medicinal": "medicinal",
  "forage": "forraje", "materials": "materiales", "food": "alimento", "ornamental": "ornamental",
  "native": "nativa", "nearby": "en la zona",
  "Part of the native flora of this country (WCVP)": "Parte de la flora nativa de este país (WCVP)",
  "GBIF occurrence records near this area": "Registros de ocurrencia (GBIF) cerca de esta área",
  "Excellent": "Excelente", "Very suitable": "Muy adecuada", "Suitable": "Adecuada",
  "Marginal": "Marginal", "Very marginal": "Muy marginal", "Not suitable": "Inadecuada",
  "{rate} growth &middot; {zone}": "crecimiento {rate} &middot; {zone}",
  "fast": "rápido", "medium": "medio", "slow": "lento", "tropical": "tropical", "temperate": "templado",
  "Temperature": "Temperatura", "Rainfall": "Lluvia", "Soil pH": "pH del suelo",
  "tolerated {a} to {d} · optimal {b} to {c}": "tolera {a} a {d} · óptimo {b} a {c}",
  "Photoperiod outside this species' range: 0.5 penalty applied.": "Fotoperiodo fuera del rango de la especie: penalización de 0,5 aplicada.",
  "Needs winter dormancy; the coldest month here is too warm for it.": "Necesita dormancia invernal; el mes más frío aquí es demasiado cálido.",
  "Origin": "Origen", "Use": "Uso", "Time to max height": "Tiempo hasta altura máx.", "Mature canopy": "Copa adulta",
  "all origins": "todas", "any": "cualquiera", "under {n} years": "hasta {n} años",
  "native here": "nativas de aquí", "all uses": "todos", "Maturity": "Madurez",
  "no limit": "sin límite", "no minimum": "sin mínimo",
  "criteria": "criterios", "clear criteria": "limpiar criterios",
  "{n} of {t}": "{n} de {t}", "{n} species": "{n} especies",
  "Reaches ~95% of its max height in ~{n} years (class-level model).": "Alcanza ~95% de su altura máxima en ~{n} años (modelo por clase).",
  "Trunk &oslash; 20 yr": "Tronco &oslash; 20 años", "Canopy, 20 yr": "Copa, 20 años",
  "CO&#8322;e/tree, 20 yr": "CO&#8322;e/árbol, 20 años", "Stand CO&#8322;e, 20 yr": "CO&#8322;e del rodal, 20 años",
  "Best window": "Mejor ventana", "Hardy to": "Resiste hasta",
  "Trees in this area, 3&times;3 m": "Árboles en el área, 3&times;3 m", "Area CO&#8322;e by year 20": "CO&#8322;e del área al año 20",
  "mean": "media", "per year": "por año", "y": "a", "yr": "años", "trunk": "tronco",
  "Suitability follows the FAO EcoCrop model (trapezoidal climate envelopes, most-limiting-factor). Growth and carbon are class-level estimates": "La aptitud sigue el modelo EcoCrop de la FAO (envolventes climáticas trapezoidales, factor más limitante). Crecimiento y carbono son estimaciones por clase",
  "(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006), for screening, not planting prescriptions.": "(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006): tamizaje, no prescripción de plantación.",
  "Data:": "Datos:", "Photos: iNaturalist": "Fotos: iNaturalist", "Map:": "Mapa:",
  "Search a city or place": "Busca una ciudad o lugar",
  "Draw area": "Dibujar área",
  "Click to drop points &middot; right-click, double-click or click the first point to close &middot; Esc cancels": "Haz clic para marcar puntos &middot; clic derecho, doble clic o clic en el primer punto para cerrar &middot; Esc cancela",
  "No matches": "Sin resultados",
  "Replantio · replanting intelligence": "Replantio · inteligencia de replantación",
  "Habit": "Porte", "all habits": "todos los portes",
  "shrubs": "arbustos", "herbs": "hierbas", "grasses": "pastos", "vines": "trepadoras",
  "Cycle": "Ciclo", "{a} to {b} days": "{a} a {b} días",
  "Find plantable land in this view": "Buscar terrenos plantables en esta vista",
  "Zoom in to city scale to scan for plantable land.": "Acerca el zoom a escala de ciudad para escanear terrenos.",
  "Nothing promising in this view. Try another neighborhood.": "Nada prometedor en esta vista. Prueba otro barrio.",
  "The land scan service is busy; try again in a minute.": "El servicio de escaneo está ocupado; intenta en un minuto.",
  "click to analyze": "clic para analizar", "candidate areas": "áreas candidatas",
  "year": "año", "height": "altura", "crown": "copa",
  "central sample of {n} trees": "muestra central de {n} árboles",
  "showing {n} of {t} trees": "mostrando {n} de {t} árboles",
  "trees": "árboles",
  "click plants a sapling · right-click removes it · Cmd+Z undoes": "clic planta un plantín · clic derecho lo quita · Cmd+Z deshace",
  "Close": "Cerrar", "Selected area": "Área seleccionada", "fit": "ajuste",
  "Delete area": "Eliminar área",
  "Import area (GeoJSON, KML, zipped shapefile)": "Importar área (GeoJSON, KML, shapefile comprimido)",
  "No polygons found in the file.": "No se encontraron polígonos en el archivo.",
  "Could not read the file.": "No se pudo leer el archivo.",
  "The shapefile must use WGS84 geographic coordinates (like SARE requires).": "El shapefile debe usar coordenadas geográficas WGS84.",
  "Report": "Informe", "SHP (SARE)": "SHP", "CSV": "CSV",
  "area": "área", "areas": "áreas", "planted": "plantados",
  "Restoration cost": "Costo de restauración",
  "range across labour arrangements, own workforce to contracted; 2023 prices, 3x2 m spacing": "rango entre mano de obra propia y contratada; precios 2023 (Brasil), espaciamiento 3x2 m",
  "Natural regeneration management": "Manejo de regeneración natural",
  "Regeneration + enrichment": "Regeneración + enriquecimiento",
  "Regeneration + densification + enrichment": "Regeneración + densificación + enriquecimiento",
  "Seedling planting, mechanized": "Plantación de plantines, mecanizada",
  "Seedling planting, manual": "Plantación de plantines, manual",
  "Direct seeding, mechanized": "Siembra directa, mecanizada",
  "Direct seeding, manual": "Siembra directa, manual",
  "Seedling planting in this area": "Plantación de plantines en esta área",
  "Costs: Instituto Escolhas 2023": "Costos: Instituto Escolhas 2023",
  "Score in the 2040s": "Nota en los 2040",
  "Rescored on a 2040-2049 CMIP6 projection (MRI-AGCM3-2-S), same scoring engine": "Reevaluada con proyección CMIP6 2040-2049 (MRI-AGCM3-2-S), mismo motor de nota",
  "Falls below suitable in the 2040s climate (CMIP6)": "Cae por debajo de adecuada en el clima de los 2040 (CMIP6)",
  "Export report": "Exportar informe",
  "Legal &middot; Forest Code": "Legal &middot; Código Forestal (Brasil)",
  "Property": "Predio", "APP type": "Tipo de APP",
  "up to 1 MF": "hasta 1 MF", "1 to 2 MF": "1 a 2 MF", "2 to 4 MF": "2 a 4 MF", "over 4 MF": "más de 4 MF",
  "rivers and streams": "ríos y arroyos", "springs": "manantiales", "lakes and ponds": "lagos y lagunas",
  "Strip to recompose (Art. 61-A)": "Franja a recomponer (Art. 61-A)",
  "{w} m on each margin": "{w} m en cada margen",
  "Art. 61-B: total recomposition capped at {p}% of the property": "Art. 61-B: recomposición total limitada al {p}% del predio",
  "above 4 MF the 61-B cap does not apply; for rivers, 20 m covers watercourses up to 10 m wide": "sobre 4 MF no aplica el tope del 61-B; en ríos, los 20 m valen para cauces de hasta 10 m de ancho",
  "SMA 32 targets (SP)": "Metas SMA 32 (São Paulo)",
  "ombrophilous and seasonal forests": "bosques ombrófilos y estacionales",
  "cerradao / cerrado stricto sensu": "cerradão / cerrado stricto sensu",
  "{n} years": "{n} años",
  "sign-off gate (Anexo II)": "cierre (Anexo II)",
  "Plots for this area: {n} of 100 m2 (25 x 4 m). A regenerant counts from 50 cm height with CAP under 15 cm.": "Parcelas para esta área: {n} de 100 m² (25 × 4 m). Un regenerante cuenta desde 50 cm de altura con CAP menor a 15 cm.",
  "Anexo III suggests at least 80 regional native species for full-area planting. It is guidance, not a requirement.": "El Anexo III sugiere al menos 80 especies nativas regionales para plantación en área total. Es orientación, no exigencia.",
};
const FR = {
  "Draw an area anywhere on Earth: Replantio shows which species would thrive there, how they grow, the carbon they store, and what restoration costs. Open data, open model.": "Dessinez une zone n'importe où sur Terre : Replantio montre quelles espèces y prospéreraient, leur croissance, le carbone stocké et le coût de la restauration. Données ouvertes, modèle ouvert.",
  "created by": "créé par",
  "Open source on GitHub": "Open source sur GitHub",
  "Go to my location": "Aller à ma position",
  "Could not get your location.": "Impossible d'obtenir votre position.",
  "Analyzing area": "Analyse de la zone", "Analysis failed": "Échec de l'analyse", "Retry": "Réessayer",
  "Climate normals &middot; Open-Meteo ERA5, 10 years daily": "Normales climatiques &middot; Open-Meteo ERA5, 10 ans journaliers",
  "Soil profile &middot; SoilGrids 2.0": "Profil du sol &middot; SoilGrids 2.0",
  "Scoring {n} species": "Évaluation de {n} espèces",
  "Could not load the climate record for this point. The Open-Meteo archive may be busy or rate limited; wait a moment and retry.": "Impossible de charger l'historique climatique de ce point. L'archive Open-Meteo est peut-être saturée; patientez puis réessayez.",
  "{s} of {n} species rate suitable or better": "{s} des {n} espèces sont adaptées ou mieux",
  "Site climate &middot; ERA5 2015&ndash;2024": "Climat du site &middot; ERA5 2015&ndash;2024",
  "Recommended species": "Espèces recommandées",
  "soil pH": "pH du sol", "elevation": "altitude", "daylength": "durée du jour", "record low": "minimum record",
  "sun": "soleil", "humidity": "humidité", "cloud": "nuages", "slope": "pente", "facing": "exposition",
  "kWh/m²·day": "kWh/m²·jour",
  "mean daily shortwave radiation, all weather included": "rayonnement solaire moyen journalier, nébulosité comprise",
  "high humidity plus high cloud cover marks fog-prone sites": "humidité et nébulosité élevées signalent les sites brumeux",
  "no data": "pas de données", "n/a": "n/d", "E": "E", "W": "O", "SW": "SO", "NW": "NO",
  "This area looks like open water (no soil data, elevation {e} m). Species scores here reflect climate only and are unlikely to be meaningful.": "Cette zone semble être de l'eau libre (pas de sol, altitude {e} m). Les notes ne reflètent que le climat et n'ont probablement aucun sens.",
  "Show scores anyway": "Afficher quand même",
  "Nothing clears the bar for this filter here.": "Rien ne passe la barre avec ce filtre ici.",
  "Show {n} more": "Afficher {n} de plus",
  "Native here": "Indigènes d'ici",
  "Only species in this country's native flora (WCVP)": "Seulement la flore indigène de ce pays (WCVP)",
  "All uses": "Tous usages",
  "timber": "bois", "fruit": "fruit", "environment": "environnement", "medicinal": "médicinal",
  "forage": "fourrage", "materials": "matériaux", "food": "aliment", "ornamental": "ornemental",
  "native": "indigène", "nearby": "à proximité",
  "Part of the native flora of this country (WCVP)": "Fait partie de la flore indigène de ce pays (WCVP)",
  "GBIF occurrence records near this area": "Occurrences GBIF près de cette zone",
  "Excellent": "Excellente", "Very suitable": "Très adaptée", "Suitable": "Adaptée",
  "Marginal": "Marginale", "Very marginal": "Très marginale", "Not suitable": "Inadaptée",
  "{rate} growth &middot; {zone}": "croissance {rate} &middot; {zone}",
  "fast": "rapide", "medium": "moyenne", "slow": "lente", "tropical": "tropicale", "temperate": "tempérée",
  "Temperature": "Température", "Rainfall": "Pluie", "Soil pH": "pH du sol",
  "tolerated {a} to {d} · optimal {b} to {c}": "toléré {a} à {d} · optimal {b} à {c}",
  "Photoperiod outside this species' range: 0.5 penalty applied.": "Photopériode hors de la plage de l'espèce : pénalité de 0,5 appliquée.",
  "Needs winter dormancy; the coldest month here is too warm for it.": "Exige une dormance hivernale; le mois le plus froid ici est trop chaud.",
  "Origin": "Origine", "Use": "Usage", "Time to max height": "Temps jusqu'à la hauteur max.", "Mature canopy": "Houppier adulte",
  "all origins": "toutes", "any": "indifférent", "under {n} years": "moins de {n} ans",
  "native here": "indigènes d'ici", "all uses": "tous", "Maturity": "Maturité",
  "no limit": "sans limite", "no minimum": "sans minimum",
  "criteria": "critères", "clear criteria": "effacer les critères",
  "{n} of {t}": "{n} sur {t}", "{n} species": "{n} espèces",
  "Reaches ~95% of its max height in ~{n} years (class-level model).": "Atteint ~95 % de sa hauteur max en ~{n} ans (modèle par classe).",
  "Trunk &oslash; 20 yr": "Tronc &oslash; 20 ans", "Canopy, 20 yr": "Houppier, 20 ans",
  "CO&#8322;e/tree, 20 yr": "CO&#8322;e/arbre, 20 ans", "Stand CO&#8322;e, 20 yr": "CO&#8322;e du peuplement, 20 ans",
  "Best window": "Meilleure fenêtre", "Hardy to": "Rustique jusqu'à",
  "Trees in this area, 3&times;3 m": "Arbres dans la zone, 3&times;3 m", "Area CO&#8322;e by year 20": "CO&#8322;e de la zone à 20 ans",
  "mean": "moyenne", "per year": "par an", "y": "a", "yr": "ans", "trunk": "tronc",
  "Suitability follows the FAO EcoCrop model (trapezoidal climate envelopes, most-limiting-factor). Growth and carbon are class-level estimates": "L'aptitude suit le modèle EcoCrop de la FAO (enveloppes climatiques trapézoïdales, facteur le plus limitant). Croissance et carbone sont des estimations par classe",
  "(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006), for screening, not planting prescriptions.": "(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006) : un tamisage, pas une prescription de plantation.",
  "Data:": "Données :", "Photos: iNaturalist": "Photos : iNaturalist", "Map:": "Carte :",
  "Search a city or place": "Cherchez une ville ou un lieu",
  "Draw area": "Dessiner la zone",
  "Click to drop points &middot; right-click, double-click or click the first point to close &middot; Esc cancels": "Cliquez pour poser des points &middot; clic droit, double-clic ou clic sur le premier point pour fermer &middot; Échap annule",
  "No matches": "Aucun résultat",
  "Replantio · replanting intelligence": "Replantio · intelligence de la replantation",
  "Habit": "Port", "all habits": "tous les ports",
  "shrubs": "arbustes", "herbs": "herbacées", "grasses": "graminées", "vines": "lianes",
  "Cycle": "Cycle", "{a} to {b} days": "{a} à {b} jours",
  "Find plantable land in this view": "Trouver des terrains plantables dans cette vue",
  "Zoom in to city scale to scan for plantable land.": "Zoomez à l'échelle de la ville pour scanner les terrains.",
  "Nothing promising in this view. Try another neighborhood.": "Rien de prometteur dans cette vue. Essayez un autre quartier.",
  "The land scan service is busy; try again in a minute.": "Le service de balayage est saturé; réessayez dans une minute.",
  "click to analyze": "cliquez pour analyser", "candidate areas": "zones candidates",
  "year": "année", "height": "hauteur", "crown": "houppier",
  "central sample of {n} trees": "échantillon central de {n} arbres",
  "showing {n} of {t} trees": "affichage de {n} sur {t} arbres",
  "trees": "arbres",
  "click plants a sapling · right-click removes it · Cmd+Z undoes": "clic plante un jeune arbre · clic droit le retire · Cmd+Z annule",
  "Close": "Fermer", "Selected area": "Zone sélectionnée", "fit": "ajust.",
  "Delete area": "Supprimer la zone",
  "Import area (GeoJSON, KML, zipped shapefile)": "Importer une zone (GeoJSON, KML, shapefile zippé)",
  "No polygons found in the file.": "Aucun polygone trouvé dans le fichier.",
  "Could not read the file.": "Impossible de lire le fichier.",
  "The shapefile must use WGS84 geographic coordinates (like SARE requires).": "Le shapefile doit être en coordonnées géographiques WGS84.",
  "Report": "Rapport", "SHP (SARE)": "SHP", "CSV": "CSV",
  "area": "zone", "areas": "zones", "planted": "plantés",
  "Restoration cost": "Coût de restauration",
  "range across labour arrangements, own workforce to contracted; 2023 prices, 3x2 m spacing": "fourchette selon la main-d'œuvre, propre à sous-traitée; prix 2023 (Brésil), espacement 3x2 m",
  "Natural regeneration management": "Conduite de la régénération naturelle",
  "Regeneration + enrichment": "Régénération + enrichissement",
  "Regeneration + densification + enrichment": "Régénération + densification + enrichissement",
  "Seedling planting, mechanized": "Plantation de plants, mécanisée",
  "Seedling planting, manual": "Plantation de plants, manuelle",
  "Direct seeding, mechanized": "Semis direct, mécanisé",
  "Direct seeding, manual": "Semis direct, manuel",
  "Seedling planting in this area": "Plantation de plants dans cette zone",
  "Costs: Instituto Escolhas 2023": "Coûts : Instituto Escolhas 2023",
  "Score in the 2040s": "Note dans les années 2040",
  "Rescored on a 2040-2049 CMIP6 projection (MRI-AGCM3-2-S), same scoring engine": "Réévaluée sur une projection CMIP6 2040-2049 (MRI-AGCM3-2-S), même moteur de notation",
  "Falls below suitable in the 2040s climate (CMIP6)": "Descend sous le seuil d'adaptée dans le climat des années 2040 (CMIP6)",
  "Export report": "Exporter le rapport",
  "Legal &middot; Forest Code": "Légal &middot; Code forestier (Brésil)",
  "Property": "Propriété", "APP type": "Type d'APP",
  "up to 1 MF": "jusqu'à 1 MF", "1 to 2 MF": "1 à 2 MF", "2 to 4 MF": "2 à 4 MF", "over 4 MF": "plus de 4 MF",
  "rivers and streams": "rivières et ruisseaux", "springs": "sources", "lakes and ponds": "lacs et étangs",
  "Strip to recompose (Art. 61-A)": "Bande à recomposer (Art. 61-A)",
  "{w} m on each margin": "{w} m sur chaque rive",
  "Art. 61-B: total recomposition capped at {p}% of the property": "Art. 61-B : recomposition totale plafonnée à {p} % de la propriété",
  "above 4 MF the 61-B cap does not apply; for rivers, 20 m covers watercourses up to 10 m wide": "au-delà de 4 MF le plafond 61-B ne s'applique pas; pour les rivières, 20 m couvre les cours d'eau jusqu'à 10 m de large",
  "SMA 32 targets (SP)": "Objectifs SMA 32 (São Paulo)",
  "ombrophilous and seasonal forests": "forêts ombrophiles et saisonnières",
  "cerradao / cerrado stricto sensu": "cerradão / cerrado stricto sensu",
  "{n} years": "{n} ans",
  "sign-off gate (Anexo II)": "validation (Anexo II)",
  "Plots for this area: {n} of 100 m2 (25 x 4 m). A regenerant counts from 50 cm height with CAP under 15 cm.": "Placettes pour cette zone : {n} de 100 m² (25 × 4 m). Un régénérant compte dès 50 cm de hauteur avec CAP sous 15 cm.",
  "Anexo III suggests at least 80 regional native species for full-area planting. It is guidance, not a requirement.": "L'Anexo III suggère au moins 80 espèces indigènes régionales pour la plantation en zone totale. C'est indicatif, pas obligatoire.",
};
const DICT = { pt: PT, es: ES, fr: FR }[LANG];
const tr = s => DICT?.[s] ?? s;
const tfmt = (s, vars) => Object.entries(vars).reduce((a, [k, v]) => a.replace(`{${k}}`, v), tr(s));

const fmt = (x, d = 0) => x.toLocaleString(LOCALE, { maximumFractionDigits: d });
const fmtC = x => x >= 1e6 ? (x / 1e6).toFixed(1) + "M" : x >= 1e4 ? Math.round(x / 1e3) + "k" : fmt(x);
const fmtHa = h => h >= 10 ? fmt(h) + " ha" : h >= 0.1 ? fmt(h, 1) + " ha" : fmt(h * 10000) + " m\u00b2";
const THIS_YEAR = new Date().getFullYear();
const MONTHS = {
  pt: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  es: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
  fr: ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"],
}[LANG];

// ---------- map ----------
const map = L.map("map", { zoomControl: true, worldCopyJump: true, attributionControl: false }).setView([-15, -52], 4);
map.zoomControl.setPosition("bottomleft");
L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
  maxZoom: 20, maxNativeZoom: 19,
  attribution: "Imagery &copy; Esri, Vantor, Earthstar Geographics",
}).addTo(map);
L.tileLayer("https://basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png", {
  maxZoom: 20, attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
}).addTo(map);

let SPECIES = [], NATIVES = {};
const speciesReady = Promise.all([
  fetch("data/species.json").then(r => r.json()).then(j => { SPECIES = j; }),
  fetch("data/natives.json").then(r => r.json()).then(j => { NATIVES = j; }).catch(() => {}), // optional layer
]);

// ---------- geocoding search ----------
const geoInput = $("#geo-input"), geoResults = $("#geo-results");
let geoTimer, geoHits = [];
geoInput.addEventListener("input", () => {
  clearTimeout(geoTimer);
  const q = geoInput.value.trim();
  if (q.length < 3) { geoResults.hidden = true; return; }
  geoTimer = setTimeout(() => searchPlaces(q), 250);
});
geoInput.addEventListener("keydown", e => { if (e.key === "Enter" && geoHits.length) pickPlace(geoHits[0]); });
document.addEventListener("click", e => { if (!e.target.closest(".search")) geoResults.hidden = true; });

async function searchPlaces(q) {
  // Photon (OSM): typo-tolerant, understands street addresses; Open-Meteo as fallback
  try {
    const r = await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=6`);
    geoHits = ((await r.json()).features ?? []).map(f => {
      const p = f.properties;
      const name = [p.housenumber && p.street ? `${p.street} ${p.housenumber}` : p.name || p.street, p.locality].filter(Boolean)[0] ?? p.name;
      return {
        name,
        sub: [p.city, p.state, p.country].filter(Boolean).join(", "),
        lat: f.geometry.coordinates[1], lng: f.geometry.coordinates[0],
        zoom: p.type === "house" || p.type === "street" ? 17 : p.type === "district" || p.type === "locality" ? 14 : 12,
      };
    }).filter(h => h.name);
  } catch {
    try {
      const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=6&language=${LANG}&format=json`);
      geoHits = ((await r.json()).results ?? []).map(h => ({
        name: h.name, sub: [h.admin1, h.country].filter(Boolean).join(", "),
        lat: h.latitude, lng: h.longitude, zoom: 12,
      }));
    } catch { geoHits = []; }
  }
  geoResults.innerHTML = geoHits.map((h, i) =>
    `<li data-i="${i}">${h.name}<div class="sub">${h.sub}</div></li>`).join("")
    || `<li><div class="sub">${tr("No matches")}</div></li>`;
  geoResults.hidden = false;
}
geoResults.addEventListener("click", e => {
  const li = e.target.closest("li[data-i]");
  if (li) pickPlace(geoHits[+li.dataset.i]);
});
function pickPlace(h) {
  geoResults.hidden = true;
  geoInput.value = h.name;
  map.flyTo([h.lat, h.lng], h.zoom, { duration: 1.6 });
}

// ---------- draw an area (click to drop vertices) ----------
const drawBtn = $("#draw-btn"), hint = $("#hint");
const SHAPE_STYLE = { color: "#55d97c", weight: 1.5, fillOpacity: 0.08, dashArray: "5 4" };
const INACTIVE_STYLE = { color: "#93a096", weight: 1, fillOpacity: 0.03, dashArray: "3 5" };
let armed = false, verts = [], draft = null, shape = null; // shape = the active area
const shapes = []; // every analyzed area stays on the map
drawBtn.addEventListener("click", () => armed ? cancelDraw() : arm());
function arm() {
  armed = true; verts = [];
  drawBtn.classList.add("armed");
  hint.hidden = false;
  map.doubleClickZoom.disable();
  map.getContainer().style.cursor = "crosshair";
  removeEditHandles();
}
function disarm() {
  armed = false; verts = [];
  drawBtn.classList.remove("armed");
  hint.hidden = true;
  map.doubleClickZoom.enable();
  map.getContainer().style.cursor = "";
  draft?.remove(); draft = null;
  addEditHandles(shape);
}
function cancelDraw() { disarm(); }
document.addEventListener("keydown", e => { if (e.key === "Escape" && armed) cancelDraw(); });
function deleteActiveArea() {
  if (!shape) return;
  removeStand(shape);
  removeEditHandles();
  map.removeLayer(shape);
  shapes.splice(shapes.indexOf(shape), 1);
  shape = null;
  panel.hidden = true;
  history.replaceState(null, "", location.pathname);
  saveAreas();
}
// Delete/Backspace removes the active area, its stand and its saplings
document.addEventListener("keydown", e => {
  if (e.key !== "Delete" && e.key !== "Backspace") return;
  if (!shape || armed) return;
  if (/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName ?? "")) return;
  deleteActiveArea();
});

function redrawDraft(cursor) {
  draft?.remove();
  const pts = cursor ? [...verts, cursor] : verts;
  draft = L.layerGroup([
    pts.length >= 2 ? L.polygon(pts, { ...SHAPE_STYLE, weight: 1.2 }) : null,
    ...verts.map((v, i) => L.circleMarker(v, {
      radius: i === 0 ? 6 : 4, color: "#55d97c", weight: 1.5,
      fillColor: i === 0 ? "#55d97c" : "#0a0d0b", fillOpacity: 1,
    })),
  ].filter(Boolean)).addTo(map);
}

function nearFirst(latlng) {
  if (!verts.length) return false;
  return map.latLngToContainerPoint(latlng).distanceTo(map.latLngToContainerPoint(verts[0])) < 12;
}

map.on("click", e => {
  if (!armed) return;
  if (verts.length >= 3 && nearFirst(e.latlng)) return finishDraw();
  verts.push(e.latlng);
  redrawDraft();
});
map.on("mousemove", e => { if (armed && verts.length) redrawDraft(e.latlng); });
// close the polygon: double-click or right-click (doubleClickZoom is disabled
// while armed; Leaflet suppresses the browser context menu for us)
map.on("dblclick", e => {
  if (!armed) return;
  e.originalEvent?.preventDefault();
  finishDraw();
});
map.on("contextmenu", e => {
  if (!armed) return;
  finishDraw();
});

function finishDraw() {
  // dedupe consecutive near-identical points (dblclick fires two clicks)
  const pts = verts.filter((v, i) => !i || Math.abs(v.lat - verts[i - 1].lat) + Math.abs(v.lng - verts[i - 1].lng) > 1e-6);
  disarm();
  if (!pts.length) return;
  let poly;
  if (pts.length === 1) {          // single click: ~1 km plot around it
    const [la, ln] = [pts[0].lat, pts[0].lng];
    const dx = 0.0045 / Math.max(0.1, Math.cos(la * Math.PI / 180)); // keep ~1 km wide at any latitude
    poly = [[la - 0.0045, ln - dx], [la - 0.0045, ln + dx], [la + 0.0045, ln + dx], [la + 0.0045, ln - dx]].map(p => L.latLng(...p));
  } else if (pts.length === 2) {   // two clicks: rectangle between corners
    const b = L.latLngBounds(pts);
    poly = [b.getSouthWest(), b.getSouthEast(), b.getNorthEast(), b.getNorthWest()];
  } else {
    poly = pts;
  }
  setShape(poly);
  analyze(poly);
}

function setShape(pts) {
  const poly = L.polygon(pts, SHAPE_STYLE).addTo(map);
  poly._pts = pts;
  poly.on("click", () => {
    if (armed || poly === shape) return; // active shape stays clickable for sapling planting
    setActive(poly);
    analyze(poly._pts);
  });
  shapes.push(poly);
  setActive(poly);
  saveAreas();
}

// areas survive reloads; the roll-up pill totals the project
function saveAreas() {
  try {
    localStorage.setItem("areas", JSON.stringify(
      shapes.map(s => s._pts.map(p => [+p.lat.toFixed(5), +p.lng.toFixed(5)]))));
  } catch { /* storage full or blocked: areas just will not persist */ }
  updateProj();
}
function updateProj() {
  const el = $("#proj");
  if (!el) return;
  if (!shapes.length) { el.hidden = true; return; }
  const totalHa = shapes.reduce((a, s) => a + polyAreaHa(s._pts), 0);
  let planted = 0;
  for (const [poly, st] of STANDS) planted += co2eTonsPerHa(st.item.sp, st.year) * polyAreaHa(poly._pts);
  if (SIM?.poly?._pts) planted += co2eTonsPerHa(SIM.item.sp, SIM.year) * polyAreaHa(SIM.poly._pts);
  el.innerHTML = `<b>${shapes.length}</b> ${shapes.length === 1 ? tr("area") : tr("areas")} &middot; <b>${fmtHa(totalHa)}</b>` +
    (planted > 0 ? ` &middot; <b>${fmtC(planted)} t</b> CO&#8322;e ${tr("planted")}` : "");
  el.hidden = false;
}
function restoreAreas() {
  try {
    const saved = JSON.parse(localStorage.getItem("areas") ?? "[]");
    for (const pts of saved) {
      if (Array.isArray(pts) && pts.length >= 3) setShape(pts.map(([la, ln]) => L.latLng(la, ln)));
    }
    if (shapes.length && !location.hash) map.fitBounds(L.latLngBounds(shapes.flatMap(s => s._pts)).pad(0.3));
  } catch { }
}
function setActive(poly) {
  shape = poly;
  for (const s of shapes) s.setStyle(s === poly ? SHAPE_STYLE : INACTIVE_STYLE);
  addEditHandles(poly);
}

// draggable vertex handles on the active area
let editHandles = [];
function addEditHandles(poly) {
  removeEditHandles();
  if (!poly) return;
  poly._pts.forEach((pt, i) => {
    const mk = L.marker(pt, {
      draggable: true,
      icon: L.divIcon({ className: "vhandle", iconSize: [12, 12] }),
    }).addTo(map);
    mk.on("drag", () => {
      poly._pts[i] = mk.getLatLng();
      poly.setLatLngs(poly._pts);
    });
    mk.on("dragend", () => {
      // discard BOTH the frozen stand and any live sim on this area, otherwise
      // the re-analysis freezes the old-geometry trees right back
      removeStand(poly);
      saveAreas();
      analyze(poly._pts);
    });
    editHandles.push(mk);
  });
}
function removeEditHandles() {
  editHandles.forEach(h => h.remove());
  editHandles = [];
}

// planar shoelace at the area's scale: fine for study areas up to ~100 km
function polyXY(pts) {
  const rad = Math.PI / 180, R = 6371000;
  const lat0 = pts.reduce((a, p) => a + p.lat, 0) / pts.length * rad;
  const lng0 = pts[0].lng;
  return pts.map(p => {
    const lng = p.lng - 360 * Math.round((p.lng - lng0) / 360); // antimeridian unwrap
    return [R * lng * rad * Math.cos(lat0), R * p.lat * rad];
  });
}
const normLng = l => ((l % 360) + 540) % 360 - 180;
function polyAreaHa(pts) {
  const xy = polyXY(pts);
  let s = 0;
  for (let i = 0; i < xy.length; i++) {
    const [x1, y1] = xy[i], [x2, y2] = xy[(i + 1) % xy.length];
    s += x1 * y2 - x2 * y1;
  }
  return Math.abs(s) / 2 / 10000;
}
function polyCentroid(pts) {
  const xy = polyXY(pts);
  let s = 0, cx = 0, cy = 0;
  for (let i = 0; i < xy.length; i++) {
    const [x1, y1] = xy[i], [x2, y2] = xy[(i + 1) % xy.length];
    const f = x1 * y2 - x2 * y1;
    s += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f;
  }
  if (Math.abs(s) < 1e-9) return L.latLng( // degenerate: vertex mean
    pts.reduce((a, p) => a + p.lat, 0) / pts.length,
    normLng(pts.reduce((a, p) => a + p.lng, 0) / pts.length));
  const rad = Math.PI / 180, R = 6371000;
  const lat0 = pts.reduce((a, p) => a + p.lat, 0) / pts.length * rad;
  return L.latLng((cy / (3 * s)) / R / rad, normLng((cx / (3 * s)) / R / Math.cos(lat0) / rad));
}

// ---------- data fetchers ----------
async function fetchClimate(c, signal) {
  const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${c.lat.toFixed(4)}&longitude=${c.lng.toFixed(4)}` +
    `&start_date=2015-01-01&end_date=2024-12-31&daily=temperature_2m_mean,temperature_2m_min,precipitation_sum,shortwave_radiation_sum,relative_humidity_2m_mean,cloud_cover_mean&timezone=auto`;
  const j = await (await fetch(url, { signal })).json();
  if (!j.daily?.time?.length) throw new Error(j.reason || "no climate data");
  return j;
}

async function fetchSoil(c, signal) {
  try {
    const url = `https://rest.isric.org/soilgrids/v2.0/properties/query?lon=${c.lng.toFixed(4)}&lat=${c.lat.toFixed(4)}` +
      `&property=phh2o&depth=0-5cm&depth=5-15cm&value=mean`;
    const j = await (await fetch(url, { signal })).json();
    const layer = j.properties?.layers?.find(l => l.name === "phh2o");
    const THICKNESS = { "0-5cm": 5, "5-15cm": 10 };
    let vsum = 0, wsum = 0;
    for (const d of layer?.depths ?? []) {
      const v = d.values.mean, w = THICKNESS[d.label] ?? 0;
      if (v != null && w) { vsum += v * w; wsum += w; }
    }
    return { phh2o: wsum ? (vsum / wsum) / layer.unit_measure.d_factor : null };
  } catch (e) {
    if (e.name === "AbortError") throw e;
    return null; // soil is optional: rate limit / outage degrades gracefully
  }
}

async function fetchPlace(c, signal) {
  try {
    const j = await (await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${c.lat}&longitude=${c.lng}&localityLanguage=${LANG}`, { signal })).json();
    return { label: [j.city || j.locality, j.principalSubdivision, j.countryName].filter(Boolean).join(", ") || null,
             cc: j.countryCode || null, state: j.principalSubdivision || "" };
  } catch { return null; }
}

async function fetchTerrain(c, signal) {
  try {
    const d = 0.0009, dx = d / Math.max(0.1, Math.cos(c.lat * Math.PI / 180));
    const lats = [], lngs = [];
    for (const i of [1, 0, -1]) for (const j of [-1, 0, 1]) { lats.push(c.lat + i * d); lngs.push(c.lng + j * dx); }
    const j = await (await fetch(`https://api.open-meteo.com/v1/elevation?latitude=${lats.map(x => x.toFixed(5)).join(",")}&longitude=${lngs.map(x => x.toFixed(5)).join(",")}`, { signal })).json();
    const e = j.elevation;
    if (!Array.isArray(e) || e.length !== 9 || e.some(v => v == null)) return null;
    const m = 111320 * 0.0009; // grid step in meters
    const gx = ((e[2] + e[5] + e[8]) - (e[0] + e[3] + e[6])) / 3 / (2 * m); // uphill east
    const gy = ((e[0] + e[1] + e[2]) - (e[6] + e[7] + e[8])) / 3 / (2 * m); // uphill north
    const slope = Math.atan(Math.hypot(gx, gy)) * 180 / Math.PI;
    const az = (Math.atan2(-gx, -gy) * 180 / Math.PI + 360) % 360; // downslope compass bearing
    const facing = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][Math.round(az / 45) % 8];
    return { slope, facing: slope < 1.5 ? null : facing };
  } catch { return null; }
}

// ---------- analysis ----------
const panel = $("#panel"), content = $("#panel-content");
let abortCtl = null, current = null; // current = {site, scored, pts, center, ha}

async function analyze(pts) {
  stopSim();
  abortCtl?.abort();
  const ctl = abortCtl = new AbortController();
  const c = polyCentroid(pts);
  const ha = polyAreaHa(pts);
  location.hash = `p=${pts.map(p => `${p.lat.toFixed(4)},${p.lng.toFixed(4)}`).join(";")}`;

  openPanel(`
    <div class="p-head">
      <div class="loc-title">${tr("Analyzing area")}</div>
      <div class="loc-geo">${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}<span class="sep">&middot;</span>${fmtHa(ha)}</div>
      <button class="panel-close" data-close title="${tr("Close")}">&times;</button>
    </div>
    <div class="p-body">
      <div class="loading">
        <div class="load-step active" id="ls-climate"><span class="dot"></span>${tr("Climate normals &middot; Open-Meteo ERA5, 10 years daily")}</div>
        <div class="load-step" id="ls-soil"><span class="dot"></span>${tr("Soil profile &middot; SoilGrids 2.0")}</div>
        <div class="load-step" id="ls-score"><span class="dot"></span>${tfmt("Scoring {n} species", { n: fmt(SPECIES.length || 1021) })}</div>
      </div>
      <div class="skel">
        <div class="skel-fig"></div>
        <div class="skel-row"></div><div class="skel-row"></div><div class="skel-row"></div>
      </div>
    </div>`);

  const climP = fetchClimate(c, ctl.signal);
  const soilP = fetchSoil(c, ctl.signal);
  const placeP = fetchPlace(c, ctl.signal);
  const terrainP = fetchTerrain(c, ctl.signal);
  climP.then(() => step("ls-climate", "ls-soil"), () => {});
  soilP.then(() => step("ls-soil", "ls-score"), () => {});

  let clim, agg;
  try {
    clim = await climP;
    agg = aggregateClimate(clim.daily);
  } catch (e) {
    if (ctl.signal.aborted) return;
    content.innerHTML = `
      <div class="p-head">
        <div class="loc-title">${tr("Analysis failed")}</div>
        <div class="loc-geo">${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}</div>
        <button class="panel-close" data-close title="${tr("Close")}">&times;</button>
      </div>
      <div class="p-body">
        <div class="error-box" style="margin-top:var(--s5)">${tr("Could not load the climate record for this point. The Open-Meteo archive may be busy or rate limited; wait a moment and retry.")}<span class="mono">${e.message}</span></div>
        <div class="retry-row"><button id="retry" class="chip">${tr("Retry")}</button></div>
      </div>`;
    $("#retry").onclick = () => analyze(pts);
    return;
  }
  // optional layers must never block results: SoilGrids (beta) sometimes hangs
  const orNull = (p, ms) => Promise.race([p.catch(() => null), new Promise(r => setTimeout(() => r(null), ms))]);
  const [soil, place, terrain] = await Promise.all([orNull(soilP, 15000), orNull(placeP, 8000), orNull(terrainP, 8000)]);
  if (ctl.signal.aborted) return;

  await speciesReady;
  const site = { ...agg, ph: soil?.phh2o ?? null, lat: c.lat, elevation: clim.elevation, place: place?.label ?? null, terrain };
  const scored = SPECIES
    .map(sp => ({ sp, ...scoreSpecies(sp, site) }))
    .sort((a, b) => (b.score - a.score) || (b.fit - a.fit));
  step("ls-score");

  current = { site, scored, pts, center: c, ha, filter: "all", habit: "tree", shown: 12, cc: place?.cc ?? null, state: place?.state ?? "", critOpen: false };
  renderResults();
  loadRowPhotos();
  gbifEvidence(scored.filter(s => s.score > 0.05).slice(0, 20), L.latLngBounds(pts), ctl.signal);
  futureOutlook(ctl);
}

function step(doneId, nextId) {
  document.getElementById(doneId)?.classList.replace("active", "done");
  document.getElementById(nextId)?.classList.add("active");
}

function openPanel(html) {
  content.innerHTML = html;
  panel.hidden = false;
}
panel.addEventListener("click", e => {
  if (e.target.closest("[data-del]")) { // explicit area deletion
    deleteActiveArea();
    return;
  }
  if (e.target.closest("[data-close]")) { // closes the panel; deletes nothing
    panel.hidden = true;
    history.replaceState(null, "", location.pathname);
  }
});

// ---------- results rendering ----------
const USE_LABELS = { timber: "timber", fruit: "fruit", environmental: "environment", medicinal: "medicinal", forage: "forage", materials: "materials", food: "food", ornamental: "ornamental" };

const nativeHere = sp => current.cc && NATIVES[sp.id] ? NATIVES[sp.id].includes(current.cc) : null;

// R$/ha at 3x2 m spacing, Instituto Escolhas 2023 (Tabela 11); each range spans
// labour arrangements from own workforce to contracted crews
const COSTS = [
  ["Natural regeneration management", 2430, 5856],
  ["Regeneration + enrichment", 6096, 12196],
  ["Regeneration + densification + enrichment", 10286, 19900],
  ["Seedling planting, mechanized", 18545, 31059],
  ["Seedling planting, manual", 19591, 36582],
  ["Direct seeding, mechanized", 14986, 21213],
  ["Direct seeding, manual", 14856, 23398],
];
const brl = v => v >= 1e6
  ? `R$ ${(v / 1e6).toLocaleString(LOCALE, { maximumFractionDigits: 1 })}M`
  : `R$ ${fmt(v)}`;
// Lei 12.651/2012 Art. 61-A recomposition strips (consolidated areas), metres
// per margin, by property size in fiscal modules; Art. 61-B caps the total.
const APP61A = {
  rios: { "1": 5, "2": 8, "4": 15, "10": 20 },
  nascentes: { "1": 5, "2": 8, "4": 15, "10": 15 },
  lagos: { "1": 5, "2": 8, "4": 15, "10": 30 },
};
// Resolucao SMA 32/2014 Anexo I "adequado" trajectory + Anexo II gate (year 20)
const SMA32 = {
  florestas: { dens: [200, 1000, 2000, 2500, 3000], spp: [3, 10, 20, 25, 30] },
  cerrado: { dens: [200, 500, 1000, 1500, 2000], spp: [3, 10, 15, 20, 25] },
};
const SMA_AGES = [3, 5, 10, 15, 20];

function legalMarkup() {
  if (current.cc !== "BR") return "";
  const lg = current.legal ?? (current.legal = { mf: "2", app: "rios", veg: "florestas" });
  const lrow = (label, key, opts) => `<div class="crit-row">
    <div class="k">${tr(label)}</div>
    <div class="opts">${opts.map(([v, txt]) => `<button class="opt${lg[key] === v ? " on constrained" : ""}" data-f="${key}" data-v="${v}">${tr(txt)}</button>`).join("")}</div>
  </div>`;
  const width = APP61A[lg.app][lg.mf];
  const cap = lg.mf === "1" || lg.mf === "2"
    ? tfmt("Art. 61-B: total recomposition capped at {p}% of the property", { p: 10 })
    : lg.mf === "4"
      ? tfmt("Art. 61-B: total recomposition capped at {p}% of the property", { p: 20 })
      : tr("above 4 MF the 61-B cap does not apply; for rivers, 20 m covers watercourses up to 10 m wide");

  let sma = "";
  if (/s[aã]o paulo/i.test(current.state)) {
    const t = SMA32[lg.veg];
    const rows = SMA_AGES.map((age, i) => {
      const gate = age === 20;
      return `<div class="stat${gate ? " wide" : ""}"><span class="sk">${tfmt("{n} years", { n: age })}${gate ? ` &middot; ${tr("sign-off gate (Anexo II)")}` : ""}</span>
        <span class="sv">&gt;80% &middot; &gt;${fmt(t.dens[i])} ind/ha &middot; &gt;${t.spp[i]} spp</span></div>`;
    }).join("");
    const plots = Math.min(50, Math.max(5, Math.ceil(current.ha) + 4));
    sma = `<div class="section-h">${tr("SMA 32 targets (SP)")}</div>
      <div class="crit-panel">${lrow("Use", "lveg", [["florestas", "ombrophilous and seasonal forests"], ["cerrado", "cerradao / cerrado stricto sensu"]])}</div>
      <div class="stats" style="margin-top:0">${rows}</div>
      <div class="evidence">${tfmt("Plots for this area: {n} of 100 m2 (25 x 4 m). A regenerant counts from 50 cm height with CAP under 15 cm.", { n: plots })}
        ${tr("Anexo III suggests at least 80 regional native species for full-area planting. It is guidance, not a requirement.")}</div>`;
  }

  return `<div class="section-h">${tr("Legal &middot; Forest Code")}</div>
    <div class="crit-panel">
      ${lrow("Property", "lmf", [["1", "up to 1 MF"], ["2", "1 to 2 MF"], ["4", "2 to 4 MF"], ["10", "over 4 MF"]])}
      ${lrow("APP type", "lapp", [["rios", "rivers and streams"], ["nascentes", "springs"], ["lagos", "lakes and ponds"]])}
    </div>
    <div class="stats" style="margin-top:0">
      <div class="stat wide"><span class="sk">${tr("Strip to recompose (Art. 61-A)")}</span><span class="sv">${tfmt("{w} m on each margin", { w: width })}</span></div>
    </div>
    <div class="evidence">${cap}</div>
    ${sma}`;
}

function costsMarkup() {
  const rows = COSTS.map(([k, lo, hi]) =>
    `<div class="stat"><span class="sk">${tr(k)}</span><span class="sv">${brl(lo)}&ndash;${brl(hi)}/ha</span></div>`).join("");
  return `<div class="section-h" title="${tr("range across labour arrangements, own workforce to contracted; 2023 prices, 3x2 m spacing")}">${tr("Restoration cost")}</div>
    <div class="stats" style="margin-top:0">
      ${rows}
      <div class="stat wide"><span class="sk">${tr("Seedling planting in this area")}</span><span class="sv">${brl(18545 * current.ha)}&ndash;${brl(36582 * current.ha)}</span></div>
    </div>`;
}

// class-level metrics, memoised per growth class
const MAT_CLS = {}, CROWN_CLS = {};
const matCls = g => MAT_CLS[g] ??= maturityYears(CLASSES[g]);
const crownCls = g => CROWN_CLS[g] ??= crownDisplayM(CLASSES[g], Math.min(maturityYears(CLASSES[g]), 120));

const critMatch = (s, c) => s.score > 0.05
  && (c.habit === "all" || s.sp.porte === c.habit)
  && (c.use === "all" || s.sp.uses.includes(c.use))
  && (!c.nativeOnly || nativeHere(s.sp) === true)
  && (!c.matMax || (s.sp.tree && matCls(s.sp.gclass) <= c.matMax))
  && (!c.crownMin || (s.sp.tree && crownCls(s.sp.gclass) >= c.crownMin));

const critState = () => ({ use: current.filter, nativeOnly: current.nativeOnly, matMax: current.matMax, crownMin: current.crownMin, habit: current.habit ?? "tree" });
const critCount = over => current.scored.reduce((n, s) => n + (critMatch(s, { ...critState(), ...over }) ? 1 : 0), 0);

const CRIT_DIMS = () => [
  ...(current.cc ? [{
    key: "origin", label: "Origin", cur: current.nativeOnly ? "native" : "all",
    opts: [["all", tr("all origins")], ["native", tr("native here")]],
    over: v => ({ nativeOnly: v === "native" }),
  }] : []),
  {
    key: "habit", label: "Habit", cur: current.habit ?? "tree",
    opts: [["tree", tr("trees")], ["shrub", tr("shrubs")], ["herb", tr("herbs")], ["grass", tr("grasses")], ["vine", tr("vines")], ["all", tr("all habits")]],
    over: v => ({ habit: v }),
  },
  {
    key: "use", label: "Use", cur: current.filter,
    opts: [["all", tr("all uses")], ...["timber", "fruit", "environmental", "medicinal", "forage"].map(u => [u, tr(USE_LABELS[u])])],
    over: v => ({ use: v }),
  },
  ...((current.habit ?? "tree") === "tree" ? [{
    key: "mat", label: "Maturity", title: tr("Time to max height"), cur: String(current.matMax ?? ""),
    opts: [["", tr("no limit")], ["20", tfmt("under {n} years", { n: 20 })], ["90", tfmt("under {n} years", { n: 90 })]],
    over: v => ({ matMax: v ? +v : null }),
  },
  {
    key: "crown", label: "Mature canopy", cur: String(current.crownMin ?? ""),
    opts: [["", tr("no minimum")], ["4", "&ge; 4 m"], ["5", "&ge; 5 m"]],
    over: v => ({ crownMin: v ? +v : null }),
  }] : []),
];

function critMarkup() {
  const dims = CRIT_DIMS();
  const n = critCount({});
  const total = critCount({ use: "all", nativeOnly: false, matMax: null, crownMin: null, habit: current.habit ?? "tree" });
  const active = dims.flatMap(d => {
    const i = d.opts.findIndex(o => o[0] === d.cur);
    return i > 0 ? [d.opts[i][1]] : [];
  });

  const rows = dims.map(d => `<div class="crit-row">
    <div class="k"${d.title ? ` title="${d.title}"` : ""}>${tr(d.label)}</div>
    <div class="opts">${d.opts.map(([v, txt], i) => {
      const on = d.cur === v, c = on ? 0 : critCount(d.over(v));
      return `<button class="opt${on ? (i ? " on constrained" : " on") : ""}" data-f="${d.key}" data-v="${v}"${on ? ' aria-pressed="true"' : ""}${!on && !c ? " disabled" : ""}>${txt}${on ? "" : `<span class="c">${c}</span>`}</button>`;
    }).join("")}</div></div>`).join("");

  return `<div class="sec-row">
      <div class="section-h">${tr("Recommended species")}</div>
      <button class="crit-toggle${active.length ? " active" : ""}" data-crit-toggle aria-expanded="${current.critOpen ? "true" : "false"}">${
        active.length ? tfmt("{n} of {t}", { n: `<b>${fmt(n)}</b>`, t: fmt(total) }) : tfmt("{n} species", { n: `<b>${fmt(total)}</b>` })
      } &middot; ${tr("criteria")}<i class="car"></i></button>
    </div>
    ${active.length && !current.critOpen ? `<button class="crit-summary" data-crit-toggle>${active.map(a => `<b>${a}</b>`).join(' <span class="d">&middot;</span> ')}</button>` : ""}
    <div class="crit-panel"${current.critOpen ? "" : " hidden"}>${rows}${
      active.length ? `<button class="crit-clear" data-crit-clear>${tr("clear criteria")}</button>` : ""
    }</div>`;
}

function loadRowPhotos() {
  content.querySelectorAll("[data-thumb]").forEach(el => {
    const item = current.scored.find(x => x.sp.id === +el.dataset.thumb);
    if (item) fillPhoto(item);
  });
}

function renderResults() {
  const { site, scored, ha, filter, shown } = current;
  const noLand = site.ph == null && (site.elevation == null || site.elevation < 1) && !current.force;
  const dls = monthlyDaylengths(site.lat);
  const suitable = scored.filter(s => s.score > 0.4).length;

  const pool = scored.filter(s => critMatch(s, critState()));
  const rows = pool.slice(0, shown);


  // the place name is the datum; the administrative tail is annotation
  const place = site.place ?? tr("Selected area");
  const [head, tail] = place.split(/,(.+)/s);
  const titleHtml = tail ? `${head}<span class="adm">,${tail}</span>` : head;
  const rd = (k, v, title) =>
    `<div class="rd"${title ? ` title="${title}"` : ""}><span>${k}</span><b>${v}</b></div>`;

  openPanel(`
    <div class="p-head">
      <div class="loc-title">${titleHtml}</div>
      <div class="loc-geo">${current.center.lat.toFixed(4)}, ${current.center.lng.toFixed(4)}<span class="sep">&middot;</span>${fmtHa(ha)}</div>
      ${noLand ? "" : `<div class="loc-note">${tfmt("{s} of {n} species rate suitable or better",
        { s: `<b>${fmt(suitable)}</b>`, n: `<b>${fmt(SPECIES.length)}</b>` })}</div>`}
      <button class="panel-del" data-del title="${tr("Delete area")}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg></button>
      <button class="panel-close" data-close title="${tr("Close")}">&times;</button>
    </div>
    <div class="p-body">
    <div class="section-h">${tr("Site climate &middot; ERA5 2015&ndash;2024")}</div>
    <div class="site-fig">${climateSvg(site)}</div>
    <div class="readout">
      ${rd(tr("soil pH"), site.ph != null ? fmt(site.ph, 1) : tr("no data"))}
      ${rd(tr("elevation"), `${fmt(site.elevation)} m`)}
      ${rd(tr("daylength"), `${fmt(Math.min(...dls), 1)}&ndash;${fmt(Math.max(...dls), 1)} h`)}
      ${rd(tr("record low"), site.absMin != null ? `${fmt(site.absMin)} °C` : tr("n/a"))}
      ${rd(tr("sun"), site.rad != null ? `${fmt(site.rad, 1)} ${tr("kWh/m²·day")}` : tr("n/a"), tr("mean daily shortwave radiation, all weather included"))}
      ${rd(tr("humidity"), site.rh != null ? `${fmt(site.rh)}%` : tr("n/a"))}
      ${rd(tr("cloud"), site.cloud != null ? `${fmt(site.cloud)}%` : tr("n/a"), tr("high humidity plus high cloud cover marks fog-prone sites"))}
      ${rd(tr("slope"), site.terrain ? `${fmt(site.terrain.slope)}°${site.terrain.facing ? ` ${tr("facing")} ` + tr(site.terrain.facing) : ""}` : tr("n/a"))}
    </div>
    ${noLand ? `<div class="error-box" style="margin-top:12px">${tfmt("This area looks like open water (no soil data, elevation {e} m). Species scores here reflect climate only and are unlikely to be meaningful.", { e: fmt(site.elevation) })}</div><div class="retry-row"><button class="chip" data-force>${tr("Show scores anyway")}</button></div>` : `
    ${critMarkup()}
    <div id="sp-list">${rows.map((s, i) => speciesRow(s, i)).join("") || `<div class="sp-empty">${tr("Nothing clears the bar for this filter here.")}</div>`}</div>
    ${pool.length > shown ? `<button class="chip more" data-more>${tfmt("Show {n} more", { n: Math.min(20, pool.length - shown) })}</button>` : ""}
    ${costsMarkup()}
    ${legalMarkup()}`}
    <div class="retry-row"><button class="chip" data-print>${tr("Report")}</button> <button class="chip" data-shp>${tr("SHP (SARE)")}</button> <button class="chip" data-csv>${tr("CSV")}</button></div>
    <div class="footnote">
      ${tr("Suitability follows the FAO EcoCrop model (trapezoidal climate envelopes, most-limiting-factor). Growth and carbon are class-level estimates")}
      ${tr("(Chapman-Richards, Chave 2014 / Jenkins 2003, IPCC 2006), for screening, not planting prescriptions.")}<br>
      ${tr("Data:")} <a href="https://gaez.fao.org/pages/ecocrop" target="_blank">FAO EcoCrop</a> &middot;
      <a href="https://open-meteo.com/" target="_blank">Open-Meteo ERA5</a> &middot;
      <a href="https://soilgrids.org/" target="_blank">SoilGrids 2.0, ISRIC (CC-BY 4.0)</a> &middot;
      <a href="https://www.gbif.org/" target="_blank">GBIF</a> &middot;
      <a href="https://powo.science.kew.org/" target="_blank">WCVP v16, RBG Kew (CC BY 3.0)</a> &middot;
      <a href="https://www.inaturalist.org/" target="_blank">${tr("Photos: iNaturalist")}</a> &middot;
      <a href="https://escolhas.org/wp-content/uploads/2023/09/Relatorio_RecuperacaoVegetal_Final.pdf" target="_blank">${tr("Costs: Instituto Escolhas 2023")}</a><br>
      ${tr("Map:")} Esri World Imagery (Esri, Vantor, Earthstar Geographics) &middot; &copy; OpenStreetMap contributors &middot; &copy; CARTO &middot; Leaflet
    </div>
    </div>
    <div class="panel-fade"></div>`);
}

function speciesRow(s, i) {
  const pct = Math.round(s.score * 100);
  const col = gradeColor(s.score);
  return `
  <div class="sp" data-id="${s.sp.id}">
    <div class="sp-head" data-toggle>
      <div class="sp-rank">${i + 1}</div>
      <div class="sp-thumb" data-thumb="${s.sp.id}"${s.photo?.sq ? ` style="background-image:url(&quot;${s.photo.sq}&quot;)"` : ""}></div>
      <div class="sp-names">
        <div class="sp-common">${s.sp.common === s.sp.sci ? `<i>${s.sp.sci}</i>` : cap(s.sp.common)}
          ${nativeHere(s.sp) === true ? `<span class="nearby" title="${tr("Part of the native flora of this country (WCVP)")}">${tr("native")}</span>` : ""}
          <span class="nearby gbif" data-nearby="${s.sp.id}" ${s.gbif?.count > 0 ? "" : "hidden"} title="${tr("GBIF occurrence records near this area")}">&#10003; ${tr("nearby")}</span>
          <span class="nearby warn45" data-f45="${s.sp.id}" ${s.score > 0.4 && s.f45 != null && s.f45 <= 0.4 ? "" : "hidden"} title="${tr("Falls below suitable in the 2040s climate (CMIP6)")}">2045 &#9662;</span>
        </div>
        <div class="sp-sci">${s.sp.common === s.sp.sci ? s.sp.family : s.sp.sci}</div>
      </div>
      <div class="sp-score">
        <span class="pct" style="color:${col}">${pct}<span class="u">%</span></span>
        <span class="fit">${tr("fit")} ${Math.round(s.fit * 100)}</span>
      </div>
    </div>
    <div class="sp-body" hidden></div>
  </div>`;
}

content.addEventListener("click", e => {
  if (e.target.closest("[data-crit-toggle]")) {
    current.critOpen = !current.critOpen;
    const p = content.querySelector(".crit-panel");
    if (p) p.hidden = !current.critOpen;
    content.querySelector(".crit-toggle")?.setAttribute("aria-expanded", String(current.critOpen));
    content.querySelector(".crit-summary")?.toggleAttribute("hidden", current.critOpen);
    return;
  }
  if (e.target.closest("[data-crit-clear]")) {
    current.filter = "all"; current.nativeOnly = false; current.matMax = null; current.crownMin = null; current.habit = "tree";
    current.shown = 12; renderResults(); loadRowPhotos(); return;
  }
  const opt = e.target.closest(".opt[data-f]");
  if (opt) {
    const v = opt.dataset.v;
    if (["lmf", "lapp", "lveg"].includes(opt.dataset.f)) {
      current.legal[opt.dataset.f === "lmf" ? "mf" : opt.dataset.f === "lapp" ? "app" : "veg"] = v;
      renderResults(); loadRowPhotos();
      return;
    }
    if (opt.dataset.f === "habit") { current.habit = v; current.matMax = null; current.crownMin = null; }
    if (opt.dataset.f === "origin") current.nativeOnly = v === "native";
    if (opt.dataset.f === "use") current.filter = v;
    if (opt.dataset.f === "mat") current.matMax = v ? +v : null;
    if (opt.dataset.f === "crown") current.crownMin = v ? +v : null;
    current.shown = 12; renderResults(); loadRowPhotos(); return;
  }
  if (e.target.closest("[data-print]")) { window.print(); return; }
  if (e.target.closest("[data-shp]")) { shpExport(); return; }
  if (e.target.closest("[data-csv]")) { csvExport(); return; }
  if (e.target.closest("[data-more]")) { current.shown += 20; renderResults(); loadRowPhotos(); return; }
  if (e.target.closest("[data-force]")) { current.force = true; renderResults(); loadRowPhotos(); return; }

  const head = e.target.closest("[data-toggle]");
  if (head) {
    const body = head.nextElementSibling;
    const item = current.scored.find(x => x.sp.id === +head.parentElement.dataset.id);
    if (body.hidden && !body.innerHTML) body.innerHTML = speciesDetail(item.sp.id);
    body.hidden = !body.hidden;
    head.parentElement.classList.toggle("open", !body.hidden);
    if (!body.hidden && item) { fillPhoto(item); if (item.sp.tree) startSim(item); else stopSim(); }
    else stopSim();
  }
});

// species envelope vs this site: dim track = tolerated, bright = optimal,
// tick = where the site sits
function rangeStrip(label, unit, env, val, dec) {
  if (env == null || val == null) return "";
  const [a, b, c, d] = env;
  const lo = Math.min(a, val), hi = Math.max(d, val), span = hi - lo || 1;
  const P = v => (((v - lo) / span) * 100).toFixed(2);
  const f = v => fmt(v, dec);
  const out = val < a || val > d;
  return `<div class="factor">
    <div class="fk">${label}</div>
    <div class="rtrack" title="${tfmt("tolerated {a} to {d} · optimal {b} to {c}", { a: f(a), b: f(b), c: f(c), d: f(d) })}${unit}">
      <div class="rabs" style="left:${P(a)}%;width:${(((d - a) / span) * 100).toFixed(2)}%"></div>
      <div class="ropt" style="left:${P(b)}%;width:${(((c - b) / span) * 100).toFixed(2)}%"></div>
      <div class="rtick${out ? " out" : ""}" style="left:${P(val)}%"></div>
    </div>
    <div class="fx">${f(val)}${unit}</div></div>`;
}
function windowVals(s) {
  const { start, months } = s.window;
  let tsum = 0, rtot = 0;
  for (let k = 0; k < months; k++) {
    const m = (start + k) % 12;
    tsum += current.site.tavg[m]; rtot += current.site.prec[m];
  }
  return { wt: tsum / months, wr: rtot };
}

// One figure, one month axis: temperature above the spine, rain hanging below.
// The spine spans the data, not the container; 4px teeth mark each month for both series.
function climateSvg(site) {
  const W = 414, L = 2, R = 64, top = 16, tH = 50, gapA = 9, letters = 13, gapB = 7, pH = 56, bot = 15;
  const spineY = top + tH + gapA;
  const barTop = spineY + letters + gapB;
  const H = barTop + pH + bot;
  const iw = W - L - R;
  const cx = m => L + (m + 0.5) * iw / 12;
  // narrow bar: at 21px the driest month rendered as a horizontal dash, not a bar
  const bw = Math.max(8, Math.round(iw / 12) - 15);
  const tmid = (Math.max(...site.tavg) + Math.min(...site.tavg)) / 2;
  // floor of 11 C, not 14: at an equatorial site the curve used half the band and looked inert
  const tspan = Math.max(11, Math.max(...site.tavg) - Math.min(...site.tavg) + 4);
  const thi = tmid + tspan / 2, tlo = tmid - tspan / 2;
  const ty = v => top + (thi - v) / (thi - tlo) * tH;
  const pmax = Math.max(...site.prec, 10) * 1.1;
  const py = v => (v / pmax) * pH;
  const warm = site.tavg.indexOf(Math.max(...site.tavg));
  const cold = site.tavg.indexOf(Math.min(...site.tavg));
  const wet = site.prec.indexOf(Math.max(...site.prec));
  const MONO = "IBM Plex Mono, monospace";
  // dark knockout behind in-plot numerals: a label can land exactly on a rule
  const KO = `paint-order="stroke" stroke="rgba(13,17,14,.9)" stroke-width="2.6" stroke-linejoin="round"`;
  const line = site.tavg.map((v, m) => `${m ? "L" : "M"}${cx(m).toFixed(1)},${ty(v).toFixed(1)}`).join("");
  const bars = site.prec.map((v, m) =>
    `<rect x="${(cx(m) - bw / 2).toFixed(1)}" y="${barTop}" width="${bw}" height="${py(v).toFixed(1)}" rx="1.5" fill="#79a6c6" opacity="${m === wet ? .95 : .52}"/>`).join("");
  const teeth = site.tavg.map((_, m) =>
    `<line x1="${cx(m).toFixed(1)}" x2="${cx(m).toFixed(1)}" y1="${spineY - 4}" y2="${spineY}" stroke="rgba(255,255,255,.13)"/>`).join("");
  const months = "JFMAMJJASOND".split("").map((ch, m) =>
    `<text x="${cx(m).toFixed(1)}" y="${spineY + 10}" font-size="8" fill="#6b786f" text-anchor="middle" letter-spacing=".4">${ch}</text>`).join("");
  const hover = site.tavg.map((v, m) =>
    `<rect x="${(cx(m) - iw / 24).toFixed(1)}" y="0" width="${(iw / 12).toFixed(1)}" height="${H}" fill="transparent"><title>${MONTHS[m]} &middot; ${fmt(v, 1)} °C &middot; ${fmt(site.prec[m])} mm</title></rect>`).join("");
  const zeroLabel = Math.abs(ty(0) - ty(site.meanTemp)) < 12 ? "" :
    `<text x="${L + iw + 11}" y="${(ty(0) + 3).toFixed(1)}" font-size="8.5" fill="#6b786f">0 °C</text>`;
  const zero = tlo < 0 && thi > 0
    ? `<line x1="${L}" x2="${L + iw}" y1="${ty(0).toFixed(1)}" y2="${ty(0).toFixed(1)}" stroke="rgba(255,255,255,.12)" stroke-dasharray="3 3"/>${zeroLabel}` : "";
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="monthly temperature and precipitation">
    ${zero}
    <line x1="${L}" x2="${L + iw}" y1="${ty(site.meanTemp).toFixed(1)}" y2="${ty(site.meanTemp).toFixed(1)}" stroke="#d7a463" stroke-opacity=".26" stroke-dasharray="2 3"/>
    <path d="${line}" fill="none" stroke="#d7a463" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${cx(warm)}" cy="${ty(site.tavg[warm]).toFixed(1)}" r="2" fill="#d7a463"/>
    <text x="${cx(warm).toFixed(1)}" y="${(ty(site.tavg[warm]) - 7).toFixed(1)}" font-size="9" font-family="${MONO}" fill="#99a69c" text-anchor="middle" ${KO}>${fmt(site.tavg[warm])}°</text>
    <circle cx="${cx(cold)}" cy="${ty(site.tavg[cold]).toFixed(1)}" r="2" fill="#d7a463"/>
    <text x="${cx(cold).toFixed(1)}" y="${(ty(site.tavg[cold]) + 12).toFixed(1)}" font-size="9" font-family="${MONO}" fill="#99a69c" text-anchor="middle" ${KO}>${fmt(site.tavg[cold])}°</text>
    <text x="${L + iw + 11}" y="${(ty(site.meanTemp) + 1).toFixed(1)}" font-size="10.5" font-family="${MONO}" fill="#d7a463">${fmt(site.meanTemp, 1)} °C</text>
    <text x="${L + iw + 11}" y="${(ty(site.meanTemp) + 12).toFixed(1)}" font-size="8.5" fill="#6b786f">${tr("mean")}</text>
    ${teeth}
    <line x1="${(cx(0) - 12).toFixed(1)}" x2="${(cx(11) + 12).toFixed(1)}" y1="${spineY}" y2="${spineY}" stroke="rgba(255,255,255,.2)"/>
    ${months}
    ${bars}
    <text x="${cx(wet).toFixed(1)}" y="${(barTop + py(site.prec[wet]) + 10).toFixed(1)}" font-size="9" font-family="${MONO}" fill="#99a69c" text-anchor="middle" ${KO}>${fmt(site.prec[wet])}</text>
    <text x="${L + iw + 11}" y="${barTop + 12}" font-size="10.5" font-family="${MONO}" fill="#79a6c6">${fmt(site.annualRain)} mm</text>
    <text x="${L + iw + 11}" y="${barTop + 23}" font-size="8.5" fill="#6b786f">${tr("per year")}</text>
    ${hover}
  </svg>`;
}

function speciesDetail(id) {
  const s = current.scored.find(x => x.sp.id === id);
  const { sp } = s;
  const cls = CLASSES[sp.gclass];
  const [zone, rate] = sp.gclass.split("_");
  const h10 = height(10, cls), h20 = height(20, cls), d20 = dbhCm(h20, cls);
  const crown20 = crownDisplayM(cls, 20);
  const co2Tree20 = co2eKgPerTree(sp, 20);
  const co2Ha20 = co2eTonsPerHa(sp, 20);
  const trees = Math.round(current.ha * STEMS_PER_HA);
  const mat = maturityYears(cls);
  const win = s.window.months < 12
    ? `<div class="stat"><span class="sk">${tr("Best window")}</span><span class="sv">${MONTHS[s.window.start]}&ndash;${MONTHS[(s.window.start + s.window.months - 1) % 12]}</span></div>` : "";

  return `
    <div class="sp-photo" data-hero="${sp.id}" hidden></div>
    <div class="sp-meta"><span class="grade">${tr(grade(s.score))}</span><span class="sep">&middot;</span>${tfmt("{rate} growth &middot; {zone}", { rate: tr(rate), zone: tr(zone) })}</div>
    <div class="sp-uses">${sp.uses.map(u => `<span class="it">${tr(USE_LABELS[u] ?? u)}</span>`).join("")}</div>
    ${(() => {
      const { wt, wr } = windowVals(s);
      const notes = [];
      if (s.factors.photo != null && s.factors.photo < 1) notes.push(tr("Photoperiod outside this species' range: 0.5 penalty applied."));
      if (s.factors.chill != null && s.factors.chill < 1) notes.push(tr("Needs winter dormancy; the coldest month here is too warm for it."));
      return `<div class="factors">
        ${rangeStrip(tr("Temperature"), " °C", sp.temp, wt, 1)}
        ${rangeStrip(tr("Rainfall"), " mm", sp.rain, wr, 0)}
        ${rangeStrip(tr("Soil pH"), "", sp.ph, current.site.ph, 1)}
      </div>${notes.map(n => `<div class="evidence">${n}</div>`).join("")}`;
    })()}
    ${sp.tree ? `<div class="growth-fig">${growthSvg(sp)}
      <div class="fig-cap">${tfmt("Reaches ~95% of its max height in ~{n} years (class-level model).", { n: fmt(mat) })}</div>
    </div>` : ""}

    <div class="stats">
      ${sp.tree ? `<div class="stat"><span class="sk">${tr("Trunk &oslash; 20 yr")}</span><span class="sv">${d20.toFixed(0)} cm</span></div>
      <div class="stat"><span class="sk">${tr("Canopy, 20 yr")}</span><span class="sv">${crown20.toFixed(1)} m &middot; ${fmt(Math.PI / 4 * crown20 * crown20)} m&sup2;</span></div>
      <div class="stat"><span class="sk">${tr("CO&#8322;e/tree, 20 yr")}</span><span class="sv">${fmt(co2Tree20)} kg</span></div>
      <div class="stat"><span class="sk">${tr("Stand CO&#8322;e, 20 yr")}</span><span class="sv">${fmt(co2Ha20)} t/ha</span></div>` : ""}
      ${!sp.tree && sp.cycle && (sp.cycle[0] || sp.cycle[1]) ? `<div class="stat"><span class="sk">${tr("Cycle")}</span><span class="sv">${tfmt("{a} to {b} days", { a: fmt(sp.cycle[0] ?? sp.cycle[1]), b: fmt(sp.cycle[1] ?? sp.cycle[0]) })}</span></div>` : ""}
      ${win}
      ${sp.ktmpr != null ? `<div class="stat"><span class="sk">${tr("Hardy to")}</span><span class="sv">${sp.ktmpr.toFixed(0)} &deg;C</span></div>` : ""}
      <div class="stat"><span class="sk" title="${tr("Rescored on a 2040-2049 CMIP6 projection (MRI-AGCM3-2-S), same scoring engine")}">${tr("Score in the 2040s")}</span><span class="sv" data-f45stat="${sp.id}">${f45Text(s)}</span></div>
      ${sp.tree ? `<div class="stat"><span class="sk">${tr("Trees in this area, 3&times;3 m")}</span><span class="sv">${fmtC(trees)}</span></div>
      <div class="stat wide"><span class="sk">${tr("Area CO&#8322;e by year 20")}</span><span class="sv">${fmtC(co2Ha20 * current.ha)} t</span></div>` : ""}
    </div>`;
}

// ---------- growth chart ----------
// Height growth. The 40 m ceiling is shared across species so they compare
// honestly, which is why a short species leaves the upper half empty on purpose.
function growthSvg(sp) {
  const pts = projection(sp, 40);
  const W = 376, H = 116, L = 26, R = 4, T = 9, B = 16, ymax = 40;
  const x = t => L + (t / 40) * (W - L - R);
  const y = h => T + (1 - h / ymax) * (H - T - B);
  const MONO = "IBM Plex Mono, monospace";
  const KO = `paint-order="stroke" stroke="rgba(13,17,14,.9)" stroke-width="2.6" stroke-linejoin="round"`;
  const path = pts.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.h).toFixed(1)}`).join("");
  const yrules = [20, 40].map(v =>
    `<line x1="${L}" y1="${y(v).toFixed(1)}" x2="${W - R}" y2="${y(v).toFixed(1)}" stroke="rgba(255,255,255,.055)"/>
     <text x="${L - 5}" y="${(y(v) + 3).toFixed(1)}" fill="#6b786f" font-size="8.5" font-family="${MONO}" text-anchor="end">${v}m</text>`).join("");
  const xlab = [10, 20, 30, 40].map(t =>
    `<text x="${x(t).toFixed(1)}" y="${H - 4}" fill="#6b786f" font-size="8.5" font-family="${MONO}" text-anchor="${t === 40 ? "end" : "middle"}">${t}${tr("y")}</text>`).join("");
  const marks = [10, 20].map(t =>
    `<circle cx="${x(t).toFixed(1)}" cy="${y(pts[t].h).toFixed(1)}" r="2.2" fill="#63c987"/>
     <text x="${x(t).toFixed(1)}" y="${(y(pts[t].h) - 7).toFixed(1)}" fill="#e8ede8" font-size="9" font-family="${MONO}" text-anchor="middle" ${KO}>${pts[t].h.toFixed(0)}m</text>`).join("");
  const hover = [5, 10, 15, 20, 25, 30, 35, 40].map(t =>
    `<circle cx="${x(t).toFixed(1)}" cy="${y(pts[t].h).toFixed(1)}" r="10" fill="transparent"><title>${t} ${tr("yr")} &middot; ${fmt(pts[t].h, 1)} m &middot; ${tr("trunk")} ${fmt(pts[t].d)} cm &middot; ${fmt(pts[t].co2)} kg CO&#8322;e</title></circle>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="height growth curve">
    ${yrules}
    <line x1="${L}" y1="${y(0)}" x2="${W - R}" y2="${y(0)}" stroke="rgba(255,255,255,.09)"/>
    <path d="${path}" fill="none" stroke="#63c987" stroke-width="1.7" stroke-linecap="round"/>
    ${marks}${xlab}${hover}</svg>`;
}


// ---------- planting simulator: trees from above, growing over a year slider ----------
// The ACTIVE simulation (the one with the slider pill) lives in SIM; drawing or
// switching areas freezes it into STANDS, keyed by its polygon, so planted
// stands persist on the map at their year until their area is deleted.
let SIM = null;
const STANDS = new Map(); // polygon layer -> frozen {item, cls, trees, year, fullCount}
let simCanvas = null;

function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | a) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function pointInPoly(la, ln, pts) {
  let ins = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const xi = pts[i].lng, yi = pts[i].lat, xj = pts[j].lng, yj = pts[j].lat;
    if ((yi > la) !== (yj > la) && ln < (xj - xi) * (la - yi) / (yj - yi) + xi) ins = !ins;
  }
  return ins;
}

function ensureSimLayer() {
  if (simCanvas) return;
  simCanvas = document.createElement("canvas");
  // leaflet-zoom-animated gives transform-origin 0 0; without it the zoom
  // animation scales around the element CENTER and the stand appears to jump
  simCanvas.className = "sim-canvas leaflet-zoom-animated";
  // inside the overlay pane Leaflet's own zoom/pan transforms apply to the
  // trees exactly as they do to tiles and polygons: no lag, no mirroring
  const pane = map.getPane("overlayPane");
  pane.insertBefore(simCanvas, pane.firstChild);
  map.on("moveend zoomend viewreset resize", drawSim);
  map.on("zoomanim", simZoomAnim);
  map.on("click", simPlant);
  map.on("contextmenu", simRemove);
}
function releaseSimLayerIfIdle() {
  if (SIM || STANDS.size || !simCanvas) return;
  map.off("moveend zoomend viewreset resize", drawSim);
  map.off("zoomanim", simZoomAnim);
  map.off("click", simPlant);
  map.off("contextmenu", simRemove);
  simCanvas.remove();
  simCanvas = null;
}

function startSim(item) {
  freezeSim();
  STANDS.delete(shape); // replanting the active area replaces its previous stand
  const cls = CLASSES[item.sp.gclass];
  const c = current.center;
  const step = 3 / 111320; // 3 m spacing in degrees latitude
  const stepLng = step / Math.max(0.1, Math.cos(c.lat * Math.PI / 180));
  const b = L.latLngBounds(current.pts);
  const CAP = 20000;
  // enormous areas: coarsen the grid first so generation stays fast, then
  // thin uniformly; never a central blob (it reads as a pond from altitude)
  const est = ((b.getNorth() - b.getSouth()) / step) * ((b.getEast() - b.getWest()) / stepLng);
  const coarse = est > 400000 ? Math.ceil(Math.sqrt(est / 400000)) : 1;
  const gStep = step * coarse, gStepLng = stepLng * coarse;
  const rnd = mulberry32(item.sp.id);
  const grid = [];
  for (let la = b.getSouth() + gStep / 2; la < b.getNorth(); la += gStep)
    for (let ln = b.getWest() + gStepLng / 2; ln < b.getEast(); ln += gStepLng)
      if (pointInPoly(la, ln, current.pts)) grid.push([la, ln]);
  const keepP = Math.min(1, CAP / grid.length);
  const kept = keepP < 1 ? grid.filter(() => rnd() < keepP) : grid;
  const fullCount = Math.round(current.ha * STEMS_PER_HA);
  const note = kept.length < fullCount * 0.98
    ? tfmt("showing {n} of {t} trees", { n: fmt(kept.length), t: fmtC(fullCount) }) : "";
  const trees = kept.map(([la, ln]) => ({
    la: la + (rnd() - 0.5) * gStep * 0.6,
    ln: ln + (rnd() - 0.5) * gStepLng * 0.6,
    s: 0.8 + rnd() * 0.4,
    hue: -10 + rnd() * 20,
    rot: rnd() * Math.PI * 2,
    seed: Math.floor(rnd() * 2147483647),
  }));
  const maxY = Math.min(120, Math.ceil(maturityYears(cls)));
  const ctl = document.createElement("div");
  ctl.id = "sim";
  ctl.innerHTML = `<span class="sim-name">${item.sp.common === item.sp.sci ? item.sp.sci : cap(item.sp.common)}</span>
    <input type="range" min="0" max="${maxY}" step="1" value="${Math.min(10, maxY)}">
    <span class="sim-label mono"></span>
    <span class="sim-note">${note ? note + " &middot; " : ""}${tr("click plants a sapling · right-click removes it · Cmd+Z undoes")}</span>
    <button class="panel-close" data-simclose title="${tr("Close")}">&times;</button>`;
  document.body.appendChild(ctl);
  SIM = { item, cls, trees, ctl, year: Math.min(10, maxY), fullCount, rnd, poly: shape };
  ctl.querySelector("input").addEventListener("input", e => { SIM.year = +e.target.value; drawSim(); });
  ctl.querySelector("[data-simclose]").addEventListener("click", stopSim);
  ensureSimLayer();
  map.getContainer().style.cursor = "copy"; // planting is armed while the pill is up
  map.fitBounds(b.pad(0.2));
  drawSim();
}

// the active sim becomes a frozen stand: its trees STAY on the map
function freezeSim() {
  if (!SIM) return;
  if (SIM.poly && shapes.includes(SIM.poly)) {
    STANDS.set(SIM.poly, { item: SIM.item, cls: SIM.cls, trees: SIM.trees, year: SIM.year, fullCount: SIM.fullCount });
  }
  SIM.ctl.remove();
  SIM = null;
  if (!armed) map.getContainer().style.cursor = "";
}

function stopSim() { // freezing, not destroying: called when analysis/card focus moves on
  freezeSim();
  drawSim();
  releaseSimLayerIfIdle();
  updateProj();
}

function removeStand(poly) { // deleting an area takes its planted stand with it
  if (SIM?.poly === poly) {
    SIM.ctl.remove();
    SIM = null;
    if (!armed) map.getContainer().style.cursor = "";
  }
  STANDS.delete(poly);
  drawSim();
  releaseSimLayerIfIdle();
  updateProj();
}

function simPlant(e) {
  if (!SIM || armed) return;
  const rnd = SIM.rnd;
  SIM.trees.push({
    la: e.latlng.lat, ln: e.latlng.lng,
    s: 0.85 + rnd() * 0.3, hue: -10 + rnd() * 20, rot: rnd() * Math.PI * 2,
    seed: Math.floor(rnd() * 2147483647),
    manual: true, // same year-0 cohort as the stand; shown at the slider's age
  });
  drawSim();
}

// right-click a hand-planted sapling to remove it
function simRemove(e) {
  if (!SIM || armed) return;
  const click = map.latLngToContainerPoint(e.latlng);
  let bestI = -1, bestD = Infinity;
  const mpp = 40075016.686 * Math.cos(map.getCenter().lat * Math.PI / 180) / (256 * Math.pow(2, map.getZoom()));
  for (let i = 0; i < SIM.trees.length; i++) {
    const tree = SIM.trees[i];
    if (!tree.manual) continue; // only hand-planted trees are removable this way
    const p = map.latLngToContainerPoint([tree.la, tree.ln]);
    const d = click.distanceTo(p);
    const rPx = SIM.year > 0 ? crownDisplayM(SIM.cls, SIM.year) * tree.s * 1.6 / 2 / mpp : 0;
    if (d < Math.max(12, rPx) && d < bestD) { bestD = d; bestI = i; }
  }
  if (bestI >= 0) {
    SIM.trees.splice(bestI, 1);
    drawSim();
  }
}

// Cmd/Ctrl+Z undoes the most recent hand planting
document.addEventListener("keydown", e => {
  if (!SIM || !(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== "z") return;
  for (let i = SIM.trees.length - 1; i >= 0; i--) {
    if (SIM.trees[i].manual) {
      SIM.trees.splice(i, 1);
      drawSim();
      e.preventDefault();
      return;
    }
  }
});

// Leaflet zoom animation transforms each layer individually (panes are not
// scaled), so the canvas must ride the same zoomanim path as every renderer.
function simZoomAnim(e) {
  // the exact leaflet.heat formula: canvas anchored at the container origin
  if (!simCanvas || !map._getCenterOffset) return;
  const scale = map.getZoomScale(e.zoom);
  const offset = map._getCenterOffset(e.center)._multiplyBy(-scale).subtract(map._getMapPanePos());
  L.DomUtil.setTransform(simCanvas, offset, scale);
}

let simAnchor = null; // where the canvas was drawn, for zoom-animation transforms
function drawSim() {
  if (!simCanvas) return;
  L.DomUtil.setTransform(simCanvas, map.containerPointToLayerPoint([0, 0]), 1);
  simAnchor = { latlng: map.containerPointToLatLng([0, 0]), zoom: map.getZoom() };
  const size = map.getSize();
  const dpr = window.devicePixelRatio || 1;
  simCanvas.width = size.x * dpr; simCanvas.height = size.y * dpr;
  simCanvas.style.width = size.x + "px"; simCanvas.style.height = size.y + "px";
  const g = simCanvas.getContext("2d");
  g.scale(dpr, dpr);
  setCrownSoft(map.getZoom(), 19);   // Esri World Imagery maxNativeZoom
  const mpp = 40075016.686 * Math.cos(map.getCenter().lat * Math.PI / 180) / (256 * Math.pow(2, map.getZoom()));
  for (const stand of STANDS.values()) renderStand(g, stand, size, mpp, false);
  if (SIM) {
    renderStand(g, SIM, size, mpp, true);
    const h = height(SIM.year, SIM.cls);
    const cd = crownDisplayM(SIM.cls, SIM.year);
    const manual = SIM.trees.reduce((n, tr2) => n + (tr2.manual ? 1 : 0), 0);
    SIM.ctl.querySelector(".sim-label").textContent =
      `${tr("year")} ${THIS_YEAR + Math.round(SIM.year)} · ${h.toFixed(1)} m · ${tr("crown")} ${cd.toFixed(1)} m · ${fmtC(SIM.fullCount + manual)} ${tr("trees")}`;
    updateProj();
  }
}

function renderStand(g, stand, size, mpp, active) {
  const { cls, trees } = stand;
  const t = stand.year;
  const conifer = stand.item.sp.wood === "conifer";
  const byAge = new Map(); // saplings planted mid-simulation grow from their planting year
  const saplings = [];     // hand-planted trees too young/small to render as crowns
  const inView = p => p.x >= -40 && p.y >= -40 && p.x <= size.x + 40 && p.y <= size.y + 40;
  for (const tree of trees) {
    const pl = tree.planted ?? 0;
    let m = byAge.get(pl);
    if (m === undefined) {
      const age = t - pl;
      if (age <= 0.01) m = null;
      else m = { h: height(age, cls), cd: crownDisplayM(cls, age) };
      byAge.set(pl, m);
    }
    if (!m || m.h < 0.3) {
      if (active && tree.manual) {
        const p = map.latLngToContainerPoint([tree.la, tree.ln]);
        if (inView(p)) saplings.push(p);
      }
      continue;
    }
    const p = map.latLngToContainerPoint([tree.la, tree.ln]);
    if (!inView(p)) continue;
    const open = tree.manual ? 1.6 : 1; // isolated trees spread open-grown crowns
    const r = m.cd * tree.s * open / 2 / mpp;
    if (r <= 0.05) {
      if (active && tree.manual) saplings.push(p);
      continue;
    }
    drawTree(g, p.x, p.y, Math.max(r, 0.4), tree, conifer);
    if (active && tree.manual && r < 2) saplings.push(p);
  }
  // a just-planted sapling is real but invisible at crown scale; mark it so
  // clicking the map gives immediate feedback
  for (const p of saplings) {
    g.beginPath();
    g.arc(p.x, p.y, 3, 0, 7);
    g.fillStyle = "rgba(99, 201, 135, .9)";
    g.fill();
    g.lineWidth = 1.5;
    g.strokeStyle = "rgba(10, 14, 9, .8)";
    g.stroke();
  }
}

// Crown renderer — candidate implementation for app.js drawTree().
//
// Calibrated against the same Esri World Imagery the app uses as its basemap,
// sampled over Atlantic forest at Cubatao (z18/z19):
//   HSL lightness p10 4.6, p25 13.8, p50 23.2, p75 30.3, p90 34.6, p98 39
//   hue p50 123 deg, saturation p50 22%, 8x8 luminance sigma 11-14
//   sun from the NE: ground shadows fall SW (measured off tank/pole shadows)
//
// Technique: pre-rendered sprite atlas, one drawImage per tree.
//  - detail is sized in ground units, not screen pixels, so texture contrast
//    falls off with zoom the way a fixed-GSD sensor's does;
//  - above maxNativeZoom the basemap is an upscale, so sprites upscale too;
//  - each sprite is histogram-matched to the reference imagery, so the palette
//    is measured rather than hand-picked;
//  - crown edges are feathered, so neighbours interleave into one canopy
//    instead of stacking as legible discs.

const SPR_R = [3, 7, 16, 40];               // reference crown radius per tier, CSS px
const SPR_SIL = 6, SPR_TINT = 7, SPR_N = SPR_SIL * SPR_TINT;
const TUFT = 0.19;                          // foliage tuft radius / crown radius
const LX = 0.455, LY = -0.455, LZ = 0.766;  // sun from NE, ~50 deg elevation

// Reference quantiles, and how much of that range one crown spans on its own:
// the rest of the spread has to come from crown-to-crown tone, or the canopy
// ends up with the right histogram but far too much local contrast.
const TONE_Q = [0, 0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98, 1];
const TONE_L = [0, 1.6, 4.6, 13.8, 23.2, 30.3, 34.6, 39.0, 47];
const TONE_MID = 23.2, TONE_NARROW = 0.55, TONE_LIFT = 1.10;

let SPR = null, SPR_DPR = 0, SOFT = 1;

// Above the imagery's native zoom Leaflet upscales its tiles; match that blur by
// picking a smaller sprite and scaling it up rather than inventing detail.
function setCrownSoft(zoom, maxNative) {
  SOFT = Math.min(4, Math.pow(2, Math.max(0, zoom - maxNative + 0.5)));
}

function crownSet(tier, conifer) {
  const dpr = window.devicePixelRatio || 1;
  if (!SPR || SPR_DPR !== dpr) { SPR = [[], []]; SPR_DPR = dpr; }
  const bank = SPR[conifer ? 1 : 0];
  let set = bank[tier];
  if (!set) {
    set = bank[tier] = [];
    for (let i = 0; i < SPR_N; i++) set.push(buildCrown(tier, conifer, i, dpr));
  }
  return set;
}

function buildCrown(tier, conifer, variant, dpr) {
  const R0 = SPR_R[tier];
  const sil = variant % SPR_SIL, tint = (variant / SPR_SIL) | 0;
  const rf = 0.92 + sil * (0.16 / (SPR_SIL - 1));   // crowns vary in width, not only shape
  const R = R0 * rf, gr = Math.max(0.45, R * TUFT);
  const M = Math.max(2, R0 * 0.86);                 // room for lobes + the SW ground shadow
  const W = Math.ceil((R0 + M) * 2), cx = W / 2, cy = W / 2;
  const rng = mulberry32(1013904 + sil * 6151 + tier * 3331 + (conifer ? 7717 : 0));

  const hue0 = (conifer ? 126 : 122) + (rng() - 0.5) * 5;
  const sat0 = (conifer ? 19 : 16) + (rng() - 0.5) * 4;
  const deepL = conifer ? 3 : 4;                    // between-tuft gaps: near black
  const litL = conifer ? 40 : 44;

  // irregular silhouette: four octaves of angular noise, tighter for conifers
  const p1 = rng() * 6.283, p2 = rng() * 6.283, p3 = rng() * 6.283, p4 = rng() * 6.283;
  const lob = conifer ? 0.5 : 1;
  const rad = a => R * (1 + lob * (0.125 * Math.sin(3 * a + p1) + 0.088 * Math.sin(5 * a + p2)
    + 0.058 * Math.sin(8 * a + p3) + 0.038 * Math.sin(13 * a + p4)));

  // ---- crown body, drawn on its own so it can be feathered and calibrated ----
  const body = document.createElement("canvas");
  body.width = body.height = Math.round(W * dpr);
  const b = body.getContext("2d");
  b.scale(dpr, dpr);

  const path = new Path2D();
  const NSEG = tier < 2 ? 24 : 72;
  for (let i = 0; i <= NSEG; i++) {
    const a = i / NSEG * 6.28319, rr = rad(a);
    const px = cx + Math.cos(a) * rr, py = cy + Math.sin(a) * rr;
    i ? path.lineTo(px, py) : path.moveTo(px, py);
  }
  path.closePath();

  // sub-crown lobes: real crowns are several bright masses, not one smooth ball
  const NL = 4 + Math.floor(rng() * 5), lobes = [];
  for (let i = 0; i < NL; i++) {
    const a = rng() * 6.283, d = Math.sqrt(rng()) * R * 0.62;
    lobes.push([Math.cos(a) * d, Math.sin(a) * d, (rng() - 0.5) * 0.42, R * (0.30 + rng() * 0.30)]);
  }
  const shadeOf = (dx, dy, jit) => {
    const u = dx / R, v = dy / R;
    const w = Math.sqrt(Math.max(0.04, 1 - u * u - v * v));
    let s = 0;
    for (let j = 0; j < NL; j++) {
      const ex = dx - lobes[j][0], ey = dy - lobes[j][1], rr = lobes[j][3];
      const t = 1 - (ex * ex + ey * ey) / (rr * rr);
      if (t > 0) s += lobes[j][2] * t;
    }
    const nd = 0.18 + 0.50 * (u * LX + v * LY + w * LZ) + s + jit;
    return nd < 0 ? 0 : nd > 1 ? 1 : nd;
  };
  const tuftCol = nd => `hsl(${hue0 + (rng() - 0.5) * 10}, ${sat0 + (1 - nd) * 9}%, ` +
    `${deepL + (litL - deepL) * Math.pow(nd, 0.85)}%)`;

  b.save();
  b.clip(path);
  b.fillStyle = `hsl(${hue0 + 8}, ${sat0 + 7}%, ${deepL}%)`;
  b.fillRect(0, 0, W, W);

  // Foliage mounds over a dark base. No ring is drawn around each mound: the
  // crevices are simply where the base shows through, which comes out sinuous
  // and irregular like the real canopy instead of a field of round dimples.
  // Every mound is nudged up-sun, so the base peeks out on its shaded side.
  for (let oct = 0; oct < 2; oct++) {
    const fg = oct ? gr * 0.46 : gr, step = fg * (oct ? 1.5 : 1.04), pts = [];
    for (let py = -R * 1.1; py <= R * 1.1; py += step)
      for (let px = -R * 1.1; px <= R * 1.1; px += step) {
        const jx = px + (rng() - 0.5) * step * 1.05, jy = py + (rng() - 0.5) * step * 1.05;
        const d2 = jx * jx + jy * jy;
        if (oct && rng() < 0.5) continue;
        if (Math.sqrt(d2) > rad(Math.atan2(jy, jx)) * (1 + 0.26 * rng())) continue;
        pts.push([jx, jy, rng(), rng()]);
      }
    pts.sort((A, B) => (A[0] - A[1]) - (B[0] - B[1]));
    const amp = oct ? 0.10 : 0.20;   // mounds belong to a crown; keep them coherent
    for (let i = 0; i < pts.length; i++) {
      const dx = pts[i][0], dy = pts[i][1], q = pts[i][3];
      const nd = shadeOf(dx, dy, (pts[i][2] - 0.5) * amp);
      if (oct && nd < 0.42) continue;                  // fine highlights only on lit mounds
      const fr = fg * (q > 0.9 ? 1.5 + q : 0.62 + q * 0.85);
      b.fillStyle = tuftCol(oct ? Math.min(1, nd + 0.14) : nd);
      b.beginPath();
      b.arc(cx + dx + fr * 0.16, cy + dy - fr * 0.16, fr * (oct ? 0.7 : 1.0), 0, 6.28319);
      b.fill();
    }
  }

  if (conifer) { // whorled branch structure reads through from above
    b.strokeStyle = `hsla(${hue0}, ${sat0 + 6}%, 5%, 0.30)`;
    b.lineWidth = Math.max(0.6, R * 0.05);
    const spokes = 7 + Math.floor(rng() * 4);
    for (let i = 0; i < spokes; i++) {
      const a = rng() * 6.283 + i / spokes * 6.283;
      b.beginPath();
      b.moveTo(cx + Math.cos(a) * R * 0.10, cy + Math.sin(a) * R * 0.10);
      b.lineTo(cx + Math.cos(a) * R * 0.86, cy + Math.sin(a) * R * 0.86);
      b.stroke();
    }
  }
  b.restore();

  // spur tufts across the silhouette so the edge never reads as a clean disc
  for (let i = 0, n = tier < 2 ? 12 : 30; i < n; i++) {
    const a = rng() * 6.283, rr = rad(a) * (0.90 + rng() * 0.24);
    const dx = Math.cos(a) * rr, dy = Math.sin(a) * rr;
    const fr = gr * (0.55 + rng() * 0.5);
    b.fillStyle = tuftCol(shadeOf(dx, dy, (rng() - 0.5) * 0.4));
    b.beginPath(); b.arc(cx + dx, cy + dy, fr * 0.9, 0, 6.28319); b.fill();
  }

  calibrate(b, W, dpr, (conifer ? 0.86 : 1) * (0.45 + tint * (0.85 / (SPR_TINT - 1))));

  // Feather the outer edge. Crowns overlap heavily at real stand densities, and
  // a hard edge is what makes a stand read as a tray of separate balls.
  b.globalCompositeOperation = "destination-out";
  const fade = b.createRadialGradient(cx, cy, R * 0.88, cx, cy, R * 1.34);
  fade.addColorStop(0, "rgba(0,0,0,0)");
  fade.addColorStop(0.45, "rgba(0,0,0,0.20)");
  fade.addColorStop(0.75, "rgba(0,0,0,0.55)");
  fade.addColorStop(1, "rgba(0,0,0,0.95)");
  b.fillStyle = fade; b.fillRect(0, 0, W, W);
  b.globalCompositeOperation = "source-over";

  // ---- final sprite: ground shadow first, crown over it ----
  const c = document.createElement("canvas");
  c.width = c.height = Math.round(W * dpr);
  const g = c.getContext("2d");
  g.scale(dpr, dpr);
  const sh = g.createRadialGradient(cx - R * 0.30, cy + R * 0.34, R * 0.10,
                                    cx - R * 0.30, cy + R * 0.34, R * 1.05);
  sh.addColorStop(0, "rgba(6,15,9,0.50)");
  sh.addColorStop(0.55, "rgba(6,15,9,0.32)");
  sh.addColorStop(1, "rgba(6,15,9,0)");
  g.fillStyle = sh; g.fillRect(0, 0, W, W);
  g.drawImage(body, 0, 0, W, W);
  return { c, w: W, cx, cy };
}

// Histogram-match the crown body to the reference imagery instead of hand-tuning
// constants. `scale` is the tint bank's exposure, so tone patches survive it.
function calibrate(g, W, dpr, scale) {
  const px = Math.round(W * dpr);
  const img = g.getImageData(0, 0, px, px), d = img.data, n = px * px;
  const lum = new Float32Array(n), ls = [];
  for (let i = 0; i < n; i++) {
    const r = d[i * 4], gg = d[i * 4 + 1], bb = d[i * 4 + 2];
    const l = (Math.max(r, gg, bb) + Math.min(r, gg, bb)) / 5.1;   // HSL L, 0..100
    lum[i] = l;
    if (d[i * 4 + 3] > 200) ls.push(l);
  }
  if (ls.length < 24) return;
  ls.sort((a, b) => a - b);
  const src = TONE_Q.map(q => ls[Math.round(q * (ls.length - 1))]);
  const dst = TONE_L.map(l => Math.min(58, (TONE_MID + (l - TONE_MID) * TONE_NARROW) * scale * TONE_LIFT));
  for (let i = 0; i < n; i++) {
    if (d[i * 4 + 3] === 0) continue;
    const l = lum[i];
    let k = 1;
    while (k < src.length - 1 && l > src[k]) k++;
    const s0 = src[k - 1], s1 = src[k];
    const nl = dst[k - 1] + (dst[k] - dst[k - 1]) * (s1 > s0 ? (l - s0) / (s1 - s0) : 0);
    if (l <= 0.4) continue;
    const f = Math.min(5, Math.max(0.12, nl / l));
    d[i * 4] = Math.min(255, d[i * 4] * f);
    d[i * 4 + 1] = Math.min(255, d[i * 4 + 1] * f);
    d[i * 4 + 2] = Math.min(255, d[i * 4 + 2] * f);
  }
  g.putImageData(img, 0, 0);
}

// Canopy tone patches: neighbouring trees share a tint, so a stand breaks into
// lighter and darker masses instead of reading as one uniform lattice.
function hash2(x, y) {
  let n = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263);
  n = Math.imul(n ^ n >>> 13, 1274126177);
  return ((n ^ n >>> 16) >>> 0) / 4294967296;
}
function vnoise(X, Y) {
  const x0 = Math.floor(X), y0 = Math.floor(Y), fx = X - x0, fy = Y - y0;
  const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
  const a = hash2(x0, y0), b = hash2(x0 + 1, y0), c = hash2(x0, y0 + 1), d = hash2(x0 + 1, y0 + 1);
  const t = a + (b - a) * sx;
  return t + ((c + (d - c) * sx) - t) * sy;
}
function toneOf(tree) {
  if (tree.tn === undefined) {
    const X = tree.ln * 3400, Y = tree.la * 3400;       // ~30 m cells, plus a ~95 m octave
    let n = 0.52 * vnoise(X, Y) + 0.48 * vnoise(X / 3.1, Y / 3.1);
    n = (n - 0.5) * 2.2 + 0.5;
    tree.tn = n < 0 ? 0 : n > 0.999 ? 0.999 : n;
  }
  return tree.tn;
}

// sub-pixel trees: one rect, lightness drawn from the real canopy histogram
const SUBPX = [];
for (let i = 0; i < 16; i++)
  SUBPX.push(`hsl(${119 + (i * 7) % 11}, ${16 + (i * 5) % 9}%, ${5.5 + i * 2.3}%)`);

function drawTree(g, x, y, r, tree, conifer) {
  if (r < 1.4) { // sub-pixel: a single rect, but never a uniform one
    g.fillStyle = SUBPX[tree.seed & 15];
    const w = r * 2 + 0.4;
    g.fillRect(x - w / 2, y - w / 2, w, w);
    return;
  }
  const e = r / SOFT;
  const tier = e < 6.5 ? 0 : e < 15 ? 1 : e < 35 ? 2 : 3;
  const set = crownSet(tier, conifer);
  let ti = toneOf(tree) * SPR_TINT + ((tree.seed >>> 11 & 3) - 1.5) * 0.6;
  ti = ti < 0 ? 0 : ti > SPR_TINT - 1 ? SPR_TINT - 1 : ti;
  const sp = set[((tree.seed >>> 3) % SPR_SIL) * SPR_TINT + (ti | 0)];
  const k = r / SPR_R[tier];
  g.drawImage(sp.c, x - sp.cx * k, y - sp.cy * k, sp.w * k, sp.w * k);
}

// ---------- 2040s outlook: rescore the shortlist on a CMIP6 projection ----------
async function futureOutlook(ctl) {
  try {
    const c = current.center;
    const url = `https://climate-api.open-meteo.com/v1/climate?latitude=${c.lat.toFixed(4)}&longitude=${c.lng.toFixed(4)}` +
      `&start_date=2040-01-01&end_date=2049-12-31&models=MRI_AGCM3_2_S&daily=temperature_2m_mean,temperature_2m_min,precipitation_sum`;
    const j = await (await fetch(url, { signal: ctl.signal })).json();
    if (!j.daily?.time?.length || ctl.signal.aborted) return;
    const agg = aggregateClimate(j.daily);
    const fsite = { ...agg, ph: current.site.ph, lat: c.lat };
    for (const s of current.scored) {
      s.f45 = scoreSpecies(s.sp, fsite).score;
      updateF45(s);
    }
  } catch { /* the projection is an enhancement; fail silent */ }
}
function f45Text(s) {
  if (s.f45 == null) return "&hellip;";
  const d = Math.round((s.f45 - s.score) * 100);
  return `${Math.round(s.f45 * 100)}% <span class="d45">(${d >= 0 ? "+" : ""}${d})</span>`;
}
function updateF45(s) {
  const badge = content.querySelector(`[data-f45="${s.sp.id}"]`);
  if (badge) badge.hidden = !(s.score > 0.4 && s.f45 != null && s.f45 <= 0.4);
  const stat = content.querySelector(`[data-f45stat="${s.sp.id}"]`);
  if (stat) stat.innerHTML = f45Text(s);
}

// ---------- species photos (iNaturalist default taxon photo) ----------
const photoQueue = [];
let photoActive = 0;
function inatPhoto(s) {
  if (s.photo !== undefined) return Promise.resolve(s.photo);
  const key = `inat:${s.sp.sci}`;
  const cached = localStorage.getItem(key);
  if (cached) { s.photo = cached === "x" ? null : JSON.parse(cached); return Promise.resolve(s.photo); }
  return new Promise(res => { photoQueue.push({ s, key, res }); pumpPhotos(); });
}
async function pumpPhotos() {
  if (photoActive >= 4 || !photoQueue.length) return;
  photoActive++;
  const { s, key, res } = photoQueue.shift();
  try {
    const j = await (await fetch(`https://api.inaturalist.org/v1/taxa?q=${encodeURIComponent(s.sp.sci)}&limit=1`)).json();
    const p = j.results?.[0]?.default_photo;
    s.photo = p?.square_url ? { sq: p.square_url, md: p.medium_url, attr: p.attribution ?? "" } : null;
    localStorage.setItem(key, s.photo ? JSON.stringify(s.photo) : "x");
  } catch { s.photo = null; } // transient failure: placeholder until next reload
  res(s.photo);
  photoActive--;
  pumpPhotos();
}
function fillPhoto(s) {
  inatPhoto(s).then(p => {
    if (!p) return;
    const t = content.querySelector(`[data-thumb="${s.sp.id}"]`);
    if (t) t.style.backgroundImage = `url("${p.sq}")`;
    const h = content.querySelector(`[data-hero="${s.sp.id}"]`);
    if (h) { h.style.backgroundImage = `url("${p.md}")`; h.hidden = false; h.title = `${p.attr} · iNaturalist`; }
  });
}

// ---------- GBIF evidence layer ----------
async function gbifEvidence(top, bounds, signal) {
  const keys = await Promise.all(top.map(async s => {
    const cacheKey = `gbifk:${s.sp.sci}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached !== null) return cached === "x" ? null : +cached;
    try {
      const j = await (await fetch(`https://api.gbif.org/v1/species/match?name=${encodeURIComponent(s.sp.sci)}`, { signal })).json();
      const ok = j.rank === "SPECIES" && (j.matchType === "EXACT" || (j.matchType === "FUZZY" && j.confidence >= 95));
      localStorage.setItem(cacheKey, ok ? String(j.usageKey) : "x");
      return ok ? j.usageKey : null;
    } catch { return "ERR"; } // transport failure, not a taxonomy verdict
  }));
  if (signal.aborted) return;

  const valid = top.map((s, i) => ({ s, key: keys[i] }));
  valid.filter(v => v.key === null || v.key === "ERR").forEach(v => { v.s.gbif = v.key === "ERR" ? "ERR" : null; updateEvidence(v.s); });
  const withKey = valid.filter(v => v.key !== null && v.key !== "ERR");
  if (!withKey.length) return;

  const pad = 0.5;
  const url = `https://api.gbif.org/v1/occurrence/search?limit=0&facet=taxonKey&facetLimit=200` +
    `&decimalLatitude=${(bounds.getSouth() - pad).toFixed(3)},${(bounds.getNorth() + pad).toFixed(3)}` +
    `&decimalLongitude=${(bounds.getWest() - pad).toFixed(3)},${(bounds.getEast() + pad).toFixed(3)}` +
    withKey.map(v => `&taxonKey=${v.key}`).join("");
  try {
    const j = await (await fetch(url, { signal })).json();
    const counts = Object.fromEntries((j.facets?.[0]?.counts ?? []).map(c => [c.name, c.count]));
    for (const v of withKey) {
      v.s.gbif = { key: v.key, count: counts[String(v.key)] ?? 0 };
      updateEvidence(v.s);
    }
  } catch {
    if (signal.aborted) return;
    for (const v of withKey) { v.s.gbif = "ERR"; updateEvidence(v.s); }
  }
}

function updateEvidence(s) {
  const dot = content.querySelector(`[data-nearby="${s.sp.id}"]`);
  if (dot) dot.hidden = !(s.gbif?.count > 0);
}

// ---------- deep link (#p=lat,lng;lat,lng;... or legacy #a=s,w,n,e) ----------
async function restoreFromHash() {
  let pts = null, expand = false;
  const a = location.hash.match(/^#a=(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)(;[xs])?$/);
  const p = location.hash.match(/^#p=((?:-?[\d.]+,-?[\d.]+;?)+?)(;[xs])?$/);
  if (a) {
    const [s, w, n, e] = a.slice(1, 5).map(Number);
    pts = [[s, w], [s, e], [n, e], [n, w]].map(q => L.latLng(...q));
    expand = a[5];
  } else if (p) {
    pts = p[1].split(";").filter(Boolean).map(pair => L.latLng(...pair.split(",").map(Number)));
    expand = p[2];
    if (pts.length < 3) return;
  } else return;
  const key = JSON.stringify(pts.map(p => [+p.lat.toFixed(5), +p.lng.toFixed(5)]));
  const existing = shapes.find(s => JSON.stringify(s._pts.map(p => [+p.lat.toFixed(5), +p.lng.toFixed(5)])) === key);
  if (existing) setActive(existing);
  else setShape(pts);
  map.fitBounds(L.latLngBounds(pts).pad(2));
  await speciesReady;
  await analyze(pts);
  if (expand) content.querySelector("[data-toggle]")?.click(); // ;x = expand first row (testing)
  if (expand === ";s" && SIM) { // ;s = preview a mature stand (testing)
    SIM.year = Math.min(25, +SIM.ctl.querySelector("input").max);
    SIM.ctl.querySelector("input").value = SIM.year;
    drawSim();
  }
}
// ---------- plantable-land radar (OSM Overpass) ----------
let radarLayer = null;
async function radarScan() {
  const btn = $("#radar-btn");
  if (radarLayer) { radarLayer.remove(); radarLayer = null; btn.classList.remove("armed"); return; }
  if (map.getZoom() < 13) { alert(tr("Zoom in to city scale to scan for plantable land.")); return; }
  btn.classList.add("armed");
  const b = map.getBounds();
  const bbox = `${b.getSouth()},${b.getWest()},${b.getNorth()},${b.getEast()}`;
  const q = `[out:json][timeout:25];(way["landuse"~"^(brownfield|greenfield|meadow|grass|village_green|allotments)$"](${bbox});way["abandoned:landuse"](${bbox}););out geom 200;`;
  try {
    const r = await fetch("https://overpass-api.de/api/interpreter", {
      method: "POST",
      body: "data=" + encodeURIComponent(q),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const j = await r.json();
    const cands = (j.elements ?? []).filter(e => e.type === "way" && e.geometry?.length >= 4)
      .map(e => ({ tag: e.tags?.landuse ?? e.tags?.["abandoned:landuse"] ?? "?", pts: e.geometry.map(g => [g.lat, g.lon]) }));
    if (!cands.length) {
      alert(tr("Nothing promising in this view. Try another neighborhood."));
      btn.classList.remove("armed");
      return;
    }
    radarLayer = L.layerGroup(cands.map(cd => {
      const poly = L.polygon(cd.pts, { color: "#d7a463", weight: 1.2, dashArray: "4 4", fillOpacity: 0.06 });
      poly.bindTooltip(`${cd.tag} &middot; ${tr("click to analyze")}`, { sticky: true });
      poly.on("click", () => {
        if (armed) return;
        const pts = cd.pts.map(([la, ln]) => L.latLng(la, ln));
        setShape(pts);
        analyze(pts);
      });
      return poly;
    })).addTo(map);
  } catch {
    alert(tr("The land scan service is busy; try again in a minute."));
    btn.classList.remove("armed");
  }
}

// ---------- geometry import/export ----------
async function importGeometryFile(file) {
  try {
    const name = file.name.toLowerCase();
    let polys;
    if (name.endsWith(".zip")) polys = await shpZipToPolys(await file.arrayBuffer());
    else if (name.endsWith(".kml")) polys = kmlToPolys(await file.text());
    else polys = geojsonToPolys(JSON.parse(await file.text()));
    polys = (polys ?? []).filter(r => r.length >= 3 && r.every(([la, ln]) => Math.abs(la) <= 90 && Math.abs(ln) <= 180)).slice(0, 50);
    if (!polys.length) { alert(tr("No polygons found in the file.")); return; }
    let last = null;
    for (const ring of polys) {
      setShape(ring.map(([la, ln]) => L.latLng(la, ln)));
      last = shape;
    }
    map.fitBounds(L.latLngBounds(polys.flat()).pad(0.15));
    await speciesReady;
    analyze(last._pts);
  } catch (err) {
    alert(`${tr("Could not read the file.")} (${err.message})`);
  }
}
function geojsonToPolys(j) {
  const out = [];
  const addGeom = g => {
    if (!g) return;
    if (g.type === "Polygon") out.push(g.coordinates[0].map(([x, y]) => [y, x]));
    if (g.type === "MultiPolygon") g.coordinates.forEach(p => out.push(p[0].map(([x, y]) => [y, x])));
    if (g.type === "GeometryCollection") (g.geometries ?? []).forEach(addGeom);
  };
  if (j.type === "FeatureCollection") (j.features ?? []).forEach(f => addGeom(f.geometry));
  else if (j.type === "Feature") addGeom(j.geometry);
  else addGeom(j);
  return out;
}
function kmlToPolys(text) {
  const doc = new DOMParser().parseFromString(text, "text/xml");
  return [...doc.getElementsByTagName("Polygon")].map(p => {
    const ring = p.getElementsByTagName("outerBoundaryIs")[0] ?? p;
    const coords = ring.getElementsByTagName("coordinates")[0]?.textContent.trim() ?? "";
    return coords.split(/\s+/).map(t => t.split(",")).filter(c => c.length >= 2).map(([x, y]) => [+y, +x]);
  });
}
async function shpZipToPolys(buf) {
  const files = await unzipStore(buf);
  const names = Object.keys(files);
  const shpName = names.find(n => n.toLowerCase().endsWith(".shp"));
  if (!shpName) throw new Error(".shp");
  const prjName = names.find(n => n.toLowerCase().endsWith(".prj"));
  if (prjName && !/WGS[_ ]?1984|4326/i.test(new TextDecoder().decode(files[prjName])))
    throw new Error(tr("The shapefile must use WGS84 geographic coordinates (like SARE requires)."));
  return parseShp(files[shpName]);
}
// minimal zip reader: stored + deflate entries
async function unzipStore(buf) {
  const dv = new DataView(buf);
  let eocd = -1;
  for (let i = buf.byteLength - 22; i >= Math.max(0, buf.byteLength - 65558); i--) {
    if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("zip");
  const count = dv.getUint16(eocd + 10, true);
  let off = dv.getUint32(eocd + 16, true);
  const out = {};
  for (let k = 0; k < count; k++) {
    if (dv.getUint32(off, true) !== 0x02014b50) break;
    const method = dv.getUint16(off + 10, true);
    const csize = dv.getUint32(off + 20, true);
    const nlen = dv.getUint16(off + 28, true), elen = dv.getUint16(off + 30, true), clen = dv.getUint16(off + 32, true);
    const lho = dv.getUint32(off + 42, true);
    const name = new TextDecoder().decode(new Uint8Array(buf, off + 46, nlen));
    const lnlen = dv.getUint16(lho + 26, true), lelen = dv.getUint16(lho + 28, true);
    const raw = new Uint8Array(buf, lho + 30 + lnlen + lelen, csize);
    if (method === 0) out[name] = raw.slice();
    else if (method === 8) out[name] = new Uint8Array(
      await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).arrayBuffer());
    off += 46 + nlen + elen + clen;
  }
  return out;
}
function parseShp(u8) {
  const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
  if (dv.getInt32(0) !== 9994) throw new Error("shp");
  const out = [];
  let pos = 100;
  while (pos + 12 <= u8.byteLength) {
    const clen = dv.getInt32(pos + 4) * 2;
    const type = dv.getInt32(pos + 8, true);
    if (type === 5 || type === 15 || type === 25) { // Polygon, PolygonZ, PolygonM
      const numParts = dv.getInt32(pos + 8 + 36, true);
      const numPoints = dv.getInt32(pos + 8 + 40, true);
      const partsOff = pos + 8 + 44;
      const ptsOff = partsOff + numParts * 4;
      const parts = [];
      for (let i = 0; i < numParts; i++) parts.push(dv.getInt32(partsOff + i * 4, true));
      parts.push(numPoints);
      // first ring of each record; interior rings (holes) are skipped
      const ring = [];
      for (let j = parts[0]; j < parts[1]; j++) {
        ring.push([dv.getFloat64(ptsOff + j * 16 + 8, true), dv.getFloat64(ptsOff + j * 16, true)]);
      }
      out.push(ring);
    }
    pos += 8 + clen;
  }
  return out;
}

// ---------- export: zipped WGS84 shapefile of the active area (SARE-shaped) ----------
function downloadBlob(name, blob) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
const WGS84_PRJ = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]';
function shpExport() {
  if (!shape) return;
  let ring = shape._pts.map(p => [p.lng, p.lat]);
  if (ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1]) ring = [...ring, [...ring[0]]];
  let s = 0; // shapefile outer rings are clockwise
  for (let i = 0; i < ring.length - 1; i++) s += (ring[i + 1][0] - ring[i][0]) * (ring[i + 1][1] + ring[i][1]);
  if (s < 0) ring.reverse();
  const xs = ring.map(p => p[0]), ys = ring.map(p => p[1]);
  const box = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
  const contentLen = 44 + 4 + ring.length * 16; // bytes of the polygon record content
  const shp = new DataView(new ArrayBuffer(100 + 8 + contentLen));
  const shpHeader = (dv, fileBytes) => {
    dv.setInt32(0, 9994);
    dv.setInt32(24, fileBytes / 2);
    dv.setInt32(28, 1000, true);
    dv.setInt32(32, 5, true);
    dv.setFloat64(36, box[0], true); dv.setFloat64(44, box[1], true);
    dv.setFloat64(52, box[2], true); dv.setFloat64(60, box[3], true);
  };
  shpHeader(shp, shp.buffer.byteLength);
  shp.setInt32(100, 1); shp.setInt32(104, contentLen / 2);
  shp.setInt32(108, 5, true);
  shp.setFloat64(112, box[0], true); shp.setFloat64(120, box[1], true);
  shp.setFloat64(128, box[2], true); shp.setFloat64(136, box[3], true);
  shp.setInt32(144, 1, true); shp.setInt32(148, ring.length, true);
  shp.setInt32(152, 0, true);
  ring.forEach(([x, y], i) => {
    shp.setFloat64(156 + i * 16, x, true);
    shp.setFloat64(156 + i * 16 + 8, y, true);
  });
  const shx = new DataView(new ArrayBuffer(100 + 8));
  shpHeader(shx, shx.buffer.byteLength);
  shx.setInt32(100, 50); shx.setInt32(104, contentLen / 2);
  // minimal dbf: one N field "ID", one record
  const dbf = new DataView(new ArrayBuffer(32 + 32 + 1 + 11 + 1));
  dbf.setUint8(0, 3); dbf.setUint8(1, 95); dbf.setUint8(2, 1); dbf.setUint8(3, 1);
  dbf.setUint32(4, 1, true);
  dbf.setUint16(8, 65, true); dbf.setUint16(10, 11, true);
  const idName = "ID";
  for (let i = 0; i < idName.length; i++) dbf.setUint8(32 + i, idName.charCodeAt(i));
  dbf.setUint8(32 + 11, 78); dbf.setUint8(32 + 16, 10);
  dbf.setUint8(64, 0x0d);
  const rec = "          1";
  for (let i = 0; i < 11; i++) dbf.setUint8(65 + i, rec.charCodeAt(i) || 32);
  dbf.setUint8(65 + 11, 0x1a);
  const base = `area-canopy-${current ? current.center.lat.toFixed(3) + "_" + current.center.lng.toFixed(3) : "poligono"}`;
  downloadBlob(`${base}.zip`, zipStore({
    [`${base}.shp`]: new Uint8Array(shp.buffer),
    [`${base}.shx`]: new Uint8Array(shx.buffer),
    [`${base}.dbf`]: new Uint8Array(dbf.buffer),
    [`${base}.prj`]: new TextEncoder().encode(WGS84_PRJ),
  }));
}
// zip writer, stored entries only
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(u8) {
  let c = 0xffffffff;
  for (let i = 0; i < u8.length; i++) c = CRC_TABLE[(c ^ u8[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function zipStore(files) {
  const enc = new TextEncoder();
  const parts = [], central = [];
  let offset = 0;
  for (const [name, data] of Object.entries(files)) {
    const n = enc.encode(name), crc = crc32(data);
    const local = new DataView(new ArrayBuffer(30));
    local.setUint32(0, 0x04034b50, true); local.setUint16(4, 20, true);
    local.setUint32(14, crc, true);
    local.setUint32(18, data.length, true); local.setUint32(22, data.length, true);
    local.setUint16(26, n.length, true);
    parts.push(new Uint8Array(local.buffer), n, data);
    const cd = new DataView(new ArrayBuffer(46));
    cd.setUint32(0, 0x02014b50, true); cd.setUint16(4, 20, true); cd.setUint16(6, 20, true);
    cd.setUint32(16, crc, true);
    cd.setUint32(20, data.length, true); cd.setUint32(24, data.length, true);
    cd.setUint16(28, n.length, true);
    cd.setUint32(42, offset, true);
    central.push(new Uint8Array(cd.buffer), n);
    offset += 30 + n.length + data.length;
  }
  const cdStart = offset;
  let cdLen = 0;
  central.forEach(u => cdLen += u.length);
  const eocd = new DataView(new ArrayBuffer(22));
  eocd.setUint32(0, 0x06054b50, true);
  eocd.setUint16(8, Object.keys(files).length, true); eocd.setUint16(10, Object.keys(files).length, true);
  eocd.setUint32(12, cdLen, true); eocd.setUint32(16, cdStart, true);
  return new Blob([...parts, ...central, new Uint8Array(eocd.buffer)], { type: "application/zip" });
}

// ---------- export: full factor matrix as CSV ----------
function csvExport() {
  if (!current) return;
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const head = ["scientific_name", "common_name", "family", "score", "fit", "score_2040s",
    "temp_factor", "rain_factor", "ph_factor", "photo_factor", "frost_factor", "chill_factor",
    "native_here", "growth_class", "uses"];
  const rows = current.scored.map(s => [
    s.sp.sci, s.sp.common, s.sp.family,
    s.score.toFixed(3), s.fit.toFixed(3), s.f45 != null ? s.f45.toFixed(3) : "",
    ...[s.factors.temp, s.factors.rain, s.factors.ph, s.factors.photo, s.factors.frost, s.factors.chill]
      .map(v => v == null ? "" : (+v).toFixed(3)),
    nativeHere(s.sp) ?? "", s.sp.gclass, s.sp.uses.join("|"),
  ].map(esc).join(","));
  const meta = `# Canopy ${new Date().toISOString().slice(0, 10)} · ${current.center.lat.toFixed(4)},${current.center.lng.toFixed(4)} · ${current.ha.toFixed(1)} ha\n`;
  downloadBlob(`canopy-especies-${current.center.lat.toFixed(3)}_${current.center.lng.toFixed(3)}.csv`,
    new Blob([meta + head.join(",") + "\n" + rows.join("\n")], { type: "text/csv;charset=utf-8" }));
}

// localize the static chrome
document.title = tr("Replantio · replanting intelligence");
geoInput.placeholder = tr("Search a city or place");
$("#draw-label").textContent = tr("Draw area");
hint.innerHTML = tr("Click to drop points &middot; right-click, double-click or click the first point to close &middot; Esc cancels");
$("#import-btn").title = tr("Import area (GeoJSON, KML, zipped shapefile)");
$("#radar-btn").title = tr("Find plantable land in this view");
$("#radar-btn").addEventListener("click", radarScan);
const syncRadarBtn = () => { $("#radar-btn").hidden = map.getZoom() < 13 && !radarLayer; };
map.on("zoomend", syncRadarBtn);
syncRadarBtn();

// go-to-my-location control, stacked with the zoom buttons
const locCtl = L.control({ position: "bottomleft" });
locCtl.onAdd = () => {
  const b = L.DomUtil.create("button", "locate-btn");
  b.type = "button";
  b.title = tr("Go to my location");
  b.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><path d="M12 2v3M22 12h-3M12 22v-3M2 12h3"/></svg>`;
  L.DomEvent.on(b, "click", e => {
    L.DomEvent.stop(e);
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      p => map.flyTo([p.coords.latitude, p.coords.longitude], 15, { duration: 1.4 }),
      () => alert(tr("Could not get your location.")),
      { maximumAge: 60000, timeout: 10000 });
  });
  return b;
};
locCtl.addTo(map);
const importInput = $("#import-input");
$("#import-btn").addEventListener("click", () => importInput.click());
importInput.addEventListener("change", () => { if (importInput.files[0]) importGeometryFile(importInput.files[0]); importInput.value = ""; });
map.getContainer().addEventListener("dragover", e => e.preventDefault());
map.getContainer().addEventListener("drop", e => {
  e.preventDefault();
  if (e.dataTransfer?.files?.[0]) importGeometryFile(e.dataTransfer.files[0]);
});

// brand popover: what this is, who made it, where the code lives
const brandEl = document.querySelector(".brand");
const aboutEl = $("#about");
aboutEl.innerHTML = `
  <p>${tr("Draw an area anywhere on Earth: Replantio shows which species would thrive there, how they grow, the carbon they store, and what restoration costs. Open data, open model.")}</p>
  <p class="about-links">${tr("created by")} <a href="https://guidavid.com" target="_blank" rel="noopener">guidavid.com</a>
  &middot; <a href="https://github.com/gdavidss/replantio" target="_blank" rel="noopener">${tr("Open source on GitHub")}</a></p>`;
brandEl.addEventListener("click", () => { aboutEl.hidden = !aboutEl.hidden; });
document.addEventListener("click", e => {
  if (!aboutEl.hidden && !e.target.closest(".brand") && !e.target.closest("#about")) aboutEl.hidden = true;
});

const langBtn = $("#lang-btn");
langBtn.value = LANG;
langBtn.addEventListener("change", () => {
  localStorage.setItem("lang", langBtn.value);
  location.reload(); // the analysis is in the hash, so it survives the reload
});

restoreAreas();
restoreFromHash();
if (!location.hash && !shapes.length && navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    p => map.setView([p.coords.latitude, p.coords.longitude], 13),
    () => {}, { maximumAge: 600000, timeout: 8000 });
}

const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
window.canopy = { map, analyze, get current() { return current; } }; // test hook
