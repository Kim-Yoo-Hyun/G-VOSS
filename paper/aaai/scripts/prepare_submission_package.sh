#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
src_dir="${repo_root}/paper/aaai"
paper_dir="${repo_root}/paper"
ts="${H001_AAAI_PACKAGE_TS:-$(date +%Y%m%d_%H%M%S)}"
pkg_dir="${repo_root}/release/h001_aaai27_submission_${ts}"
archive="${repo_root}/release/h001_aaai27_submission_${ts}.tar.zst"
log_dir="${repo_root}/logs"

mkdir -p "${pkg_dir}/figures" "${log_dir}"

flatten_tex() {
  local input_file="$1"
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" =~ ^\\input\{([^}]+)\}$ ]]; then
      local rel="${BASH_REMATCH[1]}"
      local inc="${src_dir}/${rel}.tex"
      if [[ ! -f "${inc}" ]]; then
        printf 'Missing input file: %s\n' "${inc}" >&2
        return 1
      fi
      printf '\n%% BEGIN flattened input: %s\n' "${rel}.tex"
      sed 's#../generated/figures/#figures/#g' "${inc}"
      printf '\n%% END flattened input: %s\n\n' "${rel}.tex"
    elif [[ "${line}" == "\\bibliography{../references}" ]]; then
      printf '\\bibliography{references}\n'
    else
      printf '%s\n' "${line}" | sed 's#../generated/figures/#figures/#g'
    fi
  done < "${input_file}"
}

flatten_tex "${src_dir}/main.tex" > "${pkg_dir}/main.tex"

cp "${paper_dir}/references.bib" "${pkg_dir}/references.bib"
cp "${src_dir}/aaai2027.sty" "${pkg_dir}/aaai2027.sty"
cp "${src_dir}/aaai2027.bst" "${pkg_dir}/aaai2027.bst"
cp "${paper_dir}/generated/figures/figure1_framework.png" "${pkg_dir}/figures/"
cp "${paper_dir}/generated/figures/figure2_tradeoff.png" "${pkg_dir}/figures/"
cp "${paper_dir}/generated/figures/figure3_geometry_panels.png" "${pkg_dir}/figures/"

cat > "${pkg_dir}/README.md" <<EOF
# H001 AAAI-27 Submission Package

Generated: ${ts}

Purpose:

- flattened AAAI-27 anonymous LaTeX source for upload/package checks
- metadata-clean review PDF candidate
- minimal figure/bibliography/style files needed to compile the paper

Compile:

\`\`\`bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
\`\`\`

Primary PDF for review upload:

\`\`\`text
main_review_metadata_clean.pdf
\`\`\`

Boundary:

- This package is a local submission-hygiene artifact.
- The full result artifact bundle remains
  \`release/h001_full_validation_results_20260611_025158.tar.zst\`.
- Artifact/release and supplementary-upload policy is recorded in
  \`paper/aaai/submission_plan.md\` in the source repository.
- Actual portal fields, upload size/format limits, source-package requirements,
  checklist placement, and any required artifact URL field still need the final
  OpenReview/AAAI form check.
EOF

if ! docker image inspect h001-aaai-tex:20260611 >/dev/null 2>&1; then
  docker build -f "${src_dir}/Dockerfile.tex" -t h001-aaai-tex:20260611 "${src_dir}" \
    > "${log_dir}/h001_aaai_submission_pkg_image_build_${ts}.log" 2>&1
fi

docker run --rm --user "$(id -u):$(id -g)" -v "${pkg_dir}:/work" -w /work \
  h001-aaai-tex:20260611 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex \
  > "${log_dir}/h001_aaai_submission_pkg_build_${ts}.log" 2>&1

gs -q -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 \
  -dPDFSETTINGS=/prepress -dDetectDuplicateImages=true -dCompressFonts=true \
  -sOutputFile="${pkg_dir}/main_review_metadata_clean.pdf" \
  -c "[ /Title () /Author () /Subject () /Keywords () /Creator () /Producer () /DOCINFO pdfmark" \
  -f "${pkg_dir}/main.pdf"

{
  printf '# H001 AAAI-27 Submission Package Verification\n\n'
  printf 'timestamp: `%s`\n\n' "${ts}"
  printf '## Source Flattening\n\n'
  if rg -n '\\(input|include)\{' "${pkg_dir}/main.tex" >/tmp/h001_aaai_flatten_check_${ts}.txt 2>&1; then
    printf 'status: `blocked_input_or_include_remaining`\n\n'
    cat /tmp/h001_aaai_flatten_check_${ts}.txt
  else
    printf 'status: `ok_no_input_or_include_commands`\n\n'
  fi

  printf '## Anonymous String Scan\n\n'
  if rg -n -i 'yoohyun|yhkim|yoo hyun|seoul national|kaist|korea university|acknowledg' "${pkg_dir}/main.tex" > /tmp/h001_aaai_anon_scan_${ts}.txt 2>&1; then
    printf 'status: `review_needed_matches_found`\n\n'
    cat /tmp/h001_aaai_anon_scan_${ts}.txt
  else
    printf 'status: `ok_no_obvious_local_identity_strings`\n\n'
  fi

  printf '\n## PDF Info\n\n```text\n'
  pdfinfo "${pkg_dir}/main_review_metadata_clean.pdf" || true
  printf '```\n\n## Fonts\n\n```text\n'
  pdffonts "${pkg_dir}/main_review_metadata_clean.pdf" || true
  printf '```\n\n## Log Issues\n\n```text\n'
  rg -n 'LaTeX Error|Package aaai|Undefined references|Citation .* undefined|undefined citations|Overfull \\hbox|Overfull \\vbox|Fatal error|Emergency stop|hyperref' \
    "${pkg_dir}/main.log" || true
  printf '```\n'
} > "${pkg_dir}/verification_report.md"

sha256sum \
  "${pkg_dir}/main.tex" \
  "${pkg_dir}/main.pdf" \
  "${pkg_dir}/main_review_metadata_clean.pdf" \
  "${pkg_dir}/references.bib" \
  "${pkg_dir}/aaai2027.sty" \
  "${pkg_dir}/aaai2027.bst" \
  "${pkg_dir}"/figures/*.png \
  > "${pkg_dir}/sha256s.txt"

tar --zstd -cf "${archive}" -C "${repo_root}/release" "h001_aaai27_submission_${ts}"
sha256sum "${archive}" > "${archive}.sha256"

printf '%s\n' "${pkg_dir}"
