#!/usr/bin/env bash
#
# Builds the Chrome Web Store upload zip from extension/.
#
# Pass a version to stamp into the packaged manifest; CI does this so the patch
# number always climbs without a version-bump commit on every change. Run with
# no arguments to package the version already in the manifest, which is what
# you want for the first, manual submission.
#
#   scripts/package_extension.sh          -> dist/ff-sidekick-extension-v2.1.0.zip
#   scripts/package_extension.sh 2.1.42   -> dist/ff-sidekick-extension-v2.1.42.zip
#
# Prints the path of the zip it wrote.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

override="${1:-}"

staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT

cp -R extension/. "$staging/"

# Ship only what the extension runs at runtime. README.txt is developer-facing
# load-unpacked instructions, and stray .DS_Store files fail package validation.
find "$staging" \( -name 'README.txt' -o -name '*.md' -o -name '.DS_Store' \) -delete

version="$(python3 - "$staging/manifest.json" "$override" <<'PY'
import json
import sys

path, override = sys.argv[1], sys.argv[2]
with open(path) as f:
    manifest = json.load(f)

if override:
    manifest["version"] = override
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

print(manifest["version"])
PY
)"

mkdir -p dist
out="$repo_root/dist/ff-sidekick-extension-v$version.zip"
rm -f "$out"
(cd "$staging" && zip -qr "$out" .)

# The store reads manifest.json from the archive root, not from a nested folder.
# Matched with a case glob rather than a pipe to grep, which would trip pipefail.
listing="$(unzip -Z1 "$out")"
case $'\n'"$listing"$'\n' in
  *$'\n'manifest.json$'\n'*) ;;
  *)
    echo "manifest.json is not at the zip root: $out" >&2
    exit 1
    ;;
esac

echo "$out"
