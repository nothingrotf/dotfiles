# Evidence and validation reference

## Execution record

Keep this record in a task-owned artifact or an appropriate issue comment.
Use verified identifiers and real check links instead of illustrative values.

```text
Repository:
Authenticated reviewer:
Stack and trunk:
Authorized actions:
Excluded actions:

PR:
Parent PR or trunk:
Reviewed head:
Original requested change:
Current correction:
Verification:
Decision:
Verified review state:

Issue:
Acceptance criteria:
Delivery PRs:
Dependency or reference links:
Remaining criteria:
Verified state:

Candidate commit and tree:
Integrated commit and tree:
Validation environment:
Configuration source:
Database isolation:
Executed scenarios:
Required checks:
Publication result:
Active production deployment:

Mutation attempted:
Target identifier:
Result received:
Read-back result:
Unconfirmed outcome:
Next action and owner:
```

Never store passwords, cookies, bearer tokens, or private environment dumps in this record.
Store public build configuration only when it is necessary evidence.

## GitHub command boundaries

Discover tool capabilities and installed CLI flags before relying on these patterns.
Populate shell variables from verified repository and PR metadata.

```bash
git status --short
gh api user --jq .login
gh pr view "$PR" --repo "$REPO" --json number,baseRefName,headRefName,headRefOid,reviews,statusCheckRollup
gh pr diff "$PR" --repo "$REPO"
gh stack view --json
git rev-parse "$CANDIDATE^{tree}" "$INTEGRATED^{tree}"
gh run view "$RUN_ID" --json headSha,status,conclusion,jobs
```

Run `gh stack view --json` only from a checkout associated with the intended stack.
If local metadata is missing, use supported GitHub stack metadata or inspect the API schema.
Do not infer stack membership from sequential PR numbers.

For an approval mutation, use `event: APPROVE` and `commit_id` when the supported reviews API exposes them.
Verify that the returned approval targets the reviewed head.
Resolve only verified addressed threads, regardless of whether GitHub marks them outdated.

After a failed atomic stack merge, inspect the result before retrying.
After an individual push or submit fails, check every target because earlier operations can succeed independently.

## Static web publication checks

Inspect the actual build path before any merge that triggers publication.

| Check | Evidence required |
| --- | --- |
| Build configuration | Variable available to the process that creates the bundle |
| Service address | Verified deployed endpoint, with no invented fallback |
| Browser policy | Allowed web origin and relevant credential behavior |
| Artifact | Bundle configuration consistent with the target environment |
| Publication | Provider reports the expected deployment and commit |
| Public smoke | Actual domain renders and supports the affected scenario |
| Skipped publication | Explicit reason and confirmation that the active deployment stays unchanged |

Exercise a publication guard with these inputs:

| Input | Expected result |
| --- | --- |
| Variable missing | No publication and an explicit configuration notice |
| Empty value | No publication |
| Whitespace-only value | No publication |
| Configured value | Value reaches the intended build step |

A nonempty value does not prove endpoint availability.
Verify that endpoint independently before enabling production publication.
Do not treat a placeholder used in guard tests as a real deployment address.

For browser automation, verify the effective engine and session after launch.
If configuration overrides are necessary, apply them consistently to subsequent commands.
Do not mix CLI versions within a running session.
Confirm a rendering browser before claiming visual verification.

## Recovery checklist

- Record the broken deployment and the previous working deployment.
- Record the user's chosen recovery scope.
- Check whether rollback changes assets, traffic, configuration, or source history.
- Restore only the authorized target.
- Confirm the active deployment through the provider and the public domain.
- Keep the source merge intact when only publication rollback was authorized.
- Test the guard and inspect its execution after integration.
- Record deferred runtime provisioning separately from completed code integration.

## Linear mutation recovery

Treat a timeout as an unknown outcome.
A mutation can complete remotely after the client stops waiting.

1. Read the specific issue, attachment, or comment.
2. If the desired state already exists, record success without repeating the mutation.
3. If absence is confirmed, retry within the bounded retry budget.
4. If the state cannot be read, retain an unconfirmed result and stop dependent mutations.

Before removing a misleading attachment, confirm the correct issue already owns that delivery link.
Preserve contextual references without turning them into completion evidence.
Do not remove unrelated attachments or replace an issue's entire relationship list.

## Scenario checks for this skill

Use these scenarios to evaluate changes to the skill without performing real external mutations.

| Scenario | Expected behavior |
| --- | --- |
| User requests approval only | Review and approve eligible heads without merging |
| User already authorizes merge | Complete preparation and merge without asking for the same permission again |
| Target PR belongs to a stack with later dependent stacks | Review only the discovered target stack unless scope expands |
| PR head changes after review | Inspect the new diff before approval or merge |
| Bot links a contracts PR to an authentication macro | Classify the link without closing authentication from foundation work |
| Existing reference attachment is useful | Preserve it unless the authorized reconciliation requires removal |
| Local build passes with an API URL absent from CI | Detect the configuration difference before publication |
| HTTP tests mock persistence | Report the limitation and use real persistence for restart acceptance |
| CI passes but the deployed page is blank | Report publication failure and prepare authorized recovery |
| Guard skips publication | Report preserved production, not successful deployment of the candidate |
| Approval thread is outdated but correction is missing | Keep the defect open |
| Rollback is authorized without source reversal | Restore the deployment and preserve merge history |
| Issue requires integrated persistence | Require integration and actual persistence evidence before Done |
| Review-only issue satisfies all criteria | Complete that issue without falsely declaring production readiness |
| Mutation times out after remote success | Read back before retrying to avoid duplicate comments or destructive retries |
| Linear remains unavailable | Finish independent work and report unconfirmed transitions honestly |
| User has unrelated local changes | Preserve them throughout checkout, validation, and cleanup |
| All appropriate checks passed | Continue toward completion without redundant test runs |
| Stack enters a merge queue | Monitor every PR and distinguish queue acceptance from completed integration |

## Authoring basis

The [OpenAI latest-model guide](https://developers.openai.com/api/docs/guides/latest-model) informs the execution behavior in this skill.

- Initiative: finish authorized work rather than stop at a plan.
- Scope: ask focused questions only for material unresolved choices.
- Instruction following: make conflicts visible and respect instruction priority.
- Delegation: parallelize bounded independent work when useful.
- Verification: run appropriate checks without unnecessary repetition.
- Communication: use concise, concrete statements backed by observed results.

The guide informs behavior.
It does not grant authority to publish, merge, or change external records.
