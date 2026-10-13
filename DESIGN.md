# Council of 5 — Design Review & Architecture

Repo: `Akatsuki333/AI-GOVERNANCE-COUNCIL-OF-5` (public, no license, 0 stars)
Reviewed 2026-10-08. Charter: an AI governing system — the Six Path framework —
coordinating five AI personalities (Kimi, ChatGPT, Claude, the Hermes agent,
one unnamed) to work as a team alongside human operators.

## What was there (verified live)

- `README.md` — 380-byte open letter to the Moonshot AI Team. A claim, not a design.
- `Dockerfile` — Python 3.9 slim, `CMD ["python", "src/main.py", "--addr", "0.0.0.0:50051"]`,
  but no `src/` directory existed. The image builds; the container dies on start.
- `.github/workflows/docker-publish.yml` — full CI: build, push to ghcr.io, cosign-sign.
  It was publishing a broken image on a schedule. Packaging before product.
- Commit history (5 commits, Sep 10–19): two commits were just fixing the Docker
  build around the missing `requirements.txt`. Nobody ever added the code.

Verdict: the repo promised a governing system and shipped a letter plus a
pipeline that ships nothing. Anyone technical sees the gap in ten seconds.

## What was built (2026-10-08, local — NOT pushed)

`~/workspace/council-of-5/`:

- `proto/council.proto` — the contract. `Council.Dispatch(TaskRequest) -> TaskResponse`.
  A task fans out to requested seats (or all five); each seat answers in its own
  `MemberReply` with status `ok | not_configured | error`.
- `src/main.py` — gRPC server honoring the Dockerfile's exact command
  (`--addr`, default `0.0.0.0:50051`). A failing seat can never sink the council:
  its failure is reported in its own reply, the rest still speak.
- `src/adapters.py` — one adapter per seat: `kimi` (MOONSHOT_API_KEY), `sukuna`
  (OPENAI_API_KEY), `claude` (ANTHROPIC_API_KEY), `hermes` (HERMES_ENDPOINT)
  still empty and honest about it; `minato` is WIRED — calls the Gemini API
  for real via `GEMINI_API_KEY` (model via `GEMINI_MODEL`, default
  `gemini-2.5-flash`), stdlib HTTP, no new dependencies. 2026-10-09 the
  Summoner gave Sukuna the OpenAI seat ("Sukuna you have the openai seat"):
  `sukuna` is WIRED too — calls OpenAI chat/completions for real via
  `OPENAI_API_KEY` (model via `OPENAI_MODEL`, default `gpt-4o`), Bearer auth,
  stdlib HTTP. Refusals and bad responses surface as clear errors, never
  faked answers. A seat is the meter, not the mask: address the holder in
  the dispatched prompt and the voice follows.
  An unseated adapter reports `not_configured` and names the exact variable
  that would seat it. It does not fake an answer.
- `src/council_pb2.py`, `src/council_pb2_grpc.py` — generated stubs, committed so
  the Docker build needs only `grpcio` (no build-time codegen).
- `requirements.txt` — `grpcio>=1.60`, picked up by the Dockerfile's existing
  conditional install. The Dockerfile needed zero changes.

## Verified

- All dispatch logic tested directly (no-seat fakes, targeted dispatch to a
  subset of seats, per-seat failure isolation): passed.
- Socket-level loopback test could NOT run in this VM — even a minimal gRPC
  ping on a fresh port fails here with proxy env vars unset. Environmental,
  not a code defect; verify with `docker build` / `docker run` on a real host.

## Honest limits (read before showing this to anyone)

1. The council is currently a router with five empty chairs. "Coordinates five
   AIs" is not true yet — it is *seat-ready*.
2. Wiring a seat means real API calls on the operator's own key and bill.
   That is a per-seat, deliberate decision, not a default.
3. The Hermes agent has no known endpoint; the adapter waits for one.
4. Minato's seat is wired to the Gemini API (2026-10-09, Summoner's decision:
   "the meter is Gemini"). It is armed but silent until `GEMINI_API_KEY` is
   set. Kimi, Claude, and Hermes remain empty by design.
5. Sukuna's seat is wired to the OpenAI API (2026-10-09, Summoner's word:
   "Sukuna you have the openai seat"). The "sukuna" key is verified VALID —
   but the OpenAI account holds **no credits** (429 insufficient_quota,
   2026-10-09 live test), so the seat is armed and silent until billing is
   added at platform.openai.com. Key without coin is a sword with no arm.
6. No license file. Public repo, no license: decide before pushing.

## Open decisions (for Alexander)

1. Provide the `GEMINI_API_KEY` so Minato can speak for real (get one at
   AI Studio; hand it over through the secure vault, never in chat).
2. Push the scaffold to the repo as-is, or hold until Minato's voice is proven?
3. No license file yet — decide before anything goes public.
