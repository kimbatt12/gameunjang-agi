#!/usr/bin/env bash

run_code_review() {
  remote_name=$1
  remote_url=$2

  if [ ! -s "$review_refs_file" ]; then
    printf 'pre-push: no branch refs require code review; allowing push.\n' >&2
    return 0
  fi

  if ! command -v opencode >/dev/null 2>&1; then
    abort "opencode is not installed or not on PATH; install opencode or fix PATH before pushing."
  fi

  review_context=$(mktemp "${TMPDIR:-/tmp}/opencode-pre-push-review.XXXXXX") || abort "failed to create temporary review context."

  {
    printf '# Pre-push code review context\n\n'
    printf '%s\n' "- Remote: $remote_name ($remote_url)"
    printf '## Push updates\n\n```text\n'
    while read -r local_ref local_sha remote_ref remote_sha; do
      printf '%s %s -> %s %s\n' "$local_ref" "$local_sha" "$remote_ref" "$remote_sha"
    done <"$push_updates_file"
    printf '```\n\n'
    printf '## Working tree status\n\n```text\n'
    git status --short
    printf '```\n\n'
    while read -r local_ref local_sha remote_ref remote_sha local_commit diff_base; do
      printf '## Reviewed ref: %s -> %s\n\n' "$local_ref" "$remote_ref"
      printf '%s\n' "- Local SHA: $local_sha"
      printf '%s\n' "- Review commit: $local_commit"
      printf '%s\n' "- Remote SHA: $remote_sha"
      printf '%s\n\n' "- Diff base: $diff_base"
      printf '### Diff stat (%s..%s)\n\n```text\n' "$diff_base" "$local_commit"
      git diff --stat "$diff_base" "$local_commit"
      printf '```\n\n'
      printf '### Diff (%s..%s)\n\n```diff\n' "$diff_base" "$local_commit"
      git diff --find-renames "$diff_base" "$local_commit"
      printf '```\n\n'
    done <"$review_refs_file"
  } >"$review_context" || abort "failed to prepare review context."

  review_prompt="Review the attached pre-push diff context in read-only mode as the code-reviewer agent. Focus on whether this push should be blocked for correctness, security, repository-rule, or validation issues. Do not edit files, stage changes, commit, or push. The final line must be exactly either 'PUSH_REVIEW_STATUS: pass' or 'PUSH_REVIEW_STATUS: fail'."

  printf 'pre-push: running opencode code-reviewer for pushed branch refs...\n' >&2
  if ! review_output=$(opencode run --agent code-reviewer "$review_prompt" --file "$review_context" 2>&1); then
    printf '%s\n' "$review_output" >&2
    abort "opencode code-reviewer failed to run; push blocked."
  fi

  printf '%s\n' "$review_output" >&2
  last_line=$(printf '%s\n' "$review_output" | sed '/^[[:space:]]*$/d' | tail -n 1)

  case "$last_line" in
    'PUSH_REVIEW_STATUS: pass')
      printf 'pre-push: code-reviewer passed.\n' >&2
      return 0
      ;;
    'PUSH_REVIEW_STATUS: fail')
      abort "code-reviewer reported fail; push blocked."
      ;;
    *)
      abort "code-reviewer did not end with a valid PUSH_REVIEW_STATUS line; push blocked."
      ;;
  esac
}
