for repo in $(gh repo list --limit 500 --no-archived --json nameWithOwner -q '.[].nameWithOwner'); do
  for status in in_progress queued; do
    out=$(gh run list --repo "$repo" --status "$status" --limit 1000\
      --json workflowName,displayTitle,headBranch \
      -q '.[] | "  \(.workflowName) | \(.displayTitle) | \(.headBranch)"')
    [ -n "$out" ] && echo "[$status] $repo" && echo "$out"
  done
done
