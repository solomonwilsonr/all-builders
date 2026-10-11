// Balram OCP: growth beyond the 2019 footprint (paste the whole file into the Earth Engine Code Editor)

// ===== 1. Baseline footprint =====
// Maus et al. v2 polygon fid 44352 (2019 mining footprint, merged Talcher complex)
var maus = ee.Geometry.Polygon([[[85.21680,20.96280],[85.21340,20.96410],[85.20740,20.96530],[85.20050,20.96930],[85.19840,20.96730],[85.19550,20.96990],[85.19120,20.96790],[85.19040,20.96720],[85.18930,20.96740],[85.18710,20.96530],[85.18270,20.96520],[85.18250,20.96520],[85.18190,20.96610],[85.17785,20.96717],[85.17819,20.96761],[85.17915,20.96966],[85.17801,20.97286],[85.17578,20.97563],[85.17337,20.97810],[85.17186,20.97901],[85.16836,20.97891],[85.16550,20.97910],[85.16500,20.98020],[85.16310,20.98570],[85.16190,20.98670],[85.16180,20.98710],[85.16140,20.98710],[85.16080,20.98760],[85.15380,20.98650],[85.14930,20.98570],[85.14870,20.98570],[85.14870,20.98560],[85.14760,20.98540],[85.14780,20.98320],[85.14655,20.98244],[85.14341,20.98286],[85.13787,20.98136],[85.13305,20.97967],[85.13058,20.97816],[85.12810,20.97557],[85.12527,20.97201],[85.12341,20.96725],[85.11790,20.97250],[85.11570,20.97190],[85.11420,20.96776],[85.11394,20.96798],[85.10984,20.96840],[85.10773,20.96846],[85.10587,20.96780],[85.10472,20.96629],[85.10448,20.96490],[85.10484,20.96273],[85.10693,20.96084],[85.10800,20.95670],[85.10830,20.95650],[85.10810,20.95650],[85.10800,20.95650],[85.10760,20.95640],[85.10610,20.95330],[85.10430,20.95190],[85.10100,20.95360],[85.10100,20.95730],[85.09910,20.96040],[85.09490,20.96280],[85.09244,20.96330],[85.09194,20.96526],[85.09116,20.96737],[85.08899,20.96888],[85.08652,20.96906],[85.08387,20.96924],[85.08061,20.96960],[85.07892,20.96822],[85.07929,20.96575],[85.08052,20.96484],[85.08140,20.96160],[85.08050,20.95940],[85.06510,20.95880],[85.06550,20.95860],[85.06320,20.95770],[85.06150,20.95550],[85.06100,20.95050],[85.06270,20.94720],[85.06490,20.94660],[85.06490,20.94600],[85.06890,20.94400],[85.07390,20.94320],[85.07650,20.94230],[85.07710,20.94160],[85.08100,20.94290],[85.08150,20.94280],[85.08280,20.94350],[85.08720,20.94490],[85.09000,20.94620],[85.09350,20.94840],[85.09870,20.95080],[85.09950,20.94990],[85.10160,20.94820],[85.10680,20.94550],[85.11170,20.94460],[85.11450,20.94350],[85.11610,20.94120],[85.11750,20.93980],[85.12010,20.93820],[85.12250,20.93600],[85.12690,20.93530],[85.12080,20.92870],[85.12500,20.92520],[85.12630,20.92540],[85.12850,20.92550],[85.12830,20.92560],[85.14150,20.92740],[85.15250,20.92830],[85.15840,20.93370],[85.16160,20.93930],[85.16250,20.94360],[85.16240,20.94690],[85.15780,20.95130],[85.15725,20.95246],[85.15993,20.95677],[85.16192,20.95755],[85.16396,20.95815],[85.16432,20.95823],[85.16420,20.95780],[85.16710,20.95590],[85.17200,20.95650],[85.17800,20.95530],[85.18110,20.95150],[85.18880,20.95110],[85.19600,20.95250],[85.20510,20.95510],[85.20970,20.95640],[85.21470,20.95680],[85.21610,20.95780],[85.21580,20.96120],[85.21680,20.96280]]]);

// Bounding box from the 2025 EC for Balram
var ecBox = ee.Geometry.Rectangle([85.0434, 20.9316, 85.1060, 20.9853]);

// Balram = merged mining polygon inside the EC box
var balram = maus.intersection(ecBox, 1);

Map.setOptions('SATELLITE');
Map.centerObject(ecBox, 13);
Map.addLayer(maus, {color: 'orange'}, 'Maus merged complex (2019)', true, 0.3);
Map.addLayer(ecBox, {color: 'white'}, 'EC bounding box', true, 0.1);
Map.addLayer(balram, {color: 'red'}, 'Balram (Maus within EC box)', true, 0.5);
print('Balram part area (ha):', balram.area().divide(10000));

// ===== 2. Growth beyond the 2019 footprint =====
// Zone to test: inside the EC box but OUTSIDE Balram's 2019 outline
var growthZone = ecBox.difference(balram, 1);
Map.addLayer(growthZone, {color: 'cyan'}, 'growth zone', false, 0.15);

// Bare ground (Dynamic World class 7) in each dry season, Feb-Apr
function bareDW(y) {
  return ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
    .filterBounds(ecBox)
    .filterDate(y + '-02-01', y + '-04-30')
    .select('label').mode().eq(7);
}
var bare = {};
for (var y = 2019; y <= 2025; y++) { bare[y] = bareDW(y); }

// Ignore anything already bare in 2019 (old mine, roads, fallow fields)
var notBare2019 = bare[2019].not();

// "Persistently bare from year Y to 2025": filters out crop and seasonal flicker
var persist = {};
persist[2025] = bare[2025].and(notBare2019);
for (var y = 2024; y >= 2020; y--) {
  persist[y] = bare[y].and(persist[y + 1]);
}

// Onset year = first year a pixel became (and stayed) bare
var onset = {};
onset[2020] = persist[2020];
for (var y = 2021; y <= 2025; y++) {
  onset[y] = persist[y].and(persist[y - 1].not());
}

// Hectares of new bare ground per onset year, inside the growth zone
var rows = [];
for (var y = 2020; y <= 2025; y++) {
  var ha = onset[y].multiply(ee.Image.pixelArea()).divide(10000)
    .reduceRegion({reducer: ee.Reducer.sum(), geometry: growthZone,
                   scale: 10, maxPixels: 1e9}).get('label');
  rows.push(ee.Feature(null, {year: String(y), new_ha: ha}));
}
var growthFc = ee.FeatureCollection(rows);
print('New bare ground by onset year (ha):', growthFc.aggregate_array('new_ha'));
print(ui.Chart.feature.byFeature(growthFc, 'year', 'new_ha')
  .setChartType('ColumnChart')
  .setOptions({title: 'New persistent bare ground outside the 2019 footprint (ha)',
               vAxis: {title: 'ha'}, legend: {position: 'none'}}));

// Map: colour by year the ground became bare
var onsetYear = ee.Image(0);
for (var y = 2020; y <= 2025; y++) {
  onsetYear = onsetYear.add(onset[y].multiply(y));
}
Map.addLayer(onsetYear.updateMask(onsetYear.gt(0)).clip(growthZone),
  {min: 2020, max: 2025,
   palette: ['yellow', 'orange', 'red', 'purple', 'blue', 'cyan']},
  'new ground by onset year (2020 yellow ... 2025 cyan)');
