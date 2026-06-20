#!/usr/bin/env bash

review_context=""
validation_root=""
push_updates_file=""
review_refs_file=""
empty_tree=4b825dc642cb6eb9a060e54bf8d69288fbee4904

cleanup() {
  if [ -n "$review_context" ]; then
    rm -f "$review_context"
  fi

  if [ -n "$validation_root" ]; then
    git worktree remove --force "$validation_root" >/dev/null 2>&1 || rm -rf "$validation_root"
  fi

  if [ -n "$push_updates_file" ]; then
    rm -f "$push_updates_file"
  fi

  if [ -n "$review_refs_file" ]; then
    rm -f "$review_refs_file"
  fi
}

is_zero_sha() {
  case "$1" in
    0000000000000000000000000000000000000000) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_commit() {
  git rev-parse --verify --quiet "$1^{commit}" 2>/dev/null
}

compute_diff_base() {
  local_sha=$1
  remote_sha=$2
  local_commit=$3

  if ! is_zero_sha "$remote_sha" && resolve_commit "$remote_sha" >/dev/null; then
    printf '%s\n' "$remote_sha"
    return 0
  fi

  if git rev-parse --verify --quiet origin/main >/dev/null; then
    git merge-base "$local_commit" origin/main 2>/dev/null && return 0
  fi

  git rev-parse --verify --quiet "$local_commit^" 2>/dev/null || printf '%s\n' "$empty_tree"
}

append_manual_update_if_needed() {
  if [ -s "$push_updates_file" ]; then
    return 0
  fi

  current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  local_sha=$(git rev-parse --verify HEAD 2>/dev/null) || abort "no pre-push stdin and HEAD could not be resolved."
  local_ref=HEAD
  remote_ref=HEAD
  remote_sha=0000000000000000000000000000000000000000

  if [ -n "$current_branch" ]; then
    local_ref="refs/heads/$current_branch"
    upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)
    if [ -n "$upstream" ]; then
      remote_ref="refs/heads/${upstream#*/}"
      remote_sha=$(git rev-parse --verify "$upstream" 2>/dev/null || printf '%s\n' "$remote_sha")
    elif git rev-parse --verify --quiet origin/main >/dev/null; then
      remote_ref=refs/heads/main
    fi
  fi

  printf '%s %s %s %s\n' "$local_ref" "$local_sha" "$remote_ref" "$remote_sha" >>"$push_updates_file"
  printf 'pre-push: no ref updates on stdin; reviewing current HEAD for manual hook run.\n' >&2
}

read_push_updates() {
  push_updates_file=$(mktemp "${TMPDIR:-/tmp}/pre-push-updates.XXXXXX") || abort "failed to create temporary push update list."

  if [ -t 0 ]; then
    return 0
  fi

  while read -r local_ref local_sha remote_ref remote_sha; do
    [ -n "${local_ref:-}" ] || continue
    printf '%s %s %s %s\n' "$local_ref" "$local_sha" "$remote_ref" "$remote_sha" >>"$push_updates_file"
  done
}

plan_update() {
  local_ref=$1
  local_sha=$2
  remote_ref=$3
  remote_sha=$4

  if is_zero_sha "$local_sha"; then
    printf 'pre-push: skipping deleted ref %s -> %s; no validation or review needed.\n' "$local_ref" "$remote_ref" >&2
    return 0
  fi

  case "$local_ref:$remote_ref" in
    refs/tags/*:*|*:refs/tags/*)
      printf 'pre-push: skipping tag ref %s -> %s; no branch tree validation configured.\n' "$local_ref" "$remote_ref" >&2
      return 0
      ;;
  esac

  local_commit=$(resolve_commit "$local_sha" || true)
  if [ -z "$local_commit" ]; then
    printf 'pre-push: skipping %s -> %s; local object %s has no commit/tree diff to review.\n' "$local_ref" "$remote_ref" "$local_sha" >&2
    return 0
  fi

  case "$local_ref:$remote_ref" in
    refs/heads/*:*|*:refs/heads/*|HEAD:*)
      diff_base=$(compute_diff_base "$local_sha" "$remote_sha" "$local_commit") || abort "failed to compute diff base for $local_ref -> $remote_ref."
      printf '%s %s %s %s %s %s\n' "$local_ref" "$local_sha" "$remote_ref" "$remote_sha" "$local_commit" "$diff_base" >>"$review_refs_file"
      ;;
    *)
      printf 'pre-push: skipping non-branch ref %s -> %s; no branch tree validation configured.\n' "$local_ref" "$remote_ref" >&2
      ;;
  esac
}
