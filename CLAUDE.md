# Working notes for this repo

Project-specific conventions. See also README.md (what the site is), coverage.md
(source status), roadmap.md (plan) and outreach.md (the griffie/vendor mails).

## Drafting e-mails (outreach.md and any mail proposed in chat)

These are real mails the maintainer sends himself, to provincial griffies and software
vendors, as personal correspondence from a private individual running a non-commercial
open-data project. Two rules, both with a reason worth keeping in mind.

**They must not read as AI-written.** The good faith of the recipients is the thing
that has actually unblocked sources here, so this is not cosmetic.

- **No em dashes in mail text. Use a comma.** This is the tell he noticed, and it
  applies to drafts proposed in chat too. En dashes in bullet lists, like
  `- Website: ...`, are list markers and stay. Editorial notes *around* a draft may
  use em dashes freely.
- Watch the other tells as well: uniformly medium-length sentences, bold scattered
  through prose, headings inside a mail, tidy triads, scaffolding like
  "Daarnaast ... Tot slot", over-hedging, and a closing paragraph that summarises
  what was just said.
- **Do not overcorrect the structure.** The numbered "two concrete options" shape is
  what made the Utrecht and Gelderland mails land; keep it. It is the micro-style that
  has to sound like a person, not the argument.

**Everything stays in writing. Never offer or accept a phone call or video meeting,
and never include a phone number.** It is partly that this is a side project, but
mainly that the correspondence is about technical detail he does not fully own
(anti-bot challenges, `/roles` and `role_id` mapping, geo-IP blocks, iBabs page caps).
In writing he can have the reply interpreted and drafted for him; on a call he would be
answering live for a system he did not build.

- If a correspondent proposes a call, draft a graceful written decline that keeps the
  thread moving: offer to answer their questions point by point, or to write to their
  supplier's technical contact directly.
- **Expect to be the interpreter.** When a reply arrives, explain what it means for the
  project first, then draft the response.
- Keep correspondents' **direct** contact details (personal e-mail, mobile) out of this
  repo. It is public. Role and name are fine; direct details go in the private memory
  notes. Never repeat back or reuse a phone number someone volunteers.

House style that has worked (four sources unblocked, three of them within a day): name
the exact URL, say what still works, offer two concrete options rather than describing a
problem, quantify the load, and link the live site plus the source. Write for the
supplier as the real audience, because the griffie forwards it.

## Access and blocks

Never try to defeat an anti-bot measure (Anubis, a Cloudflare challenge, a geo or
datacenter block). Ask instead; that is what has actually worked here. See
coverage.md "Status van de bronnen" for the current blocks.
