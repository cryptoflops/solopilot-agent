# Project Checklist & Task List

- **Aggressiveness Level**: Defensive

## [ ] Phase 1: Environment & Scaffolding
- [ ] Initialize repository and clean directory layout
- [ ] Install dependencies (Vite, React, tailwind css, libraries)
- [ ] Set up environment variables (.env, API keys)

## [ ] Phase 2: Must-Ship Core Loop & Demo Path (Demo-First Focus)
- [ ] Implement the primary user flow interface: Sign in with Google -> copy referral link -> simulated referral signup -> dynamic leaderboard update
- [ ] Core integration: Authenticate via social login -> interact to gain points -> update profile and referral rankings in Supabase
- [ ] Initialize Supabase schema with profiles and referrals tables.
- [ ] Write SQL row-level security (RLS) policies for user data protection.
- [ ] Implement API edge function to handle referral signup validation.
- [ ] Integrate Web3Auth or social login provider.
- [ ] Build copy-to-clipboard referral widgets and share hooks.
- [ ] Create dynamic leaderboard component sorting users by points.
- [ ] Implement connection hooks (APIs, Wallets, or Auth)
- [ ] Add loading indicators and micro-animations showing processing/state changes

## [ ] Phase 3: Validation, Mocks & Fallbacks
- [ ] Run validation method: Verify Supabase SQL RLS policies and run local endpoints to test referral logic
- [ ] Verify error states and transaction failures are correctly handled on the UI
- [ ] Setup fallback implementation path if integration fails: Replace Web3Auth/OAuth integrations with simple mock username/email input credentials

## [ ] Phase 3.5: [DEFENSIVE LEAN] Mocking & Focus
- [ ] Strip down features; mock all complex APIs/sign-ins
- [ ] Record walkthrough video utilizing local node / dev mode
- [ ] Devote final 50% of build timeframe purely to scripting and editing the 2-minute Loom


## [ ] Phase 4: Recording Prep & Walkthrough Demo
- [ ] Prepare mock data showing the happy-path execution
- [ ] Write storyboard slide descriptions (see demo_narrative.md)
- [ ] Record a 2-minute clean screen capture flow
- [ ] Voiceover and sync video narrative

## [ ] Phase 5: Submission & Documentation
- [ ] Update README.md with detailed setup and execution instructions
- [ ] Write description and final pitch (see submission_draft.md)
- [ ] Compile links and verify builds run in clean directories
