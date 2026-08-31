'use client';

import { useMemo, useRef, useState } from 'react';
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Bell, Boxes, Check,
  ChevronRight, CircleAlert, CircleCheck, CloudUpload, Download,
  FileCheck2, Gauge, LayoutDashboard, PackageCheck, RefreshCw, RotateCcw,
  Search, ShieldAlert, SlidersHorizontal, Sparkles, Target, TrendingUp,
} from 'lucide-react';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, Line, LineChart,
  Pie, PieChart, ReferenceLine, XAxis, YAxis,
} from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartConfig, ChartContainer, ChartLegendContent, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Progress } from '@/components/ui/progress';
import { monthlyPerformance, pipelineStages, qualityChecks, regionPerformance, riskAlerts, riskMix } from '@/lib/demo-data';

type View = 'overview' | 'forecast' | 'risk' | 'scenario' | 'pipeline';

const navItems: Array<{ id: View; label: string; icon: typeof LayoutDashboard; badge?: string }> = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'forecast', label: 'Forecast lab', icon: TrendingUp },
  { id: 'risk', label: 'Risk monitor', icon: ShieldAlert, badge: '4' },
  { id: 'scenario', label: 'Scenario planner', icon: SlidersHorizontal },
  { id: 'pipeline', label: 'Data pipeline', icon: Boxes },
];

const overviewChartConfig = {
  revenue: { label: 'Actual revenue', color: '#79d8bd' },
  forecast: { label: 'Forecast', color: '#e5aa66' },
} satisfies ChartConfig;

const forecastChartConfig = {
  revenue: { label: 'Actual revenue', color: '#2c7668' },
  forecast: { label: 'Forecast', color: '#e29a58' },
  upper: { label: 'Upper bound', color: '#e8c8a7' },
  lower: { label: 'Lower bound', color: '#e8c8a7' },
} satisfies ChartConfig;

const regionChartConfig = {
  actual: { label: 'Actual', color: '#2c7668' },
  target: { label: 'Target', color: '#c5d3cf' },
} satisfies ChartConfig;

const riskChartConfig = Object.fromEntries(riskMix.map((item) => [item.name, { label: item.name, color: item.fill }])) satisfies ChartConfig;

function money(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

function SectionHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#2c7668]">{eyebrow}</p><h2 className="text-2xl font-semibold tracking-[-0.03em] md:text-3xl">{title}</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p></div>{action}</div>;
}

