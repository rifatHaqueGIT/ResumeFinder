# DESIGN.md - Structural & Visual Contract

## 1. Typography & Hierarchy
* **Font Family:** Use a clean, modern sans-serif stack (e.g., `Inter`, `Plus Jakarta Sans`, or system-ui).
* **Scale & Density:** 
  * Headings: Bold weights, tight letter-spacing (`tracking-tight`), no oversized hero typography.
  * Body: Regular weight, highly readable line-height (`leading-relaxed`). Left-aligned by default; **never center-align long blocks of body text.**

## 2. Color Palette & Surface Rules
* **Strict Color Budget:** Max 3 core color families (Primary, Neutral, Accent).
* **No Gradients:** Absolutely no purple-to-blue gradients, neon glowing borders, or background blurs (`backdrop-blur` used as a decorative background).
* **Surfaces:** Use flat, solid backgrounds. Distinguish sections using subtle, light gray or muted borders (`1px solid`) instead of heavy, fuzzy drop shadows.

## 3. Component & Layout Constraints
* **Border Radius:** Enforce a strict, uniform corner radius across the app (e.g., exactly `6px` or `8px` for cards and buttons). **Ban ultra-rounded "pill" shapes** unless used for specific semantic tags/badges.
* **Iconography:** Use a single cohesive icon library (e.g., Lucide, Heroicons). Icons must strictly serve a navigational or functional purpose.
* **Forbidden Elements:** 
  * No decorative emojis (e.g., 🚀, ✨, 🔥) in headers, buttons, or feature lists.
  * No generic, center-aligned 3-column "feature grids" with abstract icons.
  * No placeholder text that reads like marketing copy; use realistic, dense system data.

## 4. UI Layout Frameworks (By Use Case)

### Case A: SaaS & Admin Dashboards
* **Layout Structure:** Multi-column layout with a fixed, dense left sidebar navigation and a main content area.
* **Data Presentation:** Prioritize structured, border-separated data tables, key-value detail grids, and clean metric cards over empty white space.

### Case B: Mobile Utilities & Consumer Feeds
* **Layout Structure:** Strict edge-to-edge container constraints. Use a fixed bottom navigation bar or a clean top header.
* **Component Rhythm:** Direct list views or uniform card streams. Maintain tight vertical padding to ensure high information density per screen.
