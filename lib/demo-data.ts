export const monthlyPerformance = [
  { month: 'Jan', revenue: 418, forecast: 410, lower: 382, upper: 438, margin: 35.1 },
  { month: 'Feb', revenue: 452, forecast: 438, lower: 409, upper: 467, margin: 35.8 },
  { month: 'Mar', revenue: 447, forecast: 461, lower: 431, upper: 491, margin: 36.2 },
  { month: 'Apr', revenue: 496, forecast: 482, lower: 451, upper: 513, margin: 36.9 },
  { month: 'May', revenue: 521, forecast: 513, lower: 481, upper: 545, margin: 37.4 },
  { month: 'Jun', revenue: 548, forecast: 541, lower: 508, upper: 574, margin: 37.8 },
  { month: 'Jul', revenue: 579, forecast: 566, lower: 531, upper: 601, margin: 38.2 },
  { month: 'Aug', revenue: 604, forecast: 596, lower: 560, upper: 632, margin: 38.7 },
  { month: 'Sep', revenue: null, forecast: 628, lower: 586, upper: 670, margin: 39.0 },
  { month: 'Oct', revenue: null, forecast: 655, lower: 608, upper: 702, margin: 39.3 },
  { month: 'Nov', revenue: null, forecast: 681, lower: 628, upper: 734, margin: 39.6 },
];

export const regionPerformance = [
  { region: 'Central', actual: 1240, target: 1120 },
  { region: 'East', actual: 1085, target: 1040 },
  { region: 'West', actual: 1028, target: 1100 },
  { region: 'South', actual: 967, target: 920 },
];

export const riskAlerts = [
  { severity: 'Critical', signal: 'Stockout risk', item: 'Alpine Field Kit', region: 'Central', exposure: 46000, confidence: 94, action: 'Transfer 320 units from West before 8 Sep.' },
  { severity: 'High', signal: 'Supplier delay', item: 'Apex Sensor', region: 'East', exposure: 31800, confidence: 88, action: 'Move 40% of September volume to supplier B.' },
  { severity: 'High', signal: 'Margin erosion', item: 'Transit Pro Case', region: 'South', exposure: 22400, confidence: 91, action: 'Pause expedited freight and restore standard routing.' },
  { severity: 'Medium', signal: 'Slow-moving stock', item: 'Base Camp Hub', region: 'West', exposure: 17600, confidence: 82, action: 'Bundle 180 units with the Alpine Field Kit.' },
  { severity: 'Low', signal: 'Demand variance', item: 'Summit Battery', region: 'East', exposure: 9400, confidence: 76, action: 'Review forecast after the next weekly refresh.' },
];

export const riskMix = [
  { name: 'Inventory', value: 46, fill: '#e58f5f' },
  { name: 'Supplier', value: 28, fill: '#e8be72' },
  { name: 'Margin', value: 17, fill: '#67bca8' },
  { name: 'Demand', value: 9, fill: '#6c8fa0' },
];

export const pipelineStages = [
  { name: 'Ingest', detail: '3 source files · CSV', rows: '18,420', status: 'Complete' },
  { name: 'Validate', detail: 'Schema + quality rules', rows: '18,274', status: 'Complete' },
  { name: 'Transform', detail: 'SQL business models', rows: '4 marts', status: 'Complete' },
  { name: 'Forecast', detail: 'Linear trend + intervals', rows: '90 days', status: 'Complete' },
  { name: 'Publish', detail: 'Dashboard-ready JSON', rows: '42 KB', status: 'Complete' },
];

export const qualityChecks = [
  { label: 'Required fields present', value: 100, result: 'Passed' },
  { label: 'Valid product references', value: 99.8, result: 'Passed' },
  { label: 'Duplicate transaction check', value: 99.3, result: 'Passed' },
  { label: 'Freshness under 24 hours', value: 100, result: 'Passed' },
];