function KpiCard({ label, value, change, note, icon: Icon, positive = true }: { label: string; value: string; change: string; note: string; icon: typeof Activity; positive?: boolean }) {
  return <Card className="border-0 bg-card shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardContent className="space-y-4"><div className="flex items-center justify-between"><p className="text-xs font-medium text-muted-foreground">{label}</p><div className="grid size-8 place-items-center rounded-lg bg-[#ecf5f1] text-[#2c7668]"><Icon className="size-4" /></div></div><div><p className="font-mono text-2xl font-semibold tracking-tight">{value}</p><div className="mt-2 flex items-center gap-2 text-xs"><span className={positive ? 'flex items-center gap-1 font-semibold text-[#2f806f]' : 'flex items-center gap-1 font-semibold text-[#c76a3a]'}>{positive ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}{change}</span><span className="text-muted-foreground">{note}</span></div></div></CardContent></Card>;
}

function Overview({ onNavigate }: { onNavigate: (view: View) => void }) {
  return <div className="space-y-6" data-view="overview">
    <SectionHeading eyebrow="Executive pulse · Jan–Aug 2026" title="Turn operating data into decisions before risk becomes cost." description="A single view of revenue, margin, inventory efficiency, and the actions most likely to protect performance." action={<Button onClick={() => onNavigate('risk')} className="h-10 gap-2 bg-[#153f3a] px-4 text-white hover:bg-[#1d514a]">View decision brief <ChevronRight /></Button>} />
    <section aria-label="Key performance indicators" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard label="Net revenue" value="$4.32M" change="+12.4%" note="vs. last period" icon={TrendingUp} />
      <KpiCard label="Gross margin" value="38.7%" change="+2.1 pts" note="ahead of target" icon={Activity} />
      <KpiCard label="Inventory turnover" value="6.8×" change="+0.6×" note="annualized" icon={Boxes} />
      <KpiCard label="At-risk stock" value="$184K" change="-8.3%" note="capital exposed" icon={CircleAlert} positive={false} />
    </section>
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,.75fr)]">
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader className="flex-row items-start justify-between"><div><CardTitle>Revenue trajectory</CardTitle><CardDescription>Actuals and 90-day statistical forecast · USD thousands</CardDescription></div><Badge variant="outline" className="text-[#2c7668]">92% confidence</Badge></CardHeader><CardContent><ChartContainer config={overviewChartConfig} className="h-[310px] w-full aspect-auto"><AreaChart data={monthlyPerformance} margin={{ left: 0, right: 8, top: 12, bottom: 0 }}><defs><linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="var(--color-revenue)" stopOpacity={0.42}/><stop offset="95%" stopColor="var(--color-revenue)" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} strokeDasharray="4 6" /><XAxis dataKey="month" axisLine={false} tickLine={false} tickMargin={12} /><YAxis axisLine={false} tickLine={false} width={38} domain={[350, 740]} /><ChartTooltip content={<ChartTooltipContent indicator="line" />} /><Area dataKey="forecast" type="monotone" fill="transparent" stroke="var(--color-forecast)" strokeWidth={2} strokeDasharray="5 5" /><Area dataKey="revenue" type="monotone" fill="url(#revenueFill)" stroke="var(--color-revenue)" strokeWidth={3} /></AreaChart></ChartContainer></CardContent></Card>
      <Card className="border-0 bg-[#112c2f] text-white shadow-[0_12px_36px_rgb(15_23_42/12%)] ring-0"><CardHeader><div className="mb-3 grid size-10 place-items-center rounded-xl bg-[#79d8bd]/14 text-[#8fe0ca]"><Sparkles className="size-5" /></div><CardTitle className="text-white">Decision brief</CardTitle><CardDescription className="text-white/45">Prioritized from this week’s signals</CardDescription></CardHeader><CardContent className="space-y-4"><div className="rounded-xl border border-white/8 bg-white/5 p-4"><div className="mb-2 flex items-center gap-2 text-xs font-semibold text-[#ffb58d]"><CircleAlert className="size-4" /> Highest impact</div><p className="text-sm leading-6 text-white/85">Rebalance 320 units of Alpine Kit from West to Central before 8 Sep.</p><p className="mt-2 text-xs text-white/40">Projected protection: $46K revenue</p></div><div className="rounded-xl border border-white/8 p-4"><p className="text-sm leading-6 text-white/75">Margin is improving, but expedited freight erased 0.7 points this month.</p></div><Button onClick={() => onNavigate('risk')} variant="ghost" className="w-full justify-between text-[#9ee5d2] hover:bg-white/6 hover:text-white">Open full analysis <ChevronRight /></Button></CardContent></Card>
    </section>
  </div>;
}

