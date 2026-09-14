External API integration: **this phase makes ZERO live retailer requests.** Dan authorised none
(*"Work offline — no live retailer request is authorised"*, 2026-09-14) and both prior budgets
(`QUESTIONS.md` § 0g, § 0h) are fully spent. Criterion 5's cap is therefore **0 per retailer**,
stated here before the first plan runs, and the actual count recorded at close must be 0. Every
measurement in this phase is read from the running daemon's own already-spent requests —
`journalctl -u boty`, `state.json`, `served/boty/status.json` — which adds nothing to any
retailer's view of us. **Reading those three files is permitted; writing any of them is not.**
