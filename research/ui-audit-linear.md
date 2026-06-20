# UI Audit — Taxos AI Executive Dashboard

## Vision Assessment

The page presents a dark-themed executive dashboard with a fixed left sidebar, top header, and a dense multi-row grid. Key stats are prominent, charts occupy the middle section, and an executive summary panel rounds the bottom right.

Overall: visually polished, modern SaaS aesthetic, clear hierarchy for large numbers, but cramped in places and minimal data-detail affordances.

## Top 10 Ranked Improvements

1. Improve contrast / reduce visual noise in the AI Modules list
   Area: bottom-left modules panel.
   Issue: dense small text and light borders reduce scan speed.
   Recommendation: increase row padding, add subtle separators, and give active modules a stronger selected state.

2. Add explicit chart axes labels and data labels
   Area: Cash Flow Forecast and Revenue vs Expenses charts.
   Issue: charts lack axis titles and point/bar values on hover/tap.
   Recommendation: label X axis months, Y axis currency, and show tooltip values on hover.

3. Group KPIs by theme and add drill-down affordance
   Area: top KPI cards.
   Issue: metrics are visually similar so important outliers are harder to catch.
   Recommendation: color-code by pillar (Revenue green, Liability red, Cash blue, Health purple) and allow clicking a card to open a focused breakdown.

4. Introduce a time-range selector
   Area: top toolbar/header.
   Issue: only a single time context is visible (MTD), so comparisons are implicit only.
   Recommendation: add a Pills/select for 1M / 3M / 6M / 12M and update the chart window.

5. Make navigation context more explicit
   Area: left sidebar.
   Issue: active state exists but the set of items is long and lacks sectional grouping.
   Recommendation: add categories (Overview, Tax & Compliance, Reports, Settings) and collapse unused sections.

6. Make the Executive Summary scannable with structured cards
   Area: bottom-right summary.
   Issue: dense paragraph with line breaks; key takeaways compete within one text block.
   Recommendation: replace with 4 small cards (Headline, Key Risk, Opportunity, Next Action) with icons and accent chips.

7. Strengthen the CTA and show progress/availability
   Area: View Full Report button below summary.
   Issue: button looks promotional next to detailed content and does not indicate expected action cost/time.
   Recommendation: rename to "Review Detailed Report", show an estimated time (for example, ~3 min), and add a small preview or download option.

8. Add data-freshness indicators
   Area: KPI cards and charts.
   Issue: no visible last-updated timestamp.
   Recommendation: show "Updated 2 min ago" and a subtle manual refresh control near the header.

9. Improve focus and keyboard navigation
   Area: sidebar and interactions.
   Issue: no visible focus state or skip link; charts may trap exploration.
   Recommendation: add visible focus rings, implement tab order, and ensure chart tooltips are reachable via keyboard.

10. Reduce visual distraction from decorative background elements
    Area: top-right decorative wireframe.
    Issue: ambient background graphic competes with data density in a small viewport.
    Recommendation: animate/opacity it down or remove for smaller screens; restore only on wide desktops.