function ForecastLab() {
  return <div className="space-y-6" data-view="forecast">
    <SectionHeading eyebrow="Predictive analytics" title="Know what is likely to happen next." description="A transparent 90-day forecast with confidence bands, model accuracy, and the regions driving the result." action={<Button variant="outline" className="gap-2"><Download /> Export forecast</Button>} />
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard label="90-day revenue" value="$1.96M" change="+14.1%" note="projected growth" icon={TrendingUp} />
      <KpiCard label="Forecast accuracy" value="93.2%" change="+1.8 pts" note="vs. last run" icon={Target} />
      <KpiCard label="MAPE" value="6.8%" change="-0.9 pts" note="lower is better" icon={Gauge} />
      <KpiCard label="Revenue at risk" value="$127K" change="-11.4%" note="in confidence range" icon={CircleAlert} positive={false} />
    </section>
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,.85fr)]">
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Revenue forecast with confidence range</CardTitle><CardDescription>The shaded range shows where actual revenue is likely to land.</CardDescription></CardHeader><CardContent><ChartContainer config={forecastChartConfig} className="h-[380px] w-full aspect-auto"><LineChart data={monthlyPerformance} margin={{ left: 8, right: 16, top: 16, bottom: 0 }}><CartesianGrid vertical={false} strokeDasharray="4 6" /><XAxis dataKey="month" axisLine={false} tickLine={false} tickMargin={12} /><YAxis axisLine={false} tickLine={false} width={42} domain={[340, 760]} /><ChartTooltip content={<ChartTooltipContent indicator="line" />} /><ReferenceLine x="Aug" stroke="#9aa8a4" strokeDasharray="4 4" label={{ value: 'Forecast starts', position: 'insideTopRight', fill: '#74817d', fontSize: 11 }} /><Line dataKey="upper" type="monotone" stroke="var(--color-upper)" strokeWidth={1.5} dot={false} strokeDasharray="3 4" /><Line dataKey="lower" type="monotone" stroke="var(--color-lower)" strokeWidth={1.5} dot={false} strokeDasharray="3 4" /><Line dataKey="forecast" type="monotone" stroke="var(--color-forecast)" strokeWidth={3} dot={false} /><Line dataKey="revenue" type="monotone" stroke="var(--color-revenue)" strokeWidth={3} dot={{ r: 3, fill: '#2c7668' }} /></LineChart></ChartContainer></CardContent></Card>
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Regional performance</CardTitle><CardDescription>Year-to-date actual revenue against target.</CardDescription></CardHeader><CardContent><ChartContainer config={regionChartConfig} className="h-[300px] w-full aspect-auto"><BarChart data={regionPerformance} layout="vertical" margin={{ left: 12, right: 16 }}><CartesianGrid horizontal={false} strokeDasharray="4 6" /><XAxis type="number" axisLine={false} tickLine={false} /><YAxis type="category" dataKey="region" axisLine={false} tickLine={false} width={58} /><ChartTooltip content={<ChartTooltipContent />} /><Bar dataKey="target" fill="var(--color-target)" radius={[0, 4, 4, 0]} /><Bar dataKey="actual" fill="var(--color-actual)" radius={[0, 4, 4, 0]} /></BarChart></ChartContainer><div className="mt-4 rounded-xl bg-[#eef6f3] p-4 text-sm leading-6 text-[#285e55]"><strong>What this means:</strong> Central is outperforming plan by 10.7%, while West needs an inventory and pricing review.</div></CardContent></Card>
    </section>
  </div>;
}

