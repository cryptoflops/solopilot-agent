# MVP Scope & Constraints

- **Preferred Stack**: react,python,typescript
- **Build Timeframe**: 14.0 days
- **Playbook Track**: Growth, Rewards & Social
- **Planning Aggressiveness**: Defensive

---

## Specificity Constraints
- **Primary User**: Web2 consumer onboarded into a Web3 ecosystem via gamified features
- **Core Loop**: Authenticate via social login -> interact to gain points -> update profile and referral rankings in Supabase
- **Demo Path**: Sign in with Google -> copy referral link -> simulated referral signup -> dynamic leaderboard update
- **Validation Method**: Verify Supabase SQL RLS policies and run local endpoints to test referral logic
- **Fallback Plan**: Replace Web3Auth/OAuth integrations with simple mock username/email input credentials

---

## Submission Strategy
Create engaging consumer dApps, referral tools, or social-fi applications with simple gamification loops that drive user acquisition and immediate on-chain onboarding.

---

## Core MVP Features
- Social-login passwordless onboarding utilizing Web3Auth or simple Supabase email link auth.
- Relational database schema (Supabase/Firebase) storing referral mappings, user profile points, and referral trees.
- Share UI incorporating pre-baked Twitter/X and Telegram sharing buttons and dynamic copy-to-clipboard referral codes.
- High-fidelity leaderboard showing real-time rankings and dynamic reward claims animation.

### 🛡️ [DEFENSIVE PLAN] Lean Focus
- **Minimal Viable Loop**: Skip full/live deployments; focus 100% on local validation and Loom capture.
- **Mocks & Spares**: Hardcode/mock non-essential integrations (e.g. social logins, external databases).
- **Video First**: Keep features strictly limited to visual actions shown in the demo storyboard.


## Stretch Goals (Scope Compression Applied)
- No extra non-core features detected. Focus remains 100% on core MVP.

---

## Expected Stack Architecture
- **Frontend**: React (Vite) / Next.js
- **Backend / Integration**: HTML/CSS, JavaScript/TypeScript, Vite, Firebase / Supabase, Web3Auth
- **Database/Persistence**: Minimal (SQLite, Supabase, or Client-Side State)

---

## Architectural Rules
1. **No Speculative Abstractions**: Stick to minimal code that compiles and solves the problem.
2. **Mock Extraneous Systems**: Mock login, auth, or advanced state if they do not serve the core judges' checklist.
3. **Prioritize Demo Video UX**: Polish the user journey that will be showcased in the 2-minute video narrative.