function RiskMonitor() {
  return <div className="space-y-6" data-view="risk">
    <SectionHeading eyebrow="Explainable alerts" title="Prioritize risk by business impact, not noise." description="Every alert includes the financial exposure, confidence score, and a plain-English recommended action." action={<Button variant="outline" className="gap-2"><RefreshCw /> Refresh signals</Button>} />
    <section className="grid gap-4 sm:grid-cols-3"><KpiCard label="Open alerts" value="12" change="4 urgent" note="need action" icon={ShieldAlert} positive={false} /><KpiCard label="Total exposure" value="$127K" change="-11.4%" note="week over week" icon={CircleAlert} positive={false} /><KpiCard label="Protected revenue" value="$284K" change="+18.6%" note="from closed actions" icon={CircleCheck} /></section>
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,.6fr)]">
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Priority queue</CardTitle><CardDescription>Ranked by severity, exposure, and model confidence.</CardDescription></CardHeader><CardContent className="overflow-x-auto px-0"><table className="w-full min-w-[800px] text-left text-sm"><thead className="border-y bg-[#f4f8f6] text-[11px] uppercase tracking-wider text-muted-foreground"><tr><th className="px-5 py-3 font-medium">Severity</th><th className="px-3 py-3 font-medium">Signal</th><th className="px-3 py-3 font-medium">Product / region</th><th className="px-3 py-3 font-medium">Exposure</th><th className="px-3 py-3 font-medium">Confidence</th><th className="px-5 py-3 font-medium">Recommended action</th></tr></thead><tbody className="divide-y">{riskAlerts.map((alert) => <tr key={alert.item} className="hover:bg-[#f7faf9]"><td className="px-5 py-4"><Badge className={alert.severity === 'Critical' ? 'border-0 bg-[#ffe8df] text-[#a84724]' : alert.severity === 'High' ? 'border-0 bg-[#fff0dc] text-[#97601c]' : 'border-0 bg-[#edf3f1] text-[#45655e]'}>{alert.severity}</Badge></td><td className="px-3 py-4 font-medium">{alert.signal}</td><td className="px-3 py-4"><p className="font-medium">{alert.item}</p><p className="text-xs text-muted-foreground">{alert.region}</p></td><td className="px-3 py-4 font-mono font-semibold">{money(alert.exposure)}</td><td className="px-3 py-4"><div className="flex items-center gap-2"><Progress value={alert.confidence} className="h-1.5 w-14" /><span className="text-xs">{alert.confidence}%</span></div></td><td className="px-5 py-4 text-xs leading-5 text-muted-foreground">{alert.action}</td></tr>)}</tbody></table></CardContent></Card>
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Exposure by risk type</CardTitle><CardDescription>Share of current financial exposure.</CardDescription></CardHeader><CardContent><ChartContainer config={riskChartConfig} className="mx-auto h-[260px] w-full aspect-auto"><PieChart><ChartTooltip content={<ChartTooltipContent hideLabel />} /><Pie data={riskMix} dataKey="value" nameKey="name" innerRadius={62} outerRadius={92} paddingAngle={3} /><Legend content={<ChartLegendContent nameKey="name" />} /></PieChart></ChartContainer><div className="mt-5 rounded-xl border border-[#e7d3bb] bg-[#fff9ef] p-4"><p className="text-xs font-semibold text-[#8d5c24]">Recommended first move</p><p className="mt-2 text-sm leading-6 text-[#6d5942]">Transfer Alpine Kit inventory. It removes 36% of total exposure with one operational action.</p></div></CardContent></Card>
    </section>
  </div>;
}

function ScenarioPlanner() {
  const [demand, setDemand] = useState(8);
  const [price, setPrice] = useState(2);
  const [cost, setCost] = useState(-1);
  const [inventory, setInventory] = useState(6);
  const result = useMemo(() => {
    const baseRevenue = 6.72;
    const revenue = baseRevenue * (1 + demand / 100) * (1 + price / 100);
    const margin = 38.7 + price * 0.72 - cost * 0.61 - Math.max(0, demand - inventory) * 0.08;
    const workingCapital = 1.24 + inventory * 0.042 + demand * 0.009;
    const service = Math.min(99.4, 92.2 + inventory * 0.78 - Math.max(0, demand - 10) * 0.25);
    return { revenue, margin, workingCapital, service };
  }, [demand, price, cost, inventory]);
  const reset = () => { setDemand(8); setPrice(2); setCost(-1); setInventory(6); };
  const slider = (label: string, value: number, setValue: (value: number) => void, min: number, max: number, suffix: string) => <label className="block rounded-xl border bg-[#fbfcfb] p-4"><div className="mb-4 flex items-center justify-between"><span className="text-sm font-medium">{label}</span><span className="rounded-lg bg-[#e7f3ef] px-2.5 py-1 font-mono text-xs font-semibold text-[#27675b]">{value > 0 ? '+' : ''}{value}{suffix}</span></div><input aria-label={label} className="scenario-slider w-full" type="range" min={min} max={max} value={value} onInput={(event) => setValue(Number(event.currentTarget.value))} /><div className="mt-2 flex justify-between text-[10px] text-muted-foreground"><span>{min}{suffix}</span><span>{max}{suffix}</span></div></label>;
  return <div className="space-y-6" data-view="scenario">
    <SectionHeading eyebrow="What-if analysis" title="Test a decision before committing resources." description="Adjust the business assumptions and see the expected impact on revenue, margin, cash tied up in stock, and service level." action={<Button onClick={reset} variant="outline" className="gap-2"><RotateCcw /> Reset scenario</Button>} />
    <section className="grid gap-6 xl:grid-cols-[minmax(340px,.72fr)_minmax(0,1.28fr)]">
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Assumptions</CardTitle><CardDescription>Move each control to model a plausible operating case.</CardDescription></CardHeader><CardContent className="space-y-3">{slider('Demand growth', demand, setDemand, -10, 25, '%')}{slider('Average price change', price, setPrice, -8, 12, '%')}{slider('Unit cost change', cost, setCost, -8, 12, '%')}{slider('Extra inventory cover', inventory, setInventory, 0, 12, ' wks')}</CardContent></Card>
      <div className="space-y-6"><Card className="border-0 bg-[#112c2f] text-white shadow-[0_12px_36px_rgb(15_23_42/12%)] ring-0"><CardHeader><div className="flex items-center justify-between"><div><CardTitle className="text-white">Scenario outcome</CardTitle><CardDescription className="text-white/45">Compared with the current operating plan</CardDescription></div><Badge className="border-0 bg-[#79d8bd]/14 text-[#9ee5d2]">Live calculation</Badge></div></CardHeader><CardContent><div className="grid gap-4 sm:grid-cols-2"><div className="rounded-xl border border-white/8 bg-white/5 p-5"><p className="text-xs text-white/45">Projected revenue</p><p className="mt-2 font-mono text-3xl font-semibold">${result.revenue.toFixed(2)}M</p><p className="mt-2 text-xs text-[#8fe0ca]">+{((result.revenue / 6.72 - 1) * 100).toFixed(1)}% vs. base</p></div><div className="rounded-xl border border-white/8 bg-white/5 p-5"><p className="text-xs text-white/45">Gross margin</p><p className="mt-2 font-mono text-3xl font-semibold">{result.margin.toFixed(1)}%</p><p className="mt-2 text-xs text-[#8fe0ca]">{result.margin - 38.7 >= 0 ? '+' : ''}{(result.margin - 38.7).toFixed(1)} points</p></div><div className="rounded-xl border border-white/8 bg-white/5 p-5"><p className="text-xs text-white/45">Working capital</p><p className="mt-2 font-mono text-3xl font-semibold">${result.workingCapital.toFixed(2)}M</p><p className="mt-2 text-xs text-[#ffb58d]">Cash tied up in inventory</p></div><div className="rounded-xl border border-white/8 bg-white/5 p-5"><p className="text-xs text-white/45">Service level</p><p className="mt-2 font-mono text-3xl font-semibold">{result.service.toFixed(1)}%</p><p className="mt-2 text-xs text-[#8fe0ca]">Orders fulfilled on time</p></div></div></CardContent></Card><Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardContent className="flex flex-col justify-between gap-5 py-5 sm:flex-row sm:items-center"><div className="flex gap-3"><div className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#e8f4f0] text-[#2c7668]"><Sparkles className="size-5" /></div><div><p className="font-semibold">Decision recommendation</p><p className="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">This scenario increases revenue without pushing service below 96%. Fund the extra inventory in Central first, where forecast confidence is highest.</p></div></div><Button className="gap-2 bg-[#153f3a] text-white hover:bg-[#1d514a]">Save scenario <ArrowRight /></Button></CardContent></Card></div>
    </section>
  </div>;
}

function DataPipeline() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState('');
  return <div className="space-y-6" data-view="pipeline">
    <SectionHeading eyebrow="End-to-end data engineering" title="From messy source files to trusted decisions." description="The Python pipeline validates incoming records, applies SQL business rules, calculates metrics, runs the forecast, and publishes dashboard-ready data." action={<Button variant="outline" className="gap-2"><Download /> Download data dictionary</Button>} />
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,.7fr)]">
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><div className="flex items-center justify-between"><div><CardTitle>Pipeline run</CardTitle><CardDescription>Run ID VO-2026-08-31-0600 · completed in 41 seconds</CardDescription></div><Badge className="border-0 bg-[#e6f4ef] text-[#236a5c]"><CircleCheck /> Healthy</Badge></div></CardHeader><CardContent><div className="grid gap-3 lg:grid-cols-5">{pipelineStages.map((stage, index) => <div key={stage.name} className="relative rounded-xl border bg-[#fbfcfb] p-4"><div className="mb-4 flex items-center justify-between"><div className="grid size-7 place-items-center rounded-full bg-[#dff2eb] text-[#2c7668]"><Check className="size-4" /></div>{index < pipelineStages.length - 1 && <ArrowRight className="hidden size-4 translate-x-7 text-[#b5c4c0] lg:block" />}</div><p className="text-sm font-semibold">{stage.name}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{stage.detail}</p><p className="mt-3 font-mono text-xs font-semibold text-[#2c7668]">{stage.rows}</p></div>)}</div><div className="mt-6 grid gap-4 sm:grid-cols-3"><div className="rounded-xl bg-[#eef6f3] p-4"><p className="text-xs text-muted-foreground">Rows accepted</p><p className="mt-1 font-mono text-xl font-semibold">18,274</p></div><div className="rounded-xl bg-[#fff6eb] p-4"><p className="text-xs text-muted-foreground">Rows quarantined</p><p className="mt-1 font-mono text-xl font-semibold">146</p></div><div className="rounded-xl bg-[#f0f3f5] p-4"><p className="text-xs text-muted-foreground">Data freshness</p><p className="mt-1 font-mono text-xl font-semibold">8 min</p></div></div></CardContent></Card>
      <Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Try a source file</CardTitle><CardDescription>Select a CSV to preview the ingestion step.</CardDescription></CardHeader><CardContent><input ref={fileRef} className="hidden" type="file" accept=".csv" onChange={(event) => setFileName(event.target.files?.[0]?.name ?? '')} /><button type="button" onClick={() => fileRef.current?.click()} className="grid w-full place-items-center rounded-2xl border border-dashed border-[#9abcb4] bg-[#f4faf7] px-6 py-10 text-center transition hover:bg-[#edf7f3]"><div className="grid size-11 place-items-center rounded-xl bg-white text-[#2c7668] shadow-sm"><CloudUpload className="size-5" /></div><p className="mt-4 text-sm font-semibold">{fileName || 'Choose a CSV file'}</p><p className="mt-1 text-xs text-muted-foreground">Demo validation runs in your browser</p></button>{fileName && <div className="mt-4 flex items-center gap-3 rounded-xl border border-[#b8ddcf] bg-[#eef9f4] p-3 text-sm text-[#28675b]"><FileCheck2 className="size-5" /><div><p className="font-semibold">File accepted</p><p className="text-xs opacity-75">Ready for schema and quality checks.</p></div></div>}</CardContent></Card>
    </section>
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]"><Card className="border-0 shadow-[0_6px_30px_rgb(15_23_42/5%)] ring-1 ring-[#102a2a]/7"><CardHeader><CardTitle>Data quality scorecard</CardTitle><CardDescription>Rules that prevent unreliable data from reaching the dashboard.</CardDescription></CardHeader><CardContent className="space-y-4">{qualityChecks.map((check) => <div key={check.label}><div className="mb-2 flex justify-between text-xs"><span className="font-medium">{check.label}</span><span className="font-mono text-[#2c7668]">{check.value}%</span></div><Progress value={check.value} className="h-1.5" /></div>)}</CardContent></Card><Card className="border-0 bg-[#112c2f] text-white shadow-[0_12px_36px_rgb(15_23_42/12%)] ring-0"><CardHeader><CardTitle className="text-white">Simple lineage</CardTitle><CardDescription className="text-white/45">How a raw sale becomes an executive metric.</CardDescription></CardHeader><CardContent><div className="flex flex-wrap items-center gap-2 text-xs"><span className="rounded-lg bg-white/7 px-3 py-2">sales.csv</span><ArrowRight className="size-4 text-white/30" /><span className="rounded-lg bg-white/7 px-3 py-2">Python validation</span><ArrowRight className="size-4 text-white/30" /><span className="rounded-lg bg-white/7 px-3 py-2">SQLite models</span><ArrowRight className="size-4 text-white/30" /><span className="rounded-lg bg-[#79d8bd]/14 px-3 py-2 text-[#9ee5d2]">Net revenue</span></div><p className="mt-6 text-sm leading-6 text-white/65">Every dashboard number can be traced back to its source and transformation. That makes review, debugging, and audit conversations much easier.</p></CardContent></Card></section>
  </div>;
}

export function VantageDashboard() {
  const [view, setView] = useState<View>('overview');
  const title = navItems.find((item) => item.id === view)?.label ?? 'Overview';
  return <main className="min-h-screen bg-background text-foreground">
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-white/8 bg-[#0d1d21] text-white lg:flex lg:flex-col"><div className="flex h-20 items-center gap-3 border-b border-white/8 px-6"><div className="grid size-9 place-items-center rounded-xl bg-[#79d8bd] text-[#09221f]"><Sparkles className="size-5" /></div><div><p className="text-[15px] font-semibold tracking-tight">VantageOps</p><p className="text-[11px] text-white/45">Decision intelligence</p></div></div><nav aria-label="Primary" className="space-y-1 px-3 py-6"><p className="mb-3 px-3 text-[10px] font-medium uppercase tracking-[0.18em] text-white/35">Workspace</p>{navItems.map((item) => <Button key={item.id} onClick={() => setView(item.id)} className={view === item.id ? 'h-10 w-full justify-start gap-3 bg-[#79d8bd]/14 text-[#a9ead8] hover:bg-[#79d8bd]/18' : 'h-10 w-full justify-start gap-3 text-white/55 hover:bg-white/6 hover:text-white'} variant="ghost"><item.icon /> {item.label}{item.badge && <Badge className="ml-auto border-0 bg-[#ef9869]/16 text-[#ffb58d]">{item.badge}</Badge>}</Button>)}</nav><div className="mt-auto p-4"><div className="rounded-2xl border border-white/8 bg-white/4 p-4"><div className="mb-2 flex items-center gap-2 text-xs text-white/60"><PackageCheck className="size-4 text-[#79d8bd]" /> Data health</div><p className="text-sm font-medium">99.2% complete</p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/8"><div className="h-full w-[99.2%] rounded-full bg-[#79d8bd]" /></div><p className="mt-3 text-[11px] text-white/40">Last refresh · 8 min ago</p></div></div></aside>
    <section className="lg:pl-64"><header className="sticky top-0 z-10 flex h-20 items-center justify-between border-b bg-background/88 px-5 backdrop-blur-xl md:px-8"><div><p className="text-xs font-medium text-muted-foreground">VantageOps / Workspace</p><h1 className="text-lg font-semibold tracking-tight">{title}</h1></div><div className="flex items-center gap-2"><Button aria-label="Search" variant="outline" size="icon"><Search /></Button><Button aria-label="Notifications" variant="outline" size="icon"><Bell /></Button><div className="ml-1 hidden items-center gap-3 border-l pl-4 sm:flex"><div className="grid size-9 place-items-center rounded-full bg-[#dbeee8] text-xs font-bold text-[#174f45]">DL</div><div><p className="text-xs font-semibold">Demo leader</p><p className="text-[10px] text-muted-foreground">Operations</p></div></div></div></header><div className="mx-auto max-w-[1500px] p-5 md:p-8">{view === 'overview' && <Overview onNavigate={setView} />}{view === 'forecast' && <ForecastLab />}{view === 'risk' && <RiskMonitor />}{view === 'scenario' && <ScenarioPlanner />}{view === 'pipeline' && <DataPipeline />}</div></section>
  </main>;
}
